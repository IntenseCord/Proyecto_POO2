from django.db import models
from django.contrib.auth.models import User
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
        ordering = ['-fecha', '-numero']
        unique_together = ['empresa', 'tipo', 'numero']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.numero} ({self.fecha})"

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
