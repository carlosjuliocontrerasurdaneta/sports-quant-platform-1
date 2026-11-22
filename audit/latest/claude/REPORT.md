# Informe del auditor Claude — ronda `audit-2026-11-22`

- **Fecha:** 2026-11-22 (UTC-3, local).
- **Base:** `main` @ `9de724f`, 1 commit por delante de `origin/main` y sin pushear. Árbol limpio al empezar.
- **Alcance:** auditoría integral del repositorio y de su estado operativo. Es solo lectura: no se modificó código, tests, configuración ni datos.
- **Auditor:** sesión principal `claude-opus-5-5` como coordinadora, con seis revisores delegados de solo lectura por área:
  - commit `9de724f` en el escalón `fable`;
  - cuantitativo y mercados en `opus`;
  - seguridad/CI, instrucciones y arquitectura/datos en `sonnet`.
- **Segunda opinión:** no hubo segundo auditor independiente (OpenAI/Codex). El MCP `codex` no conectó en esta sesión.
- **Contaminación de contexto:** ninguna sobre las conclusiones. Los revisores tenían prohibido leer `audit/`, `audits/`, ESTADO y Obsidian. El coordinador leyó la tabla de estado de la ronda anterior solo después de fijar las conclusiones (paso 7 del contrato).

## 1. Resumen

| Severidad | Confirmados | Inferidos / no verificables |
|---|---|---|
| CRITICAL | 0 | 0 |
| HIGH | 0 | 0 |
| MEDIUM | 4 | 1 (MKT-004) |
| LOW | 9 | 3 |

Por prioridad:
- **P1:** CLAUDE-001, CLAUDE-002 y CLAUDE-003, los tres del CI rojo.
- **P2:** CLAUDE-004 y CLAUDE-005.
- El resto es **P3 o P4**.

Lo esencial:

1. **CI rojo en `main` desde el 2026-11-19.** El último verde es del 2026-11-17. Hay 3 causas, todas confirmadas:
   - El test de investigación de `park_bound` dependía de la configuración viva. El commit local `9de724f` lo corrige, pero sin pushear.
   - Ese mismo `9de724f` introduce **dos regresiones nuevas** que rompen las 5 patas del CI de su rama (run `45015974345`): CLAUDE-002 y CLAUDE-003.
2. **La paridad del instrumento pre-registrado del portero NHL está rota en HEAD** (CLAUDE-003). Es la medición en curso: `--pre #1` se ejecutó sobre `04f3015`. El script aborta de forma segura con «PARIDAD ROTA … no se mide nada». No produce una medición errónea, pero bloquea la ejecución completa hasta que se diagnostique.
3. **Dos defectos MEDIUM de lógica en producción, sin impacto monetario hoy** (stake efectivo 0 y gate cerrado):
   - CLAUDE-004: la revalidación deja de revocar picks sin edge cuando Pinnacle no cotiza. Es una regresión de `9de724f`.
   - CLAUDE-005: el lado local de partidos en sede neutral (NCAAB) se anula en vez de liquidarse. Ya existía antes de `9de724f`.
4. **Sin hallazgos CRITICAL ni HIGH en el núcleo cuantitativo.** No hay leakage temporal en vivo. Las probabilidades son finitas, normalizadas y están en [0,1] sobre 104.636 filas. Los calibradores live no están colapsados. La conversión de cuotas, el no-vig, las líneas de cuarto, Kelly y sus topes y las escrituras atómicas con lock son correctos.

Aprobar estos tests y revisiones no demuestra ventaja predictiva ni rentabilidad.

## 2. Inventario y matriz de cobertura

**Inventario del repositorio:**
- Código: `src/sqp` (119 .py, 20 paquetes), `scripts/` (87 .py, más `research/`, `ai/`, PowerShell y CMD), `tests/` (215 .py, 3.747 tests recogidos).
- Operación: 10 BAT en la raíz; `configs/` con `default.yaml`, `venues.yaml` y `leagues/{ratings,soccer,team_aliases}.yaml`.
- Empaquetado y CI: `pyproject.toml`, `setup.py`, `requirements.lock`, `MANIFEST.in`, `Dockerfile`, `Makefile`, `.github/workflows/ci.yml`.
- Sistema de agentes en `.claude/`: 38 skills, 29 agentes, 8 comandos, 12 hooks cableados y 24 rutas en `model-routing.json`.
- Obsidian, `graphify-out/`, `audit/` y `audits/` (históricos).
- `data/` ocupa unos 2,6 GB (`odds` 2,1 GB) y no está versionada (solo `.gitkeep`).
- Hay 5 tareas programadas `SQP_*`.

| Área | Prio | Estado | Componentes | Método | Validación | Limitaciones |
|---|---|---|---|---|---|---|
| Commit sin pushear `9de724f` | P0 | REVISADA | 42 ficheros del diff | Diff + callers + repro antes/después (fable) | 70 tests passed; repro de REV9-001 | Sin e2e de `feature_shadow` |
| Pipeline de predicción / features / modelos | P0 | REVISADA | `pipeline/probabilities.py`, `daily.py`, `sports/`, `models/`, `configs/` | Lectura + agregados de datos reales | 306 tests passed; 5 scripts de agregados | `features/rest_form.py` y `features/mlb.py` revisados solo en parte (coeficientes a 0) |
| Calibración | P0 | REVISADA | `calibration/*`, registro live, `promotion_log` | Lectura + OOS de los calibradores live | Bootstrap por evento | Muestras pequeñas tras los cambios de modelo |
| Mercados, cuotas y edge | P0 | REVISADA | `markets/`, `providers/odds_*`, `storage/odds_store` | Lectura + conteos sobre 6,55 M filas de cuotas | 500 tests passed | Sin llamadas a la API de pago |
| Liquidación y ledgers | P0 | REVISADA | `settlement/*`, `settled_*`, `graded_*` | Lectura + repro + conteos | Mismo lote de tests | Payload crudo de `/scores` no visto |
| Riesgo y stake | P0 | REVISADA | `risk/`, Kelly, exposición, degradación | Lectura frente a la configuración efectiva | Tests de kelly y exposición | `bankroll.apply_dynamic_bankroll` no revisado en detalle |
| Gates (prediction/CLV) | P0 | REVISADA_PARCIALMENTE | `prediction_gate.py`, `audit/clv.py` | Lectura | Tests de gate | `prediction_gate` después de la línea 540 no revisado |
| Backtesting / walk-forward | P1 | REVISADA_PARCIALMENTE | `backtesting/{engine,roi_engine,availability,tuning}` | Diff + paridad de los scripts de investigación | 2 tests rojos reproducidos | No se ejecutó un walk-forward completo |
| Scripts de investigación pre-registrados | P1 | REVISADA_PARCIALMENTE | `measure_park_bound_mlb`, `measure_goalie_nhl` | Tests y CI | 20 passed / 1 failed | Causa exacta de CLAUDE-003 solo INFERRED |
| Integridad de datos | P1 | REVISADA | `storage/`, `data/historical`, `data/bets` | Agregados programáticos | Duplicados, NaN y tmp contados | `data/odds` revisado solo con conteos |
| Operación diaria (BAT, tareas) | P1 | REVISADA | 10 BAT, 5 tareas `SQP_*`, logs del 21-11 | Lectura + `Get-ScheduledTask` + cola del log | Estado: Diario rc=0 (21-11 12:00), Capture_Close en ejecución, Validate_OOS rc=0 | Historial del Programador deshabilitado |
| CI/CD | P1 | REVISADA | `ci.yml`, runs, issue #8 | `gh run list/view`, logs fallidos | Estado: **rojo** (main y la rama de `9de724f`) | — |
| Seguridad y secretos | P1 | REVISADA | Ficheros rastreados, `.gitignore`, wrappers HTTP | grep + `git ls-files` | secret-scan del CI en verde | Escáner local sin terminar en 60 s |
| Dependencias y empaquetado | P2 | REVISADA_PARCIALMENTE | `pyproject`, lock, `setup.py`, `MANIFEST.in`, Dockerfile | Lectura | dependency-audit del CI en verde | `pip_audit` local no ejecutado; imagen Docker no construida |
| Arquitectura | P2 | REVISADA | Grafo de imports de `src/sqp` | AST + graphify | Colección de pytest correcta | Ciclos solo como deuda |
| Pruebas | P1 | REVISADA_PARCIALMENTE | `tests/`, fragilidad por la configuración viva | Colección + tests por área (~1.100) | Suite completa **NO_VERIFICABLE** (timeout al 34 %, 0 fallos hasta ese punto) | Contención de la máquina |
| Lint / tipos | P2 | REVISADA | `src`, `scripts`, `tests` | ruff, mypy | ruff exit 0; mypy 0 issues (119 ficheros) | — |
| Sistema de skills, agentes y hooks | P2 | REVISADA | `.claude/**`, `AGENTS.md`, `audits/prompts` | Lectura + validadores | sync --check 0, routing 0, 198 tests passed | `settings.local.json` no legible (permiso) |
| Documentación / Obsidian | P3 | EXCLUIDA | Obsidian, docs | — | — | Independencia del diagnóstico; sin cambio de comportamiento |
| Código experimental (`scripts/ai`, ML, Monte Carlo) | P3 | REVISADA_PARCIALMENTE | `ml_train`, `monte_carlo` | Lectura de seeds y splits | — | No está en producción |
| Worktrees y ramas | P3 | REVISADA_PARCIALMENTE | 5 worktrees `agent-*`, rama `codex/remediacion-auditoria-20261122` | `git worktree list` | — | Contenido no auditado |

## 3. Hallazgos confirmados

### CLAUDE-001 — CI rojo en `main` desde el 2026-11-19 (test de investigación acoplado a la configuración viva)

| Campo | Valor |
|---|---|
| Categoría | CI / pruebas |
| Severidad | MEDIUM |
| Confianza | HIGH |
| Evidencia | REPRODUCED |
| Prioridad | P1 |

- **Dónde:** `tests/research/test_measure_park_bound_mlb.py` (versión en `origin/main`) y `scripts/research/measure_park_bound_mlb.py:300`.
- **Activación:** `6ccbca3` (2026-11-19) cambió `park_bound` de 0,10 a 0,0 en producción. El test llamaba a `assert_family_and_params()` sobre la configuración real y el script hace `SystemExit` si la configuración difiere de la base pre-registrada.
- **Observado:** 50 fallos en las 5 patas. 8 runs seguidos rojos en `main` (4632249 … 04f3015) más 1 cancelado. La issue #8 sigue abierta desde el 2026-11-19 sin actividad.
- **Esperado:** el instrumento histórico se prueba con los parámetros congelados, no con los vivos.
- **Estado en HEAD:** `9de724f` congela `FROZEN_LEAGUE_PARAMS` con un monkeypatch (líneas 41-66). En local da 20 passed, pero no está pusheado. Además, HEAD tiene otros dos fallos (CLAUDE-002 y CLAUDE-003), así que **pushear `9de724f` tal cual no pone el CI en verde**.
- **Consecuencia:** con un control rojo durante más de 3 días, cualquier otra regresión queda enmascarada. De hecho, CLAUDE-002 y CLAUDE-003 entraron así.
- **Corrección mínima:** corregir CLAUDE-002 y CLAUDE-003 y pushear juntos. Opcionalmente, que `alerta-ci-rojo` comente en la issue en cada run rojo (SEC-002, observación).
- **Aceptación:** run de CI verde en `main`; la issue #8 se cierra sola.
- **Controles existentes:** job `alerta-ci-rojo` (funcionó: abrió la #8) y `cierre-ci-verde`.
- **Alias:** SEC-001, ARC-005, SEC-002.

### CLAUDE-002 — `9de724f` añade `if errorlevel 1` en `DIARIO_COMPLETO.bat`, contra la regla fijada por test

| Campo | Valor |
|---|---|
| Categoría | Operación / CI |
| Severidad | LOW |
| Confianza | HIGH |
| Evidencia | REPRODUCED |
| Prioridad | P1, por bloquear el CI |

- **Dónde:** `DIARIO_COMPLETO.bat:212`, `:238` y `:250`; la regla está en `tests/test_run_status.py:606`.
- **Observado:** `test_ningun_bat_detecta_fallos_con_if_errorlevel_1` falla en local y en las 5 patas del run `45015974345`.
- **Esperado:** usar `if %ERRORLEVEL% neq 0 goto :error_revision`.
- **Consecuencia:** si `:verify_revision` saliera con un código negativo, la etapa no abortaría. Hoy es improbable, porque usa git; de ahí la severidad LOW. El efecto real es el CI rojo.
- **Corrección mínima:** cambiar esas 3 líneas.
- **Prueba:** el mismo test.
- **Alias:** ARC-001.

### CLAUDE-003 — Paridad rota entre `measure_goalie_nhl.py` y el motor walk-forward tras `9de724f` (pre-registro NHL en curso)

| Campo | Valor |
|---|---|
| Categoría | Cuantitativo / investigación pre-registrada |
| Severidad | MEDIUM |
| Confianza | HIGH en el fallo, MEDIUM en la causa |
| Evidencia | REPRODUCED (fallo); causa INFERRED |
| Prioridad | P1 |

- **Dónde:** `scripts/research/measure_goalie_nhl.py:1038-1040` y `src/sqp/backtesting/engine.py:53,110`.
- **Activación:** `9de724f` añadió `retrospective_starters` al motor (por defecto `False`: titulares disponibles al corte) y en el script lo fija a `arm == "M1"`.
- **Observado:** `tests/test_measure_goalie_nhl.py::test_exhibition_vs_non_nhl_club_gets_factor_one_and_keeps_engine_parity` da `SystemExit: PARIDAD ROTA (moneyline, T-M1, k=1500.0) test: no se mide nada`, en local (21 s) y en las 5 patas del CI.
- **Esperado:** paridad exacta entre el instrumento y el motor.
- **Causa raíz (inferida):** la semántica de los titulares al corte del motor nuevo no coincide con el `treat_lambdas` del brazo M1 en el caso de exhibición contra un club no NHL.
- **Consecuencia:**
  - la ejecución completa (irreversible) del pre-registro del portero NHL abortaría sobre HEAD;
  - el `--pre #1` (`pre1.json`) se hizo sobre `04f3015`, de modo que cualquier ejecución sobre `9de724f` necesita un `--pre` nuevo y probablemente una enmienda, porque cambió el instrumento;
  - no hay riesgo de medición errónea: el aborto es seguro.
- **Corrección mínima:** diagnosticar la divergencia en el test aislado y decidir, con enmienda pre-registrada si cambia el instrumento, si se corrige el script o el motor. No tocar umbrales.
- **Aceptación:** el test pasa; `--parity-only` pasa sobre la instantánea congelada.
- **Autorización:** es de clase escalada (instrumento pre-registrado): Fable revisa antes del commit.
- **Alias:** ARC-002, que pasa de INFERRED a REPRODUCED.

### CLAUDE-004 — La revalidación no revoca un pick sin edge cuando falta el precio de la casa de ejecución (regresión de `9de724f`)

| Campo | Valor |
|---|---|
| Categoría | Pipeline / riesgo |
| Severidad | MEDIUM |
| Confianza | HIGH |
| Evidencia | REPRODUCED (revisor fable, código nuevo frente a anterior) |
| Prioridad | P2 |

- **Dónde:** `src/sqp/pipeline/revalidation.py:326-341`.
- **Activación:** pick con `execution_book=pinnacle` (configuración viva) cuyo snapshot fresco no trae Pinnacle para ese mercado.
- **Observado:**
  - precio 2,0, edge ajustado 0,08, consenso fresco 1,70, `min_edge` 0,02;
  - código nuevo: `reval_action=no_execution_price`, stake 5,0, revoked 0;
  - código anterior: `revoke`, stake 0.
- **Esperado:** revocar si el edge contra el consenso cae por debajo de `min_edge`.
- **Causa:** la rama `NO_EXECUTION_PRICE` hace `continue` antes de evaluar el consenso.
- **Consecuencia:** conserva el stake con edge negativo justo cuando falta la casa de ejecución.
- **Control compensatorio:** el stake total de `candidates_*` es 0 y el gate está cerrado, así que hoy no hay impacto monetario. Sí afecta al registro sombra.
- **Corrección:** evaluar el consenso en esa rama y revocar si `p*consensus-1 < min_edge`.
- **Prueba:** añadir el caso `(None, 1.70, "revoke")` a `tests/test_audit_pipeline_repairs.py:117`.
- **Alias:** REV9-001.

### CLAUDE-005 — En partidos de sede neutral con local y visitante invertidos entre feeds, el lado local se anula en vez de liquidarse

| Campo | Valor |
|---|---|
| Categoría | Liquidación |
| Severidad | MEDIUM |
| Confianza | HIGH |
| Evidencia | REPRODUCED (revisor) + STATICALLY_VERIFIED (coordinador) |
| Prioridad | P2 |

- **Dónde:** `src/sqp/settlement/settle.py:31,44-47` y `src/sqp/settlement/runner.py:128-130`.
- **Causa:** `sel_is_home` se calcula contra el local del feed de scores, pero la guarda de identidad compara contra `row["away"]` del feed de cuotas. Si los feeds invierten la orientación, la selección local de cuotas no casa con ninguno de los dos y sale `void`.
- **Datos:**
  - `graded_ncaab`: 20 anulaciones no `stale_void` (10 eventos, todas del lado local), mientras el visitante y los totals del mismo evento sí se graduaron;
  - `settled_ncaab`: 8 picks anulados igual.
- **Consecuencia:**
  - es definitivo, porque `DEDUP_KEY` no incluye `result`;
  - sesga la muestra de calibración y del gate por lado;
  - con stake real, una pérdida quedaría con pnl 0.
- **Control compensatorio:** stake 0 en producción.
- **Corrección:** `_scores_map` devuelve también el visitante de scores; aceptar la selección si casa con cualquiera de los dos; anular solo si no casa con ninguno.
- **Prueba:** orientación invertida en h2h y spreads, incluida una línea de cuarto.
- **Datos persistidos:** la re-liquidación de las 28 filas es una escritura en `data/` y la decide y ejecuta el operador.
- **Alias:** MKT-001.

### CLAUDE-006 — `game_id` duplicado con alias o fecha distintos en `results_*.csv`; la clave compuesta del almacén no lo detecta

| Campo | Valor |
|---|---|
| Categoría | Integridad de datos |
| Severidad | LOW |
| Confianza | HIGH en el dato |
| Evidencia | REPRODUCED (coordinador) |
| Prioridad | P3 |

- **Dónde:** `src/sqp/storage/results_store.py:18,105,147`.
- **Observado:** grupos de `game_id` duplicados: mlb 15, ncaab 31, wncaab 95 (de 7.221 filas), además de atp 2, wta 3, ligamx 1 y ucl 1. Ejemplo: mlb 716404 aparece el 2023-09-28 y el 2023-10-02, Mets–Marlins 1-0.
- **Consecuencia:** Elo y forma cuentan el partido dos veces. No se midió el efecto en las probabilidades; por eso es LOW.
- **Corrección:** deduplicar por (liga, `game_id`) en la carga, conservando la ingesta más reciente. La reparación de `data/` la hace el operador.
- **Prueba:** sintética, con alias distintos y el mismo `game_id`, que espera 1 fila.
- **Alias:** ARC-003.

### CLAUDE-007 — `captured_at` con microsegundos (`9de724f`) rompe el parseo estricto en `feature_shadow.capture_store`

| Campo | Valor |
|---|---|
| Severidad | LOW |
| Confianza | HIGH |
| Evidencia | STATICALLY_VERIFIED + repro de pandas |
| Prioridad | P3 |

- **Dónde:** escritor en `providers/odds_api.py:276`, `daily.py:966` y `closing_capture.py:200`; lector en `evaluation/feature_shadow.py:331`.
- **Observado:** los ficheros mensuales mezclarán `…T15:00:03+00:00` y `…T15:00:03.123456+00:00`. `pd.to_datetime(..., errors="raise")` lanza `ValueError`.
- **Alcance:** `feature_shadow` no está en las tareas ni en los BAT; falla de forma ruidosa.
- **Corrección:** normalizar a `timespec="seconds"` en `OddsStore.append_snapshot`, lo que preserva el contrato del CSV, o usar `format="ISO8601"` en el lector.
- **Alias:** REV9-002.

### CLAUDE-008 — El dedup del entrenamiento del calibrador prefiere la fila liquidada, que no tiene `adjusted_probability`

| Campo | Valor |
|---|---|
| Severidad | LOW |
| Confianza | HIGH |
| Evidencia | REPRODUCED |
| Prioridad | P3 |

- **Dónde:** `src/sqp/calibration/data.py:148-152,228-235`.
- **Observado:** en 134 de 5.784 filas emparejadas (2,2 %) el objetivo de entrenamiento difiere del que se sirve (hasta 0,14). Se concentran entre el 2026-07-17 y el 2026-09-01, con ajustes activos.
- **Consecuencia:** hoy es casi nula, porque los coeficientes están a 0, pero reaparece en cuanto se active un ajuste.
- **Corrección:** preferir la fila servida o persistir `adjusted_probability` en `BetCandidate`.
- **Alias:** QNT-002.

### CLAUDE-009 — Los calibradores live no están ligados a los parámetros del modelo con los que se validaron

| Campo | Valor |
|---|---|
| Severidad | LOW |
| Confianza | MEDIUM |
| Evidencia | STATICALLY_VERIFIED (el hueco); impacto no demostrado |
| Prioridad | P3 |

- **Dónde:** `src/sqp/calibration/calibrator.py:852,1160-1181`.
- **Hecho:** `mlb_spreads=beta` (promovido en agosto) sigue aplicándose después de `pitcher_bound` (2026-09-26) y de `park_bound` (2026-11-19).
- **Medición tras el cambio:** ΔLL +0,013, IC95 [−0,017; 0,039], n=34 eventos. No es significativo.
- **Corrección:** guardar un hash de los `league_params` en la promoción y degradar a no-op con aviso si no coincide.
- **Alias:** QNT-001.

### CLAUDE-010 — `roi_flat` del monitor de degradación usa `price_decimal`, no `settle_price`

| Campo | Valor |
|---|---|
| Severidad | LOW |
| Evidencia | STATICALLY_VERIFIED |
| Prioridad | P4 |

- **Dónde:** `src/sqp/risk/degradation.py:86-90`.
- **Problema:** con line shopping activo hay dos definiciones distintas de ROI realizado: la del monitor que decide las pausas y la del ledger.
- **Corrección:** usar `_settle_px`.
- **Alias:** MKT-003.

### CLAUDE-011 — El CLV excluye push y medias, no valida los contratos del cierre y cuenta filas, no identidades

| Campo | Valor |
|---|---|
| Severidad | LOW |
| Evidencia | STATICALLY_VERIFIED |
| Prioridad | P4 |

- **Dónde:** `src/sqp/audit/clv.py:72,76`.
- **Control compensatorio:** `clv_gate.enabled=false` (`configs/default.yaml:261`); solo es diagnóstico.
- **Alias:** MKT-002.

### CLAUDE-012 — Escritura no atómica de artefactos derivados

| Campo | Valor |
|---|---|
| Severidad | LOW |
| Evidencia | STATICALLY_VERIFIED |
| Prioridad | P4 |

- **Dónde:** `src/sqp/audit/patterns.py:88` y `src/sqp/audit/segments.py:210`.
- **Alcance:** son ficheros regenerables. La corrección es usar `atomic_write_csv`.
- **Alias:** ARC-004.

### CLAUDE-013 — El enrutador consultivo no reconoce «auditoría integral» ni «promover calibrador»

| Campo | Valor |
|---|---|
| Severidad | LOW |
| Evidencia | REPRODUCED |
| Prioridad | P3/P4 |

- **Dónde:** `.claude/automation/model-routing.json:16-23,296-340`.
- **Observado:** `classify("auditoría integral")` devuelve `default` (sonnet), y «promover calibrador» devuelve `modeling`.
- **Alcance:** solo afecta a `/route-task`. El despacho real exige `model` mediante un hook.
- **Alias:** SKL-001, SKL-002.

## 4. Inferidos / no verificables (no confirmados)

- **MKT-004** (MEDIUM potencial, LOW confianza, NOT_VERIFIABLE): el 1X2 de copas y playoffs podría liquidarse con el marcador tras la prórroga. Nada distingue el marcador a 90'. Afecta a los playoffs MLS en curso y a UCL/UWCL desde febrero. Verificarlo exige ver el payload de `/scores`, que es de pago.
- **MKT-005** (LOW, INFERRED): `STALE_VOID_DAYS=3` frente a `--days-from 3` deja una sola pasada de margen. Dos liquidaciones fallidas seguidas, por ejemplo por caídas de red como KI-076, anularían para siempre un partido jugado. Hoy no hay daño medido.
- **SEC-004** (NOT_VERIFIABLE): `scan_tracked_secrets.py` no terminó en 60 s en local. En CI pasa.
- **Docstring de `availability.result_available_at`:** promete +24 h, pero ResultsStore no carga `start_time`. No es un defecto de decisión demostrable (DISMISSED como defecto; corregir el texto).

## 5. Observaciones (no defectos)

- **Commit sin pushear que corre en producción.** `9de724f` (02:26, 42 ficheros, +1.602/−432) está en `main` local y la tarea de las 12:00 lo ejecutará. Coincide con la rama `codex/remediacion-auditoria-20261122`, cuyo worktree está en `Documents/Codex/2026-11-22/…`. Hay, por tanto, **otra sesión (Codex) haciendo una remediación paralela**. Riesgo de escritores concurrentes sobre los mismos ficheros: coordinar antes de remediar.
- **Principio de independencia del mercado.** `estimated_probability`, edge y stake mezclan un 50 % de no-vig (`market_shrink: 0.5`); `model_probability` es la estimación pura. Es un conflicto ya declarado. En los informes hay que leer `model_probability` para separar la probabilidad estimada de la implícita.
- **Protección local.** No hay hooks de git (`.git/hooks` solo tiene `.sample`). Contra secretos solo protege el CI, y el repo es **público**.
- **Persistente de la ronda anterior:** AUD-007 sigue parcial. El historial del Programador de tareas está deshabilitado (aviso en el log del 21-11) y requiere al operador con permisos elevados. AUD-022 sigue bloqueado por diseño.
- **Ciclos de import entre paquetes** (audit↔pipeline, calibration↔pipeline, etc.): es deuda, sin fallo demostrado.
- **Worktrees.** Hay 5 worktrees `.claude/worktrees/agent-*` de sesiones anteriores y `data/models/feature_shadow_20260915_v2/worker.lock`; no se verificó si hay un proceso vivo.

## 6. Descartes relevantes

- Conversión de cuotas americanas/decimales, probabilidad implícita y no-vig potencial con fallback: correctos.
- Líneas de cuarto, push, half_win/half_loss: correctos.
- Kelly: 0,08, tope por apuesta 0,02, exposición 0,10, cableado.
- Frescura: techo de 90 min y bloqueo de partidos empezados.
- Cierre: último snapshot antes del inicio y posterior a la generación.
- Gate: la unidad es (evento, mercado) y no se infla con duplicados.
- Fuga temporal Elo/descanso/anotación: no se encuentra; se usan solo resultados `completed` y fechas estrictamente anteriores.
- Probabilidades: 0 NaN o fuera de rango y normalización ≤ 1e-4 en 104.636 filas.
- Calibradores live: ninguno constante ni colapsado.
- Contaminación NHL h2h de AUD-003 antigua: 0 grupos afectados después del 2026-10-16.
- `odds_cache` (journal, publicación con lock, idempotencia): sin pérdida ni duplicación.
- Secretos versionados: ninguno. `data/` y `logs/` no se versionan. Todas las peticiones HTTP tienen timeout y ninguna usa `verify=False`.
- Agentes, IDs de modelo y hooks: coherentes, ningún `model: inherit` y validadores en verde.
- Tests que leen `data/predictions/demo`: redirigidos a tmp por `conftest.py:29-32`.

## 7. Validaciones ejecutadas

| Comando | Resultado |
|---|---|
| `ruff check src scripts tests` | exit 0 |
| `mypy src` | exit 0, 119 ficheros sin errores |
| `pytest -q` completo (`--basetemp=.codex-tmp/pytest-aud1122 -x`, timeout 3000 s) | **timeout (124) al 34 %, 0 fallos hasta ese punto** → NOT_VERIFIABLE |
| `pytest` de los 2 tests rojos de HEAD | 2 failed (reproducido) |
| `pytest tests/research/test_measure_park_bound_mlb.py` | 20 passed |
| `pytest` por área (revisores) | 70 + 306 + 500 + 198 passed |
| `pytest --collect-only` | 3.747 tests, exit 0 |
| `sync_agent_instructions.py --check`; `validate_claude_model_routing.py` | exit 0; exit 0 |
| `gh run list/view` (main, 44851668090; rama codex, 45015974345) | rojo; fallos detallados arriba |
| `Get-ScheduledTask SQP*` | 5 tareas; Diario rc=0 el 21-11; próxima a las 12:00 del 22-11 |
| Agregados de datos (duplicados, NaN, rangos, voids) | ver los hallazgos |

Clasificación de los fallos de tests:
- `NEW_REGRESSION`: CLAUDE-002 y CLAUDE-003, introducidos por `9de724f`.
- `PRE_EXISTING_FAILURE`: CLAUDE-001 en `origin/main`, corregido en HEAD.

## 8. Plan priorizado

Ver `audit/latest/BACKLOG.md`.

## 9. Limitaciones

- La suite completa no se completó por la contención de la máquina.
- No hubo segunda opinión independiente.
- No se llamó a APIs de pago.
- No se auditaron los worktrees ni la rama Codex más allá de su HEAD.
- `settings.local.json` no era legible.
- Un revisor escribió por accidente unas líneas INFO en `logs/sqp.log`: dos invocaciones sin `SQP_LOG_DIR`, con `data/` intacto y `git status` sin cambios.
- Los ficheros `CHANGES.md`, `STATUS.md`, `VALIDATION.md` y `VERIFICATION.md` que siguen en `audit/latest/` son de la ronda `audit-2026-11-03`. No se pudieron retirar (permiso denegado) y se conservan íntegros en `audit/audit-2026-11-03/`.
