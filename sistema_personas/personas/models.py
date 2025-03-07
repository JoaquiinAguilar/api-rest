from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    sexo = models.BooleanField(default=False, help_text="0=Mujer, 1=Hombre")
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(max_length=100)
    direccion = models.TextField()
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)
    huella_digital = models.ImageField(upload_to='huellas/', null=True, blank=True)
    huella_hex = models.TextField(null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['-fecha_registro']