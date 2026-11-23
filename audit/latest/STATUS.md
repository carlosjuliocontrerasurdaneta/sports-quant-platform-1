# STATUS — ronda `audit-2026-11-22`

| ID | Prio | Remediación | Verificación independiente | Evidencia | Próxima acción |
|---|---|---|---|---|---|
| AUD-001 | P1 | Corregido, pendiente de verificación independiente | Pendiente | CI de `main` **verde** en `aadb9ab` (run 45091590076: test 3.11–3.14, test-windows, secret-scan y dependency-audit en success); issue #8 cerrada automáticamente el 2026-11-23T01:12Z. El run de `e23634b` (45077754200) falló por el retoque del log, corregido en `aadb9ab` | — |
| AUD-002 | P1 | Corregido, pendiente de verificación | Pendiente | `test_run_status.py` 67 passed | — |
| AUD-003 | P1 | Corregido (oráculo de paridad + `neutral_in_estimate`), pendiente de verificación. Enmienda 6 añadida al pre-registro | Pendiente | 97 passed; Fable APROBADO CON CAMBIOS (aplicados) | Operador/sesión: `--parity-only` y `--pre` nuevos sobre el HEAD del commit, con árbol limpio; después el modo completo con `--pre-json` |
| AUD-004 | P2 | Corregido, pendiente de verificación | Pendiente | 5 passed; Fable APROBADO | — |
| AUD-005 | P2 | Corregido (código), pendiente de verificación | Pendiente | 135 passed; fallo previo demostrado | **Operador:** re-liquidar las 28 filas NCAAB ya anuladas (escritura en `data/`) |
| AUD-006 | P3 | No aplicable: falso positivo (dedup por `game_id` ya en `ResultsStore.load`) | Pendiente de confirmar el falso positivo | `results_store.py:52-78` | — |
| AUD-007 | P3 | Corregido (lector ISO8601), pendiente de verificación | Pendiente | 47 passed | — |
| AUD-008 | P3 | Corregido, pendiente de verificación | Pendiente | 86 passed; Fable APROBADO | — |
| AUD-009 | P3 | Corregido (huella + `model_mismatch`), pendiente de verificación | Pendiente | 14 + 194 + 428 passed; Fable APROBADO CON CAMBIOS (aplicados) | **Operador:** revalidar OOS y volver a promover, o retirar, `mlb_spreads` y `wnba_spreads` (sin huella). Residual: `health.py` informa `model_mismatch` como calibrado |
| AUD-010 | P4 | Corregido, pendiente de verificación | Pendiente | 36 passed; Fable APROBADO | — |
| AUD-011 | P4 | **Parcial** (solo `superseded`) | Pendiente | 31 passed; Fable: no adoptar el resto ahora | Decisión registrada, antes de reactivar el gate CLV: incluir push/medias y `validate_book_contracts` al cierre |
| AUD-012 | P4 | Corregido, pendiente de verificación | Pendiente | 98 passed | — |
| AUD-013 | P3 | Corregido, pendiente de verificación | Pendiente | 44 passed; validadores OK | — |

**Estado de la ronda:** remediación aplicada y pendiente de verificación independiente. Esta fase no emite veredicto APTO/NO APTO.
