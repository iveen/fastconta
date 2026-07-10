"""
Servicio principal de envío de emails.
Orquesta:
- Renderizado de templates (renderer.py)
- Envío vía SMTP (fastapi-mail)
- Manejo de errores
"""
import logging
from typing import Any

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from .config import email_config
from .renderer import email_renderer

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio singleton para envío de emails transaccionales."""
    
    _instance = None
    _fast_mail = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            if not email_config.is_configured():
                logger.warning(
                    "⚠️ Email no configurado. Verifica SMTP_HOST, SMTP_USER, SMTP_PASSWORD en .env"
                )
            else:
                # Configurar fastapi-mail
                mail_config = ConnectionConfig(
                    MAIL_USERNAME=email_config.username,
                    MAIL_PASSWORD=email_config.password,
                    MAIL_FROM=email_config.from_email,
                    MAIL_FROM_NAME=email_config.from_name,
                    MAIL_PORT=email_config.port,
                    MAIL_SERVER=email_config.host,
                    MAIL_STARTTLS=email_config.use_tls,
                    MAIL_SSL_TLS=email_config.use_ssl,
                    USE_CREDENTIALS=True,
                    VALIDATE_CERTS=True,
                )
                cls._fast_mail = FastMail(mail_config)
                logger.info(f"✅ EmailService configurado: {email_config.host}:{email_config.port}")
        
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "EmailService":
        """Obtiene la instancia singleton."""
        return cls()
    
    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        template_name: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Envía un email usando un template Jinja2.
        
        Args:
            to: Email(s) destinatario(s)
            subject: Asunto del email
            template_name: Nombre del archivo template
            context: Variables para el template
        
        Returns:
            True si se envió correctamente
        """
        if not email_config.is_configured():
            logger.error("❌ No se puede enviar email: configuración incompleta")
            return False
        
        try:
            # 1. Renderizar template
            html_content = email_renderer.render(template_name, context)
            
            # 2. Construir mensaje
            recipients = [to] if isinstance(to, str) else to
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=html_content,
                subtype=MessageType.html,
            )
            
            # 3. Enviar
            await self._fast_mail.send_message(message)
            
            logger.info(f"✅ Email enviado a {recipients}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email a {to}: {e}", exc_info=True)
            return False
    
    async def send_solicitud_recibida(
        self,
        to: str,
        company_name: str,
        contact_name: str,
    ) -> bool:
        """Envía email de confirmación al solicitar registro."""
        return await self.send_email(
            to=to,
            subject="📧 Tu solicitud de acceso a FastConta ha sido recibida",
            template_name="solicitud_recibida.html",
            context={
                "company_name": company_name,
                "contact_name": contact_name,
            },
        )
    
    async def send_tenant_aprobado(
        self,
        to: str,
        company_name: str,
        admin_email: str,
        admin_password: str,
        contact_name: str,
    ) -> bool:
        """Envía email con credenciales al aprobar un tenant."""
        return await self.send_email(
            to=to,
            subject="✅ Tu cuenta FastConta ha sido activada",
            template_name="tenant_aprobado.html",
            context={
                "company_name": company_name,
                "admin_email": admin_email,
                "admin_password": admin_password,
                "contact_name": contact_name,
            },
        )
    
    async def send_tenant_rechazado(
        self,
        to: str,
        company_name: str,
        reason: str,
        contact_name: str,
    ) -> bool:
        """Envía email de rechazo de solicitud."""
        return await self.send_email(
            to=to,
            subject="⚠️ Actualización sobre tu solicitud de FastConta",
            template_name="tenant_rechazado.html",
            context={
                "company_name": company_name,
                "reason": reason,
                "contact_name": contact_name,
            },
        )
    
    async def send_password_reset(
        self,
        to: str,
        full_name: str,
        new_password: str,
    ) -> bool:
        """Envía email con nueva contraseña temporal."""
        return await self.send_email(
            to=to,
            subject="🔑 Tu contraseña de FastConta ha sido restablecida",
            template_name="password_reset.html",
            context={
                "full_name": full_name,
                "new_password": new_password,
                "login_url": f"{email_config.app_url}/login"
            },
        )


# Instancia global para usar en endpoints
email_service = EmailService.get_instance()