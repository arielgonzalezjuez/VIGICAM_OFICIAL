@echo off
:: Configuración de la ventana
title Iniciando Servidor Django
color 0A
cls

:: Verificar requisitos
where python >nul 2>nul || (
    echo Error: Python no está instalado o no está en el PATH.
    echo Descárgalo desde: https://www.python.org/downloads/
    pause
    exit /b
)

if not exist "manage.py" (
    echo Error: No se encontró manage.py. Ejecuta primero install.bat.
    pause
    exit /b
)

:: Activar entorno virtual si existe
if exist "venv\Scripts\activate" call venv\Scripts\activate

:: Iniciar servidor y abrir navegador
echo Iniciando servidor de Django...
echo -------------------------------
echo URL: http://127.0.0.1:8000/
echo -------------------------------
echo Presiona CTRL+C en esta ventana para detener el servidor.
echo.

start "" python manage.py runserver

:: Esperar 3 segundos y abrir navegador
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000/"

:: Mantener la ventana abierta para ver logs
pause