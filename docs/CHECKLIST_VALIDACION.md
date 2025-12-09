# ✅ Checklist de Validación - FASE 1

## 📋 Pre-inicio

Antes de levantar el sistema, verifica:

### Sistema

- [ ] Docker Desktop está instalado y corriendo
- [ ] Docker Compose está disponible
- [ ] Tienes al menos 2GB de RAM libres
- [ ] Puerto 8000 está libre (backend)
- [ ] Puerto 5432 está libre (PostgreSQL)

### Archivos

- [ ] Existe `docker-compose.yml` en la raíz
- [ ] Existe `Dockerfile` en la raíz
- [ ] Existe `requirements.txt` en la raíz
- [ ] Existe `.env.example` en la raíz
- [ ] Existe `alembic.ini` en la raíz

---

## 🐳 Docker

### Comandos de Verificación

```bash
# Verificar Docker
docker --version
# Esperado: Docker version 20.10+ o superior

# Verificar Docker Compose
docker-compose --version
# Esperado: Docker Compose version 1.29+ o superior

# Verificar que los puertos estén libres
# Windows PowerShell:
netstat -an | findstr "8000"
netstat -an | findstr "5432"
# No debería mostrar nada (puertos libres)

# Linux/Mac:
lsof -i :8000
lsof -i :5432
# No debería mostrar nada (puertos libres)
```

---

## 🚀 Inicio del Sistema

### Paso 1: Levantar servicios

```bash
docker-compose up --build
```

### Verificaciones durante el inicio:

- [ ] PostgreSQL inicia correctamente
  ```
  multi_postgres   | database system is ready to accept connections
  ```

- [ ] Backend ejecuta migraciones
  ```
  multi_backend    | INFO  [alembic.runtime.migration] Running upgrade  -> 001
  ```

- [ ] Backend inicia correctamente
  ```
  multi_backend    | INFO:     Application startup complete.
  multi_backend    | INFO:     Uvicorn running on http://0.0.0.0:8000
  ```

---

## 🔍 Validación de Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Esperado**:
```json
{
  "status": "healthy"
}
```

- [ ] Retorna 200 OK
- [ ] JSON con "status": "healthy"

### 2. Root Endpoint

```bash
curl http://localhost:8000/
```

**Esperado**:
```json
{
  "message": "Multi-Tenant SaaS API",
  "version": "1.0.0",
  "status": "running"
}
```

- [ ] Retorna 200 OK
- [ ] JSON con información de la API

### 3. Documentación Swagger

Abrir en navegador: http://localhost:8000/docs

- [ ] Swagger UI carga correctamente
- [ ] Se ven 3 tags: Authentication, Users, Root
- [ ] Se ven 5 endpoints en total

---

## 🧪 Testing Funcional

### Test 1: Registro de Negocio

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Test Cafetería",
    "email": "test@cafe.com",
    "password": "test123456",
    "full_name": "Test User"
  }'
```

**Validaciones**:
- [ ] Retorna 201 Created
- [ ] Respuesta incluye `access_token`
- [ ] Respuesta incluye `refresh_token`
- [ ] Token es un string JWT válido (3 partes separadas por puntos)

### Test 2: Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@cafe.com",
    "password": "test123456"
  }'
```

**Validaciones**:
- [ ] Retorna 200 OK
- [ ] Respuesta incluye `access_token`
- [ ] Respuesta incluye `refresh_token`

### Test 3: Obtener Perfil (Autenticado)

```bash
# Reemplaza TOKEN con el access_token del test anterior
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer TOKEN"
```

**Validaciones**:
- [ ] Retorna 200 OK
- [ ] Respuesta incluye datos del usuario
- [ ] Email es "test@cafe.com"
- [ ] Role es "owner"
- [ ] NO incluye `hashed_password`

### Test 4: Listar Usuarios

```bash
curl -X GET "http://localhost:8000/users/" \
  -H "Authorization: Bearer TOKEN"
```

**Validaciones**:
- [ ] Retorna 200 OK
- [ ] Respuesta es un array
- [ ] Array tiene 1 usuario
- [ ] Usuario es el que acabamos de crear

### Test 5: Refresh Token

```bash
# Reemplaza REFRESH_TOKEN con el refresh_token del test 1 o 2
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "REFRESH_TOKEN"
  }'
```

**Validaciones**:
- [ ] Retorna 200 OK
- [ ] Respuesta incluye nuevo `access_token`
- [ ] Respuesta incluye nuevo `refresh_token`

---

## 🔐 Testing Multi-Tenancy

### Test 6: Crear Segundo Negocio

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Otro Negocio",
    "email": "admin@otronegocio.com",
    "password": "pass123456",
    "full_name": "Admin Otro"
  }'
```

**Validaciones**:
- [ ] Retorna 201 Created
- [ ] Nuevo negocio creado exitosamente
- [ ] Guarda el TOKEN_NEGOCIO_2

### Test 7: Verificar Aislamiento

```bash
# Con token del Negocio 1
curl -X GET "http://localhost:8000/users/" \
  -H "Authorization: Bearer TOKEN_NEGOCIO_1"
# Debería mostrar 1 usuario (test@cafe.com)

# Con token del Negocio 2
curl -X GET "http://localhost:8000/users/" \
  -H "Authorization: Bearer TOKEN_NEGOCIO_2"
# Debería mostrar 1 usuario (admin@otronegocio.com)
```

**Validaciones**:
- [ ] Cada negocio solo ve sus propios usuarios
- [ ] NO hay cruce de datos entre negocios
- [ ] Multi-tenancy funciona correctamente

---

## 🗄️ Validación de Base de Datos

### Conectar con PgAdmin

1. Abre PgAdmin
2. Conecta a `localhost:5432`
3. Database: `multi_tenant`
4. User: `postgres`
5. Password: `postgres`

### Verificar Tablas

- [ ] Tabla `business` existe
- [ ] Tabla `users` existe
- [ ] Tabla `audit_logs` existe
- [ ] Tabla `alembic_version` existe (migraciones)

### Verificar Datos

```sql
-- Ver negocios creados
SELECT * FROM business;
-- Debería mostrar al menos 2 negocios (de los tests)

-- Ver usuarios
SELECT u.*, b.name as business_name
FROM users u
JOIN business b ON u.business_id = b.id;
-- Debería mostrar al menos 2 usuarios

-- Ver auditoría
SELECT * FROM audit_logs
ORDER BY timestamp DESC;
-- Debería mostrar registros de registro y login
```

**Validaciones**:
- [ ] Al menos 2 negocios en BD
- [ ] Al menos 2 usuarios en BD
- [ ] Registros de auditoría existen
- [ ] Foreign keys funcionan correctamente

---

## 🔧 Validación de Seguridad

### Test de Autenticación

```bash
# Intentar acceder sin token
curl -X GET "http://localhost:8000/users/me"
# Debería retornar 403 Forbidden
```

**Validaciones**:
- [ ] Sin token → 403 Forbidden
- [ ] Con token inválido → 401 Unauthorized
- [ ] Con token válido → 200 OK

### Test de Passwords

```bash
# Login con contraseña incorrecta
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@cafe.com",
    "password": "wrongpassword"
  }'
# Debería retornar 401 Unauthorized
```

**Validaciones**:
- [ ] Contraseña incorrecta → 401 Unauthorized
- [ ] Las contraseñas están hasheadas en BD (bcrypt)

---

## 📊 Validación de Logs

### Logs del Backend

```bash
docker-compose logs backend | tail -20
```

**Verificar**:
- [ ] No hay errores (ERROR)
- [ ] Hay logs de INFO
- [ ] Se registran las peticiones HTTP

### Logs de PostgreSQL

```bash
docker-compose logs db | tail -20
```

**Verificar**:
- [ ] BD inició correctamente
- [ ] No hay errores de conexión
- [ ] Conexiones del backend funcionan

---

## ✅ Checklist Final

### Funcionalidad

- [ ] ✅ Registro de negocios funciona
- [ ] ✅ Login funciona
- [ ] ✅ Refresh token funciona
- [ ] ✅ Obtener perfil funciona
- [ ] ✅ Listar usuarios funciona
- [ ] ✅ Multi-tenancy funciona (aislamiento de datos)

### Seguridad

- [ ] ✅ Contraseñas hasheadas
- [ ] ✅ JWT válido y seguro
- [ ] ✅ Endpoints protegidos requieren autenticación
- [ ] ✅ No hay fugas de datos entre negocios

### Base de Datos

- [ ] ✅ PostgreSQL funciona
- [ ] ✅ Migraciones ejecutadas
- [ ] ✅ Tablas creadas
- [ ] ✅ Índices creados
- [ ] ✅ Foreign keys funcionan

### Documentación

- [ ] ✅ Swagger UI funcional
- [ ] ✅ README completo
- [ ] ✅ Documentación técnica disponible

### Docker

- [ ] ✅ Backend containerizado
- [ ] ✅ PostgreSQL containerizado
- [ ] ✅ docker-compose funciona
- [ ] ✅ Volúmenes persistentes

---

## 🎉 Resultado Final

Si todos los checks están marcados:

**✅ FASE 1 COMPLETA Y VALIDADA**

El sistema está:
- ✅ Funcional
- ✅ Seguro
- ✅ Documentado
- ✅ Listo para desarrollo
- ✅ Listo para FASE 2

---

## 🚨 ¿Algo falló?

### Troubleshooting Rápido

**Backend no inicia**:
```bash
docker-compose logs backend
# Busca el error
# Solución común: puerto 8000 ocupado
```

**PostgreSQL no inicia**:
```bash
docker-compose logs db
# Solución común: puerto 5432 ocupado
```

**Limpia y reinicia**:
```bash
docker-compose down -v
docker-compose up --build
```

**Revisa la documentación**: [docs/INICIO_RAPIDO.md](INICIO_RAPIDO.md)
