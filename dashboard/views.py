from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from empresa.models import Empresa
from cuentas.models import Cuenta
from transacciones.models import Comprobante, DetalleComprobante
from inventario.models import Producto, Categoria, MovimientoInventario
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

def get_admin_statistics():
    """Obtiene estadísticas generales del sistema para administradores"""
    return {
        'total_empresas': Empresa.objects.filter(activo=True).count(),
        'total_cuentas': Cuenta.objects.filter(esta_activa=True).count(),
        'total_comprobantes': Comprobante.objects.filter(estado='APROBADO').count(),
    }


def get_admin_totals():
    """Calcula totales de débitos y créditos para administradores"""
    return DetalleComprobante.objects.filter(
        comprobante__estado='APROBADO'
    ).aggregate(
        total_debitos=Sum('debito'),
        total_creditos=Sum('credito')
    )


def get_inventory_statistics():
    """Obtiene estadísticas de inventario"""
    total_productos = Producto.objects.filter(estado='activo').count()
    total_categorias = Categoria.objects.count()
    productos_bajo_stock = Producto.objects.filter(
        cantidad__lte=F('stock_minimo'),
        estado='activo'
    ).count()
    
    valor_inventario = Producto.objects.filter(estado='activo').aggregate(
        total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('precio_unitario'),
                output_field=DecimalField()
            )
        )
    )['total'] or Decimal('0.00')
    
    return {
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'productos_bajo_stock': productos_bajo_stock,
        'valor_inventario': valor_inventario,
    }


def get_user_statistics():
    """Obtiene estadísticas de usuarios para administradores"""
    return {
        'total_usuarios': User.objects.filter(is_active=True).count(),
        'usuarios_admin': User.objects.filter(is_superuser=True, is_active=True).count(),
    }


def get_recent_data(es_admin):
    """Obtiene datos recientes según el tipo de usuario"""
    if es_admin:
        return {
            'comprobantes_recientes': Comprobante.objects.select_related('empresa').order_by('-fecha_creacion')[:5],
            'empresas_recientes': Empresa.objects.filter(activo=True).order_by('-fecha_creacion')[:5],
        }
    return {
        'comprobantes_recientes': [],
        'empresas_recientes': [],
    }


def get_chart_data(es_admin):
    """Obtiene datos para gráficos"""
    comprobantes_por_tipo = []
    if es_admin:
        comprobantes_por_tipo = Comprobante.objects.values('tipo').annotate(
            total=Count('id')
        ).order_by('-total')
    
    productos_por_categoria = Producto.objects.filter(
        estado='activo',
        categoria__isnull=False
    ).values(
        'categoria__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    movimientos_por_tipo = MovimientoInventario.objects.values('tipo').annotate(
        total=Count('id'),
        cantidad_total=Sum('cantidad')
    ).order_by('tipo')
    
    return {
        'comprobantes_por_tipo': comprobantes_por_tipo,
        'productos_por_categoria': productos_por_categoria,
        'movimientos_por_tipo': movimientos_por_tipo,
    }


def get_inventory_movements():
    """Obtiene movimientos de inventario recientes y de los últimos 7 días"""
    movimientos_recientes = MovimientoInventario.objects.select_related(
        'producto', 'usuario'
    ).order_by('-fecha')[:5]
    
    productos_restock = Producto.objects.filter(
        cantidad__lte=F('stock_minimo'),
        estado='activo'
    ).order_by('cantidad')[:5]
    
    fecha_hace_7_dias = timezone.now() - timedelta(days=7)
    movimientos_ultimos_7_dias = MovimientoInventario.objects.filter(
        fecha__gte=fecha_hace_7_dias
    ).extra(
        select={'fecha_dia': 'DATE(fecha)'}
    ).values('fecha_dia', 'tipo').annotate(
        total=Count('id')
    ).order_by('fecha_dia')
    
    return {
        'movimientos_recientes': movimientos_recientes,
        'productos_restock': productos_restock,
        'movimientos_ultimos_7_dias': movimientos_ultimos_7_dias,
    }


def get_monthly_financial_data(es_admin):
    """Calcula datos financieros del mes actual"""
    fecha_inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    ingresos_mes = MovimientoInventario.objects.filter(
        tipo='entrada',
        fecha__gte=fecha_inicio_mes
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto__precio_unitario'),
                output_field=DecimalField()
            )
        )
    )['total'] or Decimal('0.00')
    
    egresos_mes = MovimientoInventario.objects.filter(
        tipo='salida',
        fecha__gte=fecha_inicio_mes
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto__precio_unitario'),
                output_field=DecimalField()
            )
        )
    )['total'] or Decimal('0.00')
    
    utilidad_mes = ingresos_mes - egresos_mes
    
    if es_admin:
        cuentas_por_cobrar = DetalleComprobante.objects.filter(
            comprobante__estado='APROBADO',
            comprobante__tipo='VENTA'
        ).aggregate(total=Sum('debito'))['total'] or Decimal('0.00')
        
        cuentas_por_pagar = DetalleComprobante.objects.filter(
            comprobante__estado='APROBADO',
            comprobante__tipo='COMPRA'
        ).aggregate(total=Sum('credito'))['total'] or Decimal('0.00')
    else:
        cuentas_por_cobrar = Decimal('0.00')
        cuentas_por_pagar = Decimal('0.00')
    
    return {
        'ingresos_mes': ingresos_mes,
        'egresos_mes': egresos_mes,
        'utilidad_mes': utilidad_mes,
        'cuentas_por_cobrar': cuentas_por_cobrar,
        'cuentas_por_pagar': cuentas_por_pagar,
    }


@login_required
@never_cache
@require_GET
def dashboard_view(request):
    """Vista principal del dashboard con estadísticas personalizadas según el usuario"""
    es_admin = request.user.is_superuser
    
    # Obtener estadísticas según el tipo de usuario
    if es_admin:
        admin_stats = get_admin_statistics()
        totales = get_admin_totals()
        user_stats = get_user_statistics()
    else:
        admin_stats = {'total_empresas': 0, 'total_cuentas': 0, 'total_comprobantes': 0}
        totales = {'total_debitos': 0, 'total_creditos': 0}
        user_stats = {'total_usuarios': 0, 'usuarios_admin': 0}
    
    # Obtener todas las estadísticas usando funciones auxiliares
    inventory_stats = get_inventory_statistics()
    recent_data = get_recent_data(es_admin)
    chart_data = get_chart_data(es_admin)
    inventory_movements = get_inventory_movements()
    financial_data = get_monthly_financial_data(es_admin)
    
    # Construir contexto combinando todos los datos
    context = {
        'es_admin': es_admin,
        **admin_stats,
        'total_debitos': totales['total_debitos'] or 0,
        'total_creditos': totales['total_creditos'] or 0,
        **inventory_stats,
        **user_stats,
        **recent_data,
        **chart_data,
        **inventory_movements,
        **financial_data,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
