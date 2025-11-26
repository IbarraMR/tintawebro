from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import RegexValidator, EmailValidator



class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)

    id_empleado = models.ForeignKey(
        "Empleados",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


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
    revertido = models.BooleanField(default=False)

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


class Cliente(models.Model):
    solo_numeros = RegexValidator(r'^\d+$', 'Solo se permiten números.')
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    direccion = models.CharField(max_length=200, blank=True, null=True) 
    telefono = models.CharField(max_length=30, validators=[solo_numeros], unique=True)
    email = models.CharField(max_length=100, validators=[EmailValidator()], unique=True)
    dni = models.CharField(max_length=20, validators=[solo_numeros], unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = 'clientes'
        verbose_name_plural = "Clientes"


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



class UnidadMedida(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)

    class Meta:
        db_table = "unidad_medida"  

    def __str__(self):
            return self.nombre

class Insumos(models.Model):
    id_insumo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    unidad_medida = models.CharField(max_length=40, null=True, blank=True, db_column="unidad_medida")
    factor_conversion = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.IntegerField(blank=True, null=True)
    precio_costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    proveedor = models.ForeignKey("Proveedores", on_delete=models.PROTECT, null=True, blank=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "insumos"
        verbose_name_plural = "Insumos"

    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida or ''})"


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


class Pedidos(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.PROTECT, db_column="id_cliente")
    id_estado = models.ForeignKey(EstadosPedidos, models.PROTECT, db_column="id_estado", null=True, blank=True)
    fecha_pedido = models.DateField(blank=True, null=True)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateField(blank=True, null=True)
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_descontado = models.BooleanField(default=False)

    class Meta:
        db_table = "pedidos"
        verbose_name_plural = "Pedidos"


class TiposProducto(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre_tipo = models.CharField(max_length=80)

    class Meta:
        db_table = "tipos_producto"
        verbose_name = "Tipo de Producto"
        verbose_name_plural = "Tipos de Productos"

    def __str__(self):
        return self.nombre_tipo



class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    costo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tipo = models.ForeignKey(
        TiposProducto,
        on_delete=models.PROTECT,
        db_column="tipo_id",
        related_name="productos",
        null=True,
        blank=True
    )
    costo_diseno = models.DecimalField(max_digits=10, decimal_places=2)
    margen_ganancia = models.DecimalField(max_digits=5, decimal_places=2)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "productos"

    def __str__(self):
        return self.nombre


class PedidosProductos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(Pedidos, models.CASCADE, db_column="id_pedido")
    id_producto = models.ForeignKey(Productos, models.PROTECT, db_column="id_producto")
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "pedidos_productos"
        verbose_name_plural = "Pedidos Productos"

class ProductosInsumos(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(
        Productos,
        on_delete=models.CASCADE,
        db_column="producto_id"
    )
    insumo = models.ForeignKey(
        Insumos,
        on_delete=models.PROTECT,
        db_column="insumo_id"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        db_table = "productos_insumos"
        verbose_name = "Producto-Insumo"
        verbose_name_plural = "Productos-Insumos"
    def __str__(self):
        return f"{self.producto} → {self.insumo} ({self.cantidad})"


class Presupuestos(models.Model):
    id_presupuesto = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente,models.PROTECT,db_column="id_cliente",null=True, blank=True)
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_diseno = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    margen_ganancia = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_presupuesto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ESTADOS = [
        ("EN ESPERA", "En espera de aprobación"),
        ("CONFIRMADO", "Confirmado"),
        ("RECHAZADO", "Rechazado"),
    ]
    estado_presupuesto = models.CharField(max_length=20, choices=ESTADOS, default="EN ESPERA")
    trabajo = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)


    class Meta:
        db_table = "presupuestos"
        verbose_name_plural = "Presupuestos"


class PresupuestosInsumos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(Presupuestos, models.CASCADE, db_column="id_presupuesto")
    insumo = models.ForeignKey(Insumos, models.PROTECT, null=True, blank=True, db_column="id_insumo")
    producto = models.ForeignKey(Productos, models.PROTECT, null=True, blank=True, db_column="id_producto")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    trabajo = models.ForeignKey("Trabajo", models.CASCADE, null=True, blank=True)


    class Meta:
        db_table = "presupuestos_insumos"
        verbose_name_plural = "Presupuestos Insumos"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class Pagos(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(Pedidos, on_delete=models.SET_NULL, null=True, blank=True)
    id_forma = models.ForeignKey(FormaPago, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_forma")
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "pagos"
        verbose_name_plural = "Pagos"


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
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE, related_name='detalles')
    insumo = models.ForeignKey(Insumos, on_delete=models.RESTRICT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"
        unique_together = ('pedido', 'insumo')


class StockMovimientos(models.Model):
    MOVIMIENTO_TIPOS = (
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    )

    id_movimiento = models.AutoField(primary_key=True)
    insumo = models.ForeignKey(Insumos, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=MOVIMIENTO_TIPOS)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    detalle = models.CharField(max_length=200, null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stock_movimientos"
        verbose_name_plural = "Movimientos de Stock"

    def __str__(self):
        return f"{self.fecha_hora} - {self.insumo.nombre} ({self.tipo})"


class ConfiguracionEmpresa(models.Model):
    nombre_empresa = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    condiciones_pago = models.TextField(blank=True, null=True)
    otros_detalles = models.TextField(blank=True, null=True)
    firma_autorizada = models.CharField(max_length=255, blank=True, null=True)
    firma_digital = models.FileField(upload_to="firmas/", blank=True, null=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)

    class Meta:
        db_table = "configuracion_empresa"
    def __str__(self):
        return self.nombre_empresa or "Configuración de empresa"


class ConfiguracionEmail(models.Model):
    email_remitente = models.EmailField(null=True, blank=True)
    contraseña_app = models.CharField(max_length=200, null=True, blank=True) 
    smtp_host = models.CharField(max_length=200, default="smtp.gmail.com")
    smtp_port = models.IntegerField(default=587)
    usar_tls = models.BooleanField(default=True)

    class Meta:
        db_table = "configuracion_email"
        verbose_name_plural = "Configuración de Email"

    def __str__(self):
        return self.email_remitente or "Sin configurar"


class PresupuestosProductos(models.Model):
    id = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(Presupuestos, on_delete=models.CASCADE)
    trabajo = models.CharField(max_length=150)  
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "presupuestos_productos"

    def __str__(self):
        return f"{self.trabajo} - {self.subtotal}"


from django.db import models


class Trabajo(models.Model):
    id = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(Presupuestos, on_delete=models.CASCADE, related_name="trabajos", db_column="id_presupuesto")
    nombre_trabajo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    costo_diseno = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    margen_ganancia = models.DecimalField(max_digits=5, decimal_places=2, default=0)  
    subtotal_insumos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)  
    total_trabajo = models.DecimalField(max_digits=12, decimal_places=2, default=0)   

    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trabajos"
        verbose_name_plural = "Trabajos"

class TrabajoInsumo(models.Model):
    id = models.AutoField(primary_key=True)
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="insumos", db_column="id_trabajo")
    insumo = models.ForeignKey(Insumos, on_delete=models.PROTECT, db_column="id_insumo")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "trabajos_insumos"
        verbose_name_plural = "Trabajo Insumos"


