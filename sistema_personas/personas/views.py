from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

import json
import base64
import qrcode
import hashlib
from io import BytesIO
from PIL import Image

from .models import Persona
from .serializers import PersonaSerializer, PersonaListSerializer
from .biometrics import process_fingerprint, compare_fingerprint

# Create your views here.

# API REST ViewSets
class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'apellidos', 'correo', 'huella_hex']

    def get_serializer_class(self):
        if self.action == 'list':
            return PersonaListSerializer
        return PersonaSerializer

    @action(detail=False, methods=['post'])
    def buscar_por_huella(self, request):
        if 'huella' not in request.FILES:
            return Response({"error": "No se proporcionó archivo de huella digital"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        huella_image = request.FILES['huella']
        huella_hex = process_fingerprint(huella_image)[0]
        
        persona = Persona.objects.filter(huella_hex=huella_hex).first()
        if persona:
            serializer = self.get_serializer(persona)
            return Response(serializer.data)
        return Response({"message": "No se encontró ninguna persona con esa huella digital"}, 
                        status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Se requiere un término de búsqueda"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        personas = Persona.objects.filter(
            Q(nombre__icontains=query) | 
            Q(apellidos__icontains=query) | 
            Q(correo__icontains=query) |
            Q(telefono__icontains=query)
        )
        
        serializer = PersonaListSerializer(personas, many=True)
        return Response(serializer.data)

# Vistas para la interfaz web
@login_required
def dashboard(request):
    total_personas = Persona.objects.count()
    context = {
        'total_personas': total_personas
    }
    return render(request, 'personas/dashboard.html', context)

class PersonaListView(LoginRequiredMixin, ListView):
    model = Persona
    template_name = 'personas/lista_personas.html'
    context_object_name = 'personas'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        busqueda = self.request.GET.get('q')
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) | 
                Q(apellidos__icontains=busqueda) | 
                Q(correo__icontains=busqueda) |
                Q(telefono__icontains=busqueda)
            )
        return queryset

@login_required
def registro_paso1(request):
    if request.method == 'POST':
        # Guardar datos básicos en sesión, incluyendo los nuevos campos de dirección
        request.session['registro_persona'] = {
            'nombre': request.POST.get('nombre'),
            'apellidos': request.POST.get('apellidos'),
            'sexo': request.POST.get('sexo') == '1',
            'telefono': request.POST.get('telefono'),
            'correo': request.POST.get('correo'),
            'direccion': request.POST.get('direccion'),
            # Guardar también los campos individuales para mostrarlos en caso de edición
            'codigo_postal': request.POST.get('codigo_postal'),
            'estado': request.POST.get('estado'),
            'municipio': request.POST.get('municipio'),
            'colonia': request.POST.get('colonia'),
            'calle_numero': request.POST.get('calle_numero')
        }
        return redirect('registro_paso2')
    
    return render(request, 'personas/registro_paso1.html')

@login_required
def registro_paso2(request):
    """
    Vista para el paso 2 del registro: Captura de fotografía.
    Guarda la imagen ya sea cargada o capturada con la cámara.
    """
    if 'registro_persona' not in request.session:
        return redirect('registro_paso1')
    
    if request.method == 'POST':
        foto_guardada = False
        
        # Verificar si se ha cargado un archivo
        if 'foto' in request.FILES and request.FILES['foto']:
            try:
                # Guardar el archivo físicamente para verificar después
                from django.core.files.storage import FileSystemStorage
                import os
                from django.conf import settings
                
                # Crear directorio si no existe
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'fotos'), exist_ok=True)
                
                # Guardar el archivo directamente
                foto = request.FILES['foto']
                
                # Guardar el archivo en memoria para usarlo en paso 3
                request.session['registro_persona']['foto_temp'] = {
                    'nombre': foto.name,
                    'content_type': foto.content_type,
                    'size': foto.size
                }
                
                # También guardamos una copia en disco para respaldo
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'fotos'))
                filename = fs.save(f"temp_{request.user.id}_{foto.name}", foto)
                
                # Guardar la información en la sesión
                request.session['registro_persona']['foto_path'] = os.path.join('fotos', filename)
                request.session.modified = True  # Forzar actualización de la sesión
                
                foto_guardada = True
                print(f"Foto cargada desde archivo y guardada en: {request.session['registro_persona']['foto_path']}")
                
            except Exception as e:
                print(f"Error al guardar la foto desde archivo: {str(e)}")
                return render(request, 'personas/registro_paso2.html', {
                    'error': f'Error al procesar la imagen: {str(e)}'
                })
        
        # Verificar si se ha capturado una foto con la cámara
        elif request.POST.get('foto_base64'):
            try:
                # Si se capturó con la cámara
                img_data = request.POST.get('foto_base64').split(',')[1]
                img_binary = base64.b64decode(img_data)
                
                # Guardar en disco para respaldo
                from django.core.files.storage import FileSystemStorage
                import os
                import uuid
                from django.conf import settings
                
                # Crear directorio si no existe
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'fotos'), exist_ok=True)
                
                # Guardar la imagen con un nombre único
                filename = f"temp_camera_{request.user.id}_{uuid.uuid4()}.png"
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'fotos'))
                
                # Guardamos archivo en disco
                from django.core.files.base import ContentFile
                temp_file = ContentFile(img_binary)
                filename = fs.save(filename, temp_file)
                
                # Guardar la información en la sesión
                request.session['registro_persona']['foto_path'] = os.path.join('fotos', filename)
                request.session['registro_persona']['foto_from_camera'] = True
                request.session.modified = True  # Forzar actualización de la sesión
                
                foto_guardada = True
                print(f"Foto capturada desde cámara y guardada en: {request.session['registro_persona']['foto_path']}")
                
            except Exception as e:
                print(f"Error al guardar la foto desde cámara: {str(e)}")
                return render(request, 'personas/registro_paso2.html', {
                    'error': f'Error al procesar la imagen de la cámara: {str(e)}'
                })
        
        # Si no se guardó ninguna foto, mostrar un error
        if not foto_guardada:
            return render(request, 'personas/registro_paso2.html', {
                'error': 'Por favor, seleccione una imagen o capture una foto con la cámara.'
            })
        
        # Verificar que la información se guardó en la sesión
        if 'foto_path' in request.session['registro_persona']:
            print(f"Avanzando al paso 3 con foto_path: {request.session['registro_persona']['foto_path']}")
            return redirect('registro_paso3')
        else:
            # Si la foto no se guardó correctamente, mostrar un error
            return render(request, 'personas/registro_paso2.html', {
                'error': 'No se pudo guardar la foto. Por favor, inténtelo de nuevo.'
            })
    
    return render(request, 'personas/registro_paso2.html')

@login_required
def registro_paso3(request):
    """
    Vista para el paso 3 del registro: Captura de huella digital.
    
    Procesa la huella digital capturada, genera el hash SHA-256 y el código QR,
    y guarda la información en la base de datos.
    """
    if 'registro_persona' not in request.session:
        return redirect('registro_paso1')
    
    # Obtener datos de la sesión para depuración
    datos_persona = request.session.get('registro_persona', {})
    if 'foto_path' in datos_persona:
        print(f"En paso3, foto_path: {datos_persona['foto_path']}")
    
    if request.method == 'POST':
        # Verificar si se recibió la huella digital
        huella_hex = request.POST.get('huella_hex')
        huella_base64 = request.POST.get('huella_base64')
        
        # También verificamos si se subió un archivo
        huella_file = request.FILES.get('huella')
        
        # Si tenemos huella_base64 del SDK o un archivo subido manualmente
        if (huella_hex and huella_base64) or huella_file:
            try:
                # Si tenemos un archivo subido manualmente, procesarlo
                if huella_file:
                    # Leer el archivo y generar el hash
                    huella_content = huella_file.read()
                    hasher = hashlib.sha256()
                    hasher.update(huella_content)
                    huella_hex = hasher.hexdigest()
                    huella_content_file = ContentFile(huella_content)
                else:
                    # Si tenemos los datos del SDK, decodificar el base64
                    huella_content = base64.b64decode(huella_base64)
                    huella_content_file = ContentFile(huella_content)
                
                # Generar QR a partir del hash
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(huella_hex)
                qr.make(fit=True)
                
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format="PNG")
                qr_content = ContentFile(qr_buffer.getvalue())
                
                # Crear persona con todos los datos
                datos_persona = request.session['registro_persona']
                persona = Persona(
                    nombre=datos_persona['nombre'],
                    apellidos=datos_persona['apellidos'],
                    sexo=datos_persona['sexo'],
                    telefono=datos_persona['telefono'],
                    correo=datos_persona['correo'],
                    direccion=datos_persona['direccion'],
                    huella_hex=huella_hex
                )
                
                # MÉTODO MEJORADO: Asignar foto si existe
                if 'foto_path' in datos_persona and datos_persona['foto_path']:
                    import os
                    from django.conf import settings
                    from django.core.files import File
                    
                    # La ruta completa al archivo
                    ruta_completa = os.path.join(settings.MEDIA_ROOT, datos_persona['foto_path'])
                    
                    if os.path.exists(ruta_completa):
                        try:
                            with open(ruta_completa, 'rb') as f:
                                # Crear un nombre para la foto final basado en el nombre de la persona
                                nombre_foto_final = f"foto_{persona.nombre}_{persona.apellidos.split()[0]}.jpg"
                                
                                # Guardar el archivo con un nuevo nombre
                                persona.foto.save(nombre_foto_final, File(f), save=False)
                                
                                print(f"Foto asignada al modelo desde {ruta_completa}")
                            
                            # NUEVO: Eliminar el archivo temporal
                            try:
                                os.remove(ruta_completa)
                                print(f"Archivo temporal eliminado: {ruta_completa}")
                            except Exception as e:
                                print(f"Error al eliminar archivo temporal: {e}")
                        
                        except Exception as e:
                            print(f"Error al procesar foto: {e}")
                            # Opcional: manejar el error si no se puede abrir/procesar el archivo
                    else:
                        print(f"Advertencia: No se encontró el archivo de foto en {ruta_completa}")
                
                # Guardar huella y QR
                persona.huella_digital.save(f'huella_{persona.nombre}.png', huella_content_file)
                persona.qr_code.save(f'qr_{persona.nombre}.png', qr_content)
                
                print("Guardando persona en la base de datos...")
                persona.save()
                print(f"Persona guardada. ID: {persona.id}, Foto: {persona.foto}")
                
                # Limpiar sesión
                del request.session['registro_persona']
                
                return redirect('lista_personas')
            except Exception as e:
                # Log del error y mensaje para el usuario
                import traceback
                print(f"Error al procesar huella: {str(e)}")
                print(traceback.format_exc())
                return render(
                    request, 
                    'personas/registro_paso3.html', 
                    {'error': f'Error al procesar la huella digital: {str(e)}. Por favor, intente nuevamente.'}
                )
        else:
            # Si no se recibió la huella, mostrar mensaje de error
            return render(
                request, 
                'personas/registro_paso3.html', 
                {'error': 'No se recibió la huella digital. Por favor, capture su huella.'}
            )
    
    return render(request, 'personas/registro_paso3.html')

@login_required
def busqueda_huella(request):
    if request.method == 'POST' and 'huella' in request.FILES:
        huella = request.FILES['huella']
        huella_hex = process_fingerprint(huella)[0]
        
        persona = Persona.objects.filter(huella_hex=huella_hex).first()
        if persona:
            return redirect('persona_detalle', pk=persona.id)
        else:
            return render(request, 'personas/busqueda.html', {'error': 'No se encontró ninguna persona con esa huella digital'})
    
    return render(request, 'personas/busqueda.html')

class PersonaDetailView(LoginRequiredMixin, DetailView):
    model = Persona
    template_name = 'personas/persona_detalle.html'
    context_object_name = 'persona'

class PersonaUpdateView(LoginRequiredMixin, UpdateView):
    model = Persona
    template_name = 'personas/persona_editar.html'
    fields = ['nombre', 'apellidos', 'sexo', 'telefono', 'correo', 'direccion', 'foto']
    success_url = reverse_lazy('lista_personas')

class PersonaDeleteView(LoginRequiredMixin, DeleteView):
    model = Persona
    template_name = 'personas/persona_eliminar.html'
    success_url = reverse_lazy('lista_personas')

@csrf_exempt
def capturar_huella(request):
    """Endpoint para recibir datos de la huella digital desde el lector"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            imagen_base64 = data.get('imagen')
            
            if not imagen_base64:
                return JsonResponse({'error': 'No se proporcionó imagen de huella'}, status=400)
            
            # Convertir base64 a imagen
            imagen_data = base64.b64decode(imagen_base64.split(',')[1])
            
            # Procesamiento de huella
            huella = ContentFile(imagen_data)
            huella_hex, qr_image = process_fingerprint(huella)
            
            return JsonResponse({
                'huella_hex': huella_hex,
                'qr_code': f'data:image/png;base64,{base64.b64encode(qr_image.read()).decode("utf-8")}'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)