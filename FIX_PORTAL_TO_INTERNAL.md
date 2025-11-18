# 🔧 Fix: Conversión Automática Portal → Internal

## 🐛 Problema Original

**Error:**
```
ValidationError: El usuario no puede tener más de un tipo de usuario.
```

**Causa:**
Cuando se intentaba asignar grupos de **usuario interno** (como Sales/Manager, Inventory/User, etc.) a un usuario de tipo **Portal**, Odoo lanzaba un error porque un usuario solo puede tener un tipo a la vez:
- Portal (base.group_portal)
- Interno (base.group_user)
- Público (base.group_public)

---

## ✅ Solución Implementada

Se modificó el archivo `/home/sergio/modulos_odoo18/product_permissions/models/sale_order.py` en el método `_apply_groups_to_user()`.

### Funcionalidad Nueva

El módulo ahora **detecta automáticamente** si necesita convertir el usuario y lo hace sin intervención manual:

```python
def _apply_groups_to_user(self, user, groups_to_assign):
    # 1. Detectar tipo actual del usuario
    is_portal = portal_group in existing_groups
    is_public = public_group in existing_groups

    # 2. Verificar si los grupos a asignar requieren acceso interno
    needs_internal = [verificación de grupos]

    # 3. Si es Portal pero necesita acceso interno → CONVERTIR
    if (is_portal or is_public) and needs_internal:
        # Remover grupos de portal/public
        existing_groups = existing_groups - portal_group - public_group

        # Agregar grupo de usuario interno
        groups_to_assign = groups_to_assign | internal_group

        # Registrar en chatter
        self.message_post(
            body='ℹ️ User XXX converted from Portal to Internal User...'
        )

    # 4. Aplicar todos los grupos (aditivo)
    all_groups = existing_groups | groups_to_assign
    user.sudo().write({'groups_id': [(6, 0, all_groups.ids)]})
```

---

## 🎯 Casos de Uso

### Caso 1: Usuario Portal recibe grupos internos

**Antes del fix:**
```
Usuario: tipo Portal
Grupos a asignar: Sales/Manager
Resultado: ❌ ERROR - ValidationError
```

**Después del fix:**
```
Usuario: tipo Portal
Grupos a asignar: Sales/Manager
Resultado: ✅ Usuario convertido a Internal + Sales/Manager asignado
Mensaje: "ℹ️ User XXX converted from Portal/Public to Internal User..."
```

---

### Caso 2: Usuario Portal recibe grupos de portal

**Antes y después (sin cambios):**
```
Usuario: tipo Portal
Grupos a asignar: Portal - Custom Group
Resultado: ✅ Se asigna normalmente (sin conversión)
```

---

### Caso 3: Usuario Interno recibe más grupos internos

**Antes y después (sin cambios):**
```
Usuario: tipo Internal
Grupos a asignar: Sales/Manager, Inventory/User
Resultado: ✅ Se asignan normalmente (aditivo)
```

---

## 📋 Algoritmo de Detección

El sistema verifica si un grupo requiere acceso interno mediante:

1. **Verificación directa:**
   - ¿El grupo ES `base.group_user`? → Requiere internal

2. **Verificación de grupos implicados:**
   - ¿El grupo implica `base.group_user`? → Requiere internal

3. **Verificación por categoría:**
   - ¿El grupo NO está en categoría "Portal"? → Probablemente requiere internal

---

## 🔄 Actualizar el Módulo

Para aplicar los cambios:

### Opción 1: Desde Odoo (Recomendado)

```
1. Ir a: Aplicaciones
2. Quitar filtro "Apps"
3. Buscar: product_permissions
4. Click en (...) → Actualizar
```

### Opción 2: Línea de Comandos

```bash
# Detener Odoo
sudo systemctl stop odoo

# Actualizar módulo
odoo-bin -d odoo18 -u product_permissions --stop-after-init

# Reiniciar Odoo
sudo systemctl start odoo
```

### Opción 3: Reinicio Simple

```bash
sudo systemctl restart odoo
```

---

## ✅ Verificar que Funciona

### Prueba 1: Crear producto con grupos internos

```yaml
Producto: Acceso Completo
  Permissions Tab:
    Assign Permissions: ✓
    Permission Groups:
      - Sales / Manager
      - Inventory / User
```

### Prueba 2: Crear usuario Portal

```yaml
Usuario: Test User
Email: test@example.com
Tipo: Portal ← IMPORTANTE
```

### Prueba 3: Realizar venta

```yaml
Orden de Venta:
  Cliente: [Partner del usuario Portal]
  Producto: Acceso Completo

→ Confirmar Orden
```

### Prueba 4: Verificar resultado

**Ir al Chatter de la orden:**
```
✅ Debe aparecer:
"ℹ️ User Test User converted from Portal/Public to Internal User to receive internal permissions"

✅ Permissions assigned to user: Test User
   - Sales / Manager
   - Inventory / User
```

**Ir a Ajustes → Usuarios → Test User:**
```
✅ Tipo de Acceso: Internal User (cambió de Portal)
✅ Grupos: Sales / Manager, Inventory / User
```

---

## 🛡️ Protecciones Implementadas

### 1. Administradores Protegidos
```python
if user.has_group('base.group_system'):
    # NO modificar permisos de administradores
    return
```

### 2. Conversión Inteligente
- Solo convierte cuando es **necesario**
- Preserva grupos existentes (aditivo)
- Registra todas las conversiones

### 3. Sin Conflictos de Tipo
- Remueve grupos conflictivos (Portal/Public)
- Agrega grupo interno automáticamente
- Evita el ValidationError

---

## 📊 Comparativa

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Portal + grupos internos** | ❌ Error | ✅ Conversión automática |
| **Portal + grupos portal** | ✅ Funciona | ✅ Funciona |
| **Internal + grupos internos** | ✅ Funciona | ✅ Funciona |
| **Administradores** | ✅ Protegidos | ✅ Protegidos |
| **Tracking** | ⚠️ Básico | ✅ Completo con mensajes |

---

## 🚨 Casos Edge

### ¿Qué pasa si el usuario YA es Internal?
→ No se convierte, solo se agregan los grupos (aditivo)

### ¿Qué pasa si asigno SOLO grupos de portal?
→ No se convierte, el usuario permanece Portal

### ¿Qué pasa si el partner no tiene usuario?
→ Se crea automáticamente como Internal (si los grupos lo requieren)

### ¿Qué pasa con usuarios públicos?
→ Mismo comportamiento: se convierten a Internal si es necesario

---

## 📝 Notas Adicionales

### Licencias Odoo
- **Usuario Portal:** Gratis (sin límite)
- **Usuario Interno:** Requiere licencia Odoo

**Implicación:** Al convertir Portal → Internal, el usuario ahora cuenta contra la cuota de licencias.

### Reversión Manual
Si necesitas revertir un usuario de Internal a Portal:

```
1. Ir a: Ajustes → Usuarios
2. Abrir usuario
3. Cambiar "Tipo de Acceso" a "Portal"
4. Remover grupos internos manualmente
```

---

## 🎉 Resumen

**Problema:** Error al asignar grupos internos a usuarios Portal

**Solución:** Conversión automática Portal → Internal cuando sea necesario

**Beneficio:**
- ✅ Sin errores
- ✅ Sin intervención manual
- ✅ Tracking completo
- ✅ Proceso transparente

---

**Archivo modificado:** `/home/sergio/modulos_odoo18/product_permissions/models/sale_order.py`
**Método actualizado:** `_apply_groups_to_user()`
**Versión:** 18.0.1.0.1
**Fecha:** 2025-11-18
