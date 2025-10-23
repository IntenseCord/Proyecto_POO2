from django.contrib import admin
from .models import Categoria, Producto, MovimientoInventario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('fecha_creacion',)
    ordering = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'cantidad', 'precio_unitario', 'valor_total', 'necesita_restock', 'estado')
    list_filter = ('categoria', 'estado', 'fecha_creacion')
    search_fields = ('codigo', 'nombre', 'descripcion')
    list_editable = ('cantidad', 'precio_unitario', 'estado')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'valor_total')
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria')
        }),
        ('Inventario', {
            'fields': ('cantidad', 'stock_minimo', 'precio_unitario')
        }),
        ('Estado y Fechas', {
            'fields': ('estado', 'usuario_creador', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def valor_total(self, obj):
        return f"${obj.valor_total:,.2f}"
    valor_total.short_description = 'Valor Total'
    
    def necesita_restock(self, obj):
        return "⚠️ Sí" if obj.necesita_restock else "✅ No"
    necesita_restock.short_description = 'Necesita Restock'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.usuario_creador = request.user
        super().save_model(request, obj, form, change)

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'motivo', 'fecha', 'usuario')
    list_filter = ('tipo', 'fecha', 'producto__categoria')
    search_fields = ('producto__nombre', 'producto__codigo', 'motivo')
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Movimiento', {
            'fields': ('producto', 'tipo', 'cantidad', 'motivo')
        }),
        ('Detalles', {
            'fields': ('observaciones', 'usuario', 'fecha'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.usuario = request.user
        super().save_model(request, obj, form, change)
