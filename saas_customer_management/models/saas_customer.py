from odoo import models, fields, api

class SaasCustomer(models.Model):
    _name = 'saas.customer'
    _description = 'SaaS Customer'
    _rec_name = 'company_name'
    _order = 'company_name'

    # Thông tin công ty
    company_name = fields.Char(string='Company Name', required=True)
    tax_code = fields.Char(string='Tax Code/MST')
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    
    # Người liên hệ chính
    contact_name = fields.Char(string='Contact Person', required=True)
    contact_phone = fields.Char(string='Contact Phone')
    contact_email = fields.Char(string='Contact Email', required=True)
    contact_position = fields.Char(string='Position')
    
    # Thông tin hỗ trợ
    support_contact = fields.Char(string='Support Contact')
    support_email = fields.Char(string='Support Email')
    support_phone = fields.Char(string='Support Phone')
    
    # Trạng thái khách hàng
    state = fields.Selection([
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated')
    ], string='Status', default='prospect', required=True)
    
    # Ngày tạo và cập nhật
    date_created = fields.Datetime(string='Created Date', default=fields.Datetime.now, readonly=True)
    date_updated = fields.Datetime(string='Last Updated', default=fields.Datetime.now, readonly=True)
    
    # Quan hệ với các model khác
    instance_ids = fields.One2many('saas.instance', 'customer_id', string='Instances')
    payment_history_ids = fields.One2many('saas.payment.history', 'customer_id', string='Payment History')
    
    # Computed fields
    instance_count = fields.Integer(string='Instance Count', compute='_compute_instance_count', store=True)
    active_instance_count = fields.Integer(string='Active Instances', compute='_compute_active_instance_count', store=True)
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_total_revenue', store=True)
    
    @api.depends('instance_ids')
    def _compute_instance_count(self):
        for customer in self:
            customer.instance_count = len(customer.instance_ids)
    
    @api.depends('instance_ids.status')
    def _compute_active_instance_count(self):
        for customer in self:
            customer.active_instance_count = len(customer.instance_ids.filtered(lambda x: x.status == 'active'))
    
    @api.depends('payment_history_ids.amount')
    def _compute_total_revenue(self):
        for customer in self:
            customer.total_revenue = sum(customer.payment_history_ids.mapped('amount'))
    
    def write(self, vals):
        vals['date_updated'] = fields.Datetime.now()
        return super().write(vals)
    
    def action_view_instances(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Instances',
            'res_model': 'saas.instance',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id}
        }
    
    def action_view_active_instances(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Active Instances',
            'res_model': 'saas.instance',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id), ('status', '=', 'active')],
            'context': {'default_customer_id': self.id}
        }
