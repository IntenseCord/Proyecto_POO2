from django.db import models
from django.db.models import Sum, Q
from empresa.models import Empresa
from abc import ABC, abstractmethod
from decimal import Decimal

class TipoCuenta(models.TextChoices):
    """Tipos de cuentas contables"""
    ACTIVO = 'A', 'Activo'
    PASIVO = 'P', 'Pasivo'
    PATRIMONIO = 'PT', 'Patrimonio'
    INGRESO = 'I', 'Ingreso'
    GASTO = 'G', 'Gasto'
    COSTO = 'C', 'Costo'

class Cuenta(models.Model):
    """Modelo base para el plan de cuentas contables (Clase Base con Herencia)"""
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
    esta_activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"
        ordering = ['codigo']
        unique_together = ['empresa', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    # Métodos polimórficos (serán sobrescritos en clases hijas)
    def registrar_movimiento(self, monto, es_debito):
        """
        Registra un movimiento en la cuenta.
        Retorna el efecto en el saldo según la naturaleza de la cuenta.
        Este método implementa POLIMORFISMO.
        """
        raise NotImplementedError("Debe implementarse en las subclases específicas")
    
    def calcular_saldo(self):
        """
        Calcula el saldo actual de la cuenta.
        Implementa POLIMORFISMO según el tipo de cuenta.
        """
        from transacciones.models import DetalleComprobante
        
        movimientos = DetalleComprobante.objects.filter(
            cuenta=self,
            comprobante__estado='APROBADO'
        ).aggregate(
            total_debito=Sum('debito'),
            total_credito=Sum('credito')
        )
        
        debitos = movimientos['total_debito'] or Decimal('0.00')
        creditos = movimientos['total_credito'] or Decimal('0.00')
        
        # El cálculo del saldo depende de la naturaleza de la cuenta (polimorfismo)
        if self.naturaleza == 'DEBITO':
            return debitos - creditos
        else:  # CREDITO
            return creditos - debitos
    
    def obtener_tipo_especifico(self):
        """
        Retorna la instancia específica de la cuenta (Activo, Pasivo, etc.)
        Implementa el patrón de diseño para acceder a la clase hija.
        """
        if hasattr(self, 'activo'):
            return self.activo
        elif hasattr(self, 'pasivo'):
            return self.pasivo
        elif hasattr(self, 'patrimonio'):
            return self.patrimonio
        elif hasattr(self, 'ingreso'):
            return self.ingreso
        elif hasattr(self, 'gasto'):
            return self.gasto
        elif hasattr(self, 'costo'):
            return self.costo
        return self


# ============================================
# CLASES HIJAS - IMPLEMENTAN HERENCIA
# ============================================

class Activo(Cuenta):
    """
    Clase que hereda de Cuenta para representar cuentas de Activo.
    Implementa HERENCIA y POLIMORFISMO.
    """
    es_corriente = models.BooleanField(default=True, verbose_name="Es Corriente")
    
    class Meta:
        verbose_name = "Activo"
        verbose_name_plural = "Activos"
    
    def save(self, *args, **kwargs):
        self.tipo = TipoCuenta.ACTIVO
        self.naturaleza = 'DEBITO'
        super().save(*args, **kwargs)
    
    def registrar_movimiento(self, monto, es_debito):
        """
        Polimorfismo: Los activos aumentan con débito y disminuyen con crédito.
        """
        if es_debito:
            return monto  # Aumenta el activo
        else:
            return -monto  # Disminuye el activo


class Pasivo(Cuenta):
    """
    Clase que hereda de Cuenta para representar cuentas de Pasivo.
    Implementa HERENCIA y POLIMORFISMO.
    """
    es_corriente = models.BooleanField(default=True, verbose_name="Es Corriente")
    
    class Meta:
        verbose_name = "Pasivo"
        verbose_name_plural = "Pasivos"
    
    def save(self, *args, **kwargs):
        self.tipo = TipoCuenta.PASIVO
        self.naturaleza = 'CREDITO'
        super().save(*args, **kwargs)
    
    def registrar_movimiento(self, monto, es_debito):
        """
        Polimorfismo: Los pasivos aumentan con crédito y disminuyen con débito.
        """
        if es_debito:
            return -monto  # Disminuye el pasivo
        else:
            return monto  # Aumenta el pasivo


class Patrimonio(Cuenta):
    """
    Clase que hereda de Cuenta para representar cuentas de Patrimonio.
    Implementa HERENCIA y POLIMORFISMO.
    """
    
    class Meta:
        verbose_name = "Patrimonio"
        verbose_name_plural = "Patrimonios"
    
    def save(self, *args, **kwargs):
        self.tipo = TipoCuenta.PATRIMONIO
        self.naturaleza = 'CREDITO'
        super().save(*args, **kwargs)
    
    def registrar_movimiento(self, monto, es_debito):
        """
        Polimorfismo: El patrimonio aumenta con crédito y disminuye con débito.
        """
        if es_debito:
            return -monto  # Disminuye el patrimonio
        else:
            return monto  # Aumenta el patrimonio


class Ingreso(Cuenta):
    """
    Clase que hereda de Cuenta para representar cuentas de Ingreso.
    Implementa HERENCIA y POLIMORFISMO.
    """
    
    class Meta:
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"
    
    def save(self, *args, **kwargs):
        self.tipo = TipoCuenta.INGRESO
        self.naturaleza = 'CREDITO'
        super().save(*args, **kwargs)
    
    def registrar_movimiento(self, monto, es_debito):
        """
        Polimorfismo: Los ingresos aumentan con crédito y disminuyen con débito.
        """
        if es_debito:
            return -monto  # Disminuye el ingreso
        else:
            return monto  # Aumenta el ingreso


class Gasto(Cuenta):
    """
    Clase que hereda de Cuenta para representar cuentas de Gasto.
    Implementa HERENCIA y POLIMORFISMO.
    """
    
    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
    
    def save(self, *args, **kwargs):
        self.tipo = TipoCuenta.GASTO
        self.naturaleza = 'DEBITO'
        super().save(*args, **kwargs)
    
    def registrar_movimiento(self, monto, es_debito):
        """
        Polimorfismo: Los gastos aumentan con débito y disminuyen con crédito.
        """
        if es_debito:
            return monto  # Aumenta el gasto
        else:
            return -monto  # Disminuye el gasto


class Costo(Cuenta):
    """
    Clase que hereda de Cuenta para representar cuentas de Costo.
    Implementa HERENCIA y POLIMORFISMO.
    """
    
    class Meta:
        verbose_name = "Costo"
        verbose_name_plural = "Costos"
    
    def save(self, *args, **kwargs):
        self.tipo = TipoCuenta.COSTO
        self.naturaleza = 'DEBITO'
        super().save(*args, **kwargs)
    
    def registrar_movimiento(self, monto, es_debito):
        """
        Polimorfismo: Los costos aumentan con débito y disminuyen con crédito.
        """
        if es_debito:
            return monto  # Aumenta el costo
        else:
            return -monto  # Disminuye el costo
