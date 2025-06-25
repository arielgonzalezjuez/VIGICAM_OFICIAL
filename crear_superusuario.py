import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuraciones.settings')
import django
try:
    django.setup()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='root').exists():
        User.objects.create_superuser('root', 'root@gmail.com', 'root')
        print('\n>> Superusuario CREADO: root/root')
    else:
        print('\n>> Superusuario EXISTE')
except Exception as e:
    print(f'\n>> ERROR: {str(e)}')
