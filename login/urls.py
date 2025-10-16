from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    # Página principal del módulo de login
    path('', views.login_view, name='login'),
    
    # Páginas públicas
    path('inicio/', views.landing_view, name='landing'),
    path('registro/', views.registro_view, name='registro'),
    
    # Verificación y recuperación
    path('verificar/<uuid:token>/', views.verificar_email_view, name='verificar_email'),
    path('solicitar-recuperacion/', views.solicitar_recuperacion_view, name='solicitar_recuperacion'),
    path('restablecer/<uuid:token>/', views.restablecer_contrasena_view, name='restablecer_contrasena'),
    
    # Páginas privadas (requieren autenticación)
    path('perfil/', views.perfil_view, name='perfil'),
    path('logout/', views.logout_view, name='logout'),
]
