from django.contrib import admin
from .models import Cuenta

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo', 'naturaleza', 'acepta_movimiento', 'activo')
    list_filter = ('tipo', 'naturaleza', 'activo', 'empresa')
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('fecha_creacion',)
    list_per_page = 50
