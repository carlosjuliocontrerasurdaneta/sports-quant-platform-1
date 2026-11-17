# Estado — Sports Quant Platform Superagent

## Objetivo
Poner en verde la suite rápida: `tests/test_claude_model_routing.py:140` exige `model: opus|haiku` en `.claude/agents/*.md`, y los 4 agentes sqp-* declaran `model: inherit` (línea 6).

## Decisiones
- Causa raíz: la fábrica `C:\dev\superagent-architect\src\sqp_agent\compile_team.py:159` (roles) y `:205` (coordinador) escriben `model: inherit` de forma fija; `team.json` no tiene campo de modelo.
- La edición manual de los .md provoca drift en `instalar_sqp.py --check`, porque la fábrica guarda una huella SHA-256 en `.superagente/manifest.json` (`compile_team.py:776-791`).
- Modelo propuesto: `opus` para el coordinador y los 3 especialistas. Fable sigue entrando por el parámetro `model` al delegar.

## Cambios (2026-11-15, sesión normal de Claude Code)
- Fábrica `C:\dev\superagent-architect`: campo opcional `model` por rol y `orchestration.coordinator_model` (valores `inherit|sonnet|opus|haiku`, por omisión `inherit`) validados en `team.py` y usados en `compile_team.py` (`_claude_role`, `_claude_coordinator`). Tests nuevos en `tests/test_team.py` y `tests/test_compile.py`. Sin commit: ese repo ya tenía trabajo ajeno sin commitear (lifecycle.py, architect_cli.py, INSTRUCTIVO.md).
- `team.json`: `"model": "opus"` en los 3 roles y `coordinator_model: "opus"`.
- Reinstalado con `instalar_sqp.py --write`: los 4 `.claude/agents/sqp-*.md` declaran `model: opus`.

## Evidencia
- Fábrica: `pytest -q tests` → 370 passed, 9 skipped.
- `python instalar_sqp.py --check` → ok: true, sin drift, lint sin errores.
- `pytest -q tests/test_claude_model_routing.py` → 44 passed.
- Suite completa del proyecto `pytest -q` → 3713 passed, 1 skipped (exit 0, 67 min).

## Siguiente paso
- HECHO 2026-11-17: commit `9ad5fba` en superagent-architect (solo los hunks del modelo; lifecycle y la regla de evals siguen sin commitear) e instalación versionada en SQP (`358f3ef`).
- Pendientes del operador: `git stash drop stash@{0}`. D1 se mantuvo el 2026-11-17 (resultado MM `7164c14`).
