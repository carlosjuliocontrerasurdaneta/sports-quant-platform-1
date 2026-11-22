# BACKLOG — ronda `audit-2026-11-22`

Consolidar no autoriza a corregir. Cada lote necesita el alcance que autorice el operador.

**Coordinación previa:** hay una remediación paralela de Codex en la rama `codex/remediacion-auditoria-20261122`, con un worktree fuera del repo, sobre el mismo `9de724f`. Antes de editar hay que fijar un único escritor por fichero.

## Lote 1 — Poner el CI en verde (P1)

| Orden | ID | Cambio mínimo | Ficheros | Prueba / aceptación | Autorización |
|---|---|---|---|---|---|
| 1 | AUD-002 | Sustituir `if errorlevel 1` por `if %ERRORLEVEL% neq 0` en 3 líneas | `DIARIO_COMPLETO.bat` | `tests/test_run_status.py::test_ningun_bat_detecta_fallos_con_if_errorlevel_1` en verde; revisión del BAT | Operador. Es un BAT de producción: commitear antes de las 12:00 o tras el run (guarda KI-036) |
| 2 | AUD-003 | Diagnosticar la divergencia de paridad del brazo M1 frente a `retrospective_starters`; corregir el script o el motor sin tocar umbrales | `scripts/research/measure_goalie_nhl.py` y/o `src/sqp/backtesting/engine.py` | El test de exhibición pasa; `--parity-only` pasa sobre la instantánea congelada; nuevo `--pre` antes de la ejecución completa | **Escalado**: instrumento pre-registrado. Revisión de Fable antes del commit; enmienda si cambia el instrumento |
| 3 | AUD-001 | Pushear `9de724f` junto con las correcciones 1 y 2 | — | CI verde en `main`; la issue #8 se cierra sola | Operador (push) |

## Lote 2 — Lógica de producción (P2)

| ID | Cambio mínimo | Ficheros | Prueba / aceptación | Autorización |
|---|---|---|---|---|
| AUD-004 | En la rama `NO_EXECUTION_PRICE`, evaluar el edge frente al consenso y revocar si cae por debajo de `min_edge` | `src/sqp/pipeline/revalidation.py:326-341` | Caso `(None, 1.70, "revoke")` en `tests/test_audit_pipeline_repairs.py:117` | Control de riesgo: confirmar el criterio (Fable, según la clase de gate) |
| AUD-005 | `_scores_map` devuelve también el visitante; la guarda acepta la selección si casa con local o visitante de scores | `src/sqp/settlement/settle.py`, `runner.py` | h2h y spreads con orientación invertida (incluida línea de cuarto) | Cambia la liquidación (contrato persistido): Fable. La re-liquidación de las 28 filas la hace el operador |

## Lote 3 — Mantenimiento (P3)

| ID | Cambio mínimo | Prueba |
|---|---|---|
| AUD-006 | Deduplicar por (liga, `game_id`) en `ResultsStore.load`, conservando la ingesta más reciente | Sintética con alias distintos que espera 1 fila. La reparación de `data/` la hace el operador |
| AUD-007 | Normalizar `captured_at` a `timespec="seconds"` en `OddsStore.append_snapshot` | `capture_store` sobre un CSV con formatos mixtos |
| AUD-008 | Preferir la fila servida en el dedup, o persistir `adjusted_probability` | Test de dedup con adjusted ≠ model |
| AUD-009 | Guardar el hash de los `league_params` en la promoción y degradar a no-op si no coincide | Cambiar `ratings.yaml` deja el calibrador sin aplicar. Toca la política de calibración: Fable |
| AUD-013 | Añadir las keywords a `full-audit` y `calibration-only` | `classify()` devuelve la ruta correcta |

## Lote 4 — Opcional (P4)

| ID | Cambio mínimo |
|---|---|
| AUD-010 | Usar `_settle_px` en `risk/degradation.py:86-90`. Afecta a las pausas: Fable |
| AUD-011 | CLV: filtrar «liquidada y no void», usar el constructor de contratos y deduplicar por identidad |
| AUD-012 | Usar `atomic_write_csv` en `audit/patterns.py` y `audit/segments.py` |

## Pendientes del operador, fuera del código

- Habilitar el historial del Programador de tareas (en un proceso elevado). Persiste desde la ronda anterior.
- Decidir la re-liquidación de AUD-005 y la reparación de los duplicados de AUD-006.
- Verificar MKT-004 (prórroga en el 1X2) con un payload de `/scores` cuando se autorice el gasto.
