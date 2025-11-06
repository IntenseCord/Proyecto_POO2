from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    path('', views.lista_comprobantes, name='lista_comprobantes'),
    path('crear/', views.crear_comprobante, name='crear_comprobante'),
    path('<int:comprobante_id>/', views.detalle_comprobante, name='detalle_comprobante'),
    path('<int:comprobante_id>/editar/', views.editar_comprobante, name='editar_comprobante'),
    path('<int:comprobante_id>/aprobar/', views.aprobar_comprobante, name='aprobar_comprobante'),
    path('<int:comprobante_id>/anular/', views.anular_comprobante, name='anular_comprobante'),
    path('<int:comprobante_id>/eliminar/', views.eliminar_comprobante, name='eliminar_comprobante'),
    
    # Documentos contables (Ventas, Notas, Recibos)
    path('documentos/venta/crear/', views.crear_factura_venta, name='crear_factura_venta'),
]
