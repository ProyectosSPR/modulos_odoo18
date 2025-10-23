from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class OdashCategory(models.Model):
    _name = 'odash.category'
    _description = 'Dashboard Page Category'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,
        help="Name of the category (e.g., Sales, Support, Finance)"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Determines the display order of categories"
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help="Brief description of what this category contains"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="If unchecked, this category will be hidden"
    )
    page_ids = fields.One2many(
        comodel_name='odash.config',
        inverse_name='category_id',
        string='Pages',
        domain=[('is_page_config', '=', True)],
        help="Dashboard pages in this category"
    )
    page_count = fields.Integer(
        string='Number of Pages',
        compute='_compute_page_count',
        store=True,
        help="Total number of pages in this category"
    )
    icon = fields.Char(
        string='Icon',
        help="Font Awesome icon class (e.g., fa-chart-line, fa-users)"
    )
    security_group_ids = fields.Many2many(
        comodel_name='odash.security.group',
        string='Security Groups',
        help="Security groups that can access this category"
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users',
        domain=[('share', '=', False)],
        help="Users that can access this category"
    )
    access_summary = fields.Char(string='Access summary', compute='_compute_access_summary')

    
    @api.depends('page_ids')
    def _compute_page_count(self):
        for record in self:
            record.page_count = len(record.page_ids)
    
    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            if record.name:
                duplicate = self.search([
                    ('name', '=ilike', record.name),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        _('A category with the name "%s" already exists. Category names must be unique.') % record.name
                    )
    
    def name_get(self):
        """Display category name with page count"""
        result = []
        for record in self:
            name = record.name
            if record.page_count:
                name = f"{name} ({record.page_count})"
            result.append((record.id, name))
        return result

    def open_view_pages(self):
        return {
            'name': _('Pages'),
            'type': 'ir.actions.act_window',
            'res_model': 'odash.config',
            'domain': [('category_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    @api.depends('security_group_ids', 'user_ids')
    def _compute_access_summary(self):
        for record in self:
            if not record.security_group_ids and not record.user_ids:
                record.access_summary = _("All users")
            else:
                users_from_groups = record.security_group_ids.mapped('user_ids')
                message = _("Custom access: %(count_group)s groups (%(count_user_from_group)s distinct users), %(count_user)s directly assigned users",
                            count_group=len(record.security_group_ids),
                            count_user_from_group=len(users_from_groups),
                            count_user=len(record.user_ids)
                            )
                record.access_summary = message