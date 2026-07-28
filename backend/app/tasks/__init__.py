"""
Módulo de tareas Celery para FastConta.

Cada archivo aquí representa un dominio de tareas:
- fel_tasks.py: importación de facturas FEL (ZIPs de XMLs)
- inventario_tasks.py: importación/exportación de inventarios
- email_tasks.py: envío de notificaciones por correo

Convención:
- Las tareas son funciones decoradas con @celery_app.task
- Reciben IDs (no objetos SQLAlchemy) para ser serializables
- Configuran search_path internamente para aislamiento multi-tenant
"""
