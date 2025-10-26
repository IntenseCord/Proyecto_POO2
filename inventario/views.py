from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.db import models
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from .models import Producto, Categoria, MovimientoInventario
from .forms import ProductoForm, CategoriaForm, MovimientoInventarioForm

# Constantes para evitar duplicación
DETALLE_PRODUCTO_URL = 'inventario:detalle_producto'

@login_required
@never_cache
@require_GET
def inventario_dashboard(request):
    """Dashboard principal del inventario"""
    productos = Producto.objects.filter(estado='activo')
    
    # Estadísticas generales
    total_productos = productos.count()
    valor_total_inventario = productos.aggregate(
        total=Sum('cantidad') * Sum('precio_unitario')
    )['total'] or 0
    productos_bajo_stock = productos.filter(cantidad__lte=F('stock_minimo')).count()
    
    # Productos más recientes
    productos_recientes = productos.order_by('-fecha_creacion')[:5]
    
    # Productos con bajo stock
    productos_alerta = productos.filter(cantidad__lte=F('stock_minimo'))[:5]
    
    context = {
        'total_productos': total_productos,
        'valor_total_inventario': valor_total_inventario,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_recientes': productos_recientes,
        'productos_alerta': productos_alerta,
    }
    
    return render(request, 'inventario/dashboard.html', context)

@login_required
@never_cache
@require_GET
def lista_productos(request):
    """Lista todos los productos con filtros y paginación"""
    productos = Producto.objects.all()
    
    # Filtros
    busqueda = request.GET.get('busqueda')
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(codigo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if estado:
        productos = productos.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Para los filtros
    categorias = Categoria.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_seleccionada': categoria_id,
        'estado_seleccionado': estado,
    }
    
    return render(request, 'inventario/lista_productos.html', context)

@login_required
@never_cache
@require_GET
def detalle_producto(request, producto_id):
    """Muestra el detalle de un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    movimientos = producto.movimientos.all()[:10]  # Últimos 10 movimientos
    
    context = {
        'producto': producto,
        'movimientos': movimientos,
    }
    
    return render(request, 'inventario/detalle_producto.html', context)

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def crear_producto(request):
    """Crea un nuevo producto"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.usuario_creador = request.user
            producto.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect(DETALLE_PRODUCTO_URL, producto_id=producto.id)
    else:
        form = ProductoForm()
    
    return render(request, 'inventario/crear_producto.html', {'form': form})

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def editar_producto(request, producto_id):
    """Edita un producto existente"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect(DETALLE_PRODUCTO_URL, producto_id=producto.id)
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'inventario/editar_producto.html', {
        'form': form,
        'producto': producto
    })

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def eliminar_producto(request, producto_id):
    """Elimina (desactiva) un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        producto.estado = 'inactivo'
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" desactivado exitosamente.')
        return redirect('inventario:lista_productos')
    
    return render(request, 'inventario/confirmar_eliminacion.html', {'producto': producto})

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def crear_movimiento(request, producto_id):
    """Crea un movimiento de inventario"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.producto = producto
            movimiento.usuario = request.user
            
            # Actualizar cantidad del producto
            if movimiento.tipo == 'entrada':
                producto.cantidad += movimiento.cantidad
            elif movimiento.tipo == 'salida':
                if producto.cantidad >= movimiento.cantidad:
                    producto.cantidad -= movimiento.cantidad
                else:
                    messages.error(request, 'No hay suficiente stock para realizar esta salida.')
                    return render(request, 'inventario/crear_movimiento.html', {
                        'form': form,
                        'producto': producto
                    })
            elif movimiento.tipo == 'ajuste':
                producto.cantidad = movimiento.cantidad
            
            producto.save()
            movimiento.save()
            
            messages.success(request, f'Movimiento registrado exitosamente. Nueva cantidad: {producto.cantidad}')
            return redirect(DETALLE_PRODUCTO_URL, producto_id=producto.id)
    else:
        form = MovimientoInventarioForm()
    
    return render(request, 'inventario/crear_movimiento.html', {
        'form': form,
        'producto': producto
    })

@login_required
@never_cache
@require_GET
def lista_movimientos(request):
    """Lista todos los movimientos de inventario con filtros"""
    movimientos = MovimientoInventario.objects.select_related('producto', 'usuario').all().order_by('-fecha')
    
    # Filtros
    producto_id = request.GET.get('producto')
    tipo = request.GET.get('tipo')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)
    
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    
    if fecha_desde:
        movimientos = movimientos.filter(fecha__gte=fecha_desde)
    
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(movimientos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Productos para el filtro
    productos = Producto.objects.filter(estado='activo').order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'productos': productos,
        'producto_seleccionado': producto_id,
        'tipo_seleccionado': tipo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'inventario/lista_movimientos.html', context)

@login_required
@never_cache
@require_GET
def lista_categorias(request):
    """Lista todas las categorías"""
    categorias = Categoria.objects.all()
    return render(request, 'inventario/lista_categorias.html', {'categorias': categorias})

@login_required
@never_cache
@csrf_protect
@require_http_methods(['GET', 'POST'])
def crear_categoria(request):
    """Crea una nueva categoría"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada exitosamente.')
            return redirect('inventario:lista_categorias')
    else:
        form = CategoriaForm()
    
    return render(request, 'inventario/crear_categoria.html', {'form': form})

@login_required
@never_cache
@require_GET
def reporte_inventario(request):
    """Genera reporte de inventario"""
    productos = Producto.objects.filter(estado='activo')
    
    # Estadísticas
    total_productos = productos.count()
    valor_total = sum(p.valor_total for p in productos)
    productos_bajo_stock = productos.filter(cantidad__lte=F('stock_minimo'))
    
    context = {
        'productos': productos,
        'total_productos': total_productos,
        'valor_total': valor_total,
        'productos_bajo_stock': productos_bajo_stock,
    }
    
    return render(request, 'inventario/reporte_inventario.html', context)
