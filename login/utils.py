"""
Utilidades para el módulo de login y gestión de usuarios
"""
from django.contrib.auth.models import User
from empresa.models import Empresa


def obtener_empresa_usuario(user):
    """
    Obtiene la empresa asociada al usuario logueado.
    
    Args:
        user: Instancia de User
        
    Returns:
        Empresa: Instancia de la empresa del usuario o None si no tiene empresa asignada
        
    Raises:
        ValueError: Si el usuario no tiene perfil o empresa asignada
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        if hasattr(user, 'perfil') and user.perfil.empresa:
            return user.perfil.empresa
        
        # Si es superusuario y no tiene empresa, retornar la primera empresa disponible
        if user.is_superuser:
            return Empresa.objects.filter(activo=True).first()
        
        return None
    except Exception as e:
        return None


def usuario_tiene_empresa(user):
    """
    Verifica si el usuario tiene una empresa asignada.
    
    Args:
        user: Instancia de User
        
    Returns:
        bool: True si tiene empresa, False en caso contrario
    """
    empresa = obtener_empresa_usuario(user)
    return empresa is not None

