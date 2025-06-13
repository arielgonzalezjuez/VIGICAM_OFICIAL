# import requests
from django.conf import settings
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def enviar_foto_telegram(imagen_path, mensaje=""):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    session = requests.Session()
    retries = Retry(
        total=3,  # 3 reintentos
        backoff_factor=1,  # Espera entre reintentos: 1s, 2s, 4s
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=frozenset(['POST'])
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        with open(imagen_path, 'rb') as foto:
            files = {'photo': foto}
            data = {'chat_id': settings.TELEGRAM_CHAT_ID, 'caption': mensaje[:1024]}
            response = session.post(url, files=files, data=data, timeout=10)  # Timeout de 10s
            return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False