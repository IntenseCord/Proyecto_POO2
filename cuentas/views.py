from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from .models import Cuenta, TipoCuenta
from .forms import CuentaForm, FiltroCuentaForm
from empresa.models import Empresa

@login_required
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
        'total_cuentas': Cuenta.objects.filter(activo=True).count(),
    }
    
    return render(request, 'cuentas/lista_cuentas.html', context)

@login_required
def arbol_cuentas(request, empresa_id):
    """Muestra el árbol jerárquico de cuentas de una empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Obtener cuentas de nivel 1 (sin padre)
    cuentas_raiz = Cuenta.objects.filter(
        empresa=empresa,
        cuenta_padre__isnull=True,
        activo=True
    ).order_by('codigo')
    
    context = {
        'empresa': empresa,
        'cuentas_raiz': cuentas_raiz,
    }
    
    return render(request, 'cuentas/arbol_cuentas.html', context)

@login_required
def detalle_cuenta(request, cuenta_id):
    """Muestra el detalle de una cuenta"""
    cuenta = get_object_or_404(Cuenta.objects.select_related('empresa', 'cuenta_padre'), id=cuenta_id)
    
    # Obtener subcuentas
    subcuentas = cuenta.subcuentas.filter(activo=True).order_by('codigo')
    
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
            return redirect('cuentas:detalle_cuenta', cuenta_id=cuenta.id)
    else:
        form = CuentaForm()
    
    return render(request, 'cuentas/crear_cuenta.html', {'form': form})

@login_required
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
            return redirect('cuentas:detalle_cuenta', cuenta_id=cuenta.id)
    else:
        form = CuentaForm(instance=cuenta)
    
    return render(request, 'cuentas/editar_cuenta.html', {
        'form': form,
        'cuenta': cuenta
    })

@login_required
def eliminar_cuenta(request, cuenta_id):
    """Desactiva una cuenta (no la elimina físicamente)"""
    cuenta = get_object_or_404(Cuenta, id=cuenta_id)
    
    # Verificar si tiene movimientos
    if cuenta.movimientos.exists():
        messages.error(request, 'No se puede desactivar una cuenta con movimientos registrados.')
        return redirect('cuentas:detalle_cuenta', cuenta_id=cuenta.id)
    
    # Verificar si tiene subcuentas activas
    if cuenta.subcuentas.filter(activo=True).exists():
        messages.error(request, 'No se puede desactivar una cuenta con subcuentas activas.')
        return redirect('cuentas:detalle_cuenta', cuenta_id=cuenta.id)
    
    if request.method == 'POST':
        cuenta.activo = False
        cuenta.save()
        messages.success(request, f'Cuenta "{cuenta.codigo} - {cuenta.nombre}" desactivada exitosamente.')
        return redirect('cuentas:lista_cuentas')
    
    return render(request, 'cuentas/confirmar_eliminacion.html', {'cuenta': cuenta})
