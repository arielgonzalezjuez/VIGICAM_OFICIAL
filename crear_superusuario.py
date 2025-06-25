import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuraciones.settings')

import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='root').exists():
    user = User.objects.create_superuser(
        username='root',
        email='root@gmail.com',
        password='root'
    )
    user.rol = User.Rol.ADMINISTRADOR  # Asignar el rol personalizado
    user.save()
    print('\n>> Superusuario CREADO: root / root')
else:
    print('\n>> Superusuario EXISTE')
