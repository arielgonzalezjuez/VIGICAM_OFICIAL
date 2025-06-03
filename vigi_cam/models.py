from django.db import models
from django.contrib.auth.models import AbstractUser
from collections import namedtuple
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import FileExtensionValidator

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    carnet_identidad = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    imagen = models.ImageField(
        upload_to='imagenes_personas/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    horaE = models.TimeField(null=True, blank=True)
    horaS = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Solo establecer valores por defecto si no se han especificado
        if not self.horaE:
            self.horaE = self.get_horario_empresa_default('abre')
        if not self.horaS:
            self.horaS = self.get_horario_empresa_default('cierra')
        super().save(*args, **kwargs)

    def get_horario_empresa_default(self, campo_horario):
        """
        Obtiene el horario predeterminado de la empresa para el día actual
        campo_horario: 'abre' o 'cierra'
        """
        try:
            # Obtener el día actual en formato de HorarioEmpresa (ej. 'LUN', 'MAR')
            dia_actual = timezone.localtime().strftime('%a').upper()[:3]
            
            # Mapeo de días en inglés a español
            dias_traduccion = {
                'MON': 'LUN',
                'TUE': 'MAR',
                'WED': 'MIE',
                'THU': 'JUE',
                'FRI': 'VIE',
                'SAT': 'SAB',
                'SUN': 'DOM'
            }
            dia_actual_es = dias_traduccion.get(dia_actual, dia_actual)
            
            horario = HorarioEmpresa.objects.get(dia=dia_actual_es)
            
            if campo_horario == 'abre' and not horario.cerrado:
                return horario.abre
            elif campo_horario == 'cierra' and not horario.cerrado:
                return horario.cierra
            
        except ObjectDoesNotExist:
            # Si no existe horario para el día actual, usar valores por defecto
            if campo_horario == 'abre':
                return timezone.datetime.strptime('08:00:00', '%H:%M:%S').time()
            else:
                return timezone.datetime.strptime('17:00:00', '%H:%M:%S').time()
        
        # Si está cerrado o no se encontró horario, usar valores por defecto
        if campo_horario == 'abre':
            return timezone.datetime.strptime('08:00:00', '%H:%M:%S').time()
        else:
            return timezone.datetime.strptime('17:00:00', '%H:%M:%S').time()
    
class Camara(models.Model):
    nombreC = models.CharField(max_length=50)
    numero_ip = models.CharField(max_length=100)
    puerto = models.IntegerField()
    usuario = models.CharField(max_length=100, default='admin')
    password = models.CharField(max_length=100, default='aB12345678')

    def _str_(self):
        return self.nombreC

class RegistroAcceso(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    imagen_capturada = models.ImageField(upload_to='imagenes_capturadas/')

    def __str__(self):
        return f"{self.persona or 'Desconocido'} - {self.fecha_hora}"

    def _str_(self):
        return f'{self.persona.nombre} - {self.fecha_hora}'

class Cliente(AbstractUser):
      direccion = models.CharField(max_length=200)
      telefono = models.CharField(max_length=20)
      
      def __str__(self):
          return self.first_name
      
class Video(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='videos_capturados/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
HorarioGroup = namedtuple('HorarioGroup', ['dias', 'abre', 'cierra', 'cerrado'])

class HorarioEmpresa(models.Model):
    DIAS_SEMANA = [
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
        ('DOM', 'Domingo'),
    ]
    
    dia = models.CharField(max_length=3, choices=DIAS_SEMANA, unique=True)
    abre = models.TimeField(null=True, blank=True)
    cierra = models.TimeField(null=True, blank=True)
    cerrado = models.BooleanField(default=False)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        if self.cerrado:
            return f"{self.get_dia_display()}: Cerrado"
        return f"{self.get_dia_display()}: {self.abre.strftime('%I:%M %p')} - {self.cierra.strftime('%I:%M %p')}"
    
    def get_horario_group(self):
        """
        Retorna una tupla nombrada para agrupar horarios iguales
        """
        return HorarioGroup(
            dias=[self],  # Esto se modificará en la vista
            abre=self.abre,
            cierra=self.cierra,
            cerrado=self.cerrado
        )
    
    class Meta:
        ordering = ['dia']  # Esto asegura el orden por defecto
        verbose_name = "Horario de la empresa"
        verbose_name_plural = "Horarios de la empresa"