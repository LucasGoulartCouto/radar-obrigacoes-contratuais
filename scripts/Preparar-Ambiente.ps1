. (Join-Path $PSScriptRoot 'Usar-Uv.ps1')
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $localUv = Join-Path $projectRoot '.tools\bootstrap\Scripts\uv.exe'
    if (-not (Test-Path -LiteralPath $localUv)) {
        Invoke-RadarTool -Executable 'python' -Arguments @('-m', 'venv', '.tools/bootstrap')
        $bootstrapPython = Join-Path $projectRoot '.tools\bootstrap\Scripts\python.exe'
        Invoke-RadarTool -Executable $bootstrapPython -Arguments @(
            '-m', 'pip', 'install', 'uv==0.13.6', '--index-url',
            'https://pypi.org/simple', '--disable-pip-version-check'
        )
    }
    $env:UV_CACHE_DIR = Join-Path $projectRoot '.uv-cache'
    Invoke-RadarTool -Executable $localUv -Arguments @('sync', '--locked')
    Invoke-RadarTool -Executable $localUv -Arguments @('run', '--locked', 'radar', 'init-db')
    Write-Host 'Ambiente preparado. Inicie com scripts\Iniciar-Radar.ps1.'
} finally {
    Pop-Location
}
