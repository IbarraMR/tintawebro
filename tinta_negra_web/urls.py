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
)

urlpatterns = [

    # --- LOGIN / LOGOUT ---
    path('admin/', admin.site.urls),
    path('', views.root_redirect, name='root_redirect'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),

    # --- HOME ---
    path('home/', views.home, name='home'),

    # --- COMPRAS ---
    
    path('compras/', views.compras_list, name='compras_list'),
    path('compras/nueva/', views.compras_create, name='compras_create'),
    path('compras/<int:pk>/', views.compra_detalle, name='compra_detalle'),

    # --- CLIENTES ---
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/editar/<int:pk>/', views.cliente_edit, name='cliente_edit'),
    path('clientes/eliminar/<int:pk>/', views.cliente_delete, name='cliente_delete'),
    path('clientes/<int:pk>/compras/', views.compras_cliente, name='compras_cliente'),

    # --- PROVEEDORES ---
    path('proveedores/', views.proveedores_list, name='proveedores_list'),
    path('proveedor/nuevo/', views.proveedor_create, name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.proveedor_edit, name='proveedor_edit'),
    path('proveedores/<int:pk>/baja/', views.proveedor_baja_logica, name='proveedor_baja'),
    path('proveedores/<int:pk>/reactivar/', views.proveedor_reactivar, name='proveedor_reactivar'),
    path('ajax/proveedor/nuevo/', proveedor_create_ajax, name='proveedor_create_ajax'),

    # --- INSUMOS ---
    path('insumos/', views.insumos_list, name='insumos_list'),
    path("insumos/nuevo/", views.insumo_create, name="insumo_create"),
    path('insumos/editar/<int:pk>/', views.insumo_edit, name='insumo_edit'),
    path('insumos/eliminar/<int:pk>/', views.insumo_delete, name='insumo_delete'),


    # --- AJAX INSUMOS ---
    path('ajax/insumo/create/', views.insumo_nuevo_ajax, name='insumo_create_ajax'),
    path("ajax/insumo/datos/<int:pk>/", views.insumo_datos_ajax, name="insumo_datos_ajax"),
    path("ajax/insumo/editar/", views.insumo_editar_ajax, name="insumo_editar_ajax"),


    # --- PEDIDOS / PRESUPUESTOS ---
    path("pedidos/", views.pedidos_list, name="pedidos_list"),
    path("presupuestos/", views.presupuestos_list, name="presupuestos_list"),

    path("presupuestos/<int:pk>/generar-pedido/", convertir_presupuesto_a_pedido, name="convertir_presupuesto_a_pedido"),
    path("pedidos/<int:pk>/editar-insumos/", pedido_editar_insumos, name="pedido_editar_insumos"),
    path("pedidos/<int:pk>/confirmar/", pedido_confirmar, name="pedido_confirmar"),

    # --- EMPLEADOS ---
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('empleados/nuevo/', views.empleado_create, name='empleado_create'),
    path('empleados/editar/<int:pk>/', views.empleado_edit, name='empleado_edit'),
    path('empleados/eliminar/<int:pk>/', views.empleado_delete, name='empleado_delete'),
    path('empleados/<int:pk>/baja/', views.empleado_baja_logica, name='empleado_baja'),
    path('empleados/<int:pk>/reactivar/', views.empleado_reactivar, name='empleado_reactivar'),

    # --- CAJA ---
    path('cajas/', views.cajas_list, name='cajas_list'),
    path('cajas/abrir/', views.abrir_caja_view, name='abrir_caja'),
    path('cajas/cerrar/', views.cerrar_caja_view, name='cerrar_caja'),
    path('cajas/movimientos/', views.movimientos_list, name='movimientos_list'),
    path('cajas/movimientos/nuevo/', views.movimiento_create, name='movimiento_create'),
    path('cajas/formas-pago/', views.formas_pago_list, name='formas_pago_list'),
    path('cajas/formas-pago/nuevo/', views.formas_pago_create, name='formas_pago_create'),
    path('cajas/formas-pago/toggle/<int:id>/', views.formas_pago_toggle, name='formas_pago_toggle'),
    path('cajas/<int:id>/', views.detalle_caja_view, name='detalle_caja'),


    path('configuracion/', views.configuracion, name='configuracion'),


]
