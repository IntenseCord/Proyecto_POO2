# 🧮 S_CONTABLE - Sistema de Información Contable y Administrativa

Sistema de gestión contable desarrollado en **Django 5.2.6** para personas naturales, emprendedores y empresas de todos los tamaños.

---

## 📋 Características Principales

### 🔐 **Módulo de Autenticación (Login)**
- ✅ **Landing Page Profesional**: Página de bienvenida moderna y atractiva
- ✅ **Registro de Usuarios**: Formulario completo con validación en tiempo real
  - Nombre y apellido
  - Usuario único
  - Email
  - Celular
  - Dirección
  - Año de nacimiento
  - Contraseña con indicador de fortaleza
- ✅ **Verificación de Email**: Sistema de verificación con tokens UUID
- ✅ **Login Seguro**: Autenticación con validaciones
- ✅ **Recuperación de Contraseña**: Sistema completo de recuperación por email
- ✅ **Gestión de Perfiles**: Edición de perfil con foto de usuario
- ✅ **Autenticación JWT**: API REST con tokens JWT para integraciones
- ✅ **Logout**: Cierre de sesión seguro

### 📊 **Módulo Contable** (En desarrollo)
- **Dashboard Interactivo**: Panel con gráficos y estadísticas en tiempo real
- **Multi-Empresa**: Administración de múltiples empresas desde una cuenta
- **Plan de Cuentas**: Sistema completo de cuentas contables con jerarquía
- **Comprobantes Contables**: Registro de ingresos, egresos y notas contables
- **Reportes**: Balance General, Estado de Resultados, Estado de Cambios en el Patrimonio

### 🎨 **Diseño**
- ✅ **Interfaz Moderna**: Diseño profesional con gradientes morados
- ✅ **Responsive**: Adaptado para móviles, tablets y desktop
- ✅ **Animaciones**: Transiciones suaves y efectos visuales
- ✅ **Iconos**: Font Awesome 6.4.0

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

El archivo `.env` ya está configurado con valores por defecto. Para producción, modifica:
- `SECRET_KEY`: Genera una nueva clave secreta
- `DEBUG`: Cambia a `False` en producción
- `ALLOWED_HOSTS`: Agrega los dominios permitidos

### 3. Crear migraciones y aplicarlas

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Crear superusuario

```bash
python manage.py createsuperuser
```

### 5. Ejecutar el servidor

```bash
python manage.py runserver
```

## 📁 Estructura del Proyecto

```
S_CONTABLE/
├── S_CONTABLE/          # Configuración principal
├── login/               # Autenticación de usuarios
├── empresa/             # Gestión de empresas
├── cuentas/             # Plan de cuentas contables
├── transacciones/       # Comprobantes y movimientos
├── reportes/            # Generación de reportes
├── configuracion/       # Configuraciones del sistema
├── manage.py
├── requirements.txt
└── README.md
```

## 🔐 URLs del Sistema

### **Páginas Públicas**
- **Landing Page**: http://localhost:8000/login/inicio/
- **Login**: http://localhost:8000/login/
- **Registro**: http://localhost:8000/login/registro/
- **Recuperar Contraseña**: http://localhost:8000/login/solicitar-recuperacion/

### **Páginas Privadas** (Requieren autenticación)
- **Dashboard**: http://localhost:8000/dashboard/
- **Mi Perfil**: http://localhost:8000/login/perfil/
- **Logout**: http://localhost:8000/login/logout/

### **API REST** (JWT)
- **Obtener Token**: POST http://localhost:8000/api/token/
- **Renovar Token**: POST http://localhost:8000/api/token/refresh/

### **Administración**
- **Admin Django**: http://localhost:8000/admin/

## 📊 Modelos del Sistema

### **Módulo de Login**

#### **Perfil**
```python
- user: Usuario (OneToOne con User de Django)
- foto: Imagen de perfil
- telefono: Número de celular
- direccion: Dirección completa
- fecha_nacimiento: Año de nacimiento
- bio: Biografía del usuario
```

#### **VerificacionEmail**
```python
- user: Usuario
- token: UUID único
- verificado: Boolean
- fecha_creacion: Timestamp
- fecha_verificacion: Timestamp
- es_valido(): Método que verifica si el token es válido (24 horas)
```

#### **RecuperacionContrasena**
```python
- user: Usuario
- token: UUID único
- usado: Boolean
- fecha_creacion: Timestamp
- fecha_uso: Timestamp
- ip_address: IP del solicitante
- es_valido(): Método que verifica si el token es válido (1 hora)
```

### **Módulo Contable**

#### **Empresa**
- Información de empresas (NIT, nombre, dirección, etc.)

#### **Cuenta**
- Plan de cuentas contables con jerarquía
- Tipos: Activo, Pasivo, Patrimonio, Ingreso, Gasto, Costo
- Naturaleza: Débito o Crédito

#### **Comprobante**
- Comprobantes contables (Ingreso, Egreso, Nota Contable)
- Estados: Borrador, Aprobado, Anulado

#### **DetalleComprobante**
- Movimientos individuales de cada comprobante
- Registro de débitos y créditos

## 🔄 Flujos de Usuario

### **1. Registro de Usuario**
```
1. Usuario accede a /login/registro/
2. Completa formulario con datos personales
3. Sistema valida contraseña en tiempo real
4. Usuario envía formulario
5. Sistema crea usuario y perfil
6. Sistema envía email de verificación
7. Usuario recibe email con link
8. Usuario hace clic en link de verificación
9. Sistema marca email como verificado
10. Usuario puede hacer login ✅
```

### **2. Login**
```
1. Usuario accede a /login/
2. Ingresa username y contraseña
3. Sistema valida credenciales
4. Sistema verifica que el email esté verificado
5. Usuario accede al dashboard ✅
```

### **3. Recuperación de Contraseña**
```
1. Usuario hace clic en "¿Olvidaste tu contraseña?"
2. Ingresa su email
3. Sistema envía email con link de recuperación (válido 1 hora)
4. Usuario hace clic en el link
5. Ingresa nueva contraseña (con validación)
6. Sistema actualiza contraseña
7. Usuario puede hacer login con nueva contraseña ✅
```

### **4. Edición de Perfil**
```
1. Usuario autenticado accede a /login/perfil/
2. Edita sus datos personales
3. Sube foto de perfil (opcional)
4. Guarda cambios
5. Sistema actualiza perfil ✅
```

### **5. Autenticación JWT (API)**
```
1. Cliente envía POST a /api/token/ con credenciales
2. Sistema valida y genera tokens (access + refresh)
3. Cliente guarda tokens
4. Cliente usa access token en header Authorization
5. Cuando access expira, usa refresh para obtener nuevo access
6. Cliente continúa usando la API ✅
```

## 🛠️ Tecnologías

### **Backend**
- **Django 5.2.6**: Framework web principal
- **Python 3.10+**: Lenguaje de programación
- **SQLite**: Base de datos (desarrollo)
- **Django REST Framework**: API REST
- **Simple JWT**: Autenticación con tokens JWT
- **python-decouple**: Gestión de variables de entorno
- **Pillow**: Procesamiento de imágenes

### **Frontend**
- **HTML5**: Estructura
- **CSS3**: Estilos y animaciones
- **JavaScript**: Interactividad
- **Font Awesome 6.4.0**: Iconos

### **Seguridad**
- **CSRF Protection**: Protección contra ataques CSRF
- **Password Hashing**: Contraseñas encriptadas con PBKDF2
- **JWT Tokens**: Autenticación stateless para API
- **Email Verification**: Verificación de email obligatoria
- **Token Expiration**: Tokens con tiempo de vida limitado

## 📝 Notas

- El sistema usa SQLite por defecto para desarrollo
- Para producción, considera usar PostgreSQL o MySQL
- Todos los modelos incluyen campos de auditoría (fecha_creacion, usuario_creador)
- El idioma del sistema está configurado en español
- Zona horaria: America/Bogota

## 📧 Configuración de Email (Verificación de Usuarios)

El sistema envía emails de verificación cuando los usuarios se registran. Configura tu proveedor de email en el archivo `.env`:

### **Gmail** (Recomendado)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=contraseña_de_aplicación
DEFAULT_FROM_EMAIL=tu_email@gmail.com
```

**Pasos para Gmail:**
1. Activa verificación en 2 pasos: https://myaccount.google.com/security
2. Genera contraseña de aplicación: https://myaccount.google.com/apppasswords
3. Usa esa contraseña en `EMAIL_HOST_PASSWORD`

### **Outlook/Hotmail**
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@outlook.com
EMAIL_HOST_PASSWORD=tu_contraseña
```

### **Yahoo**
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@yahoo.com
EMAIL_HOST_PASSWORD=contraseña_de_aplicación
```

### **iCloud**
```env
EMAIL_HOST=smtp.mail.me.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@icloud.com
EMAIL_HOST_PASSWORD=contraseña_específica
```

### **Modo Desarrollo (Sin configurar email)**
Por defecto, los emails se muestran en la consola. No necesitas configurar nada para desarrollo.

## 📸 Capturas de Pantalla

### **Landing Page**
Página de bienvenida con diseño moderno y gradientes morados.

### **Registro**
Formulario completo con validación de contraseña en tiempo real:
- Indicador de fortaleza de contraseña
- Requisitos visuales (longitud, números, caracteres especiales)
- Campos: nombre, apellido, usuario, email, celular, dirección, año de nacimiento

### **Login**
Formulario de inicio de sesión con:
- Mostrar/ocultar contraseña
- Enlace de recuperación de contraseña
- Enlace de registro

### **Recuperación de Contraseña**
Sistema completo de recuperación:
- Formulario para ingresar email
- Email con link de recuperación
- Formulario para nueva contraseña con validación

### **Dashboard**
Panel principal después del login con:
- Menú lateral
- Topbar con foto de perfil
- Menú desplegable de usuario

### **Mi Perfil**
Edición de perfil con:
- Subida de foto de perfil
- Edición de datos personales
- Cambio de contraseña

## 🎯 Guía de Uso Rápido

### **Para Desarrolladores**

1. **Clonar el repositorio**
```bash
git clone <url-del-repo>
cd S_CONTABLE
```

2. **Crear entorno virtual**
```bash
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar migraciones**
```bash
python manage.py migrate
```

5. **Crear superusuario**
```bash
python manage.py createsuperuser
```

6. **Iniciar servidor**
```bash
python manage.py runserver
```

7. **Acceder al sistema**
- Landing: http://localhost:8000/login/inicio/
- Admin: http://localhost:8000/admin/

### **Para Usuarios Finales**

1. **Registro**
   - Ir a http://localhost:8000/login/registro/
   - Completar formulario
   - Verificar email

2. **Login**
   - Ir a http://localhost:8000/login/
   - Ingresar credenciales
   - Acceder al dashboard

3. **Editar Perfil**
   - Clic en foto de perfil (esquina superior derecha)
   - Seleccionar "Mi Perfil"
   - Editar datos y guardar

## 🔧 Próximos Pasos (Desarrollo)

### **Semana 1 (Oct 13-19): Empresas**
- [ ] CRUD de Empresas desde dashboard
- [ ] Selector de empresa activa
- [ ] Gestión de terceros (clientes/proveedores)

### **Semana 2 (Oct 20-26): Plan de Cuentas**
- [ ] Interfaz para crear/editar cuentas
- [ ] Árbol jerárquico visual
- [ ] Importar PUC estándar colombiano

### **Semana 3 (Oct 27 - Nov 2): Comprobantes**
- [ ] Formulario de comprobantes
- [ ] Validación débito = crédito
- [ ] Consecutivos automáticos

### **Semana 4 (Nov 3-9): Reportes**
- [ ] Balance de Prueba
- [ ] Libro Diario
- [ ] Balance General
- [ ] Estado de Resultados

### **Semana 5 (Nov 10-14): Finalización**
- [ ] Documentación completa
- [ ] Video demo
- [ ] Presentación

## 📝 Notas Técnicas

### **Configuración JWT**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),     # 1 día
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### **Ejemplo de uso de API con JWT**
```python
import requests

# 1. Obtener token
response = requests.post('http://localhost:8000/api/token/', 
    json={'username': 'usuario', 'password': 'contraseña'}
)
tokens = response.json()

# 2. Usar token en peticiones
headers = {'Authorization': f'Bearer {tokens["access"]}'}
response = requests.get('http://localhost:8000/api/endpoint/', headers=headers)
```

## 🐛 Solución de Problemas

### **Error: No module named 'decouple'**
```bash
pip install python-decouple
```

### **Error: No such table: login_perfil**
```bash
python manage.py migrate
```

### **Error: SMTP authentication failed**
- Verifica tus credenciales de email en `.env`
- Para Gmail, usa contraseña de aplicación
- Para desarrollo, los emails se muestran en consola

### **Error: 404 en /media/perfiles/**
- Asegúrate de que `DEBUG=True` en desarrollo
- Verifica que `MEDIA_URL` y `MEDIA_ROOT` estén configurados

## 👥 Contribuciones

Este proyecto fue desarrollado como parte de un proyecto universitario.

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 📞 Contacto y Soporte

Para más información sobre Django, visita: https://docs.djangoproject.com/

---

**Desarrollado con ❤️ usando Django 5.2.6**
