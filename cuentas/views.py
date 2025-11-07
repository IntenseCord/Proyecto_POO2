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

# Importar función reutilizable
from S_CONTABLE.utils import obtener_empresa_activa as obtener_empresa_unica

@login_required
@never_cache
@require_GET
def lista_cuentas(request):
    """Lista todas las cuentas con filtros jerárquicos usando utilidades centralizadas"""
    from S_CONTABLE.utils import aplicar_busqueda_texto, paginar_queryset
    
    cuentas = Cuenta.objects.select_related('empresa', 'cuenta_padre').all().order_by('codigo')
    
    # Filtros
    empresa_id = request.GET.get('empresa')
    tipo = request.GET.get('tipo')
    busqueda = request.GET.get('busqueda')
    
    if empresa_id:
        cuentas = cuentas.filter(empresa_id=empresa_id)
    
    if tipo:
        cuentas = cuentas.filter(tipo=tipo)
    
    # Usar helper centralizado para búsqueda
    cuentas = aplicar_busqueda_texto(cuentas, busqueda, ['codigo', 'nombre'])
    
    # Usar helper centralizado para paginación
    page_obj = paginar_queryset(cuentas, request, items_per_page=20)
    
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
    if not empresa:
        empresa = obtener_empresa_unica()
    
    context = {
        'empresa': empresa,
    }
    
    return render(request, 'cuentas/reportes/menu.html', context)


@login_required
@never_cache
@require_GET
def balance_comprobacion_view(request):
    """Vista para el Balance de Comprobación usando utilidades centralizadas"""
    from .reportes import BalanceComprobacion
    from login.utils import obtener_empresa_usuario
    from .models import TipoCuenta
    from S_CONTABLE.utils import obtener_fechas_desde_request
    
    reporte_data = None
    empresa = obtener_empresa_usuario(request.user)
    if not empresa:
        empresa = obtener_empresa_unica()
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
        return render(request, 'cuentas/reportes/balance_comprobacion.html', {
            'reporte': None, 
            'empresa': None,
            'tipos_cuenta': TipoCuenta.choices
        })
    
    # Si hay parámetros de fecha, generar el reporte
    if request.method == 'GET' and (request.GET.get('generar') or request.GET.get('fecha_inicio') or request.GET.get('fecha_fin')):
        tipo_cuenta = request.GET.get('tipo_cuenta', '')
        
        # Usar helper centralizado para parsear fechas
        fecha_inicio_obj, fecha_fin_obj = obtener_fechas_desde_request(request)
        
        # Generar reporte con filtro de tipo de cuenta
        reporte = BalanceComprobacion(
            empresa, 
            fecha_inicio_obj, 
            fecha_fin_obj,
            tipo_cuenta if tipo_cuenta else None
        )
        reporte_data = reporte.generar()
    
    context = {
        'empresa': empresa,
        'reporte': reporte_data,
        'tipos_cuenta': TipoCuenta.choices,
        'tipo_cuenta_seleccionado': request.GET.get('tipo_cuenta', ''),
    }
    
    return render(request, 'cuentas/reportes/balance_comprobacion.html', context)


@login_required
@never_cache
@require_GET
def balance_comprobacion_pdf(request):
    """Exporta el Balance de Comprobación a PDF usando utilidades centralizadas"""
    from django.http import HttpResponse
    from .reportes import BalanceComprobacion
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    from S_CONTABLE.pdf_utils import GeneradorPDF, formatear_moneda
    from S_CONTABLE.utils import obtener_fechas_desde_request
    from reportlab.lib.units import inch
    
    empresa = obtener_empresa_usuario(request.user)
    if not empresa:
        empresa = obtener_empresa_unica()
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada.')
        return redirect('cuentas:balance_comprobacion')
    
    # Usar helper para obtener fechas
    fecha_inicio_obj, fecha_fin_obj = obtener_fechas_desde_request(request)
    tipo_cuenta = request.GET.get('tipo_cuenta', '')
    
    # Generar reporte
    reporte = BalanceComprobacion(
        empresa, 
        fecha_inicio_obj, 
        fecha_fin_obj,
        tipo_cuenta if tipo_cuenta else None
    )
    reporte_data = reporte.generar()
    
    # Usar la clase GeneradorPDF para reducir duplicación
    generador = GeneradorPDF("Balance de Comprobación", orientacion='landscape')
    
    # Agregar encabezado
    periodo = generador.generar_periodo_texto(fecha_inicio_obj, fecha_fin_obj)
    generador.agregar_encabezado(empresa, "Balance de Comprobación", periodo)
    
    # Crear tabla de datos
    data = [['Código', 'Cuenta', 'Débitos', 'Créditos', 'Saldo Deudor', 'Saldo Acreedor']]
    
    for cuenta in reporte_data['cuentas']:
        data.append([
            cuenta['codigo'],
            cuenta['nombre'][:40],
            formatear_moneda(cuenta['debito']),
            formatear_moneda(cuenta['credito']),
            formatear_moneda(cuenta['saldo_deudor']),
            formatear_moneda(cuenta['saldo_acreedor']),
        ])
    
    # Fila de totales
    totales = reporte_data['totales']
    data.append([
        '',
        'TOTALES',
        formatear_moneda(totales['debitos']),
        formatear_moneda(totales['creditos']),
        formatear_moneda(totales['saldo_deudor']),
        formatear_moneda(totales['saldo_acreedor']),
    ])
    
    # Agregar tabla usando método del generador
    anchos = [0.8*inch, 3*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch]
    generador.agregar_tabla(data, anchos)
    
    # Indicador de balance
    generador.agregar_espaciador(0.3)
    if reporte_data['esta_balanceado']:
        balance_text = "✓ Balance Correcto: Los débitos y créditos están balanceados."
    else:
        balance_text = "⚠ Advertencia: Los débitos y créditos NO están balanceados."
    
    from reportlab.platypus import Paragraph
    generador.elements.append(Paragraph(balance_text, generador.subtitle_style))
    
    # Construir PDF
    buffer = generador.construir()
    
    # Preparar respuesta
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"balance_comprobacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@never_cache
@require_GET
def estado_resultados_view(request):
    """Vista para el Estado de Resultados usando utilidades centralizadas"""
    from .reportes import EstadoResultados
    from login.utils import obtener_empresa_usuario
    from S_CONTABLE.utils import obtener_fechas_desde_request
    
    reporte_data = None
    empresa = obtener_empresa_usuario(request.user)
    if not empresa:
        empresa = obtener_empresa_unica()
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
        return render(request, 'cuentas/reportes/estado_resultados.html', {'reporte': None, 'empresa': None})
    
    # Si hay parámetros de fecha, generar el reporte
    if request.method == 'GET' and (request.GET.get('generar') or request.GET.get('fecha_inicio') or request.GET.get('fecha_fin')):
        # Usar helper centralizado para parsear fechas
        fecha_inicio_obj, fecha_fin_obj = obtener_fechas_desde_request(request)
        
        # Generar reporte
        reporte = EstadoResultados(empresa, fecha_inicio_obj, fecha_fin_obj)
        reporte_data = reporte.generar()
    
    context = {
        'empresa': empresa,
        'reporte': reporte_data,
    }
    
    return render(request, 'cuentas/reportes/estado_resultados.html', context)


@login_required
@never_cache
@require_GET
def estado_resultados_pdf(request):
    """Exporta el Estado de Resultados a PDF"""
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from .reportes import EstadoResultados
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    from io import BytesIO
    
    empresa = obtener_empresa_usuario(request.user)
    if not empresa:
        empresa = obtener_empresa_unica()
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada.')
        return redirect('cuentas:estado_resultados')
    
    # Parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    try:
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
        fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
    except (ValueError, TypeError):
        fecha_inicio_obj = None
        fecha_fin_obj = None
    
    # Generar reporte
    reporte = EstadoResultados(empresa, fecha_inicio_obj, fecha_fin_obj)
    data = reporte.generar()
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6*inch, bottomMargin=0.6*inch, rightMargin=0.6*inch, leftMargin=0.6*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#2c3e50'), spaceAfter=8, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#7f8c8d'), spaceAfter=14, alignment=TA_CENTER)
    section_header = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#2c3e50'), spaceAfter=6)
    right = ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)
    
    # Encabezado
    elements.append(Paragraph(f"<b>{empresa.nombre}</b>", title_style))
    elements.append(Paragraph("Estado de Resultados", title_style))
    periodo = ""
    if fecha_inicio_obj and fecha_fin_obj:
        periodo = f"Del {fecha_inicio_obj.strftime('%d/%m/%Y')} al {fecha_fin_obj.strftime('%d/%m/%Y')}"
    elif fecha_inicio_obj:
        periodo = f"Desde {fecha_inicio_obj.strftime('%d/%m/%Y')}"
    elif fecha_fin_obj:
        periodo = f"Hasta {fecha_fin_obj.strftime('%d/%m/%Y')}"
    else:
        periodo = "Todos los períodos"
    elements.append(Paragraph(periodo, subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Helper para construir tabla simple de cuentas
    def tabla_cuentas(titulo, lista, total_label, total_valor):
        elements.append(Paragraph(titulo, section_header))
        data_tbl = [["Código", "Cuenta", "Monto"]]
        for c in lista:
            data_tbl.append([c['codigo'], c['nombre'][:50], f"${c['monto']:,.2f}"])
        if not lista:
            data_tbl.append(["", "Sin registros", "$0,00"])  # placeholder
        # Fila total
        data_tbl.append(["", total_label, f"${total_valor:,.2f}"])
        t = Table(data_tbl, colWidths=[1.1*inch, 3.4*inch, 1.2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (-1,1), (-1,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#e9ecef')),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.15*inch))
    
    # Ingresos, Costos, Gastos
    tabla_cuentas("Ingresos", data['ingresos'], "Total Ingresos", data['totales']['ingresos'])
    tabla_cuentas("Costos", data['costos'], "Total Costos", data['totales']['costos'])
    # Subtotal utilidad bruta
    elements.append(Paragraph(f"<b>Utilidad Bruta:</b> ${data['totales']['utilidad_bruta']:,.2f}", right))
    elements.append(Spacer(1, 0.15*inch))
    tabla_cuentas("Gastos", data['gastos'], "Total Gastos", data['totales']['gastos'])
    
    # Resultado final
    resultado = data['totales']['utilidad_neta']
    resultado_texto = "Utilidad Neta" if resultado >= 0 else "Pérdida Neta"
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"<b>{resultado_texto}:</b> ${resultado:,.2f}", title_style))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"estado_resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@never_cache
@require_GET
def balance_general_view(request):
    """Vista para el Balance General usando utilidades centralizadas"""
    from .reportes import BalanceGeneral
    from login.utils import obtener_empresa_usuario
    from S_CONTABLE.utils import obtener_fechas_desde_request
    
    reporte_data = None
    empresa = obtener_empresa_usuario(request.user)
    if not empresa:
        empresa = obtener_empresa_unica()
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada. Contacta al administrador.')
        return render(request, 'cuentas/reportes/balance_general.html', {'reporte': None, 'empresa': None})
    
    # Verificar si la empresa tiene cuentas contables
    cuentas_count = Cuenta.objects.filter(empresa=empresa).count()
    if cuentas_count == 0:
        # Inicializar plan de cuentas automáticamente
        try:
            from django.core.management import call_command
            from io import StringIO
            out = StringIO()
            call_command('init_plan_cuentas', empresa=empresa.id, force=True, stdout=out)
            messages.success(request, f'Plan de cuentas inicializado automáticamente con {Cuenta.objects.filter(empresa=empresa).count()} cuentas básicas.')
        except Exception:
            messages.warning(request, 'No se pudo inicializar el plan de cuentas automáticamente. Por favor, crea las cuentas manualmente.')
    
    # Si hay parámetros de fecha, generar el reporte
    if request.method == 'GET' and (request.GET.get('generar') or request.GET.get('fecha_inicio') or request.GET.get('fecha_fin')):
        # Usar helper centralizado para parsear fechas
        fecha_inicio_obj, fecha_fin_obj = obtener_fechas_desde_request(request)
        
        # Generar reporte
        reporte = BalanceGeneral(empresa, fecha_inicio_obj, fecha_fin_obj)
        reporte_data = reporte.generar()
    
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
        empresa = obtener_empresa_unica()
    
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
        empresa = obtener_empresa_unica()
    
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
