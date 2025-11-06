from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from .models import Comprobante, DetalleComprobante, TipoComprobante
from .forms import ComprobanteForm, DetalleComprobanteFormSet, FiltroComprobanteForm
from empresa.models import Empresa
from decimal import Decimal
from inventario.models import Producto, MovimientoInventario

# Constantes para evitar duplicación
DETALLE_COMPROBANTE_URL = 'transacciones:detalle_comprobante'
MAX_ITEMS_PER_DOCUMENT = 100  # Límite máximo de items por seguridad


def _procesar_detalles_formset(formset):
    """
    Procesa y guarda los detalles del formset.
    Extrae lógica para reducir complejidad cognitiva.
    """
    # Guardar detalles
    detalles = formset.save(commit=False)
    
    # Eliminar detalles marcados para borrar
    for detalle in formset.deleted_objects:
        detalle.delete()
    
    # Guardar y validar detalles
    for i, detalle in enumerate(detalles, start=1):
        detalle.orden = i
        detalle.full_clean()
        detalle.save()


def _mostrar_mensaje_balanceo(request, comprobante):
    """
    Muestra mensaje sobre el estado de balanceo del comprobante.
    Extrae lógica para reducir complejidad cognitiva.
    """
    if comprobante.esta_balanceado():
        messages.info(request, '✅ El comprobante está balanceado.')
    else:
        diferencia = abs(comprobante.total_debito - comprobante.total_credito)
        messages.warning(request, f'⚠️ Diferencia: ${diferencia:,.2f}')

@login_required
@require_GET
def lista_comprobantes(request):
    """Lista todos los comprobantes con filtros"""
    comprobantes = Comprobante.objects.select_related('empresa', 'usuario_creador').all()
    
    # Filtros
    empresa_id = request.GET.get('empresa')
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if empresa_id:
        comprobantes = comprobantes.filter(empresa_id=empresa_id)
    
    if tipo:
        comprobantes = comprobantes.filter(tipo=tipo)
    
    if estado:
        comprobantes = comprobantes.filter(estado=estado)
    
    if fecha_desde:
        comprobantes = comprobantes.filter(fecha__gte=fecha_desde)
    
    if fecha_hasta:
        comprobantes = comprobantes.filter(fecha__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(comprobantes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Para los filtros
    empresas = Empresa.objects.filter(activo=True)
    productos_activos = Producto.objects.filter(estado='activo').order_by('nombre')
    productos_activos = Producto.objects.filter(estado='activo').order_by('nombre')
    productos_activos = Producto.objects.filter(estado='activo').order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'empresas': empresas,
        'tipos': TipoComprobante.choices,
        'empresa_seleccionada': empresa_id,
        'tipo_seleccionado': tipo,
        'estado_seleccionado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'transacciones/lista_comprobantes.html', context)

@login_required
@require_GET
def detalle_comprobante(request, comprobante_id):
    """Muestra el detalle de un comprobante"""
    comprobante = get_object_or_404(
        Comprobante.objects.select_related('empresa', 'usuario_creador'),
        id=comprobante_id
    )
    
    # Obtener detalles ordenados
    detalles = comprobante.detalles.select_related('cuenta').order_by('orden')
    
    context = {
        'comprobante': comprobante,
        'detalles': detalles,
    }
    
    return render(request, 'transacciones/detalle_comprobante.html', context)

@login_required
@transaction.atomic
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def crear_comprobante(request):
    """Crea un nuevo comprobante con sus detalles"""
    if request.method == 'POST':
        form = ComprobanteForm(request.POST)
        formset = DetalleComprobanteFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                # Guardar comprobante
                comprobante = form.save(commit=False)
                comprobante.usuario_creador = request.user
                comprobante.save()
                
                # Guardar detalles
                formset.instance = comprobante
                detalles = formset.save(commit=False)
                
                # Asignar orden y guardar
                for i, detalle in enumerate(detalles, start=1):
                    detalle.orden = i
                    detalle.full_clean()  # Validar
                    detalle.save()
                
                # Calcular totales
                comprobante.calcular_totales()
                
                messages.success(
                    request, 
                    f'Comprobante "{comprobante.numero}" creado exitosamente. '
                    f'Total Débito: ${comprobante.total_debito:,.2f} - '
                    f'Total Crédito: ${comprobante.total_credito:,.2f}'
                )
                
                if comprobante.esta_balanceado():
                    messages.info(request, '✅ El comprobante está balanceado y listo para aprobar.')
                else:
                    messages.warning(
                        request, 
                        '⚠️ El comprobante NO está balanceado. '
                        f'Diferencia: ${abs(comprobante.total_debito - comprobante.total_credito):,.2f}'
                    )
                
                return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
                
            except ValidationError as e:
                messages.error(request, f'Error de validación: {e}')
    else:
        form = ComprobanteForm()
        formset = DetalleComprobanteFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Crear Comprobante',
    }
    
    return render(request, 'transacciones/crear_comprobante.html', context)

@login_required
@transaction.atomic
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def editar_comprobante(request, comprobante_id):
    """Edita un comprobante existente (solo si está en borrador)"""
    comprobante = get_object_or_404(Comprobante, id=comprobante_id)
    
    if comprobante.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden editar comprobantes en estado BORRADOR.')
        return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
    
    if request.method == 'POST':
        form = ComprobanteForm(request.POST, instance=comprobante)
        formset = DetalleComprobanteFormSet(request.POST, instance=comprobante)
        
        if form.is_valid() and formset.is_valid():
            try:
                form.save()
                _procesar_detalles_formset(formset)
                comprobante.calcular_totales()
                
                messages.success(request, f'Comprobante "{comprobante.numero}" actualizado exitosamente.')
                _mostrar_mensaje_balanceo(request, comprobante)
                
                return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
                
            except ValidationError as e:
                messages.error(request, f'Error de validación: {e}')
    else:
        form = ComprobanteForm(instance=comprobante)
        formset = DetalleComprobanteFormSet(instance=comprobante)
    
    context = {
        'form': form,
        'formset': formset,
        'comprobante': comprobante,
        'titulo': 'Editar Comprobante',
    }
    
    return render(request, 'transacciones/crear_comprobante.html', context)

@login_required
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def aprobar_comprobante(request, comprobante_id):
    """Aprueba un comprobante (valida partida doble)"""
    comprobante = get_object_or_404(Comprobante, id=comprobante_id)
    
    if comprobante.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden aprobar comprobantes en estado BORRADOR.')
        return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
    
    if request.method == 'POST':
        try:
            comprobante.aprobar(usuario=request.user)
            messages.success(request, f'✅ Comprobante "{comprobante.numero}" aprobado exitosamente.')
        except ValidationError as e:
            messages.error(request, f'❌ Error al aprobar: {e}')
        
        return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
    
    return render(request, 'transacciones/confirmar_aprobacion.html', {'comprobante': comprobante})

@login_required
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def anular_comprobante(request, comprobante_id):
    """Anula un comprobante aprobado"""
    comprobante = get_object_or_404(Comprobante, id=comprobante_id)
    
    if comprobante.estado == 'ANULADO':
        messages.error(request, 'El comprobante ya está anulado.')
        return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
    
    if request.method == 'POST':
        try:
            comprobante.anular()
            messages.success(request, f'Comprobante "{comprobante.numero}" anulado exitosamente.')
        except ValidationError as e:
            messages.error(request, f'Error al anular: {e}')
        
        return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
    
    return render(request, 'transacciones/confirmar_anulacion.html', {'comprobante': comprobante})

@login_required
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def eliminar_comprobante(request, comprobante_id):
    """Elimina un comprobante (solo si está en borrador)"""
    comprobante = get_object_or_404(Comprobante, id=comprobante_id)
    
    if comprobante.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden eliminar comprobantes en estado BORRADOR.')
        return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
    
    if request.method == 'POST':
        numero = comprobante.numero
        comprobante.delete()
        messages.success(request, f'Comprobante "{numero}" eliminado exitosamente.')
        return redirect('transacciones:lista_comprobantes')
    
    return render(request, 'transacciones/confirmar_eliminacion.html', {'comprobante': comprobante})


# ============================================
# VISTAS DE DOCUMENTOS CONTABLES (ABSTRACCIÓN)
# ============================================

def _obtener_empresa_desde_post(request):
    """Obtiene la empresa desde el POST o la primera activa."""
    empresa_id = request.POST.get('empresa')
    if empresa_id:
        return Empresa.objects.get(id=empresa_id)
    return Empresa.objects.filter(activo=True).first()

def _agregar_items_a_factura(request, factura, usuario):
    """Agrega ítems a la factura validando stock y registrando movimientos."""
    items_count = int(request.POST.get('items_count', 0))
    items_count = min(items_count, MAX_ITEMS_PER_DOCUMENT)
    for i in range(items_count):
        prod_id = request.POST.get(f'item_producto_{i}')
        if not prod_id:
            continue
        try:
            producto = Producto.objects.get(id=prod_id, estado='activo')
        except Producto.DoesNotExist:
            raise ValidationError('Producto inválido en la fila de ítems')

        cantidad = Decimal(request.POST.get(f'item_cantidad_{i}', 0))
        if cantidad <= 0:
            continue

        precio_venta = Decimal(request.POST.get(f'item_precio_{i}', 0) or 0)
        if precio_venta <= 0:
            precio_venta = producto.precio_venta

        if producto.cantidad < cantidad:
            raise ValidationError(
                f'Stock insuficiente para {producto.nombre}. Disponible: {producto.cantidad}'
            )

        # 1) Registrar ítem de venta (ingreso)
        factura.agregar_item(f"{producto.codigo} - {producto.nombre}", cantidad, precio_venta)

        # 2) Disminuir stock y crear movimiento de salida para COSTO DE VENTAS
        producto.cantidad -= int(cantidad)
        producto.save()
        MovimientoInventario.objects.create(
            producto=producto,
            tipo='salida',
            cantidad=int(cantidad),
            motivo='Venta (salida automática)',
            observaciones=f'Factura a {request.POST.get("cliente")}',
            usuario=usuario,
        )

@login_required
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def crear_factura_venta(request):
    """
    Crea una factura de venta que automáticamente genera un asiento contable.
    Usa la clase FacturaVenta que implementa ABSTRACCIÓN.
    """
    from .documentos import FacturaVenta
    from datetime import date
    
    empresas = Empresa.objects.filter(activo=True)
    
    if request.method == 'POST':
        try:
            empresa = _obtener_empresa_desde_post(request)
            # Crear la factura usando la clase abstracta
            factura = FacturaVenta(
                empresa=empresa,
                fecha=request.POST.get('fecha') or date.today(),
                descripcion=request.POST.get('descripcion'),
                cliente=request.POST.get('cliente'),
                forma_pago=request.POST.get('forma_pago', 'CREDITO')
            )
            # Agregar ítems y movimientos
            _agregar_items_a_factura(request, factura, request.user)
            # Generar el asiento contable automáticamente (INGRESOS)
            comprobante = factura.generar_asiento()
            messages.success(request, f'Factura creada exitosamente. Comprobante #{comprobante.numero}')
            return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
        except Exception as e:
            messages.error(request, f'Error al crear la factura: {str(e)}')
    
    from datetime import date
    productos_activos = Producto.objects.filter(estado='activo').order_by('nombre')
    context = {
        'empresas': empresas,
        'today': date.today(),
        'productos': productos_activos,
    }
    
    return render(request, 'transacciones/documentos/crear_factura_venta.html', context)


@login_required
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def crear_nota_credito(request):
    """
    Crea una nota de crédito que automáticamente genera un asiento contable.
    Usa la clase NotaCredito que implementa ABSTRACCIÓN.
    """
    from .documentos import NotaCredito
    from datetime import date
    
    empresas = Empresa.objects.filter(activo=True)
    
    if request.method == 'POST':
        try:
            empresa_id = request.POST.get('empresa')
            empresa = Empresa.objects.get(id=empresa_id)
            
            # Crear la nota de crédito usando la clase abstracta
            nota = NotaCredito(
                empresa=empresa,
                fecha=request.POST.get('fecha') or date.today(),
                descripcion=request.POST.get('descripcion'),
                cliente=request.POST.get('cliente')
            )
            
            # Agregar items con validación de seguridad
            items_count = int(request.POST.get('items_count', 0))
            # Limitar el número de items para prevenir ataques de inyección
            items_count = min(items_count, MAX_ITEMS_PER_DOCUMENT)
            for i in range(items_count):
                descripcion = request.POST.get(f'item_descripcion_{i}')
                cantidad = Decimal(request.POST.get(f'item_cantidad_{i}', 0))
                precio = Decimal(request.POST.get(f'item_precio_{i}', 0))
                
                if descripcion and cantidad > 0 and precio > 0:
                    nota.agregar_item(descripcion, cantidad, precio)
            
            # Generar el asiento contable automáticamente
            comprobante = nota.generar_asiento()
            
            messages.success(request, f'Nota de Crédito creada exitosamente. Comprobante #{comprobante.numero}')
            return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear la nota de crédito: {str(e)}')
    
    context = {
        'empresas': empresas,
    }
    
    return render(request, 'transacciones/documentos/crear_nota_credito.html', context)


@login_required
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def crear_recibo_caja(request):
    """
    Crea un recibo de caja que automáticamente genera un asiento contable.
    Usa la clase ReciboCaja que implementa ABSTRACCIÓN.
    """
    from .documentos import ReciboCaja
    from datetime import date
    
    empresas = Empresa.objects.filter(activo=True)
    
    if request.method == 'POST':
        try:
            empresa_id = request.POST.get('empresa')
            empresa = Empresa.objects.get(id=empresa_id)
            
            # Crear el recibo usando la clase abstracta
            recibo = ReciboCaja(
                empresa=empresa,
                fecha=request.POST.get('fecha') or date.today(),
                descripcion=request.POST.get('descripcion'),
                cliente=request.POST.get('cliente'),
                monto=Decimal(request.POST.get('monto', 0)),
                forma_pago=request.POST.get('forma_pago', 'EFECTIVO')
            )
            
            # Generar el asiento contable automáticamente
            comprobante = recibo.generar_asiento()
            
            messages.success(request, f'Recibo de Caja creado exitosamente. Comprobante #{comprobante.numero}')
            return redirect(DETALLE_COMPROBANTE_URL, comprobante_id=comprobante.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear el recibo: {str(e)}')
    
    context = {
        'empresas': empresas,
    }
    
    return render(request, 'transacciones/documentos/crear_recibo_caja.html', context)


@login_required
@require_GET
def menu_documentos(request):
    """Menú principal de documentos contables"""
    return render(request, 'transacciones/documentos/menu.html')
