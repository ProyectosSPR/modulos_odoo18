from odoo import models, fields, api


class OdashboardSecurityGroup(models.Model):
    _name = "odash.security.group"
    _description = "Odashboard Security Group"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")

    sequence = fields.Integer(string="Sequence", default=1)

    user_ids = fields.Many2many('res.users', string="Users", domain=[('share', '=', False)])
    user_count = fields.Integer(string="User count", compute='_compute_user_count')

    @api.depends('user_ids')
    def _compute_user_count(self):
        for record in self:
            record.user_count = len(record.user_ids)
