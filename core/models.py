from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('Empleados', on_delete=models.CASCADE)
    fecha_hora_apertura = models.DateTimeField()
    fecha_hora_cierre = models.DateTimeField(null=True, blank=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_fisico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    caja_cerrada = models.BooleanField(default=False)

    class Meta:
        db_table = 'cajas'
        verbose_name_plural = "Cajas"

class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, unique=True, null=True)
    email = models.CharField(max_length=100, blank=True, unique=True, null=True)
    dni = models.CharField(max_length=20, blank=True, unique=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido or ''}"

    class Meta:
        db_table = 'clientes'
        verbose_name_plural = "Clientes"


class Compras(models.Model):
    id_compra = models.AutoField(primary_key=True)
    id_proveedor = models.ForeignKey('Proveedores', models.PROTECT, db_column='id_proveedor')
    fecha_compra = models.DateField(blank=True, null=True)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'compras'
        verbose_name_plural = "Compras"


class DetallesCompra(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_compra = models.ForeignKey(Compras, models.CASCADE, db_column='id_compra')
    id_insumo = models.ForeignKey('Insumos', models.PROTECT, db_column='id_insumo')
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'detalles_compra'
        verbose_name_plural = "Detalles Compra"


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
    rol = models.CharField(max_length=50, choices=[
        ('Jefe', 'Jefe'),
        ('Empleado', 'Empleado'),
        ('Diseñador', 'Diseñador'),
        ('Producción', 'Producción'),
    ])
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'empleados'
        verbose_name_plural = "Empleados"
    def __str__(self):
        return f"{self.nombre} {self.apellido or ''}"


class EstadosPedidos(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre_estado = models.CharField(max_length=50)

    class Meta:
        db_table = 'estados_pedidos'
        verbose_name_plural = "Estados Pedidos"


class FormasPago(models.Model):
    id_forma = models.AutoField(primary_key=True)
    nombre_forma = models.CharField(max_length=80)

    class Meta:
        db_table = 'formas_pago'
        verbose_name_plural = "Formas de Pago"


class Insumos(models.Model):
    id_insumo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    unidad_medida = models.CharField(max_length=40, blank=True, null=True)
    stock_actual = models.IntegerField(blank=True, null=True)
    stock_minimo = models.IntegerField(blank=True, null=True)
    precio_costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'insumos'
        verbose_name_plural = "Insumos"


class MovimientosCaja(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    id_caja = models.ForeignKey(Cajas, models.PROTECT, db_column='id_caja')
    tipo_movimiento = models.CharField(max_length=7)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_hora = models.DateTimeField(blank=True, null=True)
    id_pago = models.ForeignKey('Pagos', models.SET_NULL, db_column='id_pago', blank=True, null=True)
    id_compra = models.ForeignKey(Compras, models.SET_NULL, db_column='id_compra', blank=True, null=True)
    id_forma = models.ForeignKey(FormasPago, models.PROTECT, db_column='id_forma', blank=True, null=True)

    class Meta:
        db_table = 'movimientos_caja'
        verbose_name_plural = "Movimientos de Caja"


class Pagos(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey('Pedidos', models.CASCADE, db_column='id_pedido', blank=True, null=True)
    id_forma = models.ForeignKey(FormasPago, models.PROTECT, db_column='id_forma', blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_pago = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'pagos'
        verbose_name_plural = "Pagos"


class Pedidos(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.PROTECT, db_column='id_cliente')
    id_estado = models.ForeignKey(EstadosPedidos, models.PROTECT, db_column='id_estado', blank=True, null=True)
    fecha_pedido = models.DateField(blank=True, null=True)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateField(blank=True, null=True)
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'pedidos'
        verbose_name_plural = "Pedidos"


class PedidosProductos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(Pedidos, models.CASCADE, db_column='id_pedido')
    id_producto = models.ForeignKey('Productos', models.PROTECT, db_column='id_producto')
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'pedidos_productos'
        verbose_name_plural = "Pedidos Productos"


class Presupuestos(models.Model):
    id_presupuesto = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.PROTECT, db_column='id_cliente')
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_diseno = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    margen_ganancia = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_presupuesto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado_presupuesto = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = 'presupuestos'
        verbose_name_plural = "Presupuestos"


class PresupuestosInsumos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_presupuesto = models.ForeignKey(Presupuestos, models.CASCADE, db_column='id_presupuesto')
    id_insumo = models.ForeignKey(Insumos, models.PROTECT, db_column='id_insumo')
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'presupuestos_insumos'
        verbose_name_plural = "Presupuestos Insumos"


class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    id_tipo = models.ForeignKey('TiposProducto', models.PROTECT, db_column='id_tipo', blank=True, null=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'productos'
        verbose_name_plural = "Productos"


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

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'proveedores'
        verbose_name_plural = "Proveedores"


class TiposProducto(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre_tipo = models.CharField(max_length=80)

    class Meta:
        db_table = 'tipos_producto'
        verbose_name_plural = "Tipos de Producto"

