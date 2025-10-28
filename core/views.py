from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils import timezone
from .models import Proveedores as Proveedor
from .models import Cliente, Cajas, MovimientosCaja, Empleados
from .forms import ClienteForm, ProveedorForm, EmpleadoForm
from .models import Compras
from django.db.models import Q
from django.contrib.auth.hashers import make_password



# ----------------------------------------------------------------------
# FUNCIONES DE CONTROL DE ACCESO
# ----------------------------------------------------------------------

def es_duenio(user):
    return user.is_authenticated and user.groups.filter(name='Jefe').exists()


# ----------------------------------------------------------------------
# AUTENTICACIÓN Y PÁGINAS PRINCIPALES
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
        return redirect('home')
    return render(request, 'core/register.html')


@never_cache
@login_required
def home(request):
    from core.models import Cliente, Cajas
    caja_abierta = Cajas.objects.filter(caja_cerrada=0).exists()
    es_duenio = request.user.groups.filter(name='Jefe').exists()
    es_empleado = request.user.groups.filter(name='Empleados').exists()

    context = {
        'pedidos_pendientes_count': 0,
        'ventas_30_dias': 0,
        'insumos_criticos_count': 0,
        'clientes_total_count': Cliente.objects.count(),
        'caja_abierta': caja_abierta,
        'es_duenio': es_duenio,
        'es_empleado': es_empleado,
        'puede_ver_caja': es_duenio or es_empleado
    }

    if es_empleado:
        return render(request, 'core/home_empleado.html', context)

    return render(request, 'core/home.html', context)


# ----------------------------------------------------------------------
# CLIENTES
# ----------------------------------------------------------------------

@never_cache
@login_required
@permission_required('core.view_cliente', raise_exception=True)
def clientes_list(request):
    query = request.GET.get('q', '')
    clientes = Cliente.objects.all().order_by('nombre')

    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(dni__icontains=query) |
            Q(telefono__icontains=query)
        )

    return render(request, 'core/clientes/clientes_list.html', {'clientes': clientes, 'query': query})



@never_cache
@login_required
@permission_required('core.add_cliente', raise_exception=True)
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
@permission_required('core.change_cliente', raise_exception=True)
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
    if cliente.compras.exists():
        messages.error(request, 'No se puede eliminar este cliente porque tiene compras registradas.')
        return redirect('clientes_list')

    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('clientes_list')

    return redirect('clientes_list')


@never_cache
@login_required
@permission_required('core.view_proveedores', raise_exception=True)
def proveedores_list(request):
    query = request.GET.get('q', '')
    proveedores = Proveedor.objects.all().order_by('nombre')

    if query:
        proveedores = proveedores.filter(
            Q(nombre__icontains=query) |
            Q(razon_social__icontains=query) |
            Q(cuit__icontains=query) |
            Q(telefono__icontains=query)
        )

    return render(request, 'core/proveedores/proveedores_list.html', {'proveedores': proveedores, 'query': query})



@never_cache
@login_required
@permission_required('core.add_proveedores', raise_exception=True)
def proveedor_create(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor registrado exitosamente.')
            return redirect('proveedores_list')
        else:
            messages.error(request, 'Error al registrar el proveedor. Verifica los datos.')
    else:
        form = ProveedorForm()

    return render(request, 'core/proveedores/proveedor_form.html', {
        'form': form,
        'title': 'Registrar Nuevo Proveedor',
        'is_create': True
    })


@never_cache
@login_required
@permission_required('core.change_proveedores', raise_exception=True)
def proveedor_edit(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente.')
            return redirect('proveedores_list')
        else:
            messages.error(request, 'Error al actualizar el proveedor. Verifica los datos.')
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, 'core/proveedores/proveedor_form.html', {
        'form': form,
        'title': f'Editar Proveedor: {proveedor.nombre}',
        'is_create': False
    })


@never_cache
@login_required
@permission_required('core.change_proveedores', raise_exception=True)
def proveedor_baja_logica(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if proveedor.compras.exists():
        messages.error(request, 'No se puede dar de baja este proveedor porque tiene compras asociadas.')
        return redirect('proveedores_list')

    proveedor.is_active = False
    proveedor.save()
    messages.success(request, f'Proveedor {proveedor.razon_social} dado de baja exitosamente.')
    return redirect('proveedores_list')



@never_cache
@login_required
@permission_required('core.change_proveedores', raise_exception=True)
def proveedor_reactivar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.is_active = True
    proveedor.save()
    messages.success(request, f'Proveedor {proveedor.razon_social} reactivado exitosamente.')
    return redirect('proveedores_list')


@never_cache
@login_required
def cajas_list(request):
    cajas = Cajas.objects.all().order_by('-id_caja')
    return render(request, 'core/caja/cajas_list.html', {'cajas': cajas})


@never_cache
@login_required
def abrir_caja_view(request):
    empleado = Empleados.objects.get(user=request.user)
    caja_abierta = Cajas.objects.filter(caja_cerrada=0).first()

    if caja_abierta:
        messages.warning(request, "Ya existe una caja abierta.")
        return redirect('cajas_list')

    if request.method == 'POST':
        saldo_inicial = request.POST.get('saldo_inicial', 0)
        Cajas.objects.create(
            id_empleado=empleado,
            saldo_inicial=saldo_inicial,
            fecha_hora_apertura=timezone.now(),
            caja_cerrada=0
        )
        messages.success(request, f"Caja abierta con saldo inicial ${saldo_inicial}")
        return redirect('cajas_list')

    return render(request, 'core/caja/abrir_caja.html')


@never_cache
@login_required
def cerrar_caja_view(request):
    caja_abierta = Cajas.objects.filter(caja_cerrada=False).first()

    if not caja_abierta:
        messages.warning(request, "No hay ninguna caja abierta actualmente.")
        return redirect('cajas_list')

    if request.method == 'POST':
        try:
            monto_fisico = float(request.POST.get('monto_fisico', 0))
        except ValueError:
            messages.error(request, "El monto ingresado no es válido.")
            return redirect('cerrar_caja')

        saldo_final = caja_abierta.saldo_inicial
        diferencia = monto_fisico - saldo_final
        caja_abierta.fecha_hora_cierre = timezone.now()
        caja_abierta.monto_fisico = monto_fisico
        caja_abierta.saldo_final = saldo_final
        caja_abierta.diferencia = diferencia
        caja_abierta.caja_cerrada = True
        caja_abierta.save()

        if diferencia == 0:
            messages.success(request, f"Caja cerrada correctamente. Monto exacto ${monto_fisico:.2f}.")
        elif diferencia > 0:
            messages.warning(request, f"Caja cerrada con sobrante de ${diferencia:.2f}.")
        else:
            messages.error(request, f"Caja cerrada con faltante de ${abs(diferencia):.2f}.")

        return render(request, 'core/caja/cierre_exitoso.html', {'caja': caja_abierta})

    return render(request, 'core/caja/cerrar_caja.html', {'caja': caja_abierta})




@never_cache
@login_required
def detalle_caja_view(request, id):
    caja = get_object_or_404(Cajas, id_caja=id)
    movimientos = MovimientosCaja.objects.filter(id_caja=caja)
    return render(request, 'core/caja/detalle_caja.html', {'caja': caja, 'movimientos': movimientos})


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

@never_cache
@login_required
@permission_required('core.view_compras', raise_exception=True)
def compras_list(request):
    compras = []
    return render(request, 'core/compras_list.html', {'compras': compras})

@never_cache
@login_required
@permission_required('core.view_empleados', raise_exception=True)
def empleados_list(request):
    query = request.GET.get('q', '').strip()
    empleados = Empleados.objects.all().order_by('nombre')

    # 🔍 Búsqueda
    if query:
        empleados = empleados.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(dni__icontains=query) |
            Q(telefono__icontains=query) |
            Q(email__icontains=query) |
            Q(rol__icontains=query)
        )

    context = {
        'empleados': empleados,
        'query': query,
    }

    return render(request, 'core/empleados/empleados_list.html', context)


@never_cache
@login_required
@permission_required('core.view_configuracion', raise_exception=True)
def configuracion(request):
    configuracion = []
    return render(request, 'core/configuracion.html', {'configuracion': configuracion})


@never_cache
@login_required
def compras_cliente(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)
    compras = Compras.objects.filter(id_cliente=cliente).order_by('-fecha_compra')
    return render(request, 'core/clientes/compras_cliente.html', {
        'cliente': cliente,
        'compras': compras
    })


@never_cache
@login_required
def compras_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, id_proveedor=pk)
    compras = Compras.objects.filter(id_proveedor=proveedor).order_by('-fecha_compra')
    return render(request, 'core/proveedores/compras_proveedor.html', {
        'proveedor': proveedor,
        'compras': compras
    })



# ----------------------------------------------------------------------
# COMPRAS POR CLIENTE / PROVEEDOR
# ----------------------------------------------------------------------


@never_cache
@login_required
def compras_cliente(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)
    compras = Compras.objects.filter(id_cliente=cliente).order_by('-fecha_compra')
    return render(request, 'core/clientes/compras_cliente.html', {
        'cliente': cliente,
        'compras': compras
    })


@never_cache
@login_required
def compras_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, id_proveedor=pk)
    compras = Compras.objects.filter(id_proveedor=proveedor).order_by('-fecha_compra')
    return render(request, 'core/proveedores/compras_proveedor.html', {
        'proveedor': proveedor,
        'compras': compras
    })



# ----------------------------------------------------------------------
# EMPLEADOS
# ----------------------------------------------------------------------

@never_cache
@login_required
@permission_required('core.view_empleados', raise_exception=True)
def empleados_list(request):
    query = request.GET.get('q', '').strip()
    empleados = Empleados.objects.all().order_by('nombre')

    if query:
        empleados = empleados.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(dni__icontains=query) |
            Q(telefono__icontains=query) |
            Q(email__icontains=query) |
            Q(rol__icontains=query)
        )

    es_jefe = request.user.groups.filter(name__iexact='Jefe').exists()
    puede_crear = es_jefe or request.user.has_perm('core.add_empleados')

    context = {
        'empleados': empleados,
        'query': query,
        'puede_crear': puede_crear,
    }

    return render(request, 'core/empleados/empleados_list.html', context)



@never_cache
@login_required
def empleado_create(request):
    if not request.user.groups.filter(name__iexact='Jefe').exists():
        messages.error(request, "No tienes permiso para registrar nuevos empleados.")
        return redirect('empleados_list')

    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            empleado = form.save(commit=False)
            nombre_usuario = empleado.email or empleado.dni
            if not nombre_usuario:
                messages.error(request, 'Debe ingresar un email o DNI para crear el usuario.')
                return render(request, 'core/empleados/empleado_form.html', {
                    'form': form,
                    'title': 'Registrar Nuevo Empleado'
                })
            password_temporal = "tinta123"
            user = User.objects.create_user(
                username=nombre_usuario,
                email=empleado.email or "",
                first_name=empleado.nombre,
                last_name=empleado.apellido or "",
                password=password_temporal
            )
            if empleado.rol == "Jefe":
                grupo, _ = Group.objects.get_or_create(name="Jefe")
            else:
                grupo, _ = Group.objects.get_or_create(name="Empleados")
            user.groups.add(grupo)
            empleado.user = user
            empleado.save()

            messages.success(
                request,
                f'Empleado registrado exitosamente. '
                f'Se creó el usuario: {nombre_usuario} (contraseña: {password_temporal})'
            )
            return redirect('empleados_list')

        else:
            messages.error(request, 'Error al registrar el empleado. Verifica los datos.')
    else:
        form = EmpleadoForm()

    return render(request, 'core/empleados/empleado_form.html', {
        'form': form,
        'title': 'Registrar Nuevo Empleado'
    })


@never_cache
@login_required
@permission_required('core.change_empleados', raise_exception=True)
def empleado_edit(request, pk):
    empleado = get_object_or_404(Empleados, id_empleado=pk)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado actualizado exitosamente.')
            return redirect('empleados_list')
        else:
            messages.error(request, 'Error al actualizar el empleado.')
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, 'core/empleados/empleado_form.html', {'form': form, 'title': f'Editar Empleado: {empleado.nombre}'})


@login_required
@permission_required('core.delete_empleados', raise_exception=True)
def empleado_delete(request, pk):
    empleado = get_object_or_404(Empleados, pk=pk)

    if Cajas.objects.filter(id_empleado=empleado).exists():
        messages.error(request, f"No se puede eliminar a {empleado.nombre} {empleado.apellido} porque tiene cajas registradas.")
        return redirect('empleados_list')

    empleado.delete()
    messages.success(request, f"El empleado {empleado.nombre} {empleado.apellido} fue eliminado correctamente.")
    return redirect('empleados_list')

@login_required
@permission_required('core.change_empleados', raise_exception=True)
def empleado_baja_logica(request, pk):
    empleado = get_object_or_404(Empleados, pk=pk)
    
    if Cajas.objects.filter(id_empleado=empleado, caja_cerrada=False).exists():
        messages.error(request, f"No se puede dar de baja a {empleado.nombre} {empleado.apellido} porque tiene una caja abierta.")
        return redirect('empleados_list')

    empleado.is_active = False
    empleado.save()
    messages.warning(request, f"Empleado {empleado.nombre} {empleado.apellido} dado de baja correctamente.")
    return redirect('empleados_list')


@login_required
@permission_required('core.change_empleados', raise_exception=True)
def empleado_reactivar(request, pk):
    empleado = get_object_or_404(Empleados, pk=pk)
    empleado.is_active = True
    empleado.save()
    messages.success(request, f"Empleado {empleado.nombre} {empleado.apellido} reactivado correctamente.")
    return redirect('empleados_list')