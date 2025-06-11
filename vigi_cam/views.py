from django.shortcuts import render, redirect, get_object_or_404
from .models import Persona, RegistroAcceso, Camara, Video,Cliente, HorarioEmpresa
from .forms import PersonaForm, CamaraForm
from django.http import StreamingHttpResponse
import numpy as np
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
import cv2
from datetime import datetime
from django.conf import settings
import os
import time
from onvif import ONVIFCamera, ONVIFError
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Video
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse

from django.shortcuts import render, get_object_or_404, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Camara
from .forms import CamaraForm
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import HorarioEmpresa
from django.utils import timezone
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .telegram_notifications import enviar_foto_telegram

import cv2
import numpy as np
import os
import time
from datetime import datetime
from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils import timezone
import threading
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
import face_recognition

def index(request):
    return render(request, 'index.html')

@login_required
def about(request):
    if not HorarioEmpresa.objects.exists():
        default_hours = {
            'LUN': ('08:00', '18:00', False),
            'MAR': ('08:00', '18:00', False),
            'MIE': ('08:00', '18:00', False),
            'JUE': ('08:00', '18:00', False),
            'VIE': ('08:00', '18:00', False),
            'SAB': ('09:00', '14:00', False),
            'DOM': (None, None, True)
        }
        
        for dia, (apertura, cierre, cerrado) in default_hours.items():
            HorarioEmpresa.objects.create(
                dia=dia,
                abre=datetime.strptime(apertura, '%H:%M').time() if apertura else None,
                cierra=datetime.strptime(cierre, '%H:%M').time() if cierre else None,
                cerrado=cerrado
            )
    
    horarios = HorarioEmpresa.objects.all()
    
    # Diccionario para orden personalizado
    dia_order = {'LUN': 0, 'MAR': 1, 'MIE': 2, 'JUE': 3, 'VIE': 4, 'SAB': 5, 'DOM': 6}
    
    grouped_horarios = []
    current_group = None
    
    # Ordenar los horarios según el orden de la semana
    horarios_ordenados = sorted(horarios, key=lambda x: dia_order[x.dia])
    
    for horario in horarios_ordenados:
        if current_group is None:
            current_group = {
                'dias': [horario],
                'first_day_name': horario.get_dia_display(),
                'last_day_name': horario.get_dia_display(),
                'abre': horario.abre,
                'cierra': horario.cierra,
                'cerrado': horario.cerrado
            }
        else:
            if (horario.abre == current_group['abre'] and 
                horario.cierra == current_group['cierra'] and 
                horario.cerrado == current_group['cerrado']):
                
                current_group['dias'].append(horario)
                current_group['last_day_name'] = horario.get_dia_display()
            else:
                grouped_horarios.append(current_group)
                current_group = {
                    'dias': [horario],
                    'first_day_name': horario.get_dia_display(),
                    'last_day_name': horario.get_dia_display(),
                    'abre': horario.abre,
                    'cierra': horario.cierra,
                    'cerrado': horario.cerrado
                }
    
    if current_group is not None:
        grouped_horarios.append(current_group)
    
    if request.method == 'POST' and request.user.is_staff:
        for dia in ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']:
            horario = HorarioEmpresa.objects.get(dia=dia)
            prefix = f"horario_{dia}"
            
            cerrado = f"{prefix}_cerrado" in request.POST
            
            if cerrado:
                horario.cerrado = True
                horario.abre = None
                horario.cierra = None
            else:
                hora_apertura = request.POST.get(f"{prefix}_abre")
                hora_cierre = request.POST.get(f"{prefix}_cierra")
                
                horario.cerrado = False
                horario.abre = datetime.strptime(hora_apertura, '%H:%M').time() if hora_apertura else None
                horario.cierra = datetime.strptime(hora_cierre, '%H:%M').time() if hora_cierre else None
            
            horario.actualizado_por = request.user
            horario.save()
        
        return redirect('about')
    
    horarios_individuales = HorarioEmpresa.objects.all().order_by('dia')
    
    # Para debug - verifica qué estás enviando a la plantilla
    print("Horarios agrupados:", grouped_horarios)
    print("Horarios individuales:", list(horarios_individuales.values('dia', 'abre', 'cierra', 'cerrado'))) 

    return render(request, 'about.html', {
        'grouped_horarios': grouped_horarios,  
        'horarios': horarios_ordenados      
    })

def inicio_sesion(request):
    if request.method == 'GET':
        return render(request, 'sign in.html', {'form':AuthenticationForm})
    else:
        cliente = authenticate(request,username=request.POST['username'], password=request.POST['password'])
        if cliente is None:
            return render(request, 'sign in.html', {'form':AuthenticationForm, 'error':'Usuario o contraseña incorrectos'})
        else:
            login(request,cliente)
            return redirect('index')

@login_required
def administrador(request):
    administradores = Cliente.objects.all().order_by('username')
    return render(request, 'administrador.html',{'administradores':administradores})

def registrarAdminFirstTime(request):
    if request.method == 'GET':
        return render(request, 'sign_up.html', {'form': UserCreationForm})
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request,user)
                return redirect('index')
            except IntegrityError:
                return render(request, 'sign_up.html', {'form': UserCreationForm, 'error':'Usuario ya existente'})
        return render(request, 'sign_up.html', {'form': UserCreationForm, 'error':'Contraseñas Incorrectas'})

User = get_user_model()
@require_http_methods(["GET", "POST"])
def registrar_admin(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Validaciones
        if not username:
            return JsonResponse({'success': False, 'message': 'El nombre de usuario es requerido'})
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Este nombre de usuario ya está en uso'})
        if not password:
            return JsonResponse({'success': False, 'message': 'La contraseña es requerida'})
        if len(password) < 8:
            return JsonResponse({'success': False, 'message': 'La contraseña debe tener al menos 8 caracteres'})

        # Creación
        try:
            user = User.objects.create_user(username=username, password=password)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al crear el usuario: {str(e)}'})

    # GET: mostrar lista completa
    administradores = User.objects.all()
    return render(request, 'administrador.html', {
        'administradores': administradores
    })


@require_POST
def editar_admin(request, admin_id):
    try:
        admin = User.objects.get(pk=admin_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Administrador no encontrado'})

    new_username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()

    # Validaciones
    if not new_username:
        return JsonResponse({'success': False, 'message': 'El nombre de usuario es requerido'})
    if User.objects.exclude(pk=admin_id).filter(username=new_username).exists():
        return JsonResponse({'success': False, 'message': 'Este nombre de usuario ya está en uso'})

    if password and len(password) < 8:
        return JsonResponse({'success': False, 'message': 'La contraseña debe tener al menos 8 caracteres'})

    # Actualización
    admin.username = new_username
    if password:
        admin.set_password(password)
    admin.save()
    return JsonResponse({'success': True})


@require_POST
def eliminar_administrador(request, id_administrador):
    try:
        admin = get_object_or_404(User, pk=id_administrador)
        admin.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al eliminar: {str(e)}'})


@require_http_methods(["GET"])
def buscar_admin(request):
    q = request.GET.get('q', '').strip()
    admins = User.objects.filter(username__icontains=q).order_by('username')
    data = [{'id': a.id, 'username': a.username} for a in admins]
    return JsonResponse({'administradores': data})



@login_required
def cerrarSession(request):
    logout(request) 
    return redirect('login')

# Vista para manejar la lista de personas y el registro de cámaras
@login_required
def trabajadores(request):
    personas = Persona.objects.all().order_by('nombre')
    return render(request, 'trabajadores.html', {'personas': personas})

@login_required
def registrar_persona(request):
    title = 'Registrar Persona'
    if request.method == 'POST':
        form = PersonaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('trabajadores')
    else:
        form = PersonaForm()
    return render(request, 'trabajadores.html', {'form': form, 'title': title})

@login_required
def editar_persona(request, id_persona):
    title = 'Editar Persona'
    persona = get_object_or_404(Persona, pk=id_persona)
    if request.method == 'POST':
        form = PersonaForm(request.POST, request.FILES, instance=persona)
        if form.is_valid():
            form.save()
            return redirect('trabajadores')
    else:
        form = PersonaForm(instance=persona)
    return render(request, 'trabajadores.html', {'form': form, 'persona': persona, 'title': title})

@login_required
def eliminar_persona(request, id_persona):
    persona = get_object_or_404(Persona, pk=id_persona)
    persona.delete()
    return redirect('trabajadores')

# Inicia el Trabajo con los registros de la camara
@login_required
def registro(request):
     registros = RegistroAcceso.objects.all().order_by('-fecha_hora')
     return render(request, 'registro.html', {'registros': registros})

@login_required
def eliminar_registro(request, id_registro):
    registro = get_object_or_404(RegistroAcceso, pk=id_registro)
    registro.delete()
    return redirect('registro')

@login_required
def eliminarregistros(request):
     RegistroAcceso.objects.all().delete()
     return redirect('registro')
# Finaliza el Trabajo con los registros de la camara

def reconocimiento(request):
    return render(request, 'reconocimiento.html')

# Inicio Trabajo con Camaras

def cameras(request):
    camaras = Camara.objects.all().order_by('nombreC')
    return render(request, 'reconocimiento.html',{'camaras': camaras})


@login_required
@require_POST
def registrar_camara(request):
    form = CamaraForm(request.POST)
    if form.is_valid():
        camara = form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'redirect_url': reverse('cameras')})
        return redirect('cameras')
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        return render(request, 'reconocimiento.html', {'form': form, 'errors': form.errors})

@login_required
@require_POST
def editar_camara(request, id_camara):
    camara = get_object_or_404(Camara, pk=id_camara)
    form = CamaraForm(request.POST, instance=camara)
    if form.is_valid():
        camara = form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'redirect_url': reverse('cameras')})
        return redirect('cameras')
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
@login_required
def eliminar_camara(request, id_camara):
    camara = get_object_or_404(Camara, pk=id_camara)
    try:
        camara.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@login_required
def reconocimiento_facial(request):
     cameras = Camara.objects.all()
     return render(request, 'reconocimiento.html', {'camaras': cameras})

# Fin Trabajo con camaras


# Inicio Trabajo con videos
def videos(request):
    videos = Video.objects.all()
    count = 0
    for video in videos:
        count = count + 1
        print(video.title)
    return render(request, 'videos.html', {'videos': videos, "count":count})

@require_GET
def eliminar_video(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        video_ids = request.GET.get('ids', '').split(',')
        try:
            # Eliminar videos seleccionados
            Video.objects.filter(id__in=video_ids).delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def eliminar_videos(request):
    if request.method == 'GET':
        Video.objects.all().delete()
        messages.success(request, 'Todos los videos han sido eliminados')
        return redirect('videos')

# Fin Trabajo con videos
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIN_FACE_SIZE = 80
TARGET_FPS = 10
CONFIDENCE_THRESHOLD = 0.7
RECOGNITION_THRESHOLD = 100
FRAME_SKIP = 1

def load_dnn_detector():
    """Carga el modelo de detección facial"""
    net = cv2.dnn.readNetFromCaffe(
        os.path.join(settings.BASE_DIR, 'models', 'deploy.prototxt'),
        os.path.join(settings.BASE_DIR, 'models', 'res10_300x300_ssd_iter_140000.caffemodel')
    )    
    return net

def improved_face_detection(frame, net):
    """Detección mejorada de rostros"""
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, 
                               (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    
    valid_faces = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > CONFIDENCE_THRESHOLD:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x, y, x2, y2) = box.astype("int")
            w_face = x2 - x
            h_face = y2 - y
            
            if (w_face >= MIN_FACE_SIZE and h_face >= MIN_FACE_SIZE and 
                0.5 < w_face/h_face < 2.0):
                valid_faces.append((x, y, w_face, h_face))
    return valid_faces

def train_recognizer(dnn_net):
    """Entrenamiento del reconocedor facial"""
    personas = Persona.objects.all()
    if not personas:
        return None, None

    faces = []
    labels = []
    label_map = {}
    
    for label, persona in enumerate(personas):
        try:
            if not persona.imagen:
                continue
                
            img = cv2.imread(persona.imagen.path)
            if img is None:
                continue
                
            faces_detected = improved_face_detection(img, dnn_net)
            for (x, y, w, h) in faces_detected:
                face_roi = cv2.cvtColor(img[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
                processed = cv2.resize(face_roi, (200, 200))
                processed = cv2.equalizeHist(processed)
                
                faces.append(processed)
                labels.append(label)
                faces.append(cv2.flip(processed, 1))
                labels.append(label)
                
                label_map[label] = persona
                
        except Exception as e:
            print(f"Error procesando {persona.nombre}: {e}")
            continue

    if faces:
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=2, neighbors=8, grid_x=8, grid_y=8)
        recognizer.train(faces, np.array(labels))
        print(f"Modelo entrenado con {len(faces)} muestras de {len(label_map)} personas")
        return recognizer, label_map
    
    print("Error: No se encontraron rostros válidos para entrenamiento")
    return None, None

def enhanced_recognizer_predict(recognizer, face_img, label_map):
    """Predicción mejorada con diagnóstico"""
    try:
        face_img = cv2.resize(face_img, (200, 200))
        face_img = cv2.equalizeHist(face_img)
        
        label, confidence = recognizer.predict(face_img)
        print(f"Predicción: Label={label}, Confianza={confidence}")
        
        if label not in label_map or confidence > RECOGNITION_THRESHOLD:
            return "Desconocido", confidence, (0, 0, 255)
        
        return label_map[label].nombre, confidence, (0, 255, 0)
    except Exception as e:
        print(f"Error en predicción: {e}")
        return "Desconocido", 100, (0, 0, 255)

def verify_media_dirs():
    """Verifica y crea los directorios necesarios con permisos"""
    try:
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas'), mode=0o777, exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'videos_capturados'), mode=0o777, exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'unknown_faces'), mode=0o777, exist_ok=True)
        print(f"Directorios verificados en: {settings.MEDIA_ROOT}")
        return True
    except Exception as e:
        print(f"Error creando directorios: {str(e)}")
        return False

def error_frame(message):
    """Genera un frame de error"""
    frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    cv2.putText(frame, message, (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    ret, jpeg = cv2.imencode('.jpg', frame)
    return jpeg.tobytes()

notification_timers = defaultdict(dict)
notification_lock = threading.Lock()

def schedule_telegram_notification(camera_name, absolute_path, mensaje):
    with notification_lock:
        # Cancelar temporizador existente
        if camera_name in notification_timers:
            notification_timers[camera_name]["timer"].cancel()
        
        # Determinar el intervalo de espera
        last_sent = notification_timers.get(camera_name, {}).get("last_sent")
        elapsed = datetime.now() - last_sent if last_sent else None
        delay = 0 if (not last_sent or elapsed > timedelta(minutes=5)) else 300
        
        # Crear temporizador
        timer = threading.Timer(
            interval=delay,
            function=lambda: send_telegram_notification(absolute_path, mensaje, camera_name)
        )
        timer.start()
        
        # Actualizar registro
        notification_timers[camera_name] = {
            "timer": timer,
            "last_sent": datetime.now() if delay == 0 else last_sent
        }

def send_telegram_notification(absolute_path, mensaje, camera_name):
    """Envia la notificación y actualiza el estado"""
    try:
        if os.path.exists(absolute_path):
            success = enviar_foto_telegram(absolute_path, mensaje)
            if success:
                print(f"Notificación enviada para {camera_name}")
                with notification_lock:
                    notification_timers[camera_name]["last_sent"] = datetime.now()
            else:
                print(f"Fallo al enviar notificación para {camera_name}")
        else:
            print(f"Archivo no encontrado: {absolute_path}")
    except Exception as e:
        print(f"Error enviando notificación: {str(e)}")

def save_and_notify_face(frame, face_roi, nombre, conf,camera_name):
    """Guarda la imagen detectada y envía notificación"""
    try:
        # Crear directorio si no existe
        img_dir = os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas')
        os.makedirs(img_dir, exist_ok=True)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        img_name = f"{nombre}_{timestamp}.jpg"
        img_path = os.path.join(img_dir, img_name)
        
        # Guardar imagen
        cv2.imwrite(img_path, face_roi)
        
        # Crear registro en la base de datos
        relative_path = os.path.join('imagenes_capturadas', img_name)
        persona = Persona.objects.filter(nombre=nombre).first() if nombre != "Desconocido" else None
        
        RegistroAcceso.objects.create(
            persona=persona,
            imagen_capturada=relative_path
        )
        
        ahora = timezone.localtime()
        dia_semana_ingles = ahora.strftime('%a').upper()[:3]  # 'MON', 'TUE', etc.

# Traducir a códigos en español usados en el modelo
        dias_traduccion = {
    'MON': 'LUN',
    'TUE': 'MAR',
    'WED': 'MIE',
    'THU': 'JUE',
    'FRI': 'VIE',
    'SAT': 'SAB',
    'SUN': 'DOM'
}
        dia_semana = dias_traduccion.get(dia_semana_ingles, dia_semana_ingles)

        fuera_de_horario = True  # Valor por defecto
        try:
            horario = HorarioEmpresa.objects.get(dia=dia_semana)  
          
            # Verificar condiciones de horario
            if not horario.cerrado:
                hora_actual = ahora.time()
                if horario.abre is not None and horario.cierra is not None:
                    fuera_de_horario = hora_actual < horario.abre or hora_actual > horario.cierra
                elif horario.abre is not None:
                    fuera_de_horario = hora_actual < horario.abre
                elif horario.cierra is not None:
                    fuera_de_horario = hora_actual > horario.cierra
                else:
                    fuera_de_horario = False
        except HorarioEmpresa.DoesNotExist:
            fuera_de_horario = True
        except Exception as e:
            print(f"Error al verificar horario: {e}")
            fuera_de_horario = True               
        print(f"Día: {dia_semana}, Hora actual: {ahora.time()}")
        try:
            print(f"Horario: Abre: {horario.abre}, Cierra: {horario.cierra}, Cerrado: {horario.cerrado}")
        except:
            print("No se pudo obtener información de horario")
        print(f"Fuera de horario: {fuera_de_horario}")
        
        # Enviar notificación a Telegram
        if fuera_de_horario:
            mensaje = f"⚠️ {'Intruso' if nombre == 'Desconocido' else 'Persona'} detectado fuera de horario\n"
            mensaje += f"👤 Nombre: {nombre}\n"
            mensaje += f"🕒 Fecha: {ahora.strftime('%d/%m/%Y %H:%M')}\n"
            mensaje += f"📍 Ubicación: {camera_name}"
            print('enviado sms')
            
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        
            with notification_lock:
                last_sent = notification_timers.get(camera_name, {}).get("last_sent")
            
            # Siempre programar la notificación, nunca enviar directamente
            schedule_telegram_notification(camera_name, absolute_path, mensaje)
        
            return True
    except Exception as e:
        print(f"Error al guardar/notificar rostro: {str(e)}")
        return False

def get_rtsp_url(ip, port, user, password):
    """Obtiene la URL RTSP con autenticación usando ONVIF"""
    try:
        # Crear cliente ONVIF
        cam = ONVIFCamera(ip, port, user, password)
        
        # Obtener servicio de medios
        media_service = cam.create_media_service()
        profiles = media_service.GetProfiles()
        
        if not profiles:
            print("No se encontraron perfiles de medios")
            return None
            
        # Usar primer perfil disponible
        profile_token = profiles[0].token
        
        # Obtener URI de stream
        stream_uri = media_service.GetStreamUri({
            'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': 'RTSP'},
            'ProfileToken': profile_token
        })
        
        # Parsear y agregar credenciales
        parsed = urlparse(stream_uri.Uri)
        netloc = f"{user}:{password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
            
        authenticated_url = parsed._replace(netloc=netloc).geturl()
        return f"{authenticated_url}?tcp"  # Forzar transporte TCP
        
    except ONVIFError as e:
        print(f"Error ONVIF: {str(e)}")
        return None
    except Exception as e:
        print(f"Error obteniendo RTSP: {str(e)}")
        return None

# Función principal modificada|
def robust_video_gen(camera_id=None):
    """Generador principal para cámaras IP"""
    cap = None
    out = None
    try:
        if not verify_media_dirs():
            yield error_frame("Error: No se pudieron crear directorios")
            return

        # Obtener configuración de la cámara
        try:
            camara = Camara.objects.get(id=camera_id)
            print(f"Conectando a: {camara.nombreC} ({camara.numero_ip})")
        except Camara.DoesNotExist:
            yield error_frame("Error: Cámara no registrada")
            return

        # Obtener URL RTSP
        rtsp_url = get_rtsp_url(
            camara.numero_ip,
            camara.puerto,
            camara.usuario,
            camara.password
        )
        
        if not rtsp_url:
            yield error_frame("Error: URL RTSP no disponible")
            return

        print(f"URL RTSP obtenida: {rtsp_url}")

        # Configurar captura de video con reintentos
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            yield error_frame("Error: Conexión RTSP fallida")
            return

        # Inicializar modelos
        dnn_net = load_dnn_detector()
        recognizer, label_map = train_recognizer(dnn_net)
        
        if recognizer is None:
            yield error_frame("Error: Modelo no entrenado")
            return

        # Configurar video de salida
        video_dir = os.path.join(settings.MEDIA_ROOT, 'videos_capturados')
        os.makedirs(video_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_name = f"video_{timestamp}.mp4"
        video_path = os.path.join(video_dir, video_name)
        
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(video_path, fourcc, TARGET_FPS, (FRAME_WIDTH, FRAME_HEIGHT))
        
        if not out.isOpened():
            yield error_frame("Error: No se pudo crear archivo de video")
            return

        last_detection = time.time()
        frame_count = 0
        last_reconnect = time.time()
        
        while True:
            # Reconexión preventiva cada 30 segundos
            if time.time() - last_reconnect > 30:
                cap.release()
                cap = cv2.VideoCapture(rtsp_url)
                last_reconnect = time.time()
                print("Reconexión preventiva realizada")

            start_time = time.time()
            ret, frame = cap.read()
            
            if not ret:
                print("Error leyendo frame, reintentando...")
                cap.release()
                cap = cv2.VideoCapture(rtsp_url)
                time.sleep(1)
                continue

            # Redimensionar si es necesario
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            
            # Procesamiento de rostros (igual que antes)
            faces = improved_face_detection(frame, dnn_net)
            
            for (x, y, w, h) in faces:
                try:
                    if y+h >= frame.shape[0] or x+w >= frame.shape[1]:
                        continue
                        
                    face_roi = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
                    nombre, conf, color = enhanced_recognizer_predict(recognizer, face_roi, label_map)
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, f"{nombre} ({conf:.1f})", (x, y-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    if time.time() - last_detection > 5:
                        save_and_notify_face(frame, frame[y:y+h, x:x+w], nombre, conf, camara.nombreC)
                        last_detection = time.time()
                        
                except Exception as e:
                    print(f"Error procesando rostro: {e}")
                    continue

            # Guardar frame en video
            if out.isOpened():
                out.write(frame)
                frame_count += 1

            # Stream de video
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            else:
                print("Error codificando frame JPEG")
                yield error_frame("Error codificando video")
                
            # Control FPS
            elapsed = time.time() - start_time
            time.sleep(max(0, (1/TARGET_FPS) - elapsed))
            
    except Exception as e:
        print(f"Error crítico en generador: {e}")
        yield error_frame(f"Error: {str(e)}")
        
    finally:
        if out and 'video_path' in locals() and frame_count > 0:
            out.release()
            if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                try:
                    relative_path = os.path.join('videos_capturados', video_name)
                    Video.objects.create(
                        title=f"Video {timestamp}",
                        file=relative_path,
                        uploaded_at=timezone.now()
                    )
                except Exception as e:
                    print(f"Error al guardar video: {e}")
        
        if cap:
            cap.release()

# Vista final (igual que antes)
def video_feed(request, camera_id):
    """Endpoint principal del video feed"""
    try:
        return StreamingHttpResponse(
            robust_video_gen(camera_id),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        print(f"Error en video_feed: {e}")
        return StreamingHttpResponse(
            iter([error_frame("Error inicializando cámara")]),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    
# Configuración de rendimiento (se mantiene igual)
# FRAME_WIDTH = 640
# FRAME_HEIGHT = 480
# MIN_FACE_SIZE = 80  # Ahora en píxeles (face_recognition trabaja con esto automáticamente)
# TARGET_FPS = 10
# CONFIDENCE_THRESHOLD = 0.7  # Ahora será la distancia de reconocimiento (menor es mejor)
# RECOGNITION_THRESHOLD = 0.6  # Nuevo umbral (valores típicos entre 0.5-0.6)
# FRAME_SKIP = 1

# from PIL import Image
# import io

# import numpy as np
# import cv2

# class FaceImagePreprocessor:
#     def __init__(self, image):
#         self.original_image = image
#         self.processed_image = None
#         self.error = None

#     def is_valid_image(self):
#         if self.original_image is None:
#             self.error = "Imagen es None"
#             return False
#         if not isinstance(self.original_image, np.ndarray):
#             self.error = "Imagen no es un np.ndarray"
#             return False
#         if self.original_image.ndim != 3:
#             self.error = f"Imagen no tiene 3 dimensiones: {self.original_image.shape}"
#             return False
#         if self.original_image.shape[2] not in [3, 4]:
#             self.error = f"Número de canales no soportado: {self.original_image.shape[2]}"
#             return False
#         return True

#     def convert(self):
#         if not self.is_valid_image():
#             return None

#         img = self.original_image

#         # Si tiene 4 canales (RGBA), quitar el canal alfa
#         if img.shape[2] == 4:
#             img = img[:, :, :3]

#         # Asegurar tipo uint8
#         if img.dtype != np.uint8:
#             try:
#                 img = img.astype(np.uint8)
#             except Exception as e:
#                 self.error = f"No se pudo convertir a uint8: {str(e)}"
#                 return None

#         # Convertir de BGR a RGB (si viene de OpenCV)
#         try:
#             img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#         except Exception as e:
#             self.error = f"Fallo en conversión BGR -> RGB: {str(e)}"
#             return None

#         self.processed_image = img
#         return img

#     def get_valid_rgb_image(self):
#         if self.processed_image is not None:
#             return self.processed_image
#         return self.convert()

#     def get_error(self):
#         return self.error

    
# def improved_face_detection(frame):
#     """Detección mejorada de rostros usando face_recognition"""
#     # Convertir de BGR (OpenCV) a RGB (face_recognition)
#     rgb_frame = frame[:, :, ::-1]
    
#     # Detectar caras (usamos el modelo CNN para mejor precisión, aunque es más lento)
#     face_locations = face_recognition.face_locations(rgb_frame, model="hog")  # Puedes usar "cnn" para mejor precisión
    
#     valid_faces = []
#     for (top, right, bottom, left) in face_locations:
#         w_face = right - left
#         h_face = bottom - top
        
#         if (w_face >= MIN_FACE_SIZE and h_face >= MIN_FACE_SIZE and 
#             0.5 < w_face/h_face < 2.0):
#             # Convertimos a formato (x, y, w, h) para mantener compatibilidad
#             valid_faces.append((left, top, w_face, h_face))
    
#     return valid_faces

# def train_recognizer():
#     personas = Persona.objects.all()
#     if not personas:
#         return None, None

#     known_face_encodings = []
#     known_face_names = []

#     for persona in personas:
#         try:
#             if not persona.imagen:
#                 continue
#             imagen = cv2.imread(persona.imagen.path)

#             if imagen is None:
#                 raise ValueError("No se pudo cargar la imagen. Verifica la ruta y el formato.")
#             preprocessor = FaceImagePreprocessor(imagen)
#             rgb_img = preprocessor.get_valid_rgb_image()

#             if rgb_img is None:
#                 print(f"{persona.nombre}: Error en preprocesamiento: {preprocessor.get_error()}")
#                 continue

#             face_locations = face_recognition.face_locations(rgb_img)
#             if not face_locations:
#                 print(f"{persona.nombre}: No se detectaron rostros")
#                 continue

#             encodings = face_recognition.face_encodings(rgb_img, face_locations)
#             known_face_encodings.extend(encodings)
#             known_face_names.extend([persona.nombre] * len(encodings))

#         except Exception as e:
#             print(f"Error procesando {persona.nombre}: {type(e).__name__} - {str(e)}")
#             continue

#     return (known_face_encodings, known_face_names) if known_face_encodings else (None, None)


# def enhanced_recognizer_predict(known_face_encodings, known_face_names, face_img):
#     try:
#         # Asegura formato correcto
#         if face_img.shape[2] == 4:
#             face_img = face_img[:, :, :3]
#         if face_img.dtype != np.uint8:
#             face_img = face_img.astype(np.uint8)
#         rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

#         encodings = face_recognition.face_encodings(rgb_img)
#         if not encodings:
#             return "Desconocido", 0.0, (0, 0, 255)

#         distances = face_recognition.face_distance(known_face_encodings, encodings[0])
#         best_match = np.argmin(distances)

#         if distances[best_match] <= RECOGNITION_THRESHOLD:
#             return (known_face_names[best_match],
#                     1 - distances[best_match],
#                     (0, 255, 0))
#         return "Desconocido", 1 - distances[best_match], (0, 0, 255)

#     except Exception as e:
#         print(f"Error en reconocimiento: {type(e).__name__} - {str(e)}")
#         return "Desconocido", 0.0, (0, 0, 255)


# def verify_media_dirs():
#     """Verifica y crea los directorios necesarios con permisos"""
#     try:
#         os.makedirs(os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas'), mode=0o777, exist_ok=True)
#         os.makedirs(os.path.join(settings.MEDIA_ROOT, 'videos_capturados'), mode=0o777, exist_ok=True)
#         os.makedirs(os.path.join(settings.MEDIA_ROOT, 'unknown_faces'), mode=0o777, exist_ok=True)
#         print(f"Directorios verificados en: {settings.MEDIA_ROOT}")
#         return True
#     except Exception as e:
#         print(f"Error creando directorios: {str(e)}")
#         return False

# def error_frame(message):
#     """Genera un frame de error"""
#     frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
#     cv2.putText(frame, message, (10, 30), 
#                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
#     ret, jpeg = cv2.imencode('.jpg', frame)
#     return jpeg.tobytes()

# notification_timers = defaultdict(dict)
# notification_lock = threading.Lock()

# def schedule_telegram_notification(camera_name, absolute_path, mensaje):
#     with notification_lock:
#         # Cancelar temporizador existente
#         if camera_name in notification_timers:
#             notification_timers[camera_name]["timer"].cancel()
        
#         # Determinar el intervalo de espera
#         last_sent = notification_timers.get(camera_name, {}).get("last_sent")
#         elapsed = datetime.now() - last_sent if last_sent else None
#         delay = 0 if (not last_sent or elapsed > timedelta(minutes=5)) else 300
        
#         # Crear temporizador
#         timer = threading.Timer(
#             interval=delay,
#             function=lambda: send_telegram_notification(absolute_path, mensaje, camera_name)
#         )
#         timer.start()
        
#         # Actualizar registro
#         notification_timers[camera_name] = {
#             "timer": timer,
#             "last_sent": datetime.now() if delay == 0 else last_sent
#         }

# def send_telegram_notification(absolute_path, mensaje, camera_name):
#     """Envia la notificación y actualiza el estado"""
#     try:
#         if os.path.exists(absolute_path):
#             success = enviar_foto_telegram(absolute_path, mensaje)
#             if success:
#                 print(f"Notificación enviada para {camera_name}")
#                 with notification_lock:
#                     notification_timers[camera_name]["last_sent"] = datetime.now()
#             else:
#                 print(f"Fallo al enviar notificación para {camera_name}")
#         else:
#             print(f"Archivo no encontrado: {absolute_path}")
#     except Exception as e:
#         print(f"Error enviando notificación: {str(e)}")

# def save_and_notify_face(frame, face_roi, nombre, conf,camera_name):
#     """Guarda la imagen detectada y envía notificación"""
#     try:
#         # Crear directorio si no existe
#         img_dir = os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas')
#         os.makedirs(img_dir, exist_ok=True)
        
#         # Generar nombre de archivo
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         img_name = f"{nombre}_{timestamp}.jpg"
#         img_path = os.path.join(img_dir, img_name)
        
#         # Guardar imagen
#         cv2.imwrite(img_path, face_roi)
        
#         # Crear registro en la base de datos
#         relative_path = os.path.join('imagenes_capturadas', img_name)
#         persona = Persona.objects.filter(nombre=nombre).first() if nombre != "Desconocido" else None
        
#         RegistroAcceso.objects.create(
#             persona=persona,
#             imagen_capturada=relative_path
#         )
        
#         ahora = timezone.localtime()
#         dia_semana_ingles = ahora.strftime('%a').upper()[:3]  # 'MON', 'TUE', etc.

# # Traducir a códigos en español usados en el modelo
#         dias_traduccion = {
#     'MON': 'LUN',
#     'TUE': 'MAR',
#     'WED': 'MIE',
#     'THU': 'JUE',
#     'FRI': 'VIE',
#     'SAT': 'SAB',
#     'SUN': 'DOM'
# }
#         dia_semana = dias_traduccion.get(dia_semana_ingles, dia_semana_ingles)

#         fuera_de_horario = True  # Valor por defecto
#         try:
#             horario = HorarioEmpresa.objects.get(dia=dia_semana)  
          
#             # Verificar condiciones de horario
#             if not horario.cerrado:
#                 hora_actual = ahora.time()
#                 if horario.abre is not None and horario.cierra is not None:
#                     fuera_de_horario = hora_actual < horario.abre or hora_actual > horario.cierra
#                 elif horario.abre is not None:
#                     fuera_de_horario = hora_actual < horario.abre
#                 elif horario.cierra is not None:
#                     fuera_de_horario = hora_actual > horario.cierra
#                 else:
#                     fuera_de_horario = False
#         except HorarioEmpresa.DoesNotExist:
#             fuera_de_horario = True
#         except Exception as e:
#             print(f"Error al verificar horario: {e}")
#             fuera_de_horario = True               
#         print(f"Día: {dia_semana}, Hora actual: {ahora.time()}")
#         try:
#             print(f"Horario: Abre: {horario.abre}, Cierra: {horario.cierra}, Cerrado: {horario.cerrado}")
#         except:
#             print("No se pudo obtener información de horario")
#         print(f"Fuera de horario: {fuera_de_horario}")
        
#         # Enviar notificación a Telegram
#         if fuera_de_horario:
#             mensaje = f"⚠️ {'Intruso' if nombre == 'Desconocido' else 'Persona'} detectado fuera de horario\n"
#             mensaje += f"👤 Nombre: {nombre}\n"
#             mensaje += f"🕒 Fecha: {ahora.strftime('%d/%m/%Y %H:%M')}\n"
#             mensaje += f"📍 Ubicación: {camera_name}"
#             print('enviado sms')
            
#             absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        
#             with notification_lock:
#                 last_sent = notification_timers.get(camera_name, {}).get("last_sent")
            
#             # Siempre programar la notificación, nunca enviar directamente
#             schedule_telegram_notification(camera_name, absolute_path, mensaje)
        
#             return True
#     except Exception as e:
#         print(f"Error al guardar/notificar rostro: {str(e)}")
#         return False

# def get_rtsp_url(ip, port, user, password):
#     """Obtiene la URL RTSP con autenticación usando ONVIF"""
#     try:
#         # Crear cliente ONVIF
#         cam = ONVIFCamera(ip, port, user, password)
        
#         # Obtener servicio de medios
#         media_service = cam.create_media_service()
#         profiles = media_service.GetProfiles()
        
#         if not profiles:
#             print("No se encontraron perfiles de medios")
#             return None
            
#         # Usar primer perfil disponible
#         profile_token = profiles[0].token
        
#         # Obtener URI de stream
#         stream_uri = media_service.GetStreamUri({
#             'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': 'RTSP'},
#             'ProfileToken': profile_token
#         })
        
#         # Parsear y agregar credenciales
#         parsed = urlparse(stream_uri.Uri)
#         netloc = f"{user}:{password}@{parsed.hostname}"
#         if parsed.port:
#             netloc += f":{parsed.port}"
            
#         authenticated_url = parsed._replace(netloc=netloc).geturl()
#         return f"{authenticated_url}?tcp"  # Forzar transporte TCP
        
#     except ONVIFError as e:
#         print(f"Error ONVIF: {str(e)}")
#         return None
#     except Exception as e:
#         print(f"Error obteniendo RTSP: {str(e)}")
#         return None

# def robust_video_gen(camera_id=None):
#     """Generador principal para cámaras IP con face_recognition"""
#     cap = None
#     out = None
#     try:
#         if not verify_media_dirs():
#             yield error_frame("Error: No se pudieron crear directorios")
#             return

#         # Obtener configuración de la cámara (igual)
#         try:
#             camara = Camara.objects.get(id=camera_id)
#             print(f"Conectando a: {camara.nombreC} ({camara.numero_ip})")
#         except Camara.DoesNotExist:
#             yield error_frame("Error: Cámara no registrada")
#             return

#         # Obtener URL RTSP (igual)
#         rtsp_url = get_rtsp_url(
#             camara.numero_ip,
#             camara.puerto,
#             camara.usuario,
#             camara.password
#         )
        
#         if not rtsp_url:
#             yield error_frame("Error: URL RTSP no disponible")
#             return

#         print(f"URL RTSP obtenida: {rtsp_url}")

#         # Configurar captura de video (igual)
#         cap = cv2.VideoCapture(rtsp_url)
#         if not cap.isOpened():
#             yield error_frame("Error: Conexión RTSP fallida")
#             return

#         # Inicializar modelos face_recognition
#         known_face_encodings, known_face_names = train_recognizer()
        
#         if known_face_encodings is None:
#             yield error_frame("Error: Modelo no entrenado")
#             return

#         # Configurar video de salida (igual)
#         video_dir = os.path.join(settings.MEDIA_ROOT, 'videos_capturados')
#         os.makedirs(video_dir, exist_ok=True)
        
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         video_name = f"video_{timestamp}.mp4"
#         video_path = os.path.join(video_dir, video_name)
        
#         fourcc = cv2.VideoWriter_fourcc(*'avc1')
#         out = cv2.VideoWriter(video_path, fourcc, TARGET_FPS, (FRAME_WIDTH, FRAME_HEIGHT))
        
#         if not out.isOpened():
#             yield error_frame("Error: No se pudo crear archivo de video")
#             return

#         last_detection = time.time()
#         frame_count = 0
#         last_reconnect = time.time()
        
#         while True:
#             # Reconexión preventiva (igual)
#             if time.time() - last_reconnect > 30:
#                 cap.release()
#                 cap = cv2.VideoCapture(rtsp_url)
#                 last_reconnect = time.time()
#                 print("Reconexión preventiva realizada")

#             start_time = time.time()
#             ret, frame = cap.read()
            
#             if not ret:
#                 print("Error leyendo frame, reintentando...")
#                 cap.release()
#                 cap = cv2.VideoCapture(rtsp_url)
#                 time.sleep(1)
#                 continue

#             # Redimensionar (igual)
#             frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            
#             # Procesamiento de rostros con face_recognition
#             faces = improved_face_detection(frame)
            
#             for (x, y, w, h) in faces:
#                 try:
#                     if y+h >= frame.shape[0] or x+w >= frame.shape[1]:
#                         continue
                        
#                     face_roi = frame[y:y+h, x:x+w]
#                     if face_roi is None or face_roi.shape[2] != 3:
#                         print("face_roi inválido o no RGB")
#                         continue

                    
#                     # Reconocimiento facial
#                     nombre, conf, color = enhanced_recognizer_predict(
#                         known_face_encodings, known_face_names, face_roi
#                     )
                    
#                     cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
#                     cv2.putText(frame, f"{nombre} ({conf:.2f})", (x, y-10),
#                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
#                     if time.time() - last_detection > 5:
#                         save_and_notify_face(frame, frame[y:y+h, x:x+w], nombre, conf, camara.nombreC)
#                         last_detection = time.time()
                        
#                 except Exception as e:
#                     print(f"Error procesando rostro: {e}")
#                     continue

#             # Guardar frame en video (igual)
#             if out.isOpened():
#                 out.write(frame)
#                 frame_count += 1

#             # Stream de video (igual)
#             ret, jpeg = cv2.imencode('.jpg', frame)
#             if ret:
#                 yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
#             else:
#                 print("Error codificando frame JPEG")
#                 yield error_frame("Error codificando video")
                
#             # Control FPS (igual)
#             elapsed = time.time() - start_time
#             time.sleep(max(0, (1/TARGET_FPS) - elapsed))
            
#     except Exception as e:
#         print(f"Error crítico en generador: {e}")
#         yield error_frame(f"Error: {str(e)}")
        
#     finally:
#         # Código de limpieza (igual)
#         if out and 'video_path' in locals() and frame_count > 0:
#             out.release()
#             if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
#                 try:
#                     relative_path = os.path.join('videos_capturados', video_name)
#                     Video.objects.create(
#                         title=f"Video {timestamp}",
#                         file=relative_path,
#                         uploaded_at=timezone.now()
#                     )
#                 except Exception as e:
#                     print(f"Error al guardar video: {e}")
        
#         if cap:
#             cap.release()

# def video_feed(request, camera_id):
#     """Endpoint principal del video feed"""
#     try:
#         return StreamingHttpResponse(
#             robust_video_gen(camera_id),
#             content_type='multipart/x-mixed-replace; boundary=frame'
#         )
#     except Exception as e:
#         print(f"Error en video_feed: {e}")
#         return StreamingHttpResponse(
#             iter([error_frame("Error inicializando cámara")]),
#             content_type='multipart/x-mixed-replace; boundary=frame'
#         )
