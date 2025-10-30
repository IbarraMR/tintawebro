from django.contrib import admin
from .models import (
    Cajas,
    FormaPago,
    MovimientosCaja,
    AuditoriaCaja,
    Cliente,
    Proveedores,
    Insumos,
    Empleados,
    Compras,
    DetallesCompra,
)

admin.site.register(Cajas)
admin.site.register(FormaPago)
admin.site.register(MovimientosCaja)
admin.site.register(AuditoriaCaja)
admin.site.register(Cliente)
admin.site.register(Proveedores)
admin.site.register(Insumos)
admin.site.register(Empleados)
admin.site.register(Compras)
admin.site.register(DetallesCompra)
