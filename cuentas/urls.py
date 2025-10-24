from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    path('', views.lista_cuentas, name='lista_cuentas'),
    path('crear/', views.crear_cuenta, name='crear_cuenta'),
    path('arbol/<int:empresa_id>/', views.arbol_cuentas, name='arbol_cuentas'),
    path('<int:cuenta_id>/', views.detalle_cuenta, name='detalle_cuenta'),
    path('<int:cuenta_id>/editar/', views.editar_cuenta, name='editar_cuenta'),
    path('<int:cuenta_id>/eliminar/', views.eliminar_cuenta, name='eliminar_cuenta'),
]
