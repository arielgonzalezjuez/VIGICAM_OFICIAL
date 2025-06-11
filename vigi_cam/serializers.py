from rest_framework import serializers
from .models import (
    Persona, 
    Camara, 
    RegistroAcceso, 
    Cliente,
    Video, 
    HorarioEmpresa
)
from django.contrib.auth import get_user_model

User = get_user_model()

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = [
            'id',
            'nombre',
            'carnet_identidad',
            'cargo',
            'imagen',
            'horaE',
            'horaS'
        ]
        read_only_fields = ['horaE', 'horaS']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.imagen:
            representation['imagen'] = instance.imagen.url
        else:
            representation['imagen'] = None
        return representation

class CamaraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camara
        fields = [
            'id',
            'nombreC',
            'numero_ip',
            'puerto',
            'usuario',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

class RegistroAccesoSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source='persona.nombre', read_only=True)
    imagen_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RegistroAcceso
        fields = [
            'id',
            'persona',
            'persona_nombre',
            'fecha_hora',
            'imagen_capturada',
            'imagen_url'
        ]
    
    def get_imagen_url(self, obj):
        if obj.imagen_capturada:
            return self.context['request'].build_absolute_uri(obj.imagen_capturada.url)
        return None

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'direccion',
            'telefono',
            'is_staff',
            'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

class VideoSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'file',
            'file_url',
            'uploaded_at'
        ]
    
    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None

class HorarioEmpresaSerializer(serializers.ModelSerializer):
    dia_display = serializers.CharField(source='get_dia_display', read_only=True)
    actualizado_por = serializers.StringRelatedField()
    
    class Meta:
        model = HorarioEmpresa
        fields = [
            'id',
            'dia',
            'dia_display',
            'abre',
            'cierra',
            'cerrado',
            'ultima_actualizacion',
            'actualizado_por'
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Formatear horas para mostrar
        if representation['abre']:
            representation['abre'] = instance.abre.strftime('%H:%M')
        if representation['cierra']:
            representation['cierra'] = instance.cierra.strftime('%H:%M')
        return representation

class HorarioGroupSerializer(serializers.Serializer):
    dias = serializers.ListField(child=serializers.CharField())
    first_day_name = serializers.CharField()
    last_day_name = serializers.CharField()
    abre = serializers.TimeField(format='%H:%M', allow_null=True)
    cierra = serializers.TimeField(format='%H:%M', allow_null=True)
    cerrado = serializers.BooleanField()