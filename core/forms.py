# core/forms.py

from django import forms
from .models import Cliente # Asegúrate de que tu modelo se llame Cliente

class ClienteForm(forms.ModelForm):
    """
    Define el formulario para la creación y edición del modelo Cliente.
    """
    class Meta:
        model = Cliente
        # Campos de tu modelo Cliente
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono', 'direccion']
        
        # Personalización de widgets para el estilo Dark Mode de Bootstrap
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente', 'required': True}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido del cliente'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI o CUIT'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de teléfono'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección completa'}),
        }