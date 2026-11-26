param(
    [string]$Root = "D:\CampusEvent"
)

$ErrorActionPreference = "Continue"
Set-Location $Root
$cfg = Get-Content -LiteralPath ".thevibehosting.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$sshParts = $cfg.ssh -split ' '
$hostIp = ($sshParts | Where-Object { $_ -match '^root@' }) -replace '^root@', ''
$port = $sshParts[$sshParts.Length - 1]
Write-Output "target=$hostIp port=$port subdomain=$($cfg.subdomain)"

$key = Join-Path $Root ".thevibehosting_key"
$sshOpts = @(
    "-i", $key, "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=NUL", "-o", "LogLevel=ERROR", "-o", "IPQoS=none",
    "-o", "Compression=no", "-o", "ServerAliveInterval=20"
)

$tar = Join-Path $Root ".tools\deploy.tar.gz"
if (Test-Path $tar) { Remove-Item $tar -Force }
tar -czf $tar `
    --exclude=.git --exclude=.venv --exclude=.tools --exclude=.tmp `
    --exclude=.pytest-tmp --exclude=.pytest_cache --exclude=.screenshot-profile `
    --exclude=instance --exclude=__pycache__ --exclude=.thevibehosting.json `
    --exclude=.thevibehosting_key --exclude=docs --exclude=tests `
    app app_v2 run.py run_v2.py cli.py cli_v2.py requirements.txt pytest.ini pytest_v2.ini README.md
if ($LASTEXITCODE -ne 0) { throw "tar failed" }

scp @sshOpts -P $port $tar "root@${hostIp}:/root/deploy.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "upload tar failed" }
scp @sshOpts -P $port (Join-Path $Root "deploy\remote_setup.sh") "root@${hostIp}:/root/setup.sh"
if ($LASTEXITCODE -ne 0) { throw "upload setup failed" }
ssh @sshOpts -p $port "root@$hostIp" "sed -i 's/\r$//' /root/setup.sh && bash /root/setup.sh"
if ($LASTEXITCODE -ne 0) { throw "remote setup failed" }

Write-Output "https://$($cfg.subdomain)"
