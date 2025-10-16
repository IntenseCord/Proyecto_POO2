from django.db import models
from django.contrib.auth.models import User

class Empresa(models.Model):
    """Modelo para gestionar empresas en el sistema contable"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Empresa")
    nit = models.CharField(max_length=50, unique=True, verbose_name="NIT")
    direccion = models.CharField(max_length=300, verbose_name="Dirección")
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    representante_legal = models.CharField(max_length=200, verbose_name="Representante Legal")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='empresas_creadas')
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.nit}"
