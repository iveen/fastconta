"""Configuración de email desde variables de entorno."""
import os
from dataclasses import dataclass


@dataclass
class EmailConfig:
    """Configuración SMTP para envío de correos."""
    
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    use_ssl: bool
    from_email: str
    from_name: str
    app_url: str  # ✅ NUEVO: URL de la app para links en emails
    
    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Carga configuración desde variables de entorno."""
        return cls(
            host=os.getenv("SMTP_HOST", ""),
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            use_tls=os.getenv("SMTP_TLS", "True").lower() == "true",
            use_ssl=os.getenv("SMTP_SSL", "False").lower() == "true",
            from_email=os.getenv("FROM_EMAIL", "noreply@fastconta.app"),
            from_name=os.getenv("FROM_NAME", "FastConta"),
            app_url=os.getenv("APP_URL", "https://fastconta.app"),  
        )
    
    def is_configured(self) -> bool:
        """Verifica si el email está configurado correctamente."""
        return bool(self.host and self.username and self.password)


# Instancia global de configuración
email_config = EmailConfig.from_env()