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
from django.views.decorators.http import require_http_methods, require_POST
from django.forms import modelformset_factory, inlineformset_factory
from django.db.models import Sum
from decimal import Decimal
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string, get_template
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from django.core.mail import EmailMessage
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from xhtml2pdf import pisa
from datetime import date, timedelta
from core.forms import (
    ClienteForm, ComprasForm, DetallesCompraFormSet, EmpleadoForm, 
    FormaPagoForm, InsumoForm, MovimientoCajaForm, ProveedorForm, 
    PresupuestoForm, ProductoInsumoForm, ConfiguracionEmpresaForm, ConfiguracionEmailForm, ProductoForm,
)
from core.models import (
    AuditoriaCaja, Cajas, Cliente, Compras, DetallesCompra, Empleados, 
    EstadosPedidos, FormaPago, Insumos, MovimientosCaja, Pedidos, 
    PedidosInsumos, Presupuestos, PresupuestosInsumos,UnidadMedida, Proveedores,
    StockMovimientos, Productos, ProductosInsumos,ConfiguracionEmpresa, ConfiguracionEmail,
    PresupuestosProductos, Trabajo, TrabajoInsumo, TiposProducto, FormaPago,
    Proveedores as Proveedor
) 
from core.utils_caja import registrar_movimiento
import io, base64
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from datetime import timedelta
from django.db import models
from django.db.models import F



def es_duenio(user):
    return user.is_authenticated and user.groups.filter(name='Jefe').exists()


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

    ultima_caja = Cajas.objects.order_by("-id_caja").first()
    caja_abierta = False
    saldo_actual = 0

    if ultima_caja:
        caja_abierta = not ultima_caja.caja_cerrada
        saldo_actual = ultima_caja.saldo_sistema if caja_abierta else ultima_caja.saldo_final

    pedidos_pendientes = Pedidos.objects.exclude(
        id_estado__nombre_estado__in=["ENTREGADO", "CANCELADO"]
    ).select_related("id_cliente").order_by("-id_pedido")

    pedidos_pendientes_count = pedidos_pendientes.count()
    pedidos_recientes = Pedidos.objects.select_related(
        "id_cliente", "id_estado"
    ).order_by("-id_pedido")[:5]


    insumos_criticos = Insumos.objects.filter(
        stock_actual__lte=F("stock_minimo")
    ).order_by("stock_actual")

    insumos_criticos_count = insumos_criticos.count()
    es_duenio = request.user.groups.filter(name='Jefe').exists()
    es_empleado = request.user.groups.filter(name='Empleados').exists()

    context = {
        "caja": ultima_caja,
        "caja_abierta": caja_abierta,
        "saldo_actual": saldo_actual,

        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_pendientes_count": pedidos_pendientes_count,
        "pedidos_recientes": pedidos_recientes,

        "insumos_criticos": insumos_criticos,
        "insumos_criticos_count": insumos_criticos_count,

        "es_duenio": es_duenio,
        "es_empleado": es_empleado,
        "puede_ver_caja": es_duenio or es_empleado,
    }

    if es_empleado:
        return render(request, "core/home_empleado.html", context)

    return render(request, "core/home.html", context)


from django.core.paginator import Paginator

@never_cache
@login_required
@permission_required('core.view_cliente', raise_exception=True)
def clientes_list(request):
    query = request.GET.get('q', '').strip()

    clientes_qs = Cliente.objects.all().order_by('nombre')

    if query:
        clientes_qs = clientes_qs.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(dni__icontains=query) |
            Q(telefono__icontains=query)
        )

    paginator = Paginator(clientes_qs, 15)
    page_number = request.GET.get("page")
    clientes = paginator.get_page(page_number)

    return render(request, 'core/clientes/clientes_list.html', {
        'clientes': clientes,  
        'query': query,
        'page_obj': clientes,  
    })

@never_cache
@login_required
@permission_required('core.add_cliente', raise_exception=True)
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Cliente registrado exitosamente.', extra_tags="cliente")
                list(messages.get_messages(request))
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
            messages.success(request, 'Cliente actualizado exitosamente.', extra_tags="cliente")
            list(messages.get_messages(request))
            return redirect('clientes_list')
        else:
            messages.error(request, 'Error al actualizar el cliente. Verifique los datos.')
            list(messages.get_messages(request))  
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'core/clientes/cliente_form.html', {
        'form': form,
        'cliente': cliente,                  
        'title': f'Editar Cliente: {cliente.nombre}',
        'is_create': False                    
    })


@never_cache
@login_required
@permission_required('core.delete_cliente', raise_exception=True)
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)

    if request.method == 'POST':
        try:
            cliente.delete()  
            messages.success(request, 'Cliente eliminado correctamente.', extra_tags="cliente")
            list(messages.get_messages(request))
        except ProtectedError:
            messages.error(
                request,
                'No se puede eliminar: el cliente tiene compras/pedidos (u otros movimientos) asociados.'
            )
        return redirect('clientes_list')

    return redirect('clientes_list')


from django.core.paginator import Paginator

@never_cache
@login_required
@permission_required('core.view_proveedores', raise_exception=True)
def proveedores_list(request):
    query = request.GET.get('q', '').strip()

    proveedores_qs = Proveedor.objects.all().order_by('nombre')

    if query:
        proveedores_qs = proveedores_qs.filter(
            Q(nombre__icontains=query) |
            Q(razon_social__icontains=query) |
            Q(cuit__icontains=query) |
            Q(telefono__icontains=query)
        )
    paginator = Paginator(proveedores_qs, 15)
    page_number = request.GET.get("page")
    proveedores = paginator.get_page(page_number)

    return render(request, 'core/proveedores/proveedores_list.html', {
        'proveedores': proveedores,  
        'query': query,
        'page_obj': proveedores,      
    })


@never_cache
@login_required
@permission_required('core.add_proveedores', raise_exception=True)
def proveedor_create(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor registrado exitosamente.', extra_tags="proveedor")
            list(messages.get_messages(request))
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
    proveedor = get_object_or_404(Proveedores, id_proveedor=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente.', extra_tags="proveedor")
            list(messages.get_messages(request))
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
@permission_required("core.delete_proveedores", raise_exception=True)
def proveedor_baja(request, pk):
    proveedor = get_object_or_404(Proveedores, id_proveedor=pk)
    tiene_compras = proveedor.compras_set.exists() if hasattr(proveedor, "compras_set") else False
    if tiene_compras:
        proveedor.is_active = False
        proveedor.save()
        messages.success(
            request,
            f"El proveedor {proveedor.nombre} fue dado de baja (tiene compras asociadas)."
        )
    else:
        proveedor.delete()

        messages.success(
            request,
            f"Proveedor eliminado definitivamente (no tenía compras asociadas)."
        )
    return redirect("proveedores_list")


@never_cache
@login_required
@permission_required('core.change_proveedores', raise_exception=True)
def proveedor_reactivar(request, pk):
    proveedor = get_object_or_404(Proveedores, pk=pk)
    proveedor.is_active = True
    proveedor.save()
    messages.success(request, f'Proveedor {proveedor.nombre} reactivado correctamente.')
    return redirect('proveedores_list')




from django.db.models import Q
from django.core.paginator import Paginator

@never_cache
@login_required
@permission_required('core.view_insumos', raise_exception=True)
def insumos_list(request):

    # 🔍 Buscar por nombre o proveedor
    query = request.GET.get("q", "").strip()

    lista_insumos = Insumos.objects.all().order_by("nombre")

    if query:
        lista_insumos = lista_insumos.filter(
            Q(nombre__icontains=query) |
            Q(proveedor__nombre__icontains=query)
        )
    paginator = Paginator(lista_insumos, 15)
    page_number = request.GET.get("page")
    insumos = paginator.get_page(page_number)

    return render(request, 'core/insumos/insumos_list.html', {
        'insumos': insumos,
        'query': query,
    })



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
            return redirect("insumos_list") 
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
            messages.success(request, 'Insumo actualizado exitosamente.', extra_tags="insumo")
            list(messages.get_messages(request))
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
        caja_abierta = Cajas.objects.filter(caja_cerrada=False).latest("id_caja")
    except Cajas.DoesNotExist:
        messages.error(request, "❌ No hay ninguna caja abierta. No se puede registrar la compra.")
        list(messages.get_messages(request))
        return redirect('home')

    if request.method == 'POST':
        form = ComprasForm(request.POST)
        formset = DetallesCompraFormSet(request.POST, instance=Compras())

        try:
            empleado_actual = Empleados.objects.get(user=request.user)
        except Empleados.DoesNotExist:
            messages.error(request, "❌ Tu usuario no está vinculado con un empleado.")
            return redirect('home')

        if form.is_valid() and formset.is_valid():
            from decimal import Decimal

            total_compra = Decimal('0.00')

            for detalle_form in formset:
                if detalle_form.cleaned_data.get("DELETE"):
                    continue

                insumo = detalle_form.cleaned_data.get("insumo")
                cantidad = detalle_form.cleaned_data.get("cantidad")
                precio_unitario = detalle_form.cleaned_data.get("precio_unitario")

                if not insumo:
                    continue

                if cantidad and precio_unitario:
                    cant = Decimal(str(cantidad))
                    pu = Decimal(str(precio_unitario))
                    total_compra += cant * pu

            if caja_abierta.saldo_sistema < total_compra:
                messages.error(
                    request,
                    f"❌ Saldo insuficiente en caja. Saldo actual: ${caja_abierta.saldo_sistema:.2f} — Total compra: ${total_compra:.2f}"
                )
                list(messages.get_messages(request))
                return redirect('compras_create')

            compra = form.save(commit=False)
            compra.empleado = empleado_actual 
            compra.total = total_compra
            compra.save()

            for detalle_form in formset:
                if detalle_form.cleaned_data.get("DELETE"):
                    continue

                insumo = detalle_form.cleaned_data.get("insumo")
                cantidad = detalle_form.cleaned_data.get("cantidad")
                precio_unitario = detalle_form.cleaned_data.get("precio_unitario")

                if not insumo or not cantidad or not precio_unitario:
                    continue

                detalle = detalle_form.save(commit=False)
                detalle.compra = compra
                detalle.save()

                from decimal import Decimal
                stock_actual = insumo.stock_actual or 0
                stock_actual_dec = Decimal(str(stock_actual))
                cantidad_dec = Decimal(str(cantidad))

                insumo.stock_actual = stock_actual_dec + cantidad_dec
                insumo.save()

                StockMovimientos.objects.create(
                    insumo=insumo,
                    tipo='entrada',
                    cantidad=cantidad_dec,
                    detalle=f"Compra #{compra.id_compra} - {compra.proveedor.nombre if compra.proveedor else ''}"
                )

            MovimientosCaja.objects.create(
                caja=caja_abierta,
                tipo=MovimientosCaja.Tipo.EGRESO,
                forma_pago=form.cleaned_data['forma_pago'],
                monto=total_compra,
                descripcion=f"Pago a {compra.proveedor.nombre} por Compra #{compra.id_compra}",
                origen=MovimientosCaja.Origen.COMPRA,
                referencia_id=compra.id_compra,
                creado_por=empleado_actual,
                saldo_resultante=caja_abierta.saldo_sistema - total_compra
            )

            messages.success(
                request,
                f"✅ Compra #{compra.id_compra} registrada correctamente.",
                extra_tags="compra"
            )
            list(messages.get_messages(request))
            return redirect('compras_list')

    else:
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

    storage = messages.get_messages(request)
    for _ in storage:
        pass

    query = request.GET.get("q", "").strip()

    lista_compras = Compras.objects.select_related("proveedor").order_by('-fecha')

    if query:
        lista_compras = lista_compras.filter(
            Q(id_compra__icontains=query) |
            Q(proveedor__nombre__icontains=query)
        )

    paginator = Paginator(lista_compras, 10)
    page_number = request.GET.get("page")
    compras = paginator.get_page(page_number)

    return render(request, 'tinta_negra_web/compras_list.html', {
        'compras': compras,
        'query': query,
    })


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
    insumo = get_object_or_404(Insumos, pk=pk)

    if request.method == 'POST':
        try:

            insumo.delete()
            messages.success(
                request,
                f"Insumo '{insumo.nombre}' eliminado correctamente."
            )
        except ProtectedError:
            insumo.is_active = False
            insumo.save()
            messages.warning(
                request,
                f"El insumo '{insumo.nombre}' tiene movimientos asociados, "
                "no se puede eliminar. Se marcó como INACTIVO."
            )

        list(messages.get_messages(request))
        return redirect('insumos_list')

    return redirect('insumos_list')




@login_required
def insumo_datos_ajax(request, pk):
    insumo = get_object_or_404(Insumos, id_insumo=pk)
    return JsonResponse({
        "id": insumo.id_insumo,
        "nombre": insumo.nombre,
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
    insumo.nombre = request.POST.get("nombre") or insumo.nombre
    insumo.descripcion = request.POST.get("descripcion") or insumo.descripcion
    insumo.unidad_medida = request.POST.get("unidad_medida") or insumo.unidad_medida
    insumo.stock_minimo = request.POST.get("stock_minimo") or insumo.stock_minimo

    precio = request.POST.get("precio_costo_unitario")
    if precio is not None and precio != "":
        insumo.precio_costo_unitario = precio

    prov_id = request.POST.get("proveedor")
    if prov_id:
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

def agregar_insumo_presupuesto(request, presupuesto_id):
    if request.method == "POST":
        presupuesto = get_object_or_404(Presupuestos, id_presupuesto=presupuesto_id)
        insumo = get_object_or_404(Insumos, id_insumo=request.POST["insumo_id"])
        cantidad_usada = Decimal(request.POST["cantidad_usada"])
        cantidad_real = cantidad_usada / Decimal(insumo.factor_conversion)
        subtotal = cantidad_real * insumo.precio_costo_unitario
        PresupuestosInsumos.objects.create(
            presupuesto=presupuesto,
            id_insumo=insumo,
            cantidad=cantidad_real,               
            precio_unitario=insumo.precio_costo_unitario,
        )
        presupuesto.subtotal = (presupuesto.subtotal or Decimal(0)) + subtotal
        if presupuesto.margen_ganancia:
            presupuesto.total_presupuesto = presupuesto.subtotal + (presupuesto.subtotal * presupuesto.margen_ganancia / 100)
        else:
            presupuesto.total_presupuesto = presupuesto.subtotal
        presupuesto.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@never_cache
@login_required
def cajas_list(request):

    caja_abierta = Cajas.objects.filter(caja_cerrada=False).order_by('-id_caja').first()

    lista_cajas = Cajas.objects.all().order_by('-id_caja')
    paginator = Paginator(lista_cajas, 15)
    page_number = request.GET.get("page")
    cajas = paginator.get_page(page_number)
    cierre_info = request.session.pop("cierre_info", None)

    return render(request, 'core/caja/cajas_list.html', {
        'caja_abierta': caja_abierta,
        'cajas': cajas,
        'cierre_info': cierre_info,
        'page_obj': cajas,
    })



@never_cache
@login_required
@transaction.atomic
@require_http_methods(["GET", "POST"])
def abrir_caja_view(request):

    ultima_caja = Cajas.objects.order_by('-id_caja').first()

    if ultima_caja and not ultima_caja.caja_cerrada:
        messages.warning(request, "La caja ya está abierta.")
        return redirect('cajas_list')
    saldo_inicial = ultima_caja.saldo_final if ultima_caja else 0

    if request.method == 'POST':
        caja = Cajas.objects.create(
            id_empleado=None,  # CAJA GENERAL
            saldo_inicial=saldo_inicial,
            saldo_final=saldo_inicial,
            fecha_hora_apertura=timezone.now(),
            diferencia=0,
            tolerancia=100,
            descripcion="Apertura automática (caja general)",
            caja_cerrada=False
        )

        messages.success(
            request,
            f"Caja general abierta con saldo inicial: ${saldo_inicial:,.2f}",
            extra_tags="caja"
        )

        return redirect('cajas_list')

    return render(request, 'core/caja/abrir_caja_modal.html', {
        "saldo_inicial": saldo_inicial
    })



@never_cache
@login_required
@permission_required('core.change_cajas', raise_exception=True)
@transaction.atomic
@require_http_methods(["GET", "POST"])
def cerrar_caja_view(request):

    caja = Cajas.objects.filter(caja_cerrada=False).order_by('-id_caja').first()

    if not caja:
        messages.warning(request, "No hay ninguna caja abierta.")
        return redirect('cajas_list')

    saldo_sistema = caja.saldo_sistema  # ✔ monto actual real
    if request.method == 'POST':

        caja.monto_fisico = saldo_sistema
        caja.saldo_final = saldo_sistema
        caja.diferencia = 0
        caja.fecha_hora_cierre = timezone.now()
        caja.caja_cerrada = True
        caja.save()

        request.session["cierre_info"] = {
            "saldo_inicial": f"{caja.saldo_inicial:,.2f}",
            "saldo_final": f"{caja.saldo_final:,.2f}",
            "diferencia": "0.00",
        }

        return redirect("cajas_list")

    return render(request, "core/caja/cerrar_caja_modal.html", {
        "saldo_sistema": saldo_sistema
    })






@never_cache
@login_required
def detalle_caja_view(request, id):
    caja = get_object_or_404(Cajas, id_caja=id)
    movimientos = MovimientosCaja.objects.filter(caja=caja).order_by('-fecha_hora')
    return render(request, 'core/caja/detalle_caja.html', {
        'caja': caja,
        'movimientos': movimientos,
    })
@login_required
def movimiento_create(request):

    if request.method == "GET":
        formas_pago = FormaPago.objects.filter(activo=True).order_by('nombre')

        return render(request, "core/caja/movimiento_form.html", {
            "formas_pago": formas_pago
        })

    # POST → guardar movimiento (igual que antes)
    caja = Cajas.objects.filter(caja_cerrada=False).first()
    if not caja:
        return JsonResponse({"error": "No hay una caja abierta para registrar movimientos"}, status=400)

    empleado = Empleados.objects.filter(user=request.user).first()
    if not empleado:
        return JsonResponse({"error": "Empleado no encontrado"}, status=400)

    tipo = request.POST.get("tipo")
    forma_pago_id = request.POST.get("forma_pago")
    descripcion = request.POST.get("descripcion", "").strip()

    if tipo not in ["INGRESO", "EGRESO"]:
        return JsonResponse({"error": "Tipo inválido"}, status=400)

    try:
        monto = Decimal(request.POST.get("monto").replace(",", "."))
        if monto <= 0:
            raise ValueError
    except:
        return JsonResponse({"error": "Monto inválido"}, status=400)

    try:
        forma_pago = FormaPago.objects.get(id_forma=forma_pago_id)
    except FormaPago.DoesNotExist:
        return JsonResponse({"error": "Forma de pago inválida"}, status=400)

    saldo_actual = caja.saldo_sistema  
    nuevo_saldo = saldo_actual + monto if tipo == "INGRESO" else saldo_actual - monto

    movimiento = MovimientosCaja.objects.create(
        caja=caja,
        fecha_hora=timezone.now(),
        tipo=tipo,
        forma_pago=forma_pago,
        monto=monto,
        descripcion=descripcion,
        origen=MovimientosCaja.Origen.MANUAL,
        creado_por=empleado,
        saldo_resultante=nuevo_saldo,
    )

    AuditoriaCaja.objects.create(
        caja=caja,
        movimiento=movimiento,
        usuario=request.user,
        accion=AuditoriaCaja.Accion.MOV_ALTA,
        detalle=f"Movimiento manual: {tipo} ${monto}",
        ip=request.META.get("REMOTE_ADDR"),
    )

    return redirect("movimientos_list")





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
            messages.success(request, "✅ Forma de pago agregada correctamente.", extra_tags="formapago")
        else:
            messages.error(request, "❌ Error al agregar la forma de pago.")
    list(messages.get_messages(request))
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



from django.core.mail import send_mail
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
            if not empleado.email:
                messages.error(request, 'Debe ingresar un email para crear el usuario del empleado.')
                return render(request, 'core/empleados/empleado_form.html', {
                    'form': form,
                    'title': 'Registrar Nuevo Empleado'
                })

            nombre_usuario = empleado.email 
            password_temporal = "tinta123"

            user = User.objects.create_user(
                username=nombre_usuario,
                email=empleado.email,
                first_name=empleado.nombre,
                last_name=empleado.apellido or "",
                password=password_temporal
            )

            grupo, _ = Group.objects.get_or_create(name="Jefe" if empleado.rol == "Jefe" else "Empleados")
            user.groups.add(grupo)

            empleado.user = user
            empleado.save()
            asunto = "Bienvenido a Tinta Negra - Acceso al Sistema"
            mensaje = f"""
Hola {empleado.nombre} {empleado.apellido},

Tu usuario en el sistema Tinta Negra ha sido creado.

Aquí están tus credenciales:

Usuario (email): {empleado.email}
Contraseña temporal: {password_temporal}

Por favor inicia sesión y cambia tu contraseña.

Equipo de Tinta Negra
"""

            try:
                send_mail(
                    asunto,
                    mensaje,
                    "roibarra9229@gmail.com",  
                    [empleado.email],
                    fail_silently=False,
                )
            except Exception as e:
                print("ERROR email:", e)
                messages.warning(request, "Empleado creado, pero NO se pudo enviar el correo.")

            messages.success(
                request,
                f'Empleado registrado correctamente. Se envió el usuario y la contraseña a {empleado.email}.'
            )
            list(messages.get_messages(request))
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
            messages.success(request, 'Empleado actualizado exitosamente.', extra_tags="empleado")
            list(messages.get_messages(request))
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
    messages.success(request, f"El empleado {empleado.nombre} {empleado.apellido} fue eliminado correctamente.", extra_tags="empleado")
    list(messages.get_messages(request))
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
    messages.success(request, f"Empleado {empleado.nombre} {empleado.apellido} reactivado correctamente.", extra_tags="empleado")
    list(messages.get_messages(request))
    return redirect('empleados_list')

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
    proveedor = get_object_or_404(Proveedores, id_proveedor=pk)

    compras = (
        Compras.objects.filter(proveedor=proveedor)
        .order_by('-fecha')
        .prefetch_related('detallescompra_set__insumo')
    )

    compras_info = []
    for compra in compras:
        detalles = compra.detallescompra_set.all()
        total_items = sum(
            (det.cantidad or 0) * (det.precio_unitario or 0)
            for det in detalles
        )

        compras_info.append({
            "compra": compra,
            "detalles": detalles,
            "total_items": total_items,
        })


    return render(request, 'core/proveedores/compras_proveedor.html', {
        'proveedor': proveedor,
        'compras_info': compras_info
    })



from django.core.paginator import Paginator
from django.db.models import Q

@never_cache
@login_required
@permission_required('core.view_pedidos', raise_exception=True)
def pedidos_list(request):

    pedidos_qs = Pedidos.objects.select_related("id_cliente", "id_estado").order_by('-id_pedido')

    q = request.GET.get("q", "").strip()
    if q:
        pedidos_qs = pedidos_qs.filter(
            Q(id_pedido__icontains=q) |
            Q(id_cliente__nombre__icontains=q) |
            Q(id_cliente__apellido__icontains=q)
        )

    if request.GET.get("produccion") == "1":
        pedidos_qs = pedidos_qs.filter(id_estado__nombre_estado__iexact="EN PRODUCCIÓN")

    paginator = Paginator(pedidos_qs, 15)
    page_number = request.GET.get("page")
    pedidos = paginator.get_page(page_number)

    return render(request, 'core/pedidos_list.html', {
        'pedidos': pedidos,
        'page_obj': pedidos,
        'q': q,
    })



@never_cache
@login_required
@permission_required('core.view_presupuestos', raise_exception=True)
def presupuestos_list(request):
    from decimal import Decimal
    from core.models import Productos

    q = request.GET.get("q", "").strip()
    presupuestos_qs = Presupuestos.objects.select_related("id_cliente").order_by("-id_presupuesto")

    if q:
        presupuestos_qs = presupuestos_qs.filter(
            Q(id_presupuesto__icontains=q) |
            Q(id_cliente__nombre__icontains=q) |
            Q(id_cliente__apellido__icontains=q)
        )

    paginator = Paginator(presupuestos_qs, 15)
    page_number = request.GET.get("page")
    presupuestos = paginator.get_page(page_number)

    for pre in presupuestos:

        costo_trabajos = sum([
            float(t.subtotal_insumos or 0)
            for t in pre.trabajos.all()
        ])

        costo_productos = 0

        for t in pre.trabajos.all():
            try:
                producto = Productos.objects.get(nombre=t.nombre_trabajo)

                if producto.tipo.nombre_tipo.lower() == "tercerizado":
                    costo_productos += float(producto.costo_inicial or 0) * int(t.cantidad)

            except Productos.DoesNotExist:
                pass
        costo_total_real = costo_trabajos + costo_productos
        pre.ganancia_real = round(
            float(pre.total_presupuesto or 0) - costo_total_real,
            2
        )

    return render(request, "core/presupuestos/presupuestos_list.html", {
        "presupuestos": presupuestos,
        "page_obj": presupuestos,
        "q": q,
    })


@login_required
def presupuesto_create(request):

    presupuesto = Presupuestos.objects.create(
        fecha_emision=timezone.now().date(),
        estado_presupuesto="Borrador",
        total_presupuesto=0
    )
    return redirect("presupuesto_edit", presupuesto.id_presupuesto)



@login_required
def configuracion(request):
    empleado = Empleados.objects.filter(user=request.user).first()
    if not empleado:
        messages.error(request, "No se encontró el perfil del empleado.")
        return redirect("home")

    empresa = ConfiguracionEmpresa.objects.first()
    if not empresa:
        empresa = ConfiguracionEmpresa.objects.create()
    else:
        empresa.refresh_from_db()

    return render(request, "core/configuracion.html", {
        "empleado": empleado,
        "empresa": empresa,
        "user_email": request.user.email,
    })


@login_required
@transaction.atomic
def convertir_presupuesto_a_pedido(request, pk):
    from core.models import (
        Productos, PedidosProductos,
        StockMovimientos, TrabajoInsumo, Trabajo
    )

    presupuesto = get_object_or_404(Presupuestos, id_presupuesto=pk)
    if not presupuesto.id_cliente:
        messages.error(request, "❌ No podés generar un pedido sin seleccionar un cliente.")
        return redirect("presupuesto_detalle", pk)

    pedido = Pedidos.objects.create(
        id_cliente=presupuesto.id_cliente,
        total_pedido=presupuesto.total_presupuesto,
    )

    estado_produccion = EstadosPedidos.objects.get(nombre_estado="EN PRODUCCIÓN")
    pedido.id_estado = estado_produccion
    pedido.stock_descontado = False
    pedido.save()

    trabajos = Trabajo.objects.filter(presupuesto=presupuesto)

    for trabajo in trabajos:

        producto_catalogo = None
        try:
            producto_catalogo = Productos.objects.get(nombre=trabajo.nombre_trabajo)
        except Productos.DoesNotExist:
            producto_catalogo = None

        if producto_catalogo:

            PedidosProductos.objects.create(
                pedido=pedido,
                producto=producto_catalogo,
                cantidad=trabajo.cantidad,
                precio_unitario=producto_catalogo.precio,
                subtotal=producto_catalogo.precio * trabajo.cantidad
            )

            if producto_catalogo.tipo.nombre_tipo.lower() == "tercerizado":
                stock_antes = float(producto_catalogo.stock_actual or 0)
                stock_nuevo = stock_antes - float(trabajo.cantidad)
                producto_catalogo.stock_actual = stock_nuevo
                producto_catalogo.save()

                StockMovimientos.objects.create(
                    producto=producto_catalogo,
                    tipo="salida",
                    cantidad=trabajo.cantidad,
                    detalle=f"Uso de producto en Pedido #{pedido.id_pedido}"
                )
        insumos_trabajo = TrabajoInsumo.objects.filter(trabajo=trabajo)

        for det in insumos_trabajo:

            PedidosInsumos.objects.create(
                pedido=pedido,
                insumo=det.insumo,
                cantidad=det.cantidad,
                precio_unitario=det.precio_unitario,
            )

            insumo = det.insumo
            factor = float(insumo.factor_conversion or 1)
            cantidad_real = float(det.cantidad) / factor
            stock_antes = float(insumo.stock_actual or 0)
            insumo.stock_actual = stock_antes - cantidad_real
            insumo.save()

            StockMovimientos.objects.create(
                insumo=insumo,
                tipo="salida",
                cantidad=cantidad_real,
                detalle=f"Uso de insumo por Pedido #{pedido.id_pedido}"
            )

    pedido.stock_descontado = True
    pedido.save()
    presupuesto.estado_presupuesto = "CONFIRMADO"
    presupuesto.save()

    messages.success(
        request,
        f"✅ Pedido #{pedido.id_pedido} generado y puesto en producción. Se descontó stock.",
        extra_tags="success"
    )

    return redirect("pedidos_list")





@login_required
def pedido_editar_insumos(request, pk):
    pedido = get_object_or_404(Pedidos, id_pedido=pk)
    DetalleFormSet = modelformset_factory(
        PedidosInsumos,
        fields=('cantidad',),
        extra=0
    )

    if request.method == "POST":
        formset = DetalleFormSet(request.POST, queryset=PedidosInsumos.objects.filter(pedido=pedido))
        if formset.is_valid():
            formset.save()
            messages.success(request, "Cantidades actualizadas. Lista para confirmar.", extra_tags="pedidosinsumos")
            list(messages.get_messages(request))
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
    for det in detalles:
        if det.insumo.stock_actual < det.cantidad:
            messages.error(
                request,
                f"No hay suficiente stock de {det.insumo.nombre}. Stock actual: {det.insumo.stock_actual}, necesario: {det.cantidad}"
            )
            return redirect('pedidos_list')
    for det in detalles:
        det.insumo.stock_actual -= det.cantidad
        det.insumo.save()
        StockMovimientos.objects.create(
            insumo=det.insumo,
            tipo='salida',
            cantidad=det.cantidad,
            detalle=f"Pedido #{pedido.id_pedido}"
        )

    pedido.id_estado = get_object_or_404(EstadosPedidos, pk=2)  
    pedido.save()

    messages.success(request, "Pedido confirmado ✅ Stock actualizado.", extra_tags="pedido")
    list(messages.get_messages(request))
    return redirect('pedidos_list')


@csrf_exempt 
def unidad_medida_create_ajax(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")

        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre vacío"})

        unidad, created = UnidadMedida.objects.get_or_create(nombre=nombre)

        return JsonResponse({
            "success": True,
            "id": unidad.id,
            "nombre": unidad.nombre
        })

    return JsonResponse({"success": False, "error": "Método inválido"})


    
from core.models import Presupuestos, Trabajo, TrabajoInsumo, ConfiguracionEmpresa

@login_required
def presupuesto_detalle(request, pk):
    from core.models import Productos

    presupuesto = get_object_or_404(Presupuestos, id_presupuesto=pk)
    trabajos = Trabajo.objects.filter(presupuesto=presupuesto).prefetch_related("insumos__insumo")
    config = ConfiguracionEmpresa.objects.first()
    subtotal_general = sum(t.total_trabajo for t in trabajos)
    total_general = subtotal_general
    costo_real_insumos = 0
    costo_real_tercerizados = 0

    for t in trabajos:

        costo_real_insumos += float(t.subtotal_insumos or 0)
        try:
            producto = Productos.objects.get(nombre=t.nombre_trabajo)

            if producto.tipo.nombre_tipo.lower() == "tercerizado":
                costo_real_tercerizados += float(producto.costo_inicial or 0) * int(t.cantidad)

        except Productos.DoesNotExist:
            pass

    costo_real_total = costo_real_insumos + costo_real_tercerizados
    ganancia_real = float(total_general) - costo_real_total

    return render(request, "core/presupuestos/presupuesto_detalle.html", {
        "presupuesto": presupuesto,
        "trabajos": trabajos,
        "config": config,
        "subtotal_general": subtotal_general,
        "total_general": total_general,
        "costo_real": costo_real_total,
        "ganancia_real": ganancia_real,
        "costo_real_insumos": costo_real_insumos,
        "costo_real_tercerizados": costo_real_tercerizados,
    })



def eliminar_insumo_presupuesto(request, detalle_id):
    detalle = PresupuestosInsumos.objects.get(id_detalle=detalle_id)
    presupuesto = detalle.presupuesto
    subtotal_restar = detalle.cantidad * detalle.precio_unitario
    presupuesto.subtotal = (presupuesto.subtotal or Decimal(0)) - subtotal_restar
    if presupuesto.margen_ganancia:
        presupuesto.total_presupuesto = presupuesto.subtotal + (presupuesto.subtotal * presupuesto.margen_ganancia / 100)
    else:
        presupuesto.total_presupuesto = presupuesto.subtotal
    presupuesto.save()
    detalle.delete()

    return JsonResponse({"success": True})

def editar_insumo_presupuesto(request, detalle_id):
    if request.method == "POST":
        detalle = PresupuestosInsumos.objects.get(id_detalle=detalle_id)
        presupuesto = detalle.presupuesto
        cantidad_usada = Decimal(request.POST["cantidad_usada"])
        insumo = detalle.id_insumo
        nueva_cantidad_real = cantidad_usada / Decimal(insumo.factor_conversion)
        subtotal_anterior = detalle.cantidad * detalle.precio_unitario
        presupuesto.subtotal -= subtotal_anterior
        detalle.cantidad = nueva_cantidad_real
        detalle.save()
        nuevo_subtotal = nueva_cantidad_real * detalle.precio_unitario
        presupuesto.subtotal += nuevo_subtotal
        if presupuesto.margen_ganancia:
            presupuesto.total_presupuesto = presupuesto.subtotal + (presupuesto.subtotal * presupuesto.margen_ganancia / 100)
        else:
            presupuesto.total_presupuesto = presupuesto.subtotal
        presupuesto.save()
        return JsonResponse({"success": True})


@login_required
def movimientos_stock_list(request):
    movimientos = StockMovimientos.objects.all().order_by('-fecha_hora')[:200]

    return render(request, 'core/stock/movimientos_stock_list.html', {
        'movimientos': movimientos
    })


@login_required
def producto_insumos(request, pk):
    producto = get_object_or_404(Productos, id_producto=pk)

    if producto.tipo.nombre.lower() != "fabricado":
        messages.error(request, "Este producto no admite insumos.")
        return redirect("productos_list")

    ProductoInsumoFormSet = modelformset_factory(
        ProductosInsumos, form=ProductoInsumoForm, extra=1, can_delete=True
    )

    formset = ProductoInsumoFormSet(
        request.POST or None,
        queryset=ProductosInsumos.objects.filter(producto=producto)
    )

    if request.method == "POST" and formset.is_valid():
        instances = formset.save(commit=False)

        for form in formset.deleted_objects:
            form.delete()

        for instance in instances:
            instance.producto = producto
            instance.save()

        messages.success(request, "Insumos actualizados correctamente.", extra_tags="insumo")
        list(messages.get_messages(request))
        return redirect("producto_insumos", pk=producto.id_producto)

    return render(request, "productos/producto_insumos.html", {
        "producto": producto,
        "formset": formset,
    })


@login_required
def cliente_create_ajax(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        dni = request.POST.get("dni")
        email = request.POST.get("email")
        telefono = request.POST.get("telefono")
        direccion = request.POST.get("direccion")

        if Cliente.objects.filter(email=email).exists():
            return JsonResponse({
                "success": False,
                "message": "⚠️ Ya existe un cliente con ese email."
            }, status=400)
        if Cliente.objects.filter(dni=dni).exists():
            return JsonResponse({
                "success": False,
                "message": "⚠️ Ya existe un cliente con ese DNI."
            }, status=400)
        cliente = Cliente.objects.create(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            email=email,
            telefono=telefono,
            direccion=direccion
        )

        return JsonResponse({
            "success": True,
            "id": cliente.id_cliente,
            "nombre_completo": f"{cliente.nombre} {cliente.apellido}"
        })

    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)


from core.models import Insumos
@csrf_exempt
def generar_pdf_presupuesto(request, pk):
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from xhtml2pdf import pisa

    presupuesto = Presupuestos.objects.get(id_presupuesto=pk)
    trabajos = presupuesto.trabajos.all()
    config = ConfiguracionEmpresa.objects.first()
    nombre_empresa = request.POST.get("nombre_empresa", config.nombre_empresa)
    direccion = request.POST.get("direccion", config.direccion)
    email = request.POST.get("email", config.email)
    telefono = request.POST.get("telefono", config.telefono)
    condiciones_pago = request.POST.get("condiciones_pago", config.condiciones_pago)
    otros_detalles = request.POST.get("otros_detalles", "")

    total_general = sum([t.total_trabajo for t in trabajos])

    # Logo
    logo_path = ""
    if config.logo:
        logo_path = config.logo.path

    html = render_to_string("core/presupuestos/presupuesto_pdf_template.html", {
        "presupuesto": presupuesto,
        "trabajos": trabajos,
        "total_general": total_general,
        "config": config,
        "nombre_empresa": nombre_empresa,
        "direccion": direccion,
        "email": email,
        "telefono": telefono,
        "condiciones_pago": condiciones_pago,
        "otros_detalles": otros_detalles,
        "logo_path": logo_path,
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="presupuesto_{pk}.pdf"'
    pisa.CreatePDF(html, dest=response)

    return response


@login_required
@require_POST
def presupuesto_confirmar(request, pk):
    presupuesto = get_object_or_404(Presupuestos, id_presupuesto=pk)

    if not presupuesto.id_cliente:
        messages.error(request, "Debes seleccionar un cliente antes de confirmar el presupuesto.")
        return redirect("presupuesto_edit", presupuesto.id_presupuesto)

    trabajos_qs = presupuesto.trabajos.all()
    if not trabajos_qs.exists():
        messages.error(request, "Debes agregar al menos un trabajo antes de confirmar el presupuesto.")
        return redirect("presupuesto_edit", presupuesto.id_presupuesto)

    total = trabajos_qs.aggregate(s=Sum("total_trabajo"))["s"] or 0
    presupuesto.total_presupuesto = total
    presupuesto.estado_presupuesto = "EN ESPERA"
    presupuesto.save()

    messages.success(request, "Presupuesto confirmado correctamente.")
    return redirect("presupuesto_detalle", presupuesto.id_presupuesto)

@login_required
def presupuesto_edit(request, presupuesto_id):

    presupuesto = get_object_or_404(Presupuestos, id_presupuesto=presupuesto_id)
    trabajos = presupuesto.trabajos.all()

    insumos = Insumos.objects.filter(is_active=True).order_by("nombre")
    productos = Productos.objects.select_related("tipo").order_by("nombre")

    if request.method == "POST":
        form = PresupuestoForm(request.POST, instance=presupuesto)

        if form.is_valid():
            presupuesto = form.save(commit=False)

            subtotal = trabajos.aggregate(total=Sum("total_trabajo"))["total"] or 0
            presupuesto.subtotal = subtotal

            total = subtotal

            if presupuesto.costo_diseno:
                total += presupuesto.costo_diseno

            if presupuesto.margen_ganancia:
                total = total * (1 + (presupuesto.margen_ganancia / 100))

            presupuesto.total_presupuesto = total
            presupuesto.save()

            messages.success(request, "Presupuesto actualizado exitosamente.")
            list(messages.get_messages(request))
            return redirect("presupuesto_detalle", presupuesto.id_presupuesto)

        else:
            messages.error(request, "Error al actualizar el presupuesto.")
            list(messages.get_messages(request))

    else:
        form = PresupuestoForm(instance=presupuesto)

    return render(request, "core/presupuestos/presupuesto_form.html", {
        "form": form,
        "presupuesto": presupuesto,
        "trabajos": trabajos,
        "insumos": insumos,
        "productos": productos,
        "title": f"Editar presupuesto #{presupuesto.id_presupuesto}",
    })



from django.urls import reverse
@login_required
def configuracion_empresa(request):
    empresa = ConfiguracionEmpresa.objects.first()
    if not empresa:
        empresa = ConfiguracionEmpresa.objects.create()

    if request.method == "POST":
        empresa.nombre_empresa = request.POST.get("nombre_empresa")
        empresa.direccion = request.POST.get("direccion")
        empresa.telefono = request.POST.get("telefono")
        empresa.email = request.POST.get("email")
        empresa.condiciones_pago = request.POST.get("condiciones_pago")
        empresa.otros_detalles = request.POST.get("otros_detalles")

        if request.FILES.get("logo"):
            empresa.logo = request.FILES["logo"]

        empresa.save()

        messages.success(request, "Datos de empresa guardados correctamente.")

        url = reverse("configuracion") + "?tab=empresa"
        return redirect(url)
    return redirect("configuracion")




@login_required
def presupuesto_previa_pdf(request, pk):
    presupuesto = Presupuestos.objects.get(pk=pk)
    detalle = PresupuestosInsumos.objects.filter(presupuesto=presupuesto)
    config = ConfiguracionEmpresa.objects.first()

    if request.method == "POST":
        config.nombre_empresa = request.POST.get("nombre_empresa")
        config.direccion = request.POST.get("direccion")
        config.telefono = request.POST.get("telefono")
        config.email = request.POST.get("email")
        config.condiciones_pago = request.POST.get("condiciones_pago")
        config.otros_detalles = request.POST.get("otros_detalles")
        config.save()

        return redirect("generar_pdf_presupuesto", pk=pk)

    return render(request, "core/presupuestos/previa_pdf.html", {
        "presupuesto": presupuesto,
        "detalle": detalle,
        "config": config,
    })


@login_required
def preview_pdf_presupuesto(request, pk):
    presupuesto = get_object_or_404(Presupuestos, pk=pk)
    trabajos = presupuesto.trabajos.all()
    total_general = trabajos.aggregate(total=Sum("total_trabajo"))["total"] or 0
    config = ConfiguracionEmpresa.objects.first()
    return render(request, "core/presupuestos/presupuesto_pdf_template.html", {
        "presupuesto": presupuesto,
        "trabajos": trabajos,
        "total_general": total_general,
        "config": config,
        "preview": True,  
    })


@login_required
def configuracion_email(request):
    config = ConfiguracionEmail.objects.first()

    if not config:
        config = ConfiguracionEmail.objects.create()

    if request.method == "POST":
        form = ConfiguracionEmailForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración de Email guardada ✅")
            return redirect("configuracion_email")
    else:
        form = ConfiguracionEmailForm(instance=config)

    return render(request, "core/configuracion_email.html", {"form": form})




@login_required
def presupuesto_enviar_email(request, pk):
    config = ConfiguracionEmail.objects.first()
    presupuesto = Presupuestos.objects.get(pk=pk)
    pdf_bytes = request.session.get("pdf_presupuesto").encode("latin1")
    email_to = request.POST.get("email_to", presupuesto.id_cliente.email)
    mensaje = request.POST.get("mensaje")
    email = EmailMessage(
        subject=f"Presupuesto #{presupuesto.id_presupuesto}",
        body=mensaje,
        from_email=config.email_remitente,
        to=[email_to],
    )

    email.attach(f"Presupuesto_{pk}.pdf", pdf_bytes, "application/pdf")
    email.send()
    messages.success(request, "✅ Presupuesto enviado por email correctamente.")
    list(messages.get_messages(request))
    return redirect("presupuesto_detalle", pk=pk)



@login_required
def presupuesto_email_preview(request, pk):
    presupuesto = Presupuestos.objects.get(pk=pk)
    detalle = PresupuestosInsumos.objects.filter(presupuesto=presupuesto)
    config = ConfiguracionEmpresa.objects.first()
    response_pdf = generar_pdf_presupuesto(request, pk)
    pdf_bytes = response_pdf.content
    request.session["pdf_presupuesto"] = pdf_bytes.decode("latin1")
    mensaje_predefinido = f"""
Hola {presupuesto.id_cliente.nombre} {presupuesto.id_cliente.apellido},
Te envío el presupuesto solicitado.
Monto total: ${presupuesto.total_presupuesto}
Quedo atenta a tus comentarios.
Saludos!

Emilia Lopez
{config.nombre_empresa if config and config.nombre_empresa else "Tinta Negra"}
""".strip()

    return render(request, "core/presupuestos/email_preview.html", {
        "presupuesto": presupuesto,
        "detalle": detalle,
        "config": config,
        "mensaje_predefinido": mensaje_predefinido
    })


@login_required
def agregar_trabajo_presupuesto(request, presupuesto_id):
    presupuesto = Presupuestos.objects.get(pk=presupuesto_id)

    if request.method == "POST":
        trabajo = request.POST["trabajo"]
        cantidad = int(request.POST["cantidad"])
        precio_unitario = float(request.POST["precio_unitario"])
        subtotal = cantidad * precio_unitario
        editar_id = request.POST.get("editar_id")
        if editar_id:
            Trabajo.objects.get(pk=editar_id).delete()
        PresupuestosProductos.objects.create(
            presupuesto=presupuesto,
            trabajo=trabajo,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
        )
        presupuesto.total_presupuesto += subtotal
        presupuesto.save()

        return redirect("presupuesto_detalle", presupuesto_id)

    return render(request, "core/presupuestos/agregar_trabajo.html", {
        "presupuesto": presupuesto,
    })


@login_required
def guardar_trabajo(request, pk):
    presupuesto = get_object_or_404(Presupuestos, pk=pk)
    if request.method == "POST":
        nombre = request.POST.get("nombre_trabajo")
        cantidad = int(request.POST.get("cantidad_trabajo", 1))
        subtotal = float(request.POST.get("subtotal_trabajo", 0))
        if not nombre:
            messages.error(request, "Debe ingresar un nombre para el trabajo.")
            return redirect("presupuesto_edit", pk)
        presupuesto.subtotal += subtotal * cantidad
        presupuesto.total_presupuesto = presupuesto.subtotal + float(presupuesto.costo_diseno or 0)
        presupuesto.save()

        messages.success(request, "Trabajo agregado ✅")
        list(messages.get_messages(request))
        return redirect("presupuesto_edit", pk)
    

@require_POST
@login_required
def crear_presupuesto_borrador(request):
    cliente_id = request.POST.get("cliente_id")
    cliente = Cliente.objects.filter(pk=cliente_id).first()

    if not cliente:
        return JsonResponse({"ok": False, "error": "Cliente no encontrado"})

    fecha_emision = request.POST.get("fecha_emision") or timezone.now().date()
    fecha_vencimiento = request.POST.get("fecha_vencimiento") or None
    costo_diseno = request.POST.get("costo_diseno") or 0
    margen_ganancia = request.POST.get("margen_ganancia") or 0

    presupuesto = Presupuestos.objects.create(
        id_cliente=cliente,
        fecha_emision=fecha_emision,
        fecha_vencimiento=fecha_vencimiento,
        costo_diseno=costo_diseno,
        margen_ganancia=margen_ganancia,
        subtotal=0,
        total_presupuesto=0,
        estado_presupuesto="EN ESPERA"
    )

    return JsonResponse({"ok": True, "presupuesto_id": presupuesto.id_presupuesto})


@login_required
@require_POST
@transaction.atomic
def agregar_trabajo(request, presupuesto_id):

    from decimal import Decimal

    if not presupuesto_id or presupuesto_id == "0":
        nuevo = Presupuestos.objects.create(
            fecha_emision=timezone.now().date(),
            estado_presupuesto="EN ESPERA",  # 🔹 CAMBIADO: coincide con tu modelo
            subtotal=Decimal("0.00"),
            total_presupuesto=Decimal("0.00"),
        )
        presupuesto = nuevo
        presupuesto_id = nuevo.id_presupuesto
    else:
        try:
            presupuesto = Presupuestos.objects.get(id_presupuesto=presupuesto_id)
        except Presupuestos.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Presupuesto no encontrado."}, status=404)

    # Debe haber cliente antes de agregar trabajos
    if not presupuesto.id_cliente:
        return JsonResponse({
            "ok": False,
            "error": "Debe seleccionar un cliente antes de agregar trabajos."
        })

    nombre = (request.POST.get("nombre_trabajo") or "").strip()
    descripcion = request.POST.get("descripcion_trabajo") or ""

    try:
        cantidad = int(request.POST.get("cantidad_trabajo") or 1)
    except ValueError:
        cantidad = 1

    if cantidad < 1:
        return JsonResponse({"ok": False, "error": "La cantidad debe ser mayor o igual a 1."})

    try:
        costo_diseno = Decimal(request.POST.get("costo_diseno_trabajo") or "0")
    except Exception:
        costo_diseno = Decimal("0")

    if costo_diseno < 0:
        return JsonResponse({"ok": False, "error": "El costo de diseño no puede ser negativo."})

    try:
        margen = Decimal(request.POST.get("margen_trabajo") or "0")
    except Exception:
        margen = Decimal("0")

    if margen < 0:
        return JsonResponse({"ok": False, "error": "El margen no puede ser negativo."})

    if not nombre:
        return JsonResponse({"ok": False, "error": "Debe ingresar un nombre para el trabajo."})

    insumos_json = request.POST.get("insumos_json", "[]")

    try:
        lista_insumos = json.loads(insumos_json)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Error al leer los insumos enviados."})

    if not lista_insumos:
        return JsonResponse({"ok": False, "error": "Debe agregar al menos un insumo."})

    for item in lista_insumos:
        id_insumo = item.get("id_insumo")
        if not id_insumo:
            continue

        try:
            insumo = Insumos.objects.get(id_insumo=id_insumo, is_active=True)
        except Insumos.DoesNotExist:
            return JsonResponse({
                "ok": False,
                "error": "Uno de los insumos no existe o está dado de baja."
            })

        try:
            cant = Decimal(str(item.get("cantidad") or "1"))
        except:
            cant = Decimal("1")
        if cant < 1:
            return JsonResponse({"ok": False, "error": "Las cantidades de insumos deben ser ≥ 1."})
        if cant > insumo.stock_actual:
            return JsonResponse({
                "ok": False,
                "error": f"No hay stock suficiente de '{insumo.nombre}'. Disponible: {insumo.stock_actual}"
            })

    editar_id = request.POST.get("editar_trabajo_id")
    if editar_id:
        try:
            Trabajo.objects.get(pk=editar_id, presupuesto=presupuesto).delete()
        except Trabajo.DoesNotExist:
            pass

    trabajo = Trabajo.objects.create(
        presupuesto=presupuesto,
        nombre_trabajo=nombre,
        descripcion=descripcion,
        cantidad=cantidad,
        costo_diseno=costo_diseno,
        margen_ganancia=margen,
        subtotal_insumos=Decimal("0.00"),
        precio_unitario=Decimal("0.00"),
        total_trabajo=Decimal("0.00"),
    )

    subtotal_insumos = Decimal("0.00")

    # Creo TrabajoInsumo para cada insumo
    for item in lista_insumos:
        id_insumo = item.get("id_insumo")
        if not id_insumo:
            continue

        insumo = Insumos.objects.get(id_insumo=id_insumo)

        try:
            cant = Decimal(str(item.get("cantidad") or "1"))
        except:
            cant = Decimal("1")

        try:
            precio_unit = Decimal(str(item.get("costo_unitario") or "0"))
        except:
            precio_unit = Decimal("0")

        subtotal = precio_unit * cant

        TrabajoInsumo.objects.create(
            trabajo=trabajo,
            insumo=insumo,
            cantidad=cant,
            precio_unitario=precio_unit,
            subtotal=subtotal,
        )

        subtotal_insumos += subtotal

    costo_bruto = subtotal_insumos + costo_diseno
    precio_unitario = costo_bruto * (Decimal("1.00") + (margen / Decimal("100")))
    total_trabajo = precio_unitario * cantidad

    trabajo.subtotal_insumos = subtotal_insumos
    trabajo.precio_unitario = precio_unitario
    trabajo.total_trabajo = total_trabajo
    trabajo.save()

    # Recalcular total del presupuesto
    presupuesto.total_presupuesto = (
        presupuesto.trabajos.aggregate(s=Sum("total_trabajo"))["s"] or Decimal("0.00")
    )
    presupuesto.save()

    tabla_html = render_to_string(
        "core/presupuestos/_tabla_trabajos.html",
        {"presupuesto": presupuesto},
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "tabla": tabla_html,
            "total": f"{presupuesto.total_presupuesto:.2f}",
            "presupuesto_id": presupuesto.id_presupuesto,
        }
    )



@login_required
def listar_trabajos(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuestos, pk=presupuesto_id)
    html = render_to_string("core/presupuestos/_tabla_trabajos.html", {"presupuesto": presupuesto})
    return JsonResponse({"ok": True, "tabla": html})


@require_POST
def eliminar_trabajo(request, trabajo_id):
    try:
        trabajo = Trabajo.objects.select_related("presupuesto").get(id=trabajo_id)
    except Trabajo.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Trabajo no encontrado."}, status=404)

    presupuesto = trabajo.presupuesto
    trabajo.delete()

    from decimal import Decimal
    total_presupuesto = (
        presupuesto.trabajos.aggregate(s=Sum("total_trabajo"))["s"] or Decimal("0.00")
    )
    presupuesto.total_presupuesto = total_presupuesto
    presupuesto.save()

    tabla_html = render_to_string(
        "core/presupuestos/_tabla_trabajos.html",
        {"presupuesto": presupuesto},
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "tabla": tabla_html,
            "total": f"{total_presupuesto:.2f}",
        }
    )



@login_required
def obtener_trabajo(request, trabajo_id):
    trabajo = get_object_or_404(Trabajo, pk=trabajo_id)

    insumos = []
    for ti in trabajo.insumos.all():
        insumos.append({
            "id_insumo": ti.insumo.id_insumo,
            "nombre": ti.insumo.nombre,
            "cantidad": float(ti.cantidad),
            "precio_unitario": float(ti.precio_unitario),
            "subtotal": float(ti.subtotal),
        })

    return JsonResponse({
        "ok": True,
        "trabajo": {
            "id": trabajo.id,
            "nombre_trabajo": trabajo.nombre_trabajo,
            "descripcion": trabajo.descripcion or "",
            "cantidad": float(trabajo.cantidad),
            "costo_diseno": float(trabajo.costo_diseno),
            "margen": float(trabajo.margen_ganancia),
            "insumos": insumos,
        }
    })



@require_POST
def duplicar_trabajo(request, trabajo_id):
    try:
        trabajo = Trabajo.objects.select_related("presupuesto").get(id=trabajo_id)
    except Trabajo.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Trabajo no encontrado."}, status=404)

    presupuesto = trabajo.presupuesto
    nuevo_trabajo = Trabajo.objects.create(
        presupuesto=presupuesto,
        nombre_trabajo=f"{trabajo.nombre_trabajo} (copia)",
        descripcion=trabajo.descripcion,
        cantidad=trabajo.cantidad,
        costo_diseno=trabajo.costo_diseno,
        margen_ganancia=trabajo.margen_ganancia,
        subtotal_insumos=trabajo.subtotal_insumos,
        precio_unitario=trabajo.precio_unitario,
        total_trabajo=trabajo.total_trabajo,
    )

    for ti in trabajo.insumos.filter(insumo__is_active=True):
        TrabajoInsumo.objects.create(
            trabajo=nuevo_trabajo,
            insumo=ti.insumo,
            cantidad=ti.cantidad,
            precio_unitario=ti.precio_unitario,
            subtotal=ti.subtotal,
        )

    from decimal import Decimal
    total_presupuesto = (
        presupuesto.trabajos.aggregate(s=Sum("total_trabajo"))["s"] or Decimal("0.00")
    )
    presupuesto.total_presupuesto = total_presupuesto
    presupuesto.save()

    tabla_html = render_to_string(
        "core/presupuestos/_tabla_trabajos.html",
        {"presupuesto": presupuesto},
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "tabla": tabla_html,
            "total": f"{total_presupuesto:.2f}",
        }
    )



@login_required
def obtener_producto(request, producto_id):
    from core.models import Productos

    producto = Productos.objects.filter(pk=producto_id).first()
    if not producto:
        return JsonResponse({"ok": False, "error": "Producto no encontrado"})

    return JsonResponse({
        "ok": True,
        "id": producto.id_producto,
        "nombre": producto.nombre,
        "precio": float(producto.precio or 0),
        "descripcion": producto.descripcion or ""
    })


@login_required
def presupuesto_aprobar(request, id):
    presupuesto = get_object_or_404(Presupuestos, id_presupuesto=id)

    presupuesto.estado_presupuesto = "CONFIRMADO"
    presupuesto.save()

    return redirect("presupuesto_detalle", presupuesto.id_presupuesto)



from django.core.paginator import Paginator

@never_cache
@login_required
def productos_list(request):
    query = request.GET.get("q", "")

    productos = Productos.objects.all().order_by("id_producto")

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )
    paginator = Paginator(productos, 15)
    page = request.GET.get("page")
    productos_page = paginator.get_page(page)

    return render(request, "core/productos/productos_list.html", {
        "productos": productos_page,
        "query": query,
    })



@never_cache
@login_required
@permission_required('core.add_productos', raise_exception=True)
def producto_create(request):
    insumos = Insumos.objects.all()

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        tipo_str = request.POST.get("tipo")
        precio = Decimal(request.POST.get("precio", "0"))
        costo_diseno = Decimal(request.POST.get("costo_diseno", "0"))
        margen_ganancia = Decimal(request.POST.get("margen_ganancia", "0"))

        tipo_obj = TiposProducto.objects.filter(nombre_tipo__iexact=tipo_str).first()
        if not tipo_obj:
            messages.error(request, "Tipo de producto no válido.")
            return redirect("producto_create")

        producto = Productos.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            tipo=tipo_obj,
            costo_diseno=costo_diseno,
            margen_ganancia=margen_ganancia
        )

        if tipo_str.lower() == "personalizado":
            insumos_ids = request.POST.getlist("insumo[]")
            cantidades = request.POST.getlist("cantidad[]")

            for insumo_id, cant in zip(insumos_ids, cantidades):
                if insumo_id:
                    ProductosInsumos.objects.create(
                        producto=producto,
                        insumo=Insumos.objects.get(id_insumo=insumo_id),
                        cantidad=cant
                    )

        messages.success(request, "Producto creado correctamente")
        return redirect("productos_list")

    return render(request, "core/productos/producto_form.html", {
        "title": "Nuevo Producto",
        "insumos": insumos,
        "producto": None,
        "producto_insumos": None,
        "tipo_actual": None,
    })



@never_cache
@login_required
@permission_required('core.change_productos', raise_exception=True)
def producto_edit(request, pk):
    producto = Productos.objects.get(pk=pk)
    insumos = Insumos.objects.all().order_by('nombre')
    tipo_actual = producto.tipo.nombre_tipo.lower() if producto.tipo else "personalizado"

    if request.method == "POST":

        producto.nombre = request.POST.get("nombre")
        producto.descripcion = request.POST.get("descripcion")
        tipo_valor = request.POST.get("tipo")  # "personalizado" o "tercerizado"
        tipo = TiposProducto.objects.filter(nombre_tipo__iexact=tipo_valor).first()

        if not tipo:
            messages.error(request, "Debe seleccionar un tipo de producto válido.")
            return redirect("producto_edit", pk=pk)

        producto.tipo = tipo

        if tipo_valor == "personalizado":
            producto.costo_diseno = Decimal(request.POST.get("costo_diseno", "0"))
            producto.margen_ganancia = Decimal(request.POST.get("margen_ganancia", "0"))
            producto.precio = Decimal(request.POST.get("precio", "0"))

            producto.save()
            insumo_ids = request.POST.getlist("insumo[]")
            cantidades = request.POST.getlist("cantidad[]")

            ProductosInsumos.objects.filter(producto=producto).delete()

            for insumo_id, cant in zip(insumo_ids, cantidades):
                if insumo_id:
                    ProductosInsumos.objects.create(
                        producto=producto,
                        insumo=Insumos.objects.get(id_insumo=insumo_id),
                        cantidad=cant
                    )

        else:
            producto.costo_inicial = Decimal(request.POST.get("costo_inicial", "0"))
            producto.margen_ganancia = Decimal(request.POST.get("margen_ganancia", "0"))
            producto.precio = Decimal(request.POST.get("precio", "0"))
            producto.stock_actual = Decimal(request.POST.get("stock_actual", "0"))
            producto.stock_minimo = Decimal(request.POST.get("stock_minimo", "0"))

            producto.costo_diseno = 0
            producto.save()

            ProductosInsumos.objects.filter(producto=producto).delete()

        messages.success(request, f"Producto '{producto.nombre}' actualizado correctamente.")
        return redirect("productos_list")

    producto_insumos = ProductosInsumos.objects.filter(producto=producto)

    return render(request, "core/productos/producto_form.html", {
        "title": f"Editar Producto: {producto.nombre}",
        "producto": producto,
        "insumos": insumos,
        "producto_insumos": producto_insumos,
        "tipo_actual": tipo_actual,
    })



@never_cache
@login_required
@permission_required('core.view_productos', raise_exception=True)
def producto_detalle(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    insumos = ProductosInsumos.objects.filter(producto=producto).select_related("insumo")

    return render(request, "core/productos/producto_detalle.html", {
        "producto": producto,
        "insumos": insumos,
    })


def producto_delete(request, id_producto):
    producto = get_object_or_404(Productos, id_producto=id_producto)

    if request.method == "POST":
        try:
            ProductosInsumos.objects.filter(producto=producto).delete()

            producto.delete()
            messages.success(request, "Producto eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"No se pudo eliminar el producto: {e}")

        return redirect("productos_list")

    messages.error(request, "Acción no permitida.")
    return redirect("productos_list")


@login_required
@require_POST
@transaction.atomic
def agregar_producto_presupuesto(request, presupuesto_id):

    from decimal import Decimal
    from core.models import Productos, ProductosInsumos, Trabajo, TrabajoInsumo

    if not presupuesto_id or presupuesto_id == "0":
        nuevo = Presupuestos.objects.create(
            fecha_emision=timezone.now().date(),
            estado="Borrador",
            total_presupuesto=Decimal("0.00"),
            subtotal=Decimal("0.00")
        )
        presupuesto = nuevo
        presupuesto_id = nuevo.id_presupuesto
    else:
        presupuesto = get_object_or_404(Presupuestos, pk=presupuesto_id)

    if not presupuesto.id_cliente:
        return JsonResponse({
            "ok": False,
            "error": "Debe seleccionar un cliente antes de agregar productos."
        })


    producto_id = request.POST.get("id_producto")
    cantidad = int(request.POST.get("cantidad", 1))

    producto = get_object_or_404(Productos, pk=producto_id)

    trabajo = Trabajo.objects.create(
        presupuesto=presupuesto,
        nombre_trabajo=producto.nombre,
        descripcion=producto.descripcion or "",
        cantidad=cantidad,
        costo_diseno=0,          
        margen_ganancia=0,
    )

    tipo_producto = producto.tipo.nombre_tipo.strip().lower()

    subtotal_insumos = 0
    subtotal_costo_real = 0
    total_venta = float(producto.precio) * cantidad

    if tipo_producto == "personalizado":
        insumos_producto = ProductosInsumos.objects.filter(producto=producto)

        for pi in insumos_producto:
            cant_insumo = float(pi.cantidad)
            precio_unit_insumo = float(pi.insumo.precio_costo_unitario) / float(pi.insumo.factor_conversion or 1)
            subtotal = precio_unit_insumo * cant_insumo

            subtotal_insumos += subtotal
            subtotal_costo_real += subtotal

            TrabajoInsumo.objects.create(
                trabajo=trabajo,
                insumo=pi.insumo,
                cantidad=cant_insumo,
                precio_unitario=precio_unit_insumo,
                subtotal=subtotal,
            )
    else:
        costo_real = float(producto.costo_inicial or 0)
        subtotal_costo_real = costo_real * cantidad
        subtotal_insumos = 0

    trabajo.subtotal_insumos = round(subtotal_insumos, 2)
    trabajo.precio_unitario = round(float(producto.precio), 2)
    trabajo.total_trabajo = round(total_venta, 2)
    trabajo.save()

    tot = presupuesto.trabajos.aggregate(s=Sum("total_trabajo"))["s"] or 0
    presupuesto.subtotal = tot
    presupuesto.total_presupuesto = tot
    presupuesto.save()

    html = render_to_string(
        "core/presupuestos/_tabla_trabajos.html",
        {"presupuesto": presupuesto}
    )

    return JsonResponse({
        "ok": True,
        "tabla": html,
        "total": f"{tot:.2f}",
        "presupuesto_id": presupuesto.id_presupuesto  
    })






def api_grafico_ventas(request):

    ESTADO_VENTA = 3

    def safe_label(periodo, formato):
        if periodo is None:
            return "N/D"
        return periodo.strftime(formato)

    mes = request.GET.get("mes")
    if mes:
        try:
            año, mes_num = mes.split("-")
            año = int(año)
            mes_num = int(mes_num)

            qs = (
                Pedidos.objects.filter(
                    id_estado_id=ESTADO_VENTA,
                    fecha_pedido__year=año,
                    fecha_pedido__month=mes_num
                )
                .annotate(periodo=TruncDay("fecha_pedido"))
                .values("periodo")
                .annotate(total=Sum("total_pedido"))
                .order_by("periodo")
            )

            labels = [safe_label(q["periodo"], "%d/%m") for q in qs]
            valores = [q["total"] or 0 for q in qs]

            return JsonResponse({"labels": labels, "valores": valores})

        except:
            pass

    filtro = request.GET.get("filtro", "mensual")

    if filtro == "diario":
        qs = (
            Pedidos.objects.filter(id_estado_id=ESTADO_VENTA)
            .annotate(periodo=TruncDay("fecha_pedido"))
            .values("periodo")
            .annotate(total=Sum("total_pedido"))
            .order_by("periodo")
        )
        labels = [safe_label(q["periodo"], "%d/%m/%Y") for q in qs]

    elif filtro == "anual":
        qs = (
            Pedidos.objects.filter(id_estado_id=ESTADO_VENTA)
            .annotate(periodo=TruncYear("fecha_pedido"))
            .values("periodo")
            .annotate(total=Sum("total_pedido"))
            .order_by("periodo")
        )
        labels = [safe_label(q["periodo"], "%Y") for q in qs]

    else:  
        qs = (
            Pedidos.objects.filter(id_estado_id=ESTADO_VENTA)
            .annotate(periodo=TruncMonth("fecha_pedido"))
            .values("periodo")
            .annotate(total=Sum("total_pedido"))
            .order_by("periodo")
        )
        labels = [safe_label(q["periodo"], "%m/%Y") for q in qs]

    valores = [q["total"] or 0 for q in qs]

    return JsonResponse({"labels": labels, "valores": valores})



@login_required
def movimientos_list(request):
    empleado = Empleados.objects.filter(user=request.user).first()

    formas_pago = FormaPago.objects.filter(activo=True).order_by('nombre')
    q = request.GET.get("q", "")
    fecha_desde = request.GET.get("desde", "")
    fecha_hasta = request.GET.get("hasta", "")
    filtro_forma_pago = request.GET.get("forma_pago", "")

    movimientos = MovimientosCaja.objects.all().order_by("-fecha_hora")

    if q:
        movimientos = movimientos.filter(
            Q(descripcion__icontains=q) |
            Q(id__icontains=q)
        )

    if fecha_desde:
        movimientos = movimientos.filter(fecha_hora__date__gte=fecha_desde)

    if fecha_hasta:
        movimientos = movimientos.filter(fecha_hora__date__lte=fecha_hasta)

    if filtro_forma_pago:
        movimientos = movimientos.filter(forma_pago_id=filtro_forma_pago)

    # Paginación
    paginator = Paginator(movimientos, 20)
    page = request.GET.get("page")
    movs = paginator.get_page(page)

    contexto = {
        "movs": movs,
        "formas_pago": formas_pago,        
        "filtro_busqueda": q,
        "filtro_fecha_desde": fecha_desde,
        "filtro_fecha_hasta": fecha_hasta,
        "filtro_forma_pago": filtro_forma_pago,
    }

    return render(request, "core/caja/movimientos_list.html", contexto)


@login_required
def configuracion_perfil(request):
    empleado = Empleados.objects.filter(user=request.user).first()

    if request.method == "POST":
        empleado.nombre = request.POST.get("nombre")
        empleado.apellido = request.POST.get("apellido")
        empleado.telefono = request.POST.get("telefono")
        empleado.direccion = request.POST.get("direccion")
        empleado.save()
        request.user.email = request.POST.get("email")
        request.user.save()
        empleado.refresh_from_db()
        request.user.refresh_from_db()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("configuracion")

    return redirect("configuracion")




from django.contrib.auth import update_session_auth_hash
@login_required
def configuracion_password(request):
    if request.method == "POST":
        user = request.user

        actual = request.POST.get("password_actual")
        nueva = request.POST.get("password_nueva")
        confirm = request.POST.get("password_confirm")
        if not user.check_password(actual):
            messages.error(request, "La contraseña actual es incorrecta.")
            return redirect("configuracion")

        if nueva != confirm:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("configuracion")

        user.set_password(nueva)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Contraseña actualizada correctamente.")
        return redirect("configuracion")

    return redirect("configuracion")


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.http import HttpResponse
from django.db.models.functions import TruncMonth, TruncDay, TruncYear
from django.db.models import Sum
from datetime import date
from django.contrib.auth.decorators import login_required
from core.models import Pedidos
from django.templatetags.static import static


@login_required
def reporte_ventas_pdf(request):

    filtro = request.GET.get("filtro")
    mes = request.GET.get("mes")

    ESTADO_VENTA = 3 

    if mes:
        year, month = mes.split("-")
        qs = (
            Pedidos.objects.filter(
                id_estado_id=ESTADO_VENTA,
                fecha_pedido__year=year,
                fecha_pedido__month=month,
            )
            .annotate(periodo=TruncDay("fecha_pedido"))
            .values("periodo")
            .annotate(total=Sum("total_pedido"))
            .order_by("periodo")
        )
        filas = [
            {
                "periodo_str": q["periodo"].strftime("%d/%m/%Y") if q["periodo"] else "Sin fecha",
                "total": q["total"] or 0
            }
            for q in qs
        ]

    else:
        if filtro == "diario":
            truncador = TruncDay("fecha_pedido")
            formato = "%d/%m/%Y"
        elif filtro == "anual":
            truncador = TruncYear("fecha_pedido")
            formato = "%Y"
        else:
            truncador = TruncMonth("fecha_pedido")
            formato = "%m/%Y"

        qs = (
            Pedidos.objects.filter(id_estado_id=ESTADO_VENTA)
            .annotate(periodo=truncador)
            .values("periodo")
            .annotate(total=Sum("total_pedido"))
            .order_by("periodo")
        )

        filas = [
            {
                "periodo_str": q["periodo"].strftime(formato) if q["periodo"] else "Sin fecha",
                "total": q["total"] or 0
            }
            for q in qs
        ]

    logo_url = request.build_absolute_uri(static("img/tintanegra_logo.png"))

    html_string = render_to_string(
        "core/reportes/reporte_ventas.html",
        {
            "filas": filas,
            "fecha_generado": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "usuario": request.user,
            "logo_url": logo_url,
        }
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=reporte_ventas.pdf"

    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse("Error al generar PDF", status=500)

    return response

def render_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)

    result = io.BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)

    if pdf.err:
        return None

    return result.getvalue()


@login_required
@transaction.atomic
def pedido_cambiar_estado(request, id_pedido, nuevo_estado):

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    pedido = get_object_or_404(Pedidos, id_pedido=id_pedido)

    try:
        estado = EstadosPedidos.objects.get(nombre_estado=nuevo_estado)
    except EstadosPedidos.DoesNotExist:
        return JsonResponse({"error": "Estado inválido"}, status=400)

    from django.utils import timezone
    from core.models import (
        StockMovimientos,
        PedidosInsumos,
        PedidosProductos,
        ProductosInsumos,
        MovimientosCaja,
        Cajas,
        Empleados,
        FormaPago
    )

    if nuevo_estado == "ENTREGADO":

        if not pedido.stock_descontado:

            detalles = pedido.detalles.all()
            productos_pedido = PedidosProductos.objects.filter(id_pedido=pedido)

            for det in detalles:
                insumo = det.insumo
                factor = Decimal(insumo.factor_conversion or 1)
                cantidad_real = Decimal(det.cantidad) / factor

                insumo.stock_actual -= cantidad_real
                if insumo.stock_actual < 0:
                    insumo.stock_actual = Decimal("0")
                insumo.save()

                StockMovimientos.objects.create(
                    insumo=insumo,
                    tipo="salida",
                    cantidad=cantidad_real,
                    detalle=f"Uso en Pedido #{pedido.id_pedido}"
                )

            for item in productos_pedido:
                producto = item.id_producto
                if producto.tipo and producto.tipo.nombre_tipo.upper() == "TERCERIZADO":

                    producto.stock_actual -= Decimal(item.cantidad)
                    if producto.stock_actual < 0:
                        producto.stock_actual = Decimal("0")
                    producto.save()

            for item in productos_pedido:
                producto = item.id_producto
                if producto.tipo and producto.tipo.nombre_tipo.upper() == "PERSONALIZADO":

                    receta = ProductosInsumos.objects.filter(producto=producto)

                    for pi in receta:
                        insumo = pi.insumo
                        factor = Decimal(insumo.factor_conversion or 1)
                        cantidad_real = (Decimal(pi.cantidad) * Decimal(item.cantidad)) / factor

                        insumo.stock_actual -= cantidad_real
                        if insumo.stock_actual < 0:
                            insumo.stock_actual = Decimal("0")
                        insumo.save()

                        StockMovimientos.objects.create(
                            insumo=insumo,
                            tipo="salida",
                            cantidad=cantidad_real,
                            detalle=f"Consumo Receta Producto Personalizado (Pedido #{pedido.id_pedido})"
                        )

            pedido.stock_descontado = True

        try:
            caja_abierta = Cajas.objects.filter(caja_cerrada=False).latest("id_caja")
        except Cajas.DoesNotExist:
            return JsonResponse({
                "error": "No hay caja abierta para registrar el cobro."
            }, status=400)

        empleado = Empleados.objects.filter(user=request.user).first()

        monto_cobrado = pedido.total_pedido or 0
        forma_pago = getattr(pedido, "forma_pago", None)
        if not forma_pago:
            forma_pago = FormaPago.objects.first()

        saldo_anterior = caja_abierta.saldo_sistema
        saldo_nuevo = saldo_anterior + monto_cobrado

        MovimientosCaja.objects.create(
            caja=caja_abierta,
            tipo=MovimientosCaja.Tipo.INGRESO,
            forma_pago=forma_pago,
            monto=monto_cobrado,
            descripcion=f"Cobro de Pedido #{pedido.id_pedido}",
            origen=MovimientosCaja.Origen.VENTA,
            referencia_id=pedido.id_pedido,
            creado_por=empleado,
            saldo_resultante=saldo_nuevo
        )

        pedido.id_estado = estado
        pedido.fecha_entrega_real = timezone.now().date()
        pedido.save()

        return JsonResponse({
            "success": True,
            "nuevo_estado": estado.nombre_estado,
            "fecha_entrega_real": pedido.fecha_entrega_real.strftime("%d/%m/%Y"),
            "monto": float(monto_cobrado),
            "cobro_registrado": True
        })

    if nuevo_estado == "EN PRODUCCIÓN":

        if pedido.stock_descontado is False and pedido.id_estado.nombre_estado == "CANCELADO":

            detalles = pedido.detalles.all()
            productos_pedido = PedidosProductos.objects.filter(id_pedido=pedido)

            for det in detalles:
                insumo = det.insumo
                factor = Decimal(insumo.factor_conversion or 1)
                cantidad_real = Decimal(det.cantidad) / factor

                insumo.stock_actual += cantidad_real
                insumo.save()

                StockMovimientos.objects.create(
                    insumo=insumo,
                    tipo="entrada",
                    cantidad=cantidad_real,
                    detalle=f"Reversión de Cancelación (Pedido #{pedido.id_pedido})"
                )

            for item in productos_pedido:
                producto = item.id_producto
                if producto.tipo and producto.tipo.nombre_tipo.upper() == "TERCERIZADO":
                    producto.stock_actual += Decimal(item.cantidad)
                    producto.save()

            for item in productos_pedido:
                producto = item.id_producto
                if producto.tipo and producto.tipo.nombre_tipo.upper() == "PERSONALIZADO":

                    receta = ProductosInsumos.objects.filter(producto=producto)

                    for pi in receta:
                        insumo = pi.insumo
                        factor = Decimal(insumo.factor_conversion or 1)
                        cantidad_real = (Decimal(pi.cantidad) * Decimal(item.cantidad)) / factor

                        insumo.stock_actual += cantidad_real
                        insumo.save()

                        StockMovimientos.objects.create(
                            insumo=insumo,
                            tipo="entrada",
                            cantidad=cantidad_real,
                            detalle=f"Reversión Receta Personalizado (Pedido #{pedido.id_pedido})"
                        )

        pedido.id_estado = estado
        pedido.save()

        return JsonResponse({
            "success": True,
            "nuevo_estado": estado.nombre_estado
        })

    if nuevo_estado == "CANCELADO":

        if pedido.stock_descontado:

            detalles = pedido.detalles.all()
            productos_pedido = PedidosProductos.objects.filter(id_pedido=pedido)

            for det in detalles:
                insumo = det.insumo
                factor = Decimal(insumo.factor_conversion or 1)
                cantidad_real = Decimal(det.cantidad) / factor

                insumo.stock_actual += cantidad_real
                insumo.save()

                StockMovimientos.objects.create(
                    insumo=insumo,
                    tipo="entrada",
                    cantidad=cantidad_real,
                    detalle=f"Devolución por Cancelación Pedido #{pedido.id_pedido}"
                )

            for item in productos_pedido:
                producto = item.id_producto
                if producto.tipo and producto.tipo.nombre_tipo.upper() == "TERCERIZADO":
                    producto.stock_actual += Decimal(item.cantidad)
                    producto.save()

            for item in productos_pedido:
                producto = item.id_producto
                if producto.tipo and producto.tipo.nombre_tipo.upper() == "PERSONALIZADO":

                    receta = ProductosInsumos.objects.filter(producto=producto)

                    for pi in receta:
                        insumo = pi.insumo
                        factor = Decimal(insumo.factor_conversion or 1)
                        cantidad_real = (Decimal(pi.cantidad) * Decimal(item.cantidad)) / factor

                        insumo.stock_actual += cantidad_real
                        insumo.save()

                        StockMovimientos.objects.create(
                            insumo=insumo,
                            tipo="entrada",
                            cantidad=cantidad_real,
                            detalle=f"Devolución Receta Personalizado (Pedido #{pedido.id_pedido})"
                        )

            pedido.stock_descontado = False

        pedido.id_estado = estado
        pedido.save()

        return JsonResponse({
            "success": True,
            "nuevo_estado": estado.nombre_estado,
            "stock_devuelto": True
        })


    pedido.id_estado = estado
    pedido.save()

    return JsonResponse({
        "success": True,
        "nuevo_estado": estado.nombre_estado
    })



@login_required
def cliente_pedidos(request, pk):
    cliente = get_object_or_404(Cliente, id_cliente=pk)
    pedidos = Pedidos.objects.filter(id_cliente=cliente).order_by('-id_pedido')

    return render(request, "core/clientes/cliente_pedidos.html", {
        "cliente": cliente,
        "pedidos": pedidos,
    })


@login_required
@permission_required('core.change_insumos', raise_exception=True)
def insumo_baja(request, pk):
    insumo = get_object_or_404(Insumos, pk=pk)
    insumo.is_active = False
    insumo.save()
    messages.warning(request, f"El insumo '{insumo.nombre}' fue dado de baja.")
    return redirect('insumos_list')


@never_cache
@login_required
@permission_required('core.change_insumos', raise_exception=True)
def insumo_reactivar(request, pk):
    insumo = get_object_or_404(Insumos, pk=pk)

    if request.method == 'POST':
        insumo.is_active = True
        insumo.save()
        messages.success(
            request,
            f"Insumo '{insumo.nombre}' reactivado correctamente."
        )
        list(messages.get_messages(request))
        return redirect('insumos_list')

    return redirect('insumos_list')

@login_required
@require_POST
@transaction.atomic
def set_cliente_presupuesto(request, presupuesto_id):

    id_cliente = request.POST.get("id_cliente")
    if not id_cliente:
        return JsonResponse({"ok": False, "error": "Cliente no recibido."})

    if not presupuesto_id or presupuesto_id == "0":
        presupuesto = Presupuestos.objects.create(
            id_cliente_id=id_cliente,
            fecha_emision=timezone.now().date(),
            subtotal=0,
            total_presupuesto=0,
            estado_presupuesto="EN ESPERA",
        )
        return JsonResponse({"ok": True, "presupuesto_id": presupuesto.id_presupuesto})

    try:
        presupuesto = Presupuestos.objects.get(id_presupuesto=presupuesto_id)
    except Presupuestos.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Presupuesto no encontrado."})

    presupuesto.id_cliente_id = id_cliente
    presupuesto.save()

    return JsonResponse({"ok": True, "presupuesto_id": presupuesto.id_presupuesto})


