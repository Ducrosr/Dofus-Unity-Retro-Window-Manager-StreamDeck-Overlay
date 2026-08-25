param(
    [Parameter(Mandatory = $false)]
    [string]$AppVersion = "2.20.0"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$executable = Join-Path $projectRoot "release-assets\DofusWindowManager.exe"
if (-not (Test-Path $executable -PathType Leaf)) {
    throw "Exécutable absent : $executable. Compilez puis copiez d'abord le binaire dans release-assets."
}

$compiler = (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue).Source
if (-not $compiler) {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $compiler = $candidates | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -First 1
}
if (-not $compiler) {
    throw "ISCC.exe est introuvable. Installez Inno Setup 6 depuis sa source officielle."
}

& $compiler "/DAppVersion=$AppVersion" (Join-Path $PSScriptRoot "DofusWindowManager.iss")
if ($LASTEXITCODE -ne 0) {
    throw "La compilation Inno Setup a échoué avec le code $LASTEXITCODE."
}

Write-Host "Installateur créé : release-assets\DofusWindowManager-Setup.exe"

