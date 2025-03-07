from django.contrib import admin
from .models import Persona
# Register your models here.


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellidos', 'sexo', 'telefono', 'correo', 'fecha_registro')
    list_filter = ('sexo', 'fecha_registro')
    search_fields = ('nombre', 'apellidos', 'correo', 'telefono', 'huella_hex')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellidos', 'sexo', 'telefono', 'correo', 'direccion')
        }),
        ('Biometría', {
            'fields': ('foto', 'huella_digital', 'huella_hex', 'qr_code')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_registro', 'fecha_actualizacion')
        }),
    )