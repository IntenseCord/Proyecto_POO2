from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from empresa.models import Empresa
from cuentas.models import Cuenta
from transacciones.models import Comprobante, DetalleComprobante
from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard_view(request):
    """Vista principal del dashboard con estadísticas"""
    
    # Obtener estadísticas generales
    total_empresas = Empresa.objects.filter(activo=True).count()
    total_cuentas = Cuenta.objects.filter(activo=True).count()
    total_comprobantes = Comprobante.objects.filter(estado='APROBADO').count()
    
    # Calcular totales de débitos y créditos
    totales = DetalleComprobante.objects.filter(
        comprobante__estado='APROBADO'
    ).aggregate(
        total_debitos=Sum('debito'),
        total_creditos=Sum('credito')
    )
    
    # Comprobantes recientes
    comprobantes_recientes = Comprobante.objects.select_related('empresa').order_by('-fecha_creacion')[:5]
    
    # Comprobantes por tipo (para gráfico)
    comprobantes_por_tipo = Comprobante.objects.values('tipo').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Últimas empresas registradas
    empresas_recientes = Empresa.objects.filter(activo=True).order_by('-fecha_creacion')[:5]
    
    context = {
        'total_empresas': total_empresas,
        'total_cuentas': total_cuentas,
        'total_comprobantes': total_comprobantes,
        'total_debitos': totales['total_debitos'] or 0,
        'total_creditos': totales['total_creditos'] or 0,
        'comprobantes_recientes': comprobantes_recientes,
        'comprobantes_por_tipo': comprobantes_por_tipo,
        'empresas_recientes': empresas_recientes,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
