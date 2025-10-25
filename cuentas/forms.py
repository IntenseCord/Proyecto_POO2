from django import forms
from .models import Cuenta, TipoCuenta
from empresa.models import Empresa

class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['empresa', 'codigo', 'nombre', 'tipo', 'cuenta_padre', 'naturaleza', 'acepta_movimiento', 'esta_activa']
        widgets = {
            'empresa': forms.Select(attrs={
                'class': 'form-control'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1105'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la cuenta'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cuenta_padre': forms.Select(attrs={
                'class': 'form-control'
            }),
            'naturaleza': forms.Select(attrs={
                'class': 'form-control'
            }),
            'acepta_movimiento': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'esta_activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'empresa': 'Empresa',
            'codigo': 'Código de Cuenta',
            'nombre': 'Nombre de la Cuenta',
            'tipo': 'Tipo de Cuenta',
            'cuenta_padre': 'Cuenta Padre (Opcional)',
            'naturaleza': 'Naturaleza',
            'acepta_movimiento': 'Acepta Movimientos',
            'esta_activa': 'Cuenta Activa',
        }
        help_texts = {
            'codigo': 'Código único para la cuenta (Ej: 1105 para Caja)',
            'cuenta_padre': 'Seleccione una cuenta padre si esta es una subcuenta',
            'acepta_movimiento': 'Desmarque si es una cuenta de agrupación',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar cuentas padre según la empresa seleccionada
        if 'empresa' in self.data:
            try:
                empresa_id = int(self.data.get('empresa'))
                self.fields['cuenta_padre'].queryset = Cuenta.objects.filter(
                    empresa_id=empresa_id, 
                    esta_activa=True
                ).order_by('codigo')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['cuenta_padre'].queryset = Cuenta.objects.filter(
                empresa=self.instance.empresa,
                esta_activa=True
            ).exclude(pk=self.instance.pk).order_by('codigo')
    
    def clean(self):
        cleaned_data = super().clean()
        cuenta_padre = cleaned_data.get('cuenta_padre')
        codigo = cleaned_data.get('codigo')
        
        # Calcular nivel automáticamente
        if cuenta_padre:
            cleaned_data['nivel'] = cuenta_padre.nivel + 1
        else:
            cleaned_data['nivel'] = 1
        
        # Validar que el código sea numérico
        if codigo and not codigo.isdigit():
            raise forms.ValidationError('El código debe contener solo números')
        
        return cleaned_data

class FiltroCuentaForm(forms.Form):
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.filter(activo=True),
        required=False,
        empty_label="Todas las empresas",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    tipo = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + list(TipoCuenta.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código o nombre...'
        })
    )
