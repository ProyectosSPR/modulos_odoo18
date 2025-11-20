# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MetabaseDashboard(models.Model):
    _name = 'metabase.dashboard'
    _description = 'Metabase Dashboard Configuration'
    _order = 'sequence, name'

    name = fields.Char(
        string='Dashboard Name',
        required=True,
        help='Name of the dashboard for identification'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order in which dashboards appear in menu'
    )

    iframe_url = fields.Char(
        string='Dashboard URL',
        required=True,
        help='Full URL of the Metabase dashboard to embed'
    )

    description = fields.Text(
        string='Description',
        help='Description of what this dashboard shows'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide this dashboard'
    )

    height = fields.Integer(
        string='Height (px)',
        default=800,
        help='Height of the iframe in pixels'
    )

    menu_id = fields.Many2one(
        'ir.ui.menu',
        string='Menu Item',
        readonly=True,
        help='Auto-generated menu item for this dashboard'
    )

    action_id = fields.Many2one(
        'ir.actions.client',
        string='Action',
        readonly=True,
        help='Auto-generated action for this dashboard'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create dashboard and its menu item"""
        dashboards = super().create(vals_list)
        for dashboard in dashboards:
            dashboard._create_menu_action()
        return dashboards

    def write(self, vals):
        """Update menu when name or sequence changes"""
        result = super().write(vals)
        if 'name' in vals or 'sequence' in vals or 'active' in vals:
            for dashboard in self:
                dashboard._update_menu_action()
        return result

    def unlink(self):
        """Remove menu and action when dashboard is deleted"""
        for dashboard in self:
            if dashboard.menu_id:
                dashboard.menu_id.unlink()
            if dashboard.action_id:
                dashboard.action_id.unlink()
        return super().unlink()

    def _create_menu_action(self):
        """Create menu item and action for this dashboard"""
        self.ensure_one()

        # Create client action
        action = self.env['ir.actions.client'].create({
            'name': self.name,
            'tag': 'metabase_dashboard_viewer',
            'params': {
                'dashboard_id': self.id,
            },
        })
        self.action_id = action

        # Get or create parent menu
        parent_menu = self.env.ref('metabase_iframe.menu_metabase_root', raise_if_not_found=False)

        if parent_menu:
            # Create menu item
            menu = self.env['ir.ui.menu'].create({
                'name': self.name,
                'parent_id': parent_menu.id,
                'action': f'ir.actions.client,{action.id}',
                'sequence': self.sequence,
            })
            self.menu_id = menu

    def _update_menu_action(self):
        """Update existing menu and action"""
        self.ensure_one()

        if self.action_id:
            self.action_id.write({
                'name': self.name,
            })

        if self.menu_id:
            self.menu_id.write({
                'name': self.name,
                'sequence': self.sequence,
                'active': self.active,
            })
