from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views
from core.views import logout_view

urlpatterns = [
    # Administración
    path('admin/', admin.site.urls),

    # Autenticación
    path('', views.root_redirect, name='root_redirect'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),

    # Usuarios
    path('register/', views.register_user, name='register'),

    # Páginas principales (protegidas)
    path('home/', views.home, name='home'),

    # Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/editar/<int:pk>/', views.cliente_edit, name='cliente_edit'), 
    path('clientes/eliminar/<int:pk>/', views.cliente_delete, name='cliente_delete'), 

    # Pedidos, presupuestos e insumos
    path('pedidos/', views.pedidos_list, name='pedidos_list'),
    path('presupuestos/', views.presupuestos_list, name='presupuestos_list'),
    path('insumos/', views.insumos_list, name='insumos_list'),

    # Vistas de prueba para botones extras
    path('cajas/', views.cajas_list, name='cajas_list'),
    path('compras/', views.compras_list, name='compras_list'),
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('configuracion/', views.configuracion, name='configuracion'),

    # Proveedores (CBVs y funciones)
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedores_list'),
    path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor_form'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/<int:pk>/baja/', views.proveedor_baja_logica, name='proveedor_baja'),
    path('proveedores/<int:pk>/reactivar/', views.proveedor_reactivar, name='proveedor_reactivar'),
]
