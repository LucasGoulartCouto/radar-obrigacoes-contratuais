param([string]$Saida)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Usar-Uv.ps1')
$uvExecutable = Get-RadarUv
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $env:UV_CACHE_DIR = Join-Path $projectRoot '.uv-cache'
    $env:PYTHONUTF8 = '1'
    $modelPath = Join-Path $projectRoot '.tools/ollama/model.json'
    if (-not (Test-Path -LiteralPath $modelPath)) {
        throw 'Execute Preparar-IA-Local.ps1 antes da avaliação.'
    }
    $modelState = Get-Content -LiteralPath $modelPath -Raw | ConvertFrom-Json
    $outputDirectory = Join-Path $projectRoot '.tools/ollama/results'
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    if (-not $Saida) {
        $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
        $Saida = Join-Path $outputDirectory "development-$stamp.json"
    }
    $Saida = [System.IO.Path]::GetFullPath($Saida)
    if ((Test-Path -LiteralPath $Saida) -or
        -not (Test-Path -LiteralPath (Split-Path -Parent $Saida) -PathType Container)) {
        throw 'Escolha um arquivo novo em um diretório existente; nenhuma inferência foi iniciada.'
    }
    Write-Host "Destino desta rodada: $Saida"
    Invoke-RadarTool -Executable $uvExecutable -Arguments @(
        'run', '--locked', 'python', '-m',
        'radar_contratos.infrastructure.experiments.local_ai',
        '--model', $modelState.name, '--digest', $modelState.digest,
        '--output', $Saida
    )
    Write-Host "Avaliação concluída; resultado preservado em $Saida"
} finally {
    Pop-Location
}
