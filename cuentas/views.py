from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.cache import never_cache
from .models import Cuenta, TipoCuenta
from .forms import CuentaForm, FiltroCuentaForm
from empresa.models import Empresa

# Constantes para evitar duplicación
DETALLE_CUENTA_URL = 'cuentas:detalle_cuenta'
ERROR_EMPRESA_NO_ENCONTRADA = 'Empresa no encontrada.'
ERROR_FORMATO_FECHA_INVALIDO = 'Formato de fecha inválido.'

@login_required
@never_cache
@require_GET
def lista_cuentas(request):
    """Lista todas las cuentas con filtros jerárquicos"""
    cuentas = Cuenta.objects.select_related('empresa', 'cuenta_padre').all().order_by('codigo')
    
    # Filtros
    empresa_id = request.GET.get('empresa')
    tipo = request.GET.get('tipo')
    busqueda = request.GET.get('busqueda')
    
    if empresa_id:
        cuentas = cuentas.filter(empresa_id=empresa_id)
    
    if tipo:
        cuentas = cuentas.filter(tipo=tipo)
    
    if busqueda:
        cuentas = cuentas.filter(
            Q(codigo__icontains=busqueda) | 
            Q(nombre__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(cuentas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Para los filtros
    empresas = Empresa.objects.filter(activo=True)
    
    context = {
        'page_obj': page_obj,
        'empresas': empresas,
        'tipos': TipoCuenta.choices,
        'empresa_seleccionada': empresa_id,
        'tipo_seleccionado': tipo,
        'busqueda': busqueda,
        'total_cuentas': Cuenta.objects.filter(esta_activa=True).count(),
    }
    
    return render(request, 'cuentas/lista_cuentas.html', context)

@login_required
@never_cache
@require_GET
def arbol_cuentas(request, empresa_id):
    """Muestra el árbol jerárquico de cuentas de una empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Obtener cuentas de nivel 1 (sin padre)
    cuentas_raiz = Cuenta.objects.filter(
        empresa=empresa,
        cuenta_padre__isnull=True,
        esta_activa=True
    ).order_by('codigo')
    
    context = {
        'empresa': empresa,
        'cuentas_raiz': cuentas_raiz,
    }
    
    return render(request, 'cuentas/arbol_cuentas.html', context)

@login_required
@never_cache
@require_GET
def detalle_cuenta(request, cuenta_id):
    """Muestra el detalle de una cuenta"""
    cuenta = get_object_or_404(Cuenta.objects.select_related('empresa', 'cuenta_padre'), id=cuenta_id)
    
    # Obtener subcuentas
    subcuentas = cuenta.subcuentas.filter(esta_activa=True).order_by('codigo')
    
    # Estadísticas de movimientos
    total_movimientos = cuenta.movimientos.count()
    totales = cuenta.movimientos.aggregate(
        total_debito=Sum('debito'),
        total_credito=Sum('credito')
    )
    
    # Calcular saldo
    saldo = (totales['total_debito'] or 0) - (totales['total_credito'] or 0)
    if cuenta.naturaleza == 'CREDITO':
        saldo = -saldo
    
    context = {
        'cuenta': cuenta,
        'subcuentas': subcuentas,
        'total_movimientos': total_movimientos,
        'total_debito': totales['total_debito'] or 0,
        'total_credito': totales['total_credito'] or 0,
        'saldo': saldo,
    }
    
    return render(request, 'cuentas/detalle_cuenta.html', context)

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def crear_cuenta(request):
    """Crea una nueva cuenta"""
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            # Calcular nivel
            if cuenta.cuenta_padre:
                cuenta.nivel = cuenta.cuenta_padre.nivel + 1
            else:
                cuenta.nivel = 1
            cuenta.save()
            messages.success(request, f'Cuenta "{cuenta.codigo} - {cuenta.nombre}" creada exitosamente.')
            return redirect(DETALLE_CUENTA_URL, cuenta_id=cuenta.id)
    else:
        form = CuentaForm()
    
    return render(request, 'cuentas/crear_cuenta.html', {'form': form})

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def editar_cuenta(request, cuenta_id):
    """Edita una cuenta existente"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id)
    
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            cuenta = form.save(commit=False)
            # Recalcular nivel
            if cuenta.cuenta_padre:
                cuenta.nivel = cuenta.cuenta_padre.nivel + 1
            else:
                cuenta.nivel = 1
            cuenta.save()
            messages.success(request, f'Cuenta "{cuenta.codigo} - {cuenta.nombre}" actualizada exitosamente.')
            return redirect(DETALLE_CUENTA_URL, cuenta_id=cuenta.id)
    else:
        form = CuentaForm(instance=cuenta)
    
    return render(request, 'cuentas/editar_cuenta.html', {
        'form': form,
        'cuenta': cuenta
    })

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def eliminar_cuenta(request, cuenta_id):
    """Desactiva una cuenta (no la elimina físicamente)"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id)
    
    # Verificar si tiene movimientos
    if cuenta.movimientos.exists():
        messages.error(request, 'No se puede desactivar una cuenta con movimientos registrados.')
        return redirect(DETALLE_CUENTA_URL, cuenta_id=cuenta.id)
    
    # Verificar si tiene subcuentas activas
    if cuenta.subcuentas.filter(esta_activa=True).exists():
        messages.error(request, 'No se puede desactivar una cuenta con subcuentas activas.')
        return redirect(DETALLE_CUENTA_URL, cuenta_id=cuenta.id)
    
    if request.method == 'POST':
        cuenta.esta_activa = False
        cuenta.save()
        messages.success(request, f'Cuenta "{cuenta.codigo} - {cuenta.nombre}" desactivada exitosamente.')
        return redirect('cuentas:lista_cuentas')
    
    return render(request, 'cuentas/confirmar_eliminacion.html', {'cuenta': cuenta})


# ============================================
# VISTAS DE REPORTES FINANCIEROS
# ============================================

@login_required
@never_cache
@require_GET
def reportes_menu(request):
    """Menú principal de reportes financieros"""
    from login.utils import obtener_empresa_usuario
    
    empresa = obtener_empresa_usuario(request.user)
    
    context = {
        'empresa': empresa,
    }
    
    return render(request, 'cuentas/reportes/menu.html', context)


@login_required
@never_cache
@require_GET
def balance_comprobacion_view(request):
    """Vista para el Balance de Comprobación"""
    from .reportes import BalanceComprobacion
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    
    reporte_data = None
    empresa = obtener_empresa_usuario(request.user)
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
        return render(request, 'cuentas/reportes/balance_comprobacion.html', {'reporte': None, 'empresa': None})
    
    # Si hay parámetros de fecha, generar el reporte
    if request.method == 'GET' and (request.GET.get('generar') or request.GET.get('fecha_inicio') or request.GET.get('fecha_fin')):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        try:
            # Convertir fechas si existen
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
            
            # Generar reporte
            reporte = BalanceComprobacion(empresa, fecha_inicio_obj, fecha_fin_obj)
            reporte_data = reporte.generar()
            
        except ValueError:
            messages.error(request, ERROR_FORMATO_FECHA_INVALIDO)
    
    context = {
        'empresa': empresa,
        'reporte': reporte_data,
    }
    
    return render(request, 'cuentas/reportes/balance_comprobacion.html', context)


@login_required
@never_cache
@require_GET
def estado_resultados_view(request):
    """Vista para el Estado de Resultados"""
    from .reportes import EstadoResultados
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    
    reporte_data = None
    empresa = obtener_empresa_usuario(request.user)
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
        return render(request, 'cuentas/reportes/estado_resultados.html', {'reporte': None, 'empresa': None})
    
    # Si hay parámetros de fecha, generar el reporte
    if request.method == 'GET' and (request.GET.get('generar') or request.GET.get('fecha_inicio') or request.GET.get('fecha_fin')):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        try:
            # Convertir fechas si existen
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
            
            # Generar reporte
            reporte = EstadoResultados(empresa, fecha_inicio_obj, fecha_fin_obj)
            reporte_data = reporte.generar()
            
        except ValueError:
            messages.error(request, ERROR_FORMATO_FECHA_INVALIDO)
    
    context = {
        'empresa': empresa,
        'reporte': reporte_data,
    }
    
    return render(request, 'cuentas/reportes/estado_resultados.html', context)


@login_required
@never_cache
@require_GET
def balance_general_view(request):
    """Vista para el Balance General"""
    from .reportes import BalanceGeneral
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    
    reporte_data = None
    empresa = obtener_empresa_usuario(request.user)
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
        return render(request, 'cuentas/reportes/balance_general.html', {'reporte': None, 'empresa': None})
    
    # Si hay parámetros de fecha, generar el reporte
    if request.method == 'GET' and (request.GET.get('generar') or request.GET.get('fecha_inicio') or request.GET.get('fecha_fin')):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        try:
            # Convertir fechas si existen
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
            
            # Generar reporte
            reporte = BalanceGeneral(empresa, fecha_inicio_obj, fecha_fin_obj)
            reporte_data = reporte.generar()
            
        except ValueError:
            messages.error(request, ERROR_FORMATO_FECHA_INVALIDO)
    
    context = {
        'empresa': empresa,
        'reporte': reporte_data,
    }
    
    return render(request, 'cuentas/reportes/balance_general.html', context)


@login_required
@never_cache
@require_GET
def balance_general_pdf(request):
    """Exporta el Balance General a PDF"""
    from .reportes import BalanceGeneral
    from .export_service import ExportadorBalanceGeneral
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    from django.http import FileResponse
    
    empresa = obtener_empresa_usuario(request.user)
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada.')
        return redirect('cuentas:balance_general')
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    try:
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
        fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
        
        # Generar reporte
        reporte = BalanceGeneral(empresa, fecha_inicio_obj, fecha_fin_obj)
        reporte_data = reporte.generar()
        
        # Exportar a PDF
        exportador = ExportadorBalanceGeneral(reporte_data)
        pdf_buffer = exportador.exportar_pdf()
        
        # Crear nombre de archivo
        filename = f"balance_general_{empresa.nombre}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return FileResponse(pdf_buffer, as_attachment=True, filename=filename)
        
    except Exception as e:
        messages.error(request, f'Error al generar el PDF: {str(e)}')
        return redirect('cuentas:balance_general')


@login_required
@never_cache
@require_GET
def balance_general_excel(request):
    """Exporta el Balance General a Excel"""
    from .reportes import BalanceGeneral
    from .export_service import ExportadorBalanceGeneral
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    from django.http import HttpResponse
    
    empresa = obtener_empresa_usuario(request.user)
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada.')
        return redirect('cuentas:balance_general')
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    try:
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
        fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
        
        # Generar reporte
        reporte = BalanceGeneral(empresa, fecha_inicio_obj, fecha_fin_obj)
        reporte_data = reporte.generar()
        
        # Exportar a Excel
        exportador = ExportadorBalanceGeneral(reporte_data)
        excel_buffer = exportador.exportar_excel()
        
        # Crear respuesta HTTP
        filename = f"balance_general_{empresa.nombre}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response = HttpResponse(
            excel_buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar el Excel: {str(e)}')
        return redirect('cuentas:balance_general')
