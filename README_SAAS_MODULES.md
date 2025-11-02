# Sistema de Suscripciones SaaS para Odoo 18

## 📋 Resumen Ejecutivo

Este conjunto de módulos proporciona un sistema completo y unificado para ofrecer Odoo como SaaS (Software as a Service), incluyendo gestión de clientes, instancias, suscripciones, licencias multi-empresa y integración con n8n.

### Módulos Creados

1. **odoo_saas_core** - Base del sistema SaaS (Clientes, Instancias, Paquetes de Servicio)
2. **odoo_subscription** - Gestión avanzada de suscripciones con renovaciones automáticas
3. **odoo_saas_licensing** - Sistema de licencias multi-empresa (NUEVO)
4. **odoo_n8n_sales** - Integración con n8n para vender flujos de automatización (Adaptado)

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    odoo_saas_core (Base)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Customers  │  │  Instances   │  │   Packages   │      │
│  │  (Clientes)  │  │ (Instancias) │  │  (Paquetes)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              odoo_subscription (Suscripciones)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Subscription  │  │    Plans     │  │  Renewals    │      │
│  │  Packages    │  │   (Planes)   │  │  (Renovac.)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│           odoo_saas_licensing (Licencias NUEVO)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Licenses   │  │   Licensed   │  │  Automatic   │      │
│  │ (Licencias)  │  │  Companies   │  │   Billing    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘

         Addon Opcional:
┌─────────────────────────────────────────────────────────────┐
│            odoo_n8n_sales (Integración n8n)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Workflow   │  │  Sync to     │  │   n8n API    │      │
│  │  Templates   │  │  Customer    │  │ Integration  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Módulo 1: odoo_saas_core

### Propósito
Módulo base que unifica la gestión de clientes SaaS, instancias de Odoo, y paquetes de servicio con provisión automática de acceso.

### Modelos Principales

#### saas.customer
Gestión completa del cliente SaaS con ciclo de vida:
- **Estados**: Prospect → Active → Suspended → Terminated
- **Información**: Datos de empresa, contactos, soporte
- **Relaciones**: Instancias, suscripciones, facturación
- **Métricas**: Revenue total, instancias activas

#### saas.instance
Representa una instancia individual de Odoo:
- **Información técnica**: Subdominio, URL, versión, servidor
- **Estados**: Trial → Active → Suspended → Expired → Terminated
- **Recursos**: Usuarios (current/max), Storage (usado/máximo)
- **Fechas**: Trial end, subscription end, días hasta expiración
- **Provisión**: Estado de aprovisionamiento, empresa asociada

#### saas.service.package
Paquetes de servicio (tiers):
- **Ejemplos**: Basic, Professional, Enterprise
- **Recursos**: Max users, storage GB, backup frequency
- **Pricing**: Monthly, yearly, setup fee, descuentos
- **Features**: Custom domain, SSL, API access, priority support
- **Access Control**: Grupos de seguridad asignados automáticamente

### Funcionalidades Clave

**Aprovisionamiento Automático:**
- Creación automática de empresas por cliente
- Asignación de grupos de seguridad según producto
- Restricción multi-empresa (datos aislados)

**Gestión del Ciclo de Vida:**
- Trial de 7 días (configurable)
- Activación manual o automática
- Suspensión/Terminación con razones
- Extensión de trial

**Integración con Ventas:**
- Creación automática de clientes SaaS desde sale.order
- Generación de instancias al confirmar pedido
- Asignación automática de subdominios únicos

### Configuración

```python
# En Configuración → Parámetros del Sistema
saas.base_domain = "odoo.cloud"  # Dominio base para subdominios
```

---

## 🔄 Módulo 2: odoo_subscription

### Propósito
Sistema avanzado de suscripciones con renovaciones automáticas, facturación recurrente y gestión de ciclo de vida.

### Modelos Principales

#### subscription.package
Paquete de suscripción individual:
- **Plan**: Vinculado a subscription.plan
- **Productos**: Líneas de producto (subscription.product.line)
- **Estados**: Draft → In Progress → Closed
- **Fechas**: Start, activation, next invoice, end
- **Billing**: Automática (draft invoice) o manual
- **SaaS Integration**: Link a saas.customer y saas.instance

#### subscription.plan
Plantilla de plan de suscripción:
- **Renovación**: Días/semanas/meses/años
- **Límite**: Single, manual close, o custom count
- **Facturación**: Manual o auto-draft invoice
- **Journal**: Journal de ventas para facturas

#### subscription.product.line
Línea de producto en suscripción:
- Producto, cantidad, precio unitario
- Descuento, taxes
- Totales calculados automáticamente

#### subscription.metering (NUEVO)
Facturación por uso (metering):
- **Métricas**: Users, Storage, API calls, custom
- **Tracking**: Valor métrico, precio unitario, total
- **Facturación**: Vinculación a facturas

### Funcionalidades Clave

**Renovaciones Automáticas:**
- Cron diario que verifica fechas de renovación
- Creación automática de facturas draft
- Envío de emails de alerta de renovación
- Marcado automático para renovación manual

**Facturación:**
- Factura automática en fecha de renovación
- Soporte para taxes por línea
- Descuentos por producto
- Integración con account.move

**Cierre y Expiración:**
- Cierre manual con wizard (razón de cierre)
- Expiración automática según límite de plan
- Stage kanban para visualización

### Workflow Típico

```
1. Crear Subscription Package → Estado: Draft
2. Añadir productos (líneas)
3. Activar → Estado: In Progress
   ├─ Se activa automáticamente
   ├─ Se calcula next_invoice_date
   └─ Se puede crear Sale Order
4. Renovación automática (cron diario)
   ├─ Crea invoice si modo = draft_invoice
   ├─ Envía email de renovación
   └─ Marca is_to_renew = True
5. Cierre
   ├─ Manual (wizard con razón)
   └─ Automático (límite alcanzado)
```

---

## 🏢 Módulo 3: odoo_saas_licensing (NUEVO - MÁS IMPORTANTE)

### Propósito
**Sistema innovador de licencias multi-empresa** diseñado para casos como despachos contables que administran múltiples empresas de clientes.

### Caso de Uso Principal

**Despacho Contable "Contadores Pro":**
- Tiene 1 licencia para administrar empresas
- Licencia permite 10 empresas
- Precio: $100 base + $50 por empresa
- Actualmente administran 7 empresas
- Facturación actual: $100 + (7 × $50) = $450/mes

**Cuando añaden la empresa #8:**
1. Sistema detecta nueva empresa creada
2. Verifica licencia activa del usuario
3. Comprueba límite (8 < 10 ✓)
4. Añade automáticamente a licensed_company
5. Actualiza facturación: $100 + (8 × $50) = $500/mes
6. Notifica al cliente del cambio

**Cuando intentan añadir empresa #11:**
1. Sistema detecta nueva empresa
2. Verifica límite (11 > 10 ✗)
3. Bloquea o envía alerta
4. Cliente debe actualizar licencia

### Modelos Principales

#### saas.license
Licencia principal del cliente:
- **Cliente**: Vinculado a saas.customer
- **Tipo**: Link a saas.license.type
- **Límites**: max_companies, max_users_per_company
- **Contadores**: current_companies (auto-calculado)
- **Pricing**: base_price, price_per_company, price_per_user
- **Estados**: Draft → Active → Suspended → Expired
- **Alertas**: Threshold de uso (80% por defecto)

#### saas.license.type
Tipos de licencia predefinidos:
- **Per Company**: $X base + $Y por empresa
- **Per User**: $X base + $Y por usuario total
- **Hybrid**: Combinación de ambos
- **Fixed**: Precio fijo (unlimited)

#### saas.licensed.company
Empresa licenciada (relación muchos a muchos):
- **License** ↔ **Company** (res.company)
- **Tracking**: users_count, storage_used
- **Status**: is_active, fecha de alta/baja
- **Pricing**: monthly_price individual (opcional)

### Funcionalidades Clave

**🔄 Contador Automático de Empresas:**
```python
# Al crear nueva res.company
def create(self, vals):
    company = super().create(vals)
    # Busca licencia activa del usuario
    # Si tiene licencia:
    #   - Verifica límite
    #   - Añade a licensed_company automáticamente
    #   - Actualiza subscription pricing
    # Si no tiene licencia o límite excedido:
    #   - Envía alerta
    return company
```

**💰 Actualización Dinámica de Facturación:**
```python
def update_subscription_pricing(self):
    if billing_model == 'per_company':
        new_price = base_price + (current_companies × price_per_company)
    elif billing_model == 'per_user':
        total_users = sum(all company users)
        new_price = base_price + (total_users × price_per_user)
    # Actualiza subscription asociada
```

**🚨 Sistema de Alertas:**
- Threshold configurable (80% por defecto)
- Email automático al alcanzar threshold
- Evita spam (1 email por día máximo)
- Log en chatter de la licencia

**🔒 Límites y Bloqueos:**
- Constraint en SQL: max_companies > 0
- Constraint en Python: current ≤ max
- ValidationError al exceder límite

### Modelos de Billing

#### 1. Per Company (Más Común)
```
Base: $100/mes
Por empresa: $50/mes
---
5 empresas = $100 + (5 × $50) = $350/mes
```

#### 2. Per User
```
Base: $200/mes
Por usuario: $15/mes
---
30 usuarios totales = $200 + (30 × $15) = $650/mes
```

#### 3. Hybrid
```
Base: $150/mes
Por empresa: $30/mes
Por usuario: $10/mes
---
3 empresas, 25 usuarios = $150 + (3×$30) + (25×$10) = $490/mes
```

#### 4. Fixed (Unlimited)
```
Precio fijo: $999/mes
Empresas: Ilimitadas
```

### Integraciones

**Con saas.customer:**
- Un cliente puede tener múltiples licencias
- Campo computed: total_licensed_companies
- Botón stat: "X Licenses"

**Con subscription.package:**
- License vinculada a subscription
- Actualiza pricing automáticamente
- Log de cambios en chatter

**Con res.company:**
- Campo: is_licensed
- Relación: license_id
- Hook en create() para auto-registro

### Dashboard y Reportes

**Vista de Licencia (Form):**
- Progreso de uso (7/10 empresas)
- Barra de progreso visual
- Lista de empresas licenciadas
- Cálculo de pricing en tiempo real
- Botón "Add Company" (wizard)

**Vista de Empresa Licenciada:**
- Empresa, fecha de alta
- Usuarios activos (auto-calculado)
- Storage usado
- Botones: Activate / Deactivate

---

## 🤖 Módulo 4: odoo_n8n_sales (Adaptado)

### Propósito
Vender y desplegar workflows de n8n como productos SaaS.

### Cambios de Adaptación

**Dependencias Actualizadas:**
```python
'depends': [
    'base',
    'sale_management',
    'odoo_saas_core',  # NUEVO - antes era saa_s__access_management
]
```

**Integración con saas.customer:**
- Usa saas.customer en lugar de res.partner directo
- Vincula workflows a clientes SaaS

**Workflow de Venta:**
1. Cliente compra producto n8n
2. Confirmar sale.order
3. Sistema crea usuario n8n (o reutiliza)
4. Descarga template de workflow
5. Crea n8n.workflow.instance
6. Cliente sincroniza con su API key
7. Workflow deployado y activo

### Modelos Principales

- **n8n.workflow.instance**: Instancia de workflow del cliente
- **product.template**: Extendido con n8n_workflow_template_id
- **n8n.sync.wizard**: Wizard de sincronización

---

## 🚀 Instalación y Configuración

### 1. Instalación de Módulos

**Orden de Instalación:**
```bash
# 1. Módulo base (requerido)
Apps → Buscar "Odoo SaaS Core" → Instalar

# 2. Suscripciones (opcional pero recomendado)
Apps → Buscar "Odoo Subscription Management" → Instalar

# 3. Licenciamiento (opcional - para multi-empresa)
Apps → Buscar "SaaS Licensing Management" → Instalar

# 4. n8n (opcional - para automatizaciones)
Apps → Buscar "N8N Sales" → Instalar
```

### 2. Configuración Inicial

**A. Configurar Dominio Base (SaaS Core)**
```
Configuración → Técnico → Parámetros → Parámetros del Sistema
Crear: saas.base_domain = "tudominio.com"
```

**B. Crear Paquetes de Servicio**
```
SaaS Management → Configuration → Service Packages
Crear paquetes: Basic, Pro, Enterprise
- Definir: max_users, storage_gb, pricing
- Asignar: access_group_ids (grupos de seguridad)
```

**C. Crear Productos SaaS**
```
Ventas → Productos → Productos
Crear producto:
- Nombre: "Plan Profesional SaaS"
- Marcar: is_saas_product = True
- Asociar: saas_package_id = Professional
- Configurar: saas_creation_policy = "Create User and Privileges"
- Seleccionar: access_group_ids
```

**D. Configurar Planes de Suscripción (si usas odoo_subscription)**
```
Subscriptions → Configuration → Plans
Crear plan:
- Nombre: "Mensual"
- Renovación: 1 month
- Límite: Manual close
- Invoice mode: Auto Draft Invoice
```

**E. Configurar Tipos de Licencia (si usas odoo_saas_licensing)**
```
Licensing → Configuration → License Types
Los tipos default ya están creados:
- Per Company (revisar pricing)
- Per User (revisar pricing)
- Unlimited (revisar pricing)
```

### 3. Flujo de Trabajo Completo

#### Escenario: Despacho Contable compra licencia

**Paso 1: Crear Cliente**
```
SaaS Management → Customers → Create
- Nombre: "Despacho Contadores Pro"
- Email, teléfono, contacto
- Estado: Prospect
```

**Paso 2: Crear Sale Order**
```
Ventas → Órdenes → Create
- Cliente: Despacho Contadores Pro
- Producto: "Licencia 10 Empresas"
  - Producto configurado como SaaS
  - Vinculado a paquete Professional
```

**Paso 3: Confirmar Pedido**
```
Click "Confirm"
Sistema automáticamente:
✓ Crea/actualiza saas.customer
✓ Cambia estado a "Active"
✓ Crea saas.instance (si configurado)
✓ Aprovisiona usuario (si configurado)
✓ Crea subscription.package
```

**Paso 4: Crear Licencia Multi-Empresa**
```
Licensing → Licenses → Create
- Cliente: Despacho Contadores Pro
- Tipo: Per Company
- Max Companies: 10
- Base Price: $100
- Price per Company: $50
- Vincular: Subscription creada
→ Activar licencia
```

**Paso 5: Cliente Administra Empresas**
```
Cliente crea empresas en Odoo:
1. Empresa "Cliente A S.A." → Sistema auto-añade a licencia
2. Empresa "Cliente B S.A." → Sistema auto-añade a licencia
3. ... hasta 10 empresas

Al crear empresa #11:
→ Sistema envía alerta
→ Requiere upgrade de licencia
```

**Paso 6: Renovación Automática**
```
Cron diario verifica:
- Subscriptions próximas a renovar
- Crea factura automática
- Incluye pricing actualizado de licencia
- Envía email de renovación
```

---

## 📊 Reportes y Dashboards

### SaaS Core
- **Customers**: Kanban por estado, revenue total
- **Instances**: Tree con % storage, % users
- **Stat Buttons**: Instancias activas, total revenue

### Subscriptions
- **Pivot Report**: Análisis de suscripciones
- **Kanban**: Por stage (draft, progress, closed)
- **Renewal Pipeline**: Próximas a renovar

### Licensing
- **License Usage**: Tabla con % de uso
- **Companies per License**: Gráfico de barras
- **Revenue by License Type**: Análisis financiero

---

## 🔐 Seguridad

### Grupos de Acceso

**SaaS Core:**
- `group_saas_user`: Lectura/escritura básica
- `group_saas_manager`: Control total

**Subscriptions:**
- `group_subscription_user`: Gestión de suscripciones
- `group_subscription_manager`: Configuración de planes

**Licensing:**
- `group_licensing_user`: Gestión de licencias
- `group_licensing_manager`: Configuración de tipos

### Reglas de Seguridad

**Multi-company:**
- Invoices: Solo de su empresa
- Sale Orders: Solo de su empresa
- Partners: Compartidos o de su empresa

**SaaS Instances:**
- Usuarios ven solo instancias de su empresa
- Administradores ven todas

---

## 🛠️ Personalización

### Añadir Nuevo Tipo de Licencia

```python
# En data/license_type_data.xml
<record id="license_type_custom" model="saas.license.type">
    <field name="name">Custom License</field>
    <field name="code">CUSTOM</field>
    <field name="billing_model">hybrid</field>
    <field name="default_max_companies">20</field>
    <field name="default_base_price">200.00</field>
    <field name="default_price_per_company">25.00</field>
    <field name="default_price_per_user">10.00</field>
</record>
```

### Modificar Threshold de Alertas

```python
# En saas.license
license.alert_threshold = 90  # Alertar al 90% de uso
```

### Cambiar Frecuencia de Cron

```xml
<!-- En data/automated_actions.xml -->
<field name="interval_number">1</field>
<field name="interval_type">hours</field>  <!-- Cambiar a horas -->
```

---

## 📝 Preguntas Frecuentes (FAQ)

### ¿Cuál es la diferencia entre Instance y License?

- **Instance**: Instalación individual de Odoo (1 cliente = N instancias)
- **License**: Permiso para administrar N empresas dentro de Odoo

### ¿Puedo tener una instancia CON licencia multi-empresa?

**Sí**, ese es el caso de uso principal:
```
Cliente: Despacho Contable
├─ Instance: despacho.odoo.cloud (1 instalación de Odoo)
└─ License: 10 empresas
    ├─ Empresa "Cliente A"
    ├─ Empresa "Cliente B"
    └─ ...
```

### ¿Cómo se factura el modelo híbrido?

```
Base fija + (empresas × precio_empresa) + (usuarios_totales × precio_usuario)
```

### ¿Qué pasa si el cliente excede su límite?

1. Sistema envía alerta automática
2. Bloquea creación de nuevas empresas (opcional)
3. Cliente debe:
   - Eliminar empresas, o
   - Upgrade de licencia (más empresas)

### ¿Las licencias renuevan automáticamente?

Sí, si están vinculadas a una subscription.package:
- Cron verifica diariamente
- Crea factura con pricing actualizado
- Envía email de renovación

---

## 🐛 Solución de Problemas

### Error: "No active user found for partner"

**Causa**: Partner no tiene usuario asociado

**Solución**:
```python
# Crear usuario para el partner
Configuración → Usuarios → Crear
- Partner: Seleccionar partner
- Login: email del partner
```

### Licencia no se actualiza al crear empresa

**Causa**: Usuario no tiene saas.customer asociado

**Solución**:
```python
# Verificar y crear cliente SaaS
SaaS Management → Customers → Buscar por partner
Si no existe: Crear con partner vinculado
```

### Subscription no genera facturas automáticamente

**Causa**: Invoice mode = 'manual' o cron desactivado

**Solución**:
```
1. Subscription → Plan → Invoice Mode = "Auto Draft Invoice"
2. Configuración → Técnico → Automation → Crons
   Buscar: "Subscription: Management & Renewal"
   → Activar
```

---

## 📚 Recursos Adicionales

### Estructura de Archivos

```
modulos_odoo18/
├── odoo_saas_core/
│   ├── models/          # 6 modelos
│   ├── views/           # 8 archivos XML
│   ├── wizards/         # Provisioning wizard
│   ├── security/        # Access rights + rules
│   └── data/            # Packages, sequences, crons
│
├── odoo_subscription/
│   ├── models/          # 9 modelos
│   ├── security/        # Access control
│   └── data/            # Stages, plans, crons
│
├── odoo_saas_licensing/  # ⭐ NUEVO
│   ├── models/          # 6 modelos
│   ├── security/        # Access control
│   └── data/            # License types, crons
│
└── odoo_n8n_sales/      # Adaptado
    ├── models/          # 4 modelos
    └── wizards/         # Sync wizard
```

### Próximos Pasos

1. **Testing**: Instalar en entorno de prueba
2. **Configuración**: Ajustar paquetes y precios
3. **Personalización**: Adaptar a tu modelo de negocio
4. **Demo**: Crear datos demo para mostrar a clientes
5. **Documentación**: Crear manual de usuario

### Soporte

Para dudas o mejoras:
- Email: soporte@automateai.com.mx
- Web: https://automateai.com.mx

---

## ✅ Checklist de Implementación

- [ ] Instalar odoo_saas_core
- [ ] Configurar dominio base (saas.base_domain)
- [ ] Crear service packages (Basic, Pro, Enterprise)
- [ ] Crear productos SaaS vinculados a packages
- [ ] Instalar odoo_subscription
- [ ] Crear subscription plans
- [ ] Configurar mail templates de renovación
- [ ] Instalar odoo_saas_licensing
- [ ] Revisar license types (per company, per user)
- [ ] Activar crons (subscriptions, licenses, instances)
- [ ] Crear cliente de prueba
- [ ] Crear sale order de prueba
- [ ] Verificar aprovisionamiento automático
- [ ] Crear licencia de prueba
- [ ] Probar creación de empresas
- [ ] Verificar alertas de límite
- [ ] Probar renovación automática
- [ ] Configurar n8n (si aplica)

---

## 🎯 Conclusión

Este sistema proporciona una plataforma completa para ofrecer Odoo como SaaS con:

✅ **Gestión integral de clientes** (lifecycle completo)
✅ **Instancias multi-tenant** (provisioning automático)
✅ **Suscripciones recurrentes** (facturación automática)
✅ **Licencias multi-empresa** (facturación por uso)
✅ **Integración n8n** (automatizaciones como servicio)

**Casos de uso cubiertos:**
- SaaS tradicional (1 cliente = 1 instancia)
- Multi-empresa (despachos, consultoras)
- Facturación híbrida (fixed + usage-based)
- Automatizaciones (n8n workflows)

**Mejora respecto a módulos originales:**
- ✅ Unificación (4 módulos → 3 módulos coherentes)
- ✅ Eliminación de redundancias
- ✅ Nueva funcionalidad de licencias
- ✅ Integración completa entre módulos
- ✅ Facturación automática por uso

¡Listo para producción! 🚀
