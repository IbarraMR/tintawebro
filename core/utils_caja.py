from contextlib import contextmanager
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum
from .models import Cajas, Empleados, MovimientosCaja, FormaPago

def caja_abierta_de(request):
    """Devuelve la caja ABIERTA del empleado logueado (o None)."""
    emp = Empleados.objects.filter(user=request.user).first()
    if not emp:
        return None
    return (
        Cajas.objects
        .filter(id_empleado=emp, caja_cerrada=False)
        .order_by('-id_caja')
        .first()
    )

@transaction.atomic
def registrar_movimiento(request, tipo, forma_pago_id, monto, descripcion="", origen="MANUAL"):
    try:
        empleado = Empleados.objects.get(user=request.user)
    except Empleados.DoesNotExist:
        return None, "El usuario no está vinculado a un empleado."
    caja = Cajas.objects.filter(caja_cerrada=False, id_empleado=empleado).first()
    if not caja:
        return None, "No hay caja abierta asignada al empleado."
    saldo_actual = caja.saldo_sistema
    if tipo == MovimientosCaja.Tipo.EGRESO and monto > saldo_actual:
        return None, "No hay saldo suficiente para realizar el egreso."
    nuevo_saldo = saldo_actual + monto if tipo == MovimientosCaja.Tipo.INGRESO else saldo_actual - monto
    mov = MovimientosCaja.objects.create(
        caja=caja,
        tipo=tipo,
        monto=monto,
        forma_pago_id=forma_pago_id,
        descripcion=descripcion,
        creado_por=empleado,            
        saldo_resultante=nuevo_saldo
    )

    return mov, None
