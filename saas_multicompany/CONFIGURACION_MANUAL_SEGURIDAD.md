# Configuración Manual de Seguridad Multi-Empresa

## 🎯 Objetivo

Configurar manualmente las reglas de seguridad para que:
- **Usuarios regulares**: Solo ven su empresa
- **Administradores**: Ven TODO
- **Productos**: Usuarios ven su empresa + empresa padre (para tienda)

---

## 📋 PASO 1: Activar Modo Desarrollador

1. Ve a: **Ajustes**
2. Scroll hasta abajo
3. Haz clic en **"Activar el modo de desarrollador"**

---

## 📋 PASO 2: Eliminar Reglas Existentes (IMPORTANTE)

1. Ve a: **Ajustes → Técnico → Seguridad → Reglas de Registro**
2. Busca todas las reglas que contengan:
   - "multicompany"
   - "Own Company"
   - "Parent Company"
3. **ELIMÍNALAS TODAS** o desmarca "Activo"

---

## 📋 PASO 3: Crear Regla de Admin para Partners

1. Ve a: **Ajustes → Técnico → Seguridad → Reglas de Registro**
2. Haz clic en **Crear**
3. Configura:

```
Nombre: Partner: Admin Full Access
Modelo: Contacto (res.partner)
Dominio: [(1, '=', 1)]
Grupos:
  - Administration / Settings (base.group_system)
  - SaaS Management / Manager (si existe)

Permisos:
✅ Lectura
✅ Escritura
✅ Creación
✅ Eliminación
```

4. **Guardar**

---

## 📋 PASO 4: Crear Regla de Usuario Regular para Partners

1. **Crear** nueva regla
2. Configura:

```
Nombre: Partner: Own Company Only
Modelo: Contacto (res.partner)
Dominio: ['|', ('company_id', '=', False), ('company_id', '=', user.company_id.id)]
Grupos:
  - User types / Internal User (base.group_user)

⚠️ IMPORTANTE: Marca "No Global"

Permisos:
✅ Lectura
✅ Escritura
✅ Creación
✅ Eliminación
```

3. **Guardar**

---

## 📋 PASO 5: Crear Regla de Admin para Companies

1. **Crear** nueva regla
2. Configura:

```
Nombre: Company: Admin Full Access
Modelo: Empresa (res.company)
Dominio: [(1, '=', 1)]
Grupos:
  - Administration / Settings (base.group_system)
  - SaaS Management / Manager (si existe)

Permisos:
✅ Lectura
✅ Escritura
✅ Creación
✅ Eliminación
```

3. **Guardar**

---

## 📋 PASO 6: Crear Regla de Usuario Regular para Companies

1. **Crear** nueva regla
2. Configura:

```
Nombre: Company: Own Company Only - READ
Modelo: Empresa (res.company)
Dominio: [('id', '=', user.company_id.id)]
Grupos:
  - User types / Internal User (base.group_user)

⚠️ IMPORTANTE: Marca "No Global"

Permisos:
✅ Lectura
❌ Escritura
❌ Creación
❌ Eliminación
```

3. **Guardar**

4. **Crear OTRA regla** para WRITE:

```
Nombre: Company: Own Company Only - WRITE
Modelo: Empresa (res.company)
Dominio: [('id', '=', user.company_id.id)]
Grupos:
  - User types / Internal User (base.group_user)

⚠️ IMPORTANTE: Marca "No Global"

Permisos:
❌ Lectura
✅ Escritura
❌ Creación
❌ Eliminación
```

5. **Guardar**

---

## 📋 PASO 7: Crear Regla de Admin para Products

1. **Crear** nueva regla
2. Configura:

```
Nombre: Product: Admin Full Access
Modelo: Plantilla de producto (product.template)
Dominio: [(1, '=', 1)]
Grupos:
  - Administration / Settings (base.group_system)

Permisos:
✅ Lectura
✅ Escritura
✅ Creación
✅ Eliminación
```

3. **Guardar**

---

## 📋 PASO 8: Crear Regla de Usuario Regular para Products (CON EXCEPCIÓN)

### 8.1 Regla de LECTURA (incluye empresa padre)

1. **Crear** nueva regla
2. Configura:

```
Nombre: Product: Own and Parent Company - READ
Modelo: Plantilla de producto (product.template)
Dominio: ['|', ('company_id', '=', False), '|', ('company_id', '=', user.company_id.id), ('company_id', '=', user.company_id.parent_company_id.id)]
Grupos:
  - User types / Internal User (base.group_user)

⚠️ IMPORTANTE: Marca "No Global"

Permisos:
✅ Lectura
❌ Escritura
❌ Creación
❌ Eliminación
```

3. **Guardar**

### 8.2 Regla de ESCRITURA (solo su empresa)

1. **Crear** nueva regla
2. Configura:

```
Nombre: Product: Own Company Only - WRITE
Modelo: Plantilla de producto (product.template)
Dominio: ['|', ('company_id', '=', False), ('company_id', '=', user.company_id.id)]
Grupos:
  - User types / Internal User (base.group_user)

⚠️ IMPORTANTE: Marca "No Global"

Permisos:
❌ Lectura
✅ Escritura
✅ Creación
✅ Eliminación
```

3. **Guardar**

---

## ✅ VERIFICACIÓN

### Como Administrador:
1. Ve a: **Contactos**
2. Deberías ver contactos de **TODAS** las empresas
3. Debes poder editarlos

### Como Usuario Regular:
1. Ve a: **Contactos**
2. Solo deberías ver contactos de **TU** empresa
3. Ve a: **Productos**
4. Deberías ver productos de **TU empresa** + **Empresa Padre** (si está configurado)

---

## 🔧 Solución de Problemas

### Problema: El admin no ve nada

**Solución:**
1. Ve a: **Ajustes → Técnico → Seguridad → Reglas de Registro**
2. Busca las reglas con "No Global" marcado
3. Verifica que NO incluyan al grupo "Administration / Settings"
4. Las reglas de admin deben estar en reglas SEPARADAS SIN "No Global"

### Problema: El usuario ve empresas que no debería

**Solución:**
1. Verifica el dominio de la regla
2. Debe ser: `[('company_id', '=', user.company_id.id)]`
3. NO: `[('company_id', 'in', user.company_ids.ids)]`

### Problema: No se aplican los cambios

**Solución:**
1. Cierra sesión
2. Limpia caché del navegador (Ctrl + Shift + Delete)
3. Vuelve a iniciar sesión

---

## 📝 Notas Importantes

1. **"No Global"** es CRÍTICO para que los administradores no se vean afectados
2. Las reglas de admin NUNCA deben tener "No Global" marcado
3. Separa siempre READ de WRITE en reglas diferentes cuando necesites permisos distintos
4. El dominio debe usar comillas simples: `'|'` no `"|"`

---

## 🆘 ¿Necesitas Ayuda?

Si algo no funciona:
1. Toma captura de pantalla de la regla problemática
2. Verifica que el campo "No Global" esté configurado correctamente
3. Revisa que los grupos sean los correctos
