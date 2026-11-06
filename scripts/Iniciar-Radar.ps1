. (Join-Path $PSScriptRoot 'Usar-Uv.ps1')
$uvExecutable = Get-RadarUv
$previousModelDigest = $env:RADAR_LOCAL_MODEL_DIGEST
Push-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
try {
    $env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
    $modelMetadataPath = Join-Path (Get-Location) '.tools/ollama/model.json'
    if (-not $env:RADAR_LOCAL_MODEL_DIGEST -and (Test-Path -LiteralPath $modelMetadataPath)) {
        $modelMetadata = Get-Content -LiteralPath $modelMetadataPath -Raw | ConvertFrom-Json
        if ($modelMetadata.digest -notmatch '^[a-f0-9]{64}$') {
            throw 'Metadados locais inválidos. Prepare a IA local antes de iniciar o Radar.'
        }
        $env:RADAR_LOCAL_MODEL_DIGEST = $modelMetadata.digest
    }
    Invoke-RadarTool -Executable $uvExecutable -Arguments @(
        'run', '--locked', 'streamlit', 'run', 'src/radar_contratos/ui/app.py'
    )
} finally {
    $env:RADAR_LOCAL_MODEL_DIGEST = $previousModelDigest
    Pop-Location
}
