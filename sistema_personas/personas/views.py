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
from django.contrib.auth.models import User

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

import json
import base64
from io import BytesIO
from PIL import Image

from .models import Persona, Rank, UserProfile
from .serializers import PersonaSerializer, PersonaListSerializer
from .biometrics import process_fingerprint, compare_fingerprint
from .forms import RankForm

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
        # Guardar datos básicos en sesión
        request.session['registro_persona'] = {
            'nombre': request.POST.get('nombre'),
            'apellidos': request.POST.get('apellidos'),
            'sexo': request.POST.get('sexo') == '1',
            'telefono': request.POST.get('telefono'),
            'correo': request.POST.get('correo'),
            'direccion': request.POST.get('direccion')
        }
        return redirect('registro_paso2')
    
    return render(request, 'personas/registro_paso1.html')

@login_required
def registro_paso2(request):
    if 'registro_persona' not in request.session:
        return redirect('registro_paso1')
    
    if request.method == 'POST':
        if 'foto' in request.FILES:
            # Guardar foto temporalmente
            foto = request.FILES['foto']
            foto_path = default_storage.save(f'temp/foto_{request.user.id}.png', ContentFile(foto.read()))
            request.session['registro_persona']['foto_path'] = foto_path
        
        if request.POST.get('foto_base64'):
            # Si se capturó con la cámara
            img_data = request.POST.get('foto_base64').split(',')[1]
            img = Image.open(BytesIO(base64.b64decode(img_data)))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            foto_path = default_storage.save(f'temp/foto_{request.user.id}.png', ContentFile(buffer.getvalue()))
            request.session['registro_persona']['foto_path'] = foto_path
        
        return redirect('registro_paso3')
    
    return render(request, 'personas/registro_paso2.html')

@login_required
def registro_paso3(request):
    if 'registro_persona' not in request.session:
        return redirect('registro_paso1')
    
    if request.method == 'POST':
        if 'huella' in request.FILES:
            huella = request.FILES['huella']
            
            # Procesar huella digital
            huella_hex, qr_image = process_fingerprint(huella)
            
            # Obtener datos de la sesión
            datos_persona = request.session['registro_persona']
            
            # Crear usuario
            user = User.objects.create_user(
                username=datos_persona['correo'],  # Usar el correo como nombre de usuario
                email=datos_persona['correo'],
                password='password_temporal'  # Puedes generar una contraseña temporal
            )
            
            # Asignar rol al usuario
            rank_id = request.POST.get('rol')
            rank = Rank.objects.get(id=rank_id)
            UserProfile.objects.create(user=user, rank=rank)
            
            # Crear persona con todos los datos
            persona = Persona(
                nombre=datos_persona['nombre'],
                apellidos=datos_persona['apellidos'],
                sexo=datos_persona['sexo'],
                telefono=datos_persona['telefono'],
                correo=datos_persona['correo'],
                direccion=datos_persona['direccion'],
                huella_hex=huella_hex
            )
            
            # Asignar foto si existe
            if 'foto_path' in datos_persona:
                with default_storage.open(datos_persona['foto_path']) as f:
                    persona.foto.save(f'foto_{persona.nombre}.png', ContentFile(f.read()))
                # Eliminar archivo temporal
                default_storage.delete(datos_persona['foto_path'])
            
            # Guardar huella y QR
            persona.huella_digital.save(f'huella_{persona.nombre}.png', huella)
            persona.qr_code.save(f'qr_{persona.nombre}.png', qr_image)
            
            persona.save()
            
            # Limpiar sesión
            del request.session['registro_persona']
            
            return redirect('lista_personas')
    
    # Obtener todos los roles para mostrar en el formulario
    ranks = Rank.objects.all()
    return render(request, 'personas/registro_paso3.html', {'ranks': ranks})

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

# Vistas para roles
def create_rank(request):
    if request.method == 'POST':
        form = RankForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_roles')
    else:
        form = RankForm()
    return render(request, 'personas/create_rank.html', {'form': form})

def edit_rank(request, pk):
    rank = get_object_or_404(Rank, pk=pk)
    if request.method == 'POST':
        form = RankForm(request.POST, instance=rank)
        if form.is_valid():
            form.save()
            return redirect('lista_roles')
    else:
        form = RankForm(instance=rank)
    return render(request, 'personas/edit_rank.html', {'form': form})