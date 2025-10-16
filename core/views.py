from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.utils.decorators import method_decorator

# Modelos
from .models import Proveedores as Proveedor  # Alias para Proveedores
from .models import Cliente

# Formularios
from .forms import ClienteForm  # Asegurate de que exista core/forms.py

# ----------------------------------------------------------------------
# REDIRECCIONES Y AUTENTICACIÓN
# ----------------------------------------------------------------------

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')

@never_cache
def logout_view(request):
    logout(request)
    return redirect('login')

@never_cache
@login_required
@permission_required('auth.add_user', raise_exception=True)
def register_user(request):
    if request.method == 'POST':
        # Código de creación de usuario aquí
        return redirect('home')
    return render(request, 'core/register.html')

@never_cache
@login_required
def home(request):
    from core.models import Cliente  # asegurate de importar
    context = {
        'pedidos_pendientes_count': 0,  # temporal
        'ventas_30_dias': 0,            # temporal
        'insumos_criticos_count': 0,    # temporal
        'clientes_total_count': Cliente.objects.count()
    }
    return render(request, 'core/home.html', context)

# ----------------------------------------------------------------------
# CLIENTES
# ----------------------------------------------------------------------

@never_cache
@login_required
@permission_required('core.view_clientes', raise_exception=True)
def clientes_list(request):
    clientes = Cliente.objects.all().order_by('nombre')
    return render(request, 'core/clientes/clientes_list.html', {'clientes': clientes})

@never_cache
@login_required
@permission_required('core.add_clientes', raise_exception=True)
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Cliente registrado exitosamente.')
                return redirect('clientes_list')
            except Exception as e:
                messages.error(request, f'Error al guardar el cliente: {e}.')
        else:
            messages.error(request, 'Error al registrar el cliente. Verifica los datos.')
    else:
        form = ClienteForm()

    return render(request, 'core/clientes/cliente_form.html', {
        'form': form,
        'title': 'Registrar Nuevo Cliente',
        'is_create': True
    })

@never_cache
@login_required
@permission_required('core.change_clientes', raise_exception=True)
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('clientes_list')
        else:
            messages.error(request, 'Error al actualizar el cliente. Verifique los datos.')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'core/clientes/cliente_form.html', {
        'form': form,
        'title': f'Editar Cliente: {cliente.nombre}',
        'is_create': False
    })

@never_cache
@login_required
@permission_required('core.delete_clientes', raise_exception=True)
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('clientes_list')
    return redirect('clientes_list')

# ----------------------------------------------------------------------
# PEDIDOS, PRESUPUESTOS, INSUMOS
# ----------------------------------------------------------------------

@never_cache
@login_required
@permission_required('core.view_pedidos', raise_exception=True)
def pedidos_list(request):
    pedidos = []
    return render(request, 'core/pedidos_list.html', {'pedidos': pedidos})

@never_cache
@login_required
@permission_required('core.view_presupuestos', raise_exception=True)
def presupuestos_list(request):
    presupuestos = []
    return render(request, 'core/presupuestos_list.html', {'presupuestos': presupuestos})

@never_cache
@login_required
@permission_required('core.view_insumos', raise_exception=True)
def insumos_list(request):
    insumos = []
    return render(request, 'core/insumos_list.html', {'insumos': insumos})

# ----------------------------------------------------------------------
# OTRAS VISTAS
# ----------------------------------------------------------------------

@never_cache
@login_required
def cajas_list(request):
    return render(request, 'core/cajas_list.html')

@never_cache
@login_required
def compras_list(request):
    return render(request, 'core/compras_list.html')

@never_cache
@login_required
def empleados_list(request):
    return render(request, 'core/empleados_list.html')

@never_cache
@login_required
def configuracion(request):
    return render(request, 'core/configuracion.html')

# ----------------------------------------------------------------------
# PROVEEDORES (CBVs y funciones)
# ----------------------------------------------------------------------

# Decoradores CBV
list_decorators = [never_cache, login_required, permission_required('core.view_proveedores', raise_exception=True)]
create_decorators = [never_cache, login_required, permission_required('core.add_proveedores', raise_exception=True)]
update_decorators = [never_cache, login_required, permission_required('core.change_proveedores', raise_exception=True)]

# Listado
@method_decorator(list_decorators, name='dispatch')
class ProveedorListView(ListView):
    model = Proveedor
    template_name = "core/proveedores/proveedores_list.html"
    context_object_name = 'object_list'

    def get_queryset(self):
        return Proveedor.objects.all().order_by('razon_social')

# Creación
@method_decorator(create_decorators, name='dispatch')
class ProveedorCreateView(CreateView):
    model = Proveedor
    template_name = 'core/proveedores/proveedor_form.html'
    fields = ['cuit', 'razon_social', 'direccion', 'telefono', 'ciudad', 'categoria']  # ✅ CORREGIDO
    success_url = '/proveedores/'

# Edición
@method_decorator(update_decorators, name='dispatch')
class ProveedorUpdateView(UpdateView):
    model = Proveedor
    template_name = 'core/proveedores/proveedor_form.html'
    fields = ['cuit', 'razon_social', 'direccion', 'telefono', 'ciudad', 'categoria', 'is_active']  # ✅ CORREGIDO
    success_url = '/proveedores/'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object:
            form.fields['cuit'].widget.attrs['readonly'] = True
        return form

# Baja lógica
@never_cache
@login_required
@permission_required('core.change_proveedores', raise_exception=True)
def proveedor_baja_logica(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.is_active = False
    proveedor.save()
    messages.success(request, f'Proveedor {proveedor.razon_social} dado de baja exitosamente.')
    return redirect('proveedores_list')

# Reactivación
@never_cache
@login_required
@permission_required('core.change_proveedores', raise_exception=True)
def proveedor_reactivar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.is_active = True
    proveedor.save()
    messages.success(request, f'Proveedor {proveedor.razon_social} reactivado exitosamente.')
    return redirect('proveedores_list')
