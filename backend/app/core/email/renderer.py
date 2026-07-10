"""
Motor de renderizado de templates de email.
Responsabilidades:
- Cargar templates HTML con Jinja2
- Inyectar CSS compartido automáticamente
- Renderizar con contexto de variables
"""
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import email_config

logger = logging.getLogger(__name__)


class EmailRenderer:
    """Motor de renderizado de emails con Jinja2."""
    
    def __init__(self):
        """Inicializa el motor Jinja2 y carga el CSS compartido."""
        self.templates_dir = Path(__file__).parent / "templates"
        
        if not self.templates_dir.exists():
            raise FileNotFoundError(
                f"Directorio de templates no encontrado: {self.templates_dir}"
            )
        
        # Configurar Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
        )
        
        # ✅ NUEVO: Cargar CSS compartido
        self.shared_css = ""
        self._load_shared_css()
        
        logger.info(f"✅ EmailRenderer inicializado: {self.templates_dir}")
        logger.info(f"📄 CSS compartido: {len(self.shared_css)} bytes")
    
    def _load_shared_css(self) -> None:
        """Carga el CSS compartido desde styles.css."""
        css_path = self.templates_dir / "styles.css"
        
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                self.shared_css = f.read()
            logger.debug(f"✅ CSS compartido cargado: {len(self.shared_css)} bytes")
        else:
            logger.warning(f"⚠️ styles.css no encontrado en {self.templates_dir}")
            self.shared_css = ""
    
    def render(
        self,
        template_name: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Renderiza un template HTML con CSS inyectado.
        
        Args:
            template_name: Nombre del archivo template (ej: "tenant_aprobado.html")
            context: Variables para el template
        
        Returns:
            HTML renderizado con CSS inyectado
        """
        try:
            # Cargar template
            template = self.env.get_template(template_name)
            
            # ✅ NUEVO: Construir contexto con variables globales + CSS
            full_context = {
                **(context or {}),
                'app_url': email_config.app_url,
                'from_name': email_config.from_name,
                'shared_css': self.shared_css,  
            }
            
            # Renderizar
            html = template.render(**full_context)
            
            logger.debug(f"✅ Template renderizado: {template_name}")
            return html
            
        except Exception as e:
            logger.error(f"❌ Error renderizando template {template_name}: {e}", exc_info=True)
            raise


# Instancia global
email_renderer = EmailRenderer()