# Impide la suspension por inactividad mientras corre el flujo diario (2026-11-25).
#
# El 25-11 la maquina se suspendio de 18:18 a 21:23 en mitad de DIARIO_COMPLETO
# (eventos de energia de Windows): ~30 min de trabajo tardaron 3 h 40 min. La
# tarea tiene WakeToRun, que despierta la maquina para ARRANCAR, pero nada
# impedia que volviera a dormirse a mitad de run.
#
# Mecanismo: SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) desde
# este proceso. No requiere elevacion ni cambia el plan de energia: la peticion
# muere con el proceso. Solo evita la suspension por INACTIVIDAD; cerrar la
# tapa o suspender a mano sigue suspendiendo (limitacion de Windows).
#
# Vida: mientras viva el proceso que lo lanzo (el cmd del BAT) y como mucho
# $MaxHours, para que un BAT matado a la fuerza no deje la maquina despierta
# indefinidamente. No escribe en data\ ni en logs\ salvo su propia salida.
param(
    [int]$WatchPid = 0,
    [int]$MaxHours = 12,
    [int]$PollSeconds = 30
)

$ErrorActionPreference = 'Stop'
try {
    if ($WatchPid -le 0) {
        $WatchPid = (Get-CimInstance Win32_Process -Filter "ProcessId=$PID").ParentProcessId
    }
    Add-Type -Namespace Sqp -Name Power -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("kernel32.dll")]
public static extern uint SetThreadExecutionState(uint esFlags);
'@
    $ES_CONTINUOUS = [uint32]'0x80000000'
    $ES_SYSTEM_REQUIRED = [uint32]'0x00000001'
    if ([Sqp.Power]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED) -eq 0) {
        Write-Output "[keep_awake] SetThreadExecutionState fallo; no se impide la suspension."
        exit 1
    }
    $limite = (Get-Date).AddHours($MaxHours)
    while ((Get-Date) -lt $limite) {
        if (-not (Get-Process -Id $WatchPid -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Seconds $PollSeconds
    }
    [void][Sqp.Power]::SetThreadExecutionState($ES_CONTINUOUS)
    exit 0
} catch {
    # Nunca debe tumbar ni bloquear el flujo diario: se informa y se sale.
    Write-Output "[keep_awake] no disponible: $($_.Exception.Message)"
    exit 1
}
