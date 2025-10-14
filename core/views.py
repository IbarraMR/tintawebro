from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from core.models import Clientes, Pedidos, Presupuestos, Insumos

# ============================
# Página principal
# ============================
@login_required
def home(request):
    return render(request, 'core/home.html')

# ============================
# Registrar usuario (solo Jefes)
# ============================
@login_required
@permission_required('auth.add_user', raise_exception=True)
def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']  # 'Jefe' o 'Empleado'

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return redirect('register')

        user = User.objects.create_user(username=username, password=password)
        group = Group.objects.get(name=role)
        user.groups.add(group)
        user.save()

        messages.success(request, f'Usuario {username} creado correctamente con rol {role}')
        return redirect('home')

    return render(request, 'core/register.html')

# ============================
# Listado de Clientes
# ============================
@login_required
@permission_required('core.view_clientes', raise_exception=True)
def clientes_list(request):
    clientes = Clientes.objects.all()
    return render(request, 'core/clientes_list.html', {'clientes': clientes})

# ============================
# Listado de Pedidos
# ============================
@login_required
@permission_required('core.view_pedidos', raise_exception=True)
def pedidos_list(request):
    pedidos = Pedidos.objects.all()
    return render(request, 'core/pedidos_list.html', {'pedidos': pedidos})

# ============================
# Listado de Presupuestos
# ============================
@login_required
@permission_required('core.view_presupuestos', raise_exception=True)
def presupuestos_list(request):
    presupuestos = Presupuestos.objects.all()
    return render(request, 'core/presupuestos_list.html', {'presupuestos': presupuestos})

# ============================
# Listado de Insumos
# ============================
@login_required
@permission_required('core.view_insumos', raise_exception=True)
def insumos_list(request):
    insumos = Insumos.objects.all()
    return render(request, 'core/insumos_list.html', {'insumos': insumos})
