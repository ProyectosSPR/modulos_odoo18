import json
import uuid

from odoo import fields, models, api, _
import base64
from datetime import datetime
from odoo.exceptions import UserError


class OdashConfig(models.Model):
    _name = 'odash.config'
    _description = 'Odashboard config'
    _rec_name = 'name'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    sequence = fields.Integer(string='Sequence', default=1, help="Gives the sequence order when displaying pages.")

    access_summary = fields.Char(string='Access summary', compute='_compute_access_summary')

    is_page_config = fields.Boolean(string='Is Page Config', default=False)
    config_id = fields.Char(string='Config ID')
    config = fields.Json(string='Config')
    
    category_id = fields.Many2one(
        comodel_name='odash.category',
        string='Category',
        ondelete='set null',
        help="Category for organizing dashboard pages"
    )

    security_group_ids = fields.Many2many(comodel_name='odash.security.group', string='Security Groups')
    user_ids = fields.Many2many(comodel_name='res.users', string='Users', domain=[('share', '=', False)])

    access_token = fields.Char(string='Access token', default=lambda self: uuid.uuid4())
    secret_access_token = fields.Char(string='Secret Access token', default=lambda self: uuid.uuid4())

    allow_public_access = fields.Boolean(string='Allow public access')
    public_url = fields.Char(string='Public URL', compute="_compute_public_url")

    def clean_unused_config(self):
        all_configs = self.env['odash.config'].sudo().search([])
        pages = all_configs.filtered(lambda c: c.is_page_config)
        configs = all_configs.filtered(lambda c: not c.is_page_config)

        total_pages = " ".join([json.dumps(page.config) for page in pages])

        unused_config = self.env['odash.config'].sudo()
        for config in configs:
            if config.config_id not in total_pages:
                unused_config += config
        unused_config.unlink()

    @api.depends('access_token')
    def _compute_public_url(self):
        for record in self:
            base_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record.public_url = f"{base_url}/dashboard/public/{record.id}/{record.access_token}"

    @api.depends('config')
    def _compute_name(self):
        for record in self:
            record.name = record.config.get("title", _("Unnamed"))

    @api.depends('security_group_ids', 'user_ids')
    def _compute_access_summary(self):
        for record in self:
            if not record.security_group_ids and not record.user_ids:
                record.access_summary = "All users"
            else:
                users_from_groups = record.security_group_ids.mapped('user_ids')
                record.access_summary = f"Custom access: {len(record.security_group_ids)} groups ({len(users_from_groups)} distinct users), {len(record.user_ids)} directly assigned users"

    # def action_export_configs(self):
    #     """Export all dashboard configurations to a JSON file"""
    #     configs = self.search([])
    #     export_data = {
    #         'export_date': datetime.now().isoformat(),
    #         'odoo_version': self.env['ir.module.module'].sudo().search([('name', '=', 'base')]).latest_version,
    #         'odashboard_version': self.env['ir.module.module'].sudo().search([('name', '=', 'odashboard')]).latest_version,
    #         'configs': []
    #     }
    #
    #     for config in configs:
    #         config_data = {
    #             'name': config.name,
    #             'sequence': config.sequence,
    #             'is_page_config': config.is_page_config,
    #             'config_id': config.config_id,
    #             'config': config.config,
    #             'security_groups': config.security_group_ids.mapped('name'),
    #             'users': config.user_ids.mapped('login'),
    #         }
    #         export_data['configs'].append(config_data)
    #
    #     # Create attachment with the export data
    #     json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
    #     filename = f"odashboard_config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    #
    #     attachment = self.env['ir.attachment'].create({
    #         'name': filename,
    #         'type': 'binary',
    #         'datas': base64.b64encode(json_data.encode('utf-8')),
    #         'res_model': 'odash.config',
    #         'res_id': 0,
    #         'mimetype': 'application/json',
    #     })
    #
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': f'/web/content/{attachment.id}?download=true',
    #         'target': 'self',
    #     }

    def action_export_configs(self):
        """Open wizard for exporting dashboard configurations"""
        return {
            'name': _('Export Dashboard Configurations'),
            'type': 'ir.actions.act_window',
            'res_model': 'odash.config.export.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import_configs(self):
        """Open wizard for importing dashboard configurations"""
        return {
            'name': _('Import Dashboard Configurations'),
            'type': 'ir.actions.act_window',
            'res_model': 'odash.config.import.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
