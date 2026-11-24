# STATUS — ronda `audit-2026-11-22`

| ID | Prio | Remediación | Verificación independiente | Evidencia | Próxima acción |
|---|---|---|---|---|---|
| AUD-001 | P1 | Corregido, pendiente de verificación independiente | **Verificado-corregido** (2026-11-24, Fable): CI `9054f9c` success, issue #8 cerrada | CI de `main` **verde** en `aadb9ab` (run 45091590076: test 3.11–3.14, test-windows, secret-scan y dependency-audit en success); issue #8 cerrada automáticamente el 2026-11-23T01:12Z. El run de `e23634b` (45077754200) falló por el retoque del log, corregido en `aadb9ab` | — |
| AUD-002 | P1 | Corregido, pendiente de verificación | **Verificado-corregido**: 0 `if errorlevel 1` en BAT; CRLF conforme | `test_run_status.py` 67 passed | — |
| AUD-003 | P1 | Corregido (oráculo de paridad + `neutral_in_estimate`), pendiente de verificación. Enmienda 6 añadida al pre-registro | **Verificado-corregido**: 25 passed, PARIDAD OK, RECHAZA sin re-ejecucion | 97 passed; Fable APROBADO CON CAMBIOS (aplicados) | 2026-11-23: `--parity-only` OK, `--pre` #2 y modo completo sobre `901ba7b`. **Veredicto pre-registrado: RECHAZA** (Fable); `goalie_beta` sigue en 0. Ver `docs/research/2026-11-23-resultado-portero-nhl.md` |
| AUD-004 | P2 | Corregido, pendiente de verificación | **Verificado-corregido** | 5 passed; Fable APROBADO | — |
| AUD-005 | P2 | Corregido (código), pendiente de verificación | **Verificado-corregido** (codigo y datos): 24+10 filas, 0 discrepancias; ver OBS-002/003 | 135 passed; fallo previo demostrado | **Hecho 2026-11-23** (`507a7af`): 34 filas re-liquidadas (24 + 10, 12 eventos; las 28 más 2 eventos del 22-11), Fable APTO CON CAMBIOS aplicados; solo `result`/`pnl`/`flags` cambian frente a la copia `data/backups/repair-aud005-20261123/20261123T210446Z/` |
| AUD-006 | P3 | No aplicable: falso positivo (dedup por `game_id` ya en `ResultsStore.load`) | **No aplicable, confirmado** (reproduccion sintetica, 2026-11-24); ruta alternativa OBS-001 | `results_store.py:52-78` | — |
| AUD-007 | P3 | Corregido (lector ISO8601), pendiente de verificación | **Verificado-corregido** | 47 passed | — |
| AUD-008 | P3 | Corregido, pendiente de verificación | **Verificado-corregido** | 86 passed; Fable APROBADO | — |
| AUD-009 | P3 | Corregido (huella + `model_mismatch`), pendiente de verificación | **Verificado-mitigado**: legacy `mlb_spreads`/`wnba_spreads` pendientes del operador | 14 + 194 + 428 passed; Fable APROBADO CON CAMBIOS (aplicados) | **Operador:** revalidar OOS y volver a promover, o retirar, `mlb_spreads` y `wnba_spreads` (sin huella). Evidencia OOS 2026-11-23: ninguno empeora el crudo (ΔBrier mlb −0,0003, wnba −0,0163; ver Bitácora). Residual `health.py` corregido el 2026-11-24 |
| AUD-010 | P4 | Corregido, pendiente de verificación | **Verificado-corregido** | 36 passed; Fable APROBADO | — |
| AUD-011 | P4 | **Parcial** (solo `superseded`) | **Parcial, abierto P4**: resto antes de reactivar el gate CLV | 31 passed; Fable: no adoptar el resto ahora | Decisión registrada, antes de reactivar el gate CLV: incluir push/medias y `validate_book_contracts` al cierre |
| AUD-012 | P4 | Corregido, pendiente de verificación | **Verificado-corregido** | 98 passed | — |
| AUD-013 | P3 | Corregido, pendiente de verificación | **Verificado-corregido**; OBS-004 informativa | 44 passed; validadores OK | — |

**Estado de la ronda:** verificación independiente 2026-11-24 (Fable 5.2, solo lectura): **APTO CON PENDIENTES**. Ver `VERIFICATION.md`. Pendientes: AUD-011 (P4), decisión del operador sobre AUD-009, OBS-001/002 (P4), historial del Programador y AUD-022.
