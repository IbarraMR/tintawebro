from django import forms
from .models import Cliente
from .models import Proveedores
from .models import Empleados
from .models import Insumos
from django.core.exceptions import ValidationError
from .models import MovimientosCaja, FormaPago
from core.models import FormaPago

class ClienteForm(forms.ModelForm):
    """
    Define el formulario para la creación y edición del modelo Cliente.
    """
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente', 'required': True}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido del cliente'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI o CUIT'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de teléfono'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección completa'}),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedores
        fields = [
            'nombre', 
            'cuit', 
            'razon_social', 
            'telefono', 
            'email', 
            'direccion', 
            'persona_contacto'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Nombre *'}),
            'cuit': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'CUIT *'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Razón Social *'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Teléfono *'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Email *'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Dirección *'}),
            'persona_contacto': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Persona de contacto *'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in self.fields:
            if not cleaned_data.get(field):
                raise forms.ValidationError("Todos los campos son obligatorios")
        return cleaned_data
    

class EmpleadoForm(forms.ModelForm):
    ROLES = [
        ('Jefe', 'Jefe'),
        ('Empleado', 'Empleado'),
        ('Diseñador', 'Diseñador'),
        ('Producción', 'Producción'),
    ]

    rol = forms.ChoiceField(choices=ROLES, required=False, label="Rol")

    class Meta:
        model = Empleados
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        dni = cleaned_data.get('dni')
        telefono = cleaned_data.get('telefono')
        email = cleaned_data.get('email')

        if Empleados.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese DNI.")

        if Empleados.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese teléfono.")

        if Empleados.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese email.")

        return cleaned_data
    

class MovimientoCajaForm(forms.ModelForm):
    class Meta:
        model = MovimientosCaja
        fields = ['tipo', 'forma_pago', 'monto', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'forma_pago': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción'}),
        }


class FormaPagoForm(forms.ModelForm):
    class Meta:
        model = FormaPago
        fields = ["nombre", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Tarjeta"}),
        }



class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumos
        fields = [
            'proveedor',
            'nombre',
            'descripcion',
            'unidad_medida',
            'stock_actual',
            'stock_minimo',
            'precio_costo_unitario'
        ]
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': "Nombre del insumo"}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ej: resma 500 hojas"}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'precio_costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0})
        }