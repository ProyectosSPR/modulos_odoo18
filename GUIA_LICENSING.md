# 📊 Guía Completa: SaaS Licensing

## 🔄 Flujo Actual (Manual)

### Paso 1: Vender Instancia SaaS
```
Producto: Odoo SaaS Instance
  → is_saas_instance: ✓
  → auto_create_instance: ✓

Venta confirmada →
  ✅ Cliente SaaS creado
  ✅ Instancia creada
  ❌ Subscription NO vinculada (manual)
```

### Paso 2: Vincular Subscription Manualmente
```
SaaS Management → Instances → [Abrir instancia]
→ Campo "Subscription": [Seleccionar plan manualmente]
→ Guardar
```

### Paso 3: Tracking Automático
```
Cron job diario →
  ✅ Crea license records para todas las instancias activas
  ✅ Detecta overages automáticamente
```

### Paso 4: Facturación Manual
```
SaaS Management → Licensing → License Records
→ Filtrar "Billable" = True
→ Abrir license record
→ Click "Create Invoice"
```

---

## 🚀 Flujo Mejorado (Automático)

### Propuesta: Vincular Subscription Automáticamente

En lugar de vender solo "Instancia SaaS", vendemos **"Plan Específico"** que incluye:
- Instancia SaaS ✓
- Subscription Package ✓
- Límites predefinidos ✓

---

## 💡 Solución Implementada

Voy a modificar el código para que automáticamente:
1. **Al confirmar venta** → Vincula subscription a la instancia
2. **Productos configurables** → Cada producto puede especificar su plan
3. **Sin pasos manuales** → Todo automático

---

## 📦 Configuración de Productos

### Tipo 1: Producto SaaS con Plan Incluido

```yaml
Producto: Odoo SaaS - Plan Básico

  # SaaS Configuration
  is_saas_instance: ✓
  auto_create_instance: ✓
  trial_days: 14

  # Subscription Package (NUEVO)
  subscription_package_id: [Plan Básico]

→ Al vender:
  1. Crea instancia ✓
  2. Vincula a "Plan Básico" automáticamente ✓
  3. Comienza tracking ✓
```

### Tipo 2: Producto de Upgrade

```yaml
Producto: Upgrade a Plan Pro

  # NO crea instancia nueva
  is_saas_instance: ✗

  # Solo actualiza subscription
  is_subscription_upgrade: ✓
  subscription_package_id: [Plan Pro]

→ Al vender:
  1. Busca instancia del cliente
  2. Actualiza subscription a "Plan Pro"
  3. Límites nuevos aplican
```

### Tipo 3: Producto de Addon

```yaml
Producto: +10 Usuarios Adicionales

  is_addon: ✓
  addon_type: "users"
  addon_quantity: 10

→ Al vender:
  1. Busca instancia del cliente
  2. Aumenta límite de usuarios (+10)
  3. Actualiza subscription
```

---

## 🎯 Configuración Paso a Paso

### 1. Crear Subscription Packages

```
Suscripciones → Configuración → Subscription Packages

Plan Básico:
  Max Users: 5
  Max Companies: 1
  Max Storage: 10 GB
  Price per User: $50
  Price per Company: $200
  Price per GB: $10

Plan Pro:
  Max Users: 20
  Max Companies: 5
  Max Storage: 50 GB
  Price per User: $40
  Price per Company: $150
  Price per GB: $8

Plan Enterprise:
  Max Users: 100
  Max Companies: 20
  Max Storage: 500 GB
  Price per User: $30
  Price per Company: $100
  Price per GB: $5
```

### 2. Crear Productos con Plans

```
Ventas → Productos → Crear

Producto 1: Odoo SaaS - Plan Básico
  Precio: $500/mes

  Tab "SaaS Configuration":
    Is SaaS Instance Product: ✓
    Auto-Create Instance: ✓
    Trial Days: 14
    Subscription Package: Plan Básico ← NUEVO

  Tab "Permissions":
    Assign Permissions: ✓
    Permission Groups: [Base / User]

---

Producto 2: Odoo SaaS - Plan Pro
  Precio: $1500/mes

  Tab "SaaS Configuration":
    Is SaaS Instance Product: ✓
    Auto-Create Instance: ✓
    Trial Days: 7
    Subscription Package: Plan Pro ← NUEVO

  Tab "Permissions":
    Assign Permissions: ✓
    Permission Groups: [Sales / Manager, Inventory / User]

---

Producto 3: Upgrade: Básico → Pro
  Precio: $1000 (one-time)

  Tab "SaaS Configuration":
    Is SaaS Instance Product: ✗
    Is Subscription Upgrade: ✓
    Subscription Package: Plan Pro ← NUEVO
```

---

## 🔧 Código a Modificar

Necesito agregar campos al modelo y lógica de vinculación automática.

---

## 📝 Casos de Uso Completos

### Caso 1: Venta Nueva con Plan

```
1. Cliente compra: "Odoo SaaS - Plan Básico"

2. Al confirmar orden:
   ✅ Cliente SaaS creado
   ✅ Instancia creada (subdomain único)
   ✅ Subscription vinculada: Plan Básico
   ✅ Permisos asignados

3. Cron job diario:
   ✅ Crea license record
   ✅ User count: 3 (dentro de límite 5)
   ✅ No overages
   ✅ No factura adicional

4. Cliente crece:
   → Actualiza métricas manualmente o automático
   → User count: 7 (excede límite 5)
   → Cron detecta overage de 2 usuarios
   → Admin crea factura: 2 × $50 = $100
```

### Caso 2: Upgrade de Plan

```
1. Cliente tiene: Plan Básico (5 users)
2. Cliente compra: "Upgrade: Básico → Pro"

3. Al confirmar orden:
   ✅ Busca instancia del cliente
   ✅ Actualiza subscription: Plan Básico → Plan Pro
   ✅ Límites nuevos: 20 users, 5 companies, 50 GB
   ✅ Mensaje en chatter

4. Próximo cron:
   ✅ Usa nuevos límites
   ✅ 7 usuarios ahora están dentro del límite
   ✅ No overages
```

### Caso 3: Cliente con Múltiples Instancias

```
Cliente tiene:
  - Instancia 1: Producción (Plan Pro)
  - Instancia 2: Testing (Plan Básico)

Compra: "Odoo SaaS - Plan Enterprise"

Al confirmar:
  ✅ Crea Instancia 3: Nueva (Plan Enterprise)
  ✅ Instancias 1 y 2 mantienen sus planes
  ✅ Cliente ahora tiene 3 instancias con diferentes planes
```

---

## 🔄 Flujo Automático Completo

```
VENTA
  ↓
CONFIRMAR ORDEN
  ↓
product_permissions
  ├─→ Verificar usuario
  ├─→ Convertir Portal → Internal (si necesario)
  └─→ Asignar grupos
  ↓
saas_management
  ├─→ Crear/buscar cliente SaaS
  ├─→ Crear instancia
  ├─→ Generar subdomain único
  ├─→ VINCULAR SUBSCRIPTION (NUEVO) ✨
  └─→ Configurar trial period
  ↓
CRON DIARIO (saas_licensing)
  ├─→ Crear license record
  ├─→ Copiar métricas (users, companies, storage)
  ├─→ Comparar vs límites del plan
  └─→ Detectar overages
  ↓
ADMIN REVISA
  ├─→ Filtrar records con overages
  └─→ Click "Create Invoice"
  ↓
FACTURA AUTOMÁTICA
  ├─→ Líneas por recurso excedido
  ├─→ Cálculo automático
  └─→ Cliente recibe factura
```

---

## ⚙️ Configuración Adicional

### Automatizar Actualización de Métricas

Opcionalmente, puedes conectar con APIs reales:

```python
# En saas.instance
def update_metrics_from_remote(self):
    """Actualiza métricas desde instancia real"""
    # Conectar a API de la instancia
    # GET /api/metrics
    response = requests.get(f"{self.full_url}/api/metrics")

    if response.ok:
        data = response.json()
        self.write({
            'current_users': data['active_users'],
            'company_count': data['companies'],
            'storage_used_gb': data['storage_gb'],
        })
```

### Cron para Actualizar Métricas

```xml
<record id="ir_cron_update_metrics" model="ir.cron">
    <field name="name">SaaS: Update Instance Metrics</field>
    <field name="model_id" ref="saas_management.model_saas_instance"/>
    <field name="code">model.search([('state', '=', 'active')]).update_metrics_from_remote()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">hours</field>
    <field name="active" eval="True"/>
</record>
```

---

## 🎓 Mejores Prácticas

### 1. Nombrar Productos Claramente

```
✅ "Odoo SaaS - Plan Básico (5 users, 1 company)"
✅ "Odoo SaaS - Plan Pro (20 users, 5 companies)"
❌ "Producto SaaS 1"
❌ "Plan 2"
```

### 2. Usar Suscripciones Recurrentes

Combinar con el módulo `subscription_package` para:
- Facturación mensual automática del plan base
- Facturación adicional de overages
- Renovación automática

### 3. Comunicar Límites al Cliente

En la descripción del producto:
```
Plan Básico incluye:
- Hasta 5 usuarios
- 1 empresa
- 10 GB almacenamiento
- Período de prueba: 14 días

Usuarios adicionales: $50/usuario/mes
Empresas adicionales: $200/empresa/mes
Almacenamiento adicional: $10/GB/mes
```

---

## 📊 Dashboard Recomendado

Crear vista de resumen para admin:

```
SaaS Dashboard
├─ Total Clientes: 45
├─ Instancias Activas: 67
├─ Instancias en Trial: 12
├─ Overages Este Mes: $15,400
└─ Facturas Pendientes: 23

Por Plan:
├─ Plan Básico: 30 instancias
├─ Plan Pro: 25 instancias
└─ Plan Enterprise: 12 instancias

Top Overages:
1. Acme Corp: $2,500 (50 usuarios adicionales)
2. Tech Inc: $1,800 (30 usuarios, 2 empresas)
3. ...
```

---

**¿Implemento la vinculación automática de subscription ahora?**
