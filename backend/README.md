# FastConta

**SaaS contable multi‑tenant para Guatemala**, construido con **FastAPI**, **PostgreSQL**, **Vue 3** y **TailwindCSS**.  
Permite a firmas contables llevar la contabilidad de múltiples clientes (empresas) de forma aislada, segura y escalable.

---

## 🚀 Stack tecnológico

| Capa        | Tecnología                                            |
|-------------|-------------------------------------------------------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic V2 |
| **Base de datos** | PostgreSQL (esquemas separados por tenant)       |
| **Autenticación** | JWT (JSON Web Tokens)                           |
| **Frontend**| Vue 3 (Composition API), Vite, TailwindCSS, pnpm     |
| **Empaquetado** | pnpm (en lugar de npm)                          |

---

## 📁 Estructura del proyecto
fastconta/
├── backend/ # API FastAPI
│ ├── app/
│ │ ├── api/v1/endpoints/ # Endpoints REST (auth, tenants, empresas, partidas, balances, cierre)
│ │ ├── core/ # Configuración, seguridad, lógica de tenants
│ │ ├── crud/ # Funciones auxiliares (secuencias)
│ │ ├── db/ # Módulo de base de datos (engine, sesiones)
│ │ ├── models/ # Modelos SQLAlchemy (globales y de tenant)
│ │ └── schemas/ # Esquemas Pydantic
│ ├── alembic/ # Migraciones globales (tablas public)
│ ├── alembic_tenant/ # Migraciones de tenant (schemas separados)
│ ├── db/ # Scripts SQL (creación de tablas por tenant)
│ ├── manage.py # Comandos de gestión de migraciones
│ └── requirements.txt
├── frontend/ # (próximamente) Aplicación Vue 3 + TailwindCSS
└── README.md


---

## ✨ Funcionalidades principales

### 🔐 Autenticación y roles
- Login con JWT.
- Roles: **superadmin** (crea tenants), **admin de tenant** (administra su tenant) y **usuario granular** (próximamente).
- Protección de endpoints por rol.

### 🏢 Multi‑tenancy
- Cada tenant tiene su propio **schema físico** en PostgreSQL.
- Tablas de negocio (`empresas`, `plan_cuentas`, `partidas`, `detalle_partidas`, etc.) aisladas por tenant.
- Registro de tenant con **validación de NIT/CUI guatemalteco** (incluye cambios fiscales desde 2020).

### 📊 Plan de cuentas
- Catálogo de cuentas jerárquico (código, nombre, tipo, naturaleza).
- Cada cuenta pertenece a una **empresa** dentro del tenant.

### 📝 Partidas contables
- Creación de asientos con validación de **partida doble** (débito = crédito).
- Numeración automática de póliza (`POL-0001`, `POL-0002`…).
- Validaciones: cuentas **activas**, **no duplicadas**, y **período fiscal abierto**.

### 📅 Períodos fiscales y cierre contable
- Definición de períodos fiscales por empresa.
- Cierre automático de cuentas de resultado contra **Utilidad del Ejercicio** y traslado a **Utilidades Acumuladas**.
- Bloqueo de registros en períodos cerrados.

### 📈 Reportes financieros
- **Balance de Comprobación**: sumas y saldos por período y empresa.
- **Estado de Resultados**: ingresos, gastos y utilidad neta.
- **Balance General**: activo, pasivo, patrimonio y utilidad del ejercicio.

### 🛡️ Límite freemium
- Plan **freemium** (hasta 5 empresas por tenant).
- Control de abuso por IP (máximo 3 registros en 24h).

---

## ⚙️ Requisitos previos

- Python 3.12+
- PostgreSQL 14+ (con extensión `pgcrypto` habilitada)
- pnpm (para el frontend, próximamente)
- Entorno virtual de Python (recomendado `venv`)

---

## 🛠️ Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/iveen/fastconta.git
cd fastconta/backend
```

### 2. Crear y Activar el entorno virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crear un archivo .env en la raíz de **backend/** con el siguiente contenido:<br/>
```bash
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=fastconta_user
DATABASE_PASSWORD=fastconta_pass
DATABASE_NAME=fastconta_db

SECRET_KEY=tu-clave-secreta-muy-larga
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Crear la Base de Datos
```sql
CREATE USER fastconta_user WITH PASSWORD 'fastconta_pass';
CREATE DATABASE fastconta_db OWNER fastconta_user;
```

### 6. Aplicar Migraciones Globales
```bash
python manage.py public
```

### 7. Insertar usuario superadmin
Ejecuta el siguiente **SQL** en **PostgreSQL** (genera el hash de la contraseña antes)<br/>
```bash
python -c "from app.core.security import get_password_hash; print(get_password_hash('admin'))"
```

<br/>Luego en **PostgreSQL**<br/>
```sql
INSERT INTO public.users (id, email, hashed_password, full_name, role, is_active)
VALUES (gen_random_uuid(), 'superadmin@fastconta.com', '<HASH-GENERADO>', 'Super Admin', 'superadmin', true);
```
### 8. Inicia el Servidor
```bash
uvicorn app.main:app --reload
```
<br/>
La API estará disponible en **http://localhost:8000**.<br/>
Documentación interactiva en **http://localhost:8000/docs**.<br/>