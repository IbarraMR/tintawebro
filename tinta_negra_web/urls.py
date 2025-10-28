from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views
from core.views import logout_view

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


    path('proveedores/', views.proveedores_list, name='proveedores_list'),
    path('proveedores/nuevo/', views.proveedor_create, name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.proveedor_edit, name='proveedor_edit'),
    path('proveedores/<int:pk>/baja/', views.proveedor_baja_logica, name='proveedor_baja'),
    path('proveedores/<int:pk>/reactivar/', views.proveedor_reactivar, name='proveedor_reactivar'),
    path('proveedores/<int:pk>/compras/', views.compras_proveedor, name='compras_proveedor'),

    path('cajas/', views.cajas_list, name='cajas_list'),
    path('cajas/abrir/', views.abrir_caja_view, name='abrir_caja'),
    path('cajas/cerrar/', views.cerrar_caja_view, name='cerrar_caja'),
    path('cajas/<int:id>/', views.detalle_caja_view, name='detalle_caja'),

    path('pedidos/', views.pedidos_list, name='pedidos_list'),
    path('presupuestos/', views.presupuestos_list, name='presupuestos_list'),
    path('insumos/', views.insumos_list, name='insumos_list'),
    path('compras/', views.compras_list, name='compras_list'),
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('configuracion/', views.configuracion, name='configuracion'),

    path('empleados/', views.empleados_list, name='empleados_list'),
    path('empleados/nuevo/', views.empleado_create, name='empleado_create'),
    path('empleados/editar/<int:pk>/', views.empleado_edit, name='empleado_edit'),
    path('empleados/eliminar/<int:pk>/', views.empleado_delete, name='empleado_delete'),
    path('empleados/<int:pk>/baja/', views.empleado_baja_logica, name='empleado_baja'),
    path('empleados/<int:pk>/reactivar/', views.empleado_reactivar, name='empleado_reactivar'),


    

]
