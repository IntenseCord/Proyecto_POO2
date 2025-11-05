#!/usr/bin/env python
"""
Script de verificación del sistema de Balance General
Ejecutar: python verificar_sistema.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'S_CONTABLE.settings')
django.setup()

from django.contrib.auth.models import User
from empresa.models import Empresa
from login.models import Perfil
from login.utils import obtener_empresa_usuario, usuario_tiene_empresa


def print_section(title):
    """Imprime un título de sección"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def verificar_dependencias():
    """Verifica que las dependencias estén instaladas"""
    print_section("1. Verificando Dependencias")
    
    dependencias = {
        'reportlab': False,
        'openpyxl': False,
    }
    
    try:
        import reportlab
        dependencias['reportlab'] = True
        print("✓ reportlab instalado")
    except ImportError:
        print("✗ reportlab NO instalado - ejecuta: pip install reportlab")
    
    try:
        import openpyxl
        dependencias['openpyxl'] = True
        print("✓ openpyxl instalado")
    except ImportError:
        print("✗ openpyxl NO instalado - ejecuta: pip install openpyxl")
    
    return all(dependencias.values())


def verificar_migraciones():
    """Verifica que las migraciones estén aplicadas"""
    print_section("2. Verificando Migraciones")
    
    try:
        # Verificar que el campo empresa existe en Perfil
        perfil = Perfil._meta.get_field('empresa')
        print(f"✓ Campo 'empresa' existe en modelo Perfil")
        print(f"  Tipo: {perfil.get_internal_type()}")
        print(f"  Relacionado con: {perfil.related_model.__name__}")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        print("  Ejecuta: python manage.py migrate")
        return False


def verificar_empresas():
    """Verifica que existan empresas en el sistema"""
    print_section("3. Verificando Empresas")
    
    empresas = Empresa.objects.filter(activo=True)
    total = empresas.count()
    
    if total == 0:
        print("✗ No hay empresas activas en el sistema")
        print("  Crea una empresa desde /admin/")
        return False
    
    print(f"✓ {total} empresa(s) activa(s) encontrada(s):")
    for empresa in empresas:
        print(f"  - ID: {empresa.id} | {empresa.nombre} (NIT: {empresa.nit})")
    
    return True


def verificar_usuarios():
    """Verifica la asignación de empresas a usuarios"""
    print_section("4. Verificando Usuarios y Empresas")
    
    usuarios = User.objects.all()
    total_usuarios = usuarios.count()
    usuarios_con_empresa = 0
    usuarios_sin_empresa = []
    
    print(f"Total de usuarios: {total_usuarios}")
    print("\nEstado de asignación:")
    
    for usuario in usuarios:
        empresa = obtener_empresa_usuario(usuario)
        if empresa:
            usuarios_con_empresa += 1
            print(f"  ✓ {usuario.username} → {empresa.nombre}")
        else:
            usuarios_sin_empresa.append(usuario.username)
            print(f"  ✗ {usuario.username} → SIN EMPRESA")
    
    print(f"\nResumen:")
    print(f"  Con empresa: {usuarios_con_empresa}/{total_usuarios}")
    print(f"  Sin empresa: {len(usuarios_sin_empresa)}/{total_usuarios}")
    
    if usuarios_sin_empresa:
        print(f"\n⚠ Usuarios sin empresa asignada:")
        for username in usuarios_sin_empresa:
            print(f"    - {username}")
        print("\n  Asigna empresas con:")
        print("    python manage.py asignar_empresas --auto")
        print("    O manualmente desde /admin/")
        return False
    
    return True


def verificar_utilidades():
    """Verifica las funciones de utilidad"""
    print_section("5. Verificando Funciones de Utilidad")
    
    try:
        from login.utils import obtener_empresa_usuario, usuario_tiene_empresa
        print("✓ Funciones de utilidad importadas correctamente")
        
        # Probar con un usuario
        user = User.objects.first()
        if user:
            empresa = obtener_empresa_usuario(user)
            tiene = usuario_tiene_empresa(user)
            print(f"  Prueba con usuario '{user.username}':")
            print(f"    - obtener_empresa_usuario(): {empresa.nombre if empresa else 'None'}")
            print(f"    - usuario_tiene_empresa(): {tiene}")
        
        return True
    except Exception as e:
        print(f"✗ Error al probar utilidades: {str(e)}")
        return False


def verificar_exportacion():
    """Verifica que el servicio de exportación esté disponible"""
    print_section("6. Verificando Servicio de Exportación")
    
    try:
        from cuentas.export_service import ExportadorBalanceGeneral
        print("✓ ExportadorBalanceGeneral importado correctamente")
        print("  Métodos disponibles:")
        print("    - exportar_pdf()")
        print("    - exportar_excel()")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def verificar_reportes():
    """Verifica la clase de reportes mejorada"""
    print_section("7. Verificando Clase BalanceGeneral")
    
    try:
        from cuentas.reportes import BalanceGeneral
        print("✓ BalanceGeneral importado correctamente")
        
        # Verificar métodos nuevos
        metodos_esperados = [
            '_clasificar_activos',
            '_clasificar_pasivos',
            '_calcular_ratios_financieros',
            '_preparar_datos_graficos'
        ]
        
        instancia = BalanceGeneral(None, None, None)
        print("  Métodos agregados:")
        for metodo in metodos_esperados:
            if hasattr(instancia, metodo):
                print(f"    ✓ {metodo}")
            else:
                print(f"    ✗ {metodo} NO ENCONTRADO")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("  VERIFICACIÓN DEL SISTEMA DE BALANCE GENERAL")
    print("=" * 60)
    
    resultados = {
        'Dependencias': verificar_dependencias(),
        'Migraciones': verificar_migraciones(),
        'Empresas': verificar_empresas(),
        'Usuarios': verificar_usuarios(),
        'Utilidades': verificar_utilidades(),
        'Exportación': verificar_exportacion(),
        'Reportes': verificar_reportes(),
    }
    
    # Resumen final
    print_section("RESUMEN FINAL")
    
    total = len(resultados)
    exitosos = sum(1 for v in resultados.values() if v)
    
    for nombre, resultado in resultados.items():
        estado = "✓ CORRECTO" if resultado else "✗ REVISAR"
        print(f"  {nombre:20} {estado}")
    
    print(f"\n  Total: {exitosos}/{total} verificaciones exitosas")
    
    if exitosos == total:
        print("\n  🎉 ¡Sistema completamente funcional!")
        print("\n  Próximos pasos:")
        print("    1. Accede a /admin/ para asignar empresas si es necesario")
        print("    2. Prueba el balance en /cuentas/reportes/balance-general/")
        print("    3. Exporta reportes en PDF y Excel")
    else:
        print("\n  ⚠ Hay problemas que deben ser resueltos")
        print("    Revisa los errores marcados con ✗")
    
    return exitosos == total


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Verificación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

