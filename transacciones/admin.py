from django.contrib import admin
from .models import Comprobante, DetalleComprobante

class DetalleComprobanteInline(admin.TabularInline):
    model = DetalleComprobante
    extra = 1
    fields = ('cuenta', 'descripcion', 'debito', 'credito', 'orden')

@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'fecha', 'descripcion', 'total_debito', 'total_credito', 'estado')
    list_filter = ('tipo', 'estado', 'fecha', 'empresa')
    search_fields = ('numero', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_aprobacion')
    inlines = [DetalleComprobanteInline]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creador = request.user
        super().save_model(request, obj, form, change)

@admin.register(DetalleComprobante)
class DetalleComprobanteAdmin(admin.ModelAdmin):
    list_display = ('comprobante', 'cuenta', 'descripcion', 'debito', 'credito')
    list_filter = ('comprobante__empresa', 'comprobante__tipo')
    search_fields = ('descripcion', 'cuenta__nombre', 'cuenta__codigo')
