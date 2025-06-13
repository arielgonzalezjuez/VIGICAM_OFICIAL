from django import forms
from .models import Persona, Camara, Cliente
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'carnet_identidad', 'cargo', 'imagen', 'horaE','horaS']

class CamaraForm(forms.ModelForm):
    class Meta:
        model = Camara
        fields = ['nombreC', 'numero_ip', 'puerto','usuario','password']

class ClienteRegistrarForm(UserCreationForm):
    class Meta:
        model = Cliente
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'direccion', 'password1', 'password2')

class ClienteActualizarForm(UserChangeForm):
    class Meta:
        model = Cliente
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'direccion')
   
class TelegramForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['telegram_chat_id']
        widgets = {
            'telegram_chat_id': forms.TextInput(attrs={
                'placeholder': 'Ej: 123456789',
                'class': 'form-input'
            })
        }
        labels = {
            'telegram_chat_id': 'Chat ID de Telegram para notificaciones'
        }
        help_texts = {
            'telegram_chat_id': 'Obtén tu ID con @userinfobot en Telegram'
        }
