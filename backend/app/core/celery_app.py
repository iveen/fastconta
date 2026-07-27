"""
Configuración de Celery para FastConta.

ADR 001: Reemplazo de BackgroundTasks con Redis + Celery.

Consideraciones multi-tenant:
- Cada tarea recibe `schema_name` como parámetro
- La tarea debe ejecutar `SET LOCAL search_path TO {schema_name}, public`
  antes de cualquier operación de BD
- Los workers son compartidos entre tenants, el aislamiento se hace por tarea
"""
import logging

from celery import Celery
from celery.signals import setup_logging, worker_process_init

from app.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Instancia principal de Celery
# ──────────────────────────────────────────────
celery_app = Celery(
    "fastconta",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        # Registrar módulos de tareas aquí (se agregan en PRs siguientes)
        # "app.tasks.fel_tasks",
        # "app.tasks.inventario_tasks",
    ],
)

# ──────────────────────────────────────────────
# Configuración general
# ──────────────────────────────────────────────
celery_app.conf.update(
    # Serialización
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone Guatemala
    timezone="America/Guatemala",
    enable_utc=True,
    
    # ── Confiabilidad ──────────────────────────
    # Ack DESPUÉS de ejecutar (no antes). Si el worker muere, la tarea
    # vuelve a la cola automáticamente.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    
    # ── Retries automáticos ────────────────────
    task_autoretry_for=(ConnectionError, TimeoutError, OSError),
    task_max_retries=3,
    task_retry_backoff=60,       # 1min, 2min, 4min entre retries
    task_retry_backoff_max=600,  # Máximo 10min entre retries
    task_retry_jitter=True,      # Evita thundering herd
    
    # ── Concurrencia ───────────────────────────
    # 1 tarea por worker a la vez (nuestros jobs son pesados: parseo XML, BD)
    worker_prefetch_multiplier=1,
    
    # ── Timeouts ───────────────────────────────
    # Soft limit: lanza SoftTimeLimitExceeded (la tarea puede capturarla)
    task_soft_time_limit=600,    # 10 minutos
    # Hard limit: mata el proceso (último recurso)
    task_time_limit=660,         # 11 minutos
    
    # ── Rate limiting (protección multi-tenant) ─
    task_default_rate_limit="30/m",
    
    # ── Routing por tipo de tarea ──────────────
    # Permite tener workers especializados en el futuro
    task_routes={
        "app.tasks.fel_tasks.*": {"queue": "fel"},
        "app.tasks.inventario_tasks.*": {"queue": "inventario"},
        "app.tasks.email_tasks.*": {"queue": "email"},
    },
    
    # ── Resultado ──────────────────────────────
    # No guardamos resultados en Redis (usamos nuestra BD para tracking)
    task_ignore_result=True,
    
    # ── Worker health ──────────────────────────
    worker_max_tasks_per_child=50,  # Reinicia worker cada 50 tareas
)


# ──────────────────────────────────────────────
# Signals: hooks de ciclo de vida
# ──────────────────────────────────────────────

@setup_logging.connect
def configure_logging(sender=None, **kwargs):
    """
    Celery por default overridea la configuración de logging.
    Este signal evita que lo haga y respeta nuestro logging config.
    """
    import logging.config
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
    })


@worker_process_init.connect
def on_worker_process_init(**kwargs):
    """
    Se ejecuta cuando un worker child process inicia.
    Útil para inicializar conexiones de BD, caches, etc.
    """
    logger.info("🚀 Celery worker process initialized")
