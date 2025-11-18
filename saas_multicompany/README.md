# SaaS Multi-Company Module

## Overview

This module enables **multi-tenancy** in Odoo by automatically creating dedicated companies for clients when they purchase module access products.

Perfect for:
- ISVs selling module access
- Consultants managing multiple clients
- Shared infrastructure SaaS providers

## Key Features

### ✅ Automatic Company Creation
- Creates a dedicated company for each client automatically
- Optional company template for standardized settings
- Unique company naming with auto-increment

### ✅ Data Isolation
- Users only see data from their assigned companies
- Multi-company security rules enforce separation
- Admins can access all companies

### ✅ License Tracking
- Tracks users per company
- Monitors storage usage per company
- Detects overages and enables billing

### ✅ Flexible Configuration
- Can create company + assign permissions
- Can assign permissions without creating company
- Works alongside SaaS instance model

## Installation

### Dependencies

```python
'depends': [
    'base',
    'sale_management',
    'product_permissions',
    'saas_management',
    'saas_licensing',
]
```

### Installation Order

```
1. subscription_package (Cybrosys)
2. product_permissions
3. saas_management
4. saas_licensing
5. saas_multicompany ← This module
```

## Configuration

### 1. Create Company Template (Optional)

```
Settings → Companies → Create

Name: SaaS Template Company
Is Template Company: ✓
[Configure default settings]
```

### 2. Create Subscription Package

```
Subscriptions → Subscription Packages → Create

Name: Multi-Company Plan Basic
Max Users: 5
Max Companies: 1
Max Storage: 10 GB

Overage Pricing:
  Price per User: $50
  Price per Company: $200
  Price per GB: $10
```

### 3. Create Multi-Company Product

```
Sales → Products → Create

Name: Module Access - Inventory

Tab "Permissions":
  Assign Permissions: ✓
  Permission Groups: [Inventory / Manager]

Tab "Multi-Company":
  Is Module Access Product: ✓
  Auto-Create Company: ✓
  Restrict to Company: ✓
  Company Template: [SaaS Template Company]
  Subscription: [Multi-Company Plan Basic]
```

## Usage

### Selling Module Access

```
1. Create Sales Order
   Client: [Select client]
   Product: Module Access - Inventory

2. Confirm Order

3. System automatically:
   → Creates SaaS Client (if new)
   → Creates Company for client
   → Assigns user to company
   → Assigns permissions
   → Creates license tracking
   → User can only see their company data
```

### Result

```
Chatter shows:
  ✅ SaaS Client created: Client ABC
  🏢 Company created: Client ABC
  📋 Subscription: Multi-Company Plan Basic
     • Max Users: 5
     • Max Companies: 1
     • Max Storage: 10 GB
  👤 User John assigned to company Client ABC
  🔒 Access restricted to this company only
  ✅ Permissions assigned: Inventory / Manager
  📋 License tracking started
```

## How It Works

### Data Flow

```
Sale Order Confirmed
    ↓
product_permissions
  → Convert Portal → Internal (if needed)
  → Assign permission groups
    ↓
saas_multicompany (NEW)
  → Create/find SaaS Client
  → Create Company for client
  → Assign user to company
  → Set company as default
  → Create license record
    ↓
saas_licensing
  → Track users per company
  → Detect overages
  → Enable billing
```

### Security

Users can only access data from their assigned companies:

```python
# Automatic rule enforcement
domain = [
    '|',
    ('company_id', '=', False),
    ('company_id', 'in', user.company_ids.ids)
]
```

Administrators bypass all restrictions.

## License Tracking

### Automatic Tracking

Cron job runs daily:
```
For each SaaS company:
  → Count active internal users
  → Calculate storage usage
  → Compare vs subscription limits
  → Create license record
  → Flag overages for billing
```

### Manual Snapshot

```
Company → Action → Create License Snapshot
```

### Overage Billing

```
SaaS Management → Licensing → License Records
→ Filter: Billable
→ Open record
→ Click "Create Invoice"
```

## Models

### product.template

**New Fields:**
- `is_module_access`: Boolean
- `auto_create_company`: Boolean
- `company_template_id`: Many2one(res.company)
- `restrict_to_company`: Boolean
- `multicompany_subscription_id`: Many2one(subscription.package)

### res.company

**New Fields:**
- `saas_client_id`: Many2one(saas.client)
- `is_saas_company`: Boolean
- `is_saas_template`: Boolean
- `subscription_id`: Many2one(subscription.package)
- `license_ids`: One2many(saas.license)
- `user_count`: Integer (computed)

### saas.client

**New Fields:**
- `company_ids`: One2many(res.company)
- `company_count`: Integer (computed)

### saas.license

**New Fields:**
- `company_id`: Many2one(res.company)
- `license_type`: Selection(['instance', 'company'])

## API

### Create Company Programmatically

```python
# Via sale order
order._create_saas_company(saas_client, product)

# Direct creation
company = self.env['res.company'].create({
    'name': 'Client Company',
    'saas_client_id': client.id,
    'is_saas_company': True,
    'subscription_id': subscription.id,
})
```

### Assign User to Company

```python
order._assign_user_to_company(company, product)
```

### Create License Record

```python
order._create_company_license(company, product)
```

## Menus

```
SaaS Management
├── Clients
│   └── Clients (with companies tab)
├── Instances
│   └── All Instances
├── Companies (NEW)
│   └── SaaS Companies
└── Licensing
    └── License Records (supports both instances & companies)
```

## Comparison: Multi-Company vs SaaS Instance

| Feature | Multi-Company | SaaS Instance |
|---------|---------------|---------------|
| **Infrastructure** | Shared server | Dedicated server |
| **Data Isolation** | By company_id | By database |
| **Cost** | Low | High |
| **Scalability** | Vertical | Horizontal |
| **Use Case** | Module sales | Full SaaS |

## Troubleshooting

### User can see other company data

**Check:**
1. Is `restrict_to_company` enabled on product?
2. Is user assigned to correct company?
3. Are multi-company rules active?

### Company not created

**Check:**
1. Is `is_module_access` = True?
2. Is `auto_create_company` = True?
3. Check server logs for errors

### License tracking not working

**Check:**
1. Is subscription assigned to company?
2. Is cron job active?
3. Are users marked as "Internal" (not Portal)?

## Best Practices

### 1. Company Naming
Use clear, unique names:
```
✅ Client ABC Corporation
❌ Company 1
```

### 2. Template Usage
Create template with:
- Default currency
- Default country
- Default fiscal settings
- Logo and colors

### 3. Permissions
Always combine with product_permissions:
```yaml
Product Configuration:
  Permissions: ✓ (which modules)
  Multi-Company: ✓ (data isolation)
  Subscription: ✓ (usage limits)
```

### 4. User Management
- Create users as "Internal" type
- Assign to single company by default
- Can add more companies later if needed

## Roadmap

### Future Enhancements

- [ ] Automatic storage calculation per company
- [ ] Company provisioning from template
- [ ] Bulk operations (suspend all companies)
- [ ] Company migration wizard
- [ ] Dashboard with company metrics
- [ ] API for external integrations

## Support

**Author:** AutomateAI
**Website:** https://automateai.com.mx
**Version:** 18.0.1.0.0
**License:** LGPL-3

## Related Modules

- `product_permissions` - Permission assignment
- `saas_management` - Client & instance management
- `saas_licensing` - Usage tracking & billing
- `subscription_package` - Subscription plans (Cybrosys)
