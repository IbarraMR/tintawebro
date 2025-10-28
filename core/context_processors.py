# core/context_processors.py
from django.contrib.auth.models import Group
from core.models import Cajas

def ui_flags(request):
    user = request.user
    es_duenio = False
    if user.is_authenticated:
        es_duenio = user.groups.filter(name='Dueño').exists()
    caja_abierta = Cajas.objects.filter(caja_cerrada=0).exists() if user.is_authenticated else False
    return {
        'es_duenio': es_duenio,
        'caja_abierta': caja_abierta,
    }
