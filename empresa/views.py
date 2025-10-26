from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Empresa
from .forms import EmpresaForm

# Constantes para evitar duplicación
DETALLE_EMPRESA_URL = 'empresa:detalle_empresa'

@login_required
def lista_empresas(request):
    """Lista todas las empresas con filtros y paginación"""
    empresas = Empresa.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    busqueda = request.GET.get('busqueda')
    estado = request.GET.get('estado')
    
    if busqueda:
        empresas = empresas.filter(
            Q(nombre__icontains=busqueda) | 
            Q(nit__icontains=busqueda) |
            Q(representante_legal__icontains=busqueda)
        )
    
    if estado == 'activo':
        empresas = empresas.filter(activo=True)
    elif estado == 'inactivo':
        empresas = empresas.filter(activo=False)
    
    # Paginación
    paginator = Paginator(empresas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'estado_seleccionado': estado,
        'total_empresas': Empresa.objects.filter(activo=True).count(),
    }
    
    return render(request, 'empresa/lista_empresas.html', context)

@login_required
def detalle_empresa(request, empresa_id):
    """Muestra el detalle de una empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Estadísticas de la empresa
    total_cuentas = empresa.cuentas.filter(activo=True).count()
    total_comprobantes = empresa.comprobantes.count()
    
    context = {
        'empresa': empresa,
        'total_cuentas': total_cuentas,
        'total_comprobantes': total_comprobantes,
    }
    
    return render(request, 'empresa/detalle_empresa.html', context)

@login_required
def crear_empresa(request):
    """Crea una nueva empresa"""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.usuario_creador = request.user
            empresa.save()
            messages.success(request, f'Empresa "{empresa.nombre}" creada exitosamente.')
            return redirect(DETALLE_EMPRESA_URL, empresa_id=empresa.id)
    else:
        form = EmpresaForm()
    
    return render(request, 'empresa/crear_empresa.html', {'form': form})

@login_required
def editar_empresa(request, empresa_id):
    """Edita una empresa existente"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Empresa "{empresa.nombre}" actualizada exitosamente.')
            return redirect(DETALLE_EMPRESA_URL, empresa_id=empresa.id)
    else:
        form = EmpresaForm(instance=empresa)
    
    return render(request, 'empresa/editar_empresa.html', {
        'form': form,
        'empresa': empresa
    })

@login_required
def eliminar_empresa(request, empresa_id):
    """Desactiva una empresa (no la elimina físicamente)"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        empresa.activo = False
        empresa.save()
        messages.success(request, f'Empresa "{empresa.nombre}" desactivada exitosamente.')
        return redirect('empresa:lista_empresas')
    
    return render(request, 'empresa/confirmar_eliminacion.html', {'empresa': empresa})

@login_required
def activar_empresa(request, empresa_id):
    """Reactiva una empresa desactivada"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    empresa.activo = True
    empresa.save()
    messages.success(request, f'Empresa "{empresa.nombre}" activada exitosamente.')
    return redirect(DETALLE_EMPRESA_URL, empresa_id=empresa.id)
