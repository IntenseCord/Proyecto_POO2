from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    # Gestión de Cuentas
    path('', views.lista_cuentas, name='lista_cuentas'),
    path('crear/', views.crear_cuenta, name='crear_cuenta'),
    path('arbol/<int:empresa_id>/', views.arbol_cuentas, name='arbol_cuentas'),
    path('<int:cuenta_id>/', views.detalle_cuenta, name='detalle_cuenta'),
    path('<int:cuenta_id>/editar/', views.editar_cuenta, name='editar_cuenta'),
    path('<int:cuenta_id>/eliminar/', views.eliminar_cuenta, name='eliminar_cuenta'),
    
    # Reportes Financieros
    path('reportes/', views.reportes_menu, name='reportes_menu'),
    path('reportes/balance-comprobacion/', views.balance_comprobacion_view, name='balance_comprobacion'),
    path('reportes/estado-resultados/', views.estado_resultados_view, name='estado_resultados'),
    path('reportes/balance-general/', views.balance_general_view, name='balance_general'),
]
