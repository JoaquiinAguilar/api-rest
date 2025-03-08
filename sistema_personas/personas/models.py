from django.db import models
from django.contrib.auth.models import User

# Modelo para roles
class Rank(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Rol")
    can_read = models.BooleanField(default=False, verbose_name="Puede Leer")
    can_edit = models.BooleanField(default=False, verbose_name="Puede Editar")
    can_add = models.BooleanField(default=False, verbose_name="Puede Agregar")
    can_delete = models.BooleanField(default=False, verbose_name="Puede Eliminar")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

# Modelo para perfiles de usuario
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    rank = models.ForeignKey(Rank, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Rol")

    def __str__(self):
        return f"{self.user.username} - {self.rank.name if self.rank else 'Sin Rol'}"

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

# Modelo Persona (ya existente)
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