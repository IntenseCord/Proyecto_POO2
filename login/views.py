from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import VerificacionEmail, Perfil, RecuperacionContrasena, IntentoLogin
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Constantes para evitar duplicación de literales en redirecciones
DASHBOARD_HOME = 'dashboard:home'
LOGIN_TEMPLATE = 'login.html'
LOGIN_ROUTE_NAME = 'login:login'
CAMBIAR_CONTRASENA_TEMPLATE = 'cambiar_contrasena.html'

# Mensajes de error comunes
ERROR_CLAVE_CORTA = 'La contraseña debe tener al menos 6 caracteres'

@require_GET
def landing_view(request):
    """Vista para la página de bienvenida"""
    if request.user.is_authenticated:
        return redirect(DASHBOARD_HOME)
    return render(request, 'landing.html')

# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def login_view(request):
    """Vista para el login de usuarios"""
    if request.user.is_authenticated:
        return redirect(DASHBOARD_HOME)
    
    if request.method != 'POST':
        return render(request, LOGIN_TEMPLATE)

    username = request.POST.get('username')
    password = request.POST.get('password')
    ip_address = get_client_ip(request)

    intento = _get_login_attempt(username, ip_address)
    bloqueado_response = _response_if_blocked(intento, request)
    if bloqueado_response:
        return bloqueado_response

    user = authenticate(request, username=username, password=password)
    if user is None:
        return _handle_failed_login(intento, username, ip_address, request)

    if _requires_email_verification(user):
        messages.error(request, 'Debes verificar tu email antes de iniciar sesión. Revisa tu correo.')
        return render(request, LOGIN_TEMPLATE)

    return _handle_successful_login(request, user, intento)
    
    

# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def registro_view(request):
    """Vista para el registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect(DASHBOARD_HOME)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Nuevos campos
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        telefono = request.POST.get('telefono', '')
        direccion = request.POST.get('direccion', '')
        fecha_nacimiento = request.POST.get('fecha_nacimiento', '')
        
        # Validaciones extraídas a helper para reducir complejidad cognitiva
        error_msg = _validate_registration(
            username=username,
            email=email,
            password1=password1,
            password2=password2,
            first_name=first_name,
            last_name=last_name,
            telefono=telefono,
            direccion=direccion,
            fecha_nacimiento=fecha_nacimiento,
        )

        if error_msg:
            messages.error(request, error_msg)
        else:
            # Crear usuario normal (NO superusuario)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            user.is_active = True  # El usuario puede iniciar sesión pero debe verificar email
            user.save()
            
            # Crear o actualizar perfil con los datos adicionales
            perfil, _ = Perfil.objects.get_or_create(user=user)
            perfil.telefono = telefono
            perfil.direccion = direccion
            perfil.fecha_nacimiento = fecha_nacimiento
            perfil.save()
            
            # Crear token de verificación
            verificacion = VerificacionEmail.objects.create(user=user)
            
            # Enviar email de verificación
            enviar_email_verificacion(user, verificacion.token, request)
            
            messages.success(request, '¡Cuenta creada! Te hemos enviado un email de verificación. Por favor revisa tu correo.')
            return redirect(LOGIN_ROUTE_NAME)
    
    return render(request, 'registro.html')


##-------------------------------------------------------------------------------###
def enviar_email_verificacion(user, token, request):
    """Envía el email de verificación al usuario"""
    verification_url = request.build_absolute_uri(
        reverse('login:verificar_email', args=[token])
    )
    
    subject = 'Verifica tu cuenta - Sistema Contable'
    message = f'''
Hola {user.username},

¡Gracias por registrarte en el Sistema Contable!

Para completar tu registro, por favor verifica tu dirección de email haciendo clic en el siguiente enlace:

{verification_url}

Este enlace es válido por 24 horas.

Si no creaste esta cuenta, puedes ignorar este mensaje.

Saludos,
Equipo de Sistema Contable
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Error al enviar email de verificación a {user.email}: {e}")

@require_GET
def verificar_email_view(request, token):
    """Vista para verificar el email del usuario"""
    try:
        verificacion = get_object_or_404(VerificacionEmail, token=token)
        
        if verificacion.verificado:
            messages.info(request, 'Tu email ya ha sido verificado anteriormente.')
            return redirect(LOGIN_ROUTE_NAME)
        
        if not verificacion.es_valido():
            messages.error(request, 'El enlace de verificación ha expirado. Por favor solicita uno nuevo.')
            return redirect(LOGIN_ROUTE_NAME)
        
        # Marcar como verificado
        verificacion.verificado = True
        verificacion.fecha_verificacion = timezone.now()
        verificacion.save()
        
        messages.success(request, '¡Email verificado exitosamente! Ahora puedes iniciar sesión.')
        return redirect(LOGIN_ROUTE_NAME)
        
    except Exception as _:
        messages.error(request, 'Token de verificación inválido.')
        return redirect(LOGIN_ROUTE_NAME)

# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def solicitar_recuperacion_view(request):
    """Vista para solicitar recuperación de contraseña"""
    if request.user.is_authenticated:
        return redirect(DASHBOARD_HOME)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Por favor ingresa tu email')
            return render(request, 'solicitar_recuperacion.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Crear token de recuperación
            recuperacion = RecuperacionContrasena.objects.create(
                user=user,
                ip_address=get_client_ip(request)
            )
            
            # Enviar email
            enviar_email_recuperacion(user, recuperacion.token, request)
            
            messages.success(request, 'Te hemos enviado un email con instrucciones para recuperar tu contraseña.')
            return redirect(LOGIN_ROUTE_NAME)
            
        except User.DoesNotExist:
            # Por seguridad, no revelamos si el email existe o no
            messages.success(request, 'Si el email existe, recibirás instrucciones para recuperar tu contraseña.')
            return redirect(LOGIN_ROUTE_NAME)
    
    return render(request, 'solicitar_recuperacion.html')

# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def restablecer_contrasena_view(request, token):
    """Vista para restablecer contraseña con token"""
    try:
        recuperacion = get_object_or_404(RecuperacionContrasena, token=token)
        
        if recuperacion.usado:
            messages.error(request, 'Este enlace ya ha sido utilizado.')
            return redirect(LOGIN_ROUTE_NAME)
        
        if not recuperacion.es_valido():
            messages.error(request, 'Este enlace ha expirado. Por favor solicita uno nuevo.')
            return redirect('login:solicitar_recuperacion')
        
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if not password1 or not password2:
                messages.error(request, 'Todos los campos son obligatorios')
            elif password1 != password2:
                messages.error(request, 'Las contraseñas no coinciden')
            elif len(password1) < 6:
                messages.error(request, ERROR_CLAVE_CORTA)
            else:
                # Cambiar contraseña
                user = recuperacion.user
                user.set_password(password1)
                user.save()
                
                # Marcar token como usado
                recuperacion.usado = True
                recuperacion.fecha_uso = timezone.now()
                recuperacion.save()
                
                messages.success(request, '¡Contraseña restablecida exitosamente! Ahora puedes iniciar sesión.')
                return redirect(LOGIN_ROUTE_NAME)
        
        return render(request, 'restablecer_contrasena.html', {'token': token})
        
    except Exception as _:
        messages.error(request, 'Enlace inválido.')
        return redirect(LOGIN_ROUTE_NAME)

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def enviar_email_recuperacion(user, token, request):
    """Envía el email de recuperación de contraseña"""
    recovery_url = request.build_absolute_uri(
        reverse('login:restablecer_contrasena', args=[token])
    )
    
    subject = 'Recuperación de contraseña - Sistema Contable'
    message = f'''
Hola {user.username},

Hemos recibido una solicitud para restablecer tu contraseña.

Para crear una nueva contraseña, haz clic en el siguiente enlace:

{recovery_url}

Este enlace es válido por 1 hora.

Si no solicitaste este cambio, puedes ignorar este mensaje.

Saludos,
Equipo de Sistema Contable
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Error al enviar email de recuperación a {user.email}: {e}")

@require_POST
def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('login:login')

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def perfil_view(request):
    """Vista para ver y editar el perfil del usuario"""
    # Asegurar que el usuario tenga un perfil
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Actualizar datos del usuario
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Actualizar datos del perfil
        perfil.telefono = request.POST.get('telefono', '')
        perfil.direccion = request.POST.get('direccion', '')
        perfil.bio = request.POST.get('bio', '')
        
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        if fecha_nacimiento:
            perfil.fecha_nacimiento = fecha_nacimiento
        
        # Manejar la foto de perfil
        if 'foto' in request.FILES:
            perfil.foto = request.FILES['foto']
        
        perfil.save()
        messages.success(request, '¡Perfil actualizado correctamente!')
        return redirect('login:perfil')
    
    return render(request, 'perfil.html', {'perfil': perfil})

@login_required
@never_cache
# NOSONAR - Django CSRF protection is enabled by default for POST requests
@require_http_methods(['GET', 'POST'])
def cambiar_contrasena_view(request):
    """Vista para cambiar la contraseña del usuario"""
    if request.method == 'POST':
        password_actual = request.POST.get('password_actual')
        password_nueva = request.POST.get('password_nueva')
        password_confirmacion = request.POST.get('password_confirmacion')
        
        # Validar contraseña actual
        if not request.user.check_password(password_actual):
            messages.error(request, 'La contraseña actual es incorrecta')
            return render(request, CAMBIAR_CONTRASENA_TEMPLATE)
        
        # Validar nueva contraseña
        if not password_nueva or not password_confirmacion:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, CAMBIAR_CONTRASENA_TEMPLATE)
        
        if password_nueva != password_confirmacion:
            messages.error(request, 'Las contraseñas nuevas no coinciden')
            return render(request, CAMBIAR_CONTRASENA_TEMPLATE)
        
        if len(password_nueva) < 6:
            messages.error(request, ERROR_PASSWORD_TOO_SHORT)
            return render(request, CAMBIAR_CONTRASENA_TEMPLATE)
        
        # Cambiar contraseña
        request.user.set_password(password_nueva)
        request.user.save()
        
        # Mantener la sesión activa después del cambio
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, '¡Contraseña cambiada exitosamente!')
        return redirect('dashboard:home')
    
    return render(request, CAMBIAR_CONTRASENA_TEMPLATE)

# ------------------------
# Helpers de autenticación
# ------------------------

def _get_login_attempt(username, ip_address):
    try:
        return IntentoLogin.objects.get(username=username, ip_address=ip_address)
    except IntentoLogin.DoesNotExist:
        return None

def _response_if_blocked(intento, request):
    if intento and intento.esta_bloqueado():
        tiempo_restante = intento.bloqueado_hasta - timezone.now()
        minutos = int(tiempo_restante.total_seconds() / 60)
        messages.error(request, f'Cuenta bloqueada temporalmente. Intenta de nuevo en {minutos} minutos.')
        return render(request, LOGIN_TEMPLATE, {'bloqueado': True, 'intentos': intento.intentos})
    return None

def _requires_email_verification(user):
    return (not user.is_superuser) and hasattr(user, 'verificacion') and (not user.verificacion.verificado)

def _handle_failed_login(intento, username, ip_address, request):
    if intento:
        intento.incrementar_intentos()
    else:
        intento = IntentoLogin.objects.create(
            username=username,
            ip_address=ip_address,
            intentos=1
        )

    intentos_restantes = 5 - intento.intentos
    if intentos_restantes > 0:
        messages.error(request, f'Usuario o contraseña incorrectos. Te quedan {intentos_restantes} intentos.')
    else:
        messages.error(request, 'Cuenta bloqueada por 15 minutos debido a múltiples intentos fallidos.')

    return render(request, LOGIN_TEMPLATE, {'intentos': intento.intentos})

def _handle_successful_login(request, user, intento):
    if intento:
        intento.resetear()
    login(request, user)
    messages.success(request, f'¡Bienvenido {user.username}!')
    return redirect(DASHBOARD_HOME)

# ------------------------
# Validaciones de registro
# ------------------------

def _validate_registration(
    *,
    username,
    email,
    password1,
    password2,
    first_name,
    last_name,
    telefono,
    direccion,
    fecha_nacimiento,
):
    """Devuelve un mensaje de error si alguna validación falla; None si todo ok."""
    if not username or not password1 or not password2:
        return 'Usuario y contraseñas son obligatorios'
    if not first_name or not last_name:
        return 'Nombre y apellido son obligatorios'
    if not telefono:
        return 'El teléfono es obligatorio'
    if not direccion:
        return 'La dirección es obligatoria'
    if not fecha_nacimiento:
        return 'El año de nacimiento es obligatorio'
    if password1 != password2:
        return 'Las contraseñas no coinciden'
    if len(password1) < 6:
        return ERROR_CLAVE_CORTA
    if User.objects.filter(username=username).exists():
        return 'El nombre de usuario ya existe'
    if email and User.objects.filter(email=email).exists():
        return 'El email ya está registrado'
    return None
