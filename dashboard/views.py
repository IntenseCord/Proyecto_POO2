from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from empresa.models import Empresa
from cuentas.models import Cuenta
from transacciones.models import Comprobante, DetalleComprobante
from inventario.models import Producto, Categoria, MovimientoInventario
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

@login_required
@never_cache
def dashboard_view(request):
    """Vista principal del dashboard con estadísticas personalizadas según el usuario"""
    
    # Verificar si es administrador
    es_admin = request.user.is_superuser
    
    # Obtener estadísticas generales (solo admin ve todo el sistema)
    if es_admin:
        total_empresas = Empresa.objects.filter(activo=True).count()
        total_cuentas = Cuenta.objects.filter(esta_activa=True).count()
        total_comprobantes = Comprobante.objects.filter(estado='APROBADO').count()
    else:
        # Usuarios normales: estadísticas limitadas o de su empresa
        total_empresas = 0  # No ven empresas
        total_cuentas = 0   # No ven plan de cuentas completo
        total_comprobantes = 0  # No ven comprobantes
    
    # Calcular totales de débitos y créditos (solo admin)
    if es_admin:
        totales = DetalleComprobante.objects.filter(
            comprobante__estado='APROBADO'
        ).aggregate(
            total_debitos=Sum('debito'),
            total_creditos=Sum('credito')
        )
    else:
        totales = {'total_debitos': 0, 'total_creditos': 0}
    
    # Estadísticas de inventario (todos los usuarios)
    total_productos = Producto.objects.filter(estado='activo').count()
    total_categorias = Categoria.objects.count()
    productos_bajo_stock = Producto.objects.filter(
        cantidad__lte=F('stock_minimo'),
        estado='activo'
    ).count()
    
    # Valor total del inventario
    valor_inventario = Producto.objects.filter(estado='activo').aggregate(
        total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('precio_unitario'),
                output_field=DecimalField()
            )
        )
    )['total'] or Decimal('0.00')
    
    # Estadísticas de usuarios (solo admin)
    if es_admin:
        total_usuarios = User.objects.filter(is_active=True).count()
        usuarios_admin = User.objects.filter(is_superuser=True, is_active=True).count()
    else:
        total_usuarios = 0
        usuarios_admin = 0
    
    # Comprobantes recientes (solo admin)
    if es_admin:
        comprobantes_recientes = Comprobante.objects.select_related('empresa').order_by('-fecha_creacion')[:5]
    else:
        comprobantes_recientes = []
    
    # Comprobantes por tipo (para gráfico - solo admin)
    if es_admin:
        comprobantes_por_tipo = Comprobante.objects.values('tipo').annotate(
            total=Count('id')
        ).order_by('-total')
    else:
        comprobantes_por_tipo = []
    
    # Últimas empresas registradas (solo admin)
    if es_admin:
        empresas_recientes = Empresa.objects.filter(activo=True).order_by('-fecha_creacion')[:5]
    else:
        empresas_recientes = []
    
    # Productos con bajo stock
    productos_restock = Producto.objects.filter(
        cantidad__lte=F('stock_minimo'),
        estado='activo'
    ).order_by('cantidad')[:5]
    
    # Movimientos de inventario recientes
    movimientos_recientes = MovimientoInventario.objects.select_related(
        'producto', 'usuario'
    ).order_by('-fecha')[:5]
    
    # Productos por categoría (para gráfico)
    productos_por_categoria = Producto.objects.filter(
        estado='activo',
        categoria__isnull=False  # Excluir productos sin categoría
    ).values(
        'categoria__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    context = {
        'es_admin': es_admin,  # Variable para controlar visualización
        'total_empresas': total_empresas,
        'total_cuentas': total_cuentas,
        'total_comprobantes': total_comprobantes,
        'total_debitos': totales['total_debitos'] or 0,
        'total_creditos': totales['total_creditos'] or 0,
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'productos_bajo_stock': productos_bajo_stock,
        'valor_inventario': valor_inventario,
        'total_usuarios': total_usuarios,
        'usuarios_admin': usuarios_admin,
        'comprobantes_recientes': comprobantes_recientes,
        'comprobantes_por_tipo': comprobantes_por_tipo,
        'empresas_recientes': empresas_recientes,
        'productos_restock': productos_restock,
        'movimientos_recientes': movimientos_recientes,
        'productos_por_categoria': productos_por_categoria,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
