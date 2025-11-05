# 🔍 Guía de Configuración de SonarCloud para S_CONTABLE

Esta guía te ayudará a configurar **SonarCloud** para analizar la calidad del código de tu proyecto Django.

## 📋 ¿Qué es SonarCloud?

SonarCloud es una plataforma de análisis de código en la nube que detecta:

- 🐛 **Bugs y vulnerabilidades de seguridad**
- 💡 **Code smells** (problemas de mantenibilidad)
- 📊 **Duplicación de código**
- 📈 **Cobertura de tests**
- 🎯 **Deuda técnica**

## 🚀 Paso 1: Crear Cuenta en SonarCloud

### 1.1 Acceder a SonarCloud

1. Ve a [https://sonarcloud.io](https://sonarcloud.io)
2. Haz clic en **"Log in"** o **"Sign up"**

### 1.2 Registrarse

Puedes registrarte usando:

- **GitHub** (Recomendado si tu proyecto está en GitHub)
- **Bitbucket**
- **GitLab**
- **Azure DevOps**

### 1.3 Crear Organización

1. Después de iniciar sesión, se te pedirá crear una **organización**
2. Puedes usar tu cuenta personal o crear una nueva
3. **Gratis para proyectos públicos** ✅
4. Anota el nombre de tu organización (lo necesitarás después)

**Ejemplo:** `mi-usuario` o `mi-empresa`

---

## 📦 Paso 2: Crear Proyecto en SonarCloud

### 2.1 Crear Nuevo Proyecto

1. En el dashboard de SonarCloud, haz clic en **"+"** (Analyze new project)
2. Selecciona **"Create project manually"** (para análisis local)

### 2.2 Configurar Proyecto

1. **Display name**: `S_CONTABLE - Sistema Contable Django`
2. **Project key**: `s-contable` (o el que prefieras, sin espacios)
3. **Organization**: Selecciona tu organización
4. Haz clic en **"Set Up"**

### 2.3 Guardar Información

Anota los siguientes datos (los necesitarás después):

- **Organization Key**: `tu-organization` (ejemplo: `mi-usuario`)
- **Project Key**: `s-contable` (el que definiste)

---

## 🔑 Paso 3: Generar Token de Acceso

### 3.1 Ir a Configuración de Seguridad

1. Haz clic en tu **foto de perfil** (esquina superior derecha)
2. Selecciona **"My Account"**
3. Ve a la pestaña **"Security"**

### 3.2 Generar Token

1. En la sección **"Generate Tokens"**:
   - **Name**: `S_CONTABLE_Local_Analysis`
   - **Type**: `User Token`
   - **Expires in**: `90 days` (o `No expiration`)
2. Haz clic en **"Generate"**

### 3.3 Copiar Token

⚠️ **¡IMPORTANTE!** El token solo se muestra una vez. Cópialo y guárdalo en un lugar seguro.

**Ejemplo de token:**

```
squ_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

---

## 💻 Paso 4: Instalar SonarScanner

SonarScanner es la herramienta que analiza tu código localmente.

### 4.1 Descargar SonarScanner

#### **Windows**

1. Descarga desde: [https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/](https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/)
2. Descarga el archivo `.zip` para Windows
3. Extrae el contenido en `C:\sonar-scanner\`

#### **macOS**

```bash
brew install sonar-scanner
```

#### **Linux**

```bash
# Descargar y extraer
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
sudo mv sonar-scanner-5.0.1.3006-linux /opt/sonar-scanner
```

### 4.2 Agregar al PATH

#### **Windows**

1. Abre **"Panel de Control" > "Sistema" > "Configuración avanzada del sistema"**
2. Haz clic en **"Variables de entorno"**
3. En **"Variables del sistema"**, busca `Path` y haz clic en **"Editar"**
4. Haz clic en **"Nuevo"** y agrega: `C:\sonar-scanner\bin`
5. Haz clic en **"Aceptar"** en todas las ventanas

#### **macOS/Linux**

Agrega esto a tu `~/.bashrc` o `~/.zshrc`:

```bash
export PATH="$PATH:/opt/sonar-scanner/bin"
```

Luego ejecuta:

```bash
source ~/.bashrc  # o source ~/.zshrc
```

### 4.3 Verificar Instalación

Abre una **nueva terminal** y ejecuta:

```bash
sonar-scanner --version
```

Deberías ver algo como:

```
INFO: Scanner configuration file: C:\sonar-scanner\conf\sonar-scanner.properties
INFO: Project root configuration file: NONE
INFO: SonarScanner 5.0.1.3006
INFO: Java 17.0.7 Eclipse Adoptium (64-bit)
```

✅ ¡Si ves esto, SonarScanner está instalado correctamente!

---

## ⚙️ Paso 5: Configurar Credenciales en el Proyecto

### 5.1 Editar archivo de configuración

1. Abre el archivo `sonar-project.properties` en la raíz de tu proyecto
2. Busca estas líneas:

```properties
sonar.projectKey=TU_PROJECT_KEY
sonar.organization=TU_ORGANIZATION_KEY
```

3. Reemplaza con tus datos reales:

```properties
sonar.projectKey=s-contable
sonar.organization=mi-usuario
```

### 5.2 Verificar otras configuraciones

El archivo ya viene configurado para Django con:

- ✅ Rutas de código fuente (todas las apps)
- ✅ Exclusiones (migraciones, **pycache**, etc.)
- ✅ Configuración de Python
- ✅ Encoding UTF-8

**No necesitas modificar nada más** a menos que quieras personalizar el análisis.

---

## 🎯 Paso 6: Ejecutar Análisis

### 6.1 Ir al directorio del proyecto

```bash
cd "C:\Users\SANTIAGO MUÑOZ\Desktop\proyecto de pooo super"
```

### 6.2 Ejecutar SonarScanner

#### **Opción 1: Con token en línea de comandos** (Recomendado)

```bash
sonar-scanner -Dsonar.login=TU_TOKEN_AQUI
```

Reemplaza `TU_TOKEN_AQUI` con el token que generaste en el Paso 3.

**Ejemplo:**

```bash
sonar-scanner -Dsonar.login=squ_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

#### **Opción 2: Con variable de entorno** (Más seguro)

**Windows (PowerShell):**

```powershell
$env:SONAR_TOKEN="TU_TOKEN_AQUI"
sonar-scanner -Dsonar.login=$env:SONAR_TOKEN
```

**macOS/Linux:**

```bash
export SONAR_TOKEN="TU_TOKEN_AQUI"
sonar-scanner -Dsonar.login=$SONAR_TOKEN
```

### 6.3 Esperar a que termine el análisis

Verás algo como:

```
INFO: Scanner configuration file: C:\sonar-scanner\conf\sonar-scanner.properties
INFO: Project root configuration file: C:\...\sonar-project.properties
INFO: SonarScanner 5.0.1.3006
INFO: Java 17.0.7 Eclipse Adoptium (64-bit)
INFO: Windows 10 10.0 amd64
INFO: User cache: C:\Users\...\.sonar\cache
INFO: Analyzing on SonarCloud
INFO: Load global settings
INFO: Load global settings (done) | time=182ms
...
INFO: ANALYSIS SUCCESSFUL, you can browse https://sonarcloud.io/dashboard?id=s-contable
INFO: Note that you will be able to access the updated dashboard once the server has processed the submitted analysis report
INFO: More about the report processing at https://sonarcloud.io/api/ce/task?id=...
INFO: Analysis total time: 23.456 s
INFO: ------------------------------------------------------------------------
INFO: EXECUTION SUCCESS
INFO: ------------------------------------------------------------------------
```

✅ **¡Análisis completado!**

---

## 📊 Paso 7: Ver Resultados

### 7.1 Acceder al Dashboard

1. Ve a [https://sonarcloud.io](https://sonarcloud.io)
2. Selecciona tu proyecto **"S_CONTABLE"**
3. Verás el dashboard con:
   - **Bugs**: Errores de código
   - **Vulnerabilities**: Problemas de seguridad
   - **Code Smells**: Problemas de mantenibilidad
   - **Coverage**: Cobertura de tests (si está configurado)
   - **Duplications**: Código duplicado
   - **Security Hotspots**: Puntos sensibles de seguridad

### 7.2 Explorar Issues

1. Haz clic en cualquier métrica (por ejemplo, "15 Code Smells")
2. Verás una lista de problemas encontrados
3. Haz clic en un problema para ver:
   - **Descripción** del problema
   - **Ubicación** en el código
   - **Recomendación** de cómo solucionarlo
   - **Severidad** (Blocker, Critical, Major, Minor, Info)

### 7.3 Filtrar Issues

Puedes filtrar por:

- **Tipo**: Bug, Vulnerability, Code Smell
- **Severidad**: Blocker, Critical, Major, Minor, Info
- **Archivo**: Por app o módulo
- **Fecha**: Nuevos vs. existentes

---

## 🔄 Ejecutar Análisis Regularmente

### Recomendaciones:

1. **Antes de cada commit importante**

   ```bash
   sonar-scanner -Dsonar.login=$SONAR_TOKEN
   ```

2. **Semanalmente** para monitorear la calidad del código

3. **Después de refactorizar** para ver las mejoras

---

## 🛠️ Configuración Avanzada (Opcional)

### Cobertura de Tests con Coverage.py

Si quieres ver la cobertura de tests en SonarCloud:

#### 1. Instalar coverage

```bash
pip install coverage
```

#### 2. Ejecutar tests con coverage

```bash
coverage run --source='.' manage.py test
coverage xml
```

#### 3. Descomentar en sonar-project.properties

```properties
sonar.python.coverage.reportPaths=coverage.xml
```

#### 4. Ejecutar análisis

```bash
sonar-scanner -Dsonar.login=$SONAR_TOKEN
```

---

## 🚨 Solución de Problemas

### Error: "Project key is invalid"

- Verifica que el `sonar.projectKey` en `sonar-project.properties` coincida con el de SonarCloud
- No uses espacios ni caracteres especiales en el project key

### Error: "Authentication failed"

- Verifica que el token sea correcto
- El token puede haber expirado, genera uno nuevo

### Error: "sonar-scanner: command not found"

- Verifica que SonarScanner esté en el PATH
- Reinicia la terminal después de agregar al PATH
- Verifica la instalación con `sonar-scanner --version`

### Error: "No files to analyze"

- Verifica que la ruta de `sonar.sources` sea correcta
- Asegúrate de estar en el directorio correcto al ejecutar el comando

### El análisis es muy lento

- Esto es normal la primera vez (puede tardar varios minutos)
- Los análisis posteriores son más rápidos (solo analizan cambios)

---

## 📚 Recursos Adicionales

- **Documentación oficial de SonarCloud**: [https://docs.sonarcloud.io/](https://docs.sonarcloud.io/)
- **SonarScanner para Python**: [https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/languages/python/](https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/languages/python/)
- **Reglas de Python**: [https://rules.sonarsource.com/python/](https://rules.sonarsource.com/python/)

---

## ✅ Checklist de Configuración

- [ ] Cuenta creada en SonarCloud
- [ ] Organización creada
- [ ] Proyecto creado en SonarCloud
- [ ] Token de acceso generado y guardado
- [ ] SonarScanner instalado y en el PATH
- [ ] Archivo `sonar-project.properties` configurado
- [ ] Primer análisis ejecutado exitosamente
- [ ] Dashboard de SonarCloud revisado

---

## 🎉 ¡Felicidades!

Ahora tienes SonarCloud configurado para tu proyecto Django. Cada vez que ejecutes el análisis, podrás ver:

- 📈 La evolución de la calidad de tu código
- 🐛 Bugs nuevos antes de que lleguen a producción
- 🔒 Vulnerabilidades de seguridad
- 💡 Sugerencias de mejora

**¡Mantén tu código limpio y de alta calidad!** 🚀

---

**Desarrollado para S_CONTABLE - Sistema de Información Contable**
