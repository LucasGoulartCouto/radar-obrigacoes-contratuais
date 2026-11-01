Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'

function Invoke-RadarTool {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "A ferramenta terminou com erro ($LASTEXITCODE): $Executable"
    }
}

function Get-RadarUv {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $localUv = Join-Path $projectRoot '.tools\bootstrap\Scripts\uv.exe'
    if (Test-Path -LiteralPath $localUv) { return $localUv }
    $availableUv = Get-Command uv -ErrorAction SilentlyContinue
    if ($availableUv) { return $availableUv.Source }
    throw 'Execute primeiro scripts\Preparar-Ambiente.ps1.'
}
