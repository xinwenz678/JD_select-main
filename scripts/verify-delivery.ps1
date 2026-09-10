param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$resolvedProject = (Resolve-Path -LiteralPath $ProjectRoot).Path
$deliveryRoot = Join-Path $resolvedProject 'delivery'

$requiredProjectFiles = @(
    'README.md',
    'MVP_TASK_PLAN.md',
    'handoff.md',
    'docs/user-flow.md',
    'docs/ux-design.md',
    'docs/test-plan.md',
    'docs/test-report.md',
    'docs/bug-list.md',
    'docs/demo-script.md',
    'docs/subtitles-draft.srt',
    'docs/delivery-checklist.md',
    'docs/d-progress-final.md',
    'frontend/package.json',
    'frontend/package-lock.json',
    'backend/requirements.txt'
)

$projectChecks = foreach ($relativePath in $requiredProjectFiles) {
    $fullPath = Join-Path $resolvedProject $relativePath
    [PSCustomObject]@{
        path = $relativePath
        exists = Test-Path -LiteralPath $fullPath -PathType Leaf
        nonEmpty = if (Test-Path -LiteralPath $fullPath -PathType Leaf) { (Get-Item -LiteralPath $fullPath).Length -gt 0 } else { $false }
    }
}

$archives = @(Get-ChildItem -LiteralPath $deliveryRoot -Recurse -File -Filter '*.zip' -ErrorAction SilentlyContinue)
$videos = @(Get-ChildItem -LiteralPath $deliveryRoot -Recurse -File -Filter '*.mp4' -ErrorAction SilentlyContinue)
$reports = @(Get-ChildItem -LiteralPath (Join-Path $deliveryRoot 'reports') -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @('.pdf', '.docx') })

$videoDuration = $null
$videoUnderTenMinutes = $null
$ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
if ($videos.Count -eq 1 -and $ffprobe) {
    $seconds = & $ffprobe.Source -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $videos[0].FullName
    if ($LASTEXITCODE -eq 0 -and $seconds) {
        $videoDuration = [math]::Round([double]$seconds, 2)
        $videoUnderTenMinutes = $videoDuration -lt 600
    }
}

$coreReady = @($projectChecks | Where-Object { -not $_.exists -or -not $_.nonEmpty }).Count -eq 0
$artifactsReady = $archives.Count -ge 1 -and $videos.Count -eq 1 -and $reports.Count -ge 4
$result = [PSCustomObject]@{
    checkedAt = (Get-Date).ToString('o')
    projectRoot = $resolvedProject
    projectFilesReady = $coreReady
    projectChecks = $projectChecks
    sourceArchives = @($archives | Select-Object -ExpandProperty FullName)
    mp4Files = @($videos | Select-Object -ExpandProperty FullName)
    personalReports = @($reports | Select-Object -ExpandProperty FullName)
    videoDurationSeconds = $videoDuration
    videoUnderTenMinutes = $videoUnderTenMinutes
    ffprobeAvailable = [bool]$ffprobe
    artifactsReady = $artifactsReady
    readyForFinalManualReview = $coreReady -and $artifactsReady -and ($videoUnderTenMinutes -ne $false)
    note = 'This read-only preflight does not replace manual privacy, playback, content, or platform-naming review.'
}

$result | ConvertTo-Json -Depth 5
if (-not $result.readyForFinalManualReview) { exit 2 }
