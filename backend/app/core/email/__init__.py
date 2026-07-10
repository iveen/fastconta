"""Módulo de envío de correos electrónicos para FastConta."""
from .config import email_config
from .service import EmailService

__all__ = ["EmailService", "email_config"]