# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaasServicePackage(models.Model):
    _name = 'saas.service.package'
    _description = 'SaaS Service Package'
    _order = 'sequence, name'

    # Basic Information
    name = fields.Char(string='Package Name', required=True, translate=True)
    code = fields.Char(string='Package Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(string='Active', default=True)

    # Resource Limits
    max_users = fields.Integer(string='Max Users', default=1, required=True)
    storage_gb = fields.Float(string='Storage (GB)', default=1.0, required=True)
    backup_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Backup Frequency', default='daily')

    # Pricing
    monthly_price = fields.Monetary(string='Monthly Price', currency_field='currency_id')
    yearly_price = fields.Monetary(string='Yearly Price', currency_field='currency_id')
    setup_fee = fields.Monetary(string='Setup Fee', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Features
    custom_domain = fields.Boolean(string='Custom Domain Support', default=False)
    ssl_certificate = fields.Boolean(string='SSL Certificate Included', default=False)
    api_access = fields.Boolean(string='API Access', default=False)
    priority_support = fields.Boolean(string='Priority Support', default=False)
    modules_included = fields.Many2many(
        'ir.module.module',
        string='Modules Included',
        domain=[('state', '=', 'installed')]
    )

    # SaaS Provisioning (Integration with access management)
    access_group_ids = fields.Many2many(
        'res.groups',
        string='Access Groups',
        help='Security groups automatically assigned to users of this package'
    )

    # Product Integration
    product_ids = fields.One2many(
        'product.template',
        'saas_package_id',
        string='Related Products'
    )

    # Relationships
    instance_ids = fields.One2many(
        'saas.instance',
        'service_package_id',
        string='Instances'
    )

    # Computed Fields
    instance_count = fields.Integer(
        string='Active Instances',
        compute='_compute_instance_count'
    )
    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_count'
    )

    # Discounts
    yearly_discount_percent = fields.Float(
        string='Yearly Discount %',
        compute='_compute_yearly_discount',
        store=True
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Package code must be unique!'),
    ]

    @api.depends('instance_ids')
    def _compute_instance_count(self):
        for record in self:
            record.instance_count = len(
                record.instance_ids.filtered(lambda i: i.status in ['trial', 'active'])
            )

    @api.depends('product_ids')
    def _compute_product_count(self):
        for record in self:
            record.product_count = len(record.product_ids)

    @api.depends('monthly_price', 'yearly_price')
    def _compute_yearly_discount(self):
        for record in self:
            if record.monthly_price > 0:
                annual_from_monthly = record.monthly_price * 12
                if annual_from_monthly > 0 and record.yearly_price < annual_from_monthly:
                    discount = ((annual_from_monthly - record.yearly_price) / annual_from_monthly) * 100
                    record.yearly_discount_percent = round(discount, 2)
                else:
                    record.yearly_discount_percent = 0.0
            else:
                record.yearly_discount_percent = 0.0

    def action_view_instances(self):
        """View instances using this package"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('service_package_id', '=', self.id)],
            'context': {'default_service_package_id': self.id},
        }

    def action_view_products(self):
        """View products linked to this package"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products'),
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('saas_package_id', '=', self.id)],
            'context': {'default_saas_package_id': self.id},
        }

    def name_get(self):
        """Display code and name"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
