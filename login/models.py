from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import timedelta
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    """Modelo para el perfil extendido del usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True, default='perfiles/default.png')
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario"""
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()

class VerificacionEmail(models.Model):
    """Modelo para verificación de email de usuarios"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verificacion')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    verificado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Verificación de Email"
        verbose_name_plural = "Verificaciones de Email"
    
    def __str__(self):
        return f"Verificación de {self.user.username}"
    
    def es_valido(self):
        """Verifica si el token aún es válido (24 horas)"""
        if self.verificado:
            return True
        expiracion = self.fecha_creacion + timedelta(hours=24)
        return timezone.now() < expiracion

class RecuperacionContrasena(models.Model):
    """Modelo para recuperación de contraseña"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recuperaciones')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    usado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Recuperación de Contraseña"
        verbose_name_plural = "Recuperaciones de Contraseña"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Recuperación de {self.user.username} - {self.fecha_creacion}"
    
    def es_valido(self):
        """Verifica si el token aún es válido (1 hora)"""
        if self.usado:
            return False
        expiracion = self.fecha_creacion + timedelta(hours=1)
        return timezone.now() < expiracion

class IntentoLogin(models.Model):
    """Modelo para rastrear intentos de login fallidos"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    intentos = models.IntegerField(default=1)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    ultimo_intento = models.DateTimeField(auto_now=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Intento de Login"
        verbose_name_plural = "Intentos de Login"
        unique_together = ['username', 'ip_address']
        ordering = ['-ultimo_intento']
    
    def __str__(self):
        return f"{self.username} desde {self.ip_address} - {self.intentos} intentos"
    
    def esta_bloqueado(self):
        """Verifica si el usuario está bloqueado"""
        if self.bloqueado_hasta:
            if timezone.now() < self.bloqueado_hasta:
                return True
            else:
                # El bloqueo expiró, resetear
                self.intentos = 0
                self.bloqueado_hasta = None
                self.save()
                return False
        return False
    
    def incrementar_intentos(self):
        """Incrementa el contador de intentos y bloquea si es necesario"""
        self.intentos += 1
        
        # Bloquear después de 5 intentos fallidos
        if self.intentos >= 5:
            self.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
        
        self.save()
    
    def resetear(self):
        """Resetea los intentos después de un login exitoso"""
        self.intentos = 0
        self.bloqueado_hasta = None
        self.save()
