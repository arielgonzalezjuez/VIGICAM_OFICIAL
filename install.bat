@echo off
cd /d "%~dp0"  && echo.
echo Instalando dlib desde archivo local...
pip install ./wheelhouse/dlib-19.24.99-cp312-cp312-win_amd64.whl

echo Instalando el resto de dependencias...
pip install -r requirements.txt

echo ¡Todo instalado! Ejecuta "runserver.bat" para iniciar Django.
pause