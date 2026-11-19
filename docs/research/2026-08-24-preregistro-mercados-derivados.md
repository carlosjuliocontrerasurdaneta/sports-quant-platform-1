# Pre-registro — edge del motor en mercados derivados (team_totals, F5)

**Fecha:** 2026-08-24. Escrito y commiteado **antes** de ejecutar cualquier
medición sobre datos, siguiendo la convención de los pre-registros de la regla de
salida (2026-08-16) y de momentum de línea (2026-08-15).

## Por qué

El objetivo del sistema es estimar probabilidades pregame **con el único fin de
ganar dinero** con las apuestas de sus picks. Cinco mediciones sobre el feed
público de líneas principales (`h2h`/`spreads`/`totals`) dan **cero ventaja**
(memoria `sin-ventaja-medida`), y la medición walk-forward de features del
2026-08-24 lo reconfirma: ningún feature pregame actual correlaciona con el
desenlace.

La hipótesis viva —bitácora 2026-08-18— es que la ventaja, si existe, no está en
las líneas principales sino en los **mercados derivados** que los libros precian
con una **fórmula** en lugar de con un modelo:

- **team_totals** (carreras del equipo local / visitante por separado).
- **F5 / first-5-innings** (`h2h_1st_5_innings`, `totals_1st_5_innings`).

Motivo mecánico: el motor MLB ya calcula la **distribución conjunta**
Poisson/NegBin por equipo (`lam_home`, `lam_away` con ajuste de pitcher abridor y
corrección de sobredispersión `dispersion_k`). Los derivados son **funciones
analíticas de esa misma distribución** que el motor ya produce:

- `team_totals` = cola de la marginal `score_pmf(lam_team, dispersion_k)`.
- `F5` aísla las ~5 primeras entradas, dominadas por el **abridor**, que es la
  señal más rica del motor (`fip.py`, `starters.py`) y la que el bullpen diluye en
  el juego completo.

## Restricciones de factibilidad (medidas antes de diseñar)

1. **El motor NO expone hoy estos mercados.** No hay clave de mercado F5 ni
   team_totals en `src/`. team_totals es derivable sin modelo nuevo (es la
   marginal ya calculada); F5 requiere una **lambda de 5 entradas** que no existe.
2. **No hay odds históricas** de F5/team_totals almacenadas. El sondeo del
   2026-08-18 (books=7–9) fue una consulta **en vivo** al API, no dato persistido.
   Sin odds históricas **no se puede medir edge/ROI realizado hacia atrás**.
3. **Desenlaces históricos:** los runs por equipo (`home_score`, `away_score`)
   SÍ están en `data/historical/results_mlb.csv` → team_totals es **calibrable
   walk-forward hoy, gratis**. Los runs por entrada (F5) **no** están → F5 exige
   backfill de line scores por entrada (statsapi), que consume cuota.

Estas restricciones imponen un diseño de **dos fases con gate duro**: nada de
cuota de API hasta que una condición necesaria, medible gratis, se cumpla.

## Fase 0 — condición necesaria: calibración de la marginal (GRATIS, sin API, sin tocar producción)

Un mercado derivado no puede tener edge real si la probabilidad que el motor le
asigna no es fiable. La única pieza medible sin odds es la **calibración de la
marginal por equipo** contra los runs realizados, walk-forward.

**Procedimiento (temporalmente correcto, sin lookahead):** para cada partido MLB,
ajustar el adaptador solo con partidos estrictamente anteriores, obtener
`lam_home`, `lam_away` vía el adaptador real, derivar `P(equipo Over L)` de
`score_pmf(lam, max_score, dispersion_k)` para una rejilla de líneas
`L ∈ {2.5, 3.5, 4.5, 5.5}` por equipo, y liquidar contra `home_score`/
`away_score`.

**Métricas y umbrales, fijados ANTES de correr:**

- **Sesgo** `= P̄(Over) − tasa observada de Over`, por línea. Aprobar si
  `|sesgo| ≤ 0.03` en cada línea con `n ≥ 300`.
- **ECE ≤ 0.05** agregado sobre las cuatro líneas.
- **Skill sobre base rate:** el Brier de `P(Over L)` derivada debe ser
  **≤** el Brier de un baseline de tasa-base (frecuencia histórica de Over L por
  liga, walk-forward). Si el motor no bate a la tasa base, su forma no aporta
  información y el derivado no puede tener edge propio.

**Regla de decisión de Fase 0:**

- **PASA** (los tres umbrales) → la marginal es fiable; se habilita solicitar
  aprobación para la Fase 1 de team_totals.
- **FALLA** → es una **miscalibración de la marginal a corregir**
  (candidatos: `dispersion_k` por línea, nivel de `avg_total`), **no** evidencia
  de edge de mercado. Se registra, se diagnostica, y **no se gasta ni un crédito**.

Fase 0 usa datos históricos pero **no reclama edge**; reclama calibración. Por
tanto no contamina el test de edge fuera de muestra de la Fase 1 (KI-019 intacto).

## Fase 1 — edge forward contra el libro (REQUIERE APROBACIÓN HUMANA + créditos de API)

Solo si la Fase 0 de team_totals PASA. Mide edge real, que exige odds del libro y
por tanto recolección forward.

- **Recolección:** odds de team_totals hacia adelante durante la ventana
  pre-registrada, hasta `n ≥ 300` selecciones graduadas por (equipo-lado). No-vig
  con el devig existente del proyecto. Liquidación por marcador (sin cuota extra).
- **Gate = la MISMA regla de salida ya decidida (2026-08-17), sin caso especial:**
  test de signo pareado de que el modelo **puro** bate al mercado fuera de muestra
  (`n ≥ 300` no empatadas, `p < 0.05`) **y** EV a stake plano `> 0`. El derivado
  entra al gate de predicción como un (liga, mercado) más.
- **Guardarraíles:** `shadow`/stake 0 durante toda la Fase 1; **cero capital
  real**; tope de créditos pre-registrado (`≤ 45 créditos/día`, `≤ 1.400/mes`,
  consistente con el presupuesto de 20.000 del 2026-08-18); F5 **excluido** hasta
  su propia sub-fase.
- **Fuera de muestra:** solo cuentan selecciones con `commence_time`
  estrictamente posterior a la fecha de este pre-registro.
- **CLV** con filtro de frescura (skill `clv-shadow-exit`) como evidencia
  secundaria, no rectora.

## Fase 2 (posterior, doblemente bloqueada) — F5

F5 requiere (a) un **modelo de lambda de 5 entradas** (no existe) y (b) **backfill
de line scores por entrada** para calibrar (consume cuota). Se pre-registra como
motivación pero **no se ejecuta** hasta que Fase 0/1 de team_totals cierre y exista
aprobación explícita para el backfill. Su lambda candidata: la contribución del
abridor prorrateada a 5 entradas, no `5/9 · lam` (el bullpen no entra en F5).

## Hipótesis registradas (para no re-litigar después)

- **H1:** la marginal por equipo (con `dispersion_k` de béisbol) **pasa** la
  Fase 0, porque la misma marginal ya calibra a nivel de total completo tras el
  arreglo de sobredispersión (2026-07-31). Predicción explícita: team_totals PASA.
- **H2:** el edge, si existe, es mayor en **F5** que en team_totals o juego
  completo, porque F5 aísla al abridor. Registrada como la hipótesis motivadora;
  su prueba está bloqueada por datos.
- **H3 (nula, la más probable dado "sin ventaja medida"):** el motor **tampoco**
  tiene edge en team_totals contra el libro → el gate de la Fase 1 queda vacío.
  Registrada de antemano para que un resultado nulo no se re-litigue.

## Criterios de descarte, fijados antes de ver los datos

- Sesgo de Fase 0 grande y unidireccional → **miscalibración a corregir**, no
  señal de mercado. No se avanza a Fase 1.
- **Comparaciones múltiples:** Fase 0 evalúa 4 líneas × 2 lados; Fase 1 hereda la
  postura Bonferroni del gate de predicción vigente.
- Rotura del tope de créditos → **auto-stop** de la Fase 1.
- Un derivado que pase el gate y luego lo pierda no reentra sin revisión humana
  (histéresis), igual que el gate de predicción.

## Lo que este experimento NO promete

Pasar la Fase 0 no es edge; es la condición mínima para que valga la pena gastar
créditos. Pasar la Fase 1 no es rentabilidad garantizada: el edge en derivados
puede evaporarse por line shopping, límites de cuenta y selección adversa, y F5
exige modelado aún no construido. No se promete beneficio en ninguna fase.

## Estado — Fase 1 INICIADA el 2026-09-19

- **Aprobación explícita del gasto:** operador, 2026-09-19 («Sí, hazlo», en
  respuesta a la petición nominal de aprobar la cuota de derivados MLB).
  Cuota al autorizar: 10.979 créditos restantes del mes.
- **Implementación:** `sqp.pipeline.team_totals_capture` +
  `scripts/collect_team_totals_mlb.py`, enganchado best-effort a
  `DIARIO_COMPLETO.bat` (`:lista`). Endpoint por evento de The Odds API
  (`/events/{id}/odds`, mercado `team_totals`, 2 créditos/evento con
  `us,eu`); lista de eventos por `/events` (gratis). Tope 45/día y 1.400/mes
  con auto-stop y contador propio (`data/odds/.team_totals_credits_<día>`).
- **Probabilidad del motor sellada en la captura:** marginal por equipo
  (`score_pmf(lam_equipo)`) con abridores probables adjuntos, la misma
  cantidad que pasó la Fase 0. Solo líneas medias. Solo eventos no comenzados.
- **Primera captura (2026-09-19 01:57Z):** 13 eventos, 244 filas, 6 casas,
  líneas 2,5–6,5, 94 selecciones (evento, equipo, línea, lado), 26 créditos.
  A ese ritmo el `n ≥ 300` del gate se alcanza en ~4 capturas; la temporada
  regular termina el 2026-09-27 y la postemporada añade partidos hasta
  finales de octubre.
- **Liquidación:** `--report` gradúa contra `results_mlb.csv` (sin cuota) y
  muestra el avance; **no decide**. El gate sigue siendo la regla de salida
  del `prediction_gate`, evaluada aparte y con `stake 0` durante toda la fase.
- **F5 (Fase 2) sigue bloqueada**: no se ha ejecutado backfill alguno.

---

## Addenda

Se añaden por commits posteriores, sin editar nada de lo anterior.

### Addendum 2026-11-19 — cambios de régimen del motor MLB durante la Fase 1: `pitcher_bound` 0.0 → 0.05 (2026-09-26) y `park_bound` 0.10 → 0.0 (antes de ejecutar)

Redactado por Fable (rol de pre-registro de `.claude/automation/MODEL_ROUTING.md`), con el formato de los addenda de régimen de `2026-09-25-repreregistro-gate-k52.md`. Se registra **antes** del test de entrada de `mlb|team_totals`, que aún no ha alcanzado n = 300 (n = 110 eventos no empatados el 2026-11-02, según `2026-11-02-repreregistro-gate-k69.md` §2). Después de esas cifras no se ha calculado ninguna victoria, ningún p ni ningún `ev_flat` de este corte. Hoy solo se han contado capturas por instante, sin leer resultados.

La probabilidad que sella la Fase 1 es la marginal pura por equipo, `score_pmf(lam_equipo)`, con `lam` = `adapter._rates` (`src/sqp/pipeline/team_totals_capture.py:345`). Por eso cualquier parámetro que entre en `_rates` cambia directamente la probabilidad sellada y la `d` del gate.

**1. `pitcher_bound` 0.0 → 0.05 (cambio ya ocurrido; este documento no lo tenía registrado).**

- Commit `49a6181`, 2026-09-26T08:09:21-03:00 (11:09:21Z): «feat(mlb): activa el factor del abridor (pitcher_bound 0.0 -> 0.05)», por orden del operador.
- Ya estaba registrado como régimen en el addendum 2026-09-26 de `2026-09-25-repreregistro-gate-k52.md`.
- Desde ese instante, la λ de cada equipo lleva el factor del abridor rival, acotado en ±5 %.
- Recuento de hoy en `data/odds/team_totals_mlb_2026{09,10}.csv` (5.872 filas y 160 eventos, todos con capturas a un solo lado del corte):
  - 92 eventos capturados antes del corte, con el motor sin abridor;
  - 68 eventos capturados después, con abridor 0,05. Entre ellos está la postemporada, que no se gradúa por KI-072.
- Es un recuento de eventos capturados, no de eventos graduados ni no empatados.

**2. `park_bound` 0.10 → 0.0 (cambio futuro).**

- Procede de la medición única de `2026-11-10-preregistro-park-bound-mlb.md`, que dio RECHAZA (commit `63fbb4a`; informe `2026-11-18-resultado-park-bound-mlb.md`).
- La decisión del operador (§16.2 de aquel documento) es `park_bound = 0.0`. La tomó el coordinador por delegación, bajo la autorización total del 2026-11-19.
- Efecto desde el commit que escribe `park_bound: 0.0` en `configs/leagues/ratings.yaml`, en la pausa invernal y antes del Opening Day de 2027. Hasta entonces regía 0,10, desde el 2026-06-22.
- Efecto de primer orden en `team_totals`: el mismo `pf ∈ [0,90; 1,10]` multiplicaba las dos λ.
- La última captura es del 2026-10-28. Todas las capturas de 2027 saldrán del valor nuevo si el commit precede a la primera. Si alguna se capturara antes, entra tal como operó.

**Cómo se tratan las filas.** El test de entrada de `mlb|team_totals` (Fase 1 → gate) se hace sobre todas las selecciones elegibles desde la fecha de este pre-registro, con tres regímenes del motor:

| periodo de captura | abridor | parque |
|---|---|---|
| antes de 2026-09-26T11:09:21Z (commit 49a6181) | 0,0 | 0,10 |
| desde 2026-09-26T11:09:21Z hasta el fin de la temporada 2026 | 0,05 | 0,10 |
| 2027 | 0,05 | 0,0 |

No se separan, no se descartan y no se reponderan por régimen. Se evalúa el sistema tal como operó. Ninguno de los dos addenda se usa para recortar o re-segmentar la ventana, ni para cambiar la unidad.

**Fase 0.** La Fase 0 se cerró con los parámetros que regían cuando se ejecutó. No se repite: ninguna regla de este documento la ata a un valor de parámetro. La cantidad sellada sigue siendo la misma por definición: la marginal `score_pmf(lam_equipo)` con los parámetros vigentes en cada captura. Que la Fase 0 no se haya medido con `pitcher_bound` 0,05 ni con `park_bound` 0,0 se declara como limitación, no como motivo para cambiar nada. Sus umbrales no se reabren.

**Qué no cambia.**

- El gate de la Fase 1: la misma regla de salida, con `n ≥ 300` no empatadas, test de signo pareado y EV a stake plano > 0.
- El α: el vigente cuando llegue a n = 300 (hoy 23/32760, por la enmienda K = 69 del 2026-11-03, con K = 69 contando este corte).
- La ventana: fuera de muestra desde la fecha de este pre-registro.
- La exclusión de la postemporada no graduada (KI-072), los guardarraíles de créditos, el stake 0 y la histéresis.
- H1, H2 y H3 (la H3 nula se mantiene sin predicción nueva), F5 bloqueada y los criterios de descarte.

**No altera ningún criterio.** No se pre-declara ninguna partición por régimen, ni siquiera descriptiva: el test es único y el informe de `--report` no decide. Por tanto este addendum no deja ningún código pendiente.
