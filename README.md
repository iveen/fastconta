# FastConta 💼

SaaS contable multi‑tenant para Guatemala, construido con FastAPI, PostgreSQL, Vue 3 y TailwindCSS.  
Permite a firmas contables llevar la contabilidad de múltiples clientes (empresas) de forma aislada, segura y escalable.

---

## 🚀 Stack Tecnológico

| Capa | Tecnología |
| --- | --- |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic V2 |
| **Base de Datos** | PostgreSQL 14+ (esquemas físicos separados por tenant) |
| **Autenticación** | JWT (JSON Web Tokens) con roles granulares |
| **Frontend** | Vue 3 (Composition API), Vite, TailwindCSS, Pinia, `vue3-toastify` |
| **Gestión de Paquetes** | `pnpm` (Frontend), `pip` / `venv` (Backend) |

---

## 📁 Estructura del Proyecto

```text
fastconta/
├── backend/                     # API FastAPI
│   ├── app/
│   │   ├── api/v1/endpoints/    # Endpoints REST (auth, tenants, activos_fijos, partidas, etc.)
│   │   ├── core/                # Configuración, seguridad, tenant_utils, empresa_utils
│   │   ├── db/                  # Motor de base de datos y sesiones asíncronas
│   │   ├── models/              # Modelos SQLAlchemy (globales y de tenant)
│   │   ├── schemas/             # Esquemas de validación Pydantic V2
│   │   └── services/            # Lógica de negocio (cálculos, FEL parser, etc.)
│   ├── alembic/                 # Migraciones globales (schema public)
│   ├── alembic_tenant/          # Migraciones específicas por tenant
│   └── manage.py                # Scripts de gestión y seed de datos
├── frontend/                    # Aplicación Vue 3 + TailwindCSS
└── README.md
```

---

## ✨ Funcionalidades Principales

### 🔐 Autenticación y Roles
- Login seguro con JWT.
- Roles jerárquicos: `superadmin`, `tenant_manager`, `contador`, `auxiliar`, `cliente`.
- Protección de endpoints y aislamiento de datos por rol y tenant.

### 🏢 Multi‑tenancy Robusto
- Cada tenant posee su propio schema físico en PostgreSQL (ej: `tenant_contaguate`).
- Centralización de la lógica de aislamiento en `tenant_utils.py` y `empresa_utils.py`.
- Validación de NIT/CUI guatemalteco (incluye cambios fiscales desde 2020).

### 📊 Plan de Cuentas y Partidas
- Catálogo de cuentas jerárquico (código, nombre, tipo, naturaleza).
- Creación de asientos con validación estricta de partida doble (débito = crédito).
- Numeración automática de pólizas y validación de períodos fiscales abiertos.

### 🏗️ Módulo de Activos Fijos (NUEVO)
- **Catálogo SAT**: Categorías predefinidas con límites máximos de depreciación (Decreto 10-2012, Art. 28).
- **Códigos Automáticos**: Generación inteligente de códigos internos basada en prefijos de categoría (ej: `VEH-0001`).
- **Depreciación Prorrateada**: Cálculo preciso por días para el mes de adquisición y ajuste exacto en el mes final de vida útil.
- **Proyección Visual**: Tabla dinámica que distingue entre histórico real y proyección futura hasta alcanzar el valor residual.
- **Cierre Mensual**: Procesamiento consolidado que genera automáticamente una Partida de Diario con los asientos de depreciación.

### 📄 Factura Electrónica (FEL)
- Carga masiva de XML con parsing inteligente (emisor, receptor, ítems, totales, certificaciones).
- Soporte para Compras, Ventas y Exportaciones, con manejo multi-moneda (GTQ/USD).
- Validación de duplicados, estructura XML SAT y clasificación automática.

### 📈 Reportes Financieros
- Balance de Comprobación (sumas y saldos).
- Estado de Resultados y Balance General.

---

## 🎨 Mejoras Recientes de UI/UX y Arquitectura

- **Notificaciones Elegantes**: Reemplazo de `alert()` nativos por `vue3-toastify` para mensajes no bloqueantes y visualmente coherentes con TailwindCSS.
- **Persistencia de Contexto**: La empresa seleccionada se mantiene en `localStorage` y Pinia, evitando re-selecciones al navegar entre listado, edición y proyección.
- **Ciclo de Vida Async Robusto**: Implementación del patrón `flush()` → `refresh()` → `commit()` en SQLAlchemy para evitar errores de serialización (`MissingGreenlet`) y garantizar que el `search_path` del tenant se mantenga activo durante las consultas de relaciones.
- **Navegación Absoluta**: Uso de `path` en Vue Router para evitar errores de rutas no encontradas (`No match for`) en entornos anidados.

---

## ⚙️ Requisitos Previos

- Python 3.12+
- PostgreSQL 14+ (con extensión `pgcrypto` habilitada)
- Node.js 18+ y `pnpm` instalado globalmente
- Entorno virtual de Python (`venv`)

---

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/iveen/fastconta.git
cd fastconta
```

### 2. Configurar el Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

Crea un archivo `.env` en `backend/`:
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=fastconta_user
DATABASE_PASSWORD=fastconta_pass
DATABASE_NAME=fastconta_db

SECRET_KEY=tu-clave-secreta-muy-larga
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Configurar la Base de Datos
```sql
CREATE USER fastconta_user WITH PASSWORD 'fastconta_pass';
CREATE DATABASE fastconta_db OWNER fastconta_user;
-- Habilitar extensión requerida
\c fastconta_db
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### 4. Aplicar Migraciones y Crear Superadmin
```bash
# Ejecutar migraciones globales
python manage.py public

# Generar hash de contraseña
python -c "from app.core.security import get_password_hash; print(get_password_hash('admin'))"
```
Inserta el hash generado en PostgreSQL:
```sql
INSERT INTO public.users (id, email, hashed_password, full_name, role, is_active)
VALUES (gen_random_uuid(), 'superadmin@fastconta.com', '<TU_HASH_AQUI>', 'Super Admin', 'superadmin', true);
```

### 5. Iniciar el Servidor Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
> 📖 Documentación interactiva disponible en: http://localhost:8001/docs

### 6. Configurar el Frontend
```bash
cd ../frontend
pnpm install
pnpm dev
```
> 🌐 La aplicación estará disponible en: http://localhost:5173

---

## 🧪 Flujo de Prueba Rápido

1. Inicia sesión como `superadmin@fastconta.com` / `admin`.
2. Crea un nuevo tenant: `POST /api/v1/tenants/` (o desde la UI si está habilitado).
3. Inicia sesión como el administrador del nuevo tenant.
4. Crea una empresa, configura el plan de cuentas y registra tus primeros **Activos Fijos**.
5. Prueba la generación automática de códigos y visualiza la proyección de depreciación.

---

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor, abre un *issue* para discutir cambios grandes o envía un *Pull Request* siguiendo el estándar de *Conventional Commits*.

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver el archivo `LICENSE` para más detalles.

---

## ✨ Créditos

Desarrollado con ❤️ por **Iveen Duarte**.  
*Proyecto en desarrollo activo. ¡Pronto más funcionalidades!*
