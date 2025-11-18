# 🏢 Propuesta: Soporte Multi-Company + SaaS Híbrido

## 🎯 Objetivo

Permitir 3 modelos de negocio en el mismo sistema:

1. **Permisos simples:** Solo asignar acceso a módulos
2. **Multi-company:** Crear empresa + permisos + licensing por empresa
3. **SaaS:** Instancia separada + licensing (actual)

---

## 📋 Campos Nuevos

### product.template (Agregar)

```python
# Multi-Company Configuration
is_module_access = fields.Boolean(
    string='Is Module Access Product',
    help='Grants access to modules without creating a separate instance'
)

auto_create_company = fields.Boolean(
    string='Auto-Create Company',
    help='Automatically create a company for the client'
)

company_template_id = fields.Many2one(
    'res.company',
    string='Company Template',
    help='Template company to copy settings from'
)

restrict_to_company = fields.Boolean(
    string='Restrict Access to Company',
    default=True,
    help='User can only see data from their company'
)
```

### saas.client (Agregar)

```python
# Local Companies (multi-tenancy)
company_ids = fields.One2many(
    'res.company',
    'saas_client_id',  # Nuevo campo en res.company
    string='Companies'
)

company_count = fields.Integer(
    compute='_compute_company_count'
)
```

### res.company (Agregar)

```python
saas_client_id = fields.Many2one(
    'saas.client',
    string='SaaS Client',
    help='Client that owns this company (for multi-tenancy)'
)

is_saas_company = fields.Boolean(
    string='Is SaaS Company',
    help='This company was created for a SaaS client'
)
```

---

## 🔄 Flujo de Venta - Multi-Company

### Configuración del Producto

```yaml
Producto: Empresa con Módulo Inventario

Tab "Permissions":
  Assign Permissions: ✓
  Permission Groups: [Inventory / Manager]

Tab "Multi-Company":  ← NUEVO
  Is Module Access Product: ✓
  Auto-Create Company: ✓
  Restrict Access to Company: ✓
  Subscription Package: Plan Básico

Tab "SaaS Configuration":
  Is SaaS Instance Product: ✗ (no crea instancia)
```

### Al Confirmar Venta

```python
def action_confirm(self):
    res = super().action_confirm()

    for order in self:
        for line in order.order_line:
            product = line.product_id.product_tmpl_id

            # Caso 1: Multi-Company
            if product.is_module_access and product.auto_create_company:
                company = order._create_saas_company(product)
                order._assign_user_to_company(company, product)
                order._create_company_license(company, product)

            # Caso 2: SaaS Instance
            elif product.is_saas_instance and product.auto_create_instance:
                # Lógica actual...
                pass

            # Caso 3: Solo permisos (ya existe)
            elif product.assign_permissions:
                # Lógica actual...
                pass

    return res
```

### Crear Empresa

```python
def _create_saas_company(self, product):
    """Create a company for the client"""
    self.ensure_one()

    # Get or create SaaS client
    saas_client = self._get_or_create_saas_client()

    # Generate unique company name
    base_name = self.partner_id.name
    company_name = base_name
    counter = 1

    while self.env['res.company'].search([('name', '=', company_name)]):
        company_name = f"{base_name} ({counter})"
        counter += 1

    # Create company
    company_vals = {
        'name': company_name,
        'partner_id': self.partner_id.id,
        'saas_client_id': saas_client.id,
        'is_saas_company': True,
    }

    # Copy from template if provided
    if product.company_template_id:
        template = product.company_template_id
        company_vals.update({
            'currency_id': template.currency_id.id,
            'country_id': template.country_id.id,
            # ... otros campos
        })

    company = self.env['res.company'].create(company_vals)

    self.message_post(
        body=_('🏢 Company created: <b>%s</b>') % company.name
    )

    return company
```

### Asignar Usuario a Empresa

```python
def _assign_user_to_company(self, company, product):
    """Assign user to company with restricted access"""
    self.ensure_one()

    # Get or create user
    user = self._get_or_create_user_for_partner()

    # Add company to user's companies
    user.sudo().write({
        'company_ids': [(4, company.id)],
        'company_id': company.id,  # Set as default
    })

    # Assign permissions (existing logic)
    if product.assign_permissions:
        self._apply_groups_to_user(user, product.permission_group_ids)

    self.message_post(
        body=_('👤 User <b>%s</b> assigned to company <b>%s</b>') % (
            user.name,
            company.name
        )
    )

    return user
```

### Crear License por Empresa

```python
def _create_company_license(self, company, product):
    """Create license tracking for this company"""
    self.ensure_one()

    if not product.subscription_package_id:
        return

    # Create license record
    license = self.env['saas.license'].create({
        'name': f"{company.name} - {product.name}",
        'company_id': company.id,  # Nuevo campo
        'instance_id': False,  # No hay instancia
        'client_id': company.saas_client_id.id,
        'subscription_id': product.subscription_package_id.id,
        'date': fields.Date.today(),
        'user_count': 1,  # El usuario que acaba de comprar
        'company_count': 1,
    })

    self.message_post(
        body=_('📋 License tracking started for company <b>%s</b>') % company.name
    )

    return license
```

---

## 🔐 Seguridad - Multi-Company

### Reglas de Acceso

```xml
<!-- Solo ve datos de SU empresa -->
<record id="rule_saas_company_data" model="ir.rule">
    <field name="name">Multi-tenancy: Own Company Data Only</field>
    <field name="model_id" ref="model_sale_order"/>
    <field name="domain_force">[('company_id', 'in', user.company_ids.ids)]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
</record>

<!-- Administradores ven TODO -->
<record id="rule_admin_all_companies" model="ir.rule">
    <field name="name">Admin: All Companies</field>
    <field name="model_id" ref="model_sale_order"/>
    <field name="domain_force">[(1, '=', 1)]</field>
    <field name="groups" eval="[(4, ref('base.group_system'))]"/>
</record>
```

### Restricciones Adicionales

```python
# En res.users
@api.constrains('company_ids')
def _check_saas_company_access(self):
    """Prevent users from accessing companies they don't own"""
    for user in self:
        if user.has_group('base.group_system'):
            continue  # Admins bypass

        saas_companies = user.company_ids.filtered('is_saas_company')
        if len(saas_companies) > 0:
            # User can only access companies from same client
            clients = saas_companies.mapped('saas_client_id')
            if len(clients) > 1:
                raise ValidationError(
                    _('User cannot access companies from different clients')
                )
```

---

## 📊 Licensing Multi-Company

### Modificar saas.license

```python
class SaasLicense(models.Model):
    _name = 'saas.license'

    # Campos existentes
    instance_id = fields.Many2one('saas.instance')

    # Campos NUEVOS
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='For local multi-company licensing'
    )

    license_type = fields.Selection([
        ('instance', 'SaaS Instance'),
        ('company', 'Local Company'),
    ], compute='_compute_license_type', store=True)

    @api.depends('instance_id', 'company_id')
    def _compute_license_type(self):
        for record in self:
            if record.instance_id:
                record.license_type = 'instance'
            elif record.company_id:
                record.license_type = 'company'
            else:
                record.license_type = False

    @api.depends('company_id', 'instance_id')
    def _compute_name(self):
        for record in self:
            if record.company_id:
                record.name = f"{record.company_id.name} - {record.date}"
            elif record.instance_id:
                record.name = f"{record.instance_id.name} - {record.date}"
```

### Cron para License Tracking

```python
@api.model
def create_monthly_license_records(self):
    """Create license records for instances AND companies"""

    # Existing: Track instances
    instances = self.env['saas.instance'].search([
        ('state', 'in', ['active', 'trial'])
    ])

    for instance in instances:
        # Existing logic...
        pass

    # NEW: Track companies
    companies = self.env['res.company'].search([
        ('is_saas_company', '=', True)
    ])

    for company in companies:
        # Check if record already exists
        existing = self.search([
            ('company_id', '=', company.id),
            ('date', '=', fields.Date.today())
        ])

        if not existing:
            # Count users in this company
            user_count = self.env['res.users'].search_count([
                ('company_ids', 'in', [company.id]),
                ('active', '=', True)
            ])

            self.create({
                'company_id': company.id,
                'client_id': company.saas_client_id.id,
                'subscription_id': company.saas_client_id.subscription_id.id,
                'date': fields.Date.today(),
                'user_count': user_count,
                'company_count': 1,
                'storage_gb': 0,  # TODO: calcular
            })

    return True
```

---

## 🎨 Vistas

### Vista de Empresa SaaS

```xml
<record id="view_company_saas_form" model="ir.ui.view">
    <field name="name">res.company.saas.form</field>
    <field name="model">res.company</field>
    <field name="inherit_id" ref="base.view_company_form"/>
    <field name="arch" type="xml">
        <xpath expr="//sheet" position="before">
            <div class="alert alert-info" invisible="not is_saas_company">
                <strong>SaaS Company</strong>
                <p>This company belongs to SaaS client: <field name="saas_client_id" readonly="1"/></p>
            </div>
        </xpath>

        <xpath expr="//page[@name='general_information']" position="after">
            <page string="SaaS Info" invisible="not is_saas_company">
                <group>
                    <field name="saas_client_id"/>
                    <field name="is_saas_company"/>
                </group>
            </page>
        </xpath>
    </field>
</record>
```

### Vista de Cliente con Empresas

```xml
<record id="view_saas_client_companies_form" model="ir.ui.view">
    <field name="name">saas.client.companies.form</field>
    <field name="model">saas.client</field>
    <field name="inherit_id" ref="saas_management.view_saas_client_form"/>
    <field name="arch" type="xml">
        <xpath expr="//button[@name='action_view_instances']" position="after">
            <button name="action_view_companies" type="object"
                    class="oe_stat_button" icon="fa-building">
                <field name="company_count" widget="statinfo" string="Companies"/>
            </button>
        </xpath>

        <xpath expr="//page[@name='instances']" position="after">
            <page string="Local Companies" name="companies">
                <field name="company_ids" nolabel="1"/>
            </page>
        </xpath>
    </field>
</record>
```

---

## 📝 Casos de Uso

### Caso 1: Solo Permisos (Sin Empresa)

```yaml
Producto: Acceso a Ventas
  assign_permissions: ✓
  permission_groups: [Sales / User]
  is_module_access: ✗
  is_saas_instance: ✗

Resultado:
  → Solo asigna permisos
  → Usuario usa empresa principal del sistema
  → Sin tracking especial
```

### Caso 2: Empresa + Permisos + Tracking

```yaml
Producto: Empresa con Inventario Pro
  assign_permissions: ✓
  permission_groups: [Inventory / Manager]
  is_module_access: ✓
  auto_create_company: ✓
  subscription_package: Plan Básico

Resultado:
  → Crea empresa "Cliente ABC (1)"
  → Usuario asignado a esa empresa
  → Permisos de Inventory / Manager
  → License tracking por empresa
  → Solo ve datos de su empresa
```

### Caso 3: Instancia SaaS (Como Ahora)

```yaml
Producto: Odoo SaaS Complete
  is_saas_instance: ✓
  auto_create_instance: ✓
  subscription_package: Plan Pro

Resultado:
  → Crea instancia separada
  → Subdomain único
  → License tracking por instancia
```

### Caso 4: Híbrido (Empresa Local + Instancia)

```yaml
Producto: Suite Empresarial
  # Local access
  is_module_access: ✓
  auto_create_company: ✓
  permission_groups: [Sales / User]

  # + SaaS Instance
  is_saas_instance: ✓
  auto_create_instance: ✓

Resultado:
  → Crea empresa local
  → Crea instancia SaaS
  → 2 license records (uno por empresa, otro por instancia)
```

---

## ✅ Ventajas del Sistema Híbrido

1. **Flexibilidad Total**
   - Puedes vender módulos (multi-company)
   - Puedes vender instancias (SaaS)
   - Puedes vender ambos

2. **Un Solo Sistema**
   - Mismo código para licensing
   - Misma interfaz de admin
   - Mismos reportes

3. **Escalabilidad**
   - Empieza con multi-company (bajo costo)
   - Migra a SaaS cuando sea necesario
   - Soporta ambos simultáneamente

4. **Reutilización de Código**
   - product_permissions funciona igual
   - saas_licensing funciona para ambos
   - Solo se agrega soporte de company

---

## 🎯 Plan de Implementación

### Fase 1: Campos y Modelos
- [ ] Agregar campos a product.template
- [ ] Agregar campos a saas.client
- [ ] Agregar campos a res.company
- [ ] Extender saas.license

### Fase 2: Lógica de Negocio
- [ ] Método _create_saas_company()
- [ ] Método _assign_user_to_company()
- [ ] Método _create_company_license()
- [ ] Actualizar cron de licensing

### Fase 3: Seguridad
- [ ] Reglas multi-company
- [ ] Constraints de acceso
- [ ] Tests de aislamiento

### Fase 4: Vistas
- [ ] Vista de producto multi-company
- [ ] Vista de empresa SaaS
- [ ] Vista de cliente con empresas
- [ ] Menús y acciones

---

## 🚀 Migración

Para clientes existentes:
1. Los productos SaaS actuales siguen funcionando igual
2. Puedes crear nuevos productos multi-company
3. Sin cambios breaking

---

**¿Implementamos este sistema híbrido?**
