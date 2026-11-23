"""Reparacion de AUD-005 (audit-2026-11-22), autorizada expresamente por el
operador el 2026-11-23, que ademas anadio la regla de permiso para que la
ejecute el agente. Revisada por Fable antes del commit (APTO CON CAMBIOS,
aplicados). Sin `--apply` solo informa (dry-run).

Contexto: hasta el arreglo de AUD-005 (`e23634b`), en partidos NCAAB de sede
neutral con local y visitante invertidos entre el feed de cuotas y `/scores`,
`settle._grade` anulaba (`void`) la seleccion del LOCAL de cuotas mientras el
visitante y los totals del mismo evento si se graduaban. `DEDUP_KEY` no incluye
`result`, asi que esas filas quedaron anuladas para siempre.

Que hace: para cada evento con filas h2h/spreads anuladas SIN `stale_void`,
- busca su marcador en `ResultsStore` con la identidad exacta de produccion
  (`runner.exact_history_scores_map`), en la orientacion de cuotas o en la
  invertida;
- GUARDA DE CONSISTENCIA: re-gradua con ese marcador TODAS las filas no anuladas
  del evento (en graded y settled) y exige que reproduzcan exactamente su
  `result` registrado, con al menos una de h2h o spreads (los totals solos no
  validan orientacion ni margen); si una sola difiere, el evento se descarta;
- solo entonces re-gradua las filas anuladas con `settle._grade` (la logica de
  produccion ya corregida). Una fila que siga saliendo `void` no se toca.

`settled_ncaab.csv` no tiene `start_time`: usa el marcador validado del mismo
`event_id` en graded, tras comprobar que local y visitante coinciden.

Solo cambian `result`, `pnl` (stake 0 en shadow; si alguna fila cambiada tuviera
stake>0 se aborta) y `flags` (+ `regrade_aud005`). Ni filas ni columnas nuevas;
mismo orden. Idempotente por el flag.

CONGELADO: el conjunto revisado (12 eventos, 24 + 10 filas y sus transiciones,
dry-run del 2026-11-23) esta en las constantes ESPERADO_*; si el plan no lo
reproduce exactamente, aborta sin escribir.

Escritura: lock de todos los ficheros, SHA comprobado bajo lock, copias y
MANIFEST.json (SHA-256 antes y despues, y cada fila cambiada) en
`data/backups/repair-aud005-20261123/<UTC>/`. Cada CSV se reemplaza de forma
atomica; entre ficheros NO hay atomicidad de sistema de ficheros, asi que si
falla una escritura se restauran desde las copias los ya escritos, sin soltar el
lock. Si falla tambien la restauracion, el MANIFEST queda `en_curso` y la
recuperacion manual es copiar `<backup>/data/...` sobre `data/...`.
Ejecutar fuera de las ventanas de SETTLE y DIARIO.

Es una correccion del REGISTRO, no una afirmacion de rentabilidad.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sqp.settlement.runner import exact_history_scores_map  # noqa: E402
from sqp.settlement.settle import _grade  # noqa: E402
from sqp.storage.atomic import atomic_write_csv  # noqa: E402
from sqp.storage.lock import locked  # noqa: E402
from sqp.storage.results_store import ResultsStore  # noqa: E402

LEAGUE = "ncaab"
FLAG = "regrade_aud005"
BACKUP = ROOT / "data" / "backups" / "repair-aud005-20261123"
GRADED_REL = Path("data") / "calibration" / "graded_ncaab.csv"
SETTLED_REL = Path("data") / "bets" / "settled_ncaab.csv"
SIDE_MARKETS = ("h2h", "spreads")
PNL = {"win": lambda s, p: s * (p - 1), "loss": lambda s, p: -s,
       "push": lambda s, p: 0.0, "void": lambda s, p: 0.0,
       "half_win": lambda s, p: 0.5 * s * (p - 1), "half_loss": lambda s, p: -0.5 * s}

# Congelado del dry-run revisado (2026-11-23).
ESPERADO_EVENTOS = frozenset({
    "089763b58d06f84ae9546c2037e7d941", "0c0b87a4ca3e26dae6a79d50a65514be",
    "5246df4438e82883d2aa2437d1f9857c", "683ca7110f83d94d2807e36e9bc3e10c",
    "6d51497e3276256e5dd07220b624c37f", "8f88d57c43c67df9c1beb816e0c11d5c",
    "935de84bb70edb4ad03cb37206a6325c", "a873493a7ad136458cf98553f9c8a216",
    "abe6046c0e5100a1e721207ddedccc18", "ac091b3b15d1fcf0312f8c0500329879",
    "e1a630421d7f278a4da6480a7d1c788f", "fb4e0baed91adfe2f7de6ca28ed533e8",
})
ESPERADO_CAMBIOS = {"graded_ncaab": 24, "settled_ncaab": 10}
ESPERADO_TRANSICIONES: dict[str, dict[str, int]] = {
    "graded_ncaab": {"h2h:void->loss": 6, "spreads:void->loss": 7,
                     "h2h:void->win": 6, "spreads:void->win": 5},
    "settled_ncaab": {"h2h:void->loss": 3, "spreads:void->loss": 3,
                      "h2h:void->win": 2, "spreads:void->win": 2},
}

SHA_PLAN: dict[Path, str] = {}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _leer(p: Path) -> pd.DataFrame:
    SHA_PLAN[p] = _sha(p)
    return pd.read_csv(p)


def _flags(df: pd.DataFrame) -> pd.Series:
    return (df["flags"].fillna("").astype(str) if "flags" in df.columns
            else pd.Series("", index=df.index))


def _anuladas(df: pd.DataFrame) -> pd.Index:
    f = _flags(df)
    return df.index[(df["result"] == "void") & ~f.str.contains("stale_void", regex=False)
                    & ~f.str.contains(FLAG, regex=False) & df["market"].isin(SIDE_MARKETS)]


def _marcadores(graded: pd.DataFrame, eventos: list[str]) -> dict[str, tuple[int, int, str]]:
    """event_id -> marcador del store, en orientacion de cuotas o invertida.
    Si las dos orientaciones devuelven marcadores DISTINTOS el evento es ambiguo y
    no se gradua. Si devuelven el mismo, es el mismo partido del store: pasa
    cuando el propio feed de cuotas cambio la orientacion entre capturas (sede
    neutral; p. ej. ac091b3b..., Kansas-Kentucky, con filas en ambas)."""
    results = ResultsStore(ROOT).load(LEAGUE)
    ev = graded[graded["event_id"].astype(str).isin(eventos)]
    directo = exact_history_scores_map(ev, results, LEAGUE, known_events=graded)
    inv, inv_known = ev.copy(), graded.copy()
    inv["home"], inv["away"] = ev["away"], ev["home"]
    inv_known["home"], inv_known["away"] = graded["away"], graded["home"]
    invertido = exact_history_scores_map(inv, results, LEAGUE, known_events=inv_known)
    out: dict[str, tuple[int, int, str]] = {}
    for e in eventos:
        a, b = directo.get(e), invertido.get(e)
        if a is not None and b is not None and a != b:
            continue  # ambiguo: no se gradua
        sc = a if a is not None else b
        if sc is not None:
            out[e] = sc
    return out


def _consistente(frames: list[pd.DataFrame], e: str,
                 sc: tuple[int, int, str]) -> tuple[bool, int, int]:
    """(ok, n_controles, n_controles_de_lado). Las filas NO anuladas del evento
    deben reproducir su result con `sc`."""
    hs, as_, home = sc
    n = n_lado = 0
    for df in frames:
        filas = df[(df["event_id"].astype(str) == e) & (df["result"] != "void")]
        for _, r in filas.iterrows():
            n += 1
            n_lado += int(r["market"] in SIDE_MARKETS)
            if _grade(r, hs, as_, home) != r["result"]:
                return False, n, n_lado
    return True, n, n_lado


def _equipos(df: pd.DataFrame, e: str) -> set[tuple[str, str]]:
    filas = df[df["event_id"].astype(str) == e]
    return {(str(h), str(a)) for h, a in zip(filas["home"], filas["away"])}


def planificar() -> tuple[dict[Path, pd.DataFrame], dict]:
    graded_p, settled_p = ROOT / GRADED_REL, ROOT / SETTLED_REL
    graded, settled = _leer(graded_p), _leer(settled_p)
    objetivo = {p: _anuladas(df) for p, df in ((graded_p, graded), (settled_p, settled))}
    eventos = sorted({str(x) for p, df in ((graded_p, graded), (settled_p, settled))
                      for x in df.loc[objetivo[p], "event_id"]})
    if not eventos:
        return {}, {"eventos_candidatos": 0}
    if set(eventos) != ESPERADO_EVENTOS:
        raise SystemExit(f"AUD-005: eventos candidatos {sorted(set(eventos) ^ ESPERADO_EVENTOS)} "
                         "difieren de los revisados. Aborta sin escribir nada.")
    # settled no tiene start_time: toma el marcador de graded; cada par
    # (local, visitante) de settled tiene que existir en graded para ese evento.
    # (Un evento puede traer las dos orientaciones si el feed de cuotas la cambio.)
    for e in eventos:
        eg, es = _equipos(graded, e), _equipos(settled, e)
        if not eg or not es <= eg:
            raise SystemExit(f"AUD-005: local/visitante de {e} no coinciden entre graded "
                             f"{sorted(eg)} y settled {sorted(es)}. Aborta.")
    marc = _marcadores(graded, eventos)
    informe: dict = {"eventos_candidatos": len(eventos), "eventos": {}, "ficheros": {},
                     "filas": []}
    validos: dict[str, tuple[int, int, str]] = {}
    for e in eventos:
        sc = marc.get(e)
        if sc is None:
            informe["eventos"][e] = {"estado": "sin_marcador_en_store"}
            continue
        ok, n, n_lado = _consistente([graded, settled], e, sc)
        estado = ("inconsistente" if not ok else
                  "sin_control_de_lado" if n_lado == 0 else "valido")
        informe["eventos"][e] = {"marcador": list(sc), "filas_control": n,
                                 "controles_de_lado": n_lado, "estado": estado}
        if estado == "valido":
            validos[e] = sc
    cambios: dict[Path, pd.DataFrame] = {}
    for p, df in ((graded_p, graded), (settled_p, settled)):
        out = df.copy()
        flags = _flags(out)
        info: dict = {"anuladas_candidatas": len(objetivo[p]), "cambiadas": 0, "transiciones": {}}
        for i in objetivo[p]:
            r = df.loc[i]
            sc = validos.get(str(r["event_id"]))
            if sc is None:
                continue
            nuevo = _grade(r, *sc)
            if nuevo == "void":
                continue
            stake = float(pd.to_numeric(pd.Series([r.get("stake", 0.0)]),
                                        errors="coerce").fillna(0.0).iloc[0])
            if stake > 0:
                raise SystemExit(f"AUD-005: fila {i} de {p.name} con stake>0. Aborta.")
            out.at[i, "result"] = nuevo
            out.at[i, "pnl"] = round(PNL[nuevo](stake, float(r["price_decimal"])), 2)
            flags.at[i] = (flags.at[i] + ";" + FLAG).lstrip(";")
            info["cambiadas"] += 1
            k = f"{r['market']}:void->{nuevo}"
            info["transiciones"][k] = info["transiciones"].get(k, 0) + 1
            informe["filas"].append({"fichero": p.stem, "indice": int(i),
                                     "event_id": str(r["event_id"]), "market": r["market"],
                                     "selection": r["selection"], "line": None
                                     if pd.isna(r["line"]) else float(r["line"]),
                                     "generated_at": str(r.get("generated_at")),
                                     "antes": "void", "despues": nuevo})
        out["flags"] = flags
        informe["ficheros"][p.stem] = info
        if info["cambiadas"] != ESPERADO_CAMBIOS[p.stem]:
            raise SystemExit(f"AUD-005 {p.stem}: {info['cambiadas']} cambios != esperado "
                             f"{ESPERADO_CAMBIOS[p.stem]}. Aborta sin escribir nada.")
        if info["transiciones"] != ESPERADO_TRANSICIONES[p.stem]:
            raise SystemExit(f"AUD-005 {p.stem}: transiciones {info['transiciones']} != esperado "
                             f"{ESPERADO_TRANSICIONES[p.stem]}. Aborta sin escribir nada.")
        cambios[p] = out
    return cambios, informe


def aplicar(cambios: dict[Path, pd.DataFrame], destino: Path, informe: dict) -> None:
    manifiesto: dict = {"creado": destino.name, "estado": "en_curso", "informe": informe,
                        "ficheros": {}}
    with ExitStack() as pila:
        for p in cambios:
            pila.enter_context(locked(p))
        for p in cambios:
            if _sha(p) != SHA_PLAN[p]:
                raise SystemExit(f"{p.name} cambio desde la planificacion. Aborta sin escribir.")
        copias: dict[Path, Path] = {}
        for p in cambios:
            rel = p.relative_to(ROOT)
            copia = destino / rel
            copia.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, copia)
            if _sha(copia) != SHA_PLAN[p]:
                raise SystemExit(f"La copia de {rel} no reproduce el SHA. Aborta sin escribir.")
            copias[p] = copia
            manifiesto["ficheros"][str(rel)] = {"sha256_antes": SHA_PLAN[p],
                                                "copia": str(copia.relative_to(ROOT))}
        (destino / "MANIFEST.json").write_text(
            json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
        escritos: list[Path] = []
        try:
            for p, df in cambios.items():
                atomic_write_csv(df, p)
                escritos.append(p)
                manifiesto["ficheros"][str(p.relative_to(ROOT))]["sha256_despues"] = _sha(p)
        except BaseException:
            # Rollback bajo el mismo lock: deja todo como estaba.
            for p in escritos:
                shutil.copy2(copias[p], p)
            manifiesto["estado"] = "revertido"
            (destino / "MANIFEST.json").write_text(
                json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
            raise
    manifiesto["estado"] = "aplicado"
    (destino / "MANIFEST.json").write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="escribir (sin el flag: dry-run)")
    args = ap.parse_args()
    cambios, informe = planificar()
    print(json.dumps(informe, indent=2, ensure_ascii=False))
    if not cambios:
        print("AUD-005: nada que re-graduar (ya aplicado). Nada escrito.")
        return 0
    if not args.apply:
        print("dry-run: nada escrito.")
        return 0
    destino = BACKUP / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    aplicar(cambios, destino, informe)
    print(f"Aplicado. Copias y manifiesto en {destino.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
