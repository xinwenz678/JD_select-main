param([switch]$SkipSmoke)
. "$PSScriptRoot/common.ps1"
$venvPython = Join-Path $ProjectRoot 'backend/.venv/Scripts/python.exe'
$npm = Get-RequiredCommand 'npm.cmd' 'Install Node.js with npm.'
if (-not (Test-Path $venvPython)) { throw 'Run scripts/setup.ps1 before verification.' }
Invoke-Checked $venvPython @((Join-Path $ProjectRoot 'scripts/check-lock.py'))
Invoke-Checked $venvPython @('-m', 'pip', 'check')
Invoke-Checked $venvPython @('-m', 'pytest', '-c', (Join-Path $ProjectRoot 'backend/pytest.ini'), (Join-Path $ProjectRoot 'backend/tests'), '-q')
Push-Location (Join-Path $ProjectRoot 'frontend')
try {
    Invoke-Checked $npm @('test')
    Invoke-Checked $npm @('run', 'build')
}
finally { Pop-Location }
if (-not $SkipSmoke) { & "$PSScriptRoot/start.ps1" -Smoke }
Write-Output 'Verification completed.'