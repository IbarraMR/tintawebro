from django.urls import path
from . import views

urlpatterns = [
    # HOME
    path('', views.root_redirect, name='root_redirect'),
    path('home/', views.home, name='home'),

    # CLIENTES
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/editar/<int:pk>/', views.cliente_edit, name='cliente_edit'),
    path('clientes/eliminar/<int:pk>/', views.cliente_delete, name='cliente_delete'),

    # PROVEEDORES
    path('proveedores/', views.proveedores_list, name='proveedores_list'),
    path('proveedores/nuevo/', views.proveedor_create, name='proveedor_create'),
    path('proveedores/editar/<int:pk>/', views.proveedor_edit, name='proveedor_edit'),
    path('proveedores/baja/<int:pk>/', views.proveedor_baja_logica, name='proveedor_baja'),
    path('proveedores/reactivar/<int:pk>/', views.proveedor_reactivar, name='proveedor_reactivar'),

    # CAJA
    path('cajas/', views.cajas_list, name='cajas_list'),
    path('cajas/abrir/', views.abrir_caja_view, name='abrir_caja'),
    path('cajas/cerrar/', views.cerrar_caja_view, name='cerrar_caja'),
    path('cajas/<int:id>/', views.detalle_caja_view, name='detalle_caja'),
]
