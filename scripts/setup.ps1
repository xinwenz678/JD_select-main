param([switch]$RuntimeOnly)
. "$PSScriptRoot/common.ps1"
& "$PSScriptRoot/check-env.ps1"
$python = Get-RequiredCommand 'python.exe' 'Install Python 3.13.'
$npm = Get-RequiredCommand 'npm.cmd' 'Install Node.js with npm.'
$venvPython = Join-Path $ProjectRoot 'backend/.venv/Scripts/python.exe'
if (-not (Test-Path $venvPython)) {
    Invoke-Checked $python @('-m', 'venv', (Join-Path $ProjectRoot 'backend/.venv'))
}
Invoke-Checked $venvPython @('-c', 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)')
$lockName = if ($RuntimeOnly) { 'requirements.lock.txt' } else { 'requirements-dev.lock.txt' }
Invoke-Checked $venvPython @('-m', 'pip', 'install', '-r', (Join-Path $ProjectRoot "backend/$lockName"))
Invoke-Checked $venvPython @('-m', 'pip', 'check')
$lockArguments = @((Join-Path $ProjectRoot 'scripts/check-lock.py'))
if ($RuntimeOnly) { $lockArguments += '--runtime-only' }
Invoke-Checked $venvPython $lockArguments

foreach ($folder in @('backend', 'frontend')) {
    $envPath = Join-Path $ProjectRoot "$folder/.env"
    if (-not (Test-Path $envPath)) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot "$folder/.env.example") -Destination $envPath
        Write-Output "Created $folder/.env from template."
    } else { Write-Output "Preserved existing $folder/.env." }
}
Push-Location (Join-Path $ProjectRoot 'frontend')
try { Invoke-Checked $npm @('ci', '--include=dev') }
finally { Pop-Location }
Write-Output 'Setup completed. Run scripts/start.ps1 to start, or scripts/verify.ps1 to validate.'
