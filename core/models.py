# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('Empleados', models.DO_NOTHING, db_column='id_empleado')
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_hora_apertura = models.DateTimeField(blank=True, null=True)
    fecha_hora_cierre = models.DateTimeField(blank=True, null=True)
    total_ingresos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_egresos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    caja_cerrada = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cajas'


class Clientes(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes'


class Compras(models.Model):
    id_compra = models.AutoField(primary_key=True)
    id_proveedor = models.ForeignKey('Proveedores', models.DO_NOTHING, db_column='id_proveedor')
    fecha_compra = models.DateField(blank=True, null=True)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'compras'


class DetallesCompra(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_compra = models.ForeignKey(Compras, models.DO_NOTHING, db_column='id_compra')
    id_insumo = models.ForeignKey('Insumos', models.DO_NOTHING, db_column='id_insumo')
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalles_compra'


class Empleados(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)
    apellido = models.CharField(max_length=60)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    cargo = models.CharField(max_length=80, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empleados'


class EstadosPedidos(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre_estado = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'estados_pedidos'


class FormasPago(models.Model):
    id_forma = models.AutoField(primary_key=True)
    nombre_forma = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'formas_pago'


class Insumos(models.Model):
    id_insumo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    unidad_medida = models.CharField(max_length=40, blank=True, null=True)
    stock_actual = models.IntegerField(blank=True, null=True)
    stock_minimo = models.IntegerField(blank=True, null=True)
    precio_costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'insumos'


class MovimientosCaja(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    id_caja = models.ForeignKey(Cajas, models.DO_NOTHING, db_column='id_caja')
    tipo_movimiento = models.CharField(max_length=7)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_hora = models.DateTimeField(blank=True, null=True)
    id_pago = models.ForeignKey('Pagos', models.DO_NOTHING, db_column='id_pago', blank=True, null=True)
    id_compra = models.ForeignKey(Compras, models.DO_NOTHING, db_column='id_compra', blank=True, null=True)
    id_forma = models.ForeignKey(FormasPago, models.DO_NOTHING, db_column='id_forma', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'movimientos_caja'


class Pagos(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey('Pedidos', models.DO_NOTHING, db_column='id_pedido', blank=True, null=True)
    id_forma = models.ForeignKey(FormasPago, models.DO_NOTHING, db_column='id_forma', blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_pago = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pagos'


class Pedidos(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Clientes, models.DO_NOTHING, db_column='id_cliente')
    id_estado = models.ForeignKey(EstadosPedidos, models.DO_NOTHING, db_column='id_estado', blank=True, null=True)
    fecha_pedido = models.DateField(blank=True, null=True)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateField(blank=True, null=True)
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pedidos'


class PedidosProductos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(Pedidos, models.DO_NOTHING, db_column='id_pedido')
    id_producto = models.ForeignKey('Productos', models.DO_NOTHING, db_column='id_producto')
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pedidos_productos'


class Presupuestos(models.Model):
    id_presupuesto = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Clientes, models.DO_NOTHING, db_column='id_cliente')
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_diseno = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    margen_ganancia = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_presupuesto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado_presupuesto = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'presupuestos'


class PresupuestosInsumos(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_presupuesto = models.ForeignKey(Presupuestos, models.DO_NOTHING, db_column='id_presupuesto')
    id_insumo = models.ForeignKey(Insumos, models.DO_NOTHING, db_column='id_insumo')
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'presupuestos_insumos'


class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    id_tipo = models.ForeignKey('TiposProducto', models.DO_NOTHING, db_column='id_tipo', blank=True, null=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productos'


class Proveedores(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120)
    ciudad = models.CharField(max_length=80, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    cuit = models.CharField(max_length=30, blank=True, null=True)
    categoria = models.CharField(max_length=80, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proveedores'


class TiposProducto(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre_tipo = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'tipos_producto'
