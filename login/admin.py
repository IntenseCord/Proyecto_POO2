from django.contrib import admin
from .models import VerificacionEmail, Perfil, RecuperacionContrasena, IntentoLogin

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'empresa', 'telefono', 'fecha_actualizacion')
    list_filter = ('empresa',)
    search_fields = ('user__username', 'user__email', 'telefono', 'empresa__nombre')
    readonly_fields = ('fecha_actualizacion',)
    autocomplete_fields = ['empresa']
    
    fieldsets = (
        ('Información de Usuario', {
            'fields': ('user', 'empresa')
        }),
        ('Información Personal', {
            'fields': ('foto', 'telefono', 'direccion', 'fecha_nacimiento', 'bio')
        }),
        ('Metadatos', {
            'fields': ('fecha_actualizacion',),
            'classes': ('collapse',)
        }),
    )

@admin.register(VerificacionEmail)
class VerificacionEmailAdmin(admin.ModelAdmin):
    list_display = ('user', 'verificado', 'fecha_creacion', 'fecha_verificacion')
    list_filter = ('verificado', 'fecha_creacion')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'fecha_creacion', 'fecha_verificacion')

@admin.register(RecuperacionContrasena)
class RecuperacionContrasenaAdmin(admin.ModelAdmin):
    list_display = ('user', 'usado', 'fecha_creacion', 'fecha_uso', 'ip_address')
    list_filter = ('usado', 'fecha_creacion')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('token', 'fecha_creacion', 'fecha_uso', 'ip_address')
    ordering = ('-fecha_creacion',)

@admin.register(IntentoLogin)
class IntentoLoginAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'intentos', 'bloqueado_hasta', 'ultimo_intento')
    list_filter = ('ultimo_intento', 'intentos')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('fecha_creacion', 'ultimo_intento')
    ordering = ('-ultimo_intento',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando
            return self.readonly_fields + ('username', 'ip_address')
        return self.readonly_fields
