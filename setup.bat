@echo off
call install.bat
if %errorlevel% equ 0 (
    call runserver.bat
)