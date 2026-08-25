param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($env:WINDOWS_SIGNING_CERTIFICATE_BASE64)) {
    Write-Host "Aucun certificat configuré : $FilePath reste non signé."
    exit 0
}
if ([string]::IsNullOrWhiteSpace($env:WINDOWS_SIGNING_CERTIFICATE_PASSWORD)) {
    throw "Le certificat est présent mais son mot de passe n'est pas configuré."
}

$resolvedFile = (Resolve-Path $FilePath).Path
$temporaryRoot = if ([string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
    [IO.Path]::GetTempPath()
} else {
    $env:RUNNER_TEMP
}
$certificatePath = Join-Path $temporaryRoot "dwm-signing-$([Guid]::NewGuid().ToString('N')).pfx"
try {
    [IO.File]::WriteAllBytes(
        $certificatePath,
        [Convert]::FromBase64String($env:WINDOWS_SIGNING_CERTIFICATE_BASE64)
    )
    $signTool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Filter signtool.exe -Recurse |
        Where-Object { $_.FullName -match '\\x64\\signtool\.exe$' } |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    if (-not $signTool) {
        throw "signtool.exe x64 est introuvable dans le Windows SDK."
    }
    $timestampUrl = if ([string]::IsNullOrWhiteSpace($env:WINDOWS_SIGNING_TIMESTAMP_URL)) {
        "http://timestamp.digicert.com"
    } else {
        $env:WINDOWS_SIGNING_TIMESTAMP_URL
    }
    & $signTool.FullName sign /fd SHA256 /td SHA256 /tr $timestampUrl /f $certificatePath /p $env:WINDOWS_SIGNING_CERTIFICATE_PASSWORD $resolvedFile
    if ($LASTEXITCODE -ne 0) {
        throw "La signature Authenticode a échoué avec le code $LASTEXITCODE."
    }
    & $signTool.FullName verify /pa /v $resolvedFile
    if ($LASTEXITCODE -ne 0) {
        throw "La vérification Authenticode a échoué avec le code $LASTEXITCODE."
    }
} finally {
    Remove-Item $certificatePath -Force -ErrorAction SilentlyContinue
}
