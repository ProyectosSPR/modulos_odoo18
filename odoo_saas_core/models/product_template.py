# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # SaaS Package Integration
    is_saas_product = fields.Boolean(
        string='Is SaaS Product',
        default=False,
        help='Check this if this product represents a SaaS subscription'
    )
    saas_package_id = fields.Many2one(
        'saas.service.package',
        string='SaaS Package',
        ondelete='restrict',
        help='Associated SaaS service package'
    )

    # Provisioning Configuration (from saa_s__access_management)
    saas_creation_policy = fields.Selection([
        ('nothing', 'No Action'),
        ('create_user', 'Create User and Privileges'),
        ('create_instance', 'Create Instance'),
    ], string='SaaS Provisioning Policy', default='nothing',
        help='Action to perform when this product is purchased')

    access_group_ids = fields.Many2many(
        'res.groups',
        'product_template_access_groups_rel',
        'product_id',
        'group_id',
        string='Access Groups',
        help='Security groups to assign to users when this product is purchased'
    )

    # Module-Specific Configuration (for selling specific modules like CRM, Sales, etc.)
    module_access_ids = fields.Many2many(
        'ir.module.module',
        'product_template_module_access_rel',
        'product_id',
        'module_id',
        string='Module Access',
        domain=[('state', '=', 'installed')],
        help='Specific Odoo modules included in this product (e.g., CRM, Sales)'
    )
    restrict_to_modules = fields.Boolean(
        string='Restrict to Specific Modules',
        default=False,
        help='If enabled, users will only have access to the modules specified above'
    )
    module_description = fields.Text(
        string='Module Features Description',
        help='Describe what features are included in this module package'
    )

    # Instance Configuration
    create_instance = fields.Boolean(
        string='Auto-Create Instance',
        default=False,
        help='Automatically create a SaaS instance when this product is purchased'
    )
    default_odoo_version = fields.Selection([
        ('16.0', 'Odoo 16.0'),
        ('17.0', 'Odoo 17.0'),
        ('18.0', 'Odoo 18.0'),
    ], string='Default Odoo Version', default='18.0')

    # Trial Configuration
    trial_days = fields.Integer(
        string='Trial Days',
        default=7,
        help='Number of trial days for new instances'
    )

    @api.onchange('saas_package_id')
    def _onchange_saas_package_id(self):
        """Auto-populate access groups from package"""
        if self.saas_package_id and self.saas_package_id.access_group_ids:
            self.access_group_ids = [(6, 0, self.saas_package_id.access_group_ids.ids)]

    @api.onchange('is_saas_product')
    def _onchange_is_saas_product(self):
        """Auto-configure SaaS product settings"""
        if self.is_saas_product:
            # SaaS products are typically subscription-based services
            # The recurring billing is handled by subscription.package module
            self.type = 'service'
