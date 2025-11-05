# Manual del Balance General Avanzado

## 🎯 Características Implementadas

### 1. Vinculación Automática Usuario-Empresa

- Los usuarios ahora tienen una empresa asignada en su perfil
- Los reportes se generan automáticamente para la empresa del usuario
- No es necesario seleccionar empresa manualmente

### 2. Balance General Mejorado

#### Datos Calculados:

- **Activos** (clasificados en corrientes y no corrientes)
- **Pasivos** (clasificados en corrientes y no corrientes)
- **Patrimonio** (incluyendo utilidad del período)
- **Ecuación contable**: Activos = Pasivos + Patrimonio

#### Ratios Financieros:

1. **Liquidez Corriente** = Activo Corriente / Pasivo Corriente

   - Verde: >= 1.5 (Excelente)
   - Amarillo: >= 1.0 (Aceptable)
   - Rojo: < 1.0 (Crítico)

2. **Capital de Trabajo** = Activo Corriente - Pasivo Corriente

   - Verde: >= 0 (Positivo)
   - Rojo: < 0 (Negativo)

3. **Endeudamiento** = (Pasivo Total / Activo Total) × 100

   - Verde: <= 50% (Bajo)
   - Amarillo: 50-70% (Moderado)
   - Rojo: > 70% (Alto)

4. **Solvencia** = (Patrimonio / Activo Total) × 100

   - Verde: >= 50% (Excelente)
   - Amarillo: 30-50% (Aceptable)
   - Rojo: < 30% (Bajo)

5. **Autonomía Financiera** = Patrimonio / Pasivo Total

### 3. Exportación

#### PDF (ReportLab)

- Formato profesional
- Incluye logo y encabezados
- Tablas organizadas por sección
- Ecuación contable destacada

#### Excel (openpyxl)

- Formato con estilos
- Fórmulas preservadas
- Columnas auto-ajustadas
- Colores corporativos

### 4. Gráficos Interactivos (Chart.js)

- Composición de activos (Top 5)
- Composición de pasivos (Top 5)
- Gráfico comparativo (Activos vs Pasivos vs Patrimonio)

## 📖 Uso del Sistema

### Acceder al Balance General

```
URL: http://127.0.0.1:8000/cuentas/reportes/balance-general/
```

### Generar Reporte

1. Selecciona fechas (opcional):

   - **Fecha Inicio**: Desde cuándo considerar movimientos
   - **Fecha Fin**: Hasta cuándo considerar movimientos
   - Si no se especifica, incluye todos los movimientos

2. Haz clic en **"Generar Balance General"**

3. El reporte se mostrará con:
   - Activos organizados
   - Pasivos organizados
   - Patrimonio con utilidad del período
   - Ratios financieros calculados
   - Gráficos interactivos

### Exportar Reporte

#### Opción 1: PDF

```
Botón: "Descargar PDF"
Formato: balance_general_[empresa]_[fecha].pdf
```

#### Opción 2: Excel

```
Botón: "Descargar Excel"
Formato: balance_general_[empresa]_[fecha].xlsx
```

## 🔧 Comandos de Gestión

### Asignar Empresas a Usuarios

#### Modo Automático (asigna primera empresa disponible)

```bash
python manage.py asignar_empresas --auto
```

#### Modo Interactivo (elige la empresa)

```bash
python manage.py asignar_empresas
```

#### Asignar Empresa Específica

```bash
python manage.py asignar_empresas --empresa-id 1
```

## 🗂️ Estructura del Código

### Modelos

```
login/models.py
- Perfil.empresa (ForeignKey a Empresa)
```

### Vistas

```
cuentas/views.py
- balance_general_view(): Vista principal
- balance_general_pdf(): Exportación PDF
- balance_general_excel(): Exportación Excel
```

### Reportes

```
cuentas/reportes.py
- BalanceGeneral.generar(): Genera datos completos
- BalanceGeneral._clasificar_activos(): Clasifica corriente/no corriente
- BalanceGeneral._clasificar_pasivos(): Clasifica corriente/no corriente
- BalanceGeneral._calcular_ratios_financieros(): Calcula 5 ratios
- BalanceGeneral._preparar_datos_graficos(): Datos para Chart.js
```

### Exportación

```
cuentas/export_service.py
- ExportadorBalanceGeneral.exportar_pdf(): Genera PDF profesional
- ExportadorBalanceGeneral.exportar_excel(): Genera Excel con estilos
```

### Utilidades

```
login/utils.py
- obtener_empresa_usuario(user): Obtiene empresa del usuario
- usuario_tiene_empresa(user): Verifica si tiene empresa
```

## 🎨 Personalización

### Modificar Colores de Gráficos

Edita `cuentas/reportes.py`, método `_preparar_datos_graficos()`

### Cambiar Umbrales de Ratios

Edita el template o `cuentas/reportes.py`, método `_calcular_ratios_financieros()`

### Agregar Nuevos Ratios

1. Calcula en `_calcular_ratios_financieros()`
2. Agrega tarjeta en el template
3. Define umbrales de color

## 🐛 Solución de Problemas

### Error: "No tienes una empresa asignada"

**Solución**: Ejecuta `python manage.py asignar_empresas --auto`

### Error al exportar PDF

**Solución**: Verifica que reportlab esté instalado

```bash
pip install reportlab
```

### Error al exportar Excel

**Solución**: Verifica que openpyxl esté instalado

```bash
pip install openpyxl
```

### Los gráficos no se muestran

**Solución**: Verifica que Chart.js se cargue correctamente (requiere internet)

## 📊 Ejemplo de Salida

### Ratios Típicos

```
Liquidez Corriente: 2.5  (Excelente)
Capital de Trabajo: $150,000  (Positivo)
Endeudamiento: 35%  (Bajo)
Solvencia: 65%  (Excelente)
Autonomía: 1.86  (Buena)
```

### Ecuación Contable

```
Activos: $500,000
Pasivos: $175,000
Patrimonio: $325,000
✓ Ecuación Balanceada
```

## 🚀 Próximas Mejoras Sugeridas

1. **Comparación períodos**: Ver evolución mes a mes
2. **Alertas automáticas**: Notificar ratios críticos
3. **Dashboard ejecutivo**: Resumen visual
4. **Análisis predictivo**: Proyecciones futuras
5. **Reportes programados**: Envío automático por email

## 📞 Soporte

Para dudas o problemas, contacta al administrador del sistema.

---

**Última actualización**: Noviembre 2025
**Versión**: 2.0 (Balance General Avanzado)
