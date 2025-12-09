# Modelo Entidad-Relación - FASE 1

## 🗄️ Diagrama ER (Descripción Textual)

```
┌─────────────────┐
│    BUSINESS     │
├─────────────────┤
│ PK id           │
│    name         │
│    created_at   │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────▼─────────────┐        ┌──────────────────┐
    │      USERS       │────────│   AUDIT_LOGS     │
    ├──────────────────┤   1:N  ├──────────────────┤
    │ PK id            │        │ PK id            │
    │ FK business_id   │        │ FK business_id   │
    │    email         │        │ FK user_id       │
    │    full_name     │        │    action        │
    │    hashed_pass   │        │    timestamp     │
    │    role          │        └──────────────────┘
    │    is_active     │
    │    created_at    │
    └──────────────────┘
```

---

## 📋 Tablas Detalladas

### 1. BUSINESS (Negocios)

**Descripción**: Almacena información de cada negocio registrado en el sistema.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | SERIAL | PRIMARY KEY | Identificador único del negocio |
| name | VARCHAR(255) | NOT NULL | Nombre del negocio |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de creación |

**Índices**:
- PRIMARY KEY en `id` (automático)
- INDEX en `created_at` (para reportes)

**Restricciones**:
- `name` no puede ser vacío

---

### 2. USERS (Usuarios)

**Descripción**: Usuarios del sistema, cada uno asociado a un negocio.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | SERIAL | PRIMARY KEY | Identificador único del usuario |
| business_id | INTEGER | NOT NULL, FOREIGN KEY | Referencia al negocio |
| email | VARCHAR(255) | NOT NULL | Email del usuario |
| full_name | VARCHAR(255) | NOT NULL | Nombre completo |
| hashed_password | VARCHAR(255) | NOT NULL | Contraseña hasheada |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'cashier' | Rol del usuario |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Usuario activo/inactivo |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de creación |

**Índices**:
- PRIMARY KEY en `id` (automático)
- UNIQUE INDEX en `(business_id, email)` - Email único por negocio
- INDEX en `business_id` (para filtros multi-tenant)
- INDEX en `role` (para consultas por rol)

**Foreign Keys**:
- `business_id` REFERENCES `business(id)` ON DELETE CASCADE

**Restricciones**:
- `role` debe ser uno de: 'owner', 'admin', 'cashier', 'waiter', 'cook'
- `email` debe tener formato válido (validado en aplicación)

**Valores por defecto**:
- `role`: 'cashier'
- `is_active`: TRUE

---

### 3. AUDIT_LOGS (Registros de Auditoría)

**Descripción**: Registro de acciones críticas realizadas en el sistema.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | SERIAL | PRIMARY KEY | Identificador único del log |
| business_id | INTEGER | NOT NULL, FOREIGN KEY | Referencia al negocio |
| user_id | INTEGER | NULLABLE, FOREIGN KEY | Usuario que realizó la acción |
| action | TEXT | NOT NULL | Descripción de la acción |
| timestamp | TIMESTAMP | NOT NULL, DEFAULT NOW() | Momento de la acción |

**Índices**:
- PRIMARY KEY en `id` (automático)
- INDEX en `business_id` (para filtros multi-tenant)
- INDEX en `user_id` (para consultas por usuario)
- INDEX en `timestamp` (para ordenar por fecha)
- COMPOSITE INDEX en `(business_id, timestamp)` (consultas frecuentes)

**Foreign Keys**:
- `business_id` REFERENCES `business(id)` ON DELETE CASCADE
- `user_id` REFERENCES `users(id)` ON DELETE SET NULL

**Notas**:
- `user_id` es NULL para acciones del sistema
- `action` almacena descripción legible (ej: "Usuario registrado", "Login exitoso")

---

## 🔐 Políticas Multi-Tenant

### Regla de Oro
**TODOS los queries deben filtrar por `business_id`**

### Ejemplos de Queries Seguros

```sql
-- ✅ CORRECTO: Lista usuarios del negocio 3
SELECT * FROM users WHERE business_id = 3;

-- ✅ CORRECTO: Obtener usuario específico del negocio
SELECT * FROM users
WHERE id = 42 AND business_id = 3;

-- ❌ INCORRECTO: Sin filtro de business_id
SELECT * FROM users WHERE id = 42;

-- ✅ CORRECTO: Auditoría del negocio
SELECT * FROM audit_logs
WHERE business_id = 3
ORDER BY timestamp DESC;
```

---

## 🔒 Seguridad de Datos

### Cascade Deletes

Si se elimina un negocio:
- Se eliminan todos sus usuarios
- Se eliminan todos sus audit_logs

Definición:
```sql
FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE CASCADE
```

### Soft Deletes (usuarios)

Los usuarios tienen `is_active`:
- `TRUE`: Usuario activo
- `FALSE`: Usuario desactivado (no eliminado)

Esto permite auditoría histórica.

---

## 📊 Índices Recomendados

### Por Tabla

**business**:
```sql
CREATE INDEX idx_business_created_at ON business(created_at);
```

**users**:
```sql
CREATE UNIQUE INDEX idx_users_business_email ON users(business_id, email);
CREATE INDEX idx_users_business_id ON users(business_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);
```

**audit_logs**:
```sql
CREATE INDEX idx_audit_business_id ON audit_logs(business_id);
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_business_timestamp ON audit_logs(business_id, timestamp);
```

---

## 🔄 Relaciones

### business → users (1:N)
- Un negocio tiene muchos usuarios
- Un usuario pertenece a un solo negocio

### business → audit_logs (1:N)
- Un negocio tiene muchos registros de auditoría
- Un log pertenece a un solo negocio

### users → audit_logs (1:N)
- Un usuario puede tener muchos registros de auditoría
- Un log puede tener un usuario (o NULL para acciones del sistema)

---

## 📈 Escalabilidad

### Particionamiento Futuro

Para escalar a millones de registros, considerar:

1. **Particionamiento por business_id**:
   - Particionar tablas grandes por rangos de business_id
   - Permite distribuir datos en múltiples servidores

2. **Particionamiento temporal en audit_logs**:
   - Particionar por timestamp (mensual o anual)
   - Archivar logs antiguos

3. **Sharding**:
   - Separar negocios en diferentes bases de datos
   - Útil cuando se superen 10,000+ negocios activos

---

## 🧪 Datos de Prueba

### Script de Inicialización

```sql
-- Insertar negocio de prueba
INSERT INTO business (name) VALUES ('Cafetería Demo');

-- Insertar usuario owner
INSERT INTO users (business_id, email, full_name, hashed_password, role)
VALUES (1, 'admin@cafeteriademo.com', 'Juan Pérez', '$2b$12$...', 'owner');

-- Insertar log de auditoría
INSERT INTO audit_logs (business_id, user_id, action)
VALUES (1, 1, 'Usuario owner creado');
```

---

## 📝 Notas de Implementación

1. **SQLAlchemy Models**: Cada tabla se mapea a un modelo SQLAlchemy
2. **Migrations**: Alembic gestiona cambios en el esquema
3. **Validaciones**: Pydantic valida datos antes de insertar
4. **Transactions**: Operaciones críticas usan transacciones
5. **Connection Pooling**: SQLAlchemy maneja pool de conexiones

---

## ✅ Checklist de Implementación

- [ ] Crear modelos SQLAlchemy
- [ ] Configurar foreign keys y cascades
- [ ] Crear índices mencionados
- [ ] Migración inicial con Alembic
- [ ] Validar constraints en BD
- [ ] Poblar datos de prueba
- [ ] Verificar queries multi-tenant
