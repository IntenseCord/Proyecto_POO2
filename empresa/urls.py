from django.urls import path
from . import views

app_name = 'empresa'

urlpatterns = [
    path('', views.lista_empresas, name='lista_empresas'),
    path('crear/', views.crear_empresa, name='crear_empresa'),
    path('<int:empresa_id>/', views.detalle_empresa, name='detalle_empresa'),
    path('<int:empresa_id>/editar/', views.editar_empresa, name='editar_empresa'),
    path('<int:empresa_id>/eliminar/', views.eliminar_empresa, name='eliminar_empresa'),
    path('<int:empresa_id>/activar/', views.activar_empresa, name='activar_empresa'),
]
