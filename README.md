Ubicación de los principales códigos:
• Almacenamiento en BD: models.py
• Detección de Rostro: views.py - linea (591)
• Registro de Rostro: views.py - linea (918)
• Servicios Web: views.py - (Conexión con la cámara)linea (986), (reconocimiento facial) linea (885,791, 986)


# 🚀 VigiCam - Sistema de Videovigilancia Inteligente

![Django](https://img.shields.io/badge/Django-5.2.1-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-yellow)

Sistema avanzado de control de acceso mediante reconocimiento facial con notificaciones en tiempo real vía Telegram.

## 📦 Requisitos Mínimos

- 🖥️ Windows 10/11 (64-bit)
- 🐍 Python 3.12 ([Descargar](https://www.python.org/downloads/))
- 🐘 PostgreSQL 15+ ([Descargar](https://www.postgresql.org/download/))
- 💾 4GB RAM mínimo
- 🗃️ 2GB de espacio libre

## 🛠 Instalación Paso a Paso

### 1️⃣ Descargar el proyecto
1. Haz clic en `Code` → `Download ZIP` [en GitHub](https://github.com/arielgonzalezjuez/VIGICAM_OFICIAL.git)
2. Guarda el archivo `VIGICAM_OFICIAL-main.zip` en tu carpeta de documentos
3. Extraer archivo donde desee

### 2️⃣ Configurar PostgreSQL 
🖱️ Ejecuta pgAdmin 4 desde el menú Inicio
🔍 Navega a:
text
Servers → PostgreSQL 15 → Databases
🛠️ Haz clic derecho → Create → Database...
📝 Completa los campos:
Name: db_vigi_cam
Owner: postgres
💾 Haz clic en Save

4️⃣ Instalación automática (Windows)
📂 Navega a la carpeta del proyecto
⚙️ Haz doble clic en setup.bat
⏳ Espera a que complete:
📦 Instalación de dependencias
🗃️ Migraciones de base de datos
👨💻 Creación de usuario admin
✅ Verás el mensaje: "¡Instalación completada!"

5️⃣ Primer inicio
🔑 Credenciales predeterminadas:
   Usuario: root
   Contraseña: root
