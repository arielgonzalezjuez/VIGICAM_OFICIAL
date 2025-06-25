@echo off
:: Configuración indestructible para Django
title SERVIDOR DJANGO - [NO CERRAR]
color 0A
cls

:: 1. Verificación mejorada de Python y Django
where python >nul 2>nul || (
    echo [ERROR] Python no encontrado en el PATH
    echo Instale Python y marque "Add to PATH"
    pause
    exit /b
)

if not exist "manage.py" (
    echo [ERROR] Ejecute desde la raíz del proyecto Django
    pause
    exit /b
)

:: 2. Activación de entorno virtual con verificación
if exist "venv\Scripts\activate" (
    call venv\Scripts\activate
    python -c "print('>> Entorno virtual ACTIVADO')" || (
        echo [ERROR] Fallo al activar el entorno
        pause
        exit /b
    )
)

:: 3. Migraciones automáticas con feedback
echo Aplicando migraciones...
python manage.py migrate --noinput && (
    echo [OK] Migraciones aplicadas
) || (
    echo [ERROR] Fallo en migraciones
    pause
    exit /b
)

echo Verificando superusuario...
python crear_superusuario.py || (
    echo [AVISO] Error al verificar usuario
    echo Ejecute manualmente: python manage.py createsuperuser
)


:: 5. Inicio INDEPENDIENTE del servidor
echo Iniciando servidor Django...
echo ==============================
echo URL: http://localhost:8000
echo Credenciales: root / root
echo ==============================
echo.

:: Método infalible para mantener el servidor corriendo
start "Django Server" /B cmd /c "python manage.py runserver && pause"

:: Espera segura antes de abrir navegador
timeout /t 8 /nobreak >nul

:: Abrir navegador sólo si el servidor está activo
tasklist | find "python.exe" >nul && (
    start "" "http://localhost:8000"
)

:: Mantener esta ventana abierta
pause