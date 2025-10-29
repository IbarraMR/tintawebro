from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils import timezone
from core.models import Proveedores as Proveedor
from core.models import Cliente, Cajas, MovimientosCaja, Empleados, AuditoriaCaja, FormaPago
from core.forms import ClienteForm, ProveedorForm, EmpleadoForm, MovimientoCajaForm, FormaPagoForm
from core.models import Compras
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.db import transaction
from core.utils_caja import caja_abierta_de, registrar_movimiento
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from core.models import Compras, DetalleCompra, Insumos, Proveedores, MovimientosCaja, Cajas
from core.forms import ProveedorForm, InsumoForm


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
    empleado = Empleados.objects.filter(user=request.user).first()
    caja = None
    if empleado:
        caja = Cajas.objects.filter(id_empleado=empleado, caja_cerrada=False).order_by('-id_caja').first()
    if empleado:
        cajas = Cajas.objects.filter(id_empleado=empleado).order_by('-id_caja')[:50]
    else:
        cajas = Cajas.objects.none()
    return render(request, 'core/caja/cajas_list.html', {
        'caja': caja,
        'cajas': cajas,
    })


@never_cache
@login_required
@permission_required('core.add_cajas', raise_exception=True)
@transaction.atomic
@require_http_methods(["GET", "POST"])
def abrir_caja_view(request):
    empleado = Empleados.objects.filter(user=request.user).first()
    if not empleado:
        messages.error(request, "No tenés un Empleado asociado a tu usuario. Crealo y asociá tu User primero.")
        return redirect('empleados_list')

    ya_abierta = Cajas.objects.filter(id_empleado=empleado, caja_cerrada=False).exists()
    if ya_abierta:
        messages.warning(request, "Ya tenés una caja abierta.")
        return redirect('cajas_list')

    if request.method == 'POST':
        saldo_inicial_raw = request.POST.get('saldo_inicial', '0')
        try:
            saldo_inicial = float(saldo_inicial_raw or 0)
        except ValueError:
            messages.error(request, "Saldo inicial inválido.")
            return redirect('cajas_list')

        caja = Cajas.objects.create(
            id_empleado=empleado,
            saldo_inicial=saldo_inicial,
            saldo_final=saldo_inicial,
            fecha_hora_apertura=timezone.now(),
            diferencia=0,
            tolerancia=100,
            descripcion="Apertura de caja",
            caja_cerrada=False
        )

        AuditoriaCaja.objects.create(
            caja=caja,
            usuario=request.user,
            accion=AuditoriaCaja.Accion.ABRIR,
            detalle=f"Apertura con saldo inicial ${saldo_inicial:,.2f}"
        )
        messages.success(request, "Caja abierta correctamente.")
        return redirect('cajas_list')
    return render(request, 'core/caja/abrir_caja_modal.html')


@never_cache
@login_required
@permission_required('core.change_cajas', raise_exception=True)
@transaction.atomic
@require_http_methods(["GET", "POST"])
def cerrar_caja_view(request):
    empleado = Empleados.objects.filter(user=request.user).first()
    if not empleado:
        messages.error(request, "No tenés un Empleado asociado a tu usuario.")
        return redirect('empleados_list')
    caja = Cajas.objects.filter(id_empleado=empleado, caja_cerrada=False).order_by('-id_caja').first()
    if not caja:
        messages.warning(request, "No hay ninguna caja abierta.")
        return redirect('cajas_list')
    if request.method == 'POST':
        try:
            monto_fisico = float(request.POST.get('monto_fisico', '0') or 0)
        except ValueError:
            messages.error(request, "Monto físico inválido.")
            return redirect('cajas_list')
        saldo_sistema = float(caja.saldo_sistema)
        diferencia = round(monto_fisico - saldo_sistema, 2)
        caja.monto_fisico = monto_fisico
        caja.diferencia = diferencia
        caja.saldo_final = saldo_sistema
        caja.fecha_hora_cierre = timezone.now()
        caja.caja_cerrada = True
        caja.save()
        AuditoriaCaja.objects.create(
            caja=caja,
            usuario=request.user,
            accion=AuditoriaCaja.Accion.CERRAR,
            detalle=f"Cierre: sistema ${saldo_sistema:,.2f}, físico ${monto_fisico:,.2f}, dif ${diferencia:,.2f}"
        )
        request.session['cierre_info'] = {
            'sistema': f"{saldo_sistema:,.2f}",
            'fisico': f"{monto_fisico:,.2f}",
            'dif': f"{diferencia:,.2f}",
            'dentro_tol': abs(diferencia) <= float(caja.tolerancia),
        }
        messages.success(request, "Caja cerrada correctamente.")
        return redirect('cajas_list')
    return render(request, 'core/caja/cerrar_caja_modal.html', {
        'saldo_sistema': caja.saldo_sistema
    })



@never_cache
@login_required
@permission_required('core.view_movimientoscaja', raise_exception=True)
def movimientos_list(request):

    q = request.GET.get("q", "")
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")
    forma_pago = request.GET.get("forma_pago")

    movs = MovimientosCaja.objects.all().order_by("-fecha_hora")  # ✅ trae todos

    if q:
        movs = movs.filter(Q(descripcion__icontains=q) | Q(id__icontains=q))

    if desde:
        movs = movs.filter(fecha_hora__date__gte=desde)
    if hasta:
        movs = movs.filter(fecha_hora__date__lte=hasta)

    if forma_pago:
        movs = movs.filter(forma_pago__id_forma=forma_pago)

    from django.core.paginator import Paginator
    paginator = Paginator(movs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    formas_pago = FormaPago.objects.all()
    form = MovimientoCajaForm()

    return render(request, "core/caja/movimientos_list.html", {
        "movs": page_obj,
        "page_obj": page_obj,
        "form": form,
        "formas_pago": formas_pago,
        "filtro_busqueda": q,
        "filtro_fecha_desde": desde,
        "filtro_fecha_hasta": hasta,
        "filtro_forma_pago": forma_pago,
    })



@never_cache
@login_required
@permission_required('core.add_movimientoscaja', raise_exception=True)
def movimiento_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    form = MovimientoCajaForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Datos inválidos"}, status=400)

    cd = form.cleaned_data
    mov, err = registrar_movimiento(
        request,
        tipo=cd["tipo"],
        forma_pago_id=cd["forma_pago"].id_forma,
        monto=cd["monto"],
        descripcion=cd["descripcion"],
        origen=MovimientosCaja.Origen.MANUAL
    )
    if err:
        return JsonResponse({"error": err}, status=400)

    return JsonResponse({
        "success": True,
        "mov": {
            "id": mov.id,                                               # <- PK real
            "fecha_hora": mov.fecha_hora.strftime("%d/%m/%Y %H:%M"),
            "tipo": mov.get_tipo_display(),
            "monto": f"{mov.monto:,.2f}",
            "descripcion": mov.descripcion,
            "caja": mov.caja.id_caja
        },
        "saldoActualizado": f"{mov.saldo_resultante:,.2f}"
    })



@never_cache
@login_required
def detalle_caja_view(request, id):
    caja = get_object_or_404(Cajas, id_caja=id)
    movimientos = MovimientosCaja.objects.filter(caja=caja).order_by('-fecha_hora')
    return render(request, 'core/caja/detalle_caja.html', {'caja': caja, 'movimientos': movimientos})

# FORMAS DE PAGO ------------------------------------------------------

@never_cache
@login_required
@permission_required('core.view_formapago', raise_exception=True)
def formas_pago_list(request):
    formas_pago = FormaPago.objects.all().order_by('id_forma')
    form = FormaPagoForm()  # ← AGREGADO: pasar formulario al template
    return render(request, "core/caja/formas_pago_list.html", {
        "formas_pago": formas_pago,
        "form": form
    })



@never_cache
@login_required
@permission_required('core.add_formapago', raise_exception=True)
def formas_pago_create(request):
    if request.method == "POST":
        form = FormaPagoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Forma de pago agregada correctamente.")
        else:
            messages.error(request, "❌ Error al agregar la forma de pago.")
    return redirect("formas_pago_list")



@never_cache
@login_required
@permission_required('core.change_formapago', raise_exception=True)
def formas_pago_toggle(request, id):
    forma = get_object_or_404(FormaPago, id_forma=id)
    forma.activo = not forma.activo
    forma.save()
    messages.info(request, f"🔁 Estado actualizado: {forma.nombre}")
    return redirect("formas_pago_list")


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
@permission_required("core.view_insumos", raise_exception=True)
def insumos_list(request):

    insumos = Insumos.objects.select_related("proveedor").all()
    proveedores = Proveedores.objects.all()      
    form = InsumoForm()

    return render(request, "core/insumos_list.html", {
        "insumos": insumos,
        "form": form,
        "proveedores": proveedores,            
    })


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

@login_required
@permission_required("core.add_compras", raise_exception=True)
def compras_create(request):
    if request.method == "POST":
        proveedor_id = request.POST.get("proveedor")
        insumo_id = request.POST.get("insumo")
        cantidad = request.POST.get("cantidad")
        precio_unitario = request.POST.get("precio_unitario")

        proveedor = Proveedores.objects.get(id_proveedor=proveedor_id)
        insumo = Insumos.objects.get(id_insumo=insumo_id)

        # obtenemos la caja abierta del empleado
        caja = Cajas.objects.filter(empleado=request.user.empleados, estado="ABIERTA").first()

        if not caja:
            return render(request, "compras/compras_form.html", {
                "error": "No hay una caja abierta. Debe abrir caja para registrar compras.",
                "proveedor_form": ProveedorForm(),
                "insumo_form": InsumoForm(),
            })

        total = float(precio_unitario) * float(cantidad)

        # VALIDAR SALDO SUFICIENTE
        if caja.saldo_actual < total:
            return render(request, "compras/compras_form.html", {
                "error": "Saldo insuficiente en caja.",
                "proveedor_form": ProveedorForm(),
                "insumo_form": InsumoForm(),
            })

        # Guardamos compra
        compra = Compras.objects.create(
            proveedor=proveedor,
            empleado=request.user.empleados,
            total=total
        )

        # Guardamos detalle de compra
        DetalleCompra.objects.create(
            compra=compra,
            insumo=insumo,
            cantidad=cantidad,
            precio_unitario=precio_unitario
        )

        # Actualiza el stock del insumo
        insumo.stock += float(cantidad)
        insumo.save()

        # Genera movimiento de caja
        MovimientosCaja.objects.create(
            caja=caja,
            tipo="EGRESO",
            descripcion=f"Compra de insumo: {insumo.nombre}",
            monto=total,
        )

        # Resta saldo en caja
        caja.saldo_actual -= total
        caja.save()

        return redirect("compras_list")  # o donde corresponda

    # GET (primera carga del formulario)
    return render(request, "compras/compras_form.html", {
        "proveedor_form": ProveedorForm(),
        "insumo_form": InsumoForm(),
    })


@never_cache
@login_required
@permission_required("core.add_proveedores", raise_exception=True)
def proveedor_create_ajax(request):
    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            return JsonResponse({
                "success": True,
                "id": proveedor.id_proveedor,
                "nombre": proveedor.nombre
            })
        return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


@never_cache
@login_required
@permission_required("core.add_insumos", raise_exception=True)
def insumo_create_ajax(request):
    if request.method == "POST":
        form = InsumoForm(request.POST)
        if form.is_valid():
            insumo = form.save()
            return JsonResponse({
                "success": True,
                "id": insumo.id_insumo,
                "nombre": insumo.nombre
            })
        return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
