import json

from django import forms
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.forms import modelformset_factory, inlineformset_factory
from django.db.models import Sum
from core.forms import (
    ClienteForm, ComprasForm, DetallesCompraFormSet, EmpleadoForm, 
    FormaPagoForm, InsumoForm, MovimientoCajaForm, ProveedorForm
)
from core.models import (
    AuditoriaCaja, Cajas, Cliente, Compras, DetallesCompra, Empleados, 
    EstadosPedidos, FormaPago, Insumos, MovimientosCaja, Pedidos, 
    PedidosInsumos, Presupuestos, PresupuestosInsumos, Proveedores, 
    Proveedores as Proveedor
) 
from core.utils_caja import registrar_movimiento
# ----------------------------------------------------------------------
# CONTROL DE ACCESO
# ----------------------------------------------------------------------
def es_duenio(user):
    return user.is_authenticated and user.groups.filter(name='Jefe').exists()

# ----------------------------------------------------------------------
# AUTENTICACIÓN / HOME
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

    # ✅ Obtener la última caja abierta
    caja = Cajas.objects.filter(caja_cerrada=False).order_by('-id_caja').first()

    saldo_actual = None
    caja_abierta = False

    if caja:
        caja_abierta = True
        # Usamos el saldo que guardás en tu modelo Cajas
        saldo_actual = caja.saldo_sistema

    es_duenio = request.user.groups.filter(name='Jefe').exists()
    es_empleado = request.user.groups.filter(name='Empleados').exists()

    context = {
        'pedidos_pendientes_count': 0,
        'ventas_30_dias': 0,
        'insumos_criticos_count': 0,
        'clientes_total_count': Cliente.objects.count(),

        # 🔥 Nuevos valores que necesita el template
        'caja': caja,
        'saldo_actual': saldo_actual,
        'caja_abierta': caja_abierta,

        'es_duenio': es_duenio,
        'es_empleado': es_empleado,
        'puede_ver_caja': es_duenio or es_empleado,
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
        'form': form, 'title': 'Registrar Nuevo Cliente', 'is_create': True
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
        'form': form, 'title': f'Editar Cliente: {cliente.nombre}', 'is_create': False
    })

@never_cache
@login_required
@permission_required('core.delete_cliente', raise_exception=True)
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)

    if request.method == 'POST':
        try:
            cliente.delete()  # Si tiene Pedidos/Presupuestos vinculados (PROTECT), lanzará ProtectedError
            messages.success(request, 'Cliente eliminado correctamente.')
        except ProtectedError:
            messages.error(
                request,
                'No se puede eliminar: el cliente tiene compras/pedidos (u otros movimientos) asociados.'
            )
        return redirect('clientes_list')

    return redirect('clientes_list')

# ----------------------------------------------------------------------
# PROVEEDORES
# ----------------------------------------------------------------------
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
    return render(request, 'core/proveedores/proveedores_list.html', {
        'proveedores': proveedores, 'query': query
    })

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
        'form': form, 'title': 'Registrar Nuevo Proveedor', 'is_create': True
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
        'form': form, 'title': f'Editar Proveedor: {proveedor.nombre}', 'is_create': False
    })

@never_cache
@login_required
@permission_required('core.change_proveedores', raise_exception=True)
def proveedor_baja_logica(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if hasattr(proveedor, 'compras') and proveedor.compras.exists():
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

# ----------------------------------------------------------------------
# INSUMOS 
# ----------------------------------------------------------------------
@never_cache
@login_required
@permission_required('core.view_insumos', raise_exception=True)
def insumos_list(request):
    insumos = Insumos.objects.all().order_by('nombre')
    return render(request, 'core/insumos/insumos_list.html', {'insumos': insumos})

@never_cache
@login_required
@require_http_methods(["POST"])
@permission_required("core.add_proveedores", raise_exception=True)
def proveedor_create_ajax(request):
    form = ProveedorForm(request.POST)
    if form.is_valid():
        proveedor = form.save()
        return JsonResponse({
            "success": True,
            "id": proveedor.id_proveedor,
            "nombre": proveedor.nombre
        })
    return JsonResponse({"success": False, "errors": form.errors}, status=400)

@login_required
@permission_required("core.add_insumos", raise_exception=True)
def insumo_create(request):
    if request.method == "POST":
        form = InsumoForm(request.POST)
        if form.is_valid():
            insumo = form.save()
            return redirect("compras_create")  # vuelve a la pantalla de compras

    else:
        form = InsumoForm()

    return render(request, "core/insumos/insumo_form.html", {"form": form})


@never_cache
@login_required
@permission_required('core.change_insumos', raise_exception=True)
def insumo_edit(request, pk):
    insumo = get_object_or_404(Insumos, id_insumo=pk)
    if request.method == 'POST':
        form = InsumoForm(request.POST, instance=insumo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Insumo actualizado exitosamente.')
            return redirect('insumos_list')
        else:
            messages.error(request, 'Error al actualizar el insumo.')
    else:
        form = InsumoForm(instance=insumo)

    return render(request, 'core/insumos/insumo_form.html', {
        'form': form, 'title': f'Editar Insumo: {insumo.nombre}', 'is_create': False
    })


@never_cache
@login_required
@transaction.atomic
def compras_create(request):
    try:
        cajas_abiertas = Cajas.objects.filter(caja_cerrada=False).order_by('-id_caja')
        
        if cajas_abiertas.exists():
            caja_abierta = cajas_abiertas.first() 
        else:
            raise Cajas.DoesNotExist

    except Cajas.DoesNotExist:
        messages.error(request, "ERROR: No hay ninguna caja abierta. No se puede registrar la compra.")
        return redirect('tu_url_de_inicio_o_dashboard')

    if request.method == 'POST':
        form = ComprasForm(request.POST)
        formset = DetallesCompraFormSet(request.POST, instance=Compras())
        
        try:
            empleado_actual = Empleados.objects.get(user=request.user)
        except Empleados.DoesNotExist:
             messages.error(request, "Usuario no vinculado a un empleado.")
             return redirect('tu_url_de_inicio_o_dashboard')

        if form.is_valid() and formset.is_valid():
            total_compra = 0
            
            for detalle_form in formset:
                if detalle_form.cleaned_data.get('DELETE'):
                    continue
                
                cantidad = detalle_form.cleaned_data.get('cantidad')
                precio_unitario = detalle_form.cleaned_data.get('precio_unitario')
                
                if cantidad and precio_unitario:
                    total_compra += (cantidad * precio_unitario)

            if caja_abierta.saldo_sistema < total_compra:
                 messages.error(request, f"Saldo insuficiente en caja. Saldo actual: ${caja_abierta.saldo_sistema:.2f}. Total compra: ${total_compra:.2f}.")
                 return redirect('compras_create') 
            compra = form.save(commit=False)
            compra.total = total_compra
            compra.save()
            for detalle_form in formset:
                if detalle_form.cleaned_data.get('DELETE'):
                    continue
                
                detalle = detalle_form.save(commit=False)
                detalle.compra = compra
                detalle.save()
                insumo = detalle.insumo
                insumo.stock_actual = (insumo.stock_actual or 0) + detalle.cantidad
                insumo.save()

            MovimientosCaja.objects.create(
                caja=caja_abierta,
                tipo=MovimientosCaja.Tipo.EGRESO,
                forma_pago=form.cleaned_data['forma_pago'],
                monto=total_compra,
                descripcion=f"Pago a {compra.proveedor.nombre} por Compra #{compra.id_compra}",
                origen=MovimientosCaja.Origen.COMPRA,
                referencia_id=compra.id_compra,
                creado_por=empleado_actual,
                saldo_resultante=caja_abierta.saldo_sistema - total_compra # El saldo_sistema se actualiza automáticamente con MovimientosCaja
            )

            messages.success(request, f"Compra #{compra.id_compra} registrada y stock actualizado.")
            return redirect('compras_list') 

    else:
        # GET Request
        form = ComprasForm(initial={'fecha': timezone.now().date()})
        formset = DetallesCompraFormSet(instance=Compras())

    precios_insumos = {
    str(insumo.id_insumo): str(insumo.precio_costo_unitario or 0) 
    for insumo in Insumos.objects.all()
}
    
    context = {
        'form': form,
        'formset': formset,
        'caja_abierta': caja_abierta, 
        'proveedor_form': ProveedorForm(), 
        'insumo_form': InsumoForm(),
        'insumo_precios_json': json.dumps(precios_insumos),
    }
    return render(request, 'tinta_negra_web/compras_form.html', context)

@never_cache
@login_required
def compras_list(request):
    compras = Compras.objects.all().order_by('-fecha')
    
    context = {
        'compras': compras
    }
    return render(request, 'tinta_negra_web/compras_list.html', context)

@never_cache
@login_required
def compra_detalle(request, pk):
    compra = get_object_or_404(Compras, pk=pk)
    detalles = DetallesCompra.objects.filter(compra=compra)
    
    context = {
        'compra': compra,
        'detalles': detalles,
    }
    return render(request, 'tinta_negra_web/compra_detalle.html', context)


@never_cache
@login_required
@permission_required('core.delete_insumos', raise_exception=True)
def insumo_delete(request, pk):
    insumo = get_object_or_404(Insumos, id_insumo=pk)
    if request.method == 'POST':
        insumo.delete()
        messages.success(request, 'Insumo eliminado exitosamente.')
        return redirect('insumos_list')

    return redirect('insumos_list')




@login_required
def insumo_datos_ajax(request, pk):
    insumo = get_object_or_404(Insumos, id_insumo=pk)
    return JsonResponse({
        "id": insumo.id_insumo,
        "nombre": insumo.nombre,
        # Se usa str() para asegurar formato serializable para decimales
        "precio": str(insumo.precio_costo_unitario or "0.00"), 
        "unidad": insumo.unidad_medida,
    })


@login_required
@transaction.atomic
def insumo_editar_ajax(request):
    """Edita un insumo existente desde el modal (actualiza precio y demás campos)."""
    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    insumo_id = request.POST.get("id_insumo")
    insumo = get_object_or_404(Insumos, id_insumo=insumo_id)

    # actualizar campos
    insumo.nombre = request.POST.get("nombre") or insumo.nombre
    insumo.descripcion = request.POST.get("descripcion") or insumo.descripcion
    insumo.unidad_medida = request.POST.get("unidad_medida") or insumo.unidad_medida
    insumo.stock_minimo = request.POST.get("stock_minimo") or insumo.stock_minimo

    precio = request.POST.get("precio_costo_unitario")
    if precio is not None and precio != "":
        insumo.precio_costo_unitario = precio

    prov_id = request.POST.get("proveedor")
    if prov_id:
        # Se asume que Proveedores tiene el campo id_proveedor como pk, si no, usar pk=prov_id
        insumo.proveedor = get_object_or_404(Proveedores, pk=prov_id) 

    insumo.save()

    return JsonResponse({
        "success": True,
        "id": insumo.id_insumo,
        "nombre": insumo.nombre,
        "precio_costo_unitario": str(insumo.precio_costo_unitario or "0.00"),
    })


@login_required
@transaction.atomic
def insumo_nuevo_ajax(request):
    """Crea un insumo desde el modal de compras y lo devuelve para seleccionarlo."""
    if request.method != "POST":
        return HttpResponseBadRequest("Método inválido")

    prov = get_object_or_404(Proveedores, pk=request.POST.get("proveedor"))
    insumo = Insumos.objects.create(
        proveedor=prov,
        nombre=request.POST.get("nombre"),
        descripcion=request.POST.get("descripcion"),
        unidad_medida=request.POST.get("unidad_medida"),
        stock_actual=request.POST.get("stock_actual") or 0,
        stock_minimo=request.POST.get("stock_minimo") or 0,
        precio_costo_unitario=request.POST.get("precio_costo_unitario") or 0,
    )
    return JsonResponse({
        "success": True,
        "id": insumo.id_insumo,
        "nombre": insumo.nombre,
        "precio_costo_unitario": str(insumo.precio_costo_unitario or "0.00"),
    })

# ----------------------------------------------------------------------
# CAJAS
# ----------------------------------------------------------------------
@never_cache
@login_required
def cajas_list(request):
    empleado = Empleados.objects.filter(user=request.user).first()
    caja = None
    if empleado:
        caja = Cajas.objects.filter(id_empleado=empleado, caja_cerrada=False).order_by('-id_caja').first()
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
        messages.error(request, "No tenés un Empleado asociado a tu usuario.")
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
            accion=AuditoriaCaja.Accion.ABRIR if hasattr(AuditoriaCaja, 'Accion') else "ABRIR",
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

        saldo_sistema = float(getattr(caja, 'saldo_sistema', caja.saldo_final))
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
            accion=AuditoriaCaja.Accion.CERRAR if hasattr(AuditoriaCaja, 'Accion') else "CERRAR",
            detalle=f"Cierre: sistema ${saldo_sistema:,.2f}, físico ${monto_fisico:,.2f}, dif ${diferencia:,.2f}"
        )

        request.session['cierre_info'] = {
            'sistema': f"{saldo_sistema:,.2f}",
            'fisico': f"{monto_fisico:,.2f}",
            'dif': f"{diferencia:,.2f}",
            'dentro_tol': abs(diferencia) <= float(getattr(caja, 'tolerancia', 0)),
        }
        messages.success(request, "Caja cerrada correctamente.")
        return redirect('cajas_list')

    return render(request, 'core/caja/cerrar_caja_modal.html', {
        'saldo_sistema': getattr(caja, 'saldo_sistema', caja.saldo_final)
    })

@never_cache
@login_required
def detalle_caja_view(request, id):
    caja = get_object_or_404(Cajas, id_caja=id)
    movimientos = MovimientosCaja.objects.filter(caja=caja).order_by('-fecha_hora')
    return render(request, 'core/caja/detalle_caja.html', {'caja': caja, 'movimientos': movimientos})

# ----------------------------------------------------------------------
# MOVIMIENTOS CAJA
# ----------------------------------------------------------------------
@never_cache
@login_required
@permission_required('core.view_movimientoscaja', raise_exception=True)
def movimientos_list(request):
    q = request.GET.get("q", "")
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")
    forma_pago = request.GET.get("forma_pago")

    movs = MovimientosCaja.objects.all().order_by("-fecha_hora")
    if q:
        movs = movs.filter(Q(descripcion__icontains=q))

    if desde:
        movs = movs.filter(fecha_hora__date__gte=desde)
    if hasta:
        movs = movs.filter(fecha_hora__date__lte=hasta)
    if forma_pago:
        movs = movs.filter(forma_pago__id_forma=forma_pago)

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
        forma_pago_id=cd["forma_pago"].id_forma if cd.get("forma_pago") else None,
        monto=cd["monto"],
        descripcion=cd["descripcion"],
        origen=getattr(MovimientosCaja.Origen, 'MANUAL', None),
    )
    if err:
        return JsonResponse({"error": err}, status=400)

    return JsonResponse({
        "success": True,
        "mov": {
            "id": mov.id,
            "fecha_hora": mov.fecha_hora.strftime("%d/%m/%Y %H:%M"),
            "tipo": getattr(mov, 'get_tipo_display', lambda: mov.tipo)(),
            "monto": f"{mov.monto:,.2f}",
            "descripcion": mov.descripcion,
            "caja": mov.caja.id_caja
        },
        "saldoActualizado": f"{getattr(mov, 'saldo_resultante', 0):,.2f}"
    })

# ----------------------------------------------------------------------
# FORMAS DE PAGO
# ----------------------------------------------------------------------
@never_cache
@login_required
@permission_required('core.view_formapago', raise_exception=True)
def formas_pago_list(request):
    formas_pago = FormaPago.objects.all().order_by('id_forma')
    form = FormaPagoForm()
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
            grupo, _ = Group.objects.get_or_create(name="Jefe" if empleado.rol == "Jefe" else "Empleados")
            user.groups.add(grupo)
            empleado.user = user
            empleado.save()

            messages.success(
                request,
                f'Empleado registrado. Usuario: {nombre_usuario} (contraseña: {password_temporal})'
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

    return render(request, 'core/empleados/empleado_form.html', {
        'form': form, 'title': f'Editar Empleado: {empleado.nombre}'
    })

@never_cache
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

@never_cache
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

@never_cache
@login_required
@permission_required('core.change_empleados', raise_exception=True)
def empleado_reactivar(request, pk):
    empleado = get_object_or_404(Empleados, pk=pk)
    empleado.is_active = True
    empleado.save()
    messages.success(request, f"Empleado {empleado.nombre} {empleado.apellido} reactivado correctamente.")
    return redirect('empleados_list')

# ----------------------------------------------------------------------
# COMPRAS por CLIENTE / PROVEEDOR (vínculos)
# ----------------------------------------------------------------------
@never_cache
@login_required
def compras_cliente(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)
    compras = Compras.objects.filter(id_cliente=cliente).order_by('-fecha_compra') if hasattr(Compras, 'fecha_compra') else Compras.objects.filter(id_cliente=cliente).order_by('-id_compra')
    return render(request, 'core/clientes/compras_cliente.html', {
        'cliente': cliente, 'compras': compras
    })

@never_cache
@login_required
def compras_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, id_proveedor=pk)
    compras = Compras.objects.filter(id_proveedor=proveedor).order_by('-fecha_compra') if hasattr(Compras, 'fecha_compra') else Compras.objects.filter(id_proveedor=proveedor).order_by('-id_compra')
    return render(request, 'core/proveedores/compras_proveedor.html', {
        'proveedor': proveedor, 'compras': compras
    })

# ----------------------------------------------------------------------
# PRESUPUESTOS / PEDIDOS / CONFIG
# ----------------------------------------------------------------------
@never_cache
@login_required
@permission_required('core.view_pedidos', raise_exception=True)
def pedidos_list(request):
    pedidos = Pedidos.objects.all().order_by('-id_pedido')[:100] if hasattr(Pedidos, 'id_pedido') else []
    return render(request, 'core/pedidos_list.html', {'pedidos': pedidos})

@never_cache
@login_required
@permission_required('core.view_presupuestos', raise_exception=True)
def presupuestos_list(request):
    presupuestos = Presupuestos.objects.all().order_by('-id_presupuesto')[:100] if hasattr(Presupuestos, 'id_presupuesto') else []
    return render(request, 'core/presupuestos_list.html', {'presupuestos': presupuestos})

@never_cache
@login_required
@permission_required('core.view_configuracion', raise_exception=True)
def configuracion(request):
    return render(request, 'core/configuracion.html', {'configuracion': []})


@login_required
@transaction.atomic
def convertir_presupuesto_a_pedido(request, pk):
    presupuesto = get_object_or_404(Presupuestos, id_presupuesto=pk)

    # Crear el Pedido a partir del Presupuesto
    pedido = Pedidos.objects.create(
        id_cliente=presupuesto.id_cliente,
        total_pedido=presupuesto.total_presupuesto,
        # Nota: Asume que Pedidos tiene los campos id_cliente y total_pedido
    )

    detalles_presupuesto = PresupuestosInsumos.objects.filter(id_presupuesto=presupuesto)

    # Transferir detalles
    for det in detalles_presupuesto:
        PedidosInsumos.objects.create(
            pedido=pedido,
            insumo=det.id_insumo,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
        )

    messages.success(request, "Pedido generado correctamente. Ahora puedes modificar cantidades.")

    return redirect('pedido_editar_insumos', pedido.id_pedido)


@login_required
def pedido_editar_insumos(request, pk):
    pedido = get_object_or_404(Pedidos, id_pedido=pk)

    # Formset para editar las cantidades
    DetalleFormSet = modelformset_factory(
        PedidosInsumos,
        fields=('cantidad',),
        extra=0
    )

    if request.method == "POST":
        formset = DetalleFormSet(request.POST, queryset=PedidosInsumos.objects.filter(pedido=pedido))
        if formset.is_valid():
            formset.save()
            messages.success(request, "Cantidades actualizadas. Lista para confirmar.")
            return redirect('pedido_confirmar', pedido.id_pedido)
        else:
            messages.error(request, "Error al actualizar las cantidades.")
    else:
        formset = DetalleFormSet(queryset=PedidosInsumos.objects.filter(pedido=pedido))

    return render(request, "core/pedidos/pedido_editar_insumos.html", {
        "formset": formset,
        "pedido": pedido,
    })


@login_required
@transaction.atomic
def pedido_confirmar(request, pk):
    pedido = get_object_or_404(Pedidos, id_pedido=pk)
    detalles = PedidosInsumos.objects.filter(pedido=pedido)

    # Actualizar Stock
    for det in detalles:
        # Se asume que det.insumo es la instancia de Insumos
        det.insumo.stock_actual -= det.cantidad
        det.insumo.save()

    # Actualizar Estado del Pedido
    pedido.id_estado = get_object_or_404(EstadosPedidos, pk=2) # ejemplo: 2 = confirmado
    pedido.save()

    messages.success(request, "Pedido confirmado. Stock actualizado.")
    return redirect('pedidos_list')
