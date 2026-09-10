param([switch]$CheckPorts)
. "$PSScriptRoot/common.ps1"

$python = Get-RequiredCommand 'python.exe' 'Install Python 3.13 and reopen PowerShell.'
$node = Get-RequiredCommand 'node.exe' 'Install Node.js 22.12 or newer and reopen PowerShell.'
$npm = Get-RequiredCommand 'npm.cmd' 'Install Node.js with npm.'
Invoke-Checked $python @('-c', "import sys; print('Python:', sys.version.split()[0]); sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)")
Invoke-Checked $node @('-e', "const v=process.versions.node.split('.').map(Number); console.log('Node:',process.version); process.exit(v[0]>22 || (v[0]===22 && v[1]>=12) ? 0 : 1)")
Invoke-Checked $npm @('--version')
foreach ($relative in @('backend/requirements.lock.txt', 'backend/requirements-dev.lock.txt', 'backend/.env.example', 'frontend/.env.example', 'frontend/package-lock.json', 'frontend/package.json')) {
    if (-not (Test-Path (Join-Path $ProjectRoot $relative))) { throw "Missing project file: $relative" }
}
if ($CheckPorts) {
    foreach ($port in @(8000, 5173)) {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        try { $listener.Start(); Write-Output "Port $port is available." }
        catch { throw "Port $port is busy. Stop your existing project server before starting another." }
        finally { $listener.Stop() }
    }
}
Write-Output 'Environment check completed. Validated baseline: Windows x64, Python 3.13, Node 22.19, npm 10.9.'
