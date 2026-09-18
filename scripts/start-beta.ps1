[CmdletBinding()]
param(
  [string]$PublicUrl = "https://beta.your-domain.com"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendEnv = Join-Path $Root "backend\.env"
$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"
$StateDir = Join-Path $Root "data\beta"
$BackupDir = Join-Path $StateDir "backups"
$DatabasePath = Join-Path $Root "backend\xuexibao.db"
$StateFile = Join-Path $StateDir "run-state.json"

function Get-LoopbackListener([int]$Port) {
  Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -in @("127.0.0.1", "::1") } |
    Select-Object -First 1
}

function Wait-LoopbackListener([int]$Port, [int]$Attempts = 20) {
  for ($attempt = 0; $attempt -lt $Attempts; $attempt++) {
    $listener = Get-LoopbackListener $Port
    if ($listener) { return $listener }
    Start-Sleep -Milliseconds 300
  }
  return $null
}

function Stop-BetaProcessTree([int]$ProcessId) {
  foreach ($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue)) {
    Stop-BetaProcessTree $child.ProcessId
  }
  Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path -LiteralPath $BackendEnv)) { throw "Missing backend/.env. Copy backend/.env.example first and set unique SECRET_KEY and INVITE_CODE." }
if (-not (Test-Path -LiteralPath $Python)) { throw "Missing backend virtual environment: $Python" }

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
if (Test-Path -LiteralPath $DatabasePath) {
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  Copy-Item -LiteralPath $DatabasePath -Destination (Join-Path $BackupDir "xuexibao-main-$stamp.db")

  # 只保留最新的 5 个 main 备份，清理旧备份避免无限堆积
  Get-ChildItem -LiteralPath $BackupDir -Filter "xuexibao-main-*.db" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 5 |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
}

if (Test-Path -LiteralPath $StateFile) { & (Join-Path $PSScriptRoot "stop-beta.ps1") }
foreach ($port in 8000, 8080) {
  $listener = Get-LoopbackListener $port
  if ($listener) {
    throw "Port $port is already in use by process $($listener.OwningProcess). Stop the existing local service before starting Beta."
  }
}

Push-Location $Root
try {
  & $Python -m alembic -c "backend\alembic.ini" upgrade head
  if ($LASTEXITCODE -ne 0) { throw "Database migration failed." }

  $env:VITE_API_BASE_URL = "/api"
  $env:VITE_APP_ENV = "beta"
  & npm.cmd --prefix frontend run build
  if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }

  $env:PRESERVE_SYSTEM_ENV = "1"
  $env:APP_ENV = "testing"

  $backend = Start-Process -FilePath $Python -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $Root -WindowStyle Hidden -PassThru
  $backendListener = Wait-LoopbackListener 8000
  if (-not $backendListener) {
    Stop-BetaProcessTree $backend.Id
    throw "FastAPI did not bind to 127.0.0.1:8000. Check backend/.env and backend startup errors."
  }
  $gateway = Start-Process -FilePath $Python -ArgumentList @("scripts/beta_gateway.py", "--port", "8080", "--static-root", "frontend/dist") -WorkingDirectory $Root -WindowStyle Hidden -PassThru
  $gatewayListener = Wait-LoopbackListener 8080
  if (-not $gatewayListener) {
    Stop-BetaProcessTree $gateway.Id
    Stop-BetaProcessTree $backend.Id
    throw "Beta gateway did not bind to 127.0.0.1:8080."
  }

  $healthy = $false
  for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
      $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:8080/api/health"
      if ($response.StatusCode -eq 200) { $healthy = $true; break }
    } catch { Start-Sleep -Milliseconds 500 }
  }
  if (-not $healthy) {
    Stop-BetaProcessTree $gateway.Id
    Stop-BetaProcessTree $backend.Id
    throw "Beta gateway did not become healthy. Check backend/.env and port availability."
  }

  $tunnelPid = $null
  $service = Get-Service -Name cloudflared -ErrorAction SilentlyContinue
  if ($service) {
    if ($service.Status -ne "Running") { Start-Service -Name cloudflared }
    Write-Host "cloudflared Windows service is running."
  } else {
    $cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
    if (-not $cloudflared) {
      $installedCloudflared = @(
        "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe",
        "$env:ProgramFiles\cloudflared\cloudflared.exe"
      ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
      if ($installedCloudflared) {
        $cloudflared = [pscustomobject]@{ Source = $installedCloudflared }
      }
    }
    if ($cloudflared -and $env:CLOUDFLARE_TUNNEL_TOKEN) {
      $tunnel = Start-Process -FilePath $cloudflared.Source -ArgumentList @("tunnel", "run", "--token", $env:CLOUDFLARE_TUNNEL_TOKEN) -WindowStyle Hidden -PassThru
      $tunnelPid = $tunnel.Id
      Write-Host "Started cloudflared from CLOUDFLARE_TUNNEL_TOKEN."
    } elseif (-not $cloudflared) {
      Write-Warning "cloudflared is not installed. Local beta is ready, but no Tunnel was started."
    } else {
      Write-Warning "CLOUDFLARE_TUNNEL_TOKEN is not set. Configure the Windows cloudflared service or set it for this PowerShell session."
    }
  }

  @{
    backendLauncherPid = $backend.Id
    backendListenerPid = $backendListener.OwningProcess
    gatewayLauncherPid = $gateway.Id
    gatewayListenerPid = $gatewayListener.OwningProcess
    tunnelPid = $tunnelPid
    startedAt = (Get-Date).ToString("o")
  } | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath $StateFile
  Write-Host "Beta is ready: http://localhost:8080"
  Write-Host "Public URL after your Tunnel route is configured: $PublicUrl"
} finally {
  Pop-Location
}
