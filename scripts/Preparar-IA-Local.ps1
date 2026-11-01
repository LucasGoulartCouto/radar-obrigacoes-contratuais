param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeRoot = Join-Path $projectRoot '.tools/ollama'
$version = '0.40.13'
$runtimeDirectory = Join-Path $runtimeRoot "v$version"
$runtimeExecutable = Join-Path $runtimeDirectory 'ollama.exe'
$archivePath = Join-Path $runtimeRoot "ollama-windows-amd64-v$version.zip"
$expectedArchiveSha = '7afa38624fa62ee5d8293422d0ab084c1bb4603134c7f4dafce11a033b57cc19'
$modelName = 'qwen3:4b-instruct-2507-q4_K_M'
$expectedModelDigest = '0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0'
$baseUrl = 'http://127.0.0.1:11435'
$runtimeStatePath = Join-Path $runtimeRoot 'runtime.json'
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $archivePath)) {
    Write-Host 'Baixando o runtime oficial fixado. O primeiro preparo requer internet.'
    $sourceUrl = "https://github.com/ollama/ollama/releases/download/v$version/ollama-windows-amd64.zip"
    Invoke-WebRequest -Uri $sourceUrl -OutFile "$archivePath.partial" -UseBasicParsing
    if ((Get-FileHash -LiteralPath "$archivePath.partial" -Algorithm SHA256).Hash.ToLower() -ne $expectedArchiveSha) {
        throw 'Integridade do runtime divergente; arquivo parcial preservado, sem executar.'
    }
    Move-Item -LiteralPath "$archivePath.partial" -Destination $archivePath
}
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLower() -ne $expectedArchiveSha) {
    throw 'Integridade do runtime divergente; não executar.'
}
if (-not (Test-Path -LiteralPath $runtimeExecutable)) {
    Expand-Archive -LiteralPath $archivePath -DestinationPath $runtimeDirectory
}

$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:OLLAMA_MODELS = Join-Path $runtimeRoot 'models'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_CONTEXT_LENGTH = '8192'
$listener = Get-NetTCPConnection -State Listen -LocalPort 11435 -ErrorAction SilentlyContinue
if ($listener) {
    if (-not (Test-Path -LiteralPath $runtimeStatePath)) {
        throw 'Porta em uso sem registro deste projeto. Confira o processo; nenhum serviço foi encerrado.'
    }
    $runtimeState = Get-Content -LiteralPath $runtimeStatePath -Raw | ConvertFrom-Json
    $existingProcess = Get-Process -Id $runtimeState.pid -ErrorAction SilentlyContinue
    if (-not $existingProcess -or $existingProcess.Path -ne $runtimeExecutable -or
        @($listener.OwningProcess) -notcontains $runtimeState.pid -or
        $runtimeState.models -ne $env:OLLAMA_MODELS -or -not $runtimeState.cloud_disabled) {
        throw 'O processo na porta não corresponde ao runtime registrado. Nenhum processo foi alterado.'
    }
} else {
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $stdoutPath = Join-Path $runtimeRoot "server-$stamp.stdout.log"
    $stderrPath = Join-Path $runtimeRoot "server-$stamp.stderr.log"
    $runtimeProcess = Start-Process -FilePath $runtimeExecutable -ArgumentList @('serve') -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    @{
        pid = $runtimeProcess.Id
        executable = $runtimeExecutable
        models = $env:OLLAMA_MODELS
        base_url = $baseUrl
        version = $version
        cloud_disabled = $true
        started_utc = [DateTime]::UtcNow.ToString('o')
        stderr = $stderrPath
        stdout = $stdoutPath
    } | ConvertTo-Json | Set-Content -LiteralPath $runtimeStatePath -Encoding utf8
}
$ready = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        $runtimeVersion = Invoke-RestMethod -Uri "$baseUrl/api/version" -TimeoutSec 2 -MaximumRedirection 0
        if ($runtimeVersion.version -ne $version) { throw 'Versão diferente na porta local.' }
        $ready = $true
        break
    } catch {
        Start-Sleep -Milliseconds 500
    }
}
if (-not $ready) { throw 'Runtime indisponível ou com versão diferente. Confira o registro e os logs locais.' }

$tags = Invoke-RestMethod -Uri "$baseUrl/api/tags" -TimeoutSec 5 -MaximumRedirection 0
$localModel = @($tags.models | Where-Object { $_.name -eq $modelName })
if ($localModel.Count -eq 0) {
    Write-Host 'Baixando o modelo provisório de desenvolvimento (cerca de 2,5 GB).'
    & $runtimeExecutable pull $modelName 1> (Join-Path $runtimeRoot 'pull.stdout.log') 2> (Join-Path $runtimeRoot 'pull.stderr.log')
    if ($LASTEXITCODE -ne 0) { throw 'Download não concluído; confira os logs locais antes de repetir.' }
    $tags = Invoke-RestMethod -Uri "$baseUrl/api/tags" -TimeoutSec 5 -MaximumRedirection 0
    $localModel = @($tags.models | Where-Object { $_.name -eq $modelName })
}
if ($localModel.Count -ne 1 -or $localModel[0].digest -ne $expectedModelDigest -or
    $localModel[0].details.format -ne 'gguf') {
    throw 'Modelo ausente ou digest diferente do candidato fixado; revalide antes de usar.'
}
$localModel[0] | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runtimeRoot 'model.json') -Encoding utf8
Write-Host 'IA local preparada em 127.0.0.1:11435. Modelo provisório; seleção de produção adiada.'
