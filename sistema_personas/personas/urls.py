from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para las API
router = DefaultRouter()
router.register(r'personas', views.PersonaViewSet)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Vistas de la interfaz web
    path('', views.dashboard, name='dashboard'),
    path('personas/', views.PersonaListView.as_view(), name='lista_personas'),
    path('personas/<int:pk>/', views.PersonaDetailView.as_view(), name='persona_detalle'),
    path('personas/<int:pk>/editar/', views.PersonaUpdateView.as_view(), name='persona_editar'),
    path('personas/<int:pk>/eliminar/', views.PersonaDeleteView.as_view(), name='persona_eliminar'),
    
    # Registro paso a paso
    path('registro/paso1/', views.registro_paso1, name='registro_paso1'),
    path('registro/paso2/', views.registro_paso2, name='registro_paso2'),
    path('registro/paso3/', views.registro_paso3, name='registro_paso3'),
    
    # Búsqueda por huella
    path('busqueda/', views.busqueda_huella, name='busqueda_huella'),
    
    # Endpoint para capturar huella
    path('api/capturar-huella/', views.capturar_huella, name='capturar_huella'),
]