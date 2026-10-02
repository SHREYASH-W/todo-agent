@echo off
echo ====================================
echo Windows C: Drive Cleanup Script
echo ====================================
echo.
echo This will clean:
echo - Windows Update files (~9 GB)
echo - Temp files (~0.84 GB)
echo - Old Windows installation files (~2 GB)
echo - McAfee (if you confirm) (~8 GB)
echo.
pause

echo.
echo [1/5] Cleaning Windows Temp folder...
del /q /f /s C:\Windows\Temp\* 2>nul
for /d %%p in (C:\Windows\Temp\*) do rmdir "%%p" /s /q 2>nul

echo [2/5] Cleaning User Temp folder...
del /q /f /s %TEMP%\* 2>nul
for /d %%p in (%TEMP%\*) do rmdir "%%p" /s /q 2>nul

echo [3/5] Cleaning Windows Update files...
Dism.exe /online /Cleanup-Image /StartComponentCleanup /ResetBase

echo [4/5] Removing old Windows installation files...
rmdir /s /q "C:\$WINDOWS.~BT" 2>nul
rmdir /s /q "C:\$Windows.~WS" 2>nul
rmdir /s /q "C:\$WinREAgent" 2>nul

echo [5/5] Running Windows Disk Cleanup for Update files...
cleanmgr /verylowdisk /d C:

echo.
echo ====================================
echo Cleanup completed!
echo ====================================
echo.
echo Do you want to uninstall McAfee? (This will free ~8 GB)
echo If yes, go to Settings > Apps > Installed Apps and uninstall McAfee
echo.
pause
