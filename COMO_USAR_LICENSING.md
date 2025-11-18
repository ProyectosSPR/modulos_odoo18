# 🚀 Cómo Usar el Sistema de Licensing Automático

## ✅ Cambios Implementados

He modificado **saas_management** para que automáticamente vincule el **Subscription Package** a las instancias creadas.

### Archivos Modificados:
1. `/home/sergio/modulos_odoo18/saas_management/models/product_template.py`
   - ✅ Nuevo campo: `subscription_package_id`

2. `/home/sergio/modulos_odoo18/saas_management/models/sale_order.py`
   - ✅ Vincula subscription automáticamente al crear instancia
   - ✅ Mensaje mejorado en chatter con detalles del plan

3. `/home/sergio/modulos_odoo18/saas_management/views/product_template_views.xml`
   - ✅ Campo visible en formulario de producto

---

## 📋 Guía Paso a Paso

### Paso 1: Actualizar el Módulo saas_management

```
Aplicaciones → Quitar filtro "Apps" → Buscar: saas_management
→ Click en (...) → Actualizar
```

O reiniciar Odoo:
```bash
sudo systemctl restart odoo
```

---

### Paso 2: Crear Subscription Packages (Si no existen)

```
Ir a: Suscripciones → Configuración → Subscription Packages
```

**Ejemplo - Plan Básico:**
```yaml
Nombre: Plan Básico - SaaS
Descripción: Plan starter para pequeñas empresas

Tab "License Limits":
  Max Users: 5
  Max Companies: 1
  Max Storage (GB): 10

  Price per Additional User: 50.00
  Price per Additional Company: 200.00
  Price per Additional GB: 10.00

→ Guardar
```

**Ejemplo - Plan Pro:**
```yaml
Nombre: Plan Pro - SaaS
Descripción: Plan profesional para empresas en crecimiento

Tab "License Limits":
  Max Users: 20
  Max Companies: 5
  Max Storage (GB): 50

  Price per Additional User: 40.00
  Price per Additional Company: 150.00
  Price per Additional GB: 8.00

→ Guardar
```

**Ejemplo - Plan Enterprise:**
```yaml
Nombre: Plan Enterprise - SaaS
Descripción: Plan empresarial para grandes organizaciones

Tab "License Limits":
  Max Users: 100
  Max Companies: 20
  Max Storage (GB): 500

  Price per Additional User: 30.00
  Price per Additional Company: 100.00
  Price per Additional GB: 5.00

→ Guardar
```

---

### Paso 3: Crear Productos SaaS con Planes

```
Ir a: Ventas → Productos → Productos → Crear
```

**Producto 1: Odoo SaaS - Plan Básico**
```yaml
Información General:
  Nombre: Odoo SaaS - Plan Básico
  Puede ser vendido: ✓
  Precio: 500.00
  Descripción de Venta:
    """
    Plan Básico incluye:
    • Hasta 5 usuarios
    • 1 empresa
    • 10 GB almacenamiento
    • Período de prueba: 14 días

    Costos adicionales:
    • Usuarios extra: $50/usuario/mes
    • Empresas extra: $200/empresa/mes
    • Almacenamiento extra: $10/GB/mes
    """

Tab "SaaS Configuration":
  Is SaaS Instance Product: ✓
  Auto-Create Instance: ✓
  Subscription Package: Plan Básico - SaaS ← NUEVO ✨
  Trial Days: 14

Tab "Permissions" (opcional):
  Assign Permissions: ✓
  Permission Groups: [Base / User]

→ Guardar
```

**Producto 2: Odoo SaaS - Plan Pro**
```yaml
Información General:
  Nombre: Odoo SaaS - Plan Pro
  Puede ser vendido: ✓
  Precio: 1500.00

Tab "SaaS Configuration":
  Is SaaS Instance Product: ✓
  Auto-Create Instance: ✓
  Subscription Package: Plan Pro - SaaS ← NUEVO ✨
  Trial Days: 7

Tab "Permissions":
  Assign Permissions: ✓
  Permission Groups:
    - Sales / Manager
    - Inventory / User

→ Guardar
```

**Producto 3: Odoo SaaS - Plan Enterprise**
```yaml
Información General:
  Nombre: Odoo SaaS - Plan Enterprise
  Precio: 5000.00

Tab "SaaS Configuration":
  Is SaaS Instance Product: ✓
  Auto-Create Instance: ✓
  Subscription Package: Plan Enterprise - SaaS ← NUEVO ✨
  Trial Days: 0 (sin trial, directo a activo)

Tab "Permissions":
  Assign Permissions: ✓
  Permission Groups:
    - Sales / Administrator
    - Inventory / Manager
    - Purchase / Manager

→ Guardar
```

---

### Paso 4: Realizar Venta de Prueba

```
Ir a: Ventas → Órdenes → Presupuestos → Crear
```

```yaml
Cliente: [Seleccionar o crear cliente]

Líneas del Pedido:
  Producto: Odoo SaaS - Plan Básico
  Cantidad: 1

→ Guardar
→ Click en "Confirmar"
```

---

### Paso 5: Verificar Creación Automática ✅

**A. Revisar Chatter de la orden:**

Deberías ver algo como:

```
✅ SaaS Client created: [Nombre del Cliente]

🖥️ SaaS Instance created: [Nombre] (https://cliente.odoo.cloud)
📋 Subscription Plan: Plan Básico - SaaS
   • Max Users: 5
   • Max Companies: 1
   • Max Storage: 10 GB

✅ Permissions assigned to user: [Usuario]
   - Base / User
```

**B. Verificar en SaaS Management:**

```
SaaS Management → Instances → [Abrir la instancia creada]
```

Deberías ver:
- ✅ **Subscription:** Plan Básico - SaaS (ya vinculado automáticamente)
- ✅ **Estado:** Trial
- ✅ **Trial End Date:** [14 días en el futuro]

**C. Verificar pestaña Licensing (si tienes saas_licensing instalado):**

```
[En la instancia] → Tab "Licensing"
```

- Al inicio estará vacía
- El cron job creará el primer record al siguiente día

---

### Paso 6: Simular Uso y Verificar Overages

**A. Actualizar métricas de uso:**

```
[Abrir la instancia] → Editar

Current Users: 8 (excede límite de 5)
Company Count: 1 (dentro de límite)
Storage Used (GB): 12 (excede límite de 10)

→ Guardar
```

**B. Crear snapshot manual:**

```
[En la instancia] → Tab "Licensing"
→ Click en botón "Snapshot" (en button box)
```

Se abre formulario de license record con:
```
User Count: 8 (copiado de instancia)
Company Count: 1
Storage (GB): 12

→ Guardar
```

**C. Verificar detección de overages:**

El formulario debe mostrar:
```
⚠️ Overage Detected!
This instance has usage beyond the plan limits.
Total overage amount: $270.00

Overage Quantities:
  User Overage: 3 (8 - 5)
  Company Overage: 0 (1 - 1)
  Storage Overage: 2 (12 - 10)

Billing:
  Overage Amount: $270.00

Cálculo:
  3 usuarios × $50 = $150
  0 empresas × $200 = $0
  2 GB × $10 = $20
  TOTAL = $170 ✅
```

**D. Generar factura:**

```
[En el license record] → Click en "Create Invoice"
```

Se abre factura con líneas:
```
Additional Users - [Instance Name]
  Qty: 3 | Unit Price: $50 | Total: $150

Additional Storage (GB) - [Instance Name]
  Qty: 2 | Unit Price: $10 | Total: $20

TOTAL FACTURA: $170
```

---

## 🔄 Flujo Completo Automático

```
1. CONFIGURACIÓN (Una sola vez)
   ├─ Crear Subscription Packages
   └─ Crear Productos SaaS con paquetes asignados

2. VENTA
   ├─ Crear orden con producto SaaS
   └─ Confirmar orden

3. CREACIÓN AUTOMÁTICA ✨
   ├─ Cliente SaaS creado/encontrado
   ├─ Instancia creada con subdomain único
   ├─ Subscription vinculada automáticamente ← NUEVO
   ├─ Permisos asignados
   └─ Todo registrado en chatter

4. TRACKING AUTOMÁTICO
   ├─ Cron diario crea license records
   ├─ Métricas copiadas de instancia
   └─ Overages detectados automáticamente

5. FACTURACIÓN
   ├─ Admin revisa license records
   ├─ Filtra por "Billable"
   ├─ Click "Create Invoice"
   └─ Factura generada automáticamente
```

---

## 📊 Comparativa: Antes vs Ahora

| Paso | Antes | Ahora |
|------|-------|-------|
| **Crear instancia** | ✅ Automático | ✅ Automático |
| **Vincular subscription** | ❌ Manual | ✅ Automático ✨ |
| **Crear license records** | ✅ Automático (cron) | ✅ Automático (cron) |
| **Detectar overages** | ✅ Automático | ✅ Automático |
| **Generar factura** | ❌ Manual | ❌ Manual* |

*La facturación sigue siendo manual para dar control al admin sobre cuándo cobrar.

---

## 🎯 Casos de Uso

### Caso 1: Venta Simple

```
Cliente compra: Odoo SaaS - Plan Básico
→ Instancia creada con Plan Básico
→ Límites: 5 users, 1 company, 10 GB
→ Tracking automático
```

### Caso 2: Cliente con Múltiples Instancias

```
Cliente compra:
  - Odoo SaaS - Plan Pro (Producción)
  - Odoo SaaS - Plan Básico (Testing)

→ 2 instancias creadas
→ Cada una con su plan correspondiente
→ Tracking independiente
```

### Caso 3: Upgrade de Plan (Futuro)

```
Cliente tiene: Instancia con Plan Básico
Cliente compra: Upgrade a Plan Pro

→ Se actualiza subscription de la instancia
→ Nuevos límites aplican
→ Próximo license record usa nuevos límites
```

---

## ⚡ Ventajas del Sistema Automático

1. **Menos errores:** No se olvida vincular subscription
2. **Más rápido:** Sin pasos manuales
3. **Transparente:** Todo visible en chatter
4. **Escalable:** Funciona para 1 o 1000 ventas
5. **Auditable:** Historial completo de cambios

---

## 🔍 Troubleshooting

### Problema: "No aparece el campo Subscription Package"

**Solución:** Actualizar el módulo saas_management
```
Aplicaciones → saas_management → Actualizar
```

### Problema: "La instancia se creó sin subscription"

**Verificar:**
1. ¿El producto tiene "Subscription Package" seleccionado?
2. ¿El módulo está actualizado?
3. Revisar logs de Odoo

### Problema: "No se detectan overages"

**Verificar:**
1. ¿La instancia tiene subscription vinculada?
2. ¿El subscription tiene límites configurados?
3. ¿El uso actual excede los límites?
4. ¿El license record se creó correctamente?

---

## 📝 Notas Finales

### Cron Jobs Activos

El sistema tiene 2 cron jobs (si tienes saas_licensing instalado):

1. **SaaS: Create Monthly License Records**
   - Frecuencia: Diaria
   - Función: Crea snapshots de uso para todas las instancias activas

2. **SaaS: Update Instance Metrics** (opcional, si lo implementas)
   - Frecuencia: Cada hora
   - Función: Actualiza métricas desde instancias reales

### Próximas Mejoras (Opcionales)

1. **Facturación automática:** Generar facturas automáticamente al final del mes
2. **Notificaciones:** Alertar al cliente cuando se acerca a los límites
3. **Dashboard:** Vista unificada de todos los overages
4. **Webhooks:** Notificar a sistemas externos
5. **API:** Actualizar métricas desde instancias reales

---

## 🎉 ¡Listo para Usar!

El sistema ahora es completamente automático para la vinculación de subscriptions.

**Orden de actualización:**
```bash
1. Actualizar saas_management
2. Crear subscription packages
3. Configurar productos con packages
4. ¡Vender!
```

**Documentación completa:**
- `GUIA_LICENSING.md` - Explicación detallada
- `COMO_USAR_LICENSING.md` - Este archivo (guía práctica)
- `GUIA_PRUEBAS.md` - Pruebas paso a paso

---

**Última actualización:** 2025-11-18
**Versión:** 18.0.1.0.2
