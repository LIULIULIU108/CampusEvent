param(
    [string]$PublicUrl = ""
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$screens = Join-Path $root "docs\evidence\screens"
$png = Join-Path $root "docs\evidence\png"
New-Item -ItemType Directory -Force -Path $png | Out-Null

$edgeCandidates = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
)
$edge = $edgeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $edge) { throw "Microsoft Edge not found" }

$profile = Join-Path $root ".screenshot-profile"
New-Item -ItemType Directory -Force -Path $profile | Out-Null

Get-ChildItem -LiteralPath $screens -Filter "*.html" | ForEach-Object {
    $target = Join-Path $png ($_.BaseName + ".png")
    if (Test-Path $target) { Remove-Item -LiteralPath $target -Force }
    $uri = ([System.Uri]$_.FullName).AbsoluteUri
    & $edge --headless=new --disable-gpu --hide-scrollbars --no-first-run `
        --user-data-dir=$profile --window-size=1280,900 --virtual-time-budget=2000 `
        --screenshot=$target $uri 2>$null | Out-Null
    Start-Sleep -Milliseconds 400
    if (-not (Test-Path $target)) { throw "screenshot failed: $($_.Name)" }
    Write-Output ("shot {0} -> {1:N1} KB" -f $_.BaseName, ((Get-Item $target).Length / 1KB))
}

if ($PublicUrl) {
    $target = Join-Path $png "线上-首页.png"
    if (Test-Path $target) { Remove-Item -LiteralPath $target -Force }
    & $edge --headless=new --disable-gpu --hide-scrollbars --no-first-run `
        --user-data-dir=$profile --window-size=1280,900 --virtual-time-budget=4000 `
        --screenshot=$target $PublicUrl 2>$null | Out-Null
    if (Test-Path $target) {
        Write-Output ("shot public -> {0:N1} KB" -f ((Get-Item $target).Length / 1KB))
    } else {
        Write-Output "public screenshot failed (server may still be waking); retry later."
    }
}
