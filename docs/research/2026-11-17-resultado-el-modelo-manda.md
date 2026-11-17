# Resultado — «el modelo manda»: FALLA, y el modelo sale significativamente PEOR que el mercado

**Fecha:** 2026-11-17. Ejecución única de `--medir` del pre-registro
`2026-08-26-preregistro-el-modelo-manda.md` (en adelante **MM**), con todos sus
addenda, hasta el de fijación de T1 incluido. Salida íntegra:
`2026-11-17-resultado-el-modelo-manda.json`, en este mismo directorio. Todas las cifras de
este documento se han comprobado contra ese JSON.

**Veredicto pre-registrado:** el IC95 de `diff = Brier(p_cal) − Brier(fair)` es
**[+0,01050; +0,01607]**. Queda entero por encima de 0. Según E5, el primario
**FALLA** y se registra además como **«modelo PEOR»**. No hay segmentos elegibles
(m = 0) y la segunda puerta no se calcula. Fila de la regla de adopción del
2026-11-13: **R6**. `market_shrink` sigue en 0,5.

---

## 1. Procedencia

| Elemento | Valor |
|---|---|
| Script | `scripts/research/measure_el_modelo_manda.py`, modo `medir`, exit 0, 142,6 s |
| HEAD al medir | `287984cf5b407ad773f7d077e7dac840b932b2da` (commit del addendum de T1) |
| H_MM (commit que añadió MM) | `d6e2b33f200f9a0aa4f89d35acdfe38af3af8609` (2026-08-26) |
| Commit del addendum E1–E9 | `806606abbb3f209754a2aa3d2283e9227c207163` (2026-10-13) |
| Commit del registro que cruzó N | `e3e5572b5a6c13ed5ec04873153667111ad9487a` (2026-11-17T20:51:54Z) |
| Commit del addendum de T1 | `287984cf5b407ad773f7d077e7dac840b932b2da` |
| Primera línea del registro con n ≥ 3.402 | E = 2026-11-17T20:34:56.565566+00:00, HEAD `603cfa9`, 3.887 eventos, 24.849 picks |
| **T1** | **2026-11-03T20:34:56.565566+00:00** (= E − 14 días; coincide en addendum, registro y JSON) |
| seed / `n_boot` | 42 / 10.000 (`difiere_de_lo_congelado = false`) |
| `git status --porcelain -- src configs scripts/research` | vacío |
| Entorno | Python 3.14.4, pandas 3.0.2, numpy 2.4.4 |

Hash de blob en HEAD y en disco (iguales en los cinco):

| Fichero | Blob |
|---|---|
| `src/sqp/evaluation/edge_information.py` | `6ddb2910d01be89c43cc4323e6025f3987982678` |
| `src/sqp/evaluation/model_vs_market.py` | `2db10cefb234e9ecb24f14fbbca02eb0fbb0b616` |
| `src/sqp/evaluation/bootstrap.py` | `ce7541c4a10fdba465881c3f148efdf72b820f86` |
| `src/sqp/pipeline/probabilities.py` | `012693cf8f8086df8248c45ede34785b475f8096` |
| `scripts/research/measure_el_modelo_manda.py` | `0fcd88eea7a551098e9121c82cf65c1a70a63ed5` |

**Datos.** 44 ficheros `data/calibration/graded_*.csv`: 44 listados, 44 cargados,
ninguno vacío ni faltante, 84.894 filas en total. El SHA-256 de cada uno está en
`procedencia.csv_graded`. Los 44 hashes son **idénticos** a los del `--contar` que
fijó T1 (`procedencia.registro.primera_linea_registro.csv_leidos.graded`): entre el
recuento y la medición no cambió ningún byte del graduado. Filas con
`data_label ≠ "real"`: 0. El filtro es inerte y no hace falta la sensibilidad sin él (E2).

**Comprobaciones previas (E7), sin depender de `result`.**

- ŝ sobre 20.355 primeras servidas con `|a − fair| ≥ 0,02`: mediana **0,5**; fracción
  con |ŝ − 0,5| > 0,05: **0,47 %** (tolerancias: 0,01 y 1 %). `ok = true`. Con solo
  las filas que tienen `adjusted_probability` (15.043), la mediana es 0,5 y la fracción fuera, 0.
- Fracción de primeras servidas con edge inconsistente: 0,0.
- Literales de E6 frente a `configs/default.yaml`: los 11 coinciden (`min_edge` 0,02,
  `max_plausible_edge` 0,075, `uncertainty_penalty` 0,35, `anomaly_edge_gap` 0,06,
  `anomaly_extra_penalty` 0,02, `low_book_penalty` 0,015, `min_books_for_consensus` 2,
  `market_shrink` 0,5, y las tres penalizaciones de M4 en 0,0).
  `Settings.load().risk.market_shrink` efectivo: **0,5**.
- Columna `market_shrink` del graduado: 34.726 valores no nulos, de los que **16
  son distintos de 0,5** (ver §8, amenaza 2).

## 2. Población (E3) y exclusiones

| Paso | Recuento |
|---|---:|
| Filas de entrada | 84.894 |
| Fuera por resultado: `push` / `void` / `half_win` / `half_loss` | 1.240 / 670 / 174 / 174 |
| Fuera por probabilidad ausente o no finita | 19 |
| Filas tras filtros | 82.617 |
| Picks tras colapso (primera servida por `PICK_KEY`) | 30.839 |
| Paso 4: picks con `p_cal ∉ [0,1]` | 0 |
| Paso 4b: picks `nhl\|h2h` anteriores a `ffc5ad3` (AUD-003) | 236 |
| Paso 4c: picks de línea de cuarto anteriores a `c578f52` (AUD-008) | 154 |
| Picks sin corte temporal | 30.449 (4.623 eventos) |
| Paso 5: primera servida posterior a T1 | 5.600 |
| `generated_at` / `start_time` ilegibles en la primera servida | 0 / 0 |
| Primeras servidas no pregame (informativo, no excluye) | 0 |
| **Población medida** | **24.849 picks, 3.887 eventos** |

La aritmética cierra: 82.617 = 84.894 − 2.258 − 19; 30.839 − 0 − 236 − 154 = 30.449;
30.449 − 5.600 = 24.849. El clúster es `event_id`.

Picks servidos con primera servida y `start_time` ≤ T1 que no aparecen en el graduado
(«sin graduar», contados en el `--contar` que fijó T1): **70**, el 0,28 % de la población.
Es dato informativo, no exclusión.

## 3. Test primario

Llamada fijada en E5: `score_model_vs_market(d, by=["_global"], model_col="p_cal",
market_col="implied_probability_novig", n_boot=10000, seed=42)`, con
`p_cal = 2·calibrated_probability − implied_probability_novig`.

| Magnitud | Valor |
|---|---:|
| Picks / eventos | 24.849 / 3.887 |
| Brier de `p_cal` (modelo calibrado sin mercado) | 0,24508 |
| Brier de `fair` (consenso sin vig) | 0,23184 |
| `diff` (negativo = gana el modelo) | **+0,01324** |
| IC95 bootstrap por evento | **[+0,01050; +0,01607]** |

**Decisión literal** (MM, «Test primario», y E5): PASA solo si `brier_diff_hi < 0`.
Aquí `brier_diff_hi = +0,01607`, así que **FALLA**. Como además `brier_diff_lo =
+0,01050 > 0`, se registra como **«modelo PEOR»**. El JSON dice
`decision = "FALLA"`, `modelo_peor = true` y `veredicto_score = "mercado mejor"`.

No es un fallo por falta de muestra. El efecto mínimo de interés era δ = 0,0025. La
estimación puntual es unas 5,3 veces δ y el límite inferior del IC, unas 4,2 veces.
El IC no roza el cero.

Qué mide esto y qué no. El Brier compara probabilidades: la **estimada** por el
modelo (`p_cal`) contra la **implícita sin vig** del consenso (`fair`), sobre el
mismo resultado binario. Este test no mide **acierto** ni **ROI**: la segunda puerta,
que es donde se calcularían, no se ejecuta (§5). Nada de este resultado dice nada
sobre rentabilidad, ni en un sentido ni en otro.

## 4. Secundarios (segmentos con Holm)

**m = 0. No hay secundarios.** Ningún segmento `liga|mercado` llega a 800 eventos en
la población medida. Los mayores, según el registro de T1, son `mlb|h2h` (750),
`mlb|spreads` (750), `mlb|totals` (732) y los tres de `ncaaf` (528–530). El
pre-registro ya preveía en agosto que mlb h2h no alcanzaría su N propio en 2026. Por
E5, con m = 0 no hay familia de Holm, no hay p-valores y S2 y SP quedan vacíos.

## 5. Segunda puerta (ROI)

**No se calcula.** E6 la aplica solo a unidades que pasaron la primera puerta, y
ninguna la pasó: el global falla y no hay segmentos. Por tanto este informe no tiene
ROI esperado, ROI realizado, acierto ni probabilidad prometida media de ninguna
política. Tampoco se calcula la sensibilidad de la regla simple de E6, que cuelga de
esta puerta.

## 6. Sensibilidades — **sin poder de decisión**

| Sensibilidad | Unidad | n | `diff` | IC95 | Clase |
|---|---|---|---:|---|---|
| Todas las servidas, sin colapsar (addendum de unidad) | filas | 69.386 filas, 3.887 eventos | +0,01295 | [+0,01003; +0,01590] | entero > 0 |
| Sin corte T1 (todo lo graduado al medir) | picks | 30.449 picks, 4.623 eventos | +0,01654 | [+0,01383; +0,01922] | entero > 0 (FALLA) |

Las dos caen en la misma clase que el primario. No hay discrepancia que informar en
el sentido del addendum de unidad. No se usan para nada más.

## 7. Qué implica según la regla de adopción del 2026-11-13

La regla (`2026-11-13-regla-adopcion-tras-mm.md`, commiteada antes de medir) asigna
el desenlace P = PEOR, G2 no evaluada y S2 vacío a la **fila R6**:

- **`market_shrink`: 0,5, sin cambio.** Un `s` mayor que 0,5 solo puede salir del
  pre-registro de peso del mercado por segmento (PM), con su procedimiento y su
  aprobación expresa. MM («Si el modelo sale significativamente PEOR…») lo deja como
  argumento que exige pre-registro propio, no como acción.
- **Resto de parámetros (§1.3):** `uncertainty_penalty`, `anomaly_*`, `low_book_penalty`,
  `min_edge`, `max_plausible_edge`, `prediction_gate`, monitor de degradación y
  `picks.mode` siguen igual. M4 sigue en 0,0. `park_bound` lo gobierna su propio
  pre-registro, que ya puede ejecutarse con este resultado commiteado.
- **La tesis queda cerrada para esta temporada y esta configuración** (MM, «Si
  falla»). No se reabre cambiando segmento, métrica o ventana. No se re-mide MM.
- **Independencia del mercado (§2 y D1).** En R6 la estimación cumple el principio y la
  decisión sigue mezclando al 50 %. Según D1, tal como se resolvió por delegación el
  2026-11-13, el principio se da por cumplido cuando `cal(p_adj)` congelada se
  registre y se muestre como la estimación y la mezcla quede etiquetada como política
  de decisión posterior. Esa tarea sigue pendiente. Este informe no decide la política
  de mercado: la regla ya estaba fijada y la vía alternativa (`s = 0` «por orden»,
  contra el resultado) es del operador. **Aviso:** la regla dice que D1 es revocable
  por el operador «solo antes del commit del resultado de MM». El commit de este
  fichero cierra esa ventana.

Lectura honesta, sin poder de decisión: con `s = 0` la probabilidad servida sería
peor como estimación que el consenso sin vig, y no por poco. Eso no quiere decir que
el modelo no aporte nada. Mide la población del stream servido frente a un consenso
de muchas casas, y el texto de MM ya advertía que las mediciones previas iban en esa
dirección (Brier +0,00248 en julio, escalera de `min_edge`) y que por convexidad
`diff(p_cal) ≥ 2·diff(mezcla)` fila a fila.

## 8. Amenazas y limitaciones declaradas

1. **Redondeo a 4 decimales** (amenaza 1): error de `p_cal` del orden de 1,5·10⁻⁴,
   dos órdenes por debajo de δ y de la distancia del IC a 0.
2. **`s = 0,5` en las filas** (amenaza 2). E7 pasa. Aun así, el graduado tiene 16
   filas con `market_shrink = 0,0`: 12 en `ncaab` y 4 en `wncaab`, generadas entre el
   2026-10-31 y el 2026-11-14. En esas filas, `p_cal = 2·cal − fair` no reconstruye
   lo servido. Recuento programático de este informe: solo **1** de ellas tiene
   `generated_at ≤ T1` (`ncaab`, un evento), así que como mucho afecta a 1 de 24.849
   picks. Ese pick no puede mover un IC que empieza en +0,0105. Se declara. No se
   corrige, porque E3 no prevé esa exclusión.
3. **Deriva del calibrador** (amenaza 3): el test evalúa el sistema tal como operó, con
   los reentrenos y los cambios de régimen registrados en los addenda (`pitcher_bound`
   MLB, descanso NBA, alias, `tilt_scale` NHL, AUD-001/002/008, `execution.books`). Ninguno
   se usa para recortar la ventana.
4. **Rival**: el consenso sin vig del feed público. Las filas `nhl|h2h` con no-vig falso
   están excluidas (4b). Los mercados finos (`casas < 10`) no tienen tratamiento
   propio (MM, «Lo que NO prueba»).
5. **Población**: una ventana del 2026-07 al 2026-11 con mezcla de regímenes
   deportivos (MLB, fútbol, tenis, NCAAF, NFL, NHL, NBA). No se ha comprobado que el
   resultado se sostenga por deporte: con m = 0 no hay test segmentado, y mirar
   segmentos ahora sería exploratorio.
6. **Multiplicidad** (regla de adopción §4.2): el resultado es PEOR, no PASA, así que
   la cota de unión sobre cambios espurios de `s` no se activa.
7. **Huecos de procedencia, sin efecto en el resultado:**
   - el JSON de `--medir` no guarda su propio instante de ejecución E. Solo guarda la
     duración (142,6 s) y el E del `--contar` que fijó T1. La ejecución es posterior al
     commit `287984c`, que es su HEAD;
   - los hashes de los `served_*.csv` solo constan en la línea del registro, no en la
     procedencia de `--medir`;
   - E1 pedía registrar la revisión de Fable del script en un addendum de implementación.
     Solo consta en el mensaje del commit `1133813` («revision Fable APTO CON CAMBIOS
     (menores aplicados)»).
8. **No prueba rentabilidad** ni su ausencia. No hay ROI ni acierto medidos aquí.

## 9. Coordinación: este commit fija T0 del pre-registro de peso del mercado

Por E8 y por `2026-10-13-preregistro-peso-mercado-por-segmento.md` §3.1, **T0 es el
committer date (UTC) del commit que añade este fichero**. Se resuelve con
`git log --diff-filter=A --format="%H %cI" -- "docs/research/*resultado-el-modelo-manda*.md"`.
Ese commit debe contener solo este `.md` y el `.json` hermano. El script de PM aborta
si hay cero o más de un `.md` con ese patrón, así que **no se crea ningún otro**. Una
corrección por fallo técnico va como sección añadida aquí, conservando lo anterior y
con revisión de Fable. Desde T0, PM evalúa solo eventos con `start_time > T0`,
disjuntos de esta muestra. `--ajustar` no puede ejecutarse antes de T0 + 14 días.

---

Relacionado: [[2026-08-26-preregistro-el-modelo-manda]],
[[2026-11-13-regla-adopcion-tras-mm]],
[[2026-10-13-preregistro-peso-mercado-por-segmento]].

Redactado el 2026-11-17 tras la medición única; autor: Fable (rol de pre-registro y
veredictos de `.claude/automation/MODEL_ROUTING.md`).
