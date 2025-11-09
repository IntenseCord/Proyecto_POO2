from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from empresa.models import Empresa
from cuentas.models import Cuenta

class TipoComprobante(models.TextChoices):
    """Tipos de comprobantes contables"""
    INGRESO = 'I', 'Ingreso'
    EGRESO = 'E', 'Egreso'
    NOTA_CONTABLE = 'NC', 'Nota Contable'
    APERTURA = 'A', 'Apertura'
    CIERRE = 'C', 'Cierre'

class Comprobante(models.Model):
    """Modelo para comprobantes contables"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='comprobantes')
    numero = models.CharField(max_length=50, verbose_name="Número de Comprobante")
    tipo = models.CharField(max_length=2, choices=TipoComprobante.choices, verbose_name="Tipo de Comprobante")
    fecha = models.DateField(verbose_name="Fecha")
    descripcion = models.TextField(verbose_name="Descripción")
    total_debito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Débito")
    total_credito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Crédito")
    estado = models.CharField(max_length=20, choices=[('BORRADOR', 'Borrador'), ('APROBADO', 'Aprobado'), 
                                                       ('ANULADO', 'Anulado')], 
                             default='BORRADOR', verbose_name="Estado")
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comprobantes_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Aprobación")
    
    class Meta:
        verbose_name = "Comprobante"
        verbose_name_plural = "Comprobantes"
        ordering = ['-fecha', '-id']  # Ordenar por fecha descendente y luego por ID (más reciente primero)
        unique_together = ['empresa', 'tipo', 'numero']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.numero} ({self.fecha})"
    
    def clean(self):
        """Validar que débito = crédito cuando se aprueba"""
        if self.estado == 'APROBADO':
            if self.total_debito != self.total_credito:
                raise ValidationError('Los débitos deben ser iguales a los créditos para aprobar el comprobante')
            if self.total_debito == 0:
                raise ValidationError('El comprobante debe tener al menos un movimiento')
    
    def calcular_totales(self):
        """Calcula los totales de débito y crédito desde los detalles"""
        from django.db.models import Sum
        totales = self.detalles.aggregate(
            total_debito=Sum('debito'),
            total_credito=Sum('credito')
        )
        self.total_debito = totales['total_debito'] or 0
        self.total_credito = totales['total_credito'] or 0
        self.save()
    
    def aprobar(self, usuario=None):
        """Aprueba el comprobante"""
        self.calcular_totales()
        if self.total_debito != self.total_credito:
            raise ValidationError('No se puede aprobar: Los débitos no son iguales a los créditos')
        self.estado = 'APROBADO'
        self.fecha_aprobacion = timezone.now()
        self.save()
    
    def anular(self):
        """Anula el comprobante"""
        if self.estado == 'ANULADO':
            raise ValidationError('El comprobante ya está anulado')
        self.estado = 'ANULADO'
        self.save()
    
    def esta_balanceado(self):
        """Verifica si el comprobante está balanceado"""
        return self.total_debito == self.total_credito

class DetalleComprobante(models.Model):
    """Modelo para el detalle de cada comprobante"""
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, related_name='detalles')
    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='movimientos')
    descripcion = models.CharField(max_length=300, verbose_name="Descripción")
    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Débito")
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Crédito")
    orden = models.IntegerField(default=0, verbose_name="Orden")
    
    class Meta:
        verbose_name = "Detalle de Comprobante"
        verbose_name_plural = "Detalles de Comprobantes"
        ordering = ['orden']
    
    def __str__(self):
        return f"{self.cuenta.codigo} - Débito: {self.debito} - Crédito: {self.credito}"
    
    def clean(self):
        """Validar que no se registren débito y crédito al mismo tiempo"""
        if self.debito > 0 and self.credito > 0:
            raise ValidationError('No se puede registrar débito y crédito en la misma línea')
        if self.debito == 0 and self.credito == 0:
            raise ValidationError('Debe registrar un valor en débito o crédito')
        if not self.cuenta.acepta_movimiento:
            raise ValidationError(f'La cuenta {self.cuenta.codigo} no acepta movimientos')
