"""
Script de prueba para verificar funcionalidades del Balance General
Ejecutar con: python test_balance_general.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'S_CONTABLE.settings')
django.setup()

from django.contrib.auth.models import User
from empresa.models import Empresa
from cuentas.models import Cuenta, TipoCuenta
from cuentas.reportes import BalanceGeneral
from login.utils import obtener_empresa_usuario, usuario_tiene_empresa
from decimal import Decimal


def verificar_usuarios():
    """Verifica que los usuarios tengan empresas asignadas"""
    print("\n" + "="*60)
    print("1. VERIFICACIÓN DE USUARIOS Y EMPRESAS")
    print("="*60)
    
    usuarios = User.objects.all()
    print(f"\nTotal de usuarios: {usuarios.count()}")
    
    for usuario in usuarios:
        empresa = obtener_empresa_usuario(usuario)
        tiene_empresa = usuario_tiene_empresa(usuario)
        
        status = "✓" if tiene_empresa else "✗"
        empresa_nombre = empresa.nombre if empresa else "Sin empresa"
        
        print(f"{status} {usuario.username:20} → {empresa_nombre}")
    
    usuarios_sin_empresa = User.objects.filter(perfil__empresa__isnull=True).count()
    if usuarios_sin_empresa > 0:
        print(f"\n⚠️  {usuarios_sin_empresa} usuarios sin empresa asignada")
        print("   Ejecuta: python manage.py asignar_empresas --auto")
    else:
        print(f"\n✓ Todos los usuarios tienen empresa asignada")


def verificar_empresas():
    """Verifica empresas activas"""
    print("\n" + "="*60)
    print("2. VERIFICACIÓN DE EMPRESAS")
    print("="*60)
    
    empresas = Empresa.objects.filter(activo=True)
    print(f"\nEmpresas activas: {empresas.count()}")
    
    for empresa in empresas:
        usuarios_count = empresa.usuarios.count()
        cuentas_count = empresa.cuentas.filter(esta_activa=True).count()
        
        print(f"\n  • {empresa.nombre}")
        print(f"    NIT: {empresa.nit}")
        print(f"    Usuarios: {usuarios_count}")
        print(f"    Cuentas activas: {cuentas_count}")


def verificar_cuentas():
    """Verifica estructura de cuentas"""
    print("\n" + "="*60)
    print("3. VERIFICACIÓN DE CUENTAS CONTABLES")
    print("="*60)
    
    for tipo in TipoCuenta:
        count = Cuenta.objects.filter(tipo=tipo.value, esta_activa=True).count()
        print(f"  {tipo.label:15} : {count:4} cuentas")
    
    total = Cuenta.objects.filter(esta_activa=True).count()
    print(f"\n  {'TOTAL':15} : {total:4} cuentas")


def probar_balance_general():
    """Prueba la generación del balance general"""
    print("\n" + "="*60)
    print("4. PRUEBA DE BALANCE GENERAL")
    print("="*60)
    
    # Obtener primera empresa con usuarios
    empresa = Empresa.objects.filter(activo=True, usuarios__isnull=False).first()
    
    if not empresa:
        print("✗ No hay empresas con usuarios asignados")
        return
    
    print(f"\nGenerando balance para: {empresa.nombre}")
    
    try:
        # Generar balance
        reporte = BalanceGeneral(empresa, None, None)
        resultado = reporte.generar()
        
        print("\n  ✓ Balance generado exitosamente")
        print(f"\n  Activos:")
        print(f"    - Total: ${resultado['totales']['activos']:,.2f}")
        print(f"    - Cuentas: {len(resultado['activos'])}")
        
        print(f"\n  Pasivos:")
        print(f"    - Total: ${resultado['totales']['pasivos']:,.2f}")
        print(f"    - Cuentas: {len(resultado['pasivos'])}")
        
        print(f"\n  Patrimonio:")
        print(f"    - Total: ${resultado['totales']['patrimonio']:,.2f}")
        print(f"    - Cuentas: {len(resultado['patrimonios'])}")
        print(f"    - Utilidad período: ${resultado['utilidad_periodo']:,.2f}")
        
        print(f"\n  Ratios Financieros:")
        for nombre, valor in resultado['ratios'].items():
            if 'capital' in nombre:
                print(f"    - {nombre.replace('_', ' ').title()}: ${valor:,.2f}")
            else:
                print(f"    - {nombre.replace('_', ' ').title()}: {valor:.2f}")
        
        print(f"\n  Ecuación Contable:")
        if resultado['ecuacion_balanceada']:
            print(f"    ✓ Balanceada")
        else:
            print(f"    ✗ Desbalanceada (diferencia: ${resultado['diferencia']:,.2f})")
        
        print(f"\n  Datos para gráficos:")
        print(f"    - Activos top: {len(resultado['datos_graficos']['activos_labels'])} elementos")
        print(f"    - Pasivos top: {len(resultado['datos_graficos']['pasivos_labels'])} elementos")
        
    except Exception as e:
        print(f"  ✗ Error al generar balance: {str(e)}")
        import traceback
        traceback.print_exc()


def probar_exportacion():
    """Prueba las funcionalidades de exportación"""
    print("\n" + "="*60)
    print("5. VERIFICACIÓN DE EXPORTACIÓN")
    print("="*60)
    
    try:
        import reportlab
        print("  ✓ ReportLab instalado")
    except ImportError:
        print("  ✗ ReportLab NO instalado")
        print("    Ejecuta: pip install reportlab")
    
    try:
        import openpyxl
        print("  ✓ openpyxl instalado")
    except ImportError:
        print("  ✗ openpyxl NO instalado")
        print("    Ejecuta: pip install openpyxl")


def verificar_rutas():
    """Verifica que las rutas estén configuradas"""
    print("\n" + "="*60)
    print("6. VERIFICACIÓN DE RUTAS")
    print("="*60)
    
    from django.urls import reverse
    
    rutas = [
        ('cuentas:balance_general', 'Balance General'),
        ('cuentas:balance_general_pdf', 'Exportar PDF'),
        ('cuentas:balance_general_excel', 'Exportar Excel'),
        ('cuentas:balance_comprobacion', 'Balance Comprobación'),
        ('cuentas:estado_resultados', 'Estado Resultados'),
    ]
    
    for nombre_ruta, descripcion in rutas:
        try:
            url = reverse(nombre_ruta)
            print(f"  ✓ {descripcion:25} : {url}")
        except Exception as e:
            print(f"  ✗ {descripcion:25} : Error")


def main():
    """Ejecuta todas las verificaciones"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "TEST BALANCE GENERAL AVANZADO" + " "*19 + "║")
    print("╚" + "="*58 + "╝")
    
    verificar_usuarios()
    verificar_empresas()
    verificar_cuentas()
    probar_balance_general()
    probar_exportacion()
    verificar_rutas()
    
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print("\n✓ Tests completados")
    print("\nPróximos pasos:")
    print("  1. Inicia el servidor: python manage.py runserver")
    print("  2. Accede a: http://127.0.0.1:8000/cuentas/reportes/balance-general/")
    print("  3. Genera un reporte con fechas opcionales")
    print("  4. Prueba la exportación PDF y Excel")
    print("\n")


if __name__ == '__main__':
    main()

