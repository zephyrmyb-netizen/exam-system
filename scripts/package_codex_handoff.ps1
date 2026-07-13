[CmdletBinding(DefaultParameterSetName = "Package")]
param(
    [Parameter(ParameterSetName = "Package")]
    [string]$OutputDirectory,

    [Parameter(Mandatory = $true, ParameterSetName = "Verify")]
    [string]$Verify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$RequiredMetadata = @(
    "HANDOFF_README.md",
    "SOURCE_TREE.txt",
    "SOURCE_REVISION.txt",
    "MANIFEST.sha256"
)

$AllowlistedRootFiles = @(
    ".dockerignore",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".pre-commit-config.yaml",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "Dockerfile.backend",
    "Dockerfile.frontend",
    "nginx.conf",
    "pyproject.toml",
    "README.md",
    "docs/acceptance-checklist.md",
    "docs/QA_REPORT.md",
    "docs/ops/INDEX.md"
)

$AllowlistedDirectories = @(
    ".github",
    "backend",
    "exam-platform-ui",
    "frontend",
    "scripts",
    "docs/superpowers"
)

$ForbiddenSegments = @(
    ".git",
    ".venv",
    "venv",
    "cache",
    ".cache",
    "node_modules",
    "dist",
    "test-results",
    "uploads",
    ".uploads",
    "logs",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "artifacts",
    ".idea",
    ".codex",
    ".reasonix",
    ".trae"
)

function Convert-ToArchivePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    return ($Path -replace "\\", "/").TrimStart([char[]]"/")
}

function Get-ForbiddenReason {
    param([Parameter(Mandatory = $true)][string]$ArchivePath)

    if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
        return "empty archive path"
    }
    if ($ArchivePath.Contains("\")) {
        return "backslash path separator"
    }
    if ($ArchivePath.StartsWith("/", [System.StringComparison]::Ordinal) -or $ArchivePath -match "^[A-Za-z]:") {
        return "absolute archive path"
    }

    $segments = @($ArchivePath.Split([char]"/"))
    if ($segments -contains ".." -or $segments -contains ".") {
        return "path traversal segment"
    }
    foreach ($segment in $segments) {
        if ($ForbiddenSegments -contains $segment) {
            return "forbidden path segment '$segment'"
        }
    }

    if ($ArchivePath -ieq "frontend-preview.html") {
        return "obsolete frontend preview"
    }
    if ($ArchivePath.StartsWith("docs/ops/active/", [System.StringComparison]::OrdinalIgnoreCase)) {
        return "active operation record"
    }

    $leaf = [System.IO.Path]::GetFileName($ArchivePath)
    $extension = [System.IO.Path]::GetExtension($leaf).ToLowerInvariant()
    if (@(".db", ".sqlite", ".sqlite3", ".log", ".pem", ".key", ".p12", ".pfx") -contains $extension) {
        return "forbidden file extension '$extension'"
    }
    if ($leaf -like "acceptance-*.png") {
        return "acceptance screenshot"
    }
    if ($leaf.StartsWith(".env", [System.StringComparison]::OrdinalIgnoreCase) -and $leaf -ine ".env.example") {
        return "non-example environment file"
    }

    return $null
}

function Test-IsAllowlistedPath {
    param([Parameter(Mandatory = $true)][string]$ArchivePath)

    if ($RequiredMetadata -contains $ArchivePath -or $AllowlistedRootFiles -contains $ArchivePath) {
        return $true
    }
    if (-not $ArchivePath.Contains("/") -and $ArchivePath -like "README-*.md") {
        return $true
    }
    foreach ($directory in $AllowlistedDirectories) {
        if ($ArchivePath.StartsWith("$directory/", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $false
}

function Assert-ArchivePath {
    param([Parameter(Mandatory = $true)][string]$ArchivePath)

    $reason = Get-ForbiddenReason -ArchivePath $ArchivePath
    if ($null -ne $reason) {
        throw "Archive contains forbidden path '$ArchivePath': $reason"
    }
    if (-not (Test-IsAllowlistedPath -ArchivePath $ArchivePath)) {
        throw "Archive contains non-allowlisted path '$ArchivePath'"
    }
}

function Get-EntrySha256 {
    param([Parameter(Mandatory = $true)]$Entry)

    $stream = $null
    $sha = $null
    try {
        $stream = $Entry.Open()
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $digest = $sha.ComputeHash($stream)
        return ([System.BitConverter]::ToString($digest)).Replace("-", "").ToLowerInvariant()
    }
    finally {
        if ($null -ne $sha) { $sha.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
    }
}

function New-HandoffArchive {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDirectory,
        [Parameter(Mandatory = $true)][string]$ArchivePath
    )

    $zip = $null
    try {
        $zip = [System.IO.Compression.ZipFile]::Open(
            $ArchivePath,
            [System.IO.Compression.ZipArchiveMode]::Create
        )
        foreach ($file in Get-ChildItem -LiteralPath $SourceDirectory -Recurse -File | Sort-Object FullName) {
            $relativePath = Convert-ToArchivePath -Path $file.FullName.Substring($SourceDirectory.Length).TrimStart([char[]]"\/")
            $entry = $zip.CreateEntry($relativePath, [System.IO.Compression.CompressionLevel]::Optimal)
            $inputStream = $null
            $outputStream = $null
            try {
                $inputStream = [System.IO.File]::OpenRead($file.FullName)
                $outputStream = $entry.Open()
                $inputStream.CopyTo($outputStream)
            }
            finally {
                if ($null -ne $outputStream) { $outputStream.Dispose() }
                if ($null -ne $inputStream) { $inputStream.Dispose() }
            }
        }
    }
    finally {
        if ($null -ne $zip) { $zip.Dispose() }
    }
}

function Test-HandoffArchive {
    param([Parameter(Mandatory = $true)][string]$ArchivePath)

    $resolvedArchive = (Resolve-Path -LiteralPath $ArchivePath).Path
    $zip = $null
    try {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($resolvedArchive)
        $entries = @{}

        foreach ($entry in $zip.Entries) {
            $name = $entry.FullName
            Assert-ArchivePath -ArchivePath $name
            if ([string]::IsNullOrEmpty($entry.Name)) { continue }

            if ($entries.ContainsKey($name)) {
                throw "Archive contains duplicate entry '$name'"
            }
            $entries[$name] = $entry
        }

        foreach ($required in $RequiredMetadata) {
            if (-not $entries.ContainsKey($required)) {
                throw "Archive is missing required root metadata '$required'"
            }
        }

        $manifestStream = $null
        $reader = $null
        try {
            $manifestStream = $entries["MANIFEST.sha256"].Open()
            $reader = [System.IO.StreamReader]::new($manifestStream, [System.Text.Encoding]::UTF8, $true)
            $manifestText = $reader.ReadToEnd()
        }
        finally {
            if ($null -ne $reader) { $reader.Dispose() }
            elseif ($null -ne $manifestStream) { $manifestStream.Dispose() }
        }

        $manifest = @{}
        foreach ($line in @($manifestText -split "\r?\n")) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            if ($line -notmatch "^([0-9a-f]{64})  (.+)$") {
                throw "Malformed manifest line '$line'"
            }

            $digest = $Matches[1]
            $name = $Matches[2]
            Assert-ArchivePath -ArchivePath $name
            if ($name -eq "MANIFEST.sha256") {
                throw "Manifest must not hash itself"
            }
            if ($manifest.ContainsKey($name)) {
                throw "Manifest contains duplicate entry '$name'"
            }
            $manifest[$name] = $digest
        }

        $expectedNames = @($entries.Keys | Where-Object { $_ -ne "MANIFEST.sha256" })
        if ($manifest.Count -ne $expectedNames.Count) {
            throw "Manifest entry count does not match archive file count"
        }

        foreach ($name in $expectedNames) {
            if (-not $manifest.ContainsKey($name)) {
                throw "Manifest does not cover '$name'"
            }
            $actualDigest = Get-EntrySha256 -Entry $entries[$name]
            if ($actualDigest -cne $manifest[$name]) {
                throw "SHA-256 mismatch for '$name'"
            }
        }

        foreach ($name in $manifest.Keys) {
            if (-not $entries.ContainsKey($name)) {
                throw "Manifest references missing archive entry '$name'"
            }
        }
    }
    finally {
        if ($null -ne $zip) { $zip.Dispose() }
    }

    Write-Output "Verified: $resolvedArchive"
}

if ($PSCmdlet.ParameterSetName -eq "Verify") {
    Test-HandoffArchive -ArchivePath $Verify
    exit 0
}

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $RepoRoot "artifacts"
}
$resolvedOutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($resolvedOutputDirectory) | Out-Null

$packagingPathspecs = @($AllowlistedRootFiles) + @(
    ":(top,glob)README-*.md"
) + @($AllowlistedDirectories)

$unstagedArguments = @(
    "-C", $RepoRoot,
    "-c", "core.quotePath=false",
    "diff", "--name-only", "--"
) + $packagingPathspecs
$unstagedFiles = @(& git @unstagedArguments)
if ($LASTEXITCODE -ne 0) {
    throw "git diff failed while checking the handoff packaging scope"
}

$stagedArguments = @(
    "-C", $RepoRoot,
    "-c", "core.quotePath=false",
    "diff", "--cached", "--name-only", "--"
) + $packagingPathspecs
$stagedFiles = @(& git @stagedArguments)
if ($LASTEXITCODE -ne 0) {
    throw "git diff --cached failed while checking the handoff packaging scope"
}

$untrackedArguments = @(
    "-C", $RepoRoot,
    "-c", "core.quotePath=false",
    "ls-files", "--others", "--exclude-standard", "--"
) + $packagingPathspecs
$untrackedFiles = @(& git @untrackedArguments)
if ($LASTEXITCODE -ne 0) {
    throw "git ls-files failed while checking the handoff packaging scope"
}

$dirtyPackagingFiles = @(
    $unstagedFiles + $stagedFiles + $untrackedFiles |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { Convert-ToArchivePath -Path $_ } |
        Sort-Object -Unique
)
if ($dirtyPackagingFiles.Count -gt 0) {
    throw "Packaging scope does not match HEAD: $($dirtyPackagingFiles -join ', ')"
}

$selectedFiles = @{}
$gitArguments = @(
    "-C", $RepoRoot,
    "-c", "core.quotePath=false",
    "ls-files", "--cached", "--"
) + $packagingPathspecs
$gitFiles = @(& git @gitArguments)
if ($LASTEXITCODE -ne 0) {
    throw "git ls-files failed while building the handoff allowlist"
}

foreach ($candidate in $gitFiles) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
    $relativePath = Convert-ToArchivePath -Path $candidate
    $reason = Get-ForbiddenReason -ArchivePath $relativePath
    if ($null -ne $reason) { continue }
    if (-not (Test-IsAllowlistedPath -ArchivePath $relativePath)) { continue }

    $fullPath = Join-Path $RepoRoot ($relativePath -replace "/", "\")
    if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
        $selectedFiles[$relativePath] = $fullPath
    }
}

$requiredSources = @(
    "README.md",
    "exam-platform-ui/HANDOFF_README.md",
    "exam-platform-ui/CODEX_HANDOFF.md",
    "exam-platform-ui/IMPLEMENTATION_MAP.md",
    "frontend/src/router.ts",
    "scripts/package_codex_handoff.ps1"
)
foreach ($requiredSource in $requiredSources) {
    if (-not $selectedFiles.ContainsKey($requiredSource)) {
        throw "Required handoff source is missing: $requiredSource"
    }
}

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$stagingDirectory = Join-Path $tempRoot ("xuexibao-handoff-" + [System.Guid]::NewGuid().ToString("N"))
[System.IO.Directory]::CreateDirectory($stagingDirectory) | Out-Null

try {
    foreach ($relativePath in @($selectedFiles.Keys | Sort-Object)) {
        $destination = Join-Path $stagingDirectory ($relativePath -replace "/", "\")
        $destinationDirectory = Split-Path -Parent $destination
        [System.IO.Directory]::CreateDirectory($destinationDirectory) | Out-Null
        Copy-Item -LiteralPath $selectedFiles[$relativePath] -Destination $destination
    }

    Copy-Item -LiteralPath $selectedFiles["exam-platform-ui/HANDOFF_README.md"] -Destination (Join-Path $stagingDirectory "HANDOFF_README.md")

    $fullRevision = (& git -C $RepoRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to read source revision" }
    $shortRevision = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to read short source revision" }
    $branch = (& git -C $RepoRoot branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to read source branch" }
    $workingTreeState = if ([string]::IsNullOrWhiteSpace((& git -C $RepoRoot status --porcelain))) { "clean" } else { "dirty" }

    $revisionLines = @(
        "revision=$fullRevision",
        "short_revision=$shortRevision",
        "branch=$branch",
        "working_tree=$workingTreeState"
    )
    [System.IO.File]::WriteAllLines((Join-Path $stagingDirectory "SOURCE_REVISION.txt"), $revisionLines, [System.Text.Encoding]::UTF8)

    $sourceTreeLines = @("HANDOFF_README.md") + @($selectedFiles.Keys | Sort-Object)
    [System.IO.File]::WriteAllLines((Join-Path $stagingDirectory "SOURCE_TREE.txt"), $sourceTreeLines, [System.Text.Encoding]::UTF8)

    $manifestLines = @()
    foreach ($file in Get-ChildItem -LiteralPath $stagingDirectory -Recurse -File | Sort-Object FullName) {
        $relativePath = Convert-ToArchivePath -Path $file.FullName.Substring($stagingDirectory.Length).TrimStart([char[]]"\/")
        if ($relativePath -eq "MANIFEST.sha256") { continue }
        $digest = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $manifestLines += "$digest  $relativePath"
    }
    [System.IO.File]::WriteAllLines((Join-Path $stagingDirectory "MANIFEST.sha256"), $manifestLines, [System.Text.Encoding]::UTF8)

    $archivePath = Join-Path $resolvedOutputDirectory "xuexibao-codex-handoff-$shortRevision.zip"
    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }

    New-HandoffArchive -SourceDirectory $stagingDirectory -ArchivePath $archivePath

    Test-HandoffArchive -ArchivePath $archivePath
    Write-Output "Created: $archivePath"
}
finally {
    $resolvedStaging = [System.IO.Path]::GetFullPath($stagingDirectory)
    if ($resolvedStaging.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedStaging).StartsWith("xuexibao-handoff-", [System.StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $resolvedStaging -Recurse -Force -ErrorAction SilentlyContinue
    }
}
