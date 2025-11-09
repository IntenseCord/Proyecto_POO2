from django import forms
from django.forms import inlineformset_factory
from .models import Comprobante, DetalleComprobante, TipoComprobante
from empresa.models import Empresa
from cuentas.models import Cuenta

class ComprobanteForm(forms.ModelForm):
    class Meta:
        model = Comprobante
        fields = ['empresa', 'tipo', 'numero', 'fecha', 'descripcion']
        widgets = {
            'empresa': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número consecutivo',
                'required': True
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del comprobante',
                'required': True
            }),
        }
        labels = {
            'empresa': 'Empresa',
            'tipo': 'Tipo de Comprobante',
            'numero': 'Número',
            'fecha': 'Fecha',
            'descripcion': 'Descripción',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo empresas activas
        self.fields['empresa'].queryset = Empresa.objects.filter(activo=True)

class DetalleComprobanteForm(forms.ModelForm):
    class Meta:
        model = DetalleComprobante
        fields = ['cuenta', 'descripcion', 'debito', 'credito']
        widgets = {
            'cuenta': forms.Select(attrs={
                'class': 'form-control cuenta-select',
                'required': True
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del movimiento',
                'required': True
            }),
            'debito': forms.NumberInput(attrs={
                'class': 'form-control debito-input',
                'step': '0.01',
                'min': '0',
                'value': '0',
                'placeholder': '0.00'
            }),
            'credito': forms.NumberInput(attrs={
                'class': 'form-control credito-input',
                'step': '0.01',
                'min': '0',
                'value': '0',
                'placeholder': '0.00'
            }),
        }
        labels = {
            'cuenta': 'Cuenta',
            'descripcion': 'Descripción',
            'debito': 'Débito',
            'credito': 'Crédito',
        }
    
    def __init__(self, *args, **kwargs):
        empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar cuentas por empresa y que acepten movimiento
        if empresa_id:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(
                empresa_id=empresa_id,
                acepta_movimiento=True,
                esta_activa=True
            ).order_by('codigo')
        else:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(
                acepta_movimiento=True,
                esta_activa=True
            ).order_by('codigo')
    
    def clean(self):
        cleaned_data = super().clean()
        debito = cleaned_data.get('debito', 0)
        credito = cleaned_data.get('credito', 0)
        
        if debito > 0 and credito > 0:
            raise forms.ValidationError('No puede registrar débito y crédito en la misma línea')
        
        if debito == 0 and credito == 0:
            raise forms.ValidationError('Debe registrar un valor en débito o crédito')
        
        return cleaned_data

# Formset para manejar múltiples detalles
DetalleComprobanteFormSet = inlineformset_factory(
    Comprobante,
    DetalleComprobante,
    form=DetalleComprobanteForm,
    extra=1,  # Muestra solo 1 formulario vacío inicial
    can_delete=True,
    min_num=0,  # No forzar mínimo en la visualización
    validate_min=False,  # La validación de mínimo 2 se hace en la vista
)

class FiltroComprobanteForm(forms.Form):
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.filter(activo=True),
        required=False,
        empty_label="Todas las empresas",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    tipo = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + list(TipoComprobante.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('BORRADOR', 'Borrador'),
            ('APROBADO', 'Aprobado'),
            ('ANULADO', 'Anulado')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
