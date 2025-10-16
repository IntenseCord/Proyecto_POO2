"""
Configuración de proveedores de email más utilizados
"""

EMAIL_PROVIDERS = {
    # Gmail
    'gmail.com': {
        'host': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True,
        'instructions': 'Necesitas una contraseña de aplicación de Google. Ve a: https://myaccount.google.com/apppasswords'
    },
    
    # Outlook/Hotmail
    'outlook.com': {
        'host': 'smtp-mail.outlook.com',
        'port': 587,
        'use_tls': True,
    },
    'hotmail.com': {
        'host': 'smtp-mail.outlook.com',
        'port': 587,
        'use_tls': True,
    },
    'live.com': {
        'host': 'smtp-mail.outlook.com',
        'port': 587,
        'use_tls': True,
    },
    
    # Yahoo
    'yahoo.com': {
        'host': 'smtp.mail.yahoo.com',
        'port': 587,
        'use_tls': True,
        'instructions': 'Necesitas una contraseña de aplicación de Yahoo'
    },
    'yahoo.es': {
        'host': 'smtp.mail.yahoo.com',
        'port': 587,
        'use_tls': True,
    },
    
    # iCloud
    'icloud.com': {
        'host': 'smtp.mail.me.com',
        'port': 587,
        'use_tls': True,
        'instructions': 'Necesitas una contraseña específica de app'
    },
    'me.com': {
        'host': 'smtp.mail.me.com',
        'port': 587,
        'use_tls': True,
    },
    
    # Zoho
    'zoho.com': {
        'host': 'smtp.zoho.com',
        'port': 587,
        'use_tls': True,
    },
    
    # ProtonMail
    'protonmail.com': {
        'host': 'smtp.protonmail.com',
        'port': 587,
        'use_tls': True,
        'instructions': 'Requiere ProtonMail Bridge instalado'
    },
    
    # AOL
    'aol.com': {
        'host': 'smtp.aol.com',
        'port': 587,
        'use_tls': True,
    },
}

def get_email_config(email):
    """
    Obtiene la configuración SMTP según el dominio del email
    """
    if not email or '@' not in email:
        return None
    
    domain = email.split('@')[1].lower()
    return EMAIL_PROVIDERS.get(domain)
