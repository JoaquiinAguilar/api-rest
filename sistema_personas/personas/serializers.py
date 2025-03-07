from rest_framework import serializers
from .models import Persona

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = '__all__'
        read_only_fields = ('fecha_registro', 'fecha_actualizacion')

class PersonaListSerializer(serializers.ModelSerializer):
    sexo_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Persona
        fields = ('id', 'nombre', 'apellidos', 'sexo', 'sexo_display', 'telefono', 'correo')
    
    def get_sexo_display(self, obj):
        return "Hombre" if obj.sexo else "Mujer"