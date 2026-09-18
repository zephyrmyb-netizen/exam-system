[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$StateFile = Join-Path $Root "data\beta\run-state.json"

function Stop-BetaProcessTree([int]$ProcessId) {
  foreach ($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue)) {
    Stop-BetaProcessTree $child.ProcessId
  }
  Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path -LiteralPath $StateFile)) {
  Write-Host "No beta processes are recorded."
  exit 0
}

$state = Get-Content -Raw -LiteralPath $StateFile | ConvertFrom-Json
foreach ($property in "gatewayListenerPid", "gatewayLauncherPid", "backendListenerPid", "backendLauncherPid", "tunnelPid", "gatewayPid", "backendPid") {
  $recordedPid = $state.$property
  if ($recordedPid) {
    Stop-BetaProcessTree $recordedPid
  }
}
Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue
Write-Host "Stopped beta gateway, backend, and any script-started Tunnel process."
Write-Host "An existing cloudflared Windows service was intentionally left alone."
