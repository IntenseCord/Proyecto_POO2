from django import forms
from .models import Empresa

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'nit', 'direccion', 'telefono', 'email', 'representante_legal', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NIT sin puntos ni guiones'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@empresa.com'
            }),
            'representante_legal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del representante legal'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Empresa',
            'nit': 'NIT',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Email',
            'representante_legal': 'Representante Legal',
            'activo': 'Empresa Activa',
        }
        help_texts = {
            'nit': 'Ingrese el NIT sin puntos ni guiones',
            'activo': 'Desmarque para desactivar la empresa sin eliminarla',
        }
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        # Remover espacios y caracteres especiales
        nit = ''.join(filter(str.isalnum, nit))
        return nit
