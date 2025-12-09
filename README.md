# 🚀 Multi-Tenant SaaS - Backend FASE 1

Sistema backend para plataforma SaaS Multi-Tenant dirigida a cafeterías, restaurantes, heladerías y negocios similares.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Stack Tecnológico](#-stack-tecnológico)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Endpoints API](#-endpoints-api)
- [Documentación](#-documentación)

---

## ✨ Características

### FASE 1 - Completada

- ✅ **Multi-tenant por columna** (`business_id`)
- ✅ **Autenticación JWT** (access + refresh tokens)
- ✅ **Sistema de roles** (owner, admin, cashier, waiter, cook)
- ✅ **Registro de negocios** (primer usuario = owner)
- ✅ **Auditoría de acciones**
- ✅ **Clean Architecture + SOLID**
- ✅ **PostgreSQL + SQLAlchemy Async**
- ✅ **Dockerizado** (backend + PostgreSQL)
- ✅ **Migraciones con Alembic**

---

## 🛠️ Stack Tecnológico

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Base de Datos**: PostgreSQL 15
- **Migraciones**: Alembic
- **Autenticación**: python-jose (JWT)
- **Hashing**: passlib + bcrypt
- **Containerización**: Docker + Docker Compose

---

## 📦 Requisitos Previos

- Docker Desktop instalado
- Docker Compose instalado
- Git (opcional)
- PgAdmin de escritorio (opcional, para visualizar BD)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repo>
cd APP-LOCALES
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` si necesitas cambiar alguna configuración:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/multi_tenant
SECRET_KEY=your-secret-key-change-in-production-min-32-chars-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Levantar servicios con Docker

Desde la raíz del proyecto:

```bash
docker-compose up --build
```

Esto levantará:
- **Backend** en `http://localhost:8000`
- **PostgreSQL** en `localhost:5432`

### 4. Verificar que funciona

Abre tu navegador en:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🎮 Uso

### 1. Registrar un negocio

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Cafetería Central",
    "email": "admin@cafeteria.com",
    "password": "securepass123",
    "full_name": "Juan Pérez"
  }'
```

**Respuesta**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@cafeteria.com",
    "password": "securepass123"
  }'
```

### 3. Obtener perfil del usuario

```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer {tu_access_token}"
```

### 4. Listar usuarios del negocio

```bash
curl -X GET "http://localhost:8000/users/" \
  -H "Authorization: Bearer {tu_access_token}"
```

### 5. Renovar token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "{tu_refresh_token}"
  }'
```

---

## 📁 Estructura del Proyecto

```
APP-LOCALES/
│
├── app/
│   ├── config/              # Configuración (settings, database)
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── business/
│   │   ├── users/
│   │   └── audit/
│   ├── schemas/             # Schemas Pydantic
│   │   ├── business/
│   │   ├── users/
│   │   └── auth/
│   ├── repositories/        # Capa de datos
│   │   ├── business/
│   │   ├── users/
│   │   └── audit/
│   ├── services/            # Lógica de negocio
│   │   ├── auth/
│   │   └── users/
│   ├── controllers/         # Manejo de requests
│   │   ├── auth/
│   │   └── users/
│   ├── routers/             # Definición de rutas
│   │   ├── auth/
│   │   └── users/
│   ├── middleware/          # Middlewares
│   ├── dependencies/        # FastAPI dependencies
│   ├── utils/               # Utilidades (security)
│   └── main.py              # Punto de entrada
│
├── alembic/                 # Migraciones
│   └── versions/
│
├── docs/                    # Documentación
│   ├── REQUERIMIENTOS_FASE1.md
│   ├── MODELO_ER_FASE1.md
│   └── FLUJO_MULTI_TENANT.md
│
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 🌐 Endpoints API

### Autenticación

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Registrar usuario + negocio | No |
| POST | `/auth/login` | Login | No |
| POST | `/auth/refresh` | Renovar access token | No |

### Usuarios

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/users/me` | Obtener perfil actual | Sí |
| GET | `/users/` | Listar usuarios del negocio | Sí |

### Sistema

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/` | Información de la API | No |
| GET | `/health` | Health check | No |
| GET | `/docs` | Documentación Swagger | No |

---

## 📚 Documentación

### Documentos disponibles

- **[Requerimientos FASE 1](docs/REQUERIMIENTOS_FASE1.md)**: Funcionales y no funcionales
- **[Modelo ER](docs/MODELO_ER_FASE1.md)**: Diseño de base de datos
- **[Flujo Multi-Tenant](docs/FLUJO_MULTI_TENANT.md)**: Explicación detallada del multi-tenancy

### Swagger UI

Accede a la documentación interactiva en:

http://localhost:8000/docs

---

## 🗄️ Base de Datos

### Conectar con PgAdmin (Desktop)

1. Abre PgAdmin
2. Crea un nuevo servidor:
   - **Host**: `localhost`
   - **Port**: `5432`
   - **Database**: `multi_tenant`
   - **Username**: `postgres`
   - **Password**: `postgres`

### Tablas

- `business`: Negocios
- `users`: Usuarios
- `audit_logs`: Auditoría

### Migraciones

Las migraciones se ejecutan automáticamente al levantar Docker.

Para ejecutar manualmente:

```bash
docker-compose exec backend alembic upgrade head
```

Para crear una nueva migración:

```bash
docker-compose exec backend alembic revision --autogenerate -m "descripcion"
```

---

## 🧪 Testing

### Test Multi-Tenancy

1. Registra dos negocios diferentes
2. Login con cada uno
3. Verifica que cada uno solo ve sus propios usuarios

```bash
# Negocio 1
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Cafetería A",
    "email": "admin@cafeteria-a.com",
    "password": "pass123",
    "full_name": "Admin A"
  }'

# Negocio 2
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Restaurante B",
    "email": "admin@restaurante-b.com",
    "password": "pass123",
    "full_name": "Admin B"
  }'
```

---

## 🔐 Seguridad

- **Contraseñas hasheadas** con bcrypt (12 rounds)
- **JWT firmado** con HS256
- **Tokens de corta duración** (30 min access, 7 días refresh)
- **Filtrado automático** por business_id
- **CORS configurado** (ajustar en producción)

---

## 🐛 Troubleshooting

### El backend no inicia

```bash
# Ver logs
docker-compose logs backend

# Reiniciar servicios
docker-compose restart
```

### Error de conexión a PostgreSQL

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Ver logs de PostgreSQL
docker-compose logs db
```

### Limpiar y reiniciar

```bash
# Detener servicios
docker-compose down

# Eliminar volúmenes (⚠️ borra la BD)
docker-compose down -v

# Reconstruir
docker-compose up --build
```

---

## 🚀 Próximas Fases

- **FASE 2**: Módulo de Inventario
- **FASE 3**: Punto de Venta (POS)
- **FASE 4**: Reportes y Analytics
- **FASE 5**: Cocina/Barra con WebSockets
- **FASE 6**: Contabilidad y Facturación

---

## 📝 Licencia

Este proyecto es privado y confidencial.

---

## 👨‍💻 Desarrollado con

- Clean Architecture
- SOLID Principles
- Multi-Tenant Best Practices
- FastAPI Best Practices

**¡Backend listo para escalar a SaaS!** 🎉
