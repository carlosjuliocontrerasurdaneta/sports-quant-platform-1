# Sports Quant Platform Superagent v1.0.0

`sqp-superagent` coordina auditorías de pronósticos, cuotas y operación diaria de Sports Quant Platform. La versión inicial trabaja en solo lectura y entrega decisiones trazables al operador.

| Especialista | Qué comprueba |
|---|---|
| `sqp-temporal` | Disponibilidad de datos al corte, fuga temporal, evaluación fuera de muestra y calibración |
| `sqp-mercados` | Identidad y frescura de la cuota, pricing, EV, CLV y ROI conforme a los contratos del repositorio |
| `sqp-operaciones` | Orden de liquidación y generación, dependencias, idempotencia y evidencia de fallos por liga |

`team.json` es el contrato editable y contiene 12 casos de evaluación. `generado/` contiene las definiciones de los agentes, el guardián local de Claude Code y el runtime del SDK para inspección. El instalador usa la fábrica que ya está en `C:\dev\superagent-architect`.

## Instalar y verificar

Extrae el ZIP, abre PowerShell en la carpeta extraída y usa Python 3.11 o posterior.

```powershell
python .\instalar_sqp.py
python .\instalar_sqp.py --write
python .\instalar_sqp.py --check
```

El primer comando muestra el plan. El segundo genera los archivos y el manifiesto del equipo en SQP. La simulación del 15 de noviembre de 2026 previó 38 reglas `deny` adicionales en `.claude/settings.json`. Esas reglas se aplican a todo el proyecto. La comprobación final debe mostrar `"ok": true`. Si trabajas en otro checkout, pasa `--project 'C:\ruta\sports-quant-platform'` o `--architect 'C:\ruta\superagent-architect'` en cada paso.

## Claude Code

```powershell
Set-Location 'C:\dev\3\sports-quant-platform'
claude --agent sqp-superagent --permission-mode plan
```

Primera consulta sugerida en la sesión:

> Revisa el orden de liquidación y generación de MLB. Cita los BAT y la guía de operación diaria. Indica qué evidencia se necesita para verificar el estado de una fecha concreta.

Al investigar código, el repositorio exige consultar Graphify primero. Corre `graphify query "<pregunta acotada>"` desde la raíz y adjunta el fragmento relevante a la consulta. Incluye liga, mercado, fecha de corte, zona horaria y artefactos o extractos pertinentes.

## Codex CLI

```powershell
Set-Location 'C:\dev\3\sports-quant-platform'
codex --sandbox read-only
```

> Coordina esta tarea según .superagente/team.json. Obtén evidencia acotada y delega explícitamente en los especialistas del equipo que correspondan, pasándoles los extractos necesarios. Consulta Graphify antes de explorar código, si está disponible. Devuelve dictamen, evidencias, límites y siguiente paso.

La sesión principal reúne la evidencia. Las definiciones de los especialistas llevan shell, apps y plugins deshabilitados. Codex carga las definiciones del proyecto cuando la carpeta está marcada como de confianza.

## OpenAI Agents SDK

Desde la raíz de SQP, configura en la sesión `OPENAI_API_KEY` y `OPENAI_MODEL`, instala `openai-agents` en el entorno Python destinado al agente y ejecuta:

```powershell
python .\.superagente\runtime\openai\team_runtime.py 'Audita el orden de liquidación y generación según la documentación local'
```

Esta modalidad llama a la API de OpenAI y su consumo se factura por separado. Las herramientas del runtime leen archivos del proyecto y entregan al modelo los extractos necesarios para la tarea.

## Verificación de entrega

El contrato pasó el validador. El plan para el checkout indicado quedó libre de conflictos. Se instaló y comprobó el equipo en una copia aislada de la configuración del proyecto. Los 12 casos del contrato quedan disponibles para una evaluación posterior con modelos.
