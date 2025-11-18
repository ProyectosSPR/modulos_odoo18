# Changelog - Security Model Update

## Versión 2.0 - Modelo de Seguridad Restrictivo

### 🔒 Cambios Principales

Se ha implementado un **nuevo modelo de seguridad restrictivo** que mejora significativamente la privacidad y seguridad de datos entre empresas SaaS.

### 🆕 Nuevo Campo: `parent_company_id`

**Archivo**: `models/res_company.py`

Se agregó un nuevo campo a `res.company`:

```python
parent_company_id = fields.Many2one(
    'res.company',
    string='Parent Company',
    help='Parent company that this SaaS company can view (read-only access)',
    ondelete='restrict'
)
```

**Propósito**: Define qué empresa puede ser vista (solo lectura) por los usuarios de esta empresa SaaS.

### 📊 Modelo de Acceso

#### Antes (v1.0):
- ❌ Los usuarios veían datos de TODAS las empresas en `company_ids`
- ❌ Riesgo: Los usuarios de "Cliente A" podían ver datos de "Cliente B"
- ❌ Solo se controlaba escritura, no lectura

#### Ahora (v2.0):
- ✅ Los usuarios solo ven datos de su propia empresa
- ✅ Opcionalmente pueden ver datos de la empresa padre (solo lectura)
- ✅ **NUNCA** ven datos de otras empresas SaaS
- ✅ Control granular de lectura y escritura

### 🔐 Reglas de Seguridad Actualizadas

**Archivo**: `security/saas_multicompany_security.xml`

Se reescribieron completamente las reglas de seguridad para:

#### Partners (Contactos)
- **READ**: `company_id = user.company_id` O `company_id = user.company_id.parent_company_id`
- **WRITE**: `company_id = user.company_id` (solo su empresa)

#### Companies (Empresas)
- **READ**: Puede ver su empresa y la empresa padre
- **WRITE**: Solo puede modificar su propia empresa
- **DELETE**: ❌ NO puede eliminar su empresa (por seguridad)

#### Products (Productos)
- **READ**: Propia empresa + empresa padre (solo lectura)
- **WRITE/CREATE/DELETE**: Solo su propia empresa

#### Sale Orders (Órdenes de Venta)
- **READ**: Propia empresa + empresa padre (solo lectura)
- **WRITE/CREATE/DELETE**: Solo su propia empresa

#### Invoices (Facturas)
- **READ**: Propia empresa + empresa padre (solo lectura)
- **WRITE/CREATE/DELETE**: Solo su propia empresa

### 🎨 Cambios en la Interfaz

**Archivo**: `views/res_company_views.xml`

Se agregó una nueva sección en la pestaña "SaaS Information" de las empresas:

```xml
<group string="Security & Access Control">
    <field name="parent_company_id"
           options="{'no_create': True}"
           domain="[('id', '!=', id), ('is_saas_company', '=', False)]"/>
    <p class="text-muted">
        Users of this company can view (read-only) data from the parent company.
        Leave empty if you don't want users to see data from other companies.
    </p>
</group>
```

**Características**:
- Solo permite seleccionar empresas NO SaaS como padre (empresas principales)
- No permite seleccionarse a sí misma
- Texto explicativo para el usuario

### 📖 Documentación

Se actualizó completamente `SECURITY_RULES.md` con:
- Explicación del nuevo modelo de seguridad
- Guía de configuración paso a paso
- Ejemplos prácticos con múltiples empresas
- Sección de troubleshooting actualizada
- Diagramas de permisos

### 🔄 Migración

**¿Necesitas migrar?**

Si ya tienes empresas SaaS creadas:

1. **Opcional**: Configura el campo `parent_company_id` en cada empresa SaaS
   - Ve a: Ajustes → Empresas → [Tu Empresa SaaS]
   - Pestaña "SaaS Information"
   - Selecciona la empresa padre

2. **Importante**: Los usuarios YA NO necesitan estar en `company_ids` de la empresa padre
   - El acceso de lectura se otorga automáticamente vía `parent_company_id`
   - Simplifica la gestión de usuarios

### ⚠️ Cambios de Comportamiento

#### Impacto en Usuarios Existentes:

1. **Si antes veían múltiples empresas SaaS**:
   - Ahora solo verán SU propia empresa
   - Esto es CORRECTO y más seguro

2. **Si necesitan ver la empresa padre**:
   - Configura `parent_company_id` en su empresa
   - Tendrán acceso de solo lectura automáticamente

3. **Administradores del sistema**:
   - Mantienen acceso completo a todo
   - No afectados por estos cambios

### 🧪 Pruebas Recomendadas

Después de actualizar el módulo:

1. **Test 1: Aislamiento entre empresas SaaS**
   - Usuario de Empresa A no debe ver datos de Empresa B
   - ✅ Verificar que las listas estén filtradas

2. **Test 2: Acceso a empresa padre**
   - Configurar `parent_company_id` en Empresa A
   - Usuario de Empresa A debe VER datos de la empresa padre
   - Usuario NO debe poder EDITAR datos de la empresa padre

3. **Test 3: Eliminación de empresa**
   - Usuarios normales NO deben poder eliminar su empresa
   - Solo administradores pueden eliminar empresas

### 📝 Archivos Modificados

```
saas_multicompany/
├── models/
│   └── res_company.py          [MODIFICADO] - Agregado parent_company_id
├── security/
│   └── saas_multicompany_security.xml  [REESCRITO] - Nuevas reglas restrictivas
├── views/
│   └── res_company_views.xml   [MODIFICADO] - Campo parent_company_id en UI
├── SECURITY_RULES.md           [ACTUALIZADO] - Nueva documentación
└── CHANGELOG_SECURITY.md       [NUEVO] - Este archivo
```

### 🚀 Instalación

1. Actualizar el módulo:
   ```bash
   # En Odoo: Apps → saas_multicompany → Actualizar
   ```

2. Configurar empresas (opcional):
   ```
   Ajustes → Empresas → [Empresa SaaS] → SaaS Information → Parent Company
   ```

3. Verificar reglas:
   ```
   Ajustes → Técnico → Seguridad → Reglas de Registro
   Buscar: "Partner: Read Own and Parent Company"
   ```

### ❓ Soporte

Para preguntas o problemas:
- Consulta: `SECURITY_RULES.md` para documentación completa
- Revisa: La sección Troubleshooting del mismo documento
