from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import RegexValidator, EmailValidator


# ======================================================================
# CAJA
# ======================================================================
class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey("Empleados", on_delete=models.PROTECT)
    fecha_hora_apertura = models.DateTimeField(auto_now_add=True)
    fecha_hora_cierre = models.DateTimeField(blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_fisico = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tolerancia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True, null=True)
    caja_cerrada = models.BooleanField(default=False)

    class Meta:
        db_table = "cajas"

    def __str__(self):
        estado = "CERRADA" if self.caja_cerrada else "ABIERTA"
        return f"Caja #{self.id_caja} - {estado}"

    @property
    def saldo_sistema(self):
        movs = self.movimientos.all().values("tipo").annotate(m=models.Sum("monto"))
        ingresos = sum(x["m"] for x in movs if x["tipo"] == MovimientosCaja.Tipo.INGRESO) or 0
        egresos = sum(x["m"] for x in movs if x["tipo"] == MovimientosCaja.Tipo.EGRESO) or 0
        return (self.saldo_inicial + ingresos - egresos)


# ======================================================================
# FORMAS DE PAGO
# ======================================================================
class FormaPago(models.Model):
    id_forma = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "formas_pago"
        verbose_name = "Forma de Pago"
        verbose_name_plural = "Formas de Pago"

    def __str__(self):
        return self.nombre


# ======================================================================
# MOVIMIENTOS DE CAJA
# ======================================================================
class MovimientosCaja(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        EGRESO = "EGRESO", "Egreso"

    class Origen(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        COMPRA = "COMPRA", "Por compra"
        VENTA = "VENTA", "Por venta"

    id = models.AutoField(primary_key=True)
    caja = models.ForeignKey("Cajas", on_delete=models.PROTECT, related_name="movimientos")
    fecha_hora = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    forma_pago = models.ForeignKey("FormaPago", on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=255, blank=True)
    origen = models.CharField(max_length=10, choices=Origen.choices, default=Origen.MANUAL)
    referencia_id = models.IntegerField(blank=True, null=True)
    creado_por = models.ForeignKey("Empleados", on_delete=models.PROTECT)
    saldo_resultante = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "movimientos_caja"
        verbose_name_plural = "Movimientos de Caja"

    def __str__(self):
        return f"[{self.tipo}] ${self.monto} - {self.forma_pago} - {self.fecha_hora:%Y-%m-%d %H:%M}"


class AuditoriaCaja(models.Model):
    class Accion(models.TextChoices):
        ABRIR = "ABRIR", "Abrir caja"
        CERRAR = "CERRAR", "Cerrar caja"
        MOV_ALTA = "MOV_ALTA", "Alta movimiento"
        ERROR = "ERROR", "Error de operación"

    id = models.AutoField(primary_key=True)
    caja = models.ForeignKey("Cajas", on_delete=models.SET_NULL, null=True, blank=True)
    movimiento = models.ForeignKey(MovimientosCaja, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(default=timezone.now)
    accion = models.CharField(max_length=10, choices=Accion.choices)
    detalle = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "auditoria_caja"
        verbose_name = "Auditoría de Caja"
        verbose_name_plural = "Auditoría de Caja"


# ======================================================================
# CLIENTES
# ======================================================================
class Cliente(models.Model):
    solo_numeros = RegexValidator(r'^\d+$', 'Solo se permiten números.')
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    direccion = models.CharField(max_length=200, blank=True, null=True)  # opcional
    telefono = models.CharField(max_length=30, validators=[solo_numeros])
    email = models.CharField(max_length=100, validators=[EmailValidator()])
    dni = models.CharField(max_length=20, validators=[solo_numeros])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = 'clientes'
        verbose_name_plural = "Clientes"


# ======================================================================
# PROVEEDORES
# ======================================================================
class Proveedores(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    razon_social = models.CharField(max_length=120, unique=True)
    cuit = models.CharField(max_length=30, unique=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(blank=True, unique=True, null=True)
    persona_contacto = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "proveedores"
        verbose_name_plural = "Proveedores"


    def __str__(self):
        return self.nombre


# ======================================================================
# INSUMOS
# ======================================================================
class Insumos(models.Model):
    id_insumo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    unidad_medida = models.CharField(max_length=40, blank=True, null=True)
    stock_actual = models.IntegerField(blank=True, null=True)
    stock_minimo = models.IntegerField(blank=True, null=True)
    precio_costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    proveedor = models.ForeignKey("Proveedores", on_delete=models.PROTECT, null=True, blank=False)

    class Meta:
        db_table = "insumos"
        verbose_name_plural = "Insumos"

    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida or ''})"


# ======================================================================
# EMPLEADOS
# ======================================================================
class Empleados(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    rol = models.CharField(
        max_length=50,
        choices=[
            ("Jefe", "Jefe"),
            ("Empleado", "Empleado"),
            ("Diseñador", "Diseñador"),
            ("Producción", "Producción"),
        ],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "empleados"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.nombre} {self.apellido or ''}"


class EstadosPedidos(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre_estado = models.CharField(max_length=50)

    class Meta:
        db_table = "estados_pedidos"
        verbose_name_plural = "Estados Pedidos"

    def __str__(self):
        return self.nombre_estado


# ======================================================================
# PEDIDOS / PAGOS / PRESUPUESTOS / PRODUCTOS
# ======================================================================
class Pedidos(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.PROTECT, db_column="id_cliente")
    id_estado = models.ForeignKey(EstadosPedidos, models.PROTECT, db_column="id_estado", null=True, blank=True)
    fecha_pedido = models.DateField(blank=True, null=True)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateField(blank=True, null=True)
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "pedidos"
        verbose_name_plural = "Pedidos"


class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "productos"
        verbose_name_plural = "Productos"


class PedidosProductos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(Pedidos, models.CASCADE, db_column="id_pedido")
    id_producto = models.ForeignKey(Productos, models.PROTECT, db_column="id_producto")
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "pedidos_productos"
        verbose_name_plural = "Pedidos Productos"


class Presupuestos(models.Model):
    id_presupuesto = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.PROTECT, db_column="id_cliente")
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_diseno = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    margen_ganancia = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_presupuesto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado_presupuesto = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = "presupuestos"
        verbose_name_plural = "Presupuestos"


class PresupuestosInsumos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_presupuesto = models.ForeignKey(Presupuestos, models.CASCADE, db_column="id_presupuesto")
    id_insumo = models.ForeignKey(Insumos, models.PROTECT, db_column="id_insumo")
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "presupuestos_insumos"
        verbose_name_plural = "Presupuestos Insumos"


class Pagos(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(Pedidos, on_delete=models.SET_NULL, null=True, blank=True)
    id_forma = models.ForeignKey(FormaPago, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_forma")
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "pagos"
        verbose_name_plural = "Pagos"


# ======================================================================
# DETALLE DE COMPRA
# ======================================================================
class Compras(models.Model):
    id_compra = models.AutoField(primary_key=True)
    proveedor = models.ForeignKey("Proveedores", on_delete=models.PROTECT)
    empleado = models.ForeignKey("Empleados", on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "compras"
        verbose_name_plural = "Compras"

    def __str__(self):
        return f"Compra #{self.id_compra} - ${self.total}"

class DetallesCompra(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    compra = models.ForeignKey("Compras", on_delete=models.CASCADE, db_column="id_compra")
    insumo = models.ForeignKey("Insumos", on_delete=models.PROTECT, db_column="id_insumo")
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "detalles_compra"

    def __str__(self):
        if self.insumo:
            return f"Detalle compra - {self.insumo.nombre}"
        return "Detalle compra (nuevo)"


class PedidosInsumos(models.Model):
    id_detalle_pedido = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE, related_name='detalles') # Relación con el Pedido
    insumo = models.ForeignKey(Insumos, on_delete=models.RESTRICT) # Relación con el Insumo
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"
        # Opcional: asegura que un insumo solo aparezca una vez por pedido
        unique_together = ('pedido', 'insumo')