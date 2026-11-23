---
tags: [objetivos, requisitos, sqp]
creada: 2026-07-08
actualizada: 2026-08-16
---

# Objetivos y requisitos

## EL OBJETIVO (operador, 2026-08-16) — enunciado único y sacrosanto

> «El objetivo sacrosanto del sistema es estimar probabilidades **pregame** para
> todos los partidos, mercados (H2H, spreads y totals) y deportes, con un único e
> innegociable fin: generar ganancias, es decir, ganar dinero mediante las
> apuestas realizadas a partir de los Picks generados por el sistema».

**Esta es la ÚNICA formulación del objetivo.** Por instrucción del operador
(2026-08-16), **toda otra formulación anterior queda derogada** y no gobierna:
ni las versiones previas de este mismo enunciado, ni el texto fundacional de las
seis ligas, ni la directiva del 08-02, ni el criterio de "modo precisión". Lo que
sobreviva de ellas en la bóveda es **registro histórico, no norma**.

Su estructura:

- **Medio:** estimar probabilidades **pregame**.
- **Fin — único e innegociable:** generar ganancias, ganar dinero, con las
  apuestas de los picks propios.
- **Alcance:** *todos* los partidos, *todos* los mercados (`h2h`, `spreads`,
  `totals`), *todos* los deportes.

**"Pregame"** acota el acto de estimar: solo información disponible antes del
comienzo. Incluye el re-precio intradía previo al `commence_time`; **excluye el
in-play**. Es la frontera que ya defiende el guard `captured_at < commence_time`
(KI-019), ahora elevada a definición del objetivo.

**"Único e innegociable"** es excluyente: calibración, Brier, fiabilidad y
auditoría son **instrumentos al servicio del fin**, nunca fines en sí mismos. Y a
la inversa, el fin no se persigue seleccionando por hit rate —eso ya se probó y
perdía por construcción— sino estimando bien. Estimar bien es el único camino;
ganar dinero, el único fin.

> **Consecuencia:** el sistema **no** es "un instrumento de medición barato", como
> lo redefinió la decisión de dirección del 2026-08-05. Existe para generar picks
> que generen ganancias. Ver [[Registro de decisiones]].

> **Lenguaje:** "generar ganancias" es el fin, no un logro. No hay ventaja
> demostrada a la fecha (shadow mode, cinco mediciones sin edge). Nunca redactar
> como si estuviera cumplido.

## Cómo se instrumenta

Plataforma Python de analítica cuantitativa deportiva (MLB, NBA/WNBA, NFL, NHL, soccer multi-liga, tenis ATP/WTA) que:

1. **Estima probabilidades pregame** calibradas por evento y mercado (h2h, spreads, totals).
2. **Detecta edges** contra las cuotas de mercado (The Odds API) separando probabilidad estimada, implícita no-vig, edge y ROI esperado estimado.
3. **Gestiona riesgo** (Kelly fraccionado con caps por apuesta, por día por liga y global; banca dinámica por ledger).
4. **Se audita a sí misma**: liquidación idempotente, ROI realizado por liga/mercado, CLV contra cierre capturado, backtesting walk-forward y validación OOS.

**El objetivo NO es apostar cuanto antes**: es acumular evidencia de ventaja real (CLV mediano positivo + calibración que pase gates OOS) antes de arriesgar capital. Estado actual: [[Estado del proyecto|SHADOW MODE]].

## Requisitos funcionales vigentes

- Run diario orquestado (`DIARIO_COMPLETO.bat`: settle → run encadenado) + captura horaria de cierre + backfill/refresh semanal + OOS mensual. Ver [[Arquitectura/Automatización y operación]].
- Todo pick se registra aunque no sea accionable (stream servido para calibración sin sesgo de selección).
- Promoción de calibradores y salida del shadow mode son **decisiones humanas explícitas**, nunca automáticas.
- Reporte HTML autónomo (sin assets externos) con picks, auditoría, diagnóstico (auto-pausas + segmentos flageados), patrones e historial filtrable.

## Restricciones y reglas duras

- **Disciplina OOS**: ninguna señal/parámetro/calibrador se activa sin batir al baseline fuera de muestra (regla aplicada: abridor MLB rechazado, rest/B2B rechazado, park factor aceptado).
- **Integridad de datos**: raw preservado, append-only, dedup por clave con game_id, nunca rellenar datos ausentes con defaults.
- **Anti-leakage**: features solo con información disponible pregame; validación temporal, nunca splits aleatorios.
- **Cuota de API**: The Odds API con presupuesto limitado; todo gasto de créditos históricos se autoriza explícitamente.
- **Veracidad**: nunca prometer profit; siempre "probabilidad estimada".

## Criterio de éxito (regla de salida del shadow)

**Vigente desde el 2026-08-16: `prediction_gate`** (`configs/default.yaml`, `enabled: true`, default-deny; criterio completo en `docs/research/2026-08-16-preregistro-regla-de-salida.md`; registro `data/bets/prediction_gate.json`, reescrito por `scripts/update_prediction_gate.py`). Un (liga, mercado) recibe stake real solo si:
1. Acumula **n ≥ 300** eventos resueltos desde el inicio de la ventana de validación (2026-08-16), y
2. El **test de signo pareado** del modelo frente al precio sin margen bate al mercado con p < α de Bonferroni (α = 0,000702 con K = 69, registro del 2026-11-22), y
3. El **EV realizado del lado del modelo** es positivo (condición 2 del registro desde el 2026-11-03).

Cada corte tiene **un único test**: si falla, queda `agotado_test_unico`. A 2026-11-22: 0 de 76 cortes aprobados (65 con muestra insuficiente, 11 agotados).

**Histórico, ya no vinculante:** el criterio anterior (CLV mediano positivo sobre ≥30 apuestas con `clv_gate.json`, más un gate de Brier OOS tras ~100 picks) quedó sustituido; `clv_gate.enabled` está en `false`. Ver [[Conocimiento/CLV y selección adversa]]. Corregido el 2026-11-23: esta sección seguía citando el criterio antiguo.
