# 🧪 Guía Completa de Pruebas - Módulos SaaS

Esta guía te llevará paso a paso para probar cada módulo nuevo.

---

## 📋 **Índice**

1. [Instalación Inicial](#1-instalación-inicial)
2. [Pruebas: product_permissions](#2-pruebas-product_permissions)
3. [Pruebas: saas_management](#3-pruebas-saas_management)
4. [Pruebas: saas_licensing](#4-pruebas-saas_licensing)
5. [Prueba Integrada Completa](#5-prueba-integrada-completa)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Instalación Inicial

### 1.1. Verificar que subscription_package esté instalado

```
Aplicaciones → Buscar "subscription" → Debe estar instalado
```

### 1.2. Instalar módulos en orden

**IMPORTANTE:** Instalar en este orden exacto:

```
1. product_permissions
2. saas_management
3. saas_licensing (opcional)
```

**Cómo instalar:**
1. Ir a **Aplicaciones**
2. Quitar filtro "Apps"
3. Buscar el nombre del módulo
4. Click en **Instalar**
5. Esperar a que termine

### 1.3. Verificar instalación exitosa

**Revisar menús nuevos:**
- ✅ Menú "SaaS Management" debe aparecer en el menú principal
- ✅ Dentro debe haber: Clients, Instances, Licensing

---

## 2. Pruebas: product_permissions

### 🎯 Objetivo
Verificar que los productos pueden asignar permisos automáticamente a usuarios.

### 2.1. Configuración Inicial

#### A. Crear grupos de seguridad de prueba

1. Ir a **Ajustes → Usuarios & Compañías → Grupos**
2. Crear un grupo nuevo:
   ```
   Nombre: Test - Premium Users
   Categoría: Extra Rights
   ```
3. Guardar

#### B. Crear usuario de prueba

1. Ir a **Ajustes → Usuarios & Compañías → Usuarios**
2. Crear nuevo usuario:
   ```
   Nombre: Cliente Prueba
   Email: cliente@test.com
   Tipo de Acceso: Portal
   ```
3. **NO ASIGNAR GRUPOS MANUALMENTE** (esto se hará automáticamente)
4. Guardar

#### C. Crear contacto/partner

1. Ir a **Contactos**
2. Crear contacto:
   ```
   Nombre: Empresa Test SRL
   Email: cliente@test.com (mismo email que el usuario)
   Es una Compañía: ✓
   ```
3. Guardar

### 2.2. Crear Producto con Permisos

1. Ir a **Ventas → Productos → Productos**
2. Crear nuevo producto:
   ```
   Nombre: Licencia Premium
   Puede ser vendido: ✓
   Precio: 1000.00
   ```

3. Ir a la pestaña **"Permissions"** (nueva)
4. Configurar:
   ```
   Assign Permissions on Sale: ✓
   Permission Groups: [Seleccionar "Test - Premium Users"]
   ```

5. **Opcional:** Agregar descripción de permisos
   ```
   Permission Description:
   "Al comprar este producto, el usuario obtendrá acceso premium al sistema"
   ```

6. Guardar

### 2.3. Realizar Venta

1. Ir a **Ventas → Órdenes → Presupuestos**
2. Crear nuevo presupuesto:
   ```
   Cliente: Empresa Test SRL
   ```

3. Agregar línea:
   ```
   Producto: Licencia Premium
   Cantidad: 1
   ```

4. **Guardar** el presupuesto

5. Click en **"Confirmar"**

### 2.4. Verificar Resultados ✅

**A. Revisar el Chatter de la orden:**
Deberías ver mensajes como:
```
✅ Permissions assigned to user: Cliente Prueba
   - Test - Premium Users
```

**B. Verificar el usuario:**
1. Ir a **Ajustes → Usuarios → Usuarios**
2. Abrir "Cliente Prueba"
3. Ir a pestaña "Derechos de Acceso"
4. **VERIFICAR:** El grupo "Test - Premium Users" debe estar asignado ✅

**C. Caso especial - Administradores:**
Si el partner tiene un usuario administrador:
- El mensaje debe decir: "ℹ️ Permissions not assigned: User XXX is an administrator"
- Los permisos NO se aplican a administradores (protección) ✅

### 2.5. Pruebas Adicionales

#### Prueba 1: Usuario sin cuenta Odoo

1. Crear un partner sin usuario asociado:
   ```
   Nombre: Cliente Sin Usuario
   Email: sinusuario@test.com
   ```

2. Crear orden de venta con "Licencia Premium"
3. Confirmar orden

**Resultado esperado:**
- ✅ Se crea automáticamente un usuario nuevo
- ✅ El usuario tiene los grupos asignados
- ✅ Mensaje en chatter: "✅ User created: Cliente Sin Usuario"

#### Prueba 2: Múltiples grupos

1. Crear producto con múltiples grupos:
   ```
   Producto: Licencia Empresarial
   Permission Groups:
     - Test - Premium Users
     - Sales / User: Own Documents Only
   ```

2. Vender y confirmar

**Resultado esperado:**
- ✅ Todos los grupos deben asignarse
- ✅ Los grupos previos del usuario se mantienen (aditivo)

---

## 3. Pruebas: saas_management

### 🎯 Objetivo
Verificar la creación automática de clientes SaaS e instancias Odoo.

### 3.1. Configuración Inicial

#### A. Configurar dominio base

1. Ir a **Ajustes → Técnico → Parámetros → Parámetros del Sistema**
2. Buscar la clave: `saas.base_domain`
3. Si no existe, crear:
   ```
   Clave: saas.base_domain
   Valor: odoo.cloud
   ```
   (Puedes usar tu propio dominio)

4. Guardar

#### B. Verificar grupos de seguridad

1. Ir a **Ajustes → Usuarios → Grupos**
2. Buscar "SaaS Manager"
3. Asegurarte de tener el grupo asignado a tu usuario

### 3.2. Explorar la Interfaz

1. Ir al menú **"SaaS Management"** (nuevo en el menú principal)

2. Explorar submenús:
   ```
   SaaS Management
   ├── Clients
   │   └── Clients (lista)
   ├── Instances
   │   └── All Instances (lista)
   └── Configuration
   ```

### 3.3. Crear Cliente SaaS Manualmente

1. Ir a **SaaS Management → Clients → Clients**
2. Click en **Crear**
3. Completar:
   ```
   Client Name: Acme Corporation
   Partner: [Crear nuevo o seleccionar existente]
   Email: acme@example.com
   Phone: +1234567890
   Status: Prospect (por defecto)
   ```

4. Guardar

5. Click en botón **"Activate"** (en el header)

**Resultado esperado:**
- ✅ Estado cambia a "Active"
- ✅ Fecha de activación se completa
- ✅ Mensaje en chatter

### 3.4. Crear Instancia SaaS Manualmente

1. Ir a **SaaS Management → Instances → All Instances**
2. Click en **Crear**
3. Completar:
   ```
   Instance Name: Acme - Production
   Client: Acme Corporation
   Subdomain: acme-prod (debe ser único)
   Odoo Version: 18.0
   Status: Draft
   ```

4. Guardar

5. **Verificar Full URL:**
   - Debería generarse automáticamente: `https://acme-prod.odoo.cloud`

6. Click en **"Start Trial"**

**Resultado esperado:**
- ✅ Estado cambia a "Trial"
- ✅ Trial End Date se completa (7 días en el futuro)

7. Después, click en **"Activate"**

**Resultado esperado:**
- ✅ Estado cambia a "Active"
- ✅ Activated Date se completa

### 3.5. Crear Producto SaaS

1. Ir a **Ventas → Productos → Productos**
2. Crear nuevo producto:
   ```
   Nombre: Odoo SaaS Instance - Standard
   Puede ser vendido: ✓
   Precio: 2500.00
   ```

3. Ir a pestaña **"SaaS Configuration"** (nueva)
4. Configurar:
   ```
   Is SaaS Instance Product: ✓
   Auto-Create Instance: ✓
   Trial Days: 14
   ```

5. Guardar

### 3.6. Venta Automática de Instancia SaaS

1. Crear un partner nuevo:
   ```
   Nombre: Tech Startup Inc
   Email: tech@startup.com
   ```

2. Ir a **Ventas → Órdenes → Presupuestos**
3. Crear presupuesto:
   ```
   Cliente: Tech Startup Inc
   ```

4. Agregar línea:
   ```
   Producto: Odoo SaaS Instance - Standard
   Cantidad: 1
   ```

5. **Confirmar orden**

### 3.7. Verificar Creación Automática ✅

**A. Revisar Chatter de la orden:**
Deberías ver:
```
✅ SaaS Client created: Tech Startup Inc
🖥️ SaaS Instance created: Tech Startup Inc - Odoo SaaS Instance - Standard (https://tech-startup-inc.odoo.cloud)
```

**B. Verificar en SaaS Management → Clients:**
- ✅ Debe aparecer "Tech Startup Inc"
- ✅ Estado: Active
- ✅ Total Instances: 1
- ✅ Active Instances: 0 (porque está en trial)

**C. Verificar en SaaS Management → Instances:**
- ✅ Debe aparecer instancia nueva
- ✅ Subdomain: tech-startup-inc (generado automáticamente)
- ✅ Estado: Trial
- ✅ Trial End Date: 14 días en el futuro

**D. Abrir el cliente:**
1. Click en "Tech Startup Inc" en la lista de clientes
2. Click en el botón **"Instances"** (stat button, muestra "1")

**Resultado esperado:**
- ✅ Muestra la instancia creada

### 3.8. Pruebas de Subdominios Únicos

1. Crear **otra** orden de venta para el mismo cliente
2. Usar el **mismo producto SaaS**
3. Confirmar

**Resultado esperado:**
- ✅ Se crea segunda instancia
- ✅ Subdomain: tech-startup-inc-1 (con contador)
- ✅ Cliente ahora tiene: Total Instances: 2

### 3.9. Pruebas de Estados

#### Estado: Suspend

1. Abrir un cliente activo
2. Click en botón **"Suspend"** (header)

**Resultado esperado:**
- ✅ Cliente → Estado: Suspended
- ✅ Todas las instancias activas → Estado: Suspended
- ✅ Mensaje en chatter

#### Estado: Trial → Active

1. Abrir una instancia en Trial
2. Click en **"Activate"**

**Resultado esperado:**
- ✅ Estado: Active
- ✅ Activated Date completada
- ✅ Trial End Date ya no es relevante

---

## 4. Pruebas: saas_licensing

### 🎯 Objetivo
Verificar el tracking de uso y facturación por excesos.

### 4.1. Configurar Límites en Subscription Package

1. Ir a **Suscripciones → Configuración → Paquetes de Suscripción**
2. Crear o editar un paquete:
   ```
   Nombre: Plan Básico
   ```

3. Ir a pestaña **"License Limits"** (nueva)
4. Configurar límites:
   ```
   === Plan Limits ===
   Max Users: 5
   Max Companies: 1
   Max Storage (GB): 10

   === Overage Pricing ===
   Price per Additional User: 50.00
   Price per Additional Company: 200.00
   Price per Additional GB: 10.00
   ```

5. Guardar

### 4.2. Vincular Instancia a Suscripción

1. Ir a **SaaS Management → Instances**
2. Abrir una instancia activa
3. Asignar:
   ```
   Subscription: Plan Básico
   ```
4. Guardar

### 4.3. Crear Snapshot de Licencia Manual

1. Dentro de la instancia, ir a pestaña **"Licensing"** (nueva)
2. Click en botón **"Snapshot"** (en button box)

3. Se abre formulario de license snapshot
4. Configurar uso actual:
   ```
   User Count: 8 (excede límite de 5)
   Company Count: 2 (excede límite de 1)
   Storage (GB): 12.5 (excede límite de 10)
   ```

5. Guardar

### 4.4. Verificar Detección de Excesos ✅

**A. Ver el formulario del license record:**
Deberías ver:

```
⚠️ Overage Detected!
This instance has usage beyond the plan limits.
Total overage amount: $560.00
```

**B. Verificar pestaña "Overages":**
```
=== Overage Quantities ===
User Overage: 3 (8 - 5)
Company Overage: 1 (2 - 1)
Storage Overage: 2.5 (12.5 - 10)

=== Billing ===
Overage Amount: $560.00
  3 users × $50 = $150
  1 company × $200 = $200
  2.5 GB × $10 = $25
  TOTAL = $375 ❌ Revisar cálculo
```

Cálculo correcto:
- 3 users × $50 = $150
- 1 company × $200 = $200
- 2.5 GB × $10 = $25
- **TOTAL = $375** (no $560)

### 4.5. Generar Factura por Excesos

1. En el formulario del license record
2. Click en botón **"Create Invoice"** (header, solo visible si hay overages)

**Resultado esperado:**
- ✅ Se abre factura borrador
- ✅ Cliente: El partner del cliente SaaS
- ✅ Líneas de factura:
  ```
  - Additional Users - [Instance Name] | Qty: 3 | Price: $50 | Total: $150
  - Additional Companies - [Instance Name] | Qty: 1 | Price: $200 | Total: $200
  - Additional Storage (GB) - [Instance Name] | Qty: 2.5 | Price: $10 | Total: $25

  TOTAL FACTURA: $375
  ```

3. **Validar factura** (confirmarla)

4. Volver al license record

**Resultado esperado:**
- ✅ Campo "Invoice" ahora muestra la factura
- ✅ Invoice Status: Posted
- ✅ Botón "Create Invoice" ya no aparece (ya facturado)

### 4.6. Prueba de Uso Dentro de Límites

1. Crear otro snapshot con uso normal:
   ```
   User Count: 3 (dentro de 5)
   Company Count: 1 (dentro de 1)
   Storage (GB): 8.0 (dentro de 10)
   ```

**Resultado esperado:**
- ✅ Banner verde: "Within Limits - No overage charges"
- ✅ is_billable = False
- ✅ overage_amount = 0
- ✅ Botón "Create Invoice" NO aparece

### 4.7. Verificar Cron Job (Automático)

**Nota:** El cron job corre diariamente de forma automática.

Para probarlo manualmente:

1. Ir a **Ajustes → Técnico → Automatización → Acciones Planificadas**
2. Buscar: "SaaS: Create Monthly License Records"
3. Click para abrir
4. Verificar:
   ```
   Estado: Activo ✓
   Interval: 1 Days
   ```

5. **Para ejecutar manualmente:** Click en "Run Manually"

**Resultado esperado:**
- ✅ Se crean license records para todas las instancias activas/trial
- ✅ Fecha = hoy
- ✅ Métricas copiadas de cada instancia

### 4.8. Vista de Instancia con Licensing

1. Abrir una instancia que tenga license records
2. Verificar:
   - ✅ Stat button "Licenses" muestra cantidad
   - ✅ Stat button "Snapshot" disponible
   - ✅ Si hay overages: Banner naranja de advertencia
   - ✅ Pestaña "Licensing" muestra historial

---

## 5. Prueba Integrada Completa

### 🎯 Objetivo
Probar todos los módulos trabajando juntos.

### 5.1. Crear Producto Completo

1. Ir a **Ventas → Productos**
2. Crear:
   ```
   Nombre: Odoo SaaS Enterprise Package
   Precio: 5000.00
   ```

**Pestaña "Permissions":**
```
Assign Permissions: ✓
Permission Groups:
  - Sales / Administrator
  - Test - Premium Users
```

**Pestaña "SaaS Configuration":**
```
Is SaaS Instance Product: ✓
Auto-Create Instance: ✓
Trial Days: 30
```

**Opcional - si tienes n8n-sales:**
```
N8N Workflow Template: [Seleccionar un workflow]
```

3. Guardar

### 5.2. Crear Subscription Package

1. Ir a **Suscripciones → Paquetes**
2. Crear:
   ```
   Nombre: Enterprise Plan
   ```

**Pestaña "License Limits":**
```
Max Users: 20
Max Companies: 5
Max Storage: 100

Price per Additional User: 75
Price per Additional Company: 300
Price per Additional GB: 15
```

3. Guardar

### 5.3. Realizar Venta Completa

1. Crear partner:
   ```
   Nombre: MegaCorp Industries
   Email: admin@megacorp.com
   ```

2. Crear usuario para el partner:
   ```
   Nombre: Admin MegaCorp
   Email: admin@megacorp.com
   Tipo: Portal
   ```

3. Crear orden de venta:
   ```
   Cliente: MegaCorp Industries
   Producto: Odoo SaaS Enterprise Package
   Cantidad: 1
   ```

4. **Confirmar orden**

### 5.4. Verificar TODO el Flujo ✅

**A. Chatter de la orden debe mostrar:**
```
✅ Permissions assigned to user: Admin MegaCorp
   - Sales / Administrator
   - Test - Premium Users

✅ SaaS Client created: MegaCorp Industries

🖥️ SaaS Instance created: MegaCorp Industries - Odoo SaaS Enterprise Package
   (https://megacorp-industries.odoo.cloud)

[Si tienes n8n-sales]
✅ Usuario de N8N creado exitosamente
✅ Instancia de workflow creada
```

**B. Verificar Usuario:**
- Ir a Usuarios → "Admin MegaCorp"
- ✅ Tiene grupos: Sales / Administrator, Test - Premium Users

**C. Verificar Cliente SaaS:**
- Ir a SaaS Management → Clients
- ✅ "MegaCorp Industries" existe
- ✅ Estado: Active
- ✅ Total Instances: 1

**D. Verificar Instancia:**
- Ir a SaaS Management → Instances
- ✅ Instancia creada
- ✅ Subdomain: megacorp-industries
- ✅ Estado: Trial
- ✅ Trial End Date: 30 días en el futuro
- ✅ Cliente: MegaCorp Industries

**E. Vincular a suscripción:**
1. Abrir la instancia
2. Asignar:
   ```
   Subscription: Enterprise Plan
   ```
3. Actualizar métricas:
   ```
   Current Users: 25 (excede 20)
   Company Count: 3 (dentro de 5)
   Storage Used: 120 (excede 100)
   ```
4. Guardar

**F. Crear license snapshot:**
1. Click en botón "Snapshot"
2. Verificar cálculo de overages:
   ```
   User Overage: 5 (25 - 20)
   Storage Overage: 20 (120 - 100)

   Overage Amount:
   5 × $75 = $375
   20 × $15 = $300
   TOTAL = $675
   ```

**G. Generar factura:**
1. Click "Create Invoice"
2. ✅ Factura con total $675
3. Confirmar factura

**H. Verificar integración completa:**
✅ Usuario tiene permisos
✅ Cliente SaaS creado
✅ Instancia SaaS creada y activa
✅ License tracking funcionando
✅ Facturación por excesos funcionando
✅ Todo registrado en chatter

---

## 6. Troubleshooting

### Problema: "No aparece el menú SaaS Management"

**Solución:**
1. Verificar que el módulo está instalado (Apps → saas_management)
2. Verificar que tienes el grupo "SaaS Manager" asignado
3. Refrescar la página (Ctrl + F5)

### Problema: "Los permisos no se asignan"

**Verificar:**
1. El partner tiene email
2. El email coincide con un usuario existente O se creará uno nuevo
3. El usuario no es administrador (protección automática)
4. Revisar el chatter de la orden para ver mensajes

### Problema: "No se crea la instancia SaaS automáticamente"

**Verificar:**
1. El producto tiene "Is SaaS Instance Product" = True
2. El producto tiene "Auto-Create Instance" = True
3. Revisar logs de Odoo para errores
4. Verificar que sale_order.action_confirm() se ejecuta

### Problema: "Error: subdomain must be unique"

**Solución:**
- Ya existe una instancia con ese subdomain
- El sistema debería auto-incrementar (megacorp-1, megacorp-2, etc.)
- Verificar la lógica en `sale_order.py` línea 102-104

### Problema: "No se calculan los overages"

**Verificar:**
1. La instancia tiene Subscription asignada
2. La subscription tiene límites configurados
3. El uso actual excede los límites
4. Campos compute están funcionando

### Problema: "El cron no crea snapshots"

**Verificar:**
1. Cron está activo (Acciones Planificadas)
2. Hay instancias en estado active o trial
3. Ejecutar manualmente para probar
4. Revisar logs

---

## 📊 Checklist Final de Pruebas

Marca cada item cuando lo completes:

### product_permissions
- [ ] Producto con permisos configurado
- [ ] Venta confirmada
- [ ] Usuario recibe grupos automáticamente
- [ ] Administradores están protegidos
- [ ] Usuario sin cuenta → se crea automáticamente
- [ ] Mensajes en chatter correctos

### saas_management
- [ ] Cliente SaaS creado manualmente
- [ ] Instancia SaaS creada manualmente
- [ ] Estados funcionan (activate, suspend, etc.)
- [ ] Producto SaaS configurado
- [ ] Venta crea cliente automáticamente
- [ ] Venta crea instancia automáticamente
- [ ] Subdomain único generado
- [ ] Full URL generada correctamente
- [ ] Múltiples instancias para mismo cliente

### saas_licensing
- [ ] Subscription con límites configurada
- [ ] License record creado manualmente
- [ ] Overages calculados correctamente
- [ ] Factura generada por overages
- [ ] Uso dentro de límites (sin overages)
- [ ] Cron job configurado
- [ ] Vista de instancia muestra licensing

### Integración
- [ ] Producto completo (permisos + SaaS)
- [ ] Venta activa TODO el flujo
- [ ] Permisos asignados ✓
- [ ] Cliente creado ✓
- [ ] Instancia creada ✓
- [ ] Licensing funciona ✓
- [ ] Facturación funciona ✓

---

## 🎉 ¡Felicidades!

Si completaste todas las pruebas, tus módulos están funcionando perfectamente.

**Próximos pasos:**
1. Personalizar los productos según tu negocio
2. Configurar planes de suscripción reales
3. Integrar con sistemas externos (si aplica)
4. Documentar procesos internos
5. Capacitar al equipo de ventas

---

**Documentación creada:** 2025-11-17
**Versión de Odoo:** 18.0
**Módulos:** product_permissions, saas_management, saas_licensing
