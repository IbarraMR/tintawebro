from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.utils import timezone


from .models import (
    Cliente,
    Proveedores,
    Empleados,
    FormaPago,
    MovimientosCaja,
    Compras,
    DetallesCompra,
    Insumos,
    UnidadMedida,
    ProductosInsumos,
    Presupuestos,
    ConfiguracionEmpresa,
    ConfiguracionEmail,
    Productos,
    

)
from django.forms.models import inlineformset_factory
from django import forms
from django.core.exceptions import ValidationError
from core.models import Cliente

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

    def clean(self):
        cleaned_data = super().clean()

        dni = cleaned_data.get("dni")
        email = cleaned_data.get("email")
        telefono = cleaned_data.get("telefono")
        qs = Cliente.objects.exclude(pk=self.instance.pk)

        if dni and qs.filter(dni=dni).exists():
            raise ValidationError({"dni": "Ya existe un cliente con este DNI."})

        if email and qs.filter(email=email).exists():
            raise ValidationError({"email": "Ya existe un cliente con este email."})

        if telefono and qs.filter(telefono=telefono).exists():
            raise ValidationError({"telefono": "Ya existe un cliente con este teléfono."})

        return cleaned_data


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
        



from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Empleados
from django.core.validators import validate_email

class EmpleadoForm(forms.ModelForm):

    ROLES = [
        ('Jefe', 'Jefe'),
        ('Empleado', 'Empleado'),
    ]

    rol = forms.ChoiceField(choices=ROLES, label="Rol")

    class Meta:
        model = Empleados
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={'type': 'date', 'min': '1900-01-01', 'max': '2004-12-31'}
            ),
            'dni': forms.TextInput(attrs={'pattern': '[0-9]+', 'title': 'Solo números'}),
            'telefono': forms.TextInput(attrs={'pattern': '[0-9]+', 'title': 'Solo números'}),
            'email': forms.EmailInput(),
        }

    def clean_dni(self):
        dni = (self.cleaned_data.get('dni') or "").strip()

        if not dni.isdigit():
            raise ValidationError("El DNI solo puede contener números.")
        if len(dni) < 7 or len(dni) > 10:
            raise ValidationError("El DNI debe tener entre 7 y 10 dígitos.")

        return dni

    def clean_telefono(self):
        tel = (self.cleaned_data.get('telefono') or "").strip()

        if not tel.isdigit():
            raise ValidationError("El teléfono solo puede contener números.")
        if len(tel) < 7:
            raise ValidationError("El teléfono es demasiado corto.")

        return tel

    def clean_email(self):
        email = (self.cleaned_data.get('email') or "").strip()

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Ingrese un email válido (ej: usuario@dominio.com).")
        return email

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')

        if fecha is None:
            return fecha
        limite = date(2005, 1, 1)
        if fecha >= limite:
            raise ValidationError("La fecha debe ser anterior al año 2005.")

        return fecha
    def clean(self):
        cleaned = super().clean()

        dni = cleaned.get('dni')
        telefono = cleaned.get('telefono')
        email = cleaned.get('email')

        if dni and Empleados.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese DNI.")

        if telefono and Empleados.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese teléfono.")

        if email and Empleados.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un empleado con ese email.")

        return cleaned


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

class FormaPagoForm(forms.ModelForm):
    class Meta:
        model = FormaPago
        fields = ['nombre', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tarjeta'}),
        }


class InsumoForm(forms.ModelForm):
    unidad_medida = forms.ModelChoiceField(
        queryset=UnidadMedida.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Unidad de medida"
    )

    class Meta:
        model = Insumos
        fields = [
            'proveedor', 'nombre', 'descripcion',
            'unidad_medida', 'factor_conversion',
            'stock_actual', 'stock_minimo',
            'precio_costo_unitario'
        ]
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'factor_conversion': forms.NumberInput(attrs={'class': 'form-control', 'value': 1, 'min': '1'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'value': 0, 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'precio_costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if Insumos.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("⚠ Ya existe un insumo con ese nombre.")
        return nombre
    def clean_stock_actual(self):
        stock = self.cleaned_data.get("stock_actual")
        if stock is not None and stock < 0:
            raise forms.ValidationError("El stock actual no puede ser negativo.")
        return stock

    def clean_stock_minimo(self):
        minimo = self.cleaned_data.get("stock_minimo")
        if minimo is not None and minimo < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return minimo

    def clean_factor_conversion(self):
        factor = self.cleaned_data.get("factor_conversion")
        if factor is None or factor <= 0:
            raise forms.ValidationError("El factor de conversión debe ser mayor a 0.")
        return factor

    def clean_precio_costo_unitario(self):
        precio = self.cleaned_data.get("precio_costo_unitario")
        if precio is not None and precio < 0:
            raise forms.ValidationError("El precio costo unitario no puede ser negativo.")
        return precio

        

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
        fields = ['proveedor', 'forma_pago']  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['proveedor'].queryset = Proveedores.objects.filter(is_active=True).order_by('nombre')
        self.fields['proveedor'].widget.attrs.update({'class': 'form-select'})
        self.fields['forma_pago'].widget.attrs.update({'class': 'form-select'})



DetallesCompraFormSet = inlineformset_factory(
    Compras, 
    DetallesCompra, 
    form=DetallesCompraForm, 
    extra=1, 
    can_delete=True
)



class ProductoInsumoForm(forms.ModelForm):
    class Meta:
        model = ProductosInsumos
        fields = ["insumo", "cantidad"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuestos
        fields = [
            "id_cliente",
            "fecha_emision",
            "fecha_vencimiento",
            "trabajo",
            "descripcion",
            "costo_diseno",
            "margen_ganancia",
        ]
        widgets = {
            "id_cliente": forms.Select(attrs={"class": "form-select"}),
            "trabajo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Cuadernos A5 personalizados"}),
            "fecha_emision": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "costo_diseno": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "margen_ganancia": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100, "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["id_cliente"].queryset = Cliente.objects.order_by("nombre")
        if not self.is_bound: 
            if not self.instance.pk or not self.instance.fecha_emision:
                self.initial.setdefault("fecha_emision", timezone.localdate())

    def clean_fecha_emision(self):
        fecha = self.cleaned_data.get("fecha_emision")
        hoy = timezone.localdate()
        if fecha and fecha < hoy:
            raise ValidationError("La fecha de emisión no puede ser anterior a hoy.")
        return fecha

    def clean(self):
        cleaned = super().clean()
        fecha_emision = cleaned.get("fecha_emision")
        fecha_vencimiento = cleaned.get("fecha_vencimiento")

        if fecha_emision and fecha_vencimiento:
            if fecha_vencimiento <= fecha_emision:
                self.add_error(
                    "fecha_vencimiento",
                    "La fecha de vencimiento debe ser posterior a la fecha de emisión."
                )

        return cleaned



class ConfiguracionEmpresaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = "__all__"
        widgets = {
            "condiciones_pago": forms.Textarea(attrs={"rows": 3}),
            "otros_detalles": forms.Textarea(attrs={"rows": 3}),
        }

class ConfiguracionEmailForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmail
        fields = "__all__"
        widgets = {
            "email_remitente": forms.EmailInput(attrs={"class": "form-control"}),
            "contraseña_app": forms.PasswordInput(attrs={"class": "form-control"}),
            "smtp_host": forms.TextInput(attrs={"class": "form-control"}),
            "smtp_port": forms.NumberInput(attrs={"class": "form-control"}),
            "usar_tls": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Productos
        fields = ["nombre", "descripcion", "tipo", "precio"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }