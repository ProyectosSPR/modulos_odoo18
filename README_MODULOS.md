# 📦 Módulos SaaS - Documentación Completa

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Módulos](#módulos)
4. [Instalación](#instalación)
5. [Configuración](#configuración)
6. [Casos de Uso](#casos-de-uso)
7. [API y Extensiones](#api-y-extensiones)

---

## Visión General

Suite completa de módulos para vender y gestionar productos SaaS en Odoo 18.

### Módulos Incluidos

| Módulo | Propósito | Estado |
|--------|-----------|--------|
| **product_permissions** | Asignación automática de permisos | ✅ Producción |
| **saas_management** | Gestión de clientes e instancias SaaS | ✅ Producción |
| **saas_licensing** | Facturación por uso (usuarios/empresas) | ✅ Producción |

### Dependencias

```
subscription_package (Cybrosys)
    ↓
product_permissions
    ↓
saas_management
    ↓
saas_licensing (opcional)
```

---

## Arquitectura

### Flujo de Datos

```
Orden de Venta (confirmada)
    ↓
    ├─→ product_permissions
    │       └─→ Asigna grupos al usuario
    │
    ├─→ saas_management
    │       ├─→ Crea/encuentra cliente SaaS
    │       └─→ Crea instancia con subdomain único
    │
    └─→ saas_licensing
            ├─→ Registra uso (usuarios/empresas/storage)
            ├─→ Detecta excesos vs límites
            └─→ Genera facturas por overages
```

### Modelos de Datos

```
res.partner (Odoo core)
    ↓ (1:1)
res.users (Odoo core)
    ↓ (N:1)
saas.client (SaaS Management)
    ↓ (1:N)
saas.instance (SaaS Management)
    ↓ (1:N)
saas.license (SaaS Licensing)
    ↓ (N:1)
account.move (factura)
```

---

## Módulos

### 1. product_permissions

#### Propósito
Asignar automáticamente grupos de seguridad a usuarios cuando compran productos específicos.

#### Características
- ✅ Asignación aditiva (preserva grupos existentes)
- ✅ Protección de administradores (no aplica a base.group_system)
- ✅ Auto-creación de usuarios si no existen
- ✅ Tracking completo en chatter
- ✅ Múltiples grupos por producto

#### Campos Nuevos

**product.template:**
- `assign_permissions` (Boolean): Activar asignación automática
- `permission_group_ids` (Many2many): Grupos a asignar
- `permission_description` (Text): Descripción para el usuario

**sale.order:**
- Sobrescribe `action_confirm()` para asignar permisos

#### Configuración

```python
# En el producto
product.assign_permissions = True
product.permission_group_ids = [(6, 0, [group1.id, group2.id])]
```

#### Seguridad

```
Group: No específico (usa grupos base de Odoo)
Rules: Hereda de sale.order
```

---

### 2. saas_management

#### Propósito
Gestionar clientes SaaS y sus instancias Odoo dedicadas.

#### Características
- ✅ Clientes con ciclo de vida (prospect → active → suspended → churned)
- ✅ Instancias con subdominios únicos
- ✅ Estados de instancia (draft, trial, active, suspended, terminated)
- ✅ Creación automática desde ventas
- ✅ Generación de URLs automática
- ✅ Períodos de prueba configurables
- ✅ Vistas Kanban, List, Form

#### Modelos

**saas.client:**
```python
name: Char (nombre del cliente)
partner_id: Many2one(res.partner) - required
state: Selection (prospect, active, suspended, churned)
instance_ids: One2many(saas.instance)
instance_count: Integer (computed)
active_instance_count: Integer (computed)
activated_date: Date
```

**saas.instance:**
```python
name: Char (nombre de la instancia)
subdomain: Char (único) - required
full_url: Char (computed: https://{subdomain}.{base_domain})
client_id: Many2one(saas.client) - required
partner_id: Many2one(res.partner) - related
subscription_id: Many2one(subscription.package)
state: Selection (draft, trial, active, suspended, terminated)
odoo_version: Selection (16.0, 17.0, 18.0)
trial_end_date: Date
activated_date: Datetime
current_users: Integer
storage_used_gb: Float
```

#### Campos Nuevos en Modelos Existentes

**product.template:**
```python
is_saas_instance: Boolean
auto_create_instance: Boolean
trial_days: Integer (default=7)
```

**sale.order:**
```python
has_saas_products: Boolean (computed)
saas_client_id: Many2one(saas.client) (computed)
```

#### Configuración del Sistema

```python
# Parámetro del sistema
ir.config_parameter: 'saas.base_domain' = 'odoo.cloud'
```

#### Seguridad

```
Groups:
  - SaaS Manager (full access)
  - SaaS User (read only)

Rules:
  - Manager: All access
  - User: Read only
  - Sales: Read + Create instances
```

---

### 3. saas_licensing

#### Propósito
Rastrear el uso de recursos (usuarios, empresas, storage) y facturar excesos automáticamente.

#### Características
- ✅ Tracking de usuarios, empresas y almacenamiento
- ✅ Límites configurables por subscription
- ✅ Detección automática de excesos (overages)
- ✅ Cálculo de cargos por exceso
- ✅ Generación automática de facturas
- ✅ Cron job para snapshots mensuales
- ✅ Snapshots manuales bajo demanda

#### Modelos

**saas.license:**
```python
name: Char (computed)
instance_id: Many2one(saas.instance) - required
client_id: Many2one(saas.client) - related
subscription_id: Many2one(subscription.package) - related
date: Date (default=today)

# Uso actual
user_count: Integer
company_count: Integer
storage_gb: Float

# Límites del plan (related)
plan_user_limit: Integer
plan_company_limit: Integer
plan_storage_limit: Float

# Excesos (computed)
user_overage: Integer
company_overage: Integer
storage_overage: Float

# Facturación
is_billable: Boolean (computed)
overage_amount: Float (computed)
invoice_id: Many2one(account.move)
invoice_state: Selection (related)
```

#### Campos Nuevos en Modelos Existentes

**saas.instance:**
```python
license_ids: One2many(saas.license)
license_count: Integer (computed)
company_count: Integer
latest_license_id: Many2one(saas.license) (computed)
has_overages: Boolean (computed)
```

**subscription.package:**
```python
# Límites
max_users: Integer (default=10)
max_companies: Integer (default=1)
max_storage_gb: Float (default=10.0)

# Precios por exceso
price_per_user: Float (default=10.0)
price_per_company: Float (default=50.0)
price_per_gb: Float (default=5.0)
```

#### Cron Job

```xml
<record id="ir_cron_create_license_records" model="ir.cron">
    <field name="name">SaaS: Create Monthly License Records</field>
    <field name="model_id" ref="model_saas_license"/>
    <field name="code">model.create_monthly_license_records()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
</record>
```

#### Fórmulas de Cálculo

```python
# Overages
user_overage = max(0, user_count - plan_user_limit)
company_overage = max(0, company_count - plan_company_limit)
storage_overage = max(0, storage_gb - plan_storage_limit)

# Monto facturado
overage_amount = (
    (user_overage * price_per_user) +
    (company_overage * price_per_company) +
    (storage_overage * price_per_gb)
)
```

#### Seguridad

```
Groups: Hereda de saas_management
  - SaaS Manager: All access
  - SaaS User: Read only
  - Sales: Read + Write
  - Accounting: Read + Write + Invoice
```

---

## Instalación

### Requisitos Previos

```yaml
Odoo: 18.0
Python: 3.10+
Módulos base:
  - base
  - sale_management
  - account
  - subscription_package (Cybrosys)
```

### Orden de Instalación

```bash
# 1. Asegurarse que subscription_package esté instalado
# Apps → subscription_package → Install

# 2. Instalar en orden
Apps → product_permissions → Install
Apps → saas_management → Install
Apps → saas_licensing → Install (opcional)
```

### Post-Instalación

```python
# Configurar dominio base
Settings → Technical → System Parameters
Key: saas.base_domain
Value: tu-dominio.com
```

---

## Configuración

### Grupos de Seguridad

Asignar usuarios a grupos:

```
Settings → Users & Companies → Users
→ [Seleccionar usuario]
→ Add group: "SaaS Manager"
```

### Subscription Packages

```
Subscriptions → Configuration → Subscription Packages
→ Create new package
→ Tab "License Limits": Configurar límites y precios
```

### Productos

```
Sales → Products → Create

# Para permisos
Tab "Permissions":
  - Assign Permissions: ✓
  - Permission Groups: [Seleccionar grupos]

# Para SaaS
Tab "SaaS Configuration":
  - Is SaaS Instance Product: ✓
  - Auto-Create Instance: ✓
  - Trial Days: 14
```

---

## Casos de Uso

### Caso 1: Venta de Licencias con Permisos

**Objetivo:** Vender acceso a módulos específicos de Odoo

**Configuración:**
```yaml
Producto: Módulo Inventario
  assign_permissions: True
  permission_groups:
    - Stock / User
    - Inventory / User
  is_saas_instance: False
```

**Flujo:**
1. Cliente compra "Módulo Inventario"
2. Se confirma la orden
3. Usuario del cliente recibe grupos automáticamente
4. Usuario puede accesar inventario

---

### Caso 2: Instancia SaaS Básica

**Objetivo:** Proveer instancia dedicada de Odoo

**Configuración:**
```yaml
Producto: Odoo Instance
  assign_permissions: False
  is_saas_instance: True
  auto_create_instance: True
  trial_days: 30
```

**Flujo:**
1. Cliente compra "Odoo Instance"
2. Se crea cliente SaaS automáticamente
3. Se crea instancia con subdomain único
4. Instancia inicia en modo trial (30 días)
5. URL generada: https://cliente-nombre.odoo.cloud

---

### Caso 3: SaaS Enterprise con Licensing

**Objetivo:** Instancia SaaS con facturación por uso

**Configuración:**
```yaml
Producto: Odoo Enterprise SaaS
  is_saas_instance: True
  auto_create_instance: True
  trial_days: 0 (directo a active)

Subscription Package: Enterprise Plan
  max_users: 50
  max_companies: 10
  max_storage_gb: 500
  price_per_user: 50
  price_per_company: 200
  price_per_gb: 10
```

**Flujo:**
1. Cliente compra instancia
2. Se crea y activa instancia
3. Se vincula a "Enterprise Plan"
4. Cron job crea snapshots mensuales
5. Si uso > límites → Se genera factura automática

---

### Caso 4: Combo Completo

**Objetivo:** SaaS + Permisos + N8N Workflows

**Configuración:**
```yaml
Producto: Full Stack Solution
  # Permisos
  assign_permissions: True
  permission_groups:
    - Sales / Manager
    - Inventory / Manager

  # SaaS
  is_saas_instance: True
  auto_create_instance: True
  trial_days: 14

  # N8N (si tienes n8n-sales)
  n8n_workflow_template_id: "workflow123"
```

**Flujo:**
1. Venta confirmada
2. Usuario recibe permisos
3. Cliente SaaS creado
4. Instancia creada (trial 14 días)
5. Workflow N8N creado para el cliente
6. Todo registrado en chatter

---

## API y Extensiones

### Extender product_permissions

```python
# custom_module/models/sale_order.py
from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()

        # Tu lógica adicional después de asignar permisos
        for order in self:
            if order.partner_id.email:
                # Enviar email personalizado
                self.send_welcome_email()

        return res
```

### Extender saas_management

```python
# custom_module/models/saas_instance.py
from odoo import models, api

class SaasInstance(models.Model):
    _inherit = 'saas.instance'

    @api.model
    def create(self, vals):
        instance = super().create(vals)

        # Provisionar infraestructura real (Kubernetes, etc.)
        if vals.get('auto_provision'):
            instance.provision_kubernetes_pod()

        return instance

    def provision_kubernetes_pod(self):
        # Tu lógica de provisioning
        pass
```

### Extender saas_licensing

```python
# custom_module/models/saas_license.py
from odoo import models

class SaasLicense(models.Model):
    _inherit = 'saas.license'

    def action_create_invoice(self):
        """Override para añadir líneas customizadas"""
        res = super().action_create_invoice()

        if res.get('res_id'):
            invoice = self.env['account.move'].browse(res['res_id'])
            # Agregar descuentos, impuestos, etc.
            invoice.write({
                'narration': f'Factura generada automáticamente por overages - {self.name}'
            })

        return res
```

### Webhooks para Eventos

```python
# custom_module/models/saas_client.py
from odoo import models, api
import requests

class SaasClient(models.Model):
    _inherit = 'saas.client'

    @api.model
    def create(self, vals):
        client = super().create(vals)

        # Webhook: nuevo cliente creado
        requests.post('https://your-webhook.com/client-created', json={
            'client_id': client.id,
            'name': client.name,
            'email': client.email,
        })

        return client
```

---

## Mejores Prácticas

### 1. Subdominios

```python
# Usar validación de subdomain
def _validate_subdomain(self, subdomain):
    # Solo alfanuméricos y guiones
    import re
    if not re.match(r'^[a-z0-9-]+$', subdomain):
        raise ValidationError('Subdomain inválido')
    return subdomain
```

### 2. Protección de Administradores

```python
# SIEMPRE verificar antes de asignar permisos
if user.has_group('base.group_system'):
    # NO MODIFICAR permisos de admins
    return
```

### 3. Logging

```python
import logging
_logger = logging.getLogger(__name__)

# Loggear acciones importantes
_logger.info(f'SaaS Instance created: {instance.name}')
_logger.warning(f'Overage detected: {license.overage_amount}')
```

### 4. Transacciones

```python
# Usar commits manuales para operaciones largas
@api.model
def create_monthly_license_records(self):
    instances = self.env['saas.instance'].search([...])

    for instance in instances:
        try:
            # Crear license record
            self.create({...})
            self.env.cr.commit()  # Commit por cada instancia
        except Exception as e:
            _logger.error(f'Error creating license for {instance.name}: {e}')
            self.env.cr.rollback()
```

---

## Soporte y Contribuciones

**Autor:** AutomateAI
**Website:** https://automateai.com.mx
**Email:** soporte@automateai.com.mx
**Versión:** 18.0.1.0.0
**Licencia:** LGPL-3

---

## Changelog

### v18.0.1.0.0 (2025-11-17)
- ✅ Release inicial
- ✅ Compatibilidad Odoo 18
- ✅ Módulos: product_permissions, saas_management, saas_licensing
- ✅ Migración desde odoo_saas_core (deprecated)
- ✅ Arquitectura modular
- ✅ Guías de prueba completas

---

**Documentación actualizada:** 2025-11-17
