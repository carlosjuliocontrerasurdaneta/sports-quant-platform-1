# VERIFICATION — ronda `audit-2026-11-22`

- **Fecha:** 2026-11-24.
- **Verificador:** subagente independiente con Fable 5.2 (`claude-fable-5-2`). Trabajó en solo lectura del proyecto y no implementó nada de esta remediación. Lo despachó la sesión principal, que coordinó la remediación pero no la verifica. La sesión principal transcribe aquí su informe sin cambios de fondo; solo limpia la redacción del recuento.
- **Procedimiento:** `audits/prompts/verificar-remediacion.md` (fuente: `.claude/automation/audit-workflow.md`, «Verificación independiente»). El formato sigue a `audit/audit-2026-11-03/VERIFICATION.md`, archivado.

## Veredicto: APTO CON PENDIENTES

Se aplica la regla 3 del contrato, que es la primera aplicable.

- **No es NO APTO.**
  - Los tres P1 están corregidos con evidencia actual:
    - **AUD-001:** el CI de `main` está verde en `9054f9c` y la issue #8 está cerrada.
    - **AUD-002:** ya no queda ningún `if errorlevel 1` en los BAT versionados.
    - **AUD-003:** la paridad se cumple en los tests, y `--parity-only` dio OK a 1e-12 sobre la instantánea congelada.
  - No hay ninguna regresión confirmada (ningún `REG-###`).
  - No hay ninguna corrección importante con evidencia inválida.
- **No es VERIFICACIÓN INCOMPLETA.** Todos los IDs tienen evidencia actual:
  - 536 tests acotados en verde (511 + 25);
  - reproducciones propias de AUD-006 y AUD-013;
  - comparación de agregados de la re-liquidación de AUD-005 contra su copia;
  - estado vivo de los calibradores (AUD-009);
  - CI completo verde en HEAD.
- **Quedan pendientes menores:**
  - **AUD-011:** parcial, P4. Push, medias y contratos del cierre siguen sin cambios por decisión registrada.
  - **AUD-009:** riesgo residual. `mlb_spreads` y `wnba_spreads` siguen en estado legacy y se aplican sin huella hasta que decida el operador.
  - Dos observaciones LOW/P4 de rutas alternativas (OBS-001 y OBS-002).
  - Persistentes de la ronda anterior: el historial del Programador sigue deshabilitado y AUD-022 sigue bloqueado.
- Este dictamen califica solo la remediación evaluada. No afirma ventaja predictiva ni rentabilidad, y no garantiza la ausencia absoluta de defectos.

## 1. Alcance, base, metodología y limitaciones

### Base

- `main` @ `9054f9c02ce588b20cc66eab2b74484477287052`. El árbol estaba limpio al empezar y al terminar (`git status --porcelain` vacío).
- **Remediación evaluada:** `git log 9de724f..HEAD`. Commits de código y datos:
  - `e23634b`;
  - `aadb9ab`;
  - `507a7af` (script de AUD-005);
  - `9054f9c` (residual de `health.py` en AUD-009, más la documentación del portero NHL).
- **Commits solo de documentación:** `901ba7b`, `f2747b8` y `23eaf86`. Para `901ba7b` y `f2747b8` se comprobó con `git show --stat`. `23eaf86` solo toca la Bitácora de Obsidian.
- `9de724f` es la base del diagnóstico. AUD-001 depende de publicarlo, y se evalúa por el CI.
- **Línea base:** `FINDINGS.md` y `BACKLOG.md` de `audit/latest/`, sin modificar. `CHANGES.md`, `VALIDATION.md` y `STATUS.md` son evidencia secundaria. La fuente de verdad es el código actual.
- Desde `901ba7b` (HEAD de la ejecución del portero) hasta HEAD, en `src/`, `scripts/` y `configs/` solo cambian:
  - `scripts/repair_aud005_20261123.py` (nuevo);
  - `src/sqp/calibration/calibrator.py` y `src/sqp/monitoring/health.py` (residual de AUD-009).

  Ni `measure_goalie_nhl.py` ni `engine.py` cambian después de la ejecución del pre-registro.

### Método por ID

1. Reconstruir la causa original (`FINDINGS.md`, `claude/REPORT.md` §3).
2. Leer el parche (`git diff 9de724f HEAD -- <fichero>`) y sus llamadores (`git grep` sobre `src/` y `scripts/`).
3. Reproducir cuando era seguro. Se usaron scripts propios en el scratchpad, directorios temporales y `SQP_LOG_DIR` fuera de `logs/`.
4. Ejecutar los tests acotados y comprobar cada criterio de aceptación de `BACKLOG.md`.
5. Buscar regresiones, rutas alternativas, síntomas ocultados y fallos trasladados.

### Exclusiones (no son cierres)

- No se ejecutaron los BAT de producción, la medición del portero NHL (prohibido re-ejecutarla: veredicto RECHAZA del 2026-11-23) ni ningún script que escriba en `data/`.
- No hubo llamadas a Odds API ni a servicios de pago, ni escrituras en GitHub, commits o push.
- No se re-ejecutó localmente la suite completa (máquina de 2 núcleos con otra suite corriendo). La evidencia de la suite completa (`pytest -q`, `ruff check src scripts tests` y `mypy src`) es el CI de `9054f9c`.
- MKT-004, MKT-005 y SEC-004 siguen como no confirmados de la línea base; no se revalidaron.

### Limitaciones

- La evidencia de `--parity-only`, del `--pre` #2 y del modo completo de AUD-003 está fuera del repositorio (`C:/dev/sqp-snapshots/portero-nhl-20261121-out/`). Se leyó en solo lectura: `parity2.log` dice PARIDAD OK, el `git_head` de `pre2.json` es `901ba7b` y el SHA-256 de `completo.json` coincide con el declarado. No se re-ejecutó.
- La revisión de Fable previa al commit (VALIDATION.md) es evidencia secundaria no reproducible aquí.
- Solo se leyeron agregados de datos: la comparación programática de AUD-005 y el recuento de `void` residuales por liga.

### Efectos laterales

- Ninguno sobre el proyecto.
- pytest escribió en el scratchpad de la sesión (`verif/bt1` y `bt2`), con `SQP_LOG_DIR` también fuera de `logs/`.
- La reproducción de AUD-006 usó un directorio temporal del sistema, que se borró.

## 2. Estado por ID

| ID | Prio | Estado de verificación | Evidencia | Riesgo residual |
|---|---|---|---|---|
| AUD-001 | P1 | **verificado-corregido** | `gh run list`: el CI de `main` está en success desde `aadb9ab` (run 45091590076) hasta HEAD. Run 45390007237 sobre `9054f9c02ce5…`: success en dependency-audit, secret-scan, test 3.11–3.14, test-windows y cierre-ci-verde. `ci.yml` ejecuta `pytest -q` (suite completa, sin filtros de marcador), `ruff check src scripts tests` y `mypy src`. `gh issue view 8`: CLOSED el 2026-11-23T01:12:07Z. El run de `e23634b` falló, y el implementador declara y explica la causa (motivo del log), corregida en `aadb9ab`. | — |
| AUD-002 | P1 | **verificado-corregido** | `git diff 9de724f HEAD -- DIARIO_COMPLETO.bat`: exactamente 3 líneas, `if errorlevel 1` → `if %ERRORLEVEL% neq 0` en las tres llamadas a `:verify_revision`. `git grep -i "errorlevel 1" -- '*.bat'` no devuelve nada. Fines de línea: el blob es LF (433 líneas, igual que la base) y la copia de trabajo es CRLF (433), conforme a `.gitattributes` (`*.bat eol=crlf`). `:verify_revision` sale con `exit /b 0/1`. `tests/test_run_status.py` pasa (lote A). | — |
| AUD-003 | P1 | **verificado-corregido** | Parche: `_oracle_rows` traduce el centinela `""` de la E5(1) a una identidad sin apariciones (f = 1) y aborta si M2 o la base traen una identidad real. `retrospective_starters=True` en todos los brazos restituye la semántica de `04f3015`. `neutral_in_estimate=False` solo en la llamada de paridad. `walk_forward_backtest` tiene `neutral_in_estimate=True` por defecto y no hay otros llamadores que lo pasen, así que producción no cambia. Tests: exhibición, `test_parity_holds_with_neutral_rows`, `test_oracle_rejects_real_identity_outside_m1`, `test_backtest_parity.py` y `test_audit_backtest_remediation.py`: 25 passed. Aceptación «`--parity-only` sobre la instantánea»: `parity2.log` dice «PARIDAD OK (n=33200 …) a 1e-12». La Enmienda 6 está registrada antes del modo completo; el `--pre` #2 se hizo sobre `901ba7b`; el veredicto pre-registrado es RECHAZA (`completo.json`, SHA-256 `8d31b03b…860c`, verificado). `goalie_beta` no aparece en `configs/` (`git grep`), es decir, vale 0. | La medición no se re-ejecutó (prohibido). La Enmienda 6(a) enumera tres causas pero dice «en los dos casos» (errata de redacción, sin efecto). |
| AUD-004 | P2 | **verificado-corregido** | `revalidation.py`: sin cotización de la casa de ejecución, si `p·consenso − 1 < min_edge` se revoca por el camino normal (precio = consenso, ejecución NaN, `reason="edge_below_min_no_execution"`). En caso contrario se mantiene `no_execution_price`. El caso `(None, 1.70, "revoke")` de `tests/test_audit_pipeline_repairs.py` comprueba `revoked == 1`, `skipped_no_price == 0`, `reval_price == consenso` y el motivo del log. `test_revalidation.py` pasa, incluido el motivo de los picks de consenso (marca `no_execution_quote`, no `isfinite`). | El precio de evaluación sin casa de ejecución es el consenso, una cota optimista frente a `min(consenso, ejecución)`. Para revocar es conservador en el sentido correcto: si ya falla con el consenso, fallaría también con el mínimo. |
| AUD-005 | P2 | **verificado-corregido** (código y datos) | `settle._grade` acepta la selección si es el local de cuotas y el local de `/scores` es el visitante de cuotas; si no casa con ninguno, sigue siendo `void`. Los 4 tests nuevos (h2h, spreads con +9,25 → `half_win`, ningún equipo, tercer equipo) y `tests/settlement` pasan. Comparación propia, en solo lectura, de la copia `data/backups/repair-aud005-20261123/20261123T210446Z/`: <br>• el SHA de la copia es igual a `sha256_antes` del MANIFEST en los 2 ficheros; <br>• `graded_ncaab`: 24 filas cambiadas (12 h2h y 12 spreads, 12 eventos; `void`→`loss` 13, `void`→`win` 11); <br>• `settled_ncaab`: 10 filas (5 h2h y 5 spreads, 5 eventos; `void`→`loss` 6, `void`→`win` 4); <br>• solo difieren `result`, `flags` y `pnl` (`0.0`→`-0.0`, stake 0); <br>• el flag `regrade_aud005` coincide exactamente con las filas cambiadas; <br>• re-graduar con el marcador del MANIFEST y la lógica actual da 0 discrepancias; <br>• las filas posteriores se añadieron después (+100 y +70) y ninguna lleva el flag; <br>• no queda ningún `void` h2h/spreads sin `stale_void` en NCAAB. En el resto de ligas solo quedan `void` de filas `superseded`, por diseño. | El SHA actual ya no es `sha256_despues` porque la liquidación diaria añadió filas después (esperado). Ruta alternativa no cubierta: OBS-002. |
| AUD-006 | P3 | **no aplicable, con evidencia** (falso positivo para producción) | `ResultsStore.load(dedupe_game_id=True)` (por defecto) aplica `_drop_repeated_game_ids` desde la ronda 2026-10-18. Reproducción sintética: alias distintos con el mismo `game_id` y un partido reanudado en dos fechas dan 1 fila cada uno (gana la última fecha/ingesta), y las filas legacy sin `game_id` se conservan. Resultado: 4 filas frente a 6 en crudo. Todos los llamadores de producción (`daily.py:909`, `feature_store`, `settlement/runner`, `pergame`, `patterns`, `team_totals_capture` y `goalie_backfill`) usan el valor por defecto. `dedupe_game_id=False` solo aparece en 3 scripts de investigación congelados con su propia regla. | Ruta alternativa que lee el CSV crudo: OBS-001. El CSV crudo sigue con duplicados por diseño (los datos crudos no se mutan). |
| AUD-007 | P3 | **verificado-corregido** | `feature_shadow.capture_store` parsea `commence_time` y `captured_at` con `format="ISO8601"` y mantiene `errors="raise"`. El test con sellos mixtos pasa. El resto de lectores de `captured_at` (`revalidation`, `clv_movement`, `roi_engine`) ya usaban `format="mixed"`, y `markets.line_movement.instantes_utc` admite sellos mixtos (comprobado). | — |
| AUD-008 | P3 | **verificado-corregido** | `load_calibration_training_history`: la fila liquidada sigue ganando el dedup y conserva su `result`, pero toma `adjusted_probability` de la fila servida con la misma clave (la primera no nula). Si la servida no lo tiene, conserva el suyo. `test_calibration_data.py` (2 tests nuevos), `test_calibrator.py` y `test_calibration_live.py` pasan. | No se re-midió sobre datos el 2,2 % de filas afectadas. |
| AUD-009 | P3 | **verificado-mitigado** | Huella sha256 de los parámetros efectivos del adaptador en `calibration_model_fingerprints.json`: se captura en staging, se copia al promover y se borra en cualquier escritura live. Un mismatch da `model_mismatch` y se sirve en crudo (es reversible). `_CAL_WARN_STATES` incluye `model_mismatch`. Residual de `health.py` corregido en `9054f9c`: `_live_calibration_markets` ya no cuenta un `mismatch` como calibrado. `test_calibration_model_fingerprint.py` (incluidos los tests nuevos de `health`) y `test_health.py` pasan. Estado vivo (lectura): el registro solo tiene `mlb_spreads=beta` y `wnba_spreads=beta`, ambos `legacy` → `applied`. El fichero de huellas todavía no existe, de modo que hoy no cambia ninguna probabilidad servida. | Los dos calibradores legacy se aplican sin verificar el modelo hasta que decida el operador (revalidar y volver a promover, o retirar). La evidencia OOS del 23-11 citada en STATUS no se re-ejecutó. Límites declarados: no detecta cambios de código del adaptador ni de defaults internos ausentes del dict. |
| AUD-010 | P4 | **verificado-corregido** | `degradation_metrics` usa `settle_price` si es finito y > 1, y si no `price_decimal`: la misma regla que `settle._settle_px`. Sin la columna no cambia nada. `test_degradation.py` (test nuevo con 2,2, NaN, 1,0 e inf) pasa. | — |
| AUD-011 | P4 | **parcial (abierto, P4)** | Corregido: `compute_clv` excluye las filas con el token `superseded` (comparación por token, no por subcadena). `test_clv.py` y `test_clv_gate.py` pasan. Sin aplicar, por decisión registrada (veredicto Fable): incluir push y medias, aplicar `validate_book_contracts` al cierre y deduplicar por identidad las filas anteriores a KI-071 sin marca. El control compensatorio sigue vigente (`clv_gate.enabled=false`, solo diagnóstico). | Debe resolverse antes de reactivar el gate CLV. |
| AUD-012 | P4 | **verificado-corregido** | `patterns.build_pick_history` usa `atomic_write_csv`, y `segments.segment_diagnostics_report` usa `atomic_write_bytes` + `atomic_write_csv`. `test_patterns.py` y `test_segments.py` pasan. | — |
| AUD-013 | P3 | **verificado-corregido** | Reproducido con `route_classifier.classify` y la configuración actual: «auditoría integral del repositorio» y «haz una auditoria integral» van a `full-audit`; «promover calibrador …», «promover el calibrador» y «staging de calibrador …» van a `calibration-only`; un caso de control («revisa el bug…») sigue en `bugfix`. `test_claude_model_routing.py` pasa. | Observación informativa en OBS-004. |

**Recuento:**

| Estado | IDs | Total |
|---|---|---|
| Verificado-corregido | AUD-001, 002, 003, 004, 005, 007, 008, 010, 012 y 013 | 10 |
| Verificado-mitigado | AUD-009 | 1 |
| Parcial abierto (P4) | AUD-011 | 1 |
| No aplicable | AUD-006 | 1 |
| Reabiertos | — | 0 |

## 3. Regresiones y hallazgos nuevos

**Regresiones (`REG-###`): ninguna.**

- La suite completa es verde en CI sobre HEAD.
- `neutral_in_estimate` conserva el comportamiento de producción por defecto.
- La guarda de AUD-005 sigue anulando las selecciones que no casan con ningún equipo.
- El motivo del log de AUD-004 ya no se confunde con los picks de consenso: el fallo de `e23634b` está corregido en `aadb9ab` y lo cubre el test.

**Observaciones nuevas (no bloquean):**

| ID | Relación | Sev / Prio | Evidencia | Descripción |
|---|---|---|---|---|
| OBS-001 | AUD-006 (ruta alternativa) | LOW / P4 | STATICALLY_VERIFIED (código); impacto INFERRED, no medido | `evaluation/feature_shadow.py:118-125,244-250` lee `results_{league}.csv` en crudo con `pd.read_csv` y no deduplica los `game_id` repetidos, así que el experimento sombra puede contar dos veces un partido reanudado o renombrado. No está en las tareas ni en los BAT y no afecta a los picks servidos. Opción: reutilizar `ResultsStore._drop_repeated_game_ids`. Como es un protocolo congelado con hash de la fuente, decidir antes si cambia el instrumento. |
| OBS-002 | AUD-005 (ruta alternativa) | LOW / P4 | STATICALLY_VERIFIED (código); impacto no medido | El respaldo de liquidación `runner.exact_history_scores_map` empareja solo el par (local, visitante) **ordenado**. Si un partido de sede neutral con la orientación invertida no llega por `/scores`, no se gradúa por el histórico y expira como `stale_void` a los 3 días. Es conservador (no fabrica resultados), es anterior a la ronda y se relaciona con MKT-005. El script de reparación de AUD-005 sí buscaba la orientación invertida. |
| OBS-003 | AUD-005 (datos) | Informativa | REPRODUCED | Las 19 filas re-liquidadas como `loss` llevan `pnl = -0.0` (stake 0), mientras la copia previa llevaba `0.0`. Es numéricamente igual y coincide con lo que escribe producción (`-row["stake"]` con stake 0). |
| OBS-004 | AUD-013 | Informativa | STATICALLY_VERIFIED | La ruta `calibration-only`, que ahora recibe «promover calibrador», propone `model: sonnet`. Promover un calibrador cambia las probabilidades servidas, una clase que `CLAUDE.md` asigna a la escalada. El enrutador es consultivo, y la promoción exige aprobación humana y `model` en el despacho. Lo evalúa el operador; no es un defecto del hallazgo. |

**Persistentes de la ronda anterior** (fuera de los IDs de esta ronda; no se convierten en cierre):

- Historial del Programador de tareas: `wevtutil gl Microsoft-Windows-TaskScheduler/Operational` da `enabled: false`. Es del operador, en una consola elevada.
- AUD-022 (2026-11-03): `git log --all -- data/backups` sigue mostrando `18826e2` y `f4537f5`, y el repositorio es `PUBLIC`. Sigue bloqueado por decisión del operador.
- La copia nueva `data/backups/repair-aud005-20261123/` está ignorada (`.gitignore:16`), y `git ls-files data` solo lista `.gitkeep`.

## 4. Comandos ejecutados

| Comando | Resultado |
|---|---|
| `git log --oneline 9de724f..HEAD`, `git show --stat` de cada commit, `git status --porcelain` | 7 commits. Árbol limpio al inicio y al final |
| `gh run list --branch main --limit 6`; `gh run view 45390007237 --json headSha,conclusion,jobs` | HEAD `9054f9c`: success, con las 8 tareas en success (alerta-ci-rojo skipped). `e23634b`: failure; `aadb9ab`, `901ba7b` y `23eaf86`: success |
| `gh issue view 8` | CLOSED 2026-11-23T01:12:07Z |
| `git grep -n -i "errorlevel 1" -- '*.bat'` | Sin resultados |
| Recuento de CRLF/LF de `DIARIO_COMPLETO.bat` (copia de trabajo, blob de HEAD y blob de la base) | 433 CRLF en la copia de trabajo; 433 LF en los blobs |
| Script propio de comparación de AUD-005 (solo lectura, agregados) | rc 0. Graded: 24 filas cambiadas. Settled: 10. 0 discrepancias al re-graduar |
| Recuento de `void` h2h/spreads sin `stale_void` (todas las ligas, agregados) | NCAAB 0. En el resto solo `superseded` |
| Reproducción sintética de AUD-006 (directorio temporal) | rc 0. 4 filas frente a 6 en crudo |
| `route_classifier.classify` con 6 prompts | Rutas esperadas (ver AUD-013) |
| `model_fingerprint_status` y `live_calibration_state` sobre el registro vivo (lectura) | `mlb_spreads` y `wnba_spreads`: legacy → applied |
| `python -m ruff check` sobre los 13 ficheros/directorios cambiados | rc 0 («All checks passed!») |
| Lote A: `python -m pytest -p no:cacheprovider` (con `SQP_LOG_DIR` y `--basetemp` fuera del proyecto) sobre `tests/test_run_status.py tests/test_audit_pipeline_repairs.py tests/test_revalidation.py tests/settlement tests/test_feature_shadow.py tests/test_odds_store.py tests/test_calibration_data.py tests/test_calibration_model_fingerprint.py tests/test_health.py tests/test_calibrator.py tests/test_calibration_live.py tests/test_degradation.py tests/test_clv.py tests/test_clv_gate.py tests/test_claude_model_routing.py tests/test_patterns.py tests/test_segments.py -q` | rc 0. **511 passed** (5 min 57 s) |
| Lote B: mismo prefijo, sobre los 3 tests de paridad de `tests/test_measure_goalie_nhl.py` (exhibición, filas neutrales y oráculo), `tests/test_backtest_parity.py` y `tests/test_audit_backtest_remediation.py` | rc 0. **25 passed** (2 min 03 s) |
| Lectura de `C:/dev/sqp-snapshots/portero-nhl-20261121-out/{parity2.log,pre2.json,completo.json}`; `sha256sum completo.json` | PARIDAD OK n = 33.200. `git_head` = `901ba7b…`. Veredicto RECHAZA. El SHA coincide con `8d31b03b…860c` |
| `wevtutil gl …TaskScheduler/Operational`; `git log --all -- data/backups`; `gh repo view --json visibility`; `git check-ignore -v` de la copia de AUD-005 | `enabled: false`; 2 commits; PUBLIC; ignorada |

La suite completa, `ruff check src scripts tests` y `mypy src` no se ejecutaron en local. Su evidencia es el CI de `9054f9c` (success).

## 5. P0/P1 abiertos

Ninguno.

## 6. Próxima acción

1. **Operador:** decidir qué hacer con `mlb_spreads` y `wnba_spreads` (AUD-009): revalidar OOS y volver a promover con huella, o retirarlos.
2. **Antes de reactivar `clv_gate`:** resolver lo que queda de AUD-011 (push y medias, `validate_book_contracts` al cierre, dedup por identidad anterior a KI-071).
3. **Opcional (P4):**
   - OBS-001: deduplicar `game_id` en `feature_shadow`, valorando antes el protocolo congelado.
   - OBS-002: decidir si el respaldo histórico debe aceptar la orientación invertida con la misma guarda de consistencia que usó la reparación.
4. **Persistentes:** habilitar el historial del Programador (consola elevada) y la decisión de AUD-022.
