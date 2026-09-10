param([switch]$Smoke)
. "$PSScriptRoot/common.ps1"
$venvPython = Join-Path $ProjectRoot 'backend/.venv/Scripts/python.exe'
if (-not (Test-Path $venvPython)) { throw 'Backend environment missing. Run scripts/setup.ps1 first.' }
$runArguments = @((Join-Path $ProjectRoot 'scripts/run-dev.py'))
if ($Smoke) { $runArguments += '--smoke' }
Invoke-Checked $venvPython $runArguments
