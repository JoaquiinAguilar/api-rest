import os
import uuid
import hashlib
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def optimize_image(image, max_size=(800, 800), quality=85, format='JPEG'):
    """
    Optimiza una imagen para reducir su tamaño, manteniendo una buena calidad.
    
    Args:
        image: Objeto de archivo de imagen (de request.FILES)
        max_size: Tupla con el tamaño máximo (ancho, alto)
        quality: Calidad de compresión (1-100)
        format: Formato de salida ('JPEG', 'PNG')
        
    Returns:
        ContentFile: Objeto ContentFile con la imagen optimizada
    """
    if not image:
        return None
        
    # Abrir imagen
    img = Image.open(image)
    
    # Convertir a RGB si es necesario (para evitar problemas con RGBA)
    if img.mode not in ('L', 'RGB'):
        img = img.convert('RGB')
    
    # Redimensionar si es necesario
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.LANCZOS)
    
    # Guardar imagen optimizada
    output = BytesIO()
    img.save(output, format=format, quality=quality, optimize=True)
    
    # Crear ContentFile desde BytesIO
    output.seek(0)
    content_file = ContentFile(output.read())
    
    return content_file

def generate_unique_filename(instance, filename):
    """
    Genera un nombre de archivo único para evitar colisiones.
    
    Args:
        instance: Instancia del modelo
        filename: Nombre original del archivo
        
    Returns:
        str: Ruta del archivo con nombre único
    """
    ext = filename.split('.')[-1]
    uid = uuid.uuid4().hex
    
    if hasattr(instance, 'nombre') and hasattr(instance, 'apellidos'):
        nombre_slug = f"{instance.nombre}-{instance.apellidos}".lower().replace(' ', '-')
        return f"{nombre_slug}-{uid}.{ext}"
    else:
        return f"{uid}.{ext}"

def validate_file_type(file, allowed_types=None):
    """
    Valida que el tipo de archivo sea uno de los permitidos.
    
    Args:
        file: Objeto de archivo (de request.FILES)
        allowed_types: Lista de extensiones permitidas (sin el punto)
        
    Returns:
        bool: True si el tipo de archivo es válido, False en caso contrario
    """
    if not file:
        return False
        
    if not allowed_types:
        allowed_types = ['jpg', 'jpeg', 'png']
        
    ext = os.path.splitext(file.name)[1][1:].lower()
    
    return ext in allowed_types

def validate_file_size(file, max_size_mb=5):
    """
    Valida que el tamaño del archivo no exceda el máximo permitido.
    
    Args:
        file: Objeto de archivo (de request.FILES)
        max_size_mb: Tamaño máximo en MB
        
    Returns:
        bool: True si el tamaño es válido, False en caso contrario
    """
    if not file:
        return False
        
    return file.size <= max_size_mb * 1024 * 1024

def remove_temp_files(temp_dir='temp', older_than_hours=24):
    """
    Elimina archivos temporales del almacenamiento.
    
    Args:
        temp_dir: Directorio temporal
        older_than_hours: Eliminar archivos más antiguos que estas horas
    """
    pass  # Implementación depende del almacenamiento específico