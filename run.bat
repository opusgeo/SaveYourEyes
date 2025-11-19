@echo off
echo ================================================
echo   Brightness Guard Baslatiliyor...
echo ================================================
echo.

cd /d "%~dp0"
python main.py

if errorlevel 1 (
    echo.
    echo HATA: Uygulama calistirilirken hata olustu!
    echo brightness_guard.log dosyasini kontrol edin.
    pause
)
