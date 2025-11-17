# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Permission Configuration
    assign_permissions = fields.Boolean(
        string='Assign Permissions on Sale',
        default=False,
        help='When enabled, security groups will be assigned to the customer user upon sale confirmation'
    )

    permission_group_ids = fields.Many2many(
        'res.groups',
        'product_permission_groups_rel',
        'product_id',
        'group_id',
        string='Security Groups to Assign',
        help='Select which security groups should be assigned to the user when this product is purchased'
    )

    permission_description = fields.Text(
        string='Permission Description',
        help='Describe what access/permissions this product grants (for internal reference)'
    )

    @api.onchange('assign_permissions')
    def _onchange_assign_permissions(self):
        """Clear groups if assign_permissions is disabled"""
        if not self.assign_permissions:
            self.permission_group_ids = [(5, 0, 0)]
