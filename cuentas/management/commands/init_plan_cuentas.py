"""
Comando de Django para inicializar el plan de cuentas básico.
Uso: python manage.py init_plan_cuentas --empresa=<empresa_id>
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from empresa.models import Empresa
from cuentas.models import Cuenta, Activo, Pasivo, Patrimonio, Ingreso, Costo, Gasto, TipoCuenta


class Command(BaseCommand):
    help = 'Inicializa el plan de cuentas con cuentas esenciales para una empresa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=int,
            help='ID de la empresa para la cual crear el plan de cuentas',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la creación sin pedir confirmación',
        )

    def handle(self, *args, **options):
        empresa = self._get_empresa(options)
        self.stdout.write(self.style.SUCCESS(f'\nInicializando plan de cuentas para: {empresa.nombre}'))
        if self._abort_if_exists(empresa, options):
            return
        cuentas_creadas = self._crear_plan_basico(empresa)
        self.stdout.write(self.style.SUCCESS(f'\n✓ Proceso completado: {cuentas_creadas} cuentas creadas'))
        self.stdout.write(self.style.SUCCESS(f'Total de cuentas en la empresa: {Cuenta.objects.filter(empresa=empresa).count()}'))

    def _get_empresa(self, options):
        empresa_id = options.get('empresa')
        if not empresa_id:
            empresa = Empresa.objects.filter(activo=True).first()
            if not empresa:
                raise CommandError('No hay empresas activas en el sistema')
            return empresa
        try:
            return Empresa.objects.get(id=empresa_id, activo=True)
        except Empresa.DoesNotExist:
            raise CommandError(f'No se encontró la empresa con ID {empresa_id}')

    def _abort_if_exists(self, empresa, options):
        cuentas_existentes = Cuenta.objects.filter(empresa=empresa).count()
        if cuentas_existentes > 0 and not options.get('force'):
            self.stdout.write(self.style.WARNING(f'La empresa ya tiene {cuentas_existentes} cuentas.'))
            self.stdout.write(self.style.WARNING('Use --force para agregar más cuentas sin confirmación'))
            return True
        return False

    def _plan_cuentas_basico(self):
        return [
            {
                'codigo': '1105',
                'nombre': 'Inventario de Mercancías',
                'tipo': TipoCuenta.ACTIVO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
                'es_corriente': True,
            },
            {
                'codigo': '1110',
                'nombre': 'Bancos',
                'tipo': TipoCuenta.ACTIVO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
                'es_corriente': True,
            },
            {
                'codigo': '1305',
                'nombre': 'Clientes',
                'tipo': TipoCuenta.ACTIVO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
                'es_corriente': True,
            },
            {
                'codigo': '1520',
                'nombre': 'Maquinaria y Equipo',
                'tipo': TipoCuenta.ACTIVO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
                'es_corriente': False,
            },
            {
                'codigo': '2105',
                'nombre': 'Proveedores Nacionales',
                'tipo': TipoCuenta.PASIVO,
                'naturaleza': 'CREDITO',
                'nivel': 2,
                'acepta_movimiento': True,
                'es_corriente': True,
            },
            {
                'codigo': '2335',
                'nombre': 'Costos y Gastos por Pagar',
                'tipo': TipoCuenta.PASIVO,
                'naturaleza': 'CREDITO',
                'nivel': 2,
                'acepta_movimiento': True,
                'es_corriente': True,
            },
            {
                'codigo': '2365',
                'nombre': 'Retención en la Fuente',
                'tipo': TipoCuenta.PASIVO,
                'naturaleza': 'CREDITO',
                'nivel': 2,
                'acepta_movimiento': True,
                'es_corriente': True,
            },
            {
                'codigo': '3105',
                'nombre': 'Capital Social',
                'tipo': TipoCuenta.PATRIMONIO,
                'naturaleza': 'CREDITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
            {
                'codigo': '3605',
                'nombre': 'Utilidades Acumuladas',
                'tipo': TipoCuenta.PATRIMONIO,
                'naturaleza': 'CREDITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
            {
                'codigo': '4135',
                'nombre': 'Comercio al por Mayor y al por Menor',
                'tipo': TipoCuenta.INGRESO,
                'naturaleza': 'CREDITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
            {
                'codigo': '4175',
                'nombre': 'Devoluciones en Ventas',
                'tipo': TipoCuenta.INGRESO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
            {
                'codigo': '6135',
                'nombre': 'Costo de Ventas',
                'tipo': TipoCuenta.COSTO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
            {
                'codigo': '5105',
                'nombre': 'Gastos de Personal',
                'tipo': TipoCuenta.GASTO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
            {
                'codigo': '5120',
                'nombre': 'Arrendamientos',
                'tipo': TipoCuenta.GASTO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
            {
                'codigo': '5135',
                'nombre': 'Servicios Públicos',
                'tipo': TipoCuenta.GASTO,
                'naturaleza': 'DEBITO',
                'nivel': 2,
                'acepta_movimiento': True,
            },
        ]

    def _crear_cuenta_por_tipo(self, tipo, cuenta_data, es_corriente):
        if tipo == TipoCuenta.ACTIVO and es_corriente is not None:
            Activo.objects.create(**cuenta_data, es_corriente=es_corriente)
        elif tipo == TipoCuenta.PASIVO and es_corriente is not None:
            Pasivo.objects.create(**cuenta_data, es_corriente=es_corriente)
        elif tipo == TipoCuenta.PATRIMONIO:
            Patrimonio.objects.create(**cuenta_data)
        elif tipo == TipoCuenta.INGRESO:
            Ingreso.objects.create(**cuenta_data)
        elif tipo == TipoCuenta.COSTO:
            Costo.objects.create(**cuenta_data)
        elif tipo == TipoCuenta.GASTO:
            Gasto.objects.create(**cuenta_data)
        else:
            Cuenta.objects.create(**cuenta_data)

    def _crear_plan_basico(self, empresa):
        cuentas_creadas = 0
        with transaction.atomic():
            for cuenta_data in self._plan_cuentas_basico():
                codigo = cuenta_data['codigo']
                if Cuenta.objects.filter(empresa=empresa, codigo=codigo).exists():
                    self.stdout.write(self.style.WARNING(f'  ⚠ Cuenta {codigo} ya existe, omitiendo...'))
                    continue
                tipo = cuenta_data['tipo']
                es_corriente = cuenta_data.pop('es_corriente', None)
                cuenta_data['empresa'] = empresa
                cuenta_data['esta_activa'] = True
                self._crear_cuenta_por_tipo(tipo, cuenta_data, es_corriente)
                cuentas_creadas += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Creada: {codigo} - {cuenta_data["nombre"]}'))
        return cuentas_creadas

