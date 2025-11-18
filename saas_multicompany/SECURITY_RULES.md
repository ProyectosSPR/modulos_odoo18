# Multi-Company Security Rules - Documentation

## Resumen

Este módulo implementa un modelo de seguridad **restrictivo y granular** para empresas SaaS multi-tenant:

- **Empresa Propia**: Acceso completo (leer, escribir, crear, eliminar*)
- **Empresa Padre**: Solo lectura (configurada en `parent_company_id`)
- **Otras Empresas**: Sin acceso (máxima seguridad de datos)

> *Los usuarios NO pueden eliminar su propia empresa por seguridad

## Principio de Funcionamiento

### Concepto Clave: `company_id` y `parent_company_id`

- **`user.company_id`**: Es la empresa **principal/actual** del usuario (una sola)
- **`company.parent_company_id`**: Es la empresa **padre** que esta empresa puede ver (solo lectura)

### Estrategia de Seguridad

Para cada modelo (Partners, Products, Sales Orders, Invoices, etc.), se crean **DOS reglas separadas**:

#### 1. Regla de LECTURA (Read-only)
```xml
<field name="domain_force">[
    '|', ('company_id', '=', False),
    '|', ('company_id', '=', user.company_id.id),
         ('company_id', '=', user.company_id.parent_company_id.id)
]</field>
<field name="perm_read" eval="True"/>
<field name="perm_write" eval="False"/>
<field name="perm_create" eval="False"/>
<field name="perm_unlink" eval="False"/>
```

**¿Qué hace?**
- Permite **ver** registros de:
  - Su propia empresa (`user.company_id`)
  - La empresa padre configurada (`user.company_id.parent_company_id`)
  - Registros globales sin empresa (`company_id = False`)
- **NO** permite ver registros de otras empresas
- **NO** permite editar, crear o eliminar

#### 2. Regla de ESCRITURA (Write/Create/Delete)
```xml
<field name="domain_force">[
    '|', ('company_id', '=', False),
         ('company_id', '=', user.company_id.id)
]</field>
<field name="perm_read" eval="False"/>
<field name="perm_write" eval="True"/>
<field name="perm_create" eval="True"/>
<field name="perm_unlink" eval="True"/>
```

**¿Qué hace?**
- Permite **editar, crear y eliminar** SOLO registros de:
  - Su propia empresa (`user.company_id`)
  - Registros globales sin empresa (`company_id = False`)
- **NO** puede modificar registros de la empresa padre
- **NO** puede modificar registros de otras empresas
- **NO** otorga permisos de lectura (ya cubiertos por regla anterior)

## Configuración Inicial

### Paso 1: Configurar la Empresa Padre

1. Ve a: **Ajustes → Empresas**
2. Abre la empresa SaaS (por ejemplo "Cliente A")
3. Ve a la pestaña **"SaaS Information"**
4. En la sección **"Security & Access Control"**:
   - Selecciona la **"Parent Company"** (empresa principal/matriz)
   - Ejemplo: Selecciona "AutomateAI"
5. Guarda los cambios

### Paso 2: Configurar Usuarios

Los usuarios de la empresa SaaS deben tener configurado:
- **"Empresa Actual"**: Su empresa SaaS (ej: Cliente A)
- **NO** es necesario agregarlos a "Empresas permitidas" de la empresa padre
- El acceso de solo lectura se otorga automáticamente a través del campo `parent_company_id`

### Importante:
- Si **NO configuras** el `parent_company_id`, los usuarios solo verán datos de su propia empresa (máxima seguridad)
- Los datos de otras empresas SaaS **NUNCA** son visibles, incluso si comparten la misma empresa padre

## Ejemplo Práctico

### Escenario:
- **Empresa Principal**: "AutomateAI" (ID: 1) - Empresa matriz
- **Empresa SaaS Cliente A**: "Cliente A" (ID: 2) - Con `parent_company_id` = 1
- **Empresa SaaS Cliente B**: "Cliente B" (ID: 3) - Con `parent_company_id` = 1
- **Usuario Juan**: Usuario de "Cliente A" con:
  - `company_id` = 2 (su empresa)
  - `company.parent_company_id` = 1 (AutomateAI)

### Comportamiento de Juan:

| Acción | AutomateAI (ID: 1) | Cliente A (ID: 2) | Cliente B (ID: 3) |
|--------|-------------------|-------------------|-------------------|
| **Ver** clientes | ✅ SÍ (solo lectura) | ✅ SÍ | ❌ **NO** |
| **Editar** clientes | ❌ NO | ✅ SÍ | ❌ **NO** |
| **Crear** clientes | ❌ NO | ✅ SÍ | ❌ **NO** |
| **Eliminar** clientes | ❌ NO | ✅ SÍ | ❌ **NO** |

### ¿Qué ve Juan en la interfaz?

1. **Lista de Clientes**: Ve SOLO clientes de:
   - ✅ AutomateAI (empresa padre - solo lectura)
   - ✅ Cliente A (su empresa - acceso completo)
   - ❌ NO ve clientes de Cliente B ni ninguna otra empresa

2. **Al abrir un cliente de AutomateAI**:
   - ✅ Puede ver todos los campos
   - ❌ Botón "Editar" está **deshabilitado**
   - ❌ No puede crear nuevos clientes para AutomateAI

3. **Al abrir un cliente de Cliente A** (su empresa):
   - ✅ Puede ver y **editar** libremente
   - ✅ Puede crear nuevos clientes
   - ✅ Puede eliminar clientes

4. **Intentando acceder a Cliente B**:
   - ❌ No aparecen en ninguna lista
   - ❌ Acceso denegado si intenta acceso directo por URL

## Modelos Cubiertos

Las reglas se aplican a los siguientes modelos:

### 1. **Partners (Contactos/Clientes)**
- Modelo: `res.partner`
- Reglas: `rule_partner_read_multicompany` + `rule_partner_write_own_company`

### 2. **Companies (Empresas)**
- Modelo: `res.company`
- Reglas: `rule_company_read_multicompany` + `rule_company_write_own`
- **Nota especial**: Los usuarios NO pueden crear empresas, solo editarlas

### 3. **Products (Productos)**
- Modelo: `product.template`
- Reglas: `rule_product_read_multicompany` + `rule_product_write_own_company`

### 4. **Sale Orders (Órdenes de Venta)**
- Modelo: `sale.order`
- Reglas: `rule_sale_order_read_multicompany` + `rule_sale_order_write_own_company`
- **Grupos**: Solo usuarios con rol de ventas (`sales_team.group_sale_salesman`)

### 5. **Invoices (Facturas)**
- Modelo: `account.move`
- Reglas: `rule_invoice_read_multicompany` + `rule_invoice_write_own_company`
- **Grupos**: Solo usuarios con permisos de facturación (`account.group_account_invoice`)

## Excepciones - Usuarios con Acceso Completo

### ⚠️ IMPORTANTE: Las reglas restrictivas NO aplican a:

#### 1. Administradores del Sistema
Los usuarios con el grupo `base.group_system` (Administración → Ajustes) tienen **acceso completo** a todos los datos de todas las empresas:

```xml
<field name="domain_force">[(1, '=', 1)]</field>
```

**¿Qué significa esto?**
- ✅ Ven TODAS las empresas y TODOS los datos
- ✅ Pueden editar, crear y eliminar en cualquier empresa
- ✅ No están limitados por `parent_company_id`
- ✅ Bypass completo de las reglas de seguridad multi-empresa

#### 2. SaaS Managers
Los usuarios con el grupo `saas_management.group_saas_manager` también tienen **acceso completo** a todas las empresas SaaS.

**¿Quiénes son SaaS Managers?**
- Usuarios que gestionan clientes SaaS
- Típicamente personal interno de la empresa principal
- Tienen permisos especiales para administrar todas las empresas SaaS

### 📋 Resumen de Permisos por Grupo

| Grupo de Usuario | Empresa Propia | Empresa Padre | Otras Empresas SaaS |
|-----------------|----------------|---------------|---------------------|
| **Usuario Normal** | ✅ Acceso completo | 👁️ Solo lectura | ❌ Sin acceso |
| **SaaS Manager** | ✅ Acceso completo | ✅ Acceso completo | ✅ Acceso completo |
| **Administrador** | ✅ Acceso completo | ✅ Acceso completo | ✅ Acceso completo |

### ⚙️ Configuración de Grupos

Para otorgar acceso completo a un usuario:

1. **Hacer Administrador**:
   - Ve a: Ajustes → Usuarios → [Usuario]
   - Pestaña "Derechos de Acceso"
   - Marcar: "Administración → Ajustes" (`base.group_system`)

2. **Hacer SaaS Manager**:
   - Ve a: Ajustes → Usuarios → [Usuario]
   - Pestaña "Derechos de Acceso"
   - Marcar: "SaaS Management → Manager" (`saas_management.group_saas_manager`)

## Registros sin Empresa (`company_id = False`)

Los registros que **no tienen empresa asignada** son accesibles para todos:

```xml
('company_id', '=', False)
```

Esto es útil para:
- Datos globales/compartidos
- Configuraciones del sistema
- Templates

## Cómo Funciona en Código

### Al intentar leer datos:
```python
# Usuario Juan (company_id=2, company_ids=[1,2])
partners = env['res.partner'].search([])
# Resultado: Ve partners de empresas 1 y 2 (gracias a rule_partner_read_multicompany)
```

### Al intentar editar datos:
```python
# Usuario Juan intenta editar un partner de empresa 1
partner_empresa_1.write({'name': 'Nuevo Nombre'})
# Resultado: ACCESS ERROR - La regla rule_partner_write_own_company lo bloquea
```

```python
# Usuario Juan intenta editar un partner de empresa 2 (su empresa)
partner_empresa_2.write({'name': 'Nuevo Nombre'})
# Resultado: ✅ ÉXITO - La regla rule_partner_write_own_company lo permite
```

## Troubleshooting

### Problema: Los usuarios no ven datos de la empresa principal

**Solución**: Verificar que la empresa SaaS tenga configurado el campo `parent_company_id`:
1. Ir a: Ajustes → Empresas
2. Abrir la empresa SaaS del usuario
3. Pestaña "SaaS Information" → Security & Access Control
4. Asegurarse de que "Parent Company" esté seleccionada
5. Guardar y pedirle al usuario que actualice la página (F5)

### Problema: Los usuarios pueden editar datos de la empresa principal

**Solución**: Verificar que:
1. Las reglas estén cargadas correctamente
2. El atributo `noupdate="0"` esté presente en el XML (permite actualizaciones)
3. El módulo esté actualizado después de modificar las reglas

### Problema: Los administradores no pueden crear empresas

**Solución**: Esto es por diseño. Si necesitas que usuarios específicos puedan crear empresas, agrega una nueva regla:

```xml
<record id="rule_company_create_admin" model="ir.rule">
    <field name="name">Company: Admin Can Create</field>
    <field name="model_id" ref="base.model_res_company"/>
    <field name="domain_force">[(1, '=', 1)]</field>
    <field name="groups" eval="[(4, ref('base.group_system'))]"/>
    <field name="perm_create" eval="True"/>
</record>
```

## Personalización

### Agregar más modelos

Para agregar reglas a otros modelos, sigue este patrón:

```xml
<!-- READ Rule -->
<record id="rule_MODELO_read_multicompany" model="ir.rule">
    <field name="name">MODELO: Read Multi-Company Data</field>
    <field name="model_id" ref="MODULO.model_NOMBRE_MODELO"/>
    <field name="domain_force">['|', ('company_id', '=', False), ('company_id', 'in', user.company_ids.ids)]</field>
    <field name="groups" eval="[(4, ref('GRUPO_APROPIADO'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>
    <field name="perm_create" eval="False"/>
    <field name="perm_unlink" eval="False"/>
</record>

<!-- WRITE Rule -->
<record id="rule_MODELO_write_own_company" model="ir.rule">
    <field name="name">MODELO: Write Only Own Company</field>
    <field name="model_id" ref="MODULO.model_NOMBRE_MODELO"/>
    <field name="domain_force">['|', ('company_id', '=', False), ('company_id', '=', user.company_id.id)]</field>
    <field name="groups" eval="[(4, ref('GRUPO_APROPIADO'))]"/>
    <field name="perm_read" eval="False"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="True"/>
</record>
```

## Referencias Técnicas

- **Documentación Odoo**: https://www.odoo.com/documentation/18.0/developer/reference/backend/security.html#record-rules
- **Campo `company_id`**: Campo Many2one hacia `res.company`
- **Operadores de dominio**:
  - `=`: Igual
  - `in`: Está en la lista
  - `|`: Operador OR

## Notas Importantes

1. **Orden de evaluación**: Odoo evalúa TODAS las reglas aplicables. Si una regla niega el acceso, el acceso se niega.

2. **Combinación de reglas**: Las reglas con diferentes permisos se combinan:
   - La regla READ da permisos de lectura
   - La regla WRITE da permisos de escritura (solo para `user.company_id`)
   - Ambas reglas trabajan juntas

3. **Actualización de reglas**: Si modificas las reglas, asegúrate de:
   - Actualizar el módulo `saas_multicompany`
   - Reiniciar el servidor Odoo si es necesario

4. **Seguridad por defecto**: Es mejor ser **restrictivo por defecto** y agregar permisos específicos según sea necesario.
