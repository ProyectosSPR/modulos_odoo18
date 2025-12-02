# Changelog - Módulo Wizard de Declaraciones Fiscales

## [18.0.1.0.0] - 2025-12-02

### ✅ Correcciones Aplicadas

#### 1. Vista del Wizard - Header con barra de progreso
**Problema**: Botones en header con `name="state"` causaban error de validación
```
state no es una acción válida en mx.tax.declaration.wizard
```

**Solución**: Reemplazados los botones por badges de Bootstrap 5
- Antes: `<button name="state" type="object"...>`
- Después: `<span class="badge text-bg-primary">...`
- Uso de badges con clases de Odoo 18: `text-bg-primary`, `text-bg-secondary`, `text-bg-light`, `text-bg-success`

#### 2. Acción del Wizard
**Problema**: Referencia a `model_mx_tax_declaration` antes de que exista
```xml
<field name="binding_model_id" ref="model_mx_tax_declaration"/>
```

**Solución**: Eliminado `binding_model_id` y `binding_view_types`
- El wizard se accede desde el menú, no necesita binding en el formulario

#### 3. Importación de traducción
**Problema**: Función `_()` no importada en `mx_tax_declaration_invoice_line.py`

**Solución**: Agregado `_` al import
```python
from odoo import fields, models, api, _
```

#### 4. Message post en TransientModel
**Problema**: `message_post()` llamado en wizard (TransientModel no tiene mail.thread)

**Solución**: Eliminada la línea `self.message_post()` del wizard
- Los mensajes se envían solo en el modelo permanente `mx.tax.declaration`

#### 5. Referencia a acción externa
**Problema**: Referencia incorrecta a acción del wizard en vista de declaración

**Solución**: Agregado prefijo del módulo
```xml
name="%(l10n_mx_tax_declaration_wizard.action_mx_tax_declaration_wizard)d"
```

### ✅ Características Implementadas

- [x] Wizard multi-paso (6 pasos)
- [x] Modelo de declaración permanente con estados
- [x] Líneas de facturas en declaración
- [x] Resultados de cálculos almacenados
- [x] Vistas completas (List, Form, Kanban, Search)
- [x] Seguridad (Grupos y permisos)
- [x] Menús organizados
- [x] Validaciones y restricciones
- [x] Integración con módulo base
- [x] Soporte multi-compañía
- [x] Chatter en declaraciones

### 📝 Archivos Modificados

1. `wizard/mx_tax_declaration_wizard_views.xml` - Corregida barra de progreso
2. `wizard/mx_tax_declaration_wizard_views.xml` - Eliminado binding_model_id
3. `models/mx_tax_declaration_invoice_line.py` - Agregado import de _
4. `wizard/mx_tax_declaration_wizard.py` - Eliminado message_post
5. `views/mx_tax_declaration_views.xml` - Corregida referencia a acción

### 🧪 Estado de Testing

- [x] Sintaxis Python válida
- [ ] Instalación en Odoo (pendiente)
- [ ] Prueba de wizard paso a paso (pendiente)
- [ ] Prueba de cálculos (pendiente)
- [ ] Prueba de permisos (pendiente)

### 📋 Próximos Pasos

1. Instalar módulo en Odoo
2. Crear datos de prueba (obligaciones + reglas de cálculo)
3. Probar wizard completo
4. Verificar cálculos con facturas reales
5. Probar estados y flujo de aprobación

### 🔧 Compatibilidad

- **Odoo**: 18.0
- **Python**: 3.10+
- **Dependencias**:
  - `l10n_mx_tax_declaration_base` (requerido)
  - `account` (requerido)
  - `mail` (requerido)
  - `account_reconcile_oca` (opcional)

---

**Versión**: 18.0.1.0.0
**Fecha**: 2025-12-02
**Estado**: Listo para instalación
