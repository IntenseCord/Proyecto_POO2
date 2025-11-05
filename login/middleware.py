"""
Middleware personalizado para verificación de empresa asignada
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from login.utils import usuario_tiene_empresa


class EmpresaRequeridaMiddleware:
    """
    Middleware que verifica que el usuario tenga una empresa asignada
    antes de acceder a ciertas vistas de reportes
    """
    
    # URLs que requieren empresa asignada
    RUTAS_PROTEGIDAS = [
        '/cuentas/reportes/',
    ]
    
    # URLs que NO requieren empresa (excepciones)
    RUTAS_EXCEPTUADAS = [
        '/admin/',
        '/login/',
        '/logout/',
        '/registro/',
        '/dashboard/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar si es una ruta protegida
        path = request.path
        
        # Verificar excepciones primero
        for excepcion in self.RUTAS_EXCEPTUADAS:
            if path.startswith(excepcion):
                return self.get_response(request)
        
        # Verificar si necesita protección
        requiere_empresa = any(path.startswith(ruta) for ruta in self.RUTAS_PROTEGIDAS)
        
        if requiere_empresa and request.user.is_authenticated:
            if not usuario_tiene_empresa(request.user):
                messages.warning(
                    request,
                    'No tienes una empresa asignada. Contacta al administrador para acceder a los reportes.'
                )
                return redirect('dashboard:home')
        
        response = self.get_response(request)
        return response

