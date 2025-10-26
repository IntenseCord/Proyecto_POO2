from django.contrib import admin
from .models import Cuenta, Activo, Pasivo, Patrimonio, Ingreso, Gasto, Costo

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo', 'naturaleza', 'acepta_movimiento', 'esta_activa', 'calcular_saldo')
    list_filter = ('tipo', 'naturaleza', 'esta_activa', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion',)
    list_per_page = 50
    
    def calcular_saldo(self, obj):
        """Muestra el saldo calculado de la cuenta"""
        try:
            saldo = obj.calcular_saldo()
            return f"${saldo:,.2f}"
        except Exception:
            return "N/A"
    calcular_saldo.short_description = 'Saldo'


# Registrar las clases hijas con herencia
@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'es_corriente', 'naturaleza', 'esta_activa')
    list_filter = ('es_corriente', 'esta_activa', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion', 'tipo', 'naturaleza')


@admin.register(Pasivo)
class PasivoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'es_corriente', 'naturaleza', 'esta_activa')
    list_filter = ('es_corriente', 'esta_activa', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion', 'tipo', 'naturaleza')


@admin.register(Patrimonio)
class PatrimonioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'naturaleza', 'esta_activa')
    list_filter = ('esta_activa', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion', 'tipo', 'naturaleza')


@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'naturaleza', 'esta_activa')
    list_filter = ('esta_activa', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion', 'tipo', 'naturaleza')


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'naturaleza', 'esta_activa')
    list_filter = ('esta_activa', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion', 'tipo', 'naturaleza')


@admin.register(Costo)
class CostoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'naturaleza', 'esta_activa')
    list_filter = ('esta_activa', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion', 'tipo', 'naturaleza')
