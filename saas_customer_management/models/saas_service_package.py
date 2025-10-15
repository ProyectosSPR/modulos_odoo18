from odoo import models, fields, api

class SaasServicePackage(models.Model):
    _name = 'saas.service.package'
    _description = 'SaaS Service Package'
    _order = 'sequence, name'

    name = fields.Char(string='Package Name', required=True)
    code = fields.Char(string='Package Code', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Thông tin gói dịch vụ
    max_users = fields.Integer(string='Max Users', default=1)
    storage_gb = fields.Float(string='Storage (GB)', default=1.0)
    backup_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Backup Frequency', default='daily')
    
    # Giá cả
    monthly_price = fields.Float(string='Monthly Price')
    yearly_price = fields.Float(string='Yearly Price')
    setup_fee = fields.Float(string='Setup Fee')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Tính năng
    custom_domain = fields.Boolean(string='Custom Domain')
    ssl_certificate = fields.Boolean(string='SSL Certificate')
    api_access = fields.Boolean(string='API Access')
    priority_support = fields.Boolean(string='Priority Support')
    
    # Trạng thái
    active = fields.Boolean(string='Active', default=True)
    
    # Quan hệ
    instance_ids = fields.One2many('saas.instance', 'service_package_id', string='Instances')
    
    # Computed field
    instance_count = fields.Integer(string='Instance Count', compute='_compute_instance_count')
    
    @api.depends('instance_ids')
    def _compute_instance_count(self):
        for package in self:
            package.instance_count = len(package.instance_ids)
    
    def action_view_instances(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Package Instances',
            'res_model': 'saas.instance',
            'view_mode': 'tree,form',
            'domain': [('service_package_id', '=', self.id)],
            'context': {'default_service_package_id': self.id}
        }
