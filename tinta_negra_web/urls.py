from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout 
from django.shortcuts import redirect

def logout_view(request):
    if request.method in ['POST', 'GET']:
        logout(request)
        return redirect('login')
    return redirect('home')

urlpatterns = [
    # Administración
    path('admin/', admin.site.urls),

    # Autenticación
    path('', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),

    # Usuarios
    path('register/', views.register_user, name='register'),

    # Páginas principales (protegidas con login_required)
    path('home/', login_required(views.home), name='home'),
    path('clientes/', login_required(views.clientes_list), name='clientes_list'),
    path('pedidos/', login_required(views.pedidos_list), name='pedidos_list'),
    path('presupuestos/', login_required(views.presupuestos_list), name='presupuestos_list'),
    path('insumos/', login_required(views.insumos_list), name='insumos_list'),
]
