"""
Módulo de Documentos Contables
Implementa ABSTRACCIÓN usando clases abstractas para documentos que generan asientos contables.
"""

from abc import ABC, abstractmethod
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from empresa.models import Empresa
from cuentas.models import Cuenta
from .models import Comprobante, DetalleComprobante


class DocumentoContable(ABC):
    """
    Clase abstracta base para todos los documentos contables.
    Implementa el patrón Template Method para generar asientos contables.
    
    Esta clase define la estructura común de todos los documentos que generan
    asientos contables automáticamente (Facturas, Notas de Crédito, etc.)
    """
    
    def __init__(self, empresa, fecha, descripcion):
        self.empresa = empresa
        self.fecha = fecha
        self.descripcion = descripcion
        self.items = []
    
    @abstractmethod
    def validar_documento(self):
        """
        Valida que el documento cumpla con las reglas de negocio.
        Debe ser implementado por cada tipo de documento.
        """
        pass
    
    @abstractmethod
    def obtener_cuentas_contables(self):
        """
        Retorna las cuentas contables que se usarán en el asiento.
        Debe ser implementado por cada tipo de documento.
        Retorna un diccionario con las cuentas necesarias.
        """
        pass
    
    @abstractmethod
    def calcular_totales(self):
        """
        Calcula los totales del documento.
        Debe ser implementado por cada tipo de documento.
        """
        pass
    
    def generar_asiento(self):
        """
        Método template que genera el asiento contable.
        Usa los métodos abstractos para personalizar el comportamiento.
        Este es el patrón TEMPLATE METHOD.
        """
        # 1. Validar el documento
        if not self.validar_documento():
            raise ValueError("El documento no es válido")
        
        # 2. Calcular totales
        totales = self.calcular_totales()
        
        # 3. Obtener cuentas contables
        cuentas = self.obtener_cuentas_contables()
        
        # 4. Crear el comprobante
        comprobante = Comprobante.objects.create(
            empresa=self.empresa,
            tipo=self.obtener_tipo_comprobante(),
            numero=self.generar_numero_comprobante(),
            fecha=self.fecha,
            descripcion=self.descripcion,
            estado='BORRADOR'
        )
        
        # 5. Crear los detalles del asiento
        self.crear_detalles_asiento(comprobante, cuentas, totales)
        
        # 6. Validar partida doble
        if comprobante.esta_balanceado():
            comprobante.estado = 'APROBADO'
            comprobante.save()
        else:
            comprobante.delete()
            raise ValueError("El asiento no está balanceado")
        
        return comprobante
    
    @abstractmethod
    def obtener_tipo_comprobante(self):
        """Retorna el tipo de comprobante según el documento"""
        pass
    
    @abstractmethod
    def crear_detalles_asiento(self, comprobante, cuentas, totales):
        """Crea los detalles del asiento contable"""
        pass
    
    def generar_numero_comprobante(self):
        """Genera un número único para el comprobante"""
        ultimo = Comprobante.objects.filter(empresa=self.empresa).order_by('-id').first()
        if ultimo and ultimo.numero:
            try:
                numero = int(ultimo.numero) + 1
                return str(numero).zfill(6)
            except ValueError:
                pass
        return "000001"
    
    def agregar_item(self, descripcion, cantidad, precio_unitario):
        """Agrega un item al documento"""
        self.items.append({
            'descripcion': descripcion,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'subtotal': cantidad * precio_unitario
        })


class FacturaVenta(DocumentoContable):
    """
    Factura de Venta
    Genera un asiento contable de venta:
    - DEBITO: Cuentas por Cobrar (o Caja/Banco)
    - CREDITO: Ingresos por Ventas
    """
    
    def __init__(self, empresa, fecha, descripcion, cliente, forma_pago='CREDITO'):
        super().__init__(empresa, fecha, descripcion)
        self.cliente = cliente
        self.forma_pago = forma_pago  # CREDITO o CONTADO
    
    def validar_documento(self):
        """Valida que la factura tenga items y totales válidos"""
        if not self.items:
            return False
        if not self.cliente:
            return False
        return True
    
    def obtener_cuentas_contables(self):
        """
        Obtiene las cuentas contables para una factura de venta.
        Polimorfismo: Diferentes cuentas según forma de pago.
        """
        cuentas = {}
        
        # Cuenta de débito (según forma de pago)
        if self.forma_pago == 'CONTADO':
            # Buscar cuenta de Caja
            cuentas['debito'] = Cuenta.objects.filter(
                empresa=self.empresa,
                codigo__startswith='1105',  # Caja
                esta_activa=True
            ).first()
        else:  # CREDITO
            # Buscar cuenta de Cuentas por Cobrar
            cuentas['debito'] = Cuenta.objects.filter(
                empresa=self.empresa,
                codigo__startswith='1305',  # Cuentas por Cobrar
                esta_activa=True
            ).first()
        
        # Cuenta de crédito (Ingresos por Ventas)
        cuentas['credito'] = Cuenta.objects.filter(
            empresa=self.empresa,
            codigo__startswith='4',  # Ingresos
            esta_activa=True
        ).first()
        
        if not cuentas['debito'] or not cuentas['credito']:
            raise ValueError("No se encontraron las cuentas contables necesarias")
        
        return cuentas
    
    def calcular_totales(self):
        """Calcula los totales de la factura"""
        subtotal = sum(item['subtotal'] for item in self.items)
        iva = subtotal * Decimal('0.19')  # 19% IVA
        total = subtotal + iva
        
        return {
            'subtotal': subtotal,
            'iva': iva,
            'total': total
        }
    
    def obtener_tipo_comprobante(self):
        return 'INGRESO'
    
    def crear_detalles_asiento(self, comprobante, cuentas, totales):
        """
        Crea los detalles del asiento contable para la factura.
        DEBITO: Cuentas por Cobrar (o Caja)
        CREDITO: Ingresos por Ventas
        """
        # Débito: Cuentas por Cobrar o Caja
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['debito'],
            debito=totales['total'],
            credito=Decimal('0.00'),
            descripcion=f"Venta a {self.cliente}"
        )
        
        # Crédito: Ingresos por Ventas
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['credito'],
            debito=Decimal('0.00'),
            credito=totales['total'],
            descripcion=f"Venta a {self.cliente}"
        )


class NotaCredito(DocumentoContable):
    """
    Nota de Crédito
    Genera un asiento contable que revierte una venta:
    - DEBITO: Devoluciones en Ventas (o Ingresos negativos)
    - CREDITO: Cuentas por Cobrar (o Caja/Banco)
    """
    
    def __init__(self, empresa, fecha, descripcion, cliente, factura_original=None):
        super().__init__(empresa, fecha, descripcion)
        self.cliente = cliente
        self.factura_original = factura_original
    
    def validar_documento(self):
        """Valida que la nota de crédito tenga items"""
        if not self.items:
            return False
        if not self.cliente:
            return False
        return True
    
    def obtener_cuentas_contables(self):
        """Obtiene las cuentas contables para una nota de crédito"""
        cuentas = {}
        
        # Cuenta de débito (Devoluciones en Ventas)
        cuentas['debito'] = Cuenta.objects.filter(
            empresa=self.empresa,
            codigo__startswith='4',  # Ingresos (se usará como devolución)
            esta_activa=True
        ).first()
        
        # Cuenta de crédito (Cuentas por Cobrar)
        cuentas['credito'] = Cuenta.objects.filter(
            empresa=self.empresa,
            codigo__startswith='1305',  # Cuentas por Cobrar
            esta_activa=True
        ).first()
        
        if not cuentas['debito'] or not cuentas['credito']:
            raise ValueError("No se encontraron las cuentas contables necesarias")
        
        return cuentas
    
    def calcular_totales(self):
        """Calcula los totales de la nota de crédito"""
        subtotal = sum(item['subtotal'] for item in self.items)
        iva = subtotal * Decimal('0.19')
        total = subtotal + iva
        
        return {
            'subtotal': subtotal,
            'iva': iva,
            'total': total
        }
    
    def obtener_tipo_comprobante(self):
        return 'EGRESO'
    
    def crear_detalles_asiento(self, comprobante, cuentas, totales):
        """
        Crea los detalles del asiento contable para la nota de crédito.
        DEBITO: Devoluciones en Ventas
        CREDITO: Cuentas por Cobrar
        """
        # Débito: Devoluciones en Ventas
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['debito'],
            debito=totales['total'],
            credito=Decimal('0.00'),
            descripcion=f"Nota de Crédito - {self.cliente}"
        )
        
        # Crédito: Cuentas por Cobrar
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['credito'],
            debito=Decimal('0.00'),
            credito=totales['total'],
            descripcion=f"Nota de Crédito - {self.cliente}"
        )


class FacturaCompra(DocumentoContable):
    """
    Factura de Compra
    Genera un asiento contable de compra:
    - DEBITO: Inventario (o Gastos)
    - CREDITO: Cuentas por Pagar (o Caja/Banco)
    """
    
    def __init__(self, empresa, fecha, descripcion, proveedor, forma_pago='CREDITO'):
        super().__init__(empresa, fecha, descripcion)
        self.proveedor = proveedor
        self.forma_pago = forma_pago
    
    def validar_documento(self):
        """Valida que la factura de compra tenga items"""
        if not self.items:
            return False
        if not self.proveedor:
            return False
        return True
    
    def obtener_cuentas_contables(self):
        """Obtiene las cuentas contables para una factura de compra"""
        cuentas = {}
        
        # Cuenta de débito (Inventario o Gastos)
        cuentas['debito'] = Cuenta.objects.filter(
            empresa=self.empresa,
            codigo__startswith='14',  # Inventarios
            esta_activa=True
        ).first()
        
        # Cuenta de crédito (según forma de pago)
        if self.forma_pago == 'CONTADO':
            cuentas['credito'] = Cuenta.objects.filter(
                empresa=self.empresa,
                codigo__startswith='1105',  # Caja
                esta_activa=True
            ).first()
        else:  # CREDITO
            cuentas['credito'] = Cuenta.objects.filter(
                empresa=self.empresa,
                codigo__startswith='2',  # Cuentas por Pagar
                esta_activa=True
            ).first()
        
        if not cuentas['debito'] or not cuentas['credito']:
            raise ValueError("No se encontraron las cuentas contables necesarias")
        
        return cuentas
    
    def calcular_totales(self):
        """Calcula los totales de la factura de compra"""
        subtotal = sum(item['subtotal'] for item in self.items)
        iva = subtotal * Decimal('0.19')
        total = subtotal + iva
        
        return {
            'subtotal': subtotal,
            'iva': iva,
            'total': total
        }
    
    def obtener_tipo_comprobante(self):
        return 'EGRESO'
    
    def crear_detalles_asiento(self, comprobante, cuentas, totales):
        """
        Crea los detalles del asiento contable para la factura de compra.
        DEBITO: Inventario
        CREDITO: Cuentas por Pagar (o Caja)
        """
        # Débito: Inventario
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['debito'],
            debito=totales['total'],
            credito=Decimal('0.00'),
            descripcion=f"Compra a {self.proveedor}"
        )
        
        # Crédito: Cuentas por Pagar o Caja
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['credito'],
            debito=Decimal('0.00'),
            credito=totales['total'],
            descripcion=f"Compra a {self.proveedor}"
        )


class ReciboCaja(DocumentoContable):
    """
    Recibo de Caja
    Genera un asiento contable de recaudo:
    - DEBITO: Caja o Banco
    - CREDITO: Cuentas por Cobrar
    """
    
    def __init__(self, empresa, fecha, descripcion, cliente, monto, forma_pago='EFECTIVO'):
        super().__init__(empresa, fecha, descripcion)
        self.cliente = cliente
        self.monto = monto
        self.forma_pago = forma_pago  # EFECTIVO, CHEQUE, TRANSFERENCIA
    
    def validar_documento(self):
        """Valida que el recibo tenga un monto válido"""
        if self.monto <= 0:
            return False
        if not self.cliente:
            return False
        return True
    
    def obtener_cuentas_contables(self):
        """Obtiene las cuentas contables para un recibo de caja"""
        cuentas = {}
        
        # Cuenta de débito (Caja o Banco según forma de pago)
        if self.forma_pago == 'EFECTIVO':
            cuentas['debito'] = Cuenta.objects.filter(
                empresa=self.empresa,
                codigo__startswith='1105',  # Caja
                esta_activa=True
            ).first()
        else:  # CHEQUE o TRANSFERENCIA
            cuentas['debito'] = Cuenta.objects.filter(
                empresa=self.empresa,
                codigo__startswith='1110',  # Bancos
                esta_activa=True
            ).first()
        
        # Cuenta de crédito (Cuentas por Cobrar)
        cuentas['credito'] = Cuenta.objects.filter(
            empresa=self.empresa,
            codigo__startswith='1305',  # Cuentas por Cobrar
            esta_activa=True
        ).first()
        
        if not cuentas['debito'] or not cuentas['credito']:
            raise ValueError("No se encontraron las cuentas contables necesarias")
        
        return cuentas
    
    def calcular_totales(self):
        """Retorna el monto del recibo"""
        return {
            'total': self.monto
        }
    
    def obtener_tipo_comprobante(self):
        return 'INGRESO'
    
    def crear_detalles_asiento(self, comprobante, cuentas, totales):
        """
        Crea los detalles del asiento contable para el recibo de caja.
        DEBITO: Caja o Banco
        CREDITO: Cuentas por Cobrar
        """
        # Débito: Caja o Banco
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['debito'],
            debito=totales['total'],
            credito=Decimal('0.00'),
            descripcion=f"Recibo de {self.cliente} - {self.forma_pago}"
        )
        
        # Crédito: Cuentas por Cobrar
        DetalleComprobante.objects.create(
            comprobante=comprobante,
            cuenta=cuentas['credito'],
            debito=Decimal('0.00'),
            credito=totales['total'],
            descripcion=f"Recibo de {self.cliente} - {self.forma_pago}"
        )
