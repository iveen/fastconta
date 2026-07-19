# app/models/__init__.py
# Este archivo es CRÍTICO para resolver dependencias circulares en SQLAlchemy.
# Fuerza el orden de importación: primero los modelos globales, luego los de tenant.

# 1. Importar primero los modelos globales (esquema public)
from app.models.global_models import *  # noqa: F403

# 2. Importar después los modelos del tenant (dependen de los globales)
from app.models.tenant_models import *  # noqa: F403
