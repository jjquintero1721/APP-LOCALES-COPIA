# 🚀 Guía de Inicio Rápido - FASE 1

## ✅ ¿Qué se ha creado?

La FASE 1 del backend Multi-Tenant está **100% completa y funcional**.

### 📦 Entregables

1. ✅ **Documentación completa**
   - Requerimientos funcionales y no funcionales
   - Modelo ER de base de datos
   - Flujo multi-tenant detallado

2. ✅ **Backend completo**
   - Clean Architecture + SOLID
   - Autenticación JWT con refresh tokens
   - Sistema de roles
   - Multi-tenant por `business_id`
   - Auditoría de acciones

3. ✅ **Base de datos**
   - PostgreSQL 15
   - 3 tablas: business, users, audit_logs
   - Índices optimizados
   - Migraciones con Alembic

4. ✅ **Docker**
   - docker-compose.yml
   - Dockerfile para backend
   - PostgreSQL containerizado
   - Listo para desarrollo y producción

5. ✅ **Endpoints funcionales**
   - POST /auth/register
   - POST /auth/login
   - POST /auth/refresh
   - GET /users/me
   - GET /users/

---

## 🏃 Cómo Empezar (3 pasos)

### 1️⃣ Levantar el sistema

```bash
# Desde la raíz del proyecto
docker-compose up --build
```

Espera a ver este mensaje:
```
multi_backend    | INFO:     Application startup complete.
multi_backend    | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2️⃣ Abrir la documentación interactiva

Abre tu navegador en:

**http://localhost:8000/docs**

Verás Swagger UI con todos los endpoints disponibles.

### 3️⃣ Probar el sistema

#### Opción A: Desde Swagger UI (Fácil)

1. Ve a http://localhost:8000/docs
2. Expande `POST /auth/register`
3. Click en "Try it out"
4. Ingresa los datos:
```json
{
  "business_name": "Mi Cafetería",
  "email": "admin@micafeteria.com",
  "password": "password123",
  "full_name": "Juan Pérez"
}
```
5. Click en "Execute"
6. Copia el `access_token` de la respuesta
7. Click en el botón "Authorize" (arriba a la derecha)
8. Pega el token y click en "Authorize"
9. Ahora puedes probar los endpoints protegidos (GET /users/me, etc.)

#### Opción B: Desde cURL (Terminal)

```bash
# 1. Registrar negocio
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Mi Cafetería",
    "email": "admin@micafeteria.com",
    "password": "password123",
    "full_name": "Juan Pérez"
  }'

# Copia el access_token de la respuesta

# 2. Obtener perfil
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN_AQUI"
```

---

## 🧪 Testing Multi-Tenant

### Prueba de Aislamiento de Datos

```bash
# PASO 1: Crear Negocio A
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Cafetería A",
    "email": "admin@cafeteria-a.com",
    "password": "pass123",
    "full_name": "Admin A"
  }'
# Guarda el token como TOKEN_A

# PASO 2: Crear Negocio B
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Restaurante B",
    "email": "admin@restaurante-b.com",
    "password": "pass123",
    "full_name": "Admin B"
  }'
# Guarda el token como TOKEN_B

# PASO 3: Listar usuarios de Cafetería A
curl -X GET "http://localhost:8000/users/" \
  -H "Authorization: Bearer TOKEN_A"
# ✅ Solo verás 1 usuario (Admin A)

# PASO 4: Listar usuarios de Restaurante B
curl -X GET "http://localhost:8000/users/" \
  -H "Authorization: Bearer TOKEN_B"
# ✅ Solo verás 1 usuario (Admin B)

# ✅ RESULTADO: Los datos están COMPLETAMENTE AISLADOS
```

---

## 🗄️ Conectar a la Base de Datos

### Con PgAdmin (Desktop)

1. Abre PgAdmin
2. Click derecho en "Servers" → "Create" → "Server"
3. **General Tab**:
   - Name: `Multi-Tenant Local`
4. **Connection Tab**:
   - Host: `localhost`
   - Port: `5432`
   - Database: `multi_tenant`
   - Username: `postgres`
   - Password: `postgres`
5. Click "Save"

Ahora puedes explorar las tablas:
- `business`
- `users`
- `audit_logs`

---

## 📊 Verificar Datos

### Consultas SQL útiles

```sql
-- Ver todos los negocios
SELECT * FROM business;

-- Ver todos los usuarios con su negocio
SELECT u.id, u.email, u.full_name, u.role, b.name as business_name
FROM users u
JOIN business b ON u.business_id = b.id;

-- Ver auditoría
SELECT al.*, u.email, b.name as business_name
FROM audit_logs al
JOIN business b ON al.business_id = b.id
LEFT JOIN users u ON al.user_id = u.id
ORDER BY al.timestamp DESC;
```

---

## 🔧 Comandos Útiles

### Docker

```bash
# Ver logs del backend
docker-compose logs -f backend

# Ver logs de PostgreSQL
docker-compose logs -f db

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down

# Limpiar todo (⚠️ borra la BD)
docker-compose down -v

# Reconstruir
docker-compose up --build
```

### Alembic (Migraciones)

```bash
# Ver estado de migraciones
docker-compose exec backend alembic current

# Ejecutar migraciones pendientes
docker-compose exec backend alembic upgrade head

# Crear nueva migración (autogenerar)
docker-compose exec backend alembic revision --autogenerate -m "descripcion"

# Revertir última migración
docker-compose exec backend alembic downgrade -1
```

---

## 📁 Estructura del Código

### Flujo de un Request

```
1. Request → Router (define la ruta)
   ↓
2. Router → Controller (maneja el request)
   ↓
3. Controller → Service (lógica de negocio)
   ↓
4. Service → Repository (acceso a BD)
   ↓
5. Repository → Base de Datos
   ↓
6. Respuesta ← Controller
   ↓
7. JSON ← Cliente
```

### Ejemplo Práctico

```
GET /users/me con JWT

├── routers/users/users_router.py
│   └── @router.get("/me")
│
├── controllers/users/users_controller.py
│   └── get_me() → extrae current_user del JWT
│
├── services/users/users_service.py
│   └── (no se usa en este caso, es directo)
│
└── Respuesta: UserResponse
```

---

## 🎯 Próximos Pasos

### Para Desarrolladores

1. **Familiarízate con el código**
   - Lee `app/main.py`
   - Explora `app/routers/auth/auth_router.py`
   - Revisa `app/services/auth/auth_service.py`

2. **Experimenta con los endpoints**
   - Registra múltiples negocios
   - Crea usuarios con diferentes roles
   - Verifica el aislamiento multi-tenant

3. **Prepárate para FASE 2**
   - La arquitectura ya está lista
   - Solo hay que agregar nuevos módulos
   - Seguir el mismo patrón

### Para Product Owners

1. **Prueba la funcionalidad**
   - Registra tu negocio de prueba
   - Verifica que solo ves tus datos
   - Revisa los logs de auditoría

2. **Planifica FASE 2**
   - Definir prioridad de módulos
   - Inventario vs. POS vs. Reportes

---

## ❓ Preguntas Frecuentes

### ¿Cómo agrego un nuevo usuario a un negocio existente?

En FASE 1, solo el owner puede registrarse al crear el negocio.
En FASE 2 se agregará endpoint para que el owner invite usuarios.

### ¿Puedo cambiar el puerto del backend?

Sí, edita `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Cambia 8080 por el puerto que quieras
```

### ¿Cómo hago backup de la BD?

```bash
docker-compose exec db pg_dump -U postgres multi_tenant > backup.sql
```

### ¿Cómo restauro un backup?

```bash
docker-compose exec -T db psql -U postgres multi_tenant < backup.sql
```

---

## 🎉 ¡Listo para Desarrollar!

El backend está **100% funcional** y listo para:

- ✅ Desarrollo de frontend React
- ✅ Agregar nuevos módulos (FASE 2+)
- ✅ Testing automatizado
- ✅ Deploy a producción (con ajustes de seguridad)

**La arquitectura es sólida, escalable y profesional.**

¡Ahora puedes empezar a construir el frontend o continuar con FASE 2! 🚀
