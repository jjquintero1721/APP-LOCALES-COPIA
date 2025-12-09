# 🏗️ Arquitectura del Sistema - FASE 1

## 📋 Principios Arquitectónicos

Este proyecto sigue:

- ✅ **Clean Architecture** (Arquitectura Limpia)
- ✅ **SOLID Principles** (Principios SOLID)
- ✅ **Multi-Tenant by Column** (Multi-tenant por columna)
- ✅ **Repository Pattern** (Patrón Repositorio)
- ✅ **Dependency Injection** (Inyección de Dependencias)
- ✅ **Async/Await** (Operaciones asíncronas)

---

## 🎯 Clean Architecture - Capas

```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│    (Routers - Entrada/Salida HTTP)      │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         CONTROLLERS LAYER               │
│   (Manejo de Requests y Responses)      │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         BUSINESS LOGIC LAYER            │
│         (Services - Lógica)             │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         DATA ACCESS LAYER               │
│      (Repositories - Acceso a BD)       │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│           DATABASE LAYER                │
│     (PostgreSQL + SQLAlchemy)           │
└─────────────────────────────────────────┘
```

---

## 📂 Estructura de Carpetas y Responsabilidades

### 1️⃣ **config/** - Configuración

**Responsabilidad**: Configuración global del sistema

```
config/
├── settings.py      → Variables de entorno (pydantic-settings)
└── database.py      → Conexión a BD (SQLAlchemy async)
```

**Ejemplo**:
```python
# settings.py
settings = Settings()  # Lee .env automáticamente

# database.py
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

---

### 2️⃣ **models/** - Modelos de Base de Datos

**Responsabilidad**: Definición de tablas SQL

```
models/
├── business/
│   └── business_model.py    → Tabla 'business'
├── users/
│   └── user_model.py        → Tabla 'users'
└── audit/
    └── audit_log_model.py   → Tabla 'audit_logs'
```

**Características**:
- Usan SQLAlchemy ORM
- Definen relaciones (ForeignKey)
- Incluyen índices y constraints
- Tienen `business_id` para multi-tenancy

**Ejemplo**:
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("business.id"))
    email = Column(String(255), nullable=False)
    # ...
```

---

### 3️⃣ **schemas/** - Validación de Datos

**Responsabilidad**: Validación entrada/salida (Pydantic)

```
schemas/
├── business/
│   └── business_schema.py
├── users/
│   └── user_schema.py
└── auth/
    └── auth_schema.py
```

**Tipos de Schemas**:
- **Base**: Campos comunes
- **Create**: Datos para crear (incluye password)
- **Update**: Datos para actualizar (campos opcionales)
- **Response**: Datos de salida (SIN password)

**Ejemplo**:
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str  # Se hasheará en el servicio
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    # ❌ NO incluye hashed_password
```

---

### 4️⃣ **repositories/** - Acceso a Datos

**Responsabilidad**: CRUD en base de datos

```
repositories/
├── business/
│   └── business_repository.py
├── users/
│   └── users_repository.py
└── audit/
    └── audit_repository.py
```

**Reglas**:
- Todos los queries filtran por `business_id`
- Operaciones atómicas (create, get, update, delete)
- Async/await
- NO lógica de negocio

**Ejemplo**:
```python
class UsersRepository:
    async def get_by_email(self, email: str, business_id: int):
        result = await self.db.execute(
            select(User).where(
                and_(User.email == email, User.business_id == business_id)
            )
        )
        return result.scalar_one_or_none()
```

---

### 5️⃣ **services/** - Lógica de Negocio

**Responsabilidad**: Lógica de negocio y orquestación

```
services/
├── auth/
│   └── auth_service.py      → Login, registro, tokens
└── users/
    └── users_service.py     → Gestión de usuarios
```

**Responsabilidades**:
- Validaciones de negocio
- Orquestación de repositorios
- Hashing de contraseñas
- Generación de tokens
- Auditoría

**Ejemplo**:
```python
class AuthService:
    async def register(self, data: RegisterRequest):
        # 1. Crear negocio
        business = await self.business_repo.create(data.business_name)

        # 2. Hashear contraseña
        hashed_password = get_password_hash(data.password)

        # 3. Crear usuario owner
        user = await self.users_repo.create(...)

        # 4. Auditoría
        await self.audit_repo.create_log(...)

        # 5. Generar tokens
        return TokenResponse(...)
```

---

### 6️⃣ **controllers/** - Manejo de Requests

**Responsabilidad**: Procesar requests HTTP

```
controllers/
├── auth/
│   └── auth_controller.py
└── users/
    └── users_controller.py
```

**Responsabilidades**:
- Recibir request
- Validar con Pydantic (automático)
- Llamar al servicio
- Retornar response

**Ejemplo**:
```python
class AuthController:
    @staticmethod
    async def register(data: RegisterRequest, db: AsyncSession):
        auth_service = AuthService(db)
        return await auth_service.register(data)
```

---

### 7️⃣ **routers/** - Definición de Rutas

**Responsabilidad**: Enrutamiento HTTP

```
routers/
├── auth/
│   └── auth_router.py
└── users/
    └── users_router.py
```

**Responsabilidades**:
- Definir rutas (GET, POST, PUT, DELETE)
- Asociar a controllers
- Documentación (tags, descriptions)

**Ejemplo**:
```python
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest):
    return await AuthController.register(data)
```

---

### 8️⃣ **middleware/** - Procesamiento Intermedio

**Responsabilidad**: Procesar requests/responses

```
middleware/
├── logging_middleware.py    → Log de todas las peticiones
└── (futuros: auth, tenant, rate_limit)
```

**Ejemplo**:
```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.info(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
```

---

### 9️⃣ **dependencies/** - FastAPI Dependencies

**Responsabilidad**: Inyección de dependencias

```
dependencies/
└── auth_dependencies.py     → get_current_user
```

**Ejemplo**:
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    token_data = decode_token(token)
    user = await users_repo.get_by_id(token_data.user_id, token_data.business_id)
    return user
```

---

### 🔟 **utils/** - Utilidades

**Responsabilidad**: Funciones auxiliares

```
utils/
└── security.py              → JWT, hashing
```

**Funciones**:
- `get_password_hash(password)`
- `verify_password(plain, hashed)`
- `create_access_token(user_id, business_id, role)`
- `create_refresh_token(...)`
- `decode_token(token)`

---

## 🔄 Flujo de un Request Completo

### Ejemplo: POST /auth/register

```
1. Cliente envía POST /auth/register
   ↓
2. FastAPI recibe request
   ↓
3. Router (auth_router.py)
   └── @router.post("/register")
   ↓
4. Controller (auth_controller.py)
   └── AuthController.register(data)
   ↓
5. Service (auth_service.py)
   └── AuthService.register(data)
       ├── BusinessRepository.create()  → Crea negocio
       ├── get_password_hash()          → Hashea password
       ├── UsersRepository.create()     → Crea usuario
       ├── AuditRepository.create_log() → Registra auditoría
       └── create_access_token()        → Genera JWT
   ↓
6. Response: TokenResponse
   └── { "access_token": "...", "refresh_token": "..." }
   ↓
7. Cliente recibe JSON
```

---

## 🔐 Multi-Tenancy - Implementación

### Nivel 1: Base de Datos

Todas las tablas tienen `business_id`:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES business(id),
    email VARCHAR(255),
    ...
);
```

### Nivel 2: Repositorios

Todos los queries filtran:

```python
async def get_by_id(self, user_id: int, business_id: int):
    return await self.db.execute(
        select(User).where(
            and_(User.id == user_id, User.business_id == business_id)
        )
    )
```

### Nivel 3: JWT

El token incluye `business_id`:

```json
{
  "user_id": 1,
  "business_id": 3,
  "role": "owner",
  "exp": 1234567890
}
```

### Nivel 4: Validación

Controllers extraen `business_id` del usuario autenticado:

```python
async def get_users(current_user: User = Depends(get_current_user)):
    # current_user.business_id se usa para filtrar
    return await users_service.get_all_users(current_user.business_id)
```

---

## 🧩 SOLID Principles Aplicados

### 1. Single Responsibility Principle (SRP)

Cada clase tiene UNA responsabilidad:
- **Router**: Solo enruta
- **Controller**: Solo maneja requests
- **Service**: Solo lógica de negocio
- **Repository**: Solo acceso a datos

### 2. Open/Closed Principle (OCP)

Abierto a extensión, cerrado a modificación:
- Nuevos módulos sin cambiar existentes
- Nuevos roles sin modificar código actual

### 3. Liskov Substitution Principle (LSP)

Los repositorios son intercambiables:
- Mismo interfaz
- Mismo comportamiento esperado

### 4. Interface Segregation Principle (ISP)

No hay interfaces forzadas:
- Cada servicio solo depende de lo que necesita
- No métodos no utilizados

### 5. Dependency Inversion Principle (DIP)

Dependencias por abstracción:
- Controllers dependen de Services (abstracción)
- Services dependen de Repositories (abstracción)
- NO dependencias concretas

---

## 📊 Ventajas de esta Arquitectura

### ✅ Mantenibilidad

- Código organizado por dominio
- Fácil encontrar y modificar código
- Cambios localizados

### ✅ Escalabilidad

- Fácil agregar nuevos módulos
- Fácil agregar nuevos endpoints
- Fácil agregar nuevos roles

### ✅ Testabilidad

- Cada capa se puede testear independientemente
- Mocks fáciles de crear
- Tests unitarios + integración

### ✅ Reusabilidad

- Servicios reutilizables
- Repositorios reutilizables
- Schemas reutilizables

### ✅ Seguridad

- Multi-tenancy garantizado
- Validaciones en múltiples capas
- JWT seguro

---

## 🔮 Preparado para el Futuro

Esta arquitectura está lista para:

- ✅ Agregar nuevos módulos (inventario, ventas, etc.)
- ✅ Agregar autenticación OAuth2
- ✅ Agregar caché (Redis)
- ✅ Agregar mensajería (RabbitMQ)
- ✅ Agregar WebSockets
- ✅ Agregar testing automatizado
- ✅ Escalar horizontalmente
- ✅ Microservicios (si fuera necesario)

**La base es sólida y profesional** 🎉
