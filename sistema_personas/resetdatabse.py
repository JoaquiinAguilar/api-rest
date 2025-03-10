from django.db import connection
from personas.models import Persona

# Eliminar todos los registros
Persona.objects.all().delete()

# Reiniciar secuencia (PostgreSQL)
if connection.vendor == 'postgresql':
    with connection.cursor() as cursor:
        cursor.execute("ALTER SEQUENCE personas_persona_id_seq RESTART WITH 1;")
# Para MySQL
elif connection.vendor == 'mysql':
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE personas_persona AUTO_INCREMENT = 1;")
# Para SQLite
elif connection.vendor == 'sqlite':
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='personas_persona';")