from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from tinta_negra_web import views

from tinta_negra_web.views import (
    logout_view,
    compras_create,
    proveedor_create_ajax,
    convertir_presupuesto_a_pedido,
    pedido_editar_insumos,
    pedido_confirmar,
    unidad_medida_create_ajax,
    agregar_insumo_presupuesto,
    presupuesto_detalle,
    presupuestos_list,
    presupuesto_create,
    eliminar_insumo_presupuesto,
    editar_insumo_presupuesto,
    movimientos_stock_list,
    producto_insumos,
    generar_pdf_presupuesto,
    guardar_trabajo,
    presupuesto_aprobar,
    presupuesto_confirmar,
    pedido_cambiar_estado,
)


urlpatterns = [

    path('admin/', admin.site.urls),
    path('', views.root_redirect, name='root_redirect'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),

    path('home/', views.home, name='home'),

    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/editar/<int:pk>/', views.cliente_edit, name='cliente_edit'),
    path('clientes/eliminar/<int:pk>/', views.cliente_delete, name='cliente_delete'),
    path('clientes/<int:pk>/compras/', views.compras_cliente, name='compras_cliente'),
    path("clientes/<int:pk>/pedidos/", views.cliente_pedidos, name="cliente_pedidos"),

    path('proveedores/', views.proveedores_list, name='proveedores_list'),
    path('proveedor/nuevo/', views.proveedor_create, name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.proveedor_edit, name='proveedor_edit'),
    path('proveedores/<int:pk>/baja/', views.proveedor_baja_logica, name='proveedor_baja'),
    path('proveedores/<int:pk>/reactivar/', views.proveedor_reactivar, name='proveedor_reactivar'),
    path('compras/proveedor/<int:proveedor_id>/', views.compras_proveedor, name='compras_proveedor'),
    path('ajax/proveedor/nuevo/', proveedor_create_ajax, name='proveedor_create_ajax'),

    path('insumos/', views.insumos_list, name='insumos_list'),
    path("insumos/nuevo/", views.insumo_create, name="insumo_create"),
    path('insumos/editar/<int:pk>/', views.insumo_edit, name='insumo_edit'),
    path('insumos/eliminar/<int:pk>/', views.insumo_delete, name='insumo_delete'),
    path('ajax/insumo/create/', views.insumo_nuevo_ajax, name='insumo_create_ajax'),
    path("ajax/insumo/datos/<int:pk>/", views.insumo_datos_ajax, name="insumo_datos_ajax"),
    path("ajax/insumo/editar/", views.insumo_editar_ajax, name="insumo_editar_ajax"),
    path("unidad-medida/create/ajax/", unidad_medida_create_ajax, name="unidad_medida_create_ajax"),

    path('compras/', views.compras_list, name='compras_list'),
    path('compras/nueva/', views.compras_create, name='compras_create'),
    path('compras/<int:pk>/', views.compra_detalle, name='compra_detalle'),

    path("presupuesto/nuevo/", presupuesto_create, name="presupuesto_create"),
    path("presupuestos/", views.presupuestos_list, name="presupuestos_list"),
    path("presupuesto/<int:pk>/detalle/", presupuesto_detalle, name="presupuesto_detalle"),

    path("presupuesto/<int:presupuesto_id>/agregar-insumo/", agregar_insumo_presupuesto, name="agregar_insumo_presupuesto"),
    path("presupuesto/<int:presupuesto_id>/set-cliente/", views.presupuesto_set_cliente, name="presupuesto_set_cliente"),

    path("presupuesto/detalle/<int:detalle_id>/eliminar/", eliminar_insumo_presupuesto, name="eliminar_insumo_presupuesto"),
    path("presupuesto/detalle/<int:detalle_id>/editar/", editar_insumo_presupuesto, name="editar_insumo_presupuesto"),

    path("presupuesto/borrador/crear/", views.crear_presupuesto_borrador, name="crear_presupuesto_borrador"),
    path("presupuesto/<int:presupuesto_id>/trabajos/agregar/", views.agregar_trabajo, name="agregar_trabajo"),
    path("presupuesto/<int:presupuesto_id>/trabajos/listar/", views.listar_trabajos, name="listar_trabajos"),
    path("trabajo/<int:trabajo_id>/eliminar/", views.eliminar_trabajo, name="eliminar_trabajo"),
    path("trabajo/<int:trabajo_id>/duplicar/", views.duplicar_trabajo, name="duplicar_trabajo"),

    path("presupuesto/<int:pk>/pdf/", views.generar_pdf_presupuesto, name="generar_pdf_presupuesto"),
    path("presupuesto/<int:pk>/confirmar/", presupuesto_confirmar, name="presupuesto_confirmar"),
    path("presupuesto/<int:pk>/previsualizar/", views.presupuesto_previa_pdf, name="presupuesto_previa_pdf"),
    path("presupuesto/<int:pk>/email-preview/", views.presupuesto_email_preview, name="presupuesto_email_preview"),
    path("presupuesto/<int:pk>/enviar-email/", views.presupuesto_enviar_email, name="presupuesto_enviar_email"),
    path("presupuesto/<int:id>/aprobar/", presupuesto_aprobar, name="presupuesto_aprobar"),
    path("presupuesto/<int:presupuesto_id>/editar/", views.presupuesto_edit, name="presupuesto_edit"),
    path("presupuesto/<int:presupuesto_id>/agregar-producto/", views.agregar_producto_presupuesto, name="agregar_producto_presupuesto"),
    path("presupuesto/<int:pk>/guardar_trabajo/", guardar_trabajo, name="guardar_trabajo"),

    path("pedidos/", views.pedidos_list, name="pedidos_list"),
    path("presupuestos/<int:pk>/generar-pedido/", convertir_presupuesto_a_pedido, name="convertir_presupuesto_a_pedido"),
    path("pedidos/<int:pk>/editar-insumos/", pedido_editar_insumos, name="pedido_editar_insumos"),
    path("pedidos/<int:pk>/confirmar/", pedido_confirmar, name="pedido_confirmar"),
    path("pedidos/<int:id_pedido>/estado/<str:nuevo_estado>/", pedido_cambiar_estado, name="pedido_cambiar_estado"),

    path("stock/movimientos/", movimientos_stock_list, name="movimientos_stock_list"),
    path("productos/<int:pk>/insumos/", producto_insumos, name="producto_insumos"),

    path("productos/", views.productos_list, name="productos_list"),
    path("productos/nuevo/", views.producto_create, name="producto_create"),
    path("productos/<int:pk>/editar/", views.producto_edit, name="producto_edit"),
    path("productos/<int:pk>/detalle/", views.producto_detalle, name="producto_detalle"),
    path("productos/eliminar/<int:id_producto>/", views.producto_delete, name="producto_delete"),

    path('empleados/', views.empleados_list, name='empleados_list'),
    path('empleados/nuevo/', views.empleado_create, name='empleado_create'),
    path('empleados/editar/<int:pk>/', views.empleado_edit, name='empleado_edit'),
    path('empleados/eliminar/<int:pk>/', views.empleado_delete, name='empleado_delete'),
    path('empleados/<int:pk>/baja/', views.empleado_baja_logica, name='empleado_baja'),
    path('empleados/<int:pk>/reactivar/', views.empleado_reactivar, name='empleado_reactivar'),

    path('cajas/', views.cajas_list, name='cajas_list'),
    path('cajas/abrir/', views.abrir_caja_view, name='abrir_caja'),
    path('cajas/cerrar/', views.cerrar_caja_view, name='cerrar_caja'),
    path('cajas/movimientos/nuevo/', views.movimiento_create, name='movimiento_create'),
    path('cajas/formas-pago/', views.formas_pago_list, name='formas_pago_list'),
    path('cajas/formas-pago/nuevo/', views.formas_pago_create, name='formas_pago_create'),
    path('cajas/formas-pago/toggle/<int:id>/', views.formas_pago_toggle, name='formas_pago_toggle'),
    path('cajas/<int:id>/', views.detalle_caja_view, name='detalle_caja'),
    path('cajas/movimientos/', views.movimientos_list, name='movimientos_list'),

    path("configuracion/", views.configuracion, name="configuracion"),
    path("configuracion/empresa/", views.configuracion_empresa, name="configuracion_empresa"),
    path("configuracion/perfil/", views.configuracion_perfil, name="configuracion_perfil"),
    path("configuracion/password/", views.configuracion_password, name="configuracion_password"),
    path("configuracion/email/", views.configuracion_email, name="configuracion_email"),

    path("api/grafico/ventas/", views.api_grafico_ventas, name="api_grafico_ventas"),
    path("reportes/ventas/pdf/", views.reporte_ventas_pdf, name="reporte_ventas_pdf"),
    path('clientes/create/ajax/', views.cliente_create_ajax, name='cliente_create_ajax'),

]
