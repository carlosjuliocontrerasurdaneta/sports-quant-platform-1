# Re-pre-registro: el prediction gate pasa a K = 69 (68 cortes evaluados + `mlb|team_totals`)

**Fecha:** 2026-11-02.
**Estado:** **VIGENTE desde su commit.** Redactado por el escalón Fable (rol de pre-registro de `.claude/automation/MODEL_ROUTING.md`) bajo la autorización plena del operador del 2026-11-02 (§7). Implementado el mismo día (constantes y referencias de §7).
**Enmendado el 2026-11-03** por `docs/research/2026-11-03-enmienda-gate-k69-alfa-consumido.md` (KI-078): los seis tests gastados a 0,05/52 se cuentan a su α real; α_corte pasa de 0,05/69 = 0,000725 a (0,05 − 6 × 0,05/52)/63 = 0,000702, y la cota de §3.4 se calcula con el α consumido. K = 69 y el techo de 84 no cambian. Las cifras de §3.1, §3.3.2 (punto 2), §3.4 y §4 se conservan como se escribieron y quedan superadas por la enmienda.
**Modifica:** `docs/research/2026-09-25-repreregistro-gate-k52.md`, §3: el valor de K y el techo de re-pre-registro. A través de él modifica también `docs/research/2026-09-04-preregistro-multiplicidad-del-gate.md` §3.1, solo en esos dos números. Todo lo demás de ambos documentos sigue vigente sin cambios, incluidos sus addenda, en particular §3.2 del 2026-09-04: **un solo test de entrada por corte**.

**Nota sobre el nombre del fichero.** El encargo se abrió como «K = 68», que es el número de cortes que evalúa hoy el registro. La decisión de §3.3 añade a K el corte derivado `mlb|team_totals`, cuya entrada en el gate ya estaba pre-registrada. El valor fijado aquí es **K = 69**. El fichero se renombró a `…-k69.md` antes de su commit para que el nombre coincida con el valor fijado.

---

## 1. Por qué

El re-pre-registro del 2026-09-25 fijó K = 52 y aplicó la regla de §3.1 del 2026-09-04 con sus nuevos números (§3.2 de aquel documento):

> «Por encima de 63, ERROR y re-pre-registro antes de que ningún corte nuevo sea elegible. Es la misma regla, con los números nuevos.»

El registro de producción evalúa ahora **68 cortes**. Desde el run del 2026-10-22 (64 cortes) el run diario emite el ERROR «RE-PRE-REGISTRAR el criterio antes de que un corte nuevo alcance n>=300». Con K = 52 y 68 cortes, la cota real del error de familia es 68 × 0,05/52 = **0,0654**, un 31 % por encima del 0,05 declarado y por encima de la cota máxima tolerada (0,0606).

## 2. Estado medido antes de fijar nada

Fuente: `data/bets/prediction_gate.json`, generado el 2026-11-01T15:15Z. Se ha leído sin escribir nada.

```
n_cortes_evaluados = 68 · k_bonferroni = 52 · alpha = 0,000962 · fwer_bound = 0,065385
min_n = 300 · validation_start = 2026-08-16 · 0 permitidos
6 cortes con su test de entrada gastado (agotado_test_unico) · 62 en muestra_insuficiente
```

**Los seis tests ya gastados** (todos rechazados, ninguno con pestillo de aprobación):

| corte | n | victorias | p (test de signo) | ev_flat | `entry_test_at` (UTC) | cortes evaluados ese día |
|---|---:|---:|---:|---:|---|---:|
| `mlb\|h2h` | 350 | 145 | 0,9995 | −0,0310 | 2026-09-25T15:04Z | 52 |
| `mlb\|spreads` | 351 | 180 | 0,3347 | −0,0493 | 2026-09-25T15:04Z | 52 |
| `mlb\|totals` | 343 | 175 | 0,3730 | −0,0505 | 2026-09-26T15:04Z | 52 |
| `ncaaf\|h2h` | 490 | 133 | 1,0000 | +0,4321 | 2026-10-11T15:04Z | 59 |
| `ncaaf\|spreads` | 489 | 248 | 0,3931 | −0,0489 | 2026-10-11T15:04Z | 59 |
| `ncaaf\|totals` | 490 | 240 | 0,6904 | −0,0485 | 2026-10-11T15:04Z | 59 |

La última columna sale de `logs/run_diario.log`. El run de producción calla cuando n ≤ K, informa (INFO) cuando K < n ≤ techo y emite un ERROR por encima del techo. El recuento de producción fue 52 hasta el 2026-09-24, 58–60 entre el 2026-09-30 y el 2026-10-18, 61 el 2026-10-19 y 2026-10-20, 64 desde el 2026-10-22, 67 desde el 2026-10-27 y 68 el 2026-11-01. **Los seis tests se hicieron con el número de cortes dentro de lo pre-registrado** (52 y 59, ambos ≤ 63), así que fueron válidos bajo K = 52. Ninguno se ejecutó en la franja de ERROR.

> `logs/sqp.log*` también contiene evaluaciones con 64 cortes desde el 2026-09-29, en secuencias 63/60/64 separadas por segundos. No proceden del run diario: sus marcas de tiempo no coinciden con las de `entry_test_at` y no se ha identificado su origen. No alteran lo anterior, porque los seis `entry_test_at` corresponden a runs de las 12:04 hora local cuyo recuento está en `run_diario.log`.

**Los más cercanos a n = 300** entre los 62 restantes:

| corte | n | victorias | p | ev_flat |
|---|---:|---:|---:|---:|
| `nhl\|spreads` | 219 | 121 | 0,0685 | −0,0629 |
| `nhl\|totals` | 219 | 106 | 0,7056 | −0,0469 |
| ningún otro | < 200 | — | — | — |

La NHL está en temporada, así que esos dos cortes pueden llegar a n = 300 en semanas. Es el plazo de este documento: debe estar implementado antes de que cualquiera de los dos llegue a n = 300.

**Fuera del registro:** `mlb|team_totals`, el derivado de la Fase 1 de `docs/research/2026-08-24-preregistro-mercados-derivados.md`, se evaluó hoy con la regla canónica (`_decide`, unidad = evento, desde 2026-08-25). Resultado: n = 110 eventos no empatados, 54 victorias, p = 0,612, ev_flat = −0,0543, es decir, `muestra_insuficiente`. La temporada MLB ha terminado. Hay 40 eventos de postemporada capturados que no se gradúan por KI-072 (`results_mlb.csv` solo contiene `gameType` R). Este corte **no** está entre los 68.

## 3. Criterio re-pre-registrado

### 3.1 Bonferroni sobre K = 69

```
α_corte = 0,05 / K        con K = 69 fijado hoy
α_corte = 0,000725        (0,05/69 = 0,00072464)
```

K = 69 se compone de los 68 cortes del registro (seis agotados y 62 en `muestra_insuficiente`) más `mlb|team_totals` (§3.3).

### 3.2 Las cuestiones que había que resolver antes de fijar K

**(a) ¿Se cumple «antes de que ningún corte nuevo sea elegible», aunque seis cortes ya hayan gastado su test?** Sí. La condición protege una propiedad: que el criterio que decide la entrada de un corte esté fijado antes de su único test. Los seis cortes agotados no son nuevos. Se decidieron entre el 2026-09-25 y el 2026-10-11 bajo un criterio vigente y dentro de la tolerancia (§2), y por §3.2 del 2026-09-04 no se vuelven a evaluar sin liberación humana explícita. Este documento no los reabre ni los toca. Ningún corte ha alcanzado n ≥ 300 desde el 2026-10-11, y en particular ninguno lo ha hecho desde el 2026-10-22, cuando el recuento superó el techo. El máximo actual es n = 219. **Ningún corte nuevo es elegible.** La condición se cumple, aunque con un margen de semanas, no de meses.

**(b) ¿Cuentan en K los seis agotados?** Sí, y deben contar. Bonferroni acota la probabilidad de **al menos un** falso positivo en la familia de tests que se realizan bajo el criterio. Esos seis tests se realizaron: cada uno era una oportunidad de falso positivo, que no se materializó. Si se sacaran de K y α se repartiera solo entre los que quedan, el umbral se relajaría (0,05/63 en vez de 0,05/69) **porque** esos seis salieron rechazados. Eso es exactamente re-dividir α según los resultados, lo que prohíbe §3.1 del 2026-09-04. Además pueden volver a la familia: un corte agotado es reentrable tras liberación humana (`release_prediction_gate_latch`), y si eso ocurre su nuevo test debe estar cubierto por el mismo reparto. Por último, el propio código ya los cuenta: `n_cortes_evaluados = len(markets)` incluye los agotados, y K se compara con ese recuento.

**(c) ¿Conocer los p intermedios de cortes no elegibles da ventaja?** No, por dos razones independientes:

1. **El cambio solo endurece.** α baja de 0,000962 a 0,000725. Todo corte que el criterio anterior rechazaba lo rechaza también el nuevo. Endurecer no puede abrir ninguna puerta, así que saber que `nhl|spreads` va con p = 0,0685 a n = 219 no permite elegir un K que lo favorezca: cualquier K ≥ 52 lo perjudica o lo deja igual.
2. **K no se elige mirando p.** Es el recuento de cortes del pipeline más un corte cuya entrada estaba escrita desde el 2026-08-24. Es un hecho de diseño, como lo eran K = 41 y K = 52.

### 3.3 `mlb|team_totals` cuenta ya: K = 69, no 68

Había dos opciones: contarlo ya (K = 69) o dejar que su entrada se absorbiera en la tolerancia hasta el techo. **Se cuenta ya.** Motivos:

1. **Su entrada ya está pre-registrada.** `2026-08-24-preregistro-mercados-derivados.md` dice que «el derivado entra al gate de predicción como un (liga, mercado) más» (l. 94) y que la «Fase 1 hereda la postura Bonferroni del gate de predicción vigente» (l. 128–129). Es un miembro **conocido** de la familia, no un crecimiento imprevisto. La tolerancia hasta el techo existe para lo imprevisto, es decir, las ligas que entran por calendario. Usarla para absorber algo que ya se sabe que entrará es gastar el margen antes de necesitarlo.
2. **Es lo más conservador.** Con K = 68, en cuanto `team_totals` entrara habría 69 cortes y la cota real sería 69 × 0,05/68 = 0,0507, ya por encima del 0,05 declarado desde el primer día. Con K = 69 la cota es exactamente 0,05 cuando entra.
3. **Endurece y no favorece a nadie.** α pasa de 0,000735 (K = 68) a 0,000725. Cuesta una victoria a n = 300 (§4), y lo paga cualquier corte, incluidos los dos de la NHL. Contar `team_totals` no depende de su resultado: va con p = 0,612 y n = 110, lejos de 300. Se contaría igual si fuera ganando.
4. **El criterio para contar es cerrado y no se puede estirar.** K cuenta (i) los cortes del registro de producción y (ii) los cortes cuya entrada al gate está **escrita en un pre-registro vigente** en la fecha de este documento. Hoy solo `mlb|team_totals` cumple (ii). Un corte que aparezca por calendario de temporada no se cuenta por adelantado: entra en la tolerancia, que es su función.

Consecuencia operativa: hasta que `team_totals` entre en el registro, `n_cortes_evaluados = 68 < K = 69`. La franja n ≤ K del candado es silenciosa, así que no hay aviso, y eso es correcto: el reparto cubre de sobra lo evaluado. Cuando entre, n = 69 = K, también sin aviso.

**La medición de `team_totals` no se mueve de su sitio por esto.** Sigue su propio calendario, a n ≥ 300 eventos no empatados con un solo test de entrada (§3.2 del 2026-09-04). Ese test se hará con el α vigente en el momento en que llegue a n = 300, que hoy es 0,05/69. Este documento no cambia la unidad (evento), la ventana ni la exclusión de la postemporada no graduada (KI-072).

### 3.4 Techo para el próximo re-pre-registro: 84 cortes

Se mantienen los dos invariantes con los que el operador confirmó el techo de 63 el 2026-09-25:

- **Misma tolerancia relativa**, 50/41 (+22 % sobre K): ⌊69 × 50/41⌋ = ⌊84,15⌋ = **84**.
- **Cota máxima tolerada que no empeora** respecto de 50 × 0,05/41 = 0,060976:
  - 84 × 0,05/69 = 0,060870 ≤ 0,060976. **Cumple.**
  - 85 × 0,05/69 = 0,061594. No cumple.

**Techo = 84.** Es el máximo que no relaja lo aprobado. A título de comprobación, con K = 68 el techo habría sido 82 (82 × 0,05/68 = 0,060294; 83 daría 0,061029). Se descarta junto con K = 68 (§3.3).

- Hasta 69 cortes: el reparto cuadra y no se emite nada.
- Entre 70 y 84 cortes: se informa la cota real (INFO) y el criterio se aplica tal cual.
- Por encima de 84: ERROR y re-pre-registro antes de que ningún corte nuevo sea elegible. Es la misma regla, con los números nuevos.

### 3.5 Lo que NO cambia

- α de familia 0,05.
- `n ≥ 300` no empatadas.
- La definición de `d`, el modelo puro (`model_probability`) y la exclusión de empates.
- La condición 2 (`EV > 0`).
- La ventana fuera de muestra desde el 2026-08-16.
- **Un solo test de entrada por corte** (§3.2 del pre-registro del 2026-09-04).
- La salida diaria y el pestillo.
- Añadidos hoy:
  - **Los seis tests ya gastados quedan como están.** Su decisión (`agotado_test_unico`, rechazados) se tomó bajo K = 52 y no se recalcula, ni para endurecerla ni para relajarla. Solo vuelven a evaluarse tras liberación humana explícita, y si eso ocurre, con el α vigente en ese momento.
  - **Las reglas de tolerancia y de techo**: la fórmula ⌊K × 50/41⌋ con la comprobación de que la cota no empeora, y la regla de las tres franjas del candado.
  - **Los addenda del 2026-09-26, 2026-09-30 y 2026-10-18** del documento del 2026-09-25 siguen vigentes, con su prohibición de usarlos para recortar o re-segmentar la ventana.
  - **El pre-registro de derivados**: su unidad, su ventana, sus guardarraíles y sus hipótesis H1–H3. Lo único que se fija aquí es que `team_totals` cuenta en K.

## 4. El precio

Victorias pareadas necesarias con el test de signo unilateral (binomial, p = 0,5), recalculadas hoy:

| n | α = 0,000962 (K = 52) | α = 0,000735 (K = 68, descartado) | α = 0,000725 (K = 69) |
|---:|---:|---:|---:|
| 300 | 178 (59,3 %) | 178 (59,3 %) | 179 (**59,7 %**) |
| 500 | 286 (57,2 %) | 287 (57,4 %) | 287 (57,4 %) |
| 1000 | 550 (55,0 %) | 551 (55,1 %) | 551 (55,1 %) |

A n = 300, contar `team_totals` cuesta una victoria (178 → 179). A n = 500 y n = 1000 el precio es el mismo que con K = 68: una victoria más que con K = 52. Se acepta: es el precio de que la cota de familia sea exactamente 0,05 cuando entre un corte que ya sabemos que entrará.

## 5. Predicción registrada

No cambia la predicción del pre-registro del 2026-09-04 (§6 y §9) ni la del 2026-09-25 (§5). Esta última ya se resolvió para MLB: los tres cortes fallaron, con `ev_flat` < 0 y `reason` acabado en `agotado_test_unico`, como se predijo.

Para los dos cortes que llegarán antes a n = 300, se registra hoy, antes de que lleguen:

- **`nhl|totals`** (106/219, p = 0,706, ev_flat = −0,047): **será rechazado por el test de signo**, con `no_bate_al_mercado` en el día del test y `agotado_test_unico` después. Va por debajo del 50 % de victorias. Para pasar a n = 300 necesitaría 73 victorias en las 81 siguientes (90 %).
- **`nhl|spreads`** (121/219, p = 0,0685, ev_flat = −0,063): **será rechazado.** Para pasar a n = 300 necesitaría 179 − 121 = 58 victorias en las 81 siguientes (71,6 %), muy por encima de su ritmo actual (55,3 %). Si aun así pasara el test de signo, se predice que **fallará la condición 2** (`ev_flat` ≤ 0): hoy su EV a stake plano es el más negativo de los dos. Recordatorio de §5 del 2026-09-25: `_decide` evalúa el signo antes que el EV, así que el fallo de la condición 2 se lee en `ev_flat` de la entrada del registro, no en `reason`.
- **`mlb|team_totals`**: se mantiene la H3 de su pre-registro (nula, la más probable). Sin predicción nueva. Su test no llegará antes de la temporada MLB 2027.

Las cifras de 73/81 y 58/81 suponen que el test se ejecuta exactamente a n = 300. Si el primer run con n ≥ 300 cae en un n mayor, el umbral se recalcula con ese n, sin cambiar α.

Si alguno pasara, habrá superado un listón del 59,7 % a n = 300 **y** tendrá EV positivo, y la predicción quedará refutada por escrito.

## 6. Objeciones consideradas

- **«El techo se superó el 2026-10-22 y no se re-pre-registró hasta hoy.»** Es cierto, y es una demora de 11 días. Pero no invalida nada: en ese intervalo ningún corte alcanzó n ≥ 300, así que el criterio fuera de tolerancia nunca decidió un test. La regla dice «antes de que ningún corte nuevo sea elegible», no «el mismo día», y se cumple.
- **«Contar `team_totals` es contar un corte que no existe en el registro.»** Existe en un pre-registro vigente que obliga a que entre (§3.3). La regla de recuento es cerrada: registro + pre-registros vigentes. No admite «cortes que podrían existir».
- **«Seis cortes ya gastados hacen la familia más pequeña de facto.»** Re-dividir α entre los supervivientes es relajar en función de los resultados, y está prohibido (§3.2 b).

## 7. Decisión del operador

- **Base de la orden.** El 2026-11-02 el operador (Carlos) preguntó «¿Cuál es el objetivo del proyecto y qué falta para alcanzarlo?». A la respuesta contestó con la orden textual: **«Haz todo lo necesario para lograrlo. Te otorgo plena autorización para ello.»** Este re-pre-registro se redacta y se declara vigente bajo esa autorización. No hay otra cita del operador sobre este documento.
- [x] **K = 69**: 68 cortes del registro más `mlb|team_totals` (§3.3). Es una decisión de diseño tomada bajo esa autorización.
- [x] **Techo de 84 cortes**: **valor derivado** bajo esa autorización, no confirmado expresamente por el operador, al contrario que el 63 del 2026-09-25. Sale de los mismos dos invariantes que el operador confirmó entonces (§3.4) y es el máximo que no relaja lo aprobado. Si el operador quiere confirmarlo o corregirlo, se registra aquí como tal.
- [ ] Confirmación expresa del operador del techo de 84: pendiente, **no bloqueante**. El techo derivado rige desde el commit.

### Implementación (hecha el 2026-11-02; números de línea anteriores al cambio)

| Regla | Dónde | Cambio |
|---|---|---|
| `α_corte = 0,05/69`, derivado y no escrito a mano | `src/sqp/risk/prediction_gate.py` l. 120 | `PREDICTION_GATE_K = 69` |
| Techo de 84 cortes | `src/sqp/risk/prediction_gate.py` l. 128 | `PREDICTION_GATE_K_REPREGISTRO = 84` |
| Comentarios con K = 52, 0,000962 y 63 | `src/sqp/risk/prediction_gate.py` l. 57, 117–127, 232 (mención histórica: revisar que siga siendo cierta), 578–581, 610 | Citar este re-pre-registro, 0,000725, 84 = ⌊69 × 50/41⌋, y 84 × 0,05/69 = 0,0609 |
| Umbral citado en la documentación operativa | `configs/default.yaml` l. 240–241 y 267–268; `scripts/gate_status.py` l. 25; `.claude/skills/clv-shadow-exit/SKILL.md` l. 54 | `0,05/69 = 0,000725`, K = 69 desde el re-pre-registro del 2026-11-02 (antes 52 y 41). Lo fija `test_ningun_documento_presenta_el_alpha_de_familia_como_umbral_por_mercado` |
| Tests | `tests/test_prediction_gate.py` l. 716 (docstring con 0,000962), l. 918 (comentario «63 con K=52»), l. 942 (`== 63` → `== 84`; la fórmula `K * 50 // 41` sigue igual), l. 948 (docstring con 52 y 63) | Actualizar valores. La lógica de las tres franjas no cambia |
| Skill de salida | `.claude/skills/clv-shadow-exit/SKILL.md` | Ya incluido arriba. Al ser una skill, comprobar que el bloque `## Reglas comunes` no se toca (`test_quant_skills_share_an_identical_common_rules_block`) |

La implementación debe estar en `main` antes del primer run en que `nhl|spreads` o `nhl|totals` alcancen n ≥ 300. Si un run llegara a evaluar uno de ellos antes del commit, su test se haría con 0,05/52, un criterio más laxo y fuera de lo pre-registrado. En ese caso, el corte afectado se registra como incidente: la decisión se anota y no se usa para abrir la puerta.

---

## Addenda

Se añaden por commits posteriores al de este documento, sin editar nada de lo anterior. Los addenda del 2026-09-26, 2026-09-30 y 2026-10-18 del documento del 2026-09-25 siguen vigentes (§3.5).

### Addendum 2026-11-19 — `park_bound` MLB 0.10 → 0.0 (antes de ejecutar)

**Hecho.** La medición única de `docs/research/2026-11-10-preregistro-park-bound-mlb.md` (en adelante PB) dio **RECHAZA** (commit `63fbb4a`; informe `docs/research/2026-11-18-resultado-park-bound-mlb.md` y su JSON). Con ese veredicto, la decisión del operador (PB §16.2) es **`park_bound = 0.0`**, la propuesta de PB §12.3. La tomó el coordinador por delegación, bajo la autorización total del operador del 2026-11-19. La clave se escribe explícitamente y no se borra. Desde el commit que la escribe en `configs/leagues/ratings.yaml`, el factor de parque vale 1,0 en todos los partidos MLB: las dos λ dejan de multiplicarse por el mismo `pf ∈ [0,90; 1,10]` (`src/sqp/sports/adapters.py:213-224`). Hasta ese commit regía 0,10, desde el 2026-06-22. Según PB §13.2, el commit se hace en la pausa invernal, antes del Opening Day de 2027. La última fila MLB servida es del 2026-10-26 (`generated_at`) y no hay partidos MLB hasta 2027, así que todas las filas MLB servidas en 2027 saldrán del valor nuevo. Si alguna fila MLB de 2027 llegara a servirse antes del commit, se registrará tal como operó, sin recortarla.

**Qué cortes toca.** Solo MLB. El gate usa `model_probability`, la probabilidad pura, tanto para `d` como para la condición 2, así que el cambio llega a `d` y a `ev_flat` sin pasar por ningún calibrador:

- **`mlb|totals`**: efecto de primer orden, porque `pf` escala μ = λ_h + λ_a.
- **`mlb|team_totals`**: efecto de primer orden. Su probabilidad es la marginal pura de cada λ (`adapter._rates`, `src/sqp/pipeline/team_totals_capture.py:345`), y esa λ lleva `pf`.
- **`mlb|spreads` y `mlb|h2h`**: efecto de segundo orden. En el criterio 7 de PB, el Δ de log loss fue del orden de 10⁻⁵ a 10⁻⁴ (medido con b_C = 0,05 frente a 0, no con 0,10).

Ningún otro corte cambia. **La definición de `d` no cambia.** Lo que cambia es su valor en las filas servidas desde el commit, porque cambia `model_probability`.

**Cómo se tratan las filas de 2027 frente a las anteriores.**

- **`mlb|h2h`, `mlb|spreads` y `mlb|totals`** gastaron su test único de entrada el 2026-09-25 y el 2026-09-26 (`agotado_test_unico`, §2). Este addendum no los reabre ni recalcula su decisión. Si algún día se liberan (`release_prediction_gate_latch`), el nuevo test se hará sobre la ventana que haya entonces, desde el 2026-08-16. Esa ventana mezcla filas de 2026 bajo 0,10 y filas de 2027 bajo 0,0, y no se recorta. El α de ese test será el vigente y se contará según la enmienda del 2026-11-03, §4.2 y §4.3.
- **`mlb|team_totals`** aún no ha gastado su test. Iba por n = 110 eventos no empatados el 2026-11-02 (§2) y no llegará a n = 300 antes de la temporada 2027. Su test único mezclará los eventos de 2026 bajo 0,10 con los de 2027 bajo 0,0. Al menos unos 150 de los 300 primeros serán del régimen nuevo, aunque los 40 de postemporada de KI-072 llegaran a graduarse. Se evalúa el sistema tal como operó.
- En ningún caso se separan, se descartan ni se reponderan las filas por régimen.

**Lo que no cambia.** K = 69, el techo de 84, α_corte = 23/32760 = 0,000702 y la contabilidad del α consumido (enmienda del 2026-11-03, que este addendum no toca). Tampoco cambian `n ≥ 300`, la unidad (evento), la exclusión de empates, la condición 2, la ventana desde el 2026-08-16, el test único de entrada, el pestillo ni la H3 de `team_totals` (§5). No se añade ningún filtro de población ni ninguna entrada de `INVALID_BEFORE`.

**Precisiones para que la medición siga siendo válida.**

1. La decisión de PB §16.4 sobre el calibrador `mlb_totals` no altera ninguna `d` del gate, porque el gate no lee la probabilidad calibrada. Por ese motivo no necesita otro addendum aquí.
2. Cualquier otro cambio de parámetro MLB antes del Opening Day, por ejemplo uno que salga del seguimiento de PB §13.6, exige su propio addendum antes de que entre en filas servidas.
3. Se registra **antes** de ejecutar ningún test de `mlb|team_totals`. Después de las cifras del 2026-11-02 (§2) no se ha calculado ninguna victoria, ningún p ni ningún `ev_flat` de ese corte.

**No altera ningún criterio**, y queda prohibido usarlo después para recortar o re-segmentar la ventana. Redactado por el escalón Fable (rol de pre-registro de `.claude/automation/MODEL_ROUTING.md`).

**Procedencia de la decisión §16.2 y §16.5 de PB.** Órdenes textuales del operador en la sesión de Claude Code: el 2026-11-18, «Do whatever is necessary to reach that objective. I grant you full authorization to accomplish it»; el 2026-11-19, «Continúa con todas las tareas pendientes. Te otorgo mi autorización para llevarlas a cabo». Con esa delegación se toman las propuestas del pre-registro: `park_bound = 0.0` (§16.2) y el momento del cambio después de MM y antes del Opening Day 2027 (§16.5). Registro: `Obsidian/Bitácora/2026-11-19.md`.
