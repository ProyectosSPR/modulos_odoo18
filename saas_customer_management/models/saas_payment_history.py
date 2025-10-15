from odoo import models, fields, api

class SaasPaymentHistory(models.Model):
    _name = 'saas.payment.history'
    _description = 'SaaS Payment History'
    _order = 'payment_date desc'

    customer_id = fields.Many2one('saas.customer', string='Customer', required=True, ondelete='cascade')
    instance_id = fields.Many2one('saas.instance', string='Instance', required=True, ondelete='cascade')
    
    # Thông tin thanh toán
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.today)
    amount = fields.Float(string='Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    payment_method = fields.Selection([
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('other', 'Other')
    ], string='Payment Method', required=True)
    
    # Thông tin giao dịch
    transaction_id = fields.Char(string='Transaction ID')
    invoice_number = fields.Char(string='Invoice Number')
    description = fields.Text(string='Description')
    
    # Kỳ thanh toán
    billing_period_start = fields.Date(string='Billing Period Start')
    billing_period_end = fields.Date(string='Billing Period End')
    
    # Trạng thái
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], string='Status', default='pending', required=True)
    
    notes = fields.Text(string='Notes')
    
    # Related fields for easy access
    customer_name = fields.Char(related='customer_id.company_name', string='Customer Name', store=True)
    instance_name = fields.Char(related='instance_id.instance_name', string='Instance Name', store=True)
    
    @api.onchange('instance_id')
    def _onchange_instance_id(self):
        if self.instance_id:
            self.customer_id = self.instance_id.customer_id
