from django.db import models
from empresa.models import Empresa

class TipoCuenta(models.TextChoices):
    """Tipos de cuentas contables"""
    ACTIVO = 'A', 'Activo'
    PASIVO = 'P', 'Pasivo'
    PATRIMONIO = 'PT', 'Patrimonio'
    INGRESO = 'I', 'Ingreso'
    GASTO = 'G', 'Gasto'
    COSTO = 'C', 'Costo'

class Cuenta(models.Model):
    """Modelo para el plan de cuentas contables"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cuentas')
    codigo = models.CharField(max_length=20, verbose_name="Código de Cuenta")
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Cuenta")
    tipo = models.CharField(max_length=2, choices=TipoCuenta.choices, verbose_name="Tipo de Cuenta")
    cuenta_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                     related_name='subcuentas', verbose_name="Cuenta Padre")
    nivel = models.IntegerField(default=1, verbose_name="Nivel")
    naturaleza = models.CharField(max_length=10, choices=[('DEBITO', 'Débito'), ('CREDITO', 'Crédito')], 
                                  verbose_name="Naturaleza")
    acepta_movimiento = models.BooleanField(default=True, verbose_name="Acepta Movimiento")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"
        ordering = ['codigo']
        unique_together = ['empresa', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
