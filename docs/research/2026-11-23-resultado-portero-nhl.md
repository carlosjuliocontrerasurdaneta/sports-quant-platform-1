# Resultado: portero NHL (`goalie_beta`), RECHAZA

**Fecha:** 2026-11-23. Es la ejecución única del pre-registro `2026-09-26-preregistro-portero-nhl.md`, con sus Enmiendas 1 a 6; la Enmienda 6 rige la ejecución.

Salida íntegra en este mismo directorio:
- `2026-11-23-resultado-portero-nhl.json`: modo completo. SHA-256 `8d31b03b6ba9e8ec41d26dc2e4b54bfb9098b9592622764289a4b71c753c860c`, rc = 0, 30.170 s. El SHA-256 es el del fichero original, `C:/dev/sqp-snapshots/portero-nhl-20261121-out/completo.json`. Git normaliza los fines de línea de la copia versionada, así que fuera de Windows el hash de esa copia puede diferir.
- `2026-11-23-pre-portero-nhl.json`: el `--pre` #2.
- `2026-11-23-resultado-portero-nhl.log`.

Las cifras de las §2 y §3 están copiadas de esos JSON. Las de la §1 tienen otro origen: la salida de consola de `--parity-only` (`parity2.log`), `git log` y los ficheros de estado de las tareas, fuera del repositorio, en `C:/dev/sqp-snapshots/portero-nhl-20261121-out/`. El veredicto lo emitió el escalón Fable aplicando literalmente la §8.

**Veredicto pre-registrado: RECHAZA** (M2 y M1). El portero **no se activa**:
- `goalie_beta` sigue ausente (0) en `configs/leagues/ratings.yaml`;
- la fase 2 no se ejecuta;
- la captura de probables se mantiene (decisión del operador).

**Qué no mide esto.** La medición compara la probabilidad del modelo con el desenlace (log loss y ECE) sobre el histórico. **No mide ventaja sobre el mercado ni rentabilidad.**

## 1. Procedencia

- **Instantánea congelada:** `C:\dev\sqp-snapshots\portero-nhl-20261121`.
- **Código:** HEAD `901ba7b`, con el árbol limpio al arrancar cada modo.
- **`--parity-only` con `--data-root` a la instantánea:** PARIDAD OK, n = 33.200; base, T de M1 y T de M2; moneyline, puck line y totales a 1e-12.
- **`--pre` #2:** idéntico al #1 (`04f3015`, invalidado por la Enmienda 6(d)) salvo `git_head` y la duración.
- **Modo completo:** con `--pre-json` apuntando al `--pre` #2. Los 5 hashes de entrada y los 7 ficheros de cuotas de cierre coinciden.
- **HEAD, parámetros y lista E:** el script aborta si difieren, y terminó con rc = 0.
- **Commits durante la ejecución (13:03 a 21:26):** ninguno tocó `src/`, `configs/` ni `scripts/research/`. `git log 901ba7b..23eaf86` solo muestra un script nuevo en `scripts/` y documentación.
- **Tareas `SQP_*`:** el estado antes (`tareas-antes-pre2.json`) y después (`tareas-despues-completo.json`, registrado el 24-11) está en la carpeta de salida. Todas acabaron con rc = 0. Como se usó la instantánea, las tareas no pudieron alterar las entradas.
- **Reglas de ejecución:** no se violó E10 ni las Enmiendas 2(d)/3(f). Hubo un solo modo completo, y el script se niega a sobrescribir `--out`.

## 2. Criterios de la §8 aplicados a M2

Los criterios se exigen a la vez. M2 es el proxy.

| Criterio | Cifra | ¿Cumple? |
|---|---|---|
| 1. Δ log loss de los afectados del combinado ≤ −0,002 | +0,000034 (IC95 por días [−0,000084, +0,000155]; n = 15.891) | NO |
| 2. Δ < 0 en cada partición | A +0,000104, B −0,000025, C +0,000019 | NO |
| 3. ECE(T) ≤ ECE(base) | 0,01064 frente a 0,01052 | NO |
| 4. β > 0 en las tres particiones | 0,161 / 0,103 / 0,109 | SÍ |
| 5. log loss(T) < log loss(C) | T − C = +0,000123 | NO |
| 6a. Totales ≤ 0 | +0,000134 | NO |
| 6b. Spreads ≤ 0 | +0,000100 | NO |

M2 falla 6 de los 7 subcriterios. El Δ del criterio 1 queda a unos 33 errores estándar del margen. No es un caso dudoso.

**M1 (titular real, cota superior):**
- Δ = −0,000222 (IC95 [−0,000499, +0,000052]), lejos de −0,002.
- Empeora los totales (+0,000351) y los spreads (+0,000050).
- También RECHAZA.

## 3. Lectura

- **Alcance del rechazo:** RECHAZA se refiere a **esta forma** (q con contracción k, f multiplicativo, tope 0,35 y un solo β). No dice que el portero «no importe».
- **Discriminación:** la Enmienda 3(e) ya anticipaba que esta base exigía discriminación nueva, y no ha aparecido. La AUC de M2 da T 0,60050 frente a base 0,60056.
- **Ganancia de M1:** la pequeña ganancia se concentra en los back-to-backs (−0,000325 frente a −0,000156). Por la Enmienda 2(a), una parte no identificable puede ser fatiga.
- **Reapertura:** reabrir exige una forma distinta y pre-registrada (§14). Repetir esta con otro tope, otro k u otras particiones está prohibido.
- **KI-006:** el moneyline NHL sigue sin una señal específica validada.
