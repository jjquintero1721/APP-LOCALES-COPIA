# Requerimientos FASE 1 - Backend Multi-Tenant SaaS

## 📌 Descripción General

Sistema backend para plataforma SaaS Multi-Tenant dirigida a cafeterías, restaurantes, heladerías y negocios similares. Cada negocio (tenant) opera de forma aislada con sus propios datos.

---

## ✅ Requerimientos Funcionales

### RF-001: Gestión de Negocios (Business)
- **Descripción**: Cada negocio debe poder registrarse en el sistema
- **Prioridad**: Alta
- **Criterios de Aceptación**:
  - Al registrarse, se crea automáticamente un registro de negocio (business)
  - Se genera un `business_id` único
  - El negocio tiene nombre y fecha de creación

### RF-002: Registro de Usuarios
- **Descripción**: Permitir registro de nuevos usuarios asociados a un negocio
- **Prioridad**: Alta
- **Criterios de Aceptación**:
  - El primer usuario se registra como "owner" (dueño del negocio)
  - Requiere: email, contraseña, nombre completo, nombre del negocio
  - El email debe ser único por negocio
  - La contraseña debe hashearse con bcrypt
  - Se genera automáticamente el negocio en el primer registro

### RF-003: Autenticación JWT
- **Descripción**: Sistema de autenticación basado en tokens JWT
- **Prioridad**: Alta
- **Criterios de Aceptación**:
  - Login con email y contraseña
  - Genera access_token (corta duración: 30 min)
  - Genera refresh_token (larga duración: 7 días)
  - El JWT debe incluir: user_id, business_id, role

### RF-004: Refresh Token
- **Descripción**: Renovación de tokens sin necesidad de login
- **Prioridad**: Alta
- **Criterios de Aceptación**:
  - Endpoint que recibe refresh_token
  - Valida el refresh_token
  - Genera nuevo access_token

### RF-005: Sistema de Roles
- **Descripción**: Roles predefinidos para control de acceso
- **Prioridad**: Alta
- **Roles Implementados**:
  - `owner`: Dueño del negocio (todos los permisos)
  - `admin`: Administrador del negocio
  - `cashier`: Cajero
  - `waiter`: Mesero
  - `cook`: Cocinero

### RF-006: Gestión de Usuarios
- **Descripción**: CRUD básico de usuarios por negocio
- **Prioridad**: Alta
- **Criterios de Aceptación**:
  - GET /users/me: Obtener datos del usuario autenticado
  - GET /users/: Listar usuarios del mismo negocio
  - Solo muestra usuarios del mismo business_id

### RF-007: Auditoría de Acciones
- **Descripción**: Registro de acciones críticas en el sistema
- **Prioridad**: Media
- **Criterios de Aceptación**:
  - Registra: login, registro de usuarios, creación de negocios
  - Almacena: timestamp, user_id, business_id, acción
  - Filtra por business_id

---

## 🔒 Requerimientos No Funcionales

### RNF-001: Seguridad
- **Contraseñas hasheadas** con bcrypt (salt rounds: 12)
- **JWT firmado** con algoritmo HS256
- **SECRET_KEY** almacenada en variables de entorno
- **Validación de tokens** en cada request protegido
- **HTTPS ready** (configuración para producción)

### RNF-002: Multi-Tenancy
- **Aislamiento por columna**: Todas las tablas tienen `business_id`
- **Filtrado automático**: Middleware extrae `business_id` del JWT
- **Sin cruce de datos**: Imposible acceder a datos de otro negocio
- **Queries seguros**: Todos incluyen WHERE business_id = :current_business_id

### RNF-003: Arquitectura
- **Clean Architecture**: Separación en capas
- **SOLID Principles**: Código mantenible y escalable
- **Asíncrono**: FastAPI + async SQLAlchemy
- **Modular**: Separación por módulos (auth, users, etc.)

### RNF-004: Rendimiento
- **Async/Await**: Operaciones no bloqueantes
- **Connection Pooling**: SQLAlchemy con pool de conexiones
- **Índices en BD**: business_id, email, created_at

### RNF-005: Escalabilidad
- **Dockerizado**: Fácil despliegue
- **Migraciones**: Alembic para versionado de BD
- **Configuración centralizada**: Variables de entorno
- **Stateless**: JWT permite escalado horizontal

### RNF-006: Mantenibilidad
- **Estructura modular**: Carpetas por dominio
- **Separación de responsabilidades**:
  - Routers: Enrutamiento
  - Controllers: Manejo de requests
  - Services: Lógica de negocio
  - Repositories: Acceso a datos
- **Type hints**: Código tipado
- **Logging**: Registro de eventos

### RNF-007: Disponibilidad
- **Health checks**: Endpoint de salud
- **Manejo de errores**: Respuestas HTTP consistentes
- **Logging de errores**: Trazabilidad

---

## 🔌 Endpoints Implementados - FASE 1

### Autenticación

| Método | Endpoint | Descripción | Autenticado |
|--------|----------|-------------|-------------|
| POST | `/auth/register` | Registro de usuario + negocio | No |
| POST | `/auth/login` | Login (retorna access + refresh token) | No |
| POST | `/auth/refresh` | Renovar access token | No |

### Usuarios

| Método | Endpoint | Descripción | Autenticado |
|--------|----------|-------------|-------------|
| GET | `/users/me` | Obtener perfil del usuario actual | Sí |
| GET | `/users/` | Listar usuarios del negocio | Sí |

---

## 📊 Modelo de Datos

### Tabla: business
```sql
id              SERIAL PRIMARY KEY
name            VARCHAR(255) NOT NULL
created_at      TIMESTAMP DEFAULT NOW()
```

### Tabla: users
```sql
id              SERIAL PRIMARY KEY
business_id     INTEGER REFERENCES business(id)
email           VARCHAR(255) NOT NULL
full_name       VARCHAR(255) NOT NULL
hashed_password VARCHAR(255) NOT NULL
role            VARCHAR(50) DEFAULT 'cashier'
is_active       BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP DEFAULT NOW()
```

### Tabla: audit_logs
```sql
id              SERIAL PRIMARY KEY
business_id     INTEGER REFERENCES business(id)
user_id         INTEGER REFERENCES users(id) NULL
action          TEXT NOT NULL
timestamp       TIMESTAMP DEFAULT NOW()
```

---

## 🧪 Criterios de Éxito FASE 1

- ✅ Usuario puede registrarse y crear su negocio
- ✅ Usuario puede hacer login y obtener JWT
- ✅ JWT incluye user_id, business_id, role
- ✅ Usuario puede renovar su token
- ✅ Usuario puede ver su perfil
- ✅ Usuario puede listar usuarios de su negocio
- ✅ No puede ver usuarios de otros negocios
- ✅ Se registran acciones de auditoría
- ✅ Backend dockerizado y funcional
- ✅ Migraciones funcionando

---

## 🔧 Stack Tecnológico

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Database**: PostgreSQL 15
- **Migraciones**: Alembic
- **Autenticación**: python-jose (JWT)
- **Hashing**: passlib + bcrypt
- **Containerización**: Docker + Docker Compose
- **Validation**: Pydantic v2

---

## 📦 Entregables

1. Documento de requerimientos (este archivo)
2. Modelo ER de base de datos
3. Código fuente completo del backend
4. Docker Compose funcional
5. Migraciones de base de datos
6. Documentación del flujo multi-tenant
7. README con instrucciones de instalación

---

## 🚀 Próximas Fases

- **FASE 2**: Inventario multi-tenant
- **FASE 3**: Punto de Venta (POS)
- **FASE 4**: Reportes y analytics
- **FASE 5**: Módulo de cocina/barra con WebSockets
- **FASE 6**: Contabilidad y facturación
