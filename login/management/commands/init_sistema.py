"""
Comando para inicializar el sistema con datos básicos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from empresa.models import Empresa
from login.models import Perfil


class Command(BaseCommand):
    help = 'Inicializa el sistema creando una empresa demo y asignándola a los usuarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre-empresa',
            type=str,
            default='Empresa Demo',
            help='Nombre de la empresa a crear',
        )
        parser.add_argument(
            '--nit',
            type=str,
            default='900000000-1',
            help='NIT de la empresa',
        )

    def handle(self, *args, **options):
        nombre_empresa = options['nombre_empresa']
        nit = options['nit']
        
        self.stdout.write(self.style.SUCCESS('\n=== Inicializando Sistema ===\n'))
        
        # 1. Verificar si ya existe una empresa
        empresa_existente = Empresa.objects.filter(activo=True).first()
        
        if empresa_existente:
            self.stdout.write(
                self.style.WARNING(
                    f'Ya existe una empresa activa: {empresa_existente.nombre}'
                )
            )
            empresa = empresa_existente
        else:
            # 2. Crear empresa
            self.stdout.write('Creando empresa...')
            empresa = Empresa.objects.create(
                nombre=nombre_empresa,
                nit=nit,
                direccion='Dirección Demo',
                telefono='3001234567',
                email='empresa@demo.com',
                representante_legal='Representante Legal',
                activo=True,
                usuario_creador=User.objects.first()
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Empresa creada: {empresa.nombre}')
            )
        
        # 3. Asignar empresa a todos los usuarios
        self.stdout.write('\nAsignando empresa a usuarios...')
        usuarios = User.objects.all()
        count = 0
        
        for user in usuarios:
            perfil, created = Perfil.objects.get_or_create(user=user)
            if not perfil.empresa:
                perfil.empresa = empresa
                perfil.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {user.username} → {empresa.nombre}')
                )
        
        # 4. Resumen
        self.stdout.write(self.style.SUCCESS(f'\n=== Resumen ==='))
        self.stdout.write(f'Empresa: {empresa.nombre}')
        self.stdout.write(f'NIT: {empresa.nit}')
        self.stdout.write(f'Usuarios asignados: {count}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ Sistema inicializado correctamente!'
            )
        )
        self.stdout.write(
            '\nPróximos pasos:'
        )
        self.stdout.write('  1. Accede al admin: /admin/')
        self.stdout.write('  2. Crea/edita empresas según necesites')
        self.stdout.write('  3. Reasigna usuarios a empresas diferentes si es necesario')
        self.stdout.write('  4. Prueba el Balance General: /cuentas/reportes/balance-general/')

