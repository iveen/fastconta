"""
Tareas Celery para envío de emails.

PR futuro (#6): migrar email_service de llamadas síncronas a tareas Celery.

Actualmente, los emails se envían de forma síncrona dentro de los jobs:
- FELZipProcessor: send_fel_import_completada, send_fel_import_fallida, send_fel_import_cancelada
- ImportService: send_importacion_completada, send_importacion_fallida
- tenant_tasks: send_tenant_aprobado

Cuando se migren, este módulo contendrá tareas como:
- send_email_fel_completada(job_id, user_email, ...)
- send_email_importacion_completada(job_id, user_email, ...)
- send_email_tenant_aprobado(tenant_id, admin_email, ...)
- send_email_tenant_rechazado(request_id, contact_email, ...)

Nota: La ruta "app.tasks.email_tasks.*" ya está definida en celery_app.py
(task_routes), pero el módulo NO está en el `include` todavía.
Se agregará cuando se implementen las tareas concretas.
"""
# Placeholder: no hay tareas definidas todavía.
# Las tareas se agregarán en el PR #6.
