# Vuelve a apuntar las tareas SQP_* a ESTE clon tras mover el proyecto.
#
# Cambia solo la ruta del proyecto en la accion (Execute, Arguments y
# WorkingDirectory). Disparadores, usuario, LogonType y ajustes no se tocan.
# Las tareas S4U exigen consola de ADMINISTRADOR.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\repoint_tasks.ps1 -WhatIf
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\repoint_tasks.ps1
#
# Sale con 1 si alguna tarea no queda apuntando aqui. Reversion: volver a
# ejecutarlo con -OldRoot <ruta actual> -NewRoot <ruta anterior>. Con -OldRoot
# C:\dev\3\sports-quant-platform (por omision) es idempotente.
param(
    [string]$OldRoot = 'C:\dev\3\sports-quant-platform',
    [string]$NewRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$OldRoot = $OldRoot.TrimEnd('\')
$NewRoot = $NewRoot.TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $NewRoot 'DIARIO_COMPLETO.bat'))) {
    Write-Output "[ERROR] $NewRoot no contiene DIARIO_COMPLETO.bat"
    exit 1
}
$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin -and -not $WhatIf) {
    Write-Output '[ERROR] ejecutalo desde una consola de administrador (o con -WhatIf).'
    exit 1
}

# Limite al final de la ruta: no confundir ...\sports-quant-platform con
# ...\sports-quant-platform-old.
$patron = [regex]::Escape($OldRoot) + '(?=\\|"|\s|$)'
$destino = $NewRoot.Replace('$', '$$')
function Convert-TaskPath([string]$Texto) {
    if (-not $Texto) { return $Texto }
    return [regex]::Replace($Texto, $patron, $destino, 'IgnoreCase')
}
function Get-ActionText($Accion) {
    return ('{0} {1} [{2}]' -f $Accion.Execute, $Accion.Arguments, $Accion.WorkingDirectory)
}

$fallos = 0
$nombres = 'SQP_Diario_Completo_Cdev', 'SQP_Capture_Close_Cdev', 'SQP_Backfill_Cdev', 'SQP_Validate_OOS_Cdev', 'SQP_Dashboard_Cdev'
foreach ($n in $nombres) {
    try {
        $t = Get-ScheduledTask -TaskName $n
        if (@($t.Actions).Count -ne 1) { throw 'se esperaba una sola accion' }
        $a = @($t.Actions)[0]
        $nueva = @{ Execute = (Convert-TaskPath $a.Execute) }
        $argumentos = Convert-TaskPath $a.Arguments
        $directorio = Convert-TaskPath $a.WorkingDirectory
        if ($argumentos) { $nueva.Argument = $argumentos }
        if ($directorio) { $nueva.WorkingDirectory = $directorio }
        $accion = New-ScheduledTaskAction @nueva
        $antes = Get-ActionText $a
        $despues = Get-ActionText $accion
        if ($despues.IndexOf($NewRoot + '\', [StringComparison]::OrdinalIgnoreCase) -lt 0) {
            throw "la accion no apunta a $OldRoot ni a ${NewRoot}: $antes"
        }
        if ($antes -eq $despues) { Write-Output "[ok] ${n}: ya apunta aqui"; continue }
        if ($WhatIf) { Write-Output "[whatif] ${n}:`n    $antes`n -> $despues"; continue }
        Set-ScheduledTask -TaskName $n -Action $accion | Out-Null
        $r = Get-ActionText (@((Get-ScheduledTask -TaskName $n).Actions)[0])
        if ($r -ne $despues) { throw "quedo en: $r" }
        Write-Output "[ok] ${n}: $r"
    } catch {
        $fallos++
        Write-Output ("[ERROR] {0}: {1}" -f $n, $_.Exception.Message)
    }
}
if ($fallos) { exit 1 }
exit 0
