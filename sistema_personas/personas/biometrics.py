import os
import qrcode
import hashlib
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def generate_sha256_from_image(image_file):
    """Genera un hash SHA-256 a partir de un archivo de imagen"""
    hasher = hashlib.sha256()
    for chunk in image_file.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()

def generate_qr_from_hash(hash_value):
    """Genera un código QR a partir de un hash"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(hash_value)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{hash_value[:10]}.png")

def compare_fingerprint(stored_hex, uploaded_image):
    """Compara una huella digital almacenada con una imagen subida"""
    uploaded_hex = generate_sha256_from_image(uploaded_image)
    return stored_hex == uploaded_hex

def process_fingerprint(fingerprint_image):
    """Procesa una imagen de huella digital y devuelve el hash y el código QR"""
    fingerprint_hex = generate_sha256_from_image(fingerprint_image)
    qr_image = generate_qr_from_hash(fingerprint_hex)
    return fingerprint_hex, qr_image