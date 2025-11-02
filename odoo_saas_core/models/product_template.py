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
        """Set recurring_invoice=True when SaaS product"""
        if self.is_saas_product:
            self.recurring_invoice = True
