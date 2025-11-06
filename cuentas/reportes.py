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
    
    def __init__(self, empresa, fecha_inicio=None, fecha_fin=None, tipo_cuenta=None):
        super().__init__(empresa, fecha_inicio, fecha_fin)
        self.tipo_cuenta = tipo_cuenta
    
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
        )
        
        # Filtrar por tipo de cuenta si se especifica
        if self.tipo_cuenta:
            cuentas = cuentas.filter(tipo=self.tipo_cuenta)
        
        cuentas = cuentas.order_by('codigo')
        
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

        cuentas_activo = Cuenta.objects.filter(
            empresa=self.empresa, tipo=TipoCuenta.ACTIVO, esta_activa=True
        ).order_by('codigo')
        cuentas_pasivo = Cuenta.objects.filter(
            empresa=self.empresa, tipo=TipoCuenta.PASIVO, esta_activa=True
        ).order_by('codigo')
        cuentas_patrimonio = Cuenta.objects.filter(
            empresa=self.empresa, tipo=TipoCuenta.PATRIMONIO, esta_activa=True
        ).order_by('codigo')

        activos, total_activos = self._agrupar_por_tipo(movimientos, cuentas_activo, 'DEBITO')
        activos, total_activos = self._integrar_inventario(activos, total_activos)
        pasivos, total_pasivos = self._agrupar_por_tipo(movimientos, cuentas_pasivo, 'CREDITO')
        patrimonios, total_patrimonio = self._agrupar_por_tipo(movimientos, cuentas_patrimonio, 'CREDITO')

        utilidad_periodo = self._obtener_utilidad_periodo()
        total_patrimonio_con_utilidad = total_patrimonio + utilidad_periodo

        total_pasivo_patrimonio = total_pasivos + total_patrimonio_con_utilidad
        ecuacion_balanceada = abs(total_activos - total_pasivo_patrimonio) < Decimal('0.01')

        activos_clasificados = self._clasificar_activos(activos)
        pasivos_clasificados = self._clasificar_pasivos(pasivos)

        ratios = self._calcular_ratios_financieros(
            activos_clasificados,
            pasivos_clasificados,
            total_activos,
            total_pasivos,
            total_patrimonio_con_utilidad,
        )

        datos_graficos = self._preparar_datos_graficos(
            activos, pasivos, patrimonios, total_activos, total_pasivos, total_patrimonio_con_utilidad
        )

        return {
            'empresa': self.empresa,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'activos': activos,
            'pasivos': pasivos,
            'patrimonios': patrimonios,
            'activos_clasificados': activos_clasificados,
            'pasivos_clasificados': pasivos_clasificados,
            'utilidad_periodo': utilidad_periodo,
            'totales': {
                'activos': total_activos,
                'pasivos': total_pasivos,
                'patrimonio': total_patrimonio,
                'patrimonio_con_utilidad': total_patrimonio_con_utilidad,
                'pasivo_patrimonio': total_pasivo_patrimonio,
            },
            'ecuacion_balanceada': ecuacion_balanceada,
            'diferencia': total_activos - total_pasivo_patrimonio,
            'ratios': ratios,
            'datos_graficos': datos_graficos,
        }

    def _agrupar_por_tipo(self, movimientos, cuentas_qs, naturaleza):
        """Crea la lista de cuentas y total según naturaleza 'DEBITO' o 'CREDITO'."""
        lista = []
        total = Decimal('0.00')
        for cuenta in cuentas_qs:
            movs = movimientos.filter(cuenta=cuenta).aggregate(
                debito=Sum('debito'), credito=Sum('credito')
            )
            debito = movs['debito'] or Decimal('0.00')
            credito = movs['credito'] or Decimal('0.00')
            saldo = (debito - credito) if naturaleza == 'DEBITO' else (credito - debito)
            if saldo != 0:
                lista.append({'cuenta': cuenta, 'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'monto': saldo})
                total += saldo
        return lista, total

    def _integrar_inventario(self, activos, total_activos):
        """Integra inventario físico si no hay registro contable en activos."""
        try:
            from inventario.models import Producto
            cuenta_inventario_existe = any(a['codigo'] == '1105' for a in activos)
            if not cuenta_inventario_existe:
                productos_activos = Producto.objects.filter(estado='activo')
                valor_inventario = sum([p.cantidad * p.precio_unitario for p in productos_activos])
                if valor_inventario > 0:
                    cuenta_inventario, _ = Cuenta.objects.get_or_create(
                        empresa=self.empresa,
                        codigo='1105',
                        defaults={
                            'nombre': 'Inventario de Mercancías',
                            'tipo': TipoCuenta.ACTIVO,
                            'naturaleza': 'DEBITO',
                            'acepta_movimiento': True,
                            'esta_activa': True,
                            'nivel': 2,
                        },
                    )
                    activos.append({
                        'cuenta': cuenta_inventario,
                        'codigo': cuenta_inventario.codigo,
                        'nombre': cuenta_inventario.nombre + ' (Físico)',
                        'monto': Decimal(str(valor_inventario)),
                    })
                    total_activos += Decimal(str(valor_inventario))
        except ImportError:
            pass
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f'Error al calcular inventario para balance general: {e}'
            )
        return activos, total_activos

    def _obtener_utilidad_periodo(self):
        """Calcula la utilidad neta del período desde el Estado de Resultados."""
        estado_resultados = EstadoResultados(self.empresa, self.fecha_inicio, self.fecha_fin)
        resultado = estado_resultados.generar()
        return resultado['totales']['utilidad_neta']
    
    def _clasificar_activos(self, activos):
        """Clasifica los activos en corrientes y no corrientes"""
        from .models import Activo
        
        corrientes = []
        no_corrientes = []
        total_corrientes = Decimal('0.00')
        total_no_corrientes = Decimal('0.00')
        
        for activo in activos:
            cuenta = activo['cuenta']
            # Verificar si es un Activo con campo es_corriente
            es_corriente = False
            if hasattr(cuenta, 'activo'):
                es_corriente = cuenta.activo.es_corriente
            
            if es_corriente:
                corrientes.append(activo)
                total_corrientes += activo['monto']
            else:
                no_corrientes.append(activo)
                total_no_corrientes += activo['monto']
        
        return {
            'corrientes': corrientes,
            'no_corrientes': no_corrientes,
            'total_corrientes': total_corrientes,
            'total_no_corrientes': total_no_corrientes,
        }
    
    def _clasificar_pasivos(self, pasivos):
        """Clasifica los pasivos en corrientes y no corrientes"""
        from .models import Pasivo
        
        corrientes = []
        no_corrientes = []
        total_corrientes = Decimal('0.00')
        total_no_corrientes = Decimal('0.00')
        
        for pasivo in pasivos:
            cuenta = pasivo['cuenta']
            # Verificar si es un Pasivo con campo es_corriente
            es_corriente = False
            if hasattr(cuenta, 'pasivo'):
                es_corriente = cuenta.pasivo.es_corriente
            
            if es_corriente:
                corrientes.append(pasivo)
                total_corrientes += pasivo['monto']
            else:
                no_corrientes.append(pasivo)
                total_no_corrientes += pasivo['monto']
        
        return {
            'corrientes': corrientes,
            'no_corrientes': no_corrientes,
            'total_corrientes': total_corrientes,
            'total_no_corrientes': total_no_corrientes,
        }
    
    def _calcular_ratios_financieros(self, activos_clasificados, pasivos_clasificados, total_activos, total_pasivos, total_patrimonio):
        """Calcula los ratios financieros principales"""
        ratios = {}
        
        # Ratio de Liquidez Corriente = Activo Corriente / Pasivo Corriente
        if pasivos_clasificados['total_corrientes'] > 0:
            ratios['liquidez_corriente'] = activos_clasificados['total_corrientes'] / pasivos_clasificados['total_corrientes']
        else:
            ratios['liquidez_corriente'] = Decimal('0.00')
        
        # Capital de Trabajo = Activo Corriente - Pasivo Corriente
        ratios['capital_trabajo'] = activos_clasificados['total_corrientes'] - pasivos_clasificados['total_corrientes']
        
        # Ratio de Endeudamiento = (Pasivo Total / Activo Total) * 100
        if total_activos > 0:
            ratios['endeudamiento'] = (total_pasivos / total_activos) * 100
        else:
            ratios['endeudamiento'] = Decimal('0.00')
        
        # Ratio de Solvencia = (Patrimonio / Activo Total) * 100
        if total_activos > 0:
            ratios['solvencia'] = (total_patrimonio / total_activos) * 100
        else:
            ratios['solvencia'] = Decimal('0.00')
        
        # Ratio de Autonomía Financiera = Patrimonio / Pasivo Total
        if total_pasivos > 0:
            ratios['autonomia_financiera'] = total_patrimonio / total_pasivos
        else:
            ratios['autonomia_financiera'] = Decimal('0.00')
        
        return ratios
    
    def _preparar_datos_graficos(self, activos, pasivos, patrimonios, total_activos, total_pasivos, total_patrimonio):
        """Prepara los datos para los gráficos Chart.js"""
        
        # Top 5 activos más grandes
        activos_top = sorted(activos, key=lambda x: x['monto'], reverse=True)[:5]
        
        # Top 5 pasivos más grandes
        pasivos_top = sorted(pasivos, key=lambda x: x['monto'], reverse=True)[:5]
        
        return {
            'activos_labels': [a['nombre'][:30] for a in activos_top],
            'activos_valores': [float(a['monto']) for a in activos_top],
            'pasivos_labels': [p['nombre'][:30] for p in pasivos_top],
            'pasivos_valores': [float(p['monto']) for p in pasivos_top],
            'comparativo_labels': ['Activos', 'Pasivos', 'Patrimonio'],
            'comparativo_valores': [float(total_activos), float(total_pasivos), float(total_patrimonio)],
        }
