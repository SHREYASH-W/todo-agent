# Windows C: Drive Cleanup Script (PowerShell)
# Run as Administrator

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Windows C: Drive Cleanup Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will clean:" -ForegroundColor Yellow
Write-Host "- Windows Update files (~9 GB)"
Write-Host "- Temp files (~0.84 GB)"
Write-Host "- Old Windows installation files (~2 GB)"
Write-Host "- McAfee (if you confirm) (~8 GB)"
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit
}

Write-Host ""
Write-Host "[1/6] Cleaning Windows Temp folder..." -ForegroundColor Green
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Done!" -ForegroundColor Green

Write-Host "[2/6] Cleaning User Temp folder..." -ForegroundColor Green
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Done!" -ForegroundColor Green

Write-Host "[3/6] Cleaning Windows Update download cache..." -ForegroundColor Green
Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
Start-Service wuauserv -ErrorAction SilentlyContinue
Write-Host "Done!" -ForegroundColor Green

Write-Host "[4/6] Removing old Windows installation files..." -ForegroundColor Green
Remove-Item "C:\`$WINDOWS.~BT" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\`$Windows.~WS" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\`$WinREAgent" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Done!" -ForegroundColor Green

Write-Host "[5/6] Running Windows Component Cleanup..." -ForegroundColor Green
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Dism.exe /online /Cleanup-Image /StartComponentCleanup /ResetBase
Write-Host "Done!" -ForegroundColor Green

Write-Host "[6/6] Checking disk space..." -ForegroundColor Green
$drive = Get-PSDrive C
$freeGB = [math]::Round($drive.Free / 1GB, 2)
Write-Host "C: Drive Free Space: $freeGB GB" -ForegroundColor Cyan

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Cleanup completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Ask about McAfee
Write-Host "Do you want to uninstall McAfee? (This will free ~8 GB)" -ForegroundColor Yellow
Write-Host "Press Y to uninstall McAfee, or any other key to skip..." -ForegroundColor Yellow
$response = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

if ($response.Character -eq 'y' -or $response.Character -eq 'Y') {
    Write-Host ""
    Write-Host "Uninstalling McAfee..." -ForegroundColor Green
    Get-Package | Where-Object {$_.Name -like "*McAfee*"} | Uninstall-Package -Force
    Write-Host "McAfee uninstalled! You may need to restart your computer." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Skipped McAfee uninstallation." -ForegroundColor Yellow
    Write-Host "To uninstall later: Settings > Apps > Installed Apps > McAfee" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
