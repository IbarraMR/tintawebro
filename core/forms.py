# core/forms.py

from django import forms
from .models import Cliente
from .models import Proveedores

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
        # Verifica si algún campo está vacío
        for field in self.fields:
            if not cleaned_data.get(field):
                raise forms.ValidationError("Todos los campos son obligatorios")
        return cleaned_data