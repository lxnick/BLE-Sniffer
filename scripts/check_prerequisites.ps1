[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$wiresharkCandidates = @(
    'C:\Program Files\Wireshark\Wireshark.exe',
    'C:\Program Files (x86)\Wireshark\Wireshark.exe'
)
$tsharkCandidates = @(
    'C:\Program Files\Wireshark\tshark.exe',
    'C:\Program Files (x86)\Wireshark\tshark.exe'
)
$nrfutilCandidates = @(
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links\nrfutil.exe"
)
$nrfutilPackage = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\NordicSemiconductor.nrfutil_*\nrfutil.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($nrfutilPackage) { $nrfutilCandidates += $nrfutilPackage.FullName }

function Find-Executable {
    param([string]$Name, [string[]]$Candidates = @())

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in $Candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail,
        [bool]$Required = $true
    )

    [PSCustomObject]@{
        Check = $Name
        Required = $Required
        Result = if ($Passed) { 'PASS' } else { 'FAIL' }
        Detail = $Detail
    }
}

$checks = @()
$dongles = @(Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object {
    $_.InstanceId -match '^USB\\VID_1915&PID_[0-9A-F]{4}'
})
$dfuDongles = @($dongles | Where-Object { $_.InstanceId -match 'PID_521F' })
$healthyDongles = @($dongles | Where-Object {
    $_.Status -eq 'OK' -and $_.Problem -eq 'CM_PROB_NONE'
})

$dongleDetail = if ($dongles.Count) { $dongles.InstanceId -join '; ' } else { 'No Nordic USB device detected' }
$firmwareDetail = if ($dfuDongles.Count) { 'DFU bootloader detected; sniffer firmware must be programmed' } else { 'Device is not in Nordic DFU mode' }
$checks += Add-Check 'nRF USB device' ($healthyDongles.Count -gt 0) $dongleDetail
$checks += Add-Check 'Dongle application firmware' ($dfuDongles.Count -eq 0) $firmwareDetail
$checks += Add-Check 'Project virtual environment' (Test-Path -LiteralPath $venvPython) $venvPython

if (Test-Path -LiteralPath $venvPython) {
    $pythonVersion = (& $venvPython --version 2>&1 | Out-String).Trim()
    $checks += Add-Check 'Python >= 3.11' ($pythonVersion -match 'Python 3\.(1[1-9]|[2-9][0-9])') $pythonVersion
} else {
    $checks += Add-Check 'Python >= 3.11' $false 'Create it with: py -3.11 -m venv .venv'
}

$nrfutil = Find-Executable 'nrfutil' $nrfutilCandidates
$nrfutilDetail = if ($nrfutil) { $nrfutil } else { 'nrfutil not found in PATH' }
$checks += Add-Check 'nRF Util' ([bool]$nrfutil) $nrfutilDetail

if ($nrfutil) {
    $searchOutput = & $nrfutil search 2>&1 | Out-String
    $deviceInstalled = $searchOutput -match '(?m)^device\s+\S+'
    $deviceDetail = if ($searchOutput -match '(?m)^device\s+.*$') { $Matches[0] } else { 'device command not listed' }
    $snifferInstalled = $searchOutput -match '(?m)^ble-sniffer\s+\S+'
    $snifferDetail = if ($searchOutput -match '(?m)^ble-sniffer\s+.*$') { $Matches[0] } else { 'ble-sniffer command not listed' }
    $checks += Add-Check 'nRF Util device command' $deviceInstalled $deviceDetail
    $checks += Add-Check 'nRF Util ble-sniffer command' $snifferInstalled $snifferDetail
} else {
    $checks += Add-Check 'nRF Util device command' $false 'Cannot check without nrfutil'
    $checks += Add-Check 'nRF Util ble-sniffer command' $false 'Cannot check without nrfutil'
}

$wireshark = Find-Executable 'wireshark' $wiresharkCandidates
$tshark = Find-Executable 'tshark' $tsharkCandidates
$wiresharkDetail = if ($wireshark) { $wireshark } else { 'Wireshark not found' }
$tsharkDetail = if ($tshark) { $tshark } else { 'tshark not found' }
$checks += Add-Check 'Wireshark' ([bool]$wireshark) $wiresharkDetail
$checks += Add-Check 'tshark' ([bool]$tshark) $tsharkDetail

$checks | Format-Table -AutoSize -Wrap
$failedRequired = @($checks | Where-Object { $_.Required -and $_.Result -eq 'FAIL' })
Write-Host "`nRequired checks: $($checks.Count - $failedRequired.Count)/$($checks.Count) passed"
if ($failedRequired.Count) { exit 1 }
exit 0
