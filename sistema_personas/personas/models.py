import os
import sys
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import default_storage

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

    def delete(self, *args, **kwargs):
        """
        Override delete method to remove associated files
        """
        # Debug: Imprimir información detallada
        print("\n--- DEBUG: Iniciando eliminación de Persona ---")
        print(f"Nombre: {self.nombre} {self.apellidos}")
        
        # Almacenar rutas de archivos antes de eliminar
        foto_path = None
        if self.foto:
            try:
                # Intentar obtener la ruta absoluta de la foto
                foto_path = self.foto.path
                print(f"Ruta de foto detectada: {foto_path}")
                print(f"¿Existe la foto?: {os.path.exists(foto_path)}")
            except Exception as e:
                print(f"Error al obtener ruta de foto: {e}")
                # También imprimir el valor de self.foto para más contexto
                print(f"Valor de self.foto: {self.foto}")
        
        # Referencia al directorio de medios
        media_root = settings.MEDIA_ROOT
        print(f"MEDIA_ROOT: {media_root}")

        # Llamar al método de eliminación del padre
        super().delete(*args, **kwargs)

        # Eliminar archivo de foto
        if foto_path:
            try:
                # Intentar eliminar usando diferentes métodos
                if os.path.exists(foto_path):
                    # Eliminar usando os.remove
                    try:
                        os.remove(foto_path)
                        print(f"Foto eliminada con os.remove: {foto_path}")
                    except Exception as e:
                        print(f"Error al eliminar con os.remove: {e}")
                
                # Intentar eliminar usando default_storage
                try:
                    if default_storage.exists(foto_path):
                        default_storage.delete(foto_path)
                        print(f"Foto eliminada con default_storage: {foto_path}")
                except Exception as e:
                    print(f"Error al eliminar con default_storage: {e}")
            except Exception as e:
                print(f"Error general al eliminar foto: {e}")
                # Imprimir la traza completa del error
                import traceback
                traceback.print_exc(file=sys.stdout)

        print("--- FIN DE DEPURACIÓN DE ELIMINACIÓN ---\n")

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['-fecha_registro']

# Señal de respaldo para eliminación de archivos
@receiver(post_delete, sender=Persona)
def delete_persona_files(sender, instance, **kwargs):
    """
    Receptor de señal para eliminar archivos después de eliminar la instancia
    """
    def remove_file(field, file_type):
        if field:
            try:
                # Intentar obtener la ruta del archivo
                try:
                    file_path = field.path
                except Exception as e:
                    print(f"Error al obtener ruta de {file_type}: {e}")
                    return

                print(f"\n--- Eliminando {file_type} ---")
                print(f"Ruta del archivo: {file_path}")
                print(f"¿Existe el archivo?: {os.path.exists(file_path)}")
                
                # Intentar eliminar con os.remove
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"{file_type} eliminado con os.remove")
                except Exception as e:
                    print(f"Error al eliminar {file_type} con os.remove: {e}")
                
                # Intentar eliminar con default_storage
                try:
                    if default_storage.exists(file_path):
                        default_storage.delete(file_path)
                        print(f"{file_type} eliminado con default_storage")
                except Exception as e:
                    print(f"Error al eliminar {file_type} con default_storage: {e}")
            except Exception as e:
                print(f"Error general al eliminar {file_type}: {e}")
                import traceback
                traceback.print_exc(file=sys.stdout)

    # Eliminar archivos asociados
    remove_file(instance.foto, "Foto")
    remove_file(instance.huella_digital, "Huella digital")
    remove_file(instance.qr_code, "Código QR")