. (Join-Path $PSScriptRoot 'Usar-Uv.ps1')
$uvExecutable = Get-RadarUv
Push-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
try {
    $env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
    Invoke-RadarTool -Executable $uvExecutable -Arguments @(
        'run', '--locked', 'streamlit', 'run', 'src/radar_contratos/ui/app.py'
    )
} finally {
    Pop-Location
}
