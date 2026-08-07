[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sdkRoot = 'C:\ncs\v3.3.4'
$ncsVersion = 'v3.3.4'
$board = 'nrf52840dk/nrf52840'
$nrfutil = (Get-Command nrfutil.exe -ErrorAction SilentlyContinue).Source

if (-not $nrfutil) {
    $nrfutil = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse `
        -Filter nrfutil.exe -ErrorAction SilentlyContinue |
        Where-Object FullName -Like '*NordicSemiconductor.nrfutil*' |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $nrfutil) { throw 'nrfutil was not found' }
if (-not (Test-Path -LiteralPath "$sdkRoot\.west\config")) {
    throw "nRF Connect SDK $ncsVersion was not found at $sdkRoot"
}

Push-Location $sdkRoot
try {
    foreach ($role in @('peripheral', 'central')) {
        $source = Join-Path $projectRoot "firmware\$role"
        $build = Join-Path $projectRoot "build\$role"
        & $nrfutil sdk-manager toolchain launch --ncs-version $ncsVersion -- `
            west build -p always -b $board $source -d $build
        if ($LASTEXITCODE -ne 0) { throw "$role firmware build failed" }
    }
} finally {
    Pop-Location
}

Get-FileHash -Algorithm SHA256 `
    (Join-Path $projectRoot 'build\peripheral\merged.hex'), `
    (Join-Path $projectRoot 'build\central\merged.hex')
