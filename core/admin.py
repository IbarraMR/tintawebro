from django.contrib import admin

from .models import Cajas, Cliente, Compras, DetalleCompra, Empleados, EstadosPedidos, FormaPago, Insumos, MovimientosCaja, Pagos, Pedidos, PedidosProductos, Presupuestos, PresupuestosInsumos, Productos, Proveedores, TiposProducto  # agregá todas tus tablas aquí

admin.site.register(Cajas)
admin.site.register(Cliente)
admin.site.register(Compras)
admin.site.register(DetalleCompra)
admin.site.register(Empleados)
admin.site.register(EstadosPedidos)
admin.site.register(FormaPago)
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