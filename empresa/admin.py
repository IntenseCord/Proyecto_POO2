from django.contrib import admin
from .models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nit', 'representante_legal', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'nit', 'representante_legal')
    readonly_fields = ('fecha_creacion',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.usuario_creador = request.user
        super().save_model(request, obj, form, change)
