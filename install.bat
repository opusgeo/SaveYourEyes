@echo off
echo ================================================
echo   Brightness Guard - Kurulum
echo ================================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo Lutfen Python 3.8 veya uzeri yukleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python bulundu!
python --version
echo.

REM Pip guncelleme
echo Pip guncelleniyor...
python -m pip install --upgrade pip
echo.

REM Kutuphaneleri yukle
echo Gerekli kutuphaneler yukleniyor...
pip install -r requirements.txt
echo.

echo ================================================
echo   Kurulum tamamlandi!
echo ================================================
echo.
echo Uygulamayi baslatmak icin:
echo     python main.py
echo.
pause
