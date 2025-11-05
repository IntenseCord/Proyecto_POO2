# Changelog - Balance General Avanzado

## [2.0.0] - Noviembre 2025

### 🎉 Nuevas Características

#### Vinculación Usuario-Empresa

- **Agregado**: Campo `empresa` en modelo `Perfil`
- **Agregado**: Función `obtener_empresa_usuario()` para obtener empresa del usuario
- **Agregado**: Comando `asignar_empresas` para gestión masiva
- **Eliminado**: Selector manual de empresa en reportes
- **Mejorado**: Seguridad - usuarios solo ven datos de su empresa

#### Balance General Mejorado

- **Agregado**: Clasificación de activos corrientes/no corrientes
- **Agregado**: Clasificación de pasivos corrientes/no corrientes
- **Agregado**: 5 ratios financieros clave:
  - Liquidez Corriente
  - Capital de Trabajo
  - Ratio de Endeudamiento
  - Ratio de Solvencia
  - Autonomía Financiera
- **Agregado**: Indicadores visuales (semáforos) para ratios
- **Agregado**: Preparación automática de datos para gráficos

#### Exportación Profesional

- **Agregado**: Exportación a PDF con ReportLab
  - Diseño profesional
  - Tablas estilizadas
  - Ecuación contable destacada
- **Agregado**: Exportación a Excel con openpyxl
  - Formato con colores
  - Columnas auto-ajustadas
  - Estilos empresariales
- **Agregado**: Rutas `/pdf/` y `/excel/` para cada reporte
- **Agregado**: Botones de descarga en interfaz

#### Gráficos Interactivos

- **Agregado**: Gráfico de composición de activos (Top 5)
- **Agregado**: Gráfico de composición de pasivos (Top 5)
- **Agregado**: Gráfico comparativo (Activos vs Pasivos vs Patrimonio)
- **Agregado**: Uso de Chart.js 4.4.1

### 🔄 Cambios

#### Backend

- **Modificado**: `cuentas/views.py`

  - `balance_general_view()` - Usa empresa del usuario
  - `balance_comprobacion_view()` - Usa empresa del usuario
  - `estado_resultados_view()` - Usa empresa del usuario
  - Nuevas vistas: `balance_general_pdf()`, `balance_general_excel()`

- **Modificado**: `cuentas/reportes.py`

  - Clase `BalanceGeneral` ampliada con 4 nuevos métodos
  - Métodos privados para clasificación y cálculos
  - Preparación de datos para gráficos

- **Modificado**: `cuentas/urls.py`
  - Agregadas rutas de exportación

#### Modelos

- **Modificado**: `login/models.py`
  - Modelo `Perfil` con campo `empresa` (ForeignKey)

#### Dependencias

- **Agregado**: `reportlab==4.0.7` para PDFs
- **Agregado**: `openpyxl==3.1.2` para Excel

### 🐛 Correcciones

- **Corregido**: Error de configuración CSRF_TRUSTED_ORIGINS
- **Corregido**: Archivos de caché Python causando errores
- **Corregido**: Templates con formato comprimido
- **Corregido**: Migraciones pendientes de inventario

### 📦 Migraciones

#### Nueva Migración

```
login/migrations/0006_perfil_empresa.py
- Agrega campo empresa a Perfil
- Permite null/blank para usuarios existentes
```

#### Aplicada

```bash
python manage.py migrate login 0006
```

### 📝 Archivos Nuevos

```
login/utils.py                              # Utilidades de usuario-empresa
login/management/commands/asignar_empresas.py  # Comando de gestión
cuentas/export_service.py                   # Servicio de exportación
BALANCE_GENERAL_MANUAL.md                   # Manual de usuario
CHANGELOG_BALANCE_GENERAL.md                # Este archivo
```

### 📝 Archivos Modificados

```
login/models.py                             # Campo empresa en Perfil
cuentas/views.py                            # Vistas actualizadas
cuentas/reportes.py                         # Clase BalanceGeneral mejorada
cuentas/urls.py                             # Rutas de exportación
requirements.txt                            # Nuevas dependencias
S_CONTABLE/settings.py                      # Configuración CSRF mejorada
```

### ⚙️ Configuración

#### Variables de Entorno Necesarias

```
SECRET_KEY=<tu-clave-secreta>
DEBUG=True  # False en producción
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=  # Vacío para desarrollo
DATABASE_URL=<tu-url-bd>  # Opcional
```

#### Instalación de Dependencias

```bash
pip install reportlab==4.0.7 openpyxl==3.1.2
```

### 🔐 Seguridad

- **Mejorado**: Validación de CSRF_TRUSTED_ORIGINS
- **Mejorado**: Usuarios solo acceden a datos de su empresa
- **Mejorado**: Verificación de permisos en exportación

### 📊 Rendimiento

- **Optimizado**: Queries de base de datos con select_related
- **Optimizado**: Generación de gráficos con datos pre-procesados
- **Optimizado**: Exportación lazy-loading de datos

### 🧪 Testing

#### Comandos de Prueba

```bash
# Verificar asignación de empresas
python manage.py asignar_empresas --auto

# Probar generación de reporte
# Navegar a: /cuentas/reportes/balance-general/

# Probar exportación PDF
# Clic en "Descargar PDF"

# Probar exportación Excel
# Clic en "Descargar Excel"
```

### 📈 Métricas

- **Líneas de código agregadas**: ~1,200
- **Archivos nuevos**: 4
- **Archivos modificados**: 6
- **Migraciones**: 1
- **Dependencias nuevas**: 2
- **Ratios financieros**: 5
- **Tipos de exportación**: 2

### 🔮 Roadmap Futuro

#### v2.1.0 (Próximo)

- [ ] Comparación de períodos
- [ ] Gráficos de tendencias
- [ ] Exportación a Word
- [ ] Envío automático por email

#### v2.2.0

- [ ] Dashboard ejecutivo
- [ ] Alertas automáticas
- [ ] Análisis predictivo
- [ ] Reportes programados

#### v3.0.0

- [ ] Multi-empresa para usuarios
- [ ] Consolidación de estados
- [ ] Análisis de variaciones
- [ ] Integración con BI tools

### 👥 Contribuidores

- Desarrollo Backend: Sistema Contable Team
- Análisis Financiero: Departamento Contable
- Testing: QA Team

### 📄 Licencia

Propiedad del proyecto Sistema Contable

---

## Notas de Actualización

### Para Usuarios Existentes

1. **Ejecutar migraciones**:

   ```bash
   python manage.py migrate
   ```

2. **Asignar empresas**:

   ```bash
   python manage.py asignar_empresas --auto
   ```

3. **Instalar dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Reiniciar servidor**:
   ```bash
   python manage.py runserver
   ```

### Compatibilidad

- Django 5.2.6+
- Python 3.13+
- PostgreSQL o SQLite
- Navegadores modernos (Chrome, Firefox, Edge)

### Deprecaciones

- ⚠️ Selector manual de empresa en reportes (removido)
- ⚠️ Vista antigua de balance general (reemplazada)

---

**Fecha de Release**: Noviembre 5, 2025
**Versión Anterior**: 1.0.0
**Versión Actual**: 2.0.0
