# FINDINGS — ronda `audit-2026-11-22` (línea base de diagnóstico)

- **Base:** `main` @ `9de724f` (sin pushear).
- **Informe fuente:** `audit/latest/claude/REPORT.md`. El hash está en `MANIFEST.json`.
- **Segunda opinión:** no hubo; solo hay un auditor (Claude). No existe informe OpenAI para esta ronda.
- **Origen de todos los hallazgos:** «exclusivo Claude».
- **Detalle de cada hallazgo** (activación, esperado/observado, causa, prueba): sección 3 del informe fuente. Este fichero no lo duplica.
- **Nota:** `STATUS.md`, `CHANGES.md`, `VALIDATION.md` y `VERIFICATION.md` de este directorio pertenecen a la ronda anterior `audit-2026-11-03`, cuya copia íntegra está en `audit/audit-2026-11-03/`. Sus IDs AUD-### **no** son estos: la identidad completa es `round_id + ID`.

## Defectos confirmados

| ID | Fuente | Título | Sev | Conf | Evidencia | Prio | Origen |
|---|---|---|---|---|---|---|---|
| AUD-001 | CLAUDE-001 (SEC-001, ARC-005, SEC-002) | CI rojo en `main` desde el 2026-11-19: test de `park_bound` acoplado a la configuración viva | MEDIUM | HIGH | REPRODUCED | P1 | Preexistente; corregido en `9de724f` sin pushear |
| AUD-002 | CLAUDE-002 (ARC-001) | `if errorlevel 1` en `DIARIO_COMPLETO.bat:212,238,250` | LOW | HIGH | REPRODUCED | P1 | Regresión de `9de724f` |
| AUD-003 | CLAUDE-003 (ARC-002) | Paridad rota entre `measure_goalie_nhl.py` y el motor walk-forward (pre-registro NHL en curso) | MEDIUM | HIGH | REPRODUCED (causa INFERRED) | P1 | Regresión de `9de724f` |
| AUD-004 | CLAUDE-004 (REV9-001) | La revalidación no revoca un pick sin edge si falta el precio de ejecución | MEDIUM | HIGH | REPRODUCED | P2 | Regresión de `9de724f` |
| AUD-005 | CLAUDE-005 (MKT-001) | En sede neutral con orientación invertida entre feeds, el lado local se anula | MEDIUM | HIGH | REPRODUCED | P2 | Preexistente |
| AUD-006 | CLAUDE-006 (ARC-003) | `game_id` duplicado en `results_*.csv` (alias o fecha) | LOW | HIGH | REPRODUCED | P3 | Preexistente |
| AUD-007 | CLAUDE-007 (REV9-002) | `captured_at` con microsegundos rompe `feature_shadow.capture_store` | LOW | HIGH | STATICALLY_VERIFIED | P3 | Regresión de `9de724f` |
| AUD-008 | CLAUDE-008 (QNT-002) | El dedup del calibrador prefiere la fila liquidada sin `adjusted_probability` | LOW | HIGH | REPRODUCED | P3 | Preexistente |
| AUD-009 | CLAUDE-009 (QNT-001) | Calibradores live no ligados a los `league_params` con los que se validaron | LOW | MEDIUM | STATICALLY_VERIFIED | P3 | Preexistente |
| AUD-010 | CLAUDE-010 (MKT-003) | `roi_flat` de la degradación a `price_decimal`, no a `settle_price` | LOW | HIGH | STATICALLY_VERIFIED | P4 | Preexistente |
| AUD-011 | CLAUDE-011 (MKT-002) | El CLV excluye push/medias, no valida los contratos del cierre y cuenta filas | LOW | MEDIUM | STATICALLY_VERIFIED | P4 | Preexistente |
| AUD-012 | CLAUDE-012 (ARC-004) | Escritura no atómica en `audit/patterns.py:88` y `audit/segments.py:210` | LOW | MEDIUM | STATICALLY_VERIFIED | P4 | Preexistente |
| AUD-013 | CLAUDE-013 (SKL-001, SKL-002) | El enrutador consultivo no reconoce «auditoría integral» ni «promover calibrador» | LOW | HIGH | REPRODUCED | P3 | Preexistente |

## No confirmados

| ID fuente | Título | Estado |
|---|---|---|
| MKT-004 | 1X2 de copas y playoffs con marcador tras la prórroga | NOT_VERIFIABLE (requiere un payload de pago) |
| MKT-005 | Margen de una sola pasada entre `STALE_VOID_DAYS` y `--days-from` | INFERRED |
| SEC-004 | El escáner local de secretos no termina en 60 s | NOT_VERIFIABLE |

## Métricas

- **Confirmados:** 13, de los cuales 0 CRITICAL, 0 HIGH, 4 MEDIUM y 9 LOW.
- **Por prioridad:** P1 = 3, P2 = 2, P3 = 5, P4 = 3.
- **No confirmados:** 3. Descartes relevantes: 14 (sección 6 del informe).
- **Introducidos por el commit sin pushear `9de724f`:** 4, que son AUD-002, AUD-003, AUD-004 y AUD-007.

## Comparación histórica (con `audit-2026-11-03`)

- Los 13 hallazgos son **nuevos** en esta ronda.
- **Persistentes de la ronda anterior:**
  - AUD-007 (2026-11-03) sigue parcial: el historial del Programador de tareas continúa deshabilitado, según el aviso del log del 21-11.
  - AUD-022 (2026-11-03) sigue bloqueado por diseño.
- El resto de los IDs de la ronda anterior no se revalidaron uno a uno en esta ronda: NOT_VERIFIABLE, que no equivale a cierre.
