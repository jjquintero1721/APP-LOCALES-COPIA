# Flujo Multi-Tenant - Guía Completa

## 🎯 ¿Qué es Multi-Tenancy?

Multi-tenancy significa que **múltiples negocios (tenants) comparten la misma infraestructura**, pero sus datos están **completamente aislados**.

En este sistema:
- Cada negocio tiene su propio `business_id`
- Ningún negocio puede acceder a datos de otro
- Todos los queries filtran automáticamente por `business_id`

---

## 🔐 Flujo de Autenticación Multi-Tenant

### 1️⃣ Registro (Primera vez)

```
Usuario ingresa:
├── Nombre del negocio: "Cafetería Central"
├── Email: admin@cafeteriacentral.com
├── Contraseña: ********
└── Nombre completo: Juan Pérez

Backend procesa:
├── Crea negocio → business_id = 1
├── Crea usuario owner → user_id = 1, business_id = 1
├── Genera JWT con payload:
│   {
│     "user_id": 1,
│     "business_id": 1,
│     "role": "owner"
│   }
└── Retorna access_token + refresh_token
```

**Endpoint**: `POST /auth/register`

**Request**:
```json
{
  "business_name": "Cafetería Central",
  "email": "admin@cafeteriacentral.com",
  "password": "securepass123",
  "full_name": "Juan Pérez"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 2️⃣ Login

```
Usuario ingresa:
├── Email: admin@cafeteriacentral.com
└── Contraseña: ********

Backend procesa:
├── Busca usuario por email
├── Verifica contraseña
├── Obtiene business_id del usuario
├── Genera JWT con:
│   {
│     "user_id": 1,
│     "business_id": 1,
│     "role": "owner"
│   }
└── Retorna tokens
```

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "email": "admin@cafeteriacentral.com",
  "password": "securepass123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 3️⃣ Uso del Token en Requests

Cada request protegido debe incluir el token en el header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Flujo interno**:

```
1. Request llega con token
   ↓
2. Middleware extrae token del header
   ↓
3. Decodifica JWT
   ↓
4. Obtiene: user_id, business_id, role
   ↓
5. Busca usuario en BD
   ↓
6. Verifica que user.business_id == token.business_id
   ↓
7. Inyecta current_user en el endpoint
   ↓
8. Endpoint usa current_user.business_id para filtrar
```

---

## 🛡️ Aislamiento de Datos

### Regla de Oro

**TODOS los queries DEBEN filtrar por `business_id`**

### Ejemplo: Listar Usuarios

**Request**:
```
GET /users/
Authorization: Bearer {token_con_business_id_1}
```

**Query SQL generado**:
```sql
SELECT * FROM users
WHERE business_id = 1
LIMIT 100;
```

**Resultado**:
- ✅ Retorna solo usuarios del negocio 1
- ❌ NO retorna usuarios de otros negocios

### Ejemplo: Obtener Usuario Específico

**Request**:
```
GET /users/me
Authorization: Bearer {token_con_business_id_1}
```

**Flujo**:
```
1. Token decodificado → user_id = 5, business_id = 1
2. Query: SELECT * FROM users WHERE id = 5 AND business_id = 1
3. Si existe → retorna usuario
4. Si no existe → 404 Not Found
```

---

## 🔄 Flujo Completo - Caso de Uso Real

### Escenario: Dos Negocios Separados

#### Negocio A: "Cafetería Central"
```
business_id = 1
users:
  - id=1, email=admin@cafeteria.com, role=owner
  - id=2, email=cajero@cafeteria.com, role=cashier
```

#### Negocio B: "Restaurante El Buen Sabor"
```
business_id = 2
users:
  - id=3, email=admin@restaurante.com, role=owner
  - id=4, email=mesero@restaurante.com, role=waiter
```

---

### Prueba de Aislamiento

**Usuario de Cafetería Central intenta acceder**:

```bash
# Login como admin de Cafetería
POST /auth/login
{
  "email": "admin@cafeteria.com",
  "password": "..."
}
# Retorna token con business_id = 1

# Listar usuarios
GET /users/
Authorization: Bearer {token_business_1}

# Resultado:
[
  {"id": 1, "email": "admin@cafeteria.com", ...},
  {"id": 2, "email": "cajero@cafeteria.com", ...}
]
# ✅ Solo ve usuarios de su negocio
# ❌ NO ve usuarios del Restaurante
```

---

## 🧪 Testing del Multi-Tenancy

### Test 1: Registro de Dos Negocios

```bash
# Registro Negocio 1
POST /auth/register
{
  "business_name": "Cafetería Central",
  "email": "admin1@cafe.com",
  "password": "pass123",
  "full_name": "Admin Cafe"
}
# → Crea business_id=1, user_id=1

# Registro Negocio 2
POST /auth/register
{
  "business_name": "Restaurante",
  "email": "admin2@rest.com",
  "password": "pass123",
  "full_name": "Admin Rest"
}
# → Crea business_id=2, user_id=2
```

### Test 2: Verificar Aislamiento

```bash
# Login Negocio 1
POST /auth/login
{"email": "admin1@cafe.com", "password": "pass123"}
# → Token con business_id=1

# Listar usuarios
GET /users/
Authorization: Bearer {token_business_1}
# → Solo retorna usuarios con business_id=1

# Login Negocio 2
POST /auth/login
{"email": "admin2@rest.com", "password": "pass123"}
# → Token con business_id=2

# Listar usuarios
GET /users/
Authorization: Bearer {token_business_2}
# → Solo retorna usuarios con business_id=2
```

---

## 🔒 Seguridad Multi-Tenant

### Validaciones Implementadas

1. **Token JWT incluye business_id**
   - No se puede modificar sin invalidar la firma

2. **Queries siempre filtran por business_id**
   - Imposible acceder a datos de otro negocio

3. **Unique constraints por negocio**
   - Email único POR negocio (no globalmente)
   - `UNIQUE(business_id, email)`

4. **Cascade deletes**
   - Si se elimina un negocio, se eliminan todos sus datos

---

## 📊 Diagrama de Flujo Multi-Tenant

```
┌─────────────────┐
│  Usuario 1      │
│  Negocio A      │
└────────┬────────┘
         │
         ├─ Login → JWT {business_id: A}
         │
         ├─ GET /users/ → WHERE business_id = A
         │
         └─ Solo ve datos de Negocio A

┌─────────────────┐
│  Usuario 2      │
│  Negocio B      │
└────────┬────────┘
         │
         ├─ Login → JWT {business_id: B}
         │
         ├─ GET /users/ → WHERE business_id = B
         │
         └─ Solo ve datos de Negocio B

         ╔════════════════════╗
         ║  Base de Datos     ║
         ║  ┌──────────────┐  ║
         ║  │ Negocio A    │  ║
         ║  │ business_id=A│  ║
         ║  └──────────────┘  ║
         ║  ┌──────────────┐  ║
         ║  │ Negocio B    │  ║
         ║  │ business_id=B│  ║
         ║  └──────────────┘  ║
         ╚════════════════════╝
         Datos AISLADOS
```

---

## ✅ Checklist de Implementación Multi-Tenant

- [x] Todas las tablas tienen `business_id`
- [x] JWT incluye `business_id`
- [x] Repositories filtran por `business_id`
- [x] Services usan `business_id` del token
- [x] Índices únicos incluyen `business_id`
- [x] Foreign keys con CASCADE
- [x] Auditoría por negocio
- [x] Validaciones de permisos por rol

---

## 🚀 Próximos Módulos Multi-Tenant

En las siguientes fases, TODOS los módulos seguirán el mismo patrón:

- **Inventario**: `inventory` → `business_id`
- **Productos**: `products` → `business_id`
- **Ventas**: `sales` → `business_id`
- **Reportes**: filtrados por `business_id`
- **Empleados**: `employees` → `business_id`

**La arquitectura está lista para escalar** sin cambios estructurales.
