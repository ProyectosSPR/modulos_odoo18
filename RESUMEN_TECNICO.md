# 🔧 RESUMEN TÉCNICO
## Sistema de Declaraciones Fiscales SAT México

**Para desarrolladores que continúan el proyecto**

---

## 📦 PAQUETE COMPLETO PARA MIGRACIÓN

### Archivos a Copiar

```bash
# Desde PC origen, copiar estos directorios:
modulos_odoo18/
├── l10n_mx_tax_declaration_base/          # Módulo principal
├── l10n_mx_tax_declaration_sat_sync/      # Módulo integración
├── GUIA_COMPLETA_IMPLEMENTACION.md        # Guía completa
├── DECLARACIONES_FISCALES_README.md       # README general
├── INICIO_RAPIDO.md                       # Inicio rápido
└── RESUMEN_TECNICO.md                     # Este archivo
```

---

## 🗄️ ESTRUCTURA DE BASE DE DATOS

### Tablas Creadas

El sistema crea las siguientes tablas en PostgreSQL:

```sql
-- Catálogos (maestros)
mx_tax_obligation_type          -- Tipos de obligación (IVA, ISR, etc.)
mx_tax_periodicity              -- Periodicidades (mensual, etc.)

-- Configuración por empresa
mx_tax_obligation               -- Obligaciones configuradas
mx_tax_calculation_rule         -- Reglas de cálculo

-- account.move se extiende con nuevos campos (no nueva tabla)
-- res.company se extiende con nuevos campos (no nueva tabla)
```

### Queries Útiles

```sql
-- Ver obligaciones instaladas
SELECT id, name, code, category
FROM mx_tax_obligation_type
ORDER BY sequence;

-- Ver obligaciones configuradas por empresa
SELECT o.id, c.name as company, ot.name as obligation,
       p.code as periodicity, o.deadline_day
FROM mx_tax_obligation o
JOIN res_company c ON o.company_id = c.id
JOIN mx_tax_obligation_type ot ON o.obligation_type_id = ot.id
JOIN mx_tax_periodicity p ON o.periodicity_id = p.id
WHERE o.active = true;

-- Ver reglas de cálculo
SELECT id, name, obligation_id, calculation_type,
       sequence, is_final_amount
FROM mx_tax_calculation_rule
WHERE active = true
ORDER BY obligation_id, sequence;

-- Ver facturas marcadas para declaración
SELECT id, name, partner_id, amount_total,
       include_in_tax_declaration,
       tax_declaration_status,
       tax_declaration_period
FROM account_move
WHERE include_in_tax_declaration = true
  AND state = 'posted';

-- Contar facturas por estado de declaración
SELECT tax_declaration_status, COUNT(*)
FROM account_move
WHERE include_in_tax_declaration = true
GROUP BY tax_declaration_status;
```

---

## 🎨 ARQUITECTURA DE CÓDIGO

### Patrón de Herencia en Odoo

```python
# Modelo nuevo (standalone)
class MxTaxObligation(models.Model):
    _name = 'mx.tax.obligation'
    _description = 'Obligación Fiscal'
    # ... campos

# Extensión de modelo existente
class AccountMove(models.Model):
    _inherit = 'account.move'
    # ... nuevos campos

# Modelo transient (wizard)
class MxTaxDeclarationWizard(models.TransientModel):
    _name = 'mx.tax.declaration.wizard'
    _description = 'Wizard Declaración'
    # ... campos y métodos
```

### Convenciones de Naming

```python
# Modelos
mx_tax_obligation           # snake_case para _name
MxTaxObligation            # PascalCase para clase

# Campos
obligation_type_id         # _id para Many2one
calculation_rule_ids       # _ids para One2many/Many2many

# Métodos
def action_create_declaration(self):    # action_ para botones
def _compute_total(self):               # _compute_ para computed
def _check_validity(self):              # _check_ para constraints

# External IDs
view_mx_tax_obligation_form             # vista form
view_mx_tax_obligation_list             # vista list (no tree)
action_mx_tax_obligation                # acción
menu_mx_tax_declaration_root            # menú raíz
```

### Safe Eval - Contexto de Ejecución

```python
# En mx.tax.calculation.rule._calculate_formula()

eval_context = {
    'invoices': invoices,          # recordset filtrado
    'payments': payments,          # recordset de pagos
    'rules': rules_results,        # dict {rule_id: result}
    'company': self.company_id,    # res.company record
    'period_start': date_start,    # date
    'period_end': date_end,        # date
    'sum': sum,                    # función built-in
    'len': len,
    'abs': abs,
    'min': min,
    'max': max,
    'round': round,
}

result = safe_eval(self.python_formula, eval_context)
```

---

## 📋 DEPENDENCIES

### Python Packages

```
# Ya incluidas en Odoo 18:
lxml            # Para XML
reportlab       # Para PDF (cuando se implemente)
xlsxwriter      # Para Excel (cuando se implemente)
```

### Odoo Modules

```python
# __manifest__.py dependencies:

# Para l10n_mx_tax_declaration_base:
'depends': [
    'account',      # Odoo core
    'l10n_mx',      # Localización México (core)
],

# Para l10n_mx_tax_declaration_sat_sync:
'depends': [
    'l10n_mx_tax_declaration_base',      # Nuestro módulo
    'l10n_mx_sat_sync_itadmin',          # Custom
],

# Para próximo wizard (cuando se implemente):
'depends': [
    'l10n_mx_tax_declaration_base',
    'account_reconcile_oca',             # OCA
    'account_reconcile_model_oca',       # OCA
],
```

---

## 🔐 GRUPOS DE SEGURIDAD

### Jerarquía de Grupos

```
base.group_user (Odoo core)
    ↓ implied_ids
group_mx_tax_declaration_user
    ↓ implied_ids
group_mx_tax_declaration_accountant
    ↓ implied_ids
group_mx_tax_declaration_manager
```

### Permisos por Grupo

| Modelo | User | Accountant | Manager |
|--------|------|------------|---------|
| mx.tax.obligation.type | Read | Read | Full |
| mx.tax.periodicity | Read | Read | Full |
| mx.tax.obligation | Read | Create/Write | Full |
| mx.tax.calculation.rule | Read | Create/Write | Full |

### Código de Grupos

```xml
<!-- En security/security.xml -->

<record id="group_mx_tax_declaration_user" model="res.groups">
    <field name="name">Usuario: Ver declaraciones</field>
    <field name="category_id" ref="module_category_mx_tax_declaration"/>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>

<record id="group_mx_tax_declaration_accountant" model="res.groups">
    <field name="name">Contador: Crear declaraciones</field>
    <field name="implied_ids" eval="[
        (4, ref('group_mx_tax_declaration_user')),
        (4, ref('account.group_account_user'))
    ]"/>
</record>
```

---

## 🧪 DATOS DE PRUEBA

### Script SQL para Testing

```sql
-- Crear obligación IVA de prueba
INSERT INTO mx_tax_obligation (
    company_id, obligation_type_id, periodicity_id,
    deadline_day, auto_include_invoices, invoice_type_filter,
    create_uid, write_uid, create_date, write_date
)
SELECT
    1,  -- company_id (ajustar según tu DB)
    (SELECT id FROM mx_tax_obligation_type WHERE code = 'IVA-01'),
    (SELECT id FROM mx_tax_periodicity WHERE code = '01'),
    17,
    true,
    'all',
    2,  -- admin user
    2,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM mx_tax_obligation
    WHERE obligation_type_id = (SELECT id FROM mx_tax_obligation_type WHERE code = 'IVA-01')
);

-- Marcar facturas existentes para declaración (testing)
UPDATE account_move
SET include_in_tax_declaration = true,
    tax_declaration_status = 'pending',
    tax_declaration_period = invoice_date
WHERE move_type IN ('out_invoice', 'in_invoice')
  AND state = 'posted'
  AND invoice_date >= '2025-01-01'
  AND invoice_date < '2025-02-01'
  AND include_in_tax_declaration IS NULL;
```

### Python para Testing (desde shell)

```python
# Acceder a shell de Odoo:
# odoo shell -d tu_database

# Crear obligación de prueba
Obligation = env['mx.tax.obligation']
ObligationType = env['mx.tax.obligation.type']
Periodicity = env['mx.tax.periodicity']

iva_type = ObligationType.search([('code', '=', 'IVA-01')], limit=1)
monthly = Periodicity.search([('code', '=', '01')], limit=1)

obligation = Obligation.create({
    'obligation_type_id': iva_type.id,
    'periodicity_id': monthly.id,
    'deadline_day': 17,
    'auto_include_invoices': True,
})

print(f"Obligación creada: {obligation.name}")

# Crear regla de cálculo de prueba
Rule = env['mx.tax.calculation.rule']

rule = Rule.create({
    'name': 'IVA Causado Test',
    'obligation_id': obligation.id,
    'calculation_type': 'filtered_sum',
    'source_model': 'account.move',
    'field_to_sum': 'amount_tax',
    'domain_filter': "[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]",
    'is_subtotal': True,
    'show_in_report': True,
})

print(f"Regla creada: {rule.name}")

# Probar cálculo
from datetime import date
invoices = env['account.move'].search([
    ('include_in_tax_declaration', '=', True),
    ('state', '=', 'posted'),
])

result = rule.calculate(
    invoices=invoices,
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31),
)

print(f"Resultado del cálculo: {result}")
```

---

## 🐛 DEBUG TIPS

### Activar Logging Detallado

```python
# En cualquier modelo, agregar al inicio:
import logging
_logger = logging.getLogger(__name__)

# En métodos:
_logger.info("Mensaje informativo")
_logger.warning("Advertencia")
_logger.error("Error")
_logger.debug("Debug detallado")

# Ver logs:
tail -f /var/log/odoo/odoo.log | grep "mx.tax"
```

### Breakpoint en Código

```python
# Método 1: pdb (Python debugger)
import pdb; pdb.set_trace()

# Método 2: ipdb (mejor interfaz)
import ipdb; ipdb.set_trace()

# Método 3: Odoo debugger
import odoo
odoo.tools.config['debug'] = True
```

### Inspeccionar Recordset

```python
# En shell o debugger:
invoices = self.env['account.move'].search([...])

# Ver campos
print(invoices.mapped('name'))
print(invoices.mapped('amount_total'))

# Ver IDs
print(invoices.ids)

# Ver primer registro
print(invoices[0].name)

# Contar
print(len(invoices))

# Filtrar en Python
filtered = invoices.filtered(lambda inv: inv.amount_total > 1000)

# Ordenar
sorted_invs = invoices.sorted(key=lambda inv: inv.invoice_date)
```

---

## 📊 MÉTRICAS DEL PROYECTO

### Líneas de Código

```bash
# Contar líneas Python
find l10n_mx_tax_declaration_base/models -name "*.py" -exec wc -l {} + | tail -1
# Resultado: ~1,200 líneas

# Contar líneas XML
find l10n_mx_tax_declaration_base -name "*.xml" -exec wc -l {} + | tail -1
# Resultado: ~1,800 líneas

# Total módulo base: ~3,000 líneas
# Total módulo sync: ~200 líneas
```

### Complejidad

```
Modelos creados:          6
Modelos extendidos:       2
Vistas XML:               9
Registros de datos:       32
Métodos principales:      ~40
Campos nuevos:           ~50
```

---

## 🚀 PRÓXIMO DESARROLLO: WIZARD

### Estructura Propuesta

```
l10n_mx_tax_declaration_wizard/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── mx_tax_declaration_wizard.py     # TransientModel
│   ├── mx_tax_declaration.py            # Model (persistente)
│   ├── mx_tax_declaration_line.py       # Líneas
│   └── mx_tax_declaration_calculation.py # Resultados
├── views/
│   ├── mx_tax_declaration_wizard_views.xml
│   ├── mx_tax_declaration_views.xml
│   └── menu_views.xml
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
└── report/
    └── tax_declaration_report.xml       # QWeb PDF
```

### Flujo del Wizard (Pseudocódigo)

```python
class MxTaxDeclarationWizard(models.TransientModel):
    _name = 'mx.tax.declaration.wizard'

    state = fields.Selection([
        ('step1', 'Configuración'),
        ('step2', 'Facturas'),
        ('step3', 'Conciliación'),
        ('step4', 'No Deducibles'),
        ('step5', 'Cálculos'),
        ('step6', 'Reporte'),
    ], default='step1')

    # Step 1: Config
    period_start = fields.Date()
    period_end = fields.Date()
    obligation_ids = fields.Many2many('mx.tax.obligation')

    # Step 2: Invoices
    invoice_ids = fields.Many2many('account.move')
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    invoice_total = fields.Monetary(compute='_compute_invoice_total')

    # Step 5: Results
    calculation_ids = fields.One2many(...)
    total_to_pay = fields.Monetary(compute='_compute_total')

    def action_next_step(self):
        if self.state == 'step1':
            self._load_invoices()
            self.state = 'step2'
        elif self.state == 'step2':
            self._check_reconciliation()
            self.state = 'step3'
        # ... etc

    def action_validate_and_create(self):
        # Crear declaración final
        declaration = self.env['mx.tax.declaration'].create({
            'company_id': self.env.company.id,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'state': 'draft',
        })

        # Ejecutar cálculos
        for obligation in self.obligation_ids:
            for rule in obligation.calculation_rule_ids:
                result = rule.calculate(
                    invoices=self.invoice_ids,
                    period_start=self.period_start,
                    period_end=self.period_end,
                )
                # Guardar resultado

        # Marcar facturas como declaradas
        self.invoice_ids.write({
            'tax_declaration_status': 'declared',
        })

        return declaration
```

---

## 📝 TEMPLATE DE COMMIT

Para mantener historial limpio en Git:

```bash
# Template para commits

git commit -m "feat(wizard): Implementar paso 1 del wizard de declaración

- Agregar modelo mx.tax.declaration.wizard
- Implementar selección de período y obligaciones
- Crear vista form paso 1
- Agregar validaciones de fechas

Refs: #TASK-123"

# Prefijos:
feat:     Nueva funcionalidad
fix:      Corrección de bug
refactor: Refactorización sin cambio funcional
docs:     Documentación
style:    Formato de código
test:     Tests
chore:    Mantenimiento
```

---

## 🎯 ROADMAP

### Corto Plazo (1-2 semanas)

- [ ] Wizard de declaraciones (paso 1-6)
- [ ] Integración con account_reconcile_oca
- [ ] Tests unitarios básicos

### Mediano Plazo (1 mes)

- [ ] Módulo de conciliación avanzada
- [ ] Reportes PDF/Excel
- [ ] Dashboard de declaraciones
- [ ] Alertas de fechas límite

### Largo Plazo (3 meses)

- [ ] Integración con portal SAT (web scraping)
- [ ] Machine learning para detección de anomalías
- [ ] App móvil para aprobaciones
- [ ] API REST para integraciones externas

---

## ✅ CHECKLIST DE CALIDAD

Antes de hacer commit de nuevo código:

```
CÓDIGO
☐ Siguió convenciones de naming
☐ Agregó docstrings a métodos complejos
☐ Agregó _logger para debug
☐ Manejó excepciones apropiadamente
☐ Validó inputs de usuario

SEGURIDAD
☐ Verificó permisos de acceso
☐ Usó safe_eval para código dinámico
☐ Validó datos de entrada
☐ No expuso información sensible en logs

VISTAS
☐ Usó "list" en lugar de "tree"
☐ Agregó help text a campos complejos
☐ Agregó filtros de búsqueda útiles
☐ Probó en diferentes tamaños de pantalla

DATOS
☐ Usó noupdate="1" para datos maestros
☐ Agregó description a registros
☐ Verificó que IDs externos sean únicos
☐ Probó en base de datos limpia

TESTING
☐ Probó happy path
☐ Probó edge cases
☐ Probó con datos reales
☐ Probó en modo multi-compañía
☐ Revisó logs de errores

DOCUMENTACIÓN
☐ Actualizó README si es necesario
☐ Agregó ejemplos de uso
☐ Documentó APIs nuevas
☐ Actualizó CHANGELOG
```

---

**FIN DEL RESUMEN TÉCNICO**

Este documento contiene información técnica detallada para desarrolladores
que continúan o mantienen el proyecto.

**Última actualización:** 2025-12-02 06:45 GMT
