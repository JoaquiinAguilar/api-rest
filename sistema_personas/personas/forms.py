from django import forms
from django.core.validators import RegexValidator
from .models import Persona
#cambio de rama
class PersonaForm(forms.ModelForm):
    """Formulario para el modelo Persona"""
    
    # Validadores personalizados
    telefono_validator = RegexValidator(
        regex=r'^\d{10}$',
        message='El número de teléfono debe tener 10 dígitos numéricos.'
    )
    
    # Campos con validaciones adicionales
    telefono = forms.CharField(
        max_length=15,
        validators=[telefono_validator],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 5512345678'})
    )
    
    class Meta:
        model = Persona
        fields = ['nombre', 'apellidos', 'sexo', 'telefono', 'correo', 'direccion', 'foto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'sexo': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'sexo': 'Seleccione el género',
            'foto': 'Tamaño máximo 5MB. Formatos: JPG, PNG'
        }
        error_messages = {
            'nombre': {'required': 'El nombre es obligatorio'},
            'apellidos': {'required': 'Los apellidos son obligatorios'},
            'telefono': {'required': 'El número de teléfono es obligatorio'},
            'correo': {'required': 'El correo electrónico es obligatorio', 'invalid': 'Ingrese un correo válido'},
            'direccion': {'required': 'La dirección es obligatoria'},
        }

class BusquedaForm(forms.Form):
    """Formulario para búsqueda de personas"""
    
    q = forms.CharField(
        label='Buscar',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Buscar por nombre, apellido, correo...',
            'aria-label': 'Buscar'
        })
    )

class HuellaDigitalForm(forms.Form):
    """Formulario para captura de huella digital"""
    
    huella = forms.ImageField(
        label='Archivo de Huella Digital',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    def clean_huella(self):
        huella = self.cleaned_data.get('huella')
        if huella:
            # Validar tamaño máximo (5MB)
            if huella.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo es demasiado grande. El tamaño máximo es 5MB.')
                
            # Validar formato (solo PNG y JPG)
            if not huella.name.endswith(('.png', '.jpg', '.jpeg')):
                raise forms.ValidationError('Formato no soportado. Use PNG o JPG.')
                
        return huella