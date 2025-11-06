from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('descontinuado', 'Descontinuado'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True, help_text="Código único del producto")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cantidad disponible en inventario"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio por unidad"
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio de venta por unidad",
        default=Decimal('0.01')
    )
    stock_minimo = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        help_text="Cantidad mínima antes de alertar"
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def valor_total(self):
        """Calcula el valor total del inventario para este producto"""
        return self.cantidad * self.precio_unitario
    
    @property
    def necesita_restock(self):
        """Verifica si el producto necesita reabastecimiento"""
        return self.cantidad <= self.stock_minimo
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generar código automático si no se proporciona
            ultimo_producto = Producto.objects.all().order_by('id').last()
            if ultimo_producto:
                self.codigo = f"PROD{ultimo_producto.id + 1:04d}"
            else:
                self.codigo = "PROD0001"
        super().save(*args, **kwargs)

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=200)
    observaciones = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.tipo.title()} - {self.producto.nombre} - {self.cantidad}"
    
    def save(self, *args, **kwargs):
        """
        Guarda el movimiento y genera automáticamente comprobantes contables.
        - Entrada: Débito Inventario, Crédito Bancos/Proveedores
        - Salida: Débito Costo de Ventas, Crédito Inventario
        """
        es_nuevo = self.pk is None
        super().save(*args, **kwargs)
        
        # Generar comprobante contable solo para nuevos movimientos
        if es_nuevo and self.tipo in ['entrada', 'salida']:
            self._generar_comprobante_contable()
    
    def _generar_comprobante_contable(self):
        """Genera el comprobante contable automático para el movimiento"""
        try:
            from transacciones.models import Comprobante, DetalleComprobante, TipoComprobante
            from cuentas.models import Cuenta
            from empresa.models import Empresa
            from decimal import Decimal
            
            # Obtener la empresa (primera activa o del perfil del usuario)
            empresa = None
            if self.usuario and hasattr(self.usuario, 'perfil') and self.usuario.perfil.empresa:
                empresa = self.usuario.perfil.empresa
            else:
                empresa = Empresa.objects.filter(activo=True).first()
            
            if not empresa:
                return  # No se puede crear comprobante sin empresa
            
            # Valor del movimiento
            valor = Decimal(str(self.cantidad)) * self.producto.precio_unitario
            
            # Obtener o crear cuentas necesarias
            cuenta_inventario, _ = Cuenta.objects.get_or_create(
                empresa=empresa,
                codigo='1105',
                defaults={
                    'nombre': 'Inventario de Mercancías',
                    'tipo': 'A',
                    'naturaleza': 'DEBITO',
                    'acepta_movimiento': True,
                    'esta_activa': True,
                    'nivel': 2
                }
            )
            
            if self.tipo == 'entrada':
                # Entrada de inventario: Débito Inventario, Crédito Bancos
                cuenta_contrapartida, _ = Cuenta.objects.get_or_create(
                    empresa=empresa,
                    codigo='1110',
                    defaults={
                        'nombre': 'Bancos',
                        'tipo': 'A',
                        'naturaleza': 'DEBITO',
                        'acepta_movimiento': True,
                        'esta_activa': True,
                        'nivel': 2
                    }
                )
                
                # Crear comprobante de entrada
                comprobante = Comprobante.objects.create(
                    empresa=empresa,
                    tipo=TipoComprobante.INGRESO,
                    numero=Comprobante.objects.filter(empresa=empresa).count() + 1,
                    fecha=self.fecha.date(),
                    descripcion=f'Entrada de inventario: {self.producto.nombre} - {self.motivo}',
                    estado='BORRADOR',
                    total_debito=valor,
                    total_credito=valor,
                    usuario_creador=self.usuario
                )
                
                # Débito: Inventario (aumenta activo)
                DetalleComprobante.objects.create(
                    comprobante=comprobante,
                    cuenta=cuenta_inventario,
                    descripcion=f'Entrada: {self.producto.nombre} ({self.cantidad} unidades)',
                    debito=valor,
                    credito=Decimal('0.00'),
                    orden=1
                )
                
                # Crédito: Bancos (disminuye activo)
                DetalleComprobante.objects.create(
                    comprobante=comprobante,
                    cuenta=cuenta_contrapartida,
                    descripcion=f'Pago entrada inventario: {self.producto.nombre}',
                    debito=Decimal('0.00'),
                    credito=valor,
                    orden=2
                )
                
            elif self.tipo == 'salida':
                # Salida de inventario: Débito Costo de Ventas, Crédito Inventario
                cuenta_costo, _ = Cuenta.objects.get_or_create(
                    empresa=empresa,
                    codigo='6135',
                    defaults={
                        'nombre': 'Costo de Ventas',
                        'tipo': 'C',
                        'naturaleza': 'DEBITO',
                        'acepta_movimiento': True,
                        'esta_activa': True,
                        'nivel': 2
                    }
                )
                
                # Crear comprobante de egreso
                comprobante = Comprobante.objects.create(
                    empresa=empresa,
                    tipo=TipoComprobante.EGRESO,
                    numero=Comprobante.objects.filter(empresa=empresa).count() + 1,
                    fecha=self.fecha.date(),
                    descripcion=f'Salida de inventario: {self.producto.nombre} - {self.motivo}',
                    estado='BORRADOR',
                    total_debito=valor,
                    total_credito=valor,
                    usuario_creador=self.usuario
                )
                
                # Débito: Costo de Ventas (aumenta costo)
                DetalleComprobante.objects.create(
                    comprobante=comprobante,
                    cuenta=cuenta_costo,
                    descripcion=f'Costo salida: {self.producto.nombre} ({self.cantidad} unidades)',
                    debito=valor,
                    credito=Decimal('0.00'),
                    orden=1
                )
                
                # Crédito: Inventario (disminuye activo)
                DetalleComprobante.objects.create(
                    comprobante=comprobante,
                    cuenta=cuenta_inventario,
                    descripcion=f'Salida: {self.producto.nombre}',
                    debito=Decimal('0.00'),
                    credito=valor,
                    orden=2
                )
            
            # Aprobar el comprobante automáticamente
            comprobante.estado = 'APROBADO'
            comprobante.save()
            
        except Exception as e:
            # Log del error pero no interrumpir el guardado del movimiento
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al generar comprobante contable para movimiento de inventario: {e}')