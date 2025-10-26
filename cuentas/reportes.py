"""
Módulo de Reportes Financieros
Implementa los reportes contables principales:
- Balance de Comprobación
- Estado de Resultados
- Balance General
"""

from django.db.models import Sum, Q
from decimal import Decimal
from .models import Cuenta, TipoCuenta
from transacciones.models import DetalleComprobante
from datetime import datetime


def _determinar_resultado(monto):
    """Helper: Determina si el resultado es UTILIDAD, PÉRDIDA o EQUILIBRIO"""
    if monto > 0:
        return 'UTILIDAD'
    elif monto < 0:
        return 'PÉRDIDA'
    else:
        return 'EQUILIBRIO'


def _calcular_saldos_por_naturaleza(debito, credito, naturaleza):
    """Helper: Calcula saldo deudor y acreedor según naturaleza de la cuenta"""
    if naturaleza == 'DEBITO':
        saldo = debito - credito
        saldo_deudor = saldo if saldo > 0 else Decimal('0.00')
        saldo_acreedor = abs(saldo) if saldo < 0 else Decimal('0.00')
    else:  # CREDITO
        saldo = credito - debito
        saldo_acreedor = saldo if saldo > 0 else Decimal('0.00')
        saldo_deudor = abs(saldo) if saldo < 0 else Decimal('0.00')
    
    return saldo_deudor, saldo_acreedor


class ReporteFinanciero:
    """
    Clase base para reportes financieros.
    Implementa ABSTRACCIÓN y proporciona métodos comunes.
    """
    
    def __init__(self, empresa, fecha_inicio=None, fecha_fin=None):
        self.empresa = empresa
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
    
    def obtener_movimientos(self):
        """Obtiene los movimientos filtrados por fecha y empresa"""
        movimientos = DetalleComprobante.objects.filter(
            comprobante__empresa=self.empresa,
            comprobante__estado='APROBADO'
        )
        
        if self.fecha_inicio:
            movimientos = movimientos.filter(comprobante__fecha__gte=self.fecha_inicio)
        
        if self.fecha_fin:
            movimientos = movimientos.filter(comprobante__fecha__lte=self.fecha_fin)
        
        return movimientos
    
    def generar(self):
        """Método abstracto que debe ser implementado por las subclases"""
        raise NotImplementedError("Este método debe ser implementado por las subclases")


class BalanceComprobacion(ReporteFinanciero):
    """
    Balance de Comprobación
    Muestra todas las cuentas con sus débitos, créditos y saldos.
    """
    
    def generar(self):
        """
        Genera el Balance de Comprobación.
        Retorna un diccionario con las cuentas y sus totales.
        """
        movimientos = self.obtener_movimientos()
        
        # Obtener todas las cuentas activas de la empresa
        cuentas = Cuenta.objects.filter(
            empresa=self.empresa,
            esta_activa=True,
            acepta_movimiento=True
        ).order_by('codigo')
        
        datos = []
        total_debitos = Decimal('0.00')
        total_creditos = Decimal('0.00')
        total_saldo_deudor = Decimal('0.00')
        total_saldo_acreedor = Decimal('0.00')
        
        for cuenta in cuentas:
            # Calcular totales de la cuenta
            movimientos_cuenta = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'),
                credito=Sum('credito')
            )
            
            debito = movimientos_cuenta['debito'] or Decimal('0.00')
            credito = movimientos_cuenta['credito'] or Decimal('0.00')
            
            # Calcular saldo según la naturaleza de la cuenta
            saldo_deudor, saldo_acreedor = _calcular_saldos_por_naturaleza(
                debito, credito, cuenta.naturaleza
            )
            
            # Solo incluir cuentas con movimiento
            if debito > 0 or credito > 0:
                datos.append({
                    'cuenta': cuenta,
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'debito': debito,
                    'credito': credito,
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor,
                })
                
                total_debitos += debito
                total_creditos += credito
                total_saldo_deudor += saldo_deudor
                total_saldo_acreedor += saldo_acreedor
        
        return {
            'empresa': self.empresa,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'cuentas': datos,
            'totales': {
                'debitos': total_debitos,
                'creditos': total_creditos,
                'saldo_deudor': total_saldo_deudor,
                'saldo_acreedor': total_saldo_acreedor,
            },
            'esta_balanceado': total_debitos == total_creditos and total_saldo_deudor == total_saldo_acreedor
        }


class EstadoResultados(ReporteFinanciero):
    """
    Estado de Resultados (Estado de Pérdidas y Ganancias)
    Muestra Ingresos - Gastos = Utilidad/Pérdida
    """
    
    def generar(self):
        """
        Genera el Estado de Resultados.
        Retorna ingresos, gastos, costos y utilidad/pérdida.
        """
        movimientos = self.obtener_movimientos()
        
        # Obtener cuentas de Ingresos
        cuentas_ingreso = Cuenta.objects.filter(
            empresa=self.empresa,
            tipo=TipoCuenta.INGRESO,
            esta_activa=True
        ).order_by('codigo')
        
        # Obtener cuentas de Gastos
        cuentas_gasto = Cuenta.objects.filter(
            empresa=self.empresa,
            tipo=TipoCuenta.GASTO,
            esta_activa=True
        ).order_by('codigo')
        
        # Obtener cuentas de Costos
        cuentas_costo = Cuenta.objects.filter(
            empresa=self.empresa,
            tipo=TipoCuenta.COSTO,
            esta_activa=True
        ).order_by('codigo')
        
        # Calcular Ingresos
        ingresos = []
        total_ingresos = Decimal('0.00')
        
        for cuenta in cuentas_ingreso:
            movimientos_cuenta = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'),
                credito=Sum('credito')
            )
            
            debito = movimientos_cuenta['debito'] or Decimal('0.00')
            credito = movimientos_cuenta['credito'] or Decimal('0.00')
            saldo = credito - debito  # Los ingresos tienen naturaleza crédito
            
            if saldo != 0:
                ingresos.append({
                    'cuenta': cuenta,
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'monto': saldo
                })
                total_ingresos += saldo
        
        # Calcular Costos
        costos = []
        total_costos = Decimal('0.00')
        
        for cuenta in cuentas_costo:
            movimientos_cuenta = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'),
                credito=Sum('credito')
            )
            
            debito = movimientos_cuenta['debito'] or Decimal('0.00')
            credito = movimientos_cuenta['credito'] or Decimal('0.00')
            saldo = debito - credito  # Los costos tienen naturaleza débito
            
            if saldo != 0:
                costos.append({
                    'cuenta': cuenta,
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'monto': saldo
                })
                total_costos += saldo
        
        # Calcular Gastos
        gastos = []
        total_gastos = Decimal('0.00')
        
        for cuenta in cuentas_gasto:
            movimientos_cuenta = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'),
                credito=Sum('credito')
            )
            
            debito = movimientos_cuenta['debito'] or Decimal('0.00')
            credito = movimientos_cuenta['credito'] or Decimal('0.00')
            saldo = debito - credito  # Los gastos tienen naturaleza débito
            
            if saldo != 0:
                gastos.append({
                    'cuenta': cuenta,
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'monto': saldo
                })
                total_gastos += saldo
        
        # Calcular Utilidad Bruta y Neta
        utilidad_bruta = total_ingresos - total_costos
        utilidad_neta = utilidad_bruta - total_gastos
        
        return {
            'empresa': self.empresa,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'ingresos': ingresos,
            'costos': costos,
            'gastos': gastos,
            'totales': {
                'ingresos': total_ingresos,
                'costos': total_costos,
                'gastos': total_gastos,
                'utilidad_bruta': utilidad_bruta,
                'utilidad_neta': utilidad_neta,
            },
            'resultado': _determinar_resultado(utilidad_neta)
        }


class BalanceGeneral(ReporteFinanciero):
    """
    Balance General (Estado de Situación Financiera)
    Muestra: Activos = Pasivos + Patrimonio
    """
    
    def generar(self):
        """
        Genera el Balance General.
        Retorna activos, pasivos, patrimonio y verifica la ecuación contable.
        """
        movimientos = self.obtener_movimientos()
        
        # Obtener cuentas de Activos
        cuentas_activo = Cuenta.objects.filter(
            empresa=self.empresa,
            tipo=TipoCuenta.ACTIVO,
            esta_activa=True
        ).order_by('codigo')
        
        # Obtener cuentas de Pasivos
        cuentas_pasivo = Cuenta.objects.filter(
            empresa=self.empresa,
            tipo=TipoCuenta.PASIVO,
            esta_activa=True
        ).order_by('codigo')
        
        # Obtener cuentas de Patrimonio
        cuentas_patrimonio = Cuenta.objects.filter(
            empresa=self.empresa,
            tipo=TipoCuenta.PATRIMONIO,
            esta_activa=True
        ).order_by('codigo')
        
        # Calcular Activos
        activos = []
        total_activos = Decimal('0.00')
        
        for cuenta in cuentas_activo:
            movimientos_cuenta = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'),
                credito=Sum('credito')
            )
            
            debito = movimientos_cuenta['debito'] or Decimal('0.00')
            credito = movimientos_cuenta['credito'] or Decimal('0.00')
            saldo = debito - credito  # Los activos tienen naturaleza débito
            
            if saldo != 0:
                activos.append({
                    'cuenta': cuenta,
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'monto': saldo
                })
                total_activos += saldo
        
        # Calcular Pasivos
        pasivos = []
        total_pasivos = Decimal('0.00')
        
        for cuenta in cuentas_pasivo:
            movimientos_cuenta = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'),
                credito=Sum('credito')
            )
            
            debito = movimientos_cuenta['debito'] or Decimal('0.00')
            credito = movimientos_cuenta['credito'] or Decimal('0.00')
            saldo = credito - debito  # Los pasivos tienen naturaleza crédito
            
            if saldo != 0:
                pasivos.append({
                    'cuenta': cuenta,
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'monto': saldo
                })
                total_pasivos += saldo
        
        # Calcular Patrimonio
        patrimonios = []
        total_patrimonio = Decimal('0.00')
        
        for cuenta in cuentas_patrimonio:
            movimientos_cuenta = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'),
                credito=Sum('credito')
            )
            
            debito = movimientos_cuenta['debito'] or Decimal('0.00')
            credito = movimientos_cuenta['credito'] or Decimal('0.00')
            saldo = credito - debito  # El patrimonio tiene naturaleza crédito
            
            if saldo != 0:
                patrimonios.append({
                    'cuenta': cuenta,
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'monto': saldo
                })
                total_patrimonio += saldo
        
        # Calcular utilidad del período (si aplica)
        estado_resultados = EstadoResultados(self.empresa, self.fecha_inicio, self.fecha_fin)
        resultado = estado_resultados.generar()
        utilidad_periodo = resultado['totales']['utilidad_neta']
        
        # El patrimonio total incluye la utilidad del período
        total_patrimonio_con_utilidad = total_patrimonio + utilidad_periodo
        
        # Verificar ecuación contable: Activos = Pasivos + Patrimonio
        total_pasivo_patrimonio = total_pasivos + total_patrimonio_con_utilidad
        ecuacion_balanceada = abs(total_activos - total_pasivo_patrimonio) < Decimal('0.01')
        
        return {
            'empresa': self.empresa,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'activos': activos,
            'pasivos': pasivos,
            'patrimonios': patrimonios,
            'utilidad_periodo': utilidad_periodo,
            'totales': {
                'activos': total_activos,
                'pasivos': total_pasivos,
                'patrimonio': total_patrimonio,
                'patrimonio_con_utilidad': total_patrimonio_con_utilidad,
                'pasivo_patrimonio': total_pasivo_patrimonio,
            },
            'ecuacion_balanceada': ecuacion_balanceada,
            'diferencia': total_activos - total_pasivo_patrimonio
        }
