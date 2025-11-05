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

def obtener_empresa_unica():
    try:
        return Empresa.objects.filter(activo=True).order_by('id').first()
    except Exception:
        return None

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
    if not empresa:
        empresa = obtener_empresa_unica()
    
    context = {
        'empresa': empresa,
    }
    
    return render(request, 'cuentas/reportes/menu.html', context)


@login_required
@never_cache
def balance_comprobacion_view(request):
    """Vista para el Balance de Comprobación"""
    from .reportes import BalanceComprobacion
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    from .models import TipoCuenta
    
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
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipo_cuenta = request.GET.get('tipo_cuenta', '')
        
        try:
            # Convertir fechas si existen
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
            
            # Generar reporte con filtro de tipo de cuenta
            reporte = BalanceComprobacion(
                empresa, 
                fecha_inicio_obj, 
                fecha_fin_obj,
                tipo_cuenta if tipo_cuenta else None
            )
            reporte_data = reporte.generar()
            
        except ValueError:
            messages.error(request, ERROR_FORMATO_FECHA_INVALIDO)
    
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
    """Exporta el Balance de Comprobación a PDF"""
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from .reportes import BalanceComprobacion
    from datetime import datetime
    from login.utils import obtener_empresa_usuario
    from io import BytesIO
    
    empresa = obtener_empresa_usuario(request.user)
    if not empresa:
        empresa = obtener_empresa_unica()
    
    if not empresa:
        messages.error(request, 'No tienes una empresa asignada.')
        return redirect('cuentas:balance_comprobacion')
    
    # Obtener parámetros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    tipo_cuenta = request.GET.get('tipo_cuenta', '')
    
    try:
        fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
        fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
    except (ValueError, TypeError):
        fecha_inicio_obj = None
        fecha_fin_obj = None
    
    # Generar reporte
    reporte = BalanceComprobacion(
        empresa, 
        fecha_inicio_obj, 
        fecha_fin_obj,
        tipo_cuenta if tipo_cuenta else None
    )
    reporte_data = reporte.generar()
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Encabezado
    elements.append(Paragraph(f"<b>{empresa.nombre}</b>", title_style))
    elements.append(Paragraph("Balance de Comprobación", title_style))
    
    # Período
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
    
    # Crear tabla
    data = [['Código', 'Cuenta', 'Débitos', 'Créditos', 'Saldo Deudor', 'Saldo Acreedor']]
    
    for cuenta in reporte_data['cuentas']:
        data.append([
            cuenta['codigo'],
            cuenta['nombre'][:40],  # Limitar longitud del nombre
            f"${cuenta['debito']:,.2f}",
            f"${cuenta['credito']:,.2f}",
            f"${cuenta['saldo_deudor']:,.2f}",
            f"${cuenta['saldo_acreedor']:,.2f}",
        ])
    
    # Fila de totales
    totales = reporte_data['totales']
    data.append([
        '',
        'TOTALES',
        f"${totales['debitos']:,.2f}",
        f"${totales['creditos']:,.2f}",
        f"${totales['saldo_deudor']:,.2f}",
        f"${totales['saldo_acreedor']:,.2f}",
    ])
    
    # Crear tabla con estilo
    table = Table(data, colWidths=[0.8*inch, 3*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Contenido
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
        
        # Totales
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ]))
    
    elements.append(table)
    
    # Indicador de balance
    elements.append(Spacer(1, 0.3*inch))
    if reporte_data['esta_balanceado']:
        balance_text = "✓ Balance Correcto: Los débitos y créditos están balanceados."
        color = colors.HexColor('#155724')
    else:
        balance_text = "⚠ Advertencia: Los débitos y créditos NO están balanceados."
        color = colors.HexColor('#721c24')
    
    balance_style = ParagraphStyle(
        'Balance',
        parent=styles['Normal'],
        fontSize=10,
        textColor=color,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(balance_text, balance_style))
    
    # Construir PDF
    doc.build(elements)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"balance_comprobacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


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
        empresa = obtener_empresa_unica()
    
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
        except Exception as e:
            messages.warning(request, f'No se pudo inicializar el plan de cuentas automáticamente. Por favor, crea las cuentas manualmente.')
    
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
