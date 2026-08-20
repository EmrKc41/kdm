@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM Kurulum yapilmis mi?
if not exist ".venv\Scripts\python.exe" goto :kurulumyok
if not exist "web\node_modules" goto :kurulumyok

REM Derlenmis surum varsa onu calistir: acilis hizli olur.
REM Yoksa gelistirme sunucusuna duser (ilk acilis yavastir ama calisir).
set "MOD=--uretim"
if not exist "web\.next" set "MOD="

echo.
echo ===============================================
echo   Kalite Dokuman Merkezi baslatiliyor...
echo ===============================================
echo.
echo Tarayici birazdan kendiliginden acilacak.
echo Adres: http://localhost:3000
echo.
echo Programi kapatmak icin bu pencerede Ctrl+C yapin
echo veya pencereyi kapatin.
echo.

".venv\Scripts\python.exe" calistir.py %MOD% --tarayici
goto :son

:kurulumyok
echo.
echo [HATA] Kurulum yapilmamis.
echo.
echo Once kur.bat dosyasini calistirin. Tek seferlik bir islemdir.
echo.
pause
exit /b 1

:son
echo.
echo Program kapandi.
timeout /t 3 >nul
