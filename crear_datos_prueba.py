import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tinta_negra_web.settings")
django.setup()

from core.models import Pedidos, EstadosPedidos, Cliente


def crear_datos_prueba():
    print("===== Creando datos de prueba =====")

    # Crear estado ENTREGADO si no existe
    estado, _ = EstadosPedidos.objects.get_or_create(
        nombre_estado="ENTREGADO"
    )

    # Crear cliente DEMO con los campos correctos
    cliente, _ = Cliente.objects.get_or_create(
        nombre="Cliente DEMO",
        apellido="Pruebas",
        defaults={
            "telefono": "000000",
            "email": "demo@tintanegra.com",
        }
    )

    hoy = timezone.now().date()

    for i in range(50):
        dias_atras = random.randint(0, 365)
        fecha = hoy - timedelta(days=dias_atras)
        total = random.randint(2000, 45000)

        Pedidos.objects.create(
            id_cliente=cliente,
            total_pedido=total,
            fecha_entrega_real=fecha,
            id_estado=estado,
            stock_descontado=False  # no afecta stock
        )

    print("✔ 50 pedidos de prueba creados correctamente.")


if __name__ == "__main__":
    crear_datos_prueba()
