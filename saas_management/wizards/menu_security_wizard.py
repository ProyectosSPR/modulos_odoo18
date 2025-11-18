# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MenuSecurityWizard(models.TransientModel):
    _name = 'menu.security.wizard'
    _description = 'Menu Security Configuration Wizard'

    group_ids = fields.Many2many(
        'res.groups',
        string='Groups to Apply',
        required=True,
        default=lambda self: self.env.ref('base.group_system'),
        help='Select the groups that will be added to all menu items'
    )

    apply_to_existing = fields.Boolean(
        string='Apply to Existing Menus',
        default=True,
        help='If checked, will add the selected groups to all existing menu items'
    )

    menu_count = fields.Integer(
        string='Total Menus',
        compute='_compute_menu_count',
        help='Total number of menu items in the system'
    )

    restricted_count = fields.Integer(
        string='Already Restricted Menus',
        compute='_compute_menu_count',
        help='Number of menus that already have group restrictions'
    )

    @api.depends('apply_to_existing')
    def _compute_menu_count(self):
        for wizard in self:
            all_menus = self.env['ir.ui.menu'].search([])
            wizard.menu_count = len(all_menus)
            wizard.restricted_count = len(all_menus.filtered(lambda m: m.groups_id))

    def action_apply_security(self):
        """Apply the selected groups to all menu items"""
        self.ensure_one()

        if not self.group_ids:
            raise UserError(_('Please select at least one group to apply.'))

        # Get all menu items
        all_menus = self.env['ir.ui.menu'].search([])

        # Counter for tracking changes
        updated_count = 0

        for menu in all_menus:
            # Get existing groups
            existing_groups = menu.groups_id

            # Add new groups (avoiding duplicates)
            new_groups = existing_groups | self.group_ids

            if new_groups != existing_groups:
                menu.write({'groups_id': [(6, 0, new_groups.ids)]})
                updated_count += 1

        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Security Applied'),
                'message': _('%d menu items have been updated with the selected security groups.') % updated_count,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_remove_all_security(self):
        """Remove all group restrictions from menu items (use with caution!)"""
        self.ensure_one()

        # Get all menu items with group restrictions
        restricted_menus = self.env['ir.ui.menu'].search([('groups_id', '!=', False)])

        # Remove all group restrictions
        restricted_menus.write({'groups_id': [(5, 0, 0)]})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Security Removed'),
                'message': _('%d menu items now have no group restrictions (visible to all users).') % len(restricted_menus),
                'type': 'warning',
                'sticky': False,
            }
        }

    def action_apply_to_specific_group(self):
        """Open a tree view to manually select which menus to restrict"""
        self.ensure_one()

        return {
            'name': _('Menu Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.ui.menu',
            'view_mode': 'tree,form',
            'domain': [],
            'context': {
                'default_groups_id': [(6, 0, self.group_ids.ids)],
            },
            'target': 'current',
        }
