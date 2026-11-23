# VALIDATION — ronda `audit-2026-11-22` (remediación)

Entorno: Windows 11, Python 3.14.4. Para no escribir en `logs/` ni en `data/`, pytest se ejecutó siempre con `SQP_LOG_DIR=.codex-tmp/logs -p no:cacheprovider --basetemp=.codex-tmp/...`.

## Línea base (antes de corregir, sobre `9de724f`)

| Comando | Resultado |
|---|---|
| CI `main` (`gh run list`) | Rojo desde el 2026-11-19 (8 runs) |
| CI de la rama `codex/remediacion-auditoria-20261122` @ `9de724f` (run 45015974345) | Las 5 patas de test rojas: AUD-002 y AUD-003 |
| `pytest` de los 2 tests de AUD-002/003 | 2 failed |
| Suite rápida (`not slow and not heavy`, `-x`), hook de cierre | 1 failed (AUD-003), 1.777 passed |
| ruff / mypy | exit 0 / exit 0 |

## Por lote (después)

| ID | Comando | Resultado |
|---|---|---|
| AUD-002 | `tests/test_run_status.py` | 67 passed |
| AUD-003 | `tests/test_measure_goalie_nhl.py`, `test_backtest_parity.py`, `test_backtest_markets.py`, `test_backtest_tuning.py`, `tests/research/test_measure_park_bound_mlb.py` | 97 passed (14 min 31 s) |
| AUD-004 | `tests/test_audit_pipeline_repairs.py -k execution_book` | 5 passed |
| AUD-005 | `tests/settlement` | 135 passed. Fallo previo demostrado (código viejo `void`, nuevo `loss`) |
| AUD-007 | `test_odds_store`, `test_feature_shadow`, `test_odds_cache`, `test_audit_pipeline_repairs` | 47 passed (tras descartar el truncado del escritor, que rompía 2 tests) |
| AUD-008 | `test_calibration_data`, `test_calibrator`, `test_calibration_live` | 86 passed |
| AUD-009 | Test nuevo de huella más 10 ficheros de calibración; `test_health` y 19 consumidores (Fable) | 14 + 194 + 428 passed |
| AUD-010 | `tests/test_degradation.py` | 36 passed |
| AUD-011 | `test_clv`, `test_clv_gate` | 31 passed |
| AUD-012 | `pytest tests -k "segment or pattern or pick_history"` | 98 passed |
| AUD-013 | `test_claude_model_routing`; `validate_claude_model_routing.py`; `sync_agent_instructions.py --check` | 44 passed; OK; synchronized |

## Revisión de Fable previa al commit

Veredicto: **se puede commitear**. Ninguna pieza rechazada.
- AUD-003 y AUD-009: APROBADO CON CAMBIOS.
- Resto: APROBADO. Fable ejecutó 201 passed.

Cambios exigidos, ya aplicados:
- huella en la escritura live directa de `train_calibration(staging=False)`;
- docstring obsoleta en `measure_goalie_nhl.py`.

Cambio opcional, también aplicado: `reason="edge_below_min_no_execution"`.

Tras aplicarlos: 88 passed (pipeline_repairs, huella, calibrator, calibration_live y los 2 tests de paridad del portero).

## Validación global final

| Comando | Resultado |
|---|---|
| `python -m ruff check src scripts tests` | exit 0 |
| `python -m mypy src` | exit 0, 119 ficheros |
| `pytest -q -m "not slow and not heavy"` (suite rápida completa, sin `-x`) | **2.962 passed, 0 failed**, 811 deselected (34 min 45 s) |
| Suite `slow`/`heavy` | No ejecutada localmente en su totalidad; las partes afectadas (paridad y backtest) se ejecutaron arriba. La cubre el CI |
| CI de `main` tras el push | `e23634b` rojo (motivo del log); `aadb9ab` **verde** (run 45091590076) |

Las suites se ejecutaron antes de los últimos retoques de la revisión de Fable (huella en `staging=False`, docstring, `reason` del log). Esos retoques se validaron con el lote acotado de 88 tests, más ruff y mypy.

## Seguimiento tras el push de `e23634b`

- **Fallo:** CI de `e23634b` (run 45077754200) en rojo por `tests/test_revalidation.py::test_price_revoke_logs_reason`, que esperaba `edge_below_min` y recibía `edge_below_min_no_execution`.
- **Causa:** el retoque opcional del motivo del log usaba `math.isfinite(execution)`, que también es NaN en los picks de consenso sin casa de ejecución. El fichero de ese test no estaba en el lote acotado de 88 tests ejecutado después del retoque.
- **Arreglo:** marca explícita `no_execution_quote`, y el test de AUD-004 fija ahora el motivo.
- **Validación:** 210 passed (los 14 ficheros que tocan la revalidación); ruff y mypy limpios.
- **CI del arreglo:** `aadb9ab`, run 45091590076: **todo en verde** (test 3.11–3.14, test-windows, secret-scan, dependency-audit); la issue #8 se cerró sola.
