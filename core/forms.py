from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

from .models import (
    Cliente,
    Proveedores,
    Empleados,
    FormaPago,
    MovimientosCaja,
    Compras,
    DetallesCompra,
    Insumos
)
from django.forms.models import inlineformset_factory

# ==========================================================
# FORM CLIENTE
# ==========================================================
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente', 'required': True}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI / CUIT'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección completa'}),
        }


# ==========================================================
# FORM PROVEEDOR
# ==========================================================
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedores
        fields = ['nombre', 'razon_social', 'cuit', 'telefono', 'email', 'direccion', 'persona_contacto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'cuit': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'persona_contacto': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        for field in self.fields:
            if not cleaned.get(field):
                raise ValidationError("Todos los campos son obligatorios.")
        return cleaned
        


# ==========================================================
# FORM EMPLEADOS
# ==========================================================
class EmpleadoForm(forms.ModelForm):
    ROLES = [
        ('Jefe', 'Jefe'),
        ('Empleado', 'Empleado'),
        ('Diseñador', 'Diseñador'),
        ('Producción', 'Producción'),
    ]

    rol = forms.ChoiceField(choices=ROLES, label="Rol")

    class Meta:
        model = Empleados
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        dni = cleaned.get('dni')
        telefono = cleaned.get('telefono')
        email = cleaned.get('email')

        if Empleados.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese DNI.")
        if Empleados.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese teléfono.")
        if Empleados.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese email.")

        return cleaned


# ==========================================================
# FORM MOVIMIENTO DE CAJA
# ==========================================================
class MovimientoCajaForm(forms.ModelForm):
    class Meta:
        model = MovimientosCaja
        fields = ['tipo', 'forma_pago', 'monto', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'forma_pago': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ==========================================================
# FORM FORMA DE PAGO
# ==========================================================
class FormaPagoForm(forms.ModelForm):
    class Meta:
        model = FormaPago
        fields = ['nombre', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tarjeta'}),
        }


# ==========================================================
# FORM INSUMOS
# ==========================================================
class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumos
        fields = ['proveedor', 'nombre', 'descripcion', 'unidad_medida', 'stock_actual', 'stock_minimo', 'precio_costo_unitario']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class DetallesCompraForm(forms.ModelForm):
    precio_unitario = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control detalle-precio', 'step': '0.01'})
    )
    
    subtotal = forms.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=False, 
        initial=0.00,
        widget=forms.TextInput(attrs={'class': 'form-control subtotal-input', 'readonly': 'readonly'})
    )

    class Meta:
        model = DetallesCompra
        fields = ['insumo', 'cantidad', 'precio_unitario'] 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['insumo'].widget.attrs.update({'class': 'form-select detalle-insumo'})
        self.fields['cantidad'].widget.attrs.update({'class': 'form-control detalle-cantidad', 'min': '1'})
    



class ComprasForm(forms.ModelForm):
    forma_pago = forms.ModelChoiceField(
        queryset=FormaPago.objects.all(),
        label="Forma de Pago",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    class Meta:
        model = Compras
        fields = ['proveedor', 'empleado', 'forma_pago']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].widget.attrs.update({'class': 'form-select'})
        self.fields['empleado'].widget.attrs.update({'class': 'form-select'})


# Formset para los detalles de la compra (Múltiples insumos)
DetallesCompraFormSet = inlineformset_factory(
    Compras, 
    DetallesCompra, 
    form=DetallesCompraForm, 
    extra=1, 
    can_delete=True
)