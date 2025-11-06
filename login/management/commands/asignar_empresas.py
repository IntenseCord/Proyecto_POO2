"""
Comando de gestión para asignar empresas a usuarios existentes
Uso: python manage.py asignar_empresas
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from empresa.models import Empresa
from login.models import Perfil


class Command(BaseCommand):
    help = 'Asigna empresas a usuarios que no tienen una asignada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID de la empresa a asignar a todos los usuarios sin empresa',
        )
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Asigna automáticamente la primera empresa disponible',
        )

    def handle(self, *args, **options):
        usuarios_sin_empresa = self._obtener_usuarios_sin_empresa()
        if not usuarios_sin_empresa.exists():
            self.stdout.write(self.style.SUCCESS('✓ Todos los usuarios ya tienen empresa asignada'))
            return
        self.stdout.write(f'Usuarios sin empresa: {usuarios_sin_empresa.count()}')

        empresa = self._seleccionar_empresa(options)
        if not empresa:
            return

        count = self._asignar_empresas_a_usuarios(usuarios_sin_empresa, empresa)
        self.stdout.write(self.style.SUCCESS(f'\n✓ {count} usuarios actualizados correctamente'))
        self.stdout.write(self.style.SUCCESS(f'✓ Empresa asignada: {empresa.nombre}'))

    def _obtener_usuarios_sin_empresa(self):
        return User.objects.filter(perfil__empresa__isnull=True)

    def _seleccionar_empresa(self, options):
        if options['empresa_id']:
            try:
                return Empresa.objects.get(id=options['empresa_id'])
            except Empresa.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ Empresa con ID {options["empresa_id"]} no existe'))
                return None
        if options['auto']:
            empresa = Empresa.objects.filter(activo=True).first()
            if not empresa:
                self.stdout.write(self.style.ERROR('✗ No hay empresas activas disponibles'))
            return empresa
        return self._seleccionar_empresa_interactivo()

    def _seleccionar_empresa_interactivo(self):
        empresas = Empresa.objects.filter(activo=True)
        if not empresas.exists():
            self.stdout.write(self.style.ERROR('✗ No hay empresas activas disponibles'))
            return None
        self.stdout.write('\nEmpresas disponibles:')
        for emp in empresas:
            self.stdout.write(f'  {emp.id}. {emp.nombre} (NIT: {emp.nit})')
        empresa_id = input('\nIngrese el ID de la empresa a asignar (o "q" para salir): ')
        if empresa_id.lower() == 'q':
            self.stdout.write('Operación cancelada')
            return None
        try:
            return Empresa.objects.get(id=int(empresa_id))
        except (ValueError, Empresa.DoesNotExist):
            self.stdout.write(self.style.ERROR('✗ ID de empresa inválido'))
            return None

    def _asignar_empresas_a_usuarios(self, usuarios_qs, empresa):
        count = 0
        for usuario in usuarios_qs:
            if hasattr(usuario, 'perfil'):
                usuario.perfil.empresa = empresa
                usuario.perfil.save()
                count += 1
                self.stdout.write(f'  ✓ {usuario.username} → {empresa.nombre}')
            else:
                Perfil.objects.create(user=usuario, empresa=empresa)
                count += 1
                self.stdout.write(f'  ✓ {usuario.username} → {empresa.nombre} (perfil creado)')
        return count
