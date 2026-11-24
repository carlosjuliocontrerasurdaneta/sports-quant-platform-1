"""AUD-009 (ronda audit-2026-11-22): calibrador live ligado a la huella del
modelo de su liga.

Un mapa promovido se valido contra un modelo concreto; si despues cambian los
parametros efectivos del adaptador (MLB: `pitcher_bound` 0 -> 0,05,
`park_bound` 0,10 -> 0,0) el mapa no debe seguir aplicandose sin revalidar.
Las claves LEGACY (sin huella) conservan su comportamiento: se aplican y se
avisa."""
from __future__ import annotations

import json
import logging

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.isotonic import IsotonicRegression

import sqp.calibration.calibrator as cal
from sqp.pipeline import daily

_X = np.linspace(0.01, 0.99, 99)
KEY = "mlb_spreads"


@pytest.fixture(autouse=True)
def models(tmp_path, monkeypatch):
    d = tmp_path / "models"
    (d / "staging").mkdir(parents=True)
    monkeypatch.setattr(cal, "MODELS_DIR", d)
    cal._load_calibrator.cache_clear()
    cal._current_model_fingerprint.cache_clear()
    cal._fingerprint_warned.clear()
    yield d
    cal._load_calibrator.cache_clear()
    cal._current_model_fingerprint.cache_clear()
    cal._fingerprint_warned.clear()


def _iso():
    return IsotonicRegression(out_of_bounds="clip").fit(_X, 0.05 + 0.9 * _X)


def _put_live(key=KEY):
    path = cal._model_path(key, "iso")
    joblib.dump(_iso(), str(path))
    cal._write_hash(path)
    cal._set_best_method(key, "isotonic")


def _stage(key=KEY, fingerprint=None):
    path = cal._model_path(key, "iso", staging=True)
    joblib.dump(_iso(), str(path))
    cal._write_hash(path)
    cal._set_best_method(key, "isotonic", staging=True)
    cal._write_staging_meta(key, n_val=500, n_val_events=200,
                            model_fingerprint=fingerprint)


def _patch_mlb_params(monkeypatch, **over):
    """Simula un cambio de configs/leagues/ratings.yaml para MLB."""
    original = daily._league_meta

    def fake(league):
        meta = original(league)
        if league == "mlb":
            meta = dict(meta)
            meta["league_params"] = {**(meta.get("league_params") or {}), **over}
        return meta

    monkeypatch.setattr(daily, "_league_meta", fake)
    cal._current_model_fingerprint.cache_clear()


def _fp_file(models):
    return models / "calibration_model_fingerprints.json"


PROBS = np.array([0.2, 0.5, 0.8])


def test_state_tuple_includes_model_mismatch():
    assert "model_mismatch" in cal.LIVE_CALIBRATION_STATES
    assert len(set(cal.LIVE_CALIBRATION_STATES)) == 7


def test_fingerprint_uses_canonical_league_config():
    """La huella sale de la MISMA ruta que el run (ratings.yaml), no de los
    defaults del codigo (pitcher_bound=0.35 en la firma del adaptador)."""
    fp, motivo = cal._current_model_fingerprint(KEY)
    assert motivo is None and fp is not None
    assert fp["league"] == "mlb" and fp["family"] == "baseball"
    params = fp["adapter_params"]
    assert params["pitcher_bound"] == 0.05
    assert params["park_bound"] == 0.0
    assert len(fp["sha256"]) == 64


def test_int_and_float_params_fingerprint_equally(monkeypatch):
    base = cal._current_model_fingerprint(KEY)[0]
    _patch_mlb_params(monkeypatch, park_bound=0)          # int 0 == 0.0
    assert cal._current_model_fingerprint(KEY)[0]["sha256"] == base["sha256"]


def test_legacy_key_without_fingerprint_keeps_being_applied(models, caplog):
    """Comportamiento de hoy para mlb_spreads/wnba_spreads: se aplica, con
    WARNING una sola vez por clave y proceso."""
    _put_live()
    assert not _fp_file(models).exists()
    with caplog.at_level(logging.WARNING):
        assert cal.live_calibration_state(KEY, "auto") == "applied"
        out = cal.apply_calibration(PROBS, sport=KEY, method="auto")
        cal.apply_calibration(PROBS, sport=KEY, method="auto")
    assert not np.allclose(out, PROBS)
    avisos = [r for r in caplog.records if "SIN huella" in r.getMessage()]
    assert len(avisos) == 1
    assert cal.model_fingerprint_status(KEY) == ("legacy", None)


def test_promotion_records_fingerprint_and_serves_when_it_matches(models):
    _stage()
    assert cal.promote_calibrators(keys=[KEY]) == [KEY]
    reg = json.loads(_fp_file(models).read_text(encoding="utf-8"))
    assert reg[KEY]["source"] == "promotion"
    assert reg[KEY]["fingerprint"]["adapter_params"]["pitcher_bound"] == 0.05
    # el registro de metodos conserva su formato {clave: metodo}
    assert cal._load_method_registry() == {KEY: "isotonic"}
    assert cal.live_calibration_state(KEY, "auto") == "applied"
    assert not np.allclose(cal.apply_calibration(PROBS, sport=KEY, method="auto"),
                           PROBS)


def test_model_change_after_promotion_degrades_to_raw_and_is_reversible(
        models, monkeypatch, caplog):
    _stage()
    cal.promote_calibrators(keys=[KEY])
    _patch_mlb_params(monkeypatch, park_bound=0.10)
    with caplog.at_level(logging.WARNING):
        assert cal.live_calibration_state(KEY, "auto") == "model_mismatch"
        out = cal.apply_calibration(PROBS, sport=KEY, method="auto")
    assert np.array_equal(out, PROBS)
    msg = [r.getMessage() for r in caplog.records if "DESLIGADO" in r.getMessage()]
    assert len(msg) == 1 and "park_bound: 0.0 -> 0.1" in msg[0]
    # no se borra nada: el registro sigue y, si la config vuelve, se aplica
    assert cal._load_method_registry() == {KEY: "isotonic"}
    monkeypatch.undo()
    monkeypatch.setattr(cal, "MODELS_DIR", models)
    cal._current_model_fingerprint.cache_clear()
    assert cal.live_calibration_state(KEY, "auto") == "applied"


def test_staged_fingerprint_wins_over_promotion_time_config(models, monkeypatch):
    """El candidato se entreno con otra configuracion: la promocion no se
    bloquea (no hay puerta nueva) pero el servicio lo ignora."""
    original = daily._league_meta
    _patch_mlb_params(monkeypatch, pitcher_bound=0.0)    # config del entreno
    entrenado = cal._current_model_fingerprint(KEY)[0]
    monkeypatch.setattr(daily, "_league_meta", original)  # config actual
    cal._current_model_fingerprint.cache_clear()
    _stage(fingerprint=entrenado)
    assert cal.promote_calibrators(keys=[KEY]) == [KEY]
    reg = json.loads(_fp_file(models).read_text(encoding="utf-8"))
    assert reg[KEY]["source"] == "staging"
    assert cal.live_calibration_state(KEY, "auto") == "model_mismatch"


def test_train_calibration_stores_fingerprint_in_staging_meta(models):
    rng = np.random.default_rng(7)
    p = rng.uniform(0.2, 0.8, 400)
    df = pd.DataFrame({"probability": p,
                       "home_win": (rng.uniform(size=400) < p).astype(int)})
    cal.train_calibration(df, sport=KEY, staging=True)
    meta = cal._load_staging_meta(KEY)
    assert meta["model_fingerprint"]["sha256"] == \
        cal._current_model_fingerprint(KEY)[0]["sha256"]


def test_demotion_forgets_the_fingerprint(models):
    _stage()
    cal.promote_calibrators(keys=[KEY])
    assert KEY in json.loads(_fp_file(models).read_text(encoding="utf-8"))
    assert cal.demote_calibrators([KEY], reason="test") == [KEY]
    assert KEY not in json.loads(_fp_file(models).read_text(encoding="utf-8"))


def test_direct_live_write_invalidates_previous_fingerprint(models):
    """Otro mapa escrito a mano en live ya no es el que se valido."""
    _stage()
    cal.promote_calibrators(keys=[KEY])
    cal._set_best_method(KEY, "isotonic")
    assert cal.model_fingerprint_status(KEY) == ("legacy", None)


def test_unreadable_fingerprint_registry_serves_raw_and_is_not_rewritten(models):
    _put_live()
    _fp_file(models).write_text("{no es json", encoding="utf-8")
    assert cal.live_calibration_state(KEY, "auto") == "model_mismatch"
    assert np.array_equal(cal.apply_calibration(PROBS, sport=KEY, method="auto"),
                          PROBS)
    cal._forget_model_fingerprint(KEY)
    assert _fp_file(models).read_text(encoding="utf-8") == "{no es json"


def test_recorded_fingerprint_that_cannot_be_recomputed_is_mismatch(models):
    _put_live("liga_h2h")
    _fp_file(models).write_text(json.dumps(
        {"liga_h2h": {"fingerprint": {"sha256": "a" * 64}}}), encoding="utf-8")
    estado, detalle = cal.model_fingerprint_status("liga_h2h")
    assert estado == "mismatch" and "no calculable" in detalle
    assert cal.live_calibration_state("liga_h2h", "auto") == "model_mismatch"


def test_promotion_without_computable_fingerprint_stays_legacy(models):
    _stage("liga_h2h")
    assert cal.promote_calibrators(keys=["liga_h2h"]) == ["liga_h2h"]
    assert cal.model_fingerprint_status("liga_h2h") == ("legacy", None)
    assert cal.live_calibration_state("liga_h2h", "auto") == "applied"


def test_revalidate_reports_but_never_removes_mismatch_or_legacy(
        models, monkeypatch, caplog):
    _stage()
    cal.promote_calibrators(keys=[KEY])
    _put_live("wnba_spreads")                       # legacy
    _patch_mlb_params(monkeypatch, park_bound=0.10)
    with caplog.at_level(logging.WARNING):
        assert cal.revalidate_live_registry() == []
    assert cal._load_method_registry() == {KEY: "isotonic",
                                           "wnba_spreads": "isotonic"}
    textos = " ".join(r.getMessage() for r in caplog.records)
    assert "DESLIGADO" in textos and "SIN huella" in textos


def test_health_does_not_count_model_mismatch_as_calibrated(models, monkeypatch):
    """Residual de AUD-009 (audit-2026-11-22): `health` informaba como calibrado
    un calibrador en `model_mismatch`, que se sirve en crudo."""
    from sqp.monitoring.health import _live_calibration_markets
    _stage()
    cal.promote_calibrators(keys=[KEY])
    assert _live_calibration_markets(models, "mlb") == ["spreads"]
    _patch_mlb_params(monkeypatch, park_bound=0.10)
    assert cal.live_calibration_state(KEY, "auto") == "model_mismatch"
    assert _live_calibration_markets(models, "mlb") == []


def test_health_still_counts_legacy_key_without_fingerprint(models):
    """Sin huella (legacy) se sigue aplicando, asi que sigue contando."""
    from sqp.monitoring.health import _live_calibration_markets
    _put_live()
    assert _live_calibration_markets(models, "mlb") == ["spreads"]


def test_health_reads_fingerprints_from_its_own_models_dir(models, tmp_path, monkeypatch):
    """Revision Fable 2026-11-24: health debe leer el registro de huellas de su
    `models_dir`, no el de MODELS_DIR global."""
    from sqp.monitoring.health import _live_calibration_markets
    _stage()
    cal.promote_calibrators(keys=[KEY])
    _patch_mlb_params(monkeypatch, park_bound=0.10)        # huella en mismatch
    vacio = tmp_path / "otro_models"
    vacio.mkdir()
    monkeypatch.setattr(cal, "MODELS_DIR", vacio)           # global sin huellas
    assert _live_calibration_markets(models, "mlb") == []


def test_health_unreadable_fingerprint_registry_counts_nothing(models):
    """Registro ilegible: el servicio sirve en crudo, asi que health no cuenta."""
    from sqp.monitoring.health import _live_calibration_markets
    _put_live()
    _fp_file(models).write_text("{no es json", encoding="utf-8")
    assert _live_calibration_markets(models, "mlb") == []
