. (Join-Path $PSScriptRoot 'Usar-Uv.ps1')
$uvExecutable = Get-RadarUv
Push-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
try {
    $env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
    Invoke-RadarTool -Executable $uvExecutable -Arguments @('lock', '--check')
    Invoke-RadarTool -Executable $uvExecutable -Arguments @('run', '--locked', 'ruff', 'check', '.')
    Invoke-RadarTool -Executable $uvExecutable -Arguments @(
        'run', '--locked', 'ruff', 'format', '--check', '.'
    )
    Invoke-RadarTool -Executable $uvExecutable -Arguments @('run', '--locked', 'pytest')
    Invoke-RadarTool -Executable $uvExecutable -Arguments @(
        'run', '--locked', 'python', 'scripts/check_docs.py'
    )
    Invoke-RadarTool -Executable $uvExecutable -Arguments @('pip', 'check')
} finally {
    Pop-Location
}
