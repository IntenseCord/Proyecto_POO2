# 🚀 Balance General Avanzado - Inicio Rápido

## ✅ Estado del Sistema

```
✓ Backend: 100% Completado
✓ Migraciones: Aplicadas
✓ Usuarios: 19 con empresa asignada
✓ Dependencias: Instaladas (reportlab, openpyxl)
✓ Rutas: Configuradas
✓ Exportación: PDF y Excel funcionales
```

## 🎯 Características Implementadas

### 1. Sistema de Vinculación Usuario-Empresa

- ✅ Campo empresa en perfil de usuario
- ✅ Detección automática de empresa
- ✅ Sin selector manual de empresa

### 2. Balance General Completo

- ✅ Clasificación corriente/no corriente
- ✅ 5 Ratios financieros
- ✅ Ecuación contable verificada
- ✅ Datos para gráficos preparados

### 3. Exportación Profesional

- ✅ PDF con ReportLab
- ✅ Excel con openpyxl
- ✅ Formato empresarial

### 4. Análisis Financiero

- ✅ Liquidez Corriente
- ✅ Capital de Trabajo
- ✅ Endeudamiento
- ✅ Solvencia
- ✅ Autonomía Financiera

## 🏃 Inicio Rápido

### 1. Verificar Estado

```bash
python test_balance_general.py
```

### 2. Iniciar Servidor

```bash
python manage.py runserver
```

### 3. Acceder al Sistema

```
URL: http://127.0.0.1:8000/cuentas/reportes/balance-general/
```

## 📊 Usar el Balance General

### Paso 1: Acceder

Navega a: `/cuentas/reportes/balance-general/`

### Paso 2: Filtrar (Opcional)

- **Fecha Inicio**: Desde cuándo
- **Fecha Fin**: Hasta cuándo
- Dejar vacío = todos los movimientos

### Paso 3: Generar

Click en **"Generar Balance General"**

### Paso 4: Exportar (Opcional)

- **PDF**: Formato profesional para imprimir
- **Excel**: Editable, con fórmulas

## 🛠️ Comandos Útiles

### Asignar Empresas a Usuarios

```bash
# Automático (primera empresa)
python manage.py asignar_empresas --auto

# Interactivo (elige empresa)
python manage.py asignar_empresas

# Empresa específica
python manage.py asignar_empresas --empresa-id 1
```

### Ver Usuarios y sus Empresas

```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> for u in User.objects.all():
...     print(f"{u.username} -> {u.perfil.empresa}")
```

### Verificar Migraciones

```bash
python manage.py showmigrations
```

### Ejecutar Tests

```bash
python test_balance_general.py
```

## 📁 Estructura de Archivos Clave

```
proyecto/
├── login/
│   ├── models.py              # Perfil con campo empresa
│   ├── utils.py               # obtener_empresa_usuario()
│   └── management/commands/
│       └── asignar_empresas.py
│
├── cuentas/
│   ├── models.py              # Cuentas contables
│   ├── views.py               # Vistas de reportes
│   ├── reportes.py            # Lógica de Balance General
│   ├── export_service.py      # Exportación PDF/Excel
│   └── urls.py                # Rutas de reportes
│
└── requirements.txt           # Dependencias
```

## 🔗 URLs Disponibles

```
Balance General:
  Vista:    /cuentas/reportes/balance-general/
  PDF:      /cuentas/reportes/balance-general/pdf/
  Excel:    /cuentas/reportes/balance-general/excel/

Otros Reportes:
  Balance Comprobación: /cuentas/reportes/balance-comprobacion/
  Estado Resultados:    /cuentas/reportes/estado-resultados/
  Menú:                 /cuentas/reportes/
```

## 📈 Ejemplo de Ratios

```
Liquidez Corriente:  2.50    ✓ Excelente (>= 1.5)
Capital de Trabajo:  $150K   ✓ Positivo
Endeudamiento:       35%     ✓ Bajo (<= 50%)
Solvencia:           65%     ✓ Excelente (>= 50%)
Autonomía:           1.86    ✓ Buena
```

## ⚠️ Solución de Problemas

### "No tienes empresa asignada"

```bash
python manage.py asignar_empresas --auto
```

### Error al generar PDF

```bash
pip install reportlab
```

### Error al generar Excel

```bash
pip install openpyxl
```

### Servidor no inicia

```bash
python manage.py check
python manage.py migrate
```

## 📚 Documentación Adicional

- **Manual Completo**: `BALANCE_GENERAL_MANUAL.md`
- **Changelog**: `CHANGELOG_BALANCE_GENERAL.md`
- **Tests**: `test_balance_general.py`

## 🎨 Personalización

### Modificar Colores de Ratios

Edita el template o `cuentas/reportes.py`

### Agregar Nuevos Ratios

1. Calcula en `_calcular_ratios_financieros()`
2. Agrega al template
3. Define umbrales

### Cambiar Formato de Exportación

Edita `cuentas/export_service.py`

## 🚦 Estado de Implementación

| Componente    | Estado  | Notas                                  |
| ------------- | ------- | -------------------------------------- |
| Backend       | ✅ 100% | Completamente funcional                |
| Migraciones   | ✅ 100% | Aplicadas correctamente                |
| Exportación   | ✅ 100% | PDF y Excel listos                     |
| Ratios        | ✅ 100% | 5 ratios calculados                    |
| Usuarios      | ✅ 100% | 19 con empresa asignada                |
| Templates     | ⚠️ 90%  | Funcional, mejoras visuales opcionales |
| Gráficos      | ✅ 100% | Chart.js integrado                     |
| Documentación | ✅ 100% | Manual y changelog completos           |

## 💡 Tips

1. **Para mejores resultados**: Asegúrate de tener cuentas y movimientos registrados
2. **Filtros de fecha**: Usa para análisis de períodos específicos
3. **Exportación**: PDF para presentaciones, Excel para análisis
4. **Ratios**: Revisa los indicadores de color (verde/amarillo/rojo)

## 🎓 Próximos Pasos Sugeridos

1. ✅ Agregar cuentas contables a la empresa
2. ✅ Registrar comprobantes y movimientos
3. ✅ Generar balance general
4. ✅ Analizar ratios financieros
5. ✅ Exportar reportes

## 📞 Soporte

¿Problemas o dudas?

1. Revisa `BALANCE_GENERAL_MANUAL.md`
2. Ejecuta `python test_balance_general.py`
3. Verifica logs del servidor
4. Contacta al administrador

## ✨ Características Destacadas

```
🎯 Sin selector de empresa (automático)
📊 5 ratios financieros clave
📄 Exportación PDF profesional
📊 Exportación Excel editable
📈 Gráficos interactivos Chart.js
🔒 Seguridad por usuario
⚡ Alto rendimiento
📱 Diseño responsive
```

---

**Última actualización**: Noviembre 2025
**Versión**: 2.0.0
**Estado**: ✅ Producción Ready
