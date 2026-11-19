# Resultado — `park_bound` de MLB revalidado con datos deportivos: RECHAZA

**Fecha:** 2026-11-18. Ejecución única del pre-registro
`2026-11-10-preregistro-park-bound-mlb.md` (en adelante **PB**), con su Addendum 1,
que manda sobre el texto. Salida íntegra: `2026-11-18-resultado-park-bound-mlb.json`
(modo completo), `2026-11-18-pre-park-bound-mlb.json` (`--pre`) y
`2026-11-18-resultado-park-bound-mlb.log`, en este mismo directorio. Las cifras de
este documento están copiadas de esos JSON. Aquí solo se han convertido a notación
decimal española, redondeado, pasado a porcentaje y comparado de forma descriptiva.

**Veredicto pre-registrado: RECHAZA.** El valor que se desplegaría es b_C = **0,05**.
Pasan los criterios 3, 4 y 6, y fallan el **1, el 2, el 5 y el 7**. El parque **no
queda validado por datos deportivos**. Según PB §8, el único valor con origen legítimo
es el de la familia, **0**. La medición no cambia nada en producción:
`configs/leagues/ratings.yaml` sigue en `park_bound: 0.10` hasta que se haga un commit
aparte con aprobación (§12.3, §13 y la §6 de este documento).

**Qué no mide esto.** La medición no lee cuotas en ningún modo (PB §14). **No mide
ventaja sobre el mercado ni rentabilidad.** Compara la probabilidad del modelo con el
desenlace (log loss, Brier y ECE) sobre una línea teórica derivada del propio modelo.
Ningún resultado de este documento, sea ACEPTA o RECHAZA, dice nada de edge, de hit
rate, de ROI esperado ni de ROI realizado.

---

## 1. Procedencia

| Elemento | Valor |
|---|---|
| Script | `scripts/research/measure_park_bound_mlb.py` (commit `3c16a6c`), blob `c4f288fdccbb43a024f16364fca94da3da1695c5` en HEAD |
| HEAD (`--pre` y completo) | `04dae1a4921f03c9dd2580587fda545f4eab4749`, en un worktree limpio (`git_status_porcelain` del `--pre` vacío) |
| Instantánea | `C:\dev\3\snapshots\park-bound-mlb-20261118` |
| `results_mlb.csv` | 9.733 filas, SHA-256 `a25db212c635ad165205e3397ddd1bedb25a0cb71708e9a0195df24bdd4d7cb4` |
| `starters_mlb.csv` | 6.319 filas, SHA-256 `aad4615b2c54e2b4a87fa6b2cc352900644ecf65aaa8bf2545d7734c9eb99773` |
| `pre_json_sha256` | `ac8178a5d8aef504533fd14b9fccbbd86ae1e0c68a31a9f7564cc710c4eb1e54` (coincide con el SHA-256 de `2026-11-18-pre-park-bound-mlb.json` y del `pre.json` de la instantánea, comprobado) |
| SHA-256 de `configs/` | iguales en `--pre` y completo: `default.yaml` `8d497e8b…`, `leagues/ratings.yaml` `eed4222b…`, `leagues/soccer.yaml` `ecd31cc1…`, `leagues/team_aliases.yaml` `7ebc8ca7…`, `venues.yaml` `58b07943…` |
| Semilla / `n_boot` | 42 / 10.000 |
| Duración | `--pre` 187,7 s; modo completo 12.175,7 s (≈ 3 h 23 min; medición 12.171,5 s), exit 0 |
| Entorno | Python 3.14.4, numpy 2.4.4, pandas 3.0.2, scipy 1.17.1, Windows-11-10.0.26200 |
| Copia del resultado | El SHA-256 de `resultado.json` de la instantánea y el de `2026-11-18-resultado-park-bound-mlb.json` son iguales: `7a820f5f…358e` |

**Parámetros resueltos** (aserción de PB §5.2 superada, en los niveles `league_params`
y `adapter_params`): `park_bound 0,1`, `pitcher_bound 0,05`, `pitcher_prior_starts 5,0`
y `tilt_scale 0,4`. Familia: `avg_total 8,7`, `dispersion_k 3,8`, `elo_home_adv 25`,
`elo_k 6`, `home_scoring_bonus 0,1` y `max_score 25`. Pricing: `three_way false`,
`max_goals 25`, `dispersion_k 3,8`, `score_rho 0`, `dc_rho 0` y `tie_adds_goal false`.

**Orden de ejecución (PB §15).** Primero `--pre`, después `--parity-only` (PARIDAD OK,
n = 9.644, stride 1, tolerancia 1e-12) y por último el modo completo, con el mismo HEAD.
El modo completo repitió la paridad con stride 1, como pide el Addendum 1.5. Las
diferencias máximas fueron **0,0** en `h2h`, `spreads@-1.5`, `spreads@1.5` y
`totals@8.5` bajo las cotas 0, 0,10 y 0,20, y `lam0_f_identicos_bajo_las_tres_cotas = true`.
El log solo contiene el aviso de deduplicación (15 filas, AUD-003), las marcas de
avance, los valores de `a` de C y T2, la ruta de salida y el código de salida.

## 2. Datos y recuentos (PB §6 y §7)

| Recuento | Valor | Referencia de la §6 |
|---|---:|---:|
| Filas sin dedupe / con dedupe (total) | 9.733 / 9.718 | — |
| Filas sin dedupe / con dedupe hasta el corte 2026-09-26 | 9.719 / **9.704** | 9.704 (diferencia 0) |
| Descartadas por la dedupe de `game_id` hasta el corte | **15** | 15 |
| Partidos con los dos abridores adjuntos | 6.299 | — |
| Evaluados tras el warmup de 60 | **9.644** | 9.644 (diferencia 0) |

| Partición | Entrenamiento | Test (partidos / días) | Referencia | Test sin muestra de parque |
|---|---:|---:|---|---:|
| A (test 2024) | 2.370 | 2.429 / 185 | nueva | 0 |
| B (test 2025) | 4.799 | **2.430 / 184** | 2.430 / 184 | 1 |
| C (test 2026) | 7.229 | **2.415 / 183** | 2.415 / 183 | 0 |
| Combinado | — | 7.274 / 552 | — | — |

`MIN_EVAL` = 200 se supera en las tres particiones. No hizo falta ninguna enmienda.

**Claves del equipo local (Addendum 1.3).** Según el `--pre`, «oakland athletics»
aparece en 2023 y 2024, y «athletics» en 2025 y 2026. «tampa bay rays» aparece en las
cuatro temporadas. Los Athletics no mezclan recintos: su factor se reinicia en 2025.

## 3. Lo que dio el `--pre`, comparado con la aritmética de PB §9

- **Cota no vinculante:** con b = 0,50 hay 0 partidos recortados
  (`cota_050_no_vinculante = true`). Con b = 0,30 tampoco se recorta ninguno en ninguna
  partición, así que 0,30 y 0,50 forman una sola clase de equivalencia en los tres
  entrenamientos. Las demás cotas son clases distintas.
- **Fracción de partidos recortados en el test** (A / B / C):
  b = 0,05 → 0,473 / 0,400 / 0,344; b = 0,10 → 0,181 / 0,126 / 0,099;
  b = 0,15 → 0,040 / 0,056 / 0,076; b = 0,20 → 0,031 / 0,033 / 0,051.
- **Distribución de f_i en el test combinado** (n = 7.274): p1 0,848, p5 0,896,
  p25 0,961, p50 0,997, p75 1,040, p95 1,140 y p99 1,261. El mínimo es 0,830 y el
  máximo 1,284. La fracción con factor 1,0 es 0,082 % y la fracción sin muestra, 0,014 %.
- **E[KL(p_b ‖ p_0)] en el test combinado:** 0,00186 con b = 0,05; 0,00404 con 0,10;
  0,00548 con 0,15; 0,00622 con 0,20; y 0,00695 con 0,30 y con 0,50.
- **Comparación con PB §9.** La §9 esperaba que la mayoría de los parques quedaran en
  |f − 1| ≤ 0,03 y que solo dos o tres estadios pasaran de 0,05. Los factores medidos
  están más dispersos. Los cortes de quintil de |f − 1| en el test (informe 6) son
  0,0131, 0,0307, 0,0507 y 0,0801, de modo que unos dos quintos de los partidos tienen
  |f − 1| > 0,05. Por eso el techo de ganancia (E[KL]) sale por encima del rango
  0,001-0,003 que estimaba la §9 en cuanto b ≥ 0,10. Lo que se midió en el test fue
  mucho menor que ese techo (sección 4).

## 4. Criterios de aceptación (PB §8, todos a la vez)

Selección en el entrenamiento (PB §2): **b_P = 0,05 en A, B y C**, con un mínimo
interior en las tres. Por tanto **b_C = 0,05**. Pérdida primaria = log loss binario de
P(Over L_i), con L_i = ⌊μ_i^0⌋ + 0,5.

| # | Criterio | Valor | Umbral | Resultado |
|---|---|---|---|---|
| 1 | Δ log loss (T − N), test combinado | **−0,000308** | ≤ −0,002 | **FALLA** |
| 2 | Δ < 0 en cada partición | A **+0,000713**; B **+0,000610**; C −0,002257 | < 0 en las tres | **FALLA** |
| 3 | b_P > 0 en las tres | A 0,05; B 0,05; C 0,05 | > 0 | pasa |
| 4 | Brier(T) ≤ Brier(N), combinado | T 0,244579; N 0,244730 | ≤ | pasa |
| 5 | ECE(T) ≤ ECE(N), combinado | T **0,017312**; N 0,016389 | ≤ | **FALLA** |
| 6 | ll(T) < ll(C), combinado | T − C = −0,000405 | < 0 | pasa |
| 7 | Moneyline y run line no empeoran | Δ moneyline **+0,0000213**; Δ medio de run line −0,0000555 (−1,5: +0,0000124; +1,5: −0,0001235) | ambos ≤ 0 | **FALLA** (por el moneyline) |

`veredicto.criterios_fallidos` = `1_delta_logloss_combinado`,
`2_delta_negativo_en_cada_particion`, `5_ece_T_le_N` y
`7_moneyline_y_runline_no_empeoran`. `valor_validado = null`.

**Pérdidas en el test por brazo** (log loss primario):

| Partición | N (b = 0) | T (b_P = 0,05) | C (nivel) |
|---|---:|---:|---:|
| A | 0,677782 | 0,678495 | 0,678128 |
| B | 0,683356 | 0,683966 | 0,683141 |
| C | 0,686550 | 0,684293 | 0,686712 |
| Combinado | 0,682555 | 0,682247 | 0,682653 |

El efecto no tiene un signo coherente entre particiones, de modo que no es el caso de
«efecto en la dirección esperada por debajo del margen» de PB §8. El parque empeora
los dos tests que nunca vieron el parámetro, **A y B**, y solo mejora **C**. C es la
partición que PB §3.1 declaró **expuesta** al parámetro, porque la elección de 0,10
frente a 0,20 se hizo en junio con el ROI de 2026. Esto es una lectura y no una
atribución causal.

## 5. Incertidumbre (PB §11, no es puerta)

Bootstrap por bloques de día UTC del test combinado: 552 días y 10.000 réplicas.

| Cantidad | Estimación | EE | IC95 percentil | Fracción de réplicas |
|---|---:|---:|---|---|
| Δ log loss (criterio 1) | −0,000308 | 0,000721 | [−0,001709; +0,001120] | Δ ≤ −0,002: **0,91 %** |
| T − C | −0,000405 | 0,000779 | [−0,001919; +0,001133] | T − C < 0: 70,04 % |
| Δ Brier | −0,000151 | 0,000356 | [−0,000845; +0,000553] | — |
| Δ moneyline | +0,0000213 | 0,0000144 | [−0,0000070; +0,0000495] | — |
| Δ medio de run line | −0,0000555 | 0,0000507 | [−0,0001532; +0,0000451] | — |
| Δ(b_C) − Δ(0,10) (Addendum 1.1) | −0,000389 | 0,000433 | [−0,001257; +0,000452] | — |

p unilateral = Φ(Δ̂/EE) = **0,335** (informativo, sin poder de decisión). Todos los IC
contienen el 0. El Δ combinado queda muy lejos del margen: solo un 0,91 % de las
réplicas lo alcanza. El fallo del criterio 7 depende de un empeoramiento del moneyline
del orden de 2·10⁻⁵, cuyo IC también contiene el 0. Aun así el criterio 7 es de signo y
falla igualmente. Sobre el valor vigente: frente a b = 0,05, el 0,10 queda 0,000389 por
detrás en el test combinado, y el IC de esa diferencia contiene el 0.

## 6. Qué implica (PB §12.3, §13 y §16)

Esta sección describe lo que el pre-registro ordena. **La medición no ha aplicado
nada.** Cualquier cambio es un commit aparte, con aprobación.

1. **Propuesta (§12.3):** `park_bound: 0.0` en `configs/leagues/ratings.yaml`. Se
   escribe explícitamente y no se borra la clave, porque
   `tests/test_validate_oos_frozen_params.py` exige que exista. El comentario debe
   citar este resultado y no las cifras de ROI de junio.
2. **Alternativa (decisión del operador, §16.2):** conservar 0,10 «por orden», como se
   hizo con `pitcher_bound 0,05`. En ese caso el comentario debe decir «por orden del
   operador, medición del 2026-11-18 RECHAZA».
3. **En los dos casos** `park_bound` sale de `LEGACY_ROI_JUSTIFIED` en
   `tests/test_market_independence.py`, porque su justificación deja de ser el ROI.
   Este documento no decide el estado de `paused_markets` para `mlb/totals`: lo
   gobiernan el monitor de degradación y el operador.
4. **Cronología, si el valor cambia a 0 (§13):**
   - Regla 1, después de «el modelo manda»: se cumple. MM se midió el 2026-11-17
     (`7164c14`).
   - Regla 2: el cambio se aplica **en la pausa invernal, antes del Opening Day de
     2027**, para que todas las filas MLB servidas en 2027 salgan de un solo régimen.
     La §16.5 recoge la alternativa: esperar al resultado del peso por segmento
     (≈ marzo de 2027) y activar después, en una ventana limpia.
   - Regla 3: antes del cambio hacen falta **addenda previos «antes de ejecutar»** en
     los pre-registros vivos sobre el stream servido, sin alterar sus criterios. Son el
     **gate K = 69** (`2026-11-02-repreregistro-gate-k69.md` y su enmienda del
     2026-11-03; cambia la `d` de `mlb|totals` y de `mlb|team_totals`, no K), el
     **peso del mercado por segmento** (`2026-10-13-preregistro-peso-mercado-por-segmento.md`)
     y la **brecha tier A** (`2026-10-02-preregistro-brecha-tier-a.md`).
   - Regla 4, el **calibrador `mlb_totals`** (isotónico y vivo, entrenado con filas
     servidas bajo 0,10): mantenerlo de forma provisional o retirarlo a no-op es
     **decisión del operador (§16.4)**. Se resuelve en `controlled-recalibration`, no
     aquí.
   - Regla 5: el commit va antes del run de las 12:00 (KI-036), con un test del valor
     resuelto y una revisión de `tests/test_pipeline_demo.py`.
   - Regla 6: si la primera temporada con el valor nuevo empeora el log loss de los
     totales MLB, se abre otro pre-registro.
5. **Hipótesis de reapertura (§15).** Reabrir exige otra hipótesis pre-registrada, no
   otra rejilla. Según lo que falló:
   - Falló el **7** (el moneyline empeora): el parque no es «solo total». La hipótesis
     siguiente es medir la forma, por ejemplo un factor sobre el total con la proporción
     λ_h/λ_a fija.
   - El **6 pasó** (T bate a C): la reapertura «el problema es el nivel de μ» no es la
     que indica este resultado.
   - **Prior (informe 10):** la sensibilidad, descriptiva, cambia la magnitud del perfil
     pero no su argmin (sección 7); si eso basta para la reapertura de §15 es decisión
     del operador.
   - **Cambio de estadio (informe 7):** el parque por equipo no falla donde hubo cambio
     de estadio. Sin esos partidos el Δ empeora (de −0,000308 a +0,000329), así que la
     hipótesis de parque por `venue_id` (`configs/venues.yaml`) no la sugiere este
     informe.
   - Fallos 1, 2 y 5: no tienen una reapertura específica en §15. Re-ejecutar está
     prohibido (ejecución única, E10).

## 7. Informes secundarios (PB §10, **no deciden**)

**Informe 1. Δ (T(b) − N) de toda la rejilla en el test:**

| b | A | B | C | Combinado |
|---|---:|---:|---:|---:|
| 0,05 | +0,000713 | +0,000610 | −0,002257 | −0,000308 |
| 0,10 | +0,001663 | +0,001687 | −0,003126 | +0,000081 |
| 0,15 | +0,002190 | +0,001885 | −0,003785 | +0,000104 |
| 0,20 | +0,002383 | +0,001802 | −0,004005 | +0,000068 |
| 0,30 = 0,50 | +0,002582 | +0,001832 | −0,003844 | +0,000198 |

En A el Δ empeora de forma monótona al subir la cota. En B empeora de 0,05 a 0,15 y
después se estabiliza en torno a +0,0018. En C mejora hasta 0,20 y retrocede ligeramente
en 0,30. El valor vigente, 0,10, empeora el test combinado frente a b = 0.

**Informe 2. Perfil de entrenamiento** (pérdida primaria media, `park_prior_games` 20):

| b | A | B | C |
|---|---:|---:|---:|
| 0 | 0,685268 | 0,681479 | 0,682110 |
| 0,05 | **0,683672** | **0,681052** | **0,682031** |
| 0,10 | 0,684347 | 0,681866 | 0,682934 |
| 0,15 | 0,685196 | 0,682552 | 0,683456 |
| 0,20 | 0,685379 | 0,682740 | 0,683553 |
| 0,30 = 0,50 | 0,685555 | 0,682928 | 0,683687 |

El mínimo es interior en las tres particiones (`tipo_de_minimo = interior`).

**Informe 3. Procedimiento canónico `tune_market_param`** (`totals@8.5`, 4 bloques,
n_eval = 9.644): `best_value` 0,05, `improvement` 0,000439 y `oos_improvement` 0,000564,
por debajo del margen de 0,0020. `oos_selections` = [0; 0; 0; 0,05], `accepted = false`
y `recommended_value = 0,0` («family default kept»). En la línea fija 8,5 los valores
de la tabla son: ECE 0,0104 con b = 0, 0,0221 con 0,05 y 0,0323 con 0,10; log loss
0,692158 con b = 0 y 0,691718 con 0,05. Va en el mismo sentido que el veredicto, sin
decidir nada.

**Informe 4. Pérdida del total sin línea** (−log P(T = T_i); ningún T_i > 50):

| Partición | N | T | C | T2 |
|---|---:|---:|---:|---:|
| A | 2,830981 | 2,832234 | 2,831513 | 2,833210 |
| B | 2,879697 | 2,881785 | 2,879086 | 2,881147 |
| C | 2,870885 | 2,867359 | 2,871344 | 2,871344 |
| Combinado | 2,860504 | 2,860449 | 2,860630 | 2,861885 |

**Informe 5. Sesgo y T2.** El sesgo es la media de P(Over L_i) menos la tasa de Over
observada. N: A +0,0337, B +0,0111, C +0,0043. T: A +0,0312, B +0,0113, C +0,0028.
El nivel `a` de C es +0,00303 en A, −0,01974 en B y −0,01783 en C. En T2, (b_T2, a)
vale (0,05; +0,00580) en A, (0,05; −0,01694) en B y (**0**; −0,01783) en C: con el
nivel controlado, la partición C ya no elige el parque. `ganancia_T` = 0,000308 y
`ganancia_T2` = −0,000622, es decir, T2 empeora el test frente a N. La fracción
«ganancia de T2 que captura T» vale −0,495 y no es interpretable con una ganancia de T2
negativa (Incidencia 2).

**Informe 6. Fiabilidad y quintiles.** Las 7.274 probabilidades de N caen en el bin
[0,4; 0,5]: media estimada 0,4492 frente a una frecuencia observada de 0,4328. Las de T
se reparten así: [0,3; 0,4], n 1.000, 0,3851 frente a 0,393; [0,4; 0,5], n 5.425,
0,4489 frente a 0,4275; [0,5; 0,6], n 849, 0,5156 frente a 0,5135. Δ por quintil de
|f − 1|, del menor al mayor: +0,000347, −0,000227, +0,000994, +0,002532 y −0,005182
(n ≈ 1.455 por quintil). La ganancia se concentra en el quintil más extremo, y el cuarto
empeora.

**Informe 7. Sin los partidos en casa de los equipos que cambiaron de estadio**
(claves `athletics`, `oakland athletics`, `sacramento athletics` y `tampa bay rays`;
485 partidos excluidos): Δ = +0,000329, frente a −0,000308 con todos.

**Informe 8. Por temporada y mes.** Por temporada, Δ vale +0,000713 en 2024 (n 2.429),
+0,000610 en 2025 (n 2.430) y −0,002257 en 2026 (n 2.415). Por mes:

| Mes | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| Mar | +0,003463 | −0,002447 | −0,006607 |
| Abr | +0,002296 | +0,002948 | −0,005015 |
| May | −0,001924 | +0,000234 | −0,001363 |
| Jun | +0,002936 | +0,001058 | −0,004622 |
| Jul | +0,003396 | +0,003832 | +0,003653 |
| Ago | −0,002985 | −0,002370 | −0,007349 |
| Sep | +0,000587 | −0,001174 | +0,003232 |

La comparación «regular frente a postemporada» no aplica, porque el proveedor solo
ingiere `gameType=R` (Addendum 1.2).

**Informe 9. Run line y moneyline.**

| Mercado | Δ | ECE N | ECE T |
|---|---:|---:|---:|
| Moneyline | +0,0000213 | 0,004573 | 0,004639 |
| Run line −1,5 | +0,0000124 | 0,026467 | 0,026867 |
| Run line +1,5 | −0,0001235 | 0,034510 | 0,034824 |

**Informe 10. Sensibilidad al prior** (descriptivo: el perfil de entrenamiento del
informe 2 con otros `park_prior_games`):

| Prior | Partición | b = 0 | b = 0,05 | b = 0,10 | b = 0,30 = 0,50 | argmin |
|---|---|---:|---:|---:|---:|---|
| 10 | A | 0,685268 | 0,683704 | 0,685263 | 0,688426 / 0,688563 | 0,05 |
| 10 | B | 0,681479 | 0,681136 | 0,682544 | 0,684783 / 0,684851 | 0,05 |
| 10 | C | 0,682110 | 0,682093 | 0,683444 | 0,685054 / 0,685096 | 0,05 |
| 40 | A | 0,685268 | 0,683325 | 0,683614 | 0,683619 | 0,05 |
| 40 | B | 0,681479 | 0,680747 | 0,681152 | 0,681374 | 0,05 |
| 40 | C | 0,682110 | 0,681815 | 0,682345 | 0,682447 | 0,05 |

Con prior 10, la cota 0,50 ya no coincide con la 0,30, señal de que con ese prior
hay factores fuera de [0,70; 1,30]. El argmin del entrenamiento es 0,05 con los tres priors. Con prior 40 el perfil es
más plano y la ventaja de 0,05 sobre 0 es algo mayor en las tres particiones. No se usa
para elegir nada.

## 8. Incidencias

Ninguna afecta a los criterios, al veredicto ni a la paridad, y ninguna es un defecto de
código o datos según E10. No se ha corregido nada.

1. **Clave sobrante en el informe 7.** El Addendum 1.3 limita las claves a las que
   lista el `--pre`: «oakland athletics», «athletics» y «tampa bay rays». El script
   excluye además `sacramento athletics`, que no aparece en ninguna temporada del
   `--pre`. No tiene efecto observable, porque la clave no existe en los datos. Los 485
   excluidos corresponden a los partidos en casa de esos dos equipos en 2024-2026.
2. **Métrica no interpretable en el informe 5.**
   `fraccion_de_la_ganancia_de_T2_que_captura_T` = −0,495 sale del cociente
   `ganancia_T / ganancia_T2`, y el denominador es negativo (T2 empeora el test). PB §10
   no define qué hacer en ese caso. Se informa la cifra, pero no se lee como fracción.
3. **Aritmética previa de PB §9 frente al `--pre`** (no es una incoherencia de criterio).
   Los f_i están más dispersos de lo que suponía la §9 (sección 3). Esto no altera
   ningún criterio y se deja anotado para el próximo pre-registro sobre el parque.

---

Relacionado: [[2026-11-10-preregistro-park-bound-mlb]], [[2026-11-17-resultado-el-modelo-manda]],
[[2026-10-09-resultado-bateria-ajustes]], [[2026-11-02-repreregistro-gate-k69]],
[[2026-10-13-preregistro-peso-mercado-por-segmento]], [[2026-10-02-preregistro-brecha-tier-a]].
