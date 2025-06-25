@echo off
:: Configuración mejorada
title SERVIDOR DJANGO - [CIERRE AUTOMÁTICO]
color 0A
cls

:: 1. Verificación de requisitos
where python >nul 2>nul || (
    echo [ERROR] Python no encontrado en el PATH
    pause
    exit /b
)

if not exist "manage.py" (
    echo [ERROR] Ejecute desde la raíz del proyecto Django
    pause
    exit /b
)

:: 2. Activación de entorno virtual
if exist "venv\Scripts\activate" call venv\Scripts\activate

:: 3. Migraciones
echo Aplicando migraciones...
python manage.py migrate --noinput || (
    echo [ERROR] Fallo en migraciones
    pause
    exit /b
)

:: 4. Creación de superusuario
echo Verificando superusuario...
python crear_superusuario.py || (
    echo [AVISO] Error al verificar usuario
)

:: 5. Inicio del servidor con cierre controlado
echo Iniciando servidor Django...
echo ==============================
echo URL: http://localhost:8000
echo Credenciales: root / root
echo ==============================
echo.

:: Iniciar servidor y capturar PID
start "Django Server" /B cmd /c "python manage.py runserver & pause"
for /f "tokens=2" %%a in ('tasklist /fi "WINDOWTITLE eq Django Server*" /nh') do set PID=%%a

:: Esperar y abrir navegador
timeout /t 5 /nobreak >nul
start "" "http://localhost:8000"

:: Esperar a que el usuario cierre esta ventana
pause

:: Cerrar el servidor al salir
taskkill /pid %PID% /f >nul 2>&1