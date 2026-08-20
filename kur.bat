@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ===============================================
echo   Kalite Dokuman Merkezi - Kurulum
echo ===============================================
echo.
echo Bu islem birkac dakika surebilir. Tek seferliktir;
echo bundan sonra sadece baslat.bat kullanacaksiniz.
echo.

REM --- 1) Python var mi -------------------------------------------------
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo [HATA] Python bulunamadi.
  echo.
  echo Cozum: https://www.python.org/downloads/ adresinden Python 3.11 veya
  echo uzerini kurun. Kurulum ekranindaki "Add Python to PATH" kutusunu
  echo MUTLAKA isaretleyin, sonra bu dosyayi tekrar calistirin.
  goto :hata
)
echo [1/5] Python bulundu: !PY!

REM --- 2) Node.js var mi ------------------------------------------------
where npm >nul 2>&1
if errorlevel 1 (
  echo [HATA] Node.js / npm bulunamadi.
  echo.
  echo Cozum: https://nodejs.org adresinden Node.js 20 veya uzerini kurun,
  echo sonra bu dosyayi tekrar calistirin.
  goto :hata
)
echo [2/5] Node.js bulundu

REM --- 3) Python paketleri (izole ortam) --------------------------------
REM Sanal ortam kullanilir: paketler bilgisayarin geneline bulasmaz ve
REM baska projelerin surumleriyle catismaz.
if not exist ".venv\Scripts\python.exe" (
  echo [3/5] Python ortami olusturuluyor...
  !PY! -m venv .venv
  if errorlevel 1 (
    echo [HATA] Sanal ortam olusturulamadi.
    goto :hata
  )
) else (
  echo [3/5] Python ortami zaten var
)

echo       Paketler yukleniyor...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
  echo [HATA] Python paketleri yuklenemedi.
  echo Internet baglantinizi kontrol edin.
  goto :hata
)

REM --- 4) Arayuz paketleri ----------------------------------------------
echo [4/5] Arayuz paketleri yukleniyor... (en uzun adim)
pushd web
call npm install --no-audit --no-fund
if errorlevel 1 (
  popd
  echo [HATA] npm install basarisiz.
  echo Internet baglantinizi kontrol edin.
  goto :hata
)

REM --- 5) Arayuzu derle -------------------------------------------------
echo [5/5] Arayuz derleniyor...
call npm run build
if errorlevel 1 (
  popd
  echo [HATA] Derleme basarisiz.
  goto :hata
)
popd

REM --- Sablon uyarisi ---------------------------------------------------
set "EKSIK="
if not exist "templates\taslaktalimat.xlsx" set "EKSIK=1"
if not exist "templates\taslaktne.xlsx" set "EKSIK=1"

echo.
echo ===============================================
echo   Kurulum tamamlandi.
echo ===============================================
if defined EKSIK (
  echo.
  echo [UYARI] templates klasorunde sablon dosyalari yok:
  echo         taslaktalimat.xlsx  ve  taslaktne.xlsx
  echo.
  echo Bunlar olmadan Is Talimati ve Tek Nokta Egitimi uretilemez.
  echo Vardiya Listesi ve Kalite Raporu calismaya devam eder.
)
echo.
echo Programi baslatmak icin: baslat.bat
echo.
pause
exit /b 0

:hata
echo.
pause
exit /b 1
