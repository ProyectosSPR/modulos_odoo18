# Guía de Pruebas - SaaS Multi-Company

## Índice de Pruebas

1. [Prueba Básica: Creación de Empresa](#prueba-1-creación-básica-de-empresa)
2. [Prueba de Aislamiento de Datos](#prueba-2-aislamiento-de-datos-multi-company)
3. [Prueba de Licenciamiento](#prueba-3-licenciamiento-y-overages)
4. [Prueba de Permisos](#prueba-4-asignación-de-permisos)
5. [Prueba de Plantillas](#prueba-5-uso-de-plantillas)
6. [Prueba de Múltiples Clientes](#prueba-6-múltiples-clientes)
7. [Prueba de Reglas de Seguridad](#prueba-7-reglas-de-seguridad)
8. [Prueba de Cron Jobs](#prueba-8-cron-jobs-automaticos)

---

## Prueba 1: Creación Básica de Empresa

**Objetivo**: Verificar que se crea una empresa automáticamente al vender un producto de acceso a módulos.

### Setup

1. Crear producto de prueba:
   ```
   Sales → Products → Create

   Nombre: Test Module Access
   Tipo: Service

   Tab "Multi-Company":
     ☑ Is Module Access Product
     ☑ Auto-Create Company
     ☑ Restrict to Company
   ```

2. Crear cliente de prueba:
   ```
   Contacts → Create

   Nombre: Test Company Alpha
   Email: alpha@test.com
   ```

### Ejecución

1. Crear orden de venta:
   ```
   Sales → Orders → Create

   Cliente: Test Company Alpha
   Producto: Test Module Access
   Cantidad: 1
   ```

2. Confirmar la orden

### Verificación

✅ **Chatter debe mostrar**:
- "✅ SaaS Client created: Test Company Alpha"
- "🏢 Company created: Test Company Alpha"
- "👤 User assigned to company Test Company Alpha"

✅ **Verificar empresa creada**:
```
SaaS Management → Companies → SaaS Companies
→ Debe aparecer "Test Company Alpha"
→ Abrir la empresa
→ Verificar:
  • SaaS Client: Test Company Alpha
  • Is SaaS Company: ☑
  • User Count: 1
```

✅ **Verificar usuario**:
```
Settings → Users & Companies → Users
→ Buscar usuario de alpha@test.com
→ Verificar:
  • Allowed Companies: debe incluir "Test Company Alpha"
  • Current Company: Test Company Alpha
```

---

## Prueba 2: Aislamiento de Datos Multi-Company

**Objetivo**: Verificar que los usuarios solo vean datos de su propia empresa.

### Setup

1. Crear dos clientes:
   ```
   Cliente A: Test Company Beta (beta@test.com)
   Cliente B: Test Company Gamma (gamma@test.com)
   ```

2. Crear órdenes para ambos clientes con producto de acceso a módulos

3. Crear datos de prueba para cada empresa:
   ```
   Como Admin:
   → Cambiar a empresa "Test Company Beta"
   → Contacts → Create
     Nombre: Contact Beta 1
     Empresa: Test Company Beta

   → Cambiar a empresa "Test Company Gamma"
   → Contacts → Create
     Nombre: Contact Gamma 1
     Empresa: Test Company Gamma
   ```

### Ejecución

1. Iniciar sesión como usuario de Cliente A (beta@test.com)

2. Ir a Contacts

### Verificación

✅ **Usuario de Beta debe ver**:
- Contact Beta 1 ✓
- Contact Gamma 1 ✗ (NO debe aparecer)

✅ **Cambiar a usuario de Gamma**:
- Iniciar sesión como gamma@test.com
- Contact Gamma 1 ✓
- Contact Beta 1 ✗ (NO debe aparecer)

✅ **Admin debe ver todos**:
- Iniciar sesión como Admin
- Debe ver ambos contactos

---

## Prueba 3: Licenciamiento y Overages

**Objetivo**: Verificar que el sistema detecta cuando se exceden los límites de la suscripción.

### Setup

1. Crear paquete de suscripción con límites bajos:
   ```
   Subscriptions → Subscription Packages → Create

   Nombre: Test Plan Limited
   Max Users: 2
   Max Companies: 1
   Max Storage GB: 5

   Price per User: $50
   Price per Company: $100
   Price per GB: $10
   ```

2. Crear producto con esta suscripción:
   ```
   Nombre: Limited Module Access
   Multi-Company Subscription: Test Plan Limited
   ```

3. Vender producto a un cliente

### Ejecución

**Escenario 1: Exceder límite de usuarios**

1. Crear orden para "Test Company Delta"
2. Crear 3 usuarios internos en la empresa "Test Company Delta"
3. Ir a la empresa:
   ```
   SaaS Management → Companies → Test Company Delta
   → User Count debe mostrar 3
   ```

4. Crear snapshot de licencia:
   ```
   En la empresa → Action → Create License Snapshot
   (o esperar al cron diario)
   ```

5. Verificar licencia:
   ```
   SaaS Management → Licensing → License Records
   → Filtrar por Company: Test Company Delta
   → Abrir registro más reciente

   Verificar:
     • User Count: 3
     • Max Users (from subscription): 2
     • Is Billable: ☑
     • User Overage: 1
     • Overage Amount: $50 (1 user × $50)
   ```

**Escenario 2: Crear factura de overage**

1. Desde el registro de licencia billable:
   ```
   → Botón "Create Invoice"
   ```

2. Verificar factura creada:
   ```
   → Debe crear factura con línea:
     Descripción: "Additional User Overage"
     Cantidad: 1
     Precio Unitario: $50
     Total: $50
   ```

### Verificación

✅ **Sistema detecta overage correctamente**
✅ **Cálculo de overage es correcto**
✅ **Factura se crea automáticamente**

---

## Prueba 4: Asignación de Permisos

**Objetivo**: Verificar que los permisos se asignan correctamente al crear la empresa.

### Setup

1. Crear producto con permisos específicos:
   ```
   Sales → Products → Create

   Nombre: Inventory Access Product

   Tab "Permissions":
     ☑ Assign Permissions
     Permission Groups:
       - Inventory / User
       - Inventory / Manager

   Tab "Multi-Company":
     ☑ Is Module Access Product
     ☑ Auto-Create Company
   ```

### Ejecución

1. Crear cliente nuevo: "Test Company Epsilon"
2. Vender "Inventory Access Product" al cliente
3. Confirmar orden

### Verificación

1. Verificar usuario creado:
   ```
   Settings → Users & Companies → Users
   → Buscar usuario epsilon@test.com
   → Tab "Access Rights"

   Verificar que tenga:
     ☑ Inventory / User
     ☑ Inventory / Manager
   ```

2. Probar acceso:
   ```
   → Iniciar sesión como epsilon@test.com
   → Debe tener acceso al menú "Inventory"
   ```

✅ **Permisos asignados correctamente**
✅ **Usuario puede acceder a funcionalidades**

---

## Prueba 5: Uso de Plantillas

**Objetivo**: Verificar que las empresas se crean con configuración de la plantilla.

### Setup

1. Crear empresa plantilla:
   ```
   Settings → Companies → Create

   Nombre: SaaS Template - Premium
   ☑ Is Template Company
   Currency: MXN
   Country: Mexico
   Email: soporte@template.com
   Phone: +52 55 1234 5678
   ```

2. Crear producto con plantilla:
   ```
   Nombre: Premium Module Access
   Company Template: SaaS Template - Premium
   ```

### Ejecución

1. Vender producto a nuevo cliente "Test Company Zeta"
2. Confirmar orden

### Verificación

1. Verificar empresa creada:
   ```
   SaaS Management → Companies → Test Company Zeta

   Verificar que copió de plantilla:
     • Currency: MXN ✓
     • Country: Mexico ✓
     • Email: soporte@template.com ✓
     • Phone: +52 55 1234 5678 ✓
   ```

✅ **Configuración de plantilla se copia correctamente**

---

## Prueba 6: Múltiples Clientes

**Objetivo**: Verificar que el sistema maneja múltiples clientes simultáneamente.

### Ejecución

1. Crear 10 clientes de prueba (puedes usar script o manual)
2. Vender producto de acceso a módulos a cada uno
3. Confirmar todas las órdenes

### Verificación

1. Ver todas las empresas SaaS:
   ```
   SaaS Management → Companies → SaaS Companies
   → Debe mostrar 10+ empresas
   ```

2. Verificar clientes:
   ```
   SaaS Management → Clients → Clients
   → Cada cliente debe tener:
     • Tab "Local Companies" con su empresa
     • Companies count: 1
   ```

3. Verificar licencias:
   ```
   SaaS Management → Licensing → License Records
   → Debe haber registros para todas las empresas
   ```

✅ **Sistema escala correctamente con múltiples clientes**

---

## Prueba 7: Reglas de Seguridad

**Objetivo**: Verificar que las reglas de seguridad funcionan correctamente.

### Ejecución

**Test 1: Usuario normal - Solo su empresa**
```
1. Iniciar sesión como usuario no-admin de una empresa
2. Ir a SaaS Management → Companies
3. Verificar que SOLO ve su propia empresa
```

**Test 2: SaaS Manager - Todas las empresas**
```
1. Crear usuario con grupo "SaaS / Manager"
2. Iniciar sesión
3. Ir a SaaS Management → Companies
4. Debe ver TODAS las empresas SaaS
```

**Test 3: Admin - Acceso total**
```
1. Iniciar sesión como Admin
2. Debe tener acceso a TODO sin restricciones
```

### Verificación

✅ **Usuarios regulares: acceso restringido**
✅ **SaaS Managers: acceso a gestión completa**
✅ **Admins: acceso sin restricciones**

---

## Prueba 8: Cron Jobs Automáticos

**Objetivo**: Verificar que el cron job crea snapshots de licencias automáticamente.

### Setup

1. Configurar cron para ejecución inmediata:
   ```
   Settings → Technical → Automation → Scheduled Actions
   → Buscar: "SaaS: Create Monthly License Records"
   → Cambiar "Interval Number" a 1 minuto (temporalmente)
   → Activar
   ```

### Ejecución

1. Esperar 1 minuto
2. Verificar logs:
   ```bash
   tail -f /var/log/odoo/odoo-server.log | grep -i "license"
   ```

### Verificación

1. Ver registros creados:
   ```
   SaaS Management → Licensing → License Records
   → Filtrar por "Date" = Hoy
   → Debe haber registros para:
     ✓ Todas las empresas SaaS activas con suscripción
     ✓ Con User Count actualizado
     ✓ Con Company Count = 1
   ```

2. Verificar que no se duplican:
   ```
   → Ejecutar cron nuevamente
   → NO deben crearse registros duplicados para la misma fecha
   ```

✅ **Cron job funciona correctamente**
✅ **No hay duplicados**
✅ **Datos calculados correctamente**

---

## Matriz de Pruebas

| Prueba | Componente | Crítico | Estado |
|--------|-----------|---------|--------|
| 1. Creación básica | sale_order.py | ✓ | ⬜ |
| 2. Aislamiento de datos | security.xml | ✓ | ⬜ |
| 3. Licenciamiento | saas_license.py | ✓ | ⬜ |
| 4. Asignación permisos | product_permissions | ✓ | ⬜ |
| 5. Uso plantillas | res_company.py | - | ⬜ |
| 6. Múltiples clientes | Escalabilidad | ✓ | ⬜ |
| 7. Seguridad | security.xml | ✓ | ⬜ |
| 8. Cron jobs | saas_license.py | ✓ | ⬜ |

**Leyenda**: ✓ = Crítico, - = Opcional, ⬜ = Pendiente, ✅ = Pasado, ❌ = Fallado

---

## Troubleshooting Común

### Problema: Empresa no se crea

**Verificar**:
```python
# En Odoo shell (odoo-bin shell -d your_database)
product = env['product.template'].search([('name', '=', 'Tu Producto')])
print(f"is_module_access: {product.is_module_access}")
print(f"auto_create_company: {product.auto_create_company}")

# Debe ser True en ambos
```

### Problema: Usuario no ve datos restringidos

**Verificar reglas activas**:
```
Settings → Technical → Security → Record Rules
→ Buscar "Multi-Company"
→ Todas deben estar Active = ☑
```

### Problema: Licencias no se crean

**Verificar cron**:
```
Settings → Technical → Automation → Scheduled Actions
→ "SaaS: Create Monthly License Records"
→ Verificar:
  • Active: ☑
  • Model: saas.license
  • State: code
```

---

## Reporte de Bugs

Si encuentras un bug durante las pruebas, reporta con:

1. **Descripción del problema**
2. **Pasos para reproducir**
3. **Resultado esperado**
4. **Resultado actual**
5. **Logs del servidor** (si aplica)
6. **Screenshots** (si aplica)

---

**Versión**: 18.0.1.0.0
**Última actualización**: 2025-11-17
