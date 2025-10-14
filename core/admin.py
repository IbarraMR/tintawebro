from django.contrib import admin

from .models import Cajas, Clientes, Compras, DetallesCompra, Empleados, EstadosPedidos, FormasPago, Insumos, MovimientosCaja, Pagos, Pedidos, PedidosProductos, Presupuestos, PresupuestosInsumos, Productos, Proveedores, TiposProducto  # agregá todas tus tablas aquí

admin.site.register(Cajas)
admin.site.register(Clientes)
admin.site.register(Compras)
admin.site.register(DetallesCompra)
admin.site.register(Empleados)
admin.site.register(EstadosPedidos)
admin.site.register(FormasPago)
admin.site.register(Insumos)
admin.site.register(MovimientosCaja)
admin.site.register(Pagos)
admin.site.register(Pedidos)
admin.site.register(PedidosProductos)
admin.site.register(Presupuestos)
admin.site.register(PresupuestosInsumos)
admin.site.register(Productos)
admin.site.register(Proveedores)
admin.site.register(TiposProducto)