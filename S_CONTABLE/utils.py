"""
Utilidades comunes para reducir duplicación de código en las views
"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.db.models import Q
from empresa.models import Empresa
from datetime import datetime
from decimal import Decimal


def obtener_empresa_activa():
    """
    Obtiene la primera empresa activa.
    Función reutilizable para evitar duplicación.
    """
    try:
        return Empresa.objects.filter(activo=True).order_by('id').first()
    except Exception:
        return None


def aplicar_filtros_fecha(queryset, fecha_desde, fecha_hasta, campo_fecha='fecha'):
    """
    Aplica filtros de fecha a un queryset.
    
    Args:
        queryset: El queryset a filtrar
        fecha_desde: Fecha inicial (puede ser None)
        fecha_hasta: Fecha final (puede ser None)
        campo_fecha: Nombre del campo de fecha en el modelo (default: 'fecha')
    
    Returns:
        Queryset filtrado
    """
    if fecha_desde:
        queryset = queryset.filter(**{f'{campo_fecha}__gte': fecha_desde})
    
    if fecha_hasta:
        queryset = queryset.filter(**{f'{campo_fecha}__lte': fecha_hasta})
    
    return queryset


def construir_query_params(request_get):
    """
    Construye un diccionario de parámetros de consulta desde request.GET
    para uso en paginación y filtros.
    
    Args:
        request_get: request.GET object
    
    Returns:
        Diccionario con parámetros de consulta
    """
    params = {}
    for key, value in request_get.items():
        if key != 'page' and value:  # Excluir 'page' y valores vacíos
            params[key] = value
    return params


def manejar_formulario_crud(request, form_class, template_name, redirect_url, 
                            instance=None, mensaje_exito='', context_extra=None):
    """
    Maneja el patrón común GET/POST para formularios CRUD.
    Reduce duplicación en views de crear/editar.
    
    Args:
        request: HttpRequest object
        form_class: Clase del formulario
        template_name: Nombre del template
        redirect_url: URL de redirección tras éxito
        instance: Instancia del modelo (None para crear, objeto para editar)
        mensaje_exito: Mensaje de éxito personalizado
        context_extra: Contexto adicional para el template (dict)
    
    Returns:
        HttpResponse
    """
    if request.method == 'POST':
        if instance:
            form = form_class(request.POST, request.FILES, instance=instance)
        else:
            form = form_class(request.POST, request.FILES)
        
        if form.is_valid():
            obj = form.save()
            if mensaje_exito:
                messages.success(request, mensaje_exito)
            return redirect(redirect_url, **{'pk': obj.pk} if hasattr(obj, 'pk') else {})
    else:
        if instance:
            form = form_class(instance=instance)
        else:
            form = form_class()
    
    context = {'form': form}
    if context_extra:
        context.update(context_extra)
    
    return render(request, template_name, context)


def paginar_queryset(queryset, request, items_per_page=20):
    """
    Aplica paginación a un queryset.
    
    Args:
        queryset: QuerySet a paginar
        request: HttpRequest object para obtener el número de página
        items_per_page: Número de items por página
    
    Returns:
        Objeto page_obj con los resultados paginados
    """
    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def parsear_fecha(fecha_str, formato='%Y-%m-%d'):
    """
    Convierte una cadena de fecha a objeto date.
    
    Args:
        fecha_str: String con la fecha
        formato: Formato de la fecha (default: '%Y-%m-%d')
    
    Returns:
        datetime.date object o None si la conversión falla
    """
    if not fecha_str:
        return None
    
    try:
        return datetime.strptime(fecha_str, formato).date()
    except (ValueError, TypeError):
        return None


def obtener_fechas_desde_request(request):
    """
    Extrae y parsea fechas de inicio y fin desde request.GET.
    Evita duplicación del código de parseo de fechas.
    
    Args:
        request: HttpRequest object
    
    Returns:
        Tuple (fecha_inicio, fecha_fin) con objetos date o None
    """
    fecha_inicio = parsear_fecha(request.GET.get('fecha_inicio'))
    fecha_fin = parsear_fecha(request.GET.get('fecha_fin'))
    return fecha_inicio, fecha_fin


def aplicar_busqueda_texto(queryset, busqueda, campos):
    """
    Aplica búsqueda de texto sobre múltiples campos usando Q objects.
    
    Args:
        queryset: QuerySet a filtrar
        busqueda: Texto de búsqueda
        campos: Lista de nombres de campos para buscar (ej: ['nombre', 'codigo'])
    
    Returns:
        QuerySet filtrado
    """
    if not busqueda:
        return queryset
    
    q_objects = Q()
    for campo in campos:
        q_objects |= Q(**{f'{campo}__icontains': busqueda})
    
    return queryset.filter(q_objects)

