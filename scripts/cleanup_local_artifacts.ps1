param(
  [switch]$IncludeBackupDbs,
  [switch]$IncludeDuplicateVenv,
  [switch]$IncludeRootDb
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$backend = Join-Path $root "backend"

function Remove-PathIfExists {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [switch]$Recurse
  )

  if (Test-Path -LiteralPath $Path) {
    $resolved = Resolve-Path -LiteralPath $Path
    if ($Recurse) {
      Remove-Item -LiteralPath $resolved -Recurse -Force
    } else {
      Remove-Item -LiteralPath $resolved -Force
    }
    Write-Host "[removed] $resolved"
  }
}

function Remove-ByPattern {
  param(
    [Parameter(Mandatory = $true)][string]$Base,
    [Parameter(Mandatory = $true)][string]$Filter,
    [switch]$Recurse
  )

  if (-not (Test-Path -LiteralPath $Base)) {
    return
  }

  Get-ChildItem -LiteralPath $Base -Filter $Filter -File -Recurse:$Recurse |
    ForEach-Object {
      Remove-Item -LiteralPath $_.FullName -Force
      Write-Host "[removed] $($_.FullName)"
    }
}

Write-Host "Cleaning local-only artifacts under: $root"
Write-Host "Safe defaults: caches and logs only."

Remove-PathIfExists -Path (Join-Path $root ".pytest_cache") -Recurse
Remove-PathIfExists -Path (Join-Path $backend ".pytest_cache") -Recurse
Remove-PathIfExists -Path (Join-Path $root "frontend\dist") -Recurse
Remove-PathIfExists -Path (Join-Path $backend "server.out.log")
Remove-PathIfExists -Path (Join-Path $backend "server.err.log")

$pycacheDirs = @(
  (Join-Path $backend "__pycache__"),
  (Join-Path $backend "routers\__pycache__"),
  (Join-Path $backend "tests\__pycache__")
)

foreach ($cacheDir in $pycacheDirs) {
  Remove-PathIfExists -Path $cacheDir -Recurse
}

# Always clean backup DB files (pattern: any-prefix.backup-*.db).
# These are local SQLite backups that accumulate quickly and are not version-controlled.
Remove-ByPattern -Base $backend -Filter "*.backup-*.db"

if ($IncludeDuplicateVenv) {
  $preferredVenv = Join-Path $backend ".venv"
  $duplicateVenv = Join-Path $backend "venv"
  if ((Test-Path -LiteralPath $preferredVenv) -and (Test-Path -LiteralPath $duplicateVenv)) {
    Remove-PathIfExists -Path $duplicateVenv -Recurse
  } else {
    Write-Host "[skip] Duplicate venv cleanup requires both backend\.venv and backend\venv to exist."
  }
}

if ($IncludeRootDb) {
  Remove-PathIfExists -Path (Join-Path $root "xuexibao.db")
}

Write-Host "Done."
