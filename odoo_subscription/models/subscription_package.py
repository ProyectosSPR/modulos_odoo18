# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class SubscriptionPackage(models.Model):
    _name = 'subscription.package'
    _description = 'Subscription Package'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_started desc, id desc'

    # Basic Information
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    reference_code = fields.Char(string='Reference', readonly=True, copy=False, default=lambda self: _('New'))

    # Customer & Partner
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', related='partner_id', readonly=True)
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', related='partner_id', readonly=True)

    # SaaS Integration
    saas_customer_id = fields.Many2one('saas.customer', string='SaaS Customer', ondelete='restrict', tracking=True)
    saas_instance_ids = fields.One2many('saas.instance', 'subscription_id', string='SaaS Instances')
    instance_count = fields.Integer(string='Instances', compute='_compute_instance_count')

    # Plan & Products
    plan_id = fields.Many2one('subscription.plan', string='Subscription Plan', required=True, tracking=True)
    product_line_ids = fields.One2many('subscription.product.line', 'subscription_id', string='Products')

    # Dates
    start_date = fields.Date(string='Start Date', default=fields.Date.today, required=True)
    date_started = fields.Date(string='Activation Date', readonly=True, copy=False)
    next_invoice_date = fields.Date(string='Next Invoice Date', compute='_compute_next_invoice_date', store=True, readonly=False)
    end_date = fields.Date(string='End Date', compute='_compute_end_date', store=True)
    close_date = fields.Date(string='Close Date', readonly=True, copy=False)

    # Lifecycle & Status
    stage_id = fields.Many2one('subscription.stage', string='Stage', default=lambda self: self._default_stage_id(), tracking=True, group_expand='_read_group_stage_ids')
    stage_category = fields.Selection(related='stage_id.category', string='Stage Category', store=True)
    is_to_renew = fields.Boolean(string='To Renew', default=False, copy=False)
    is_closed = fields.Boolean(string='Closed', default=False, copy=False)
    close_reason_id = fields.Many2one('subscription.stop.reason', string='Close Reason', readonly=True)
    closed_by = fields.Many2one('res.users', string='Closed By', readonly=True)

    # Billing
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True, copy=False)
    invoice_ids = fields.One2many('account.move', 'subscription_id', string='Invoices')
    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')
    invoice_mode = fields.Selection(related='plan_id.invoice_mode', string='Invoice Mode')

    # Pricing
    total_recurring_price = fields.Monetary(string='Recurring Total', compute='_compute_totals', store=True, currency_field='currency_id')
    tax_total = fields.Monetary(string='Taxes', compute='_compute_totals', store=True, currency_field='currency_id')
    total_with_tax = fields.Monetary(string='Total', compute='_compute_totals', store=True, currency_field='currency_id')

    # Metering (Usage-based billing)
    enable_metering = fields.Boolean(string='Enable Usage Metering', default=False)
    metering_ids = fields.One2many('subscription.metering', 'subscription_id', string='Usage Records')

    # Other
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, required=True)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user, tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    tag_ids = fields.Many2many('account.account.tag', string='Tags')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    @api.depends('plan_id', 'plan_id.short_code', 'reference_code', 'partner_id')
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.plan_id and rec.plan_id.short_code:
                parts.append(rec.plan_id.short_code)
            if rec.reference_code and rec.reference_code != _('New'):
                parts.append(rec.reference_code)
            if rec.partner_id:
                parts.append(rec.partner_id.name)
            rec.name = ' - '.join(parts) if parts else _('New Subscription')

    @api.depends('saas_instance_ids')
    def _compute_instance_count(self):
        for rec in self:
            rec.instance_count = len(rec.saas_instance_ids)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice'))

    @api.depends('product_line_ids', 'product_line_ids.total_amount', 'product_line_ids.price_tax')
    def _compute_totals(self):
        for rec in self:
            rec.total_recurring_price = sum(rec.product_line_ids.mapped('total_amount'))
            rec.tax_total = sum(rec.product_line_ids.mapped('price_tax'))
            rec.total_with_tax = rec.total_recurring_price + rec.tax_total

    @api.depends('start_date', 'date_started', 'plan_id', 'plan_id.renewal_time')
    def _compute_next_invoice_date(self):
        for rec in self:
            if rec.date_started and rec.plan_id and rec.plan_id.renewal_time:
                rec.next_invoice_date = rec.date_started + timedelta(days=rec.plan_id.renewal_time)
            elif rec.start_date and rec.plan_id and rec.plan_id.renewal_time:
                rec.next_invoice_date = rec.start_date + timedelta(days=rec.plan_id.renewal_time)
            else:
                rec.next_invoice_date = False

    @api.depends('date_started', 'plan_id', 'plan_id.days_to_end')
    def _compute_end_date(self):
        for rec in self:
            if rec.date_started and rec.plan_id and rec.plan_id.days_to_end:
                rec.end_date = rec.date_started + timedelta(days=rec.plan_id.days_to_end)
            else:
                rec.end_date = False

    @api.model
    def _default_stage_id(self):
        return self.env['subscription.stage'].search([('category', '=', 'draft')], limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env['subscription.stage'].search([])

    @api.model
    def create(self, vals):
        if vals.get('reference_code', _('New')) == _('New'):
            vals['reference_code'] = self.env['ir.sequence'].next_by_code('subscription.package') or _('New')
        return super(SubscriptionPackage, self).create(vals)

    def button_start_subscription(self):
        """Activate subscription"""
        for rec in self:
            progress_stage = self.env['subscription.stage'].search([('category', '=', 'progress')], limit=1)
            rec.write({
                'stage_id': progress_stage.id,
                'date_started': fields.Date.today(),
            })
            rec.message_post(body=_('Subscription activated'))

    def button_create_sale_order(self):
        """Create sale order from subscription"""
        self.ensure_one()
        if self.sale_order_id:
            raise UserError(_('Sale order already exists for this subscription'))

        order_vals = self._prepare_sale_order_vals()
        order = self.env['sale.order'].create(order_vals)

        self.sale_order_id = order.id
        self.message_post(body=_('Sale Order %s created') % order.name)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _prepare_sale_order_vals(self):
        """Prepare sale order values"""
        self.ensure_one()
        order_lines = []

        for line in self.product_line_ids:
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'price_unit': line.unit_price,
                'discount': line.discount,
                'tax_id': [(6, 0, line.tax_ids.ids)],
            }))

        return {
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'order_line': order_lines,
            'subscription_id': self.id,
        }

    def button_close(self):
        """Open close wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Close Subscription'),
            'res_model': 'subscription.close.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_subscription_id': self.id},
        }

    def action_close_subscription(self, reason_id=False, closed_by=False):
        """Close subscription"""
        for rec in self:
            closed_stage = self.env['subscription.stage'].search([('category', '=', 'closed')], limit=1)
            vals = {
                'stage_id': closed_stage.id,
                'is_closed': True,
                'close_date': fields.Date.today(),
            }
            if reason_id:
                vals['close_reason_id'] = reason_id
            if closed_by:
                vals['closed_by'] = closed_by

            rec.write(vals)
            rec.message_post(body=_('Subscription closed'))

    def action_renew(self):
        """Renew subscription"""
        for rec in self:
            if rec.plan_id and rec.plan_id.renewal_time:
                rec.next_invoice_date = fields.Date.today() + timedelta(days=rec.plan_id.renewal_time)
                rec.is_to_renew = False
                rec.message_post(body=_('Subscription renewed'))

    def action_view_invoices(self):
        """View invoices"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_move_type': 'out_invoice', 'default_subscription_id': self.id},
        }

    def action_view_instances(self):
        """View SaaS instances"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('SaaS Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.saas_instance_ids.ids)],
        }

    @api.model
    def _cron_subscription_management(self):
        """Cron job for subscription management"""
        today = fields.Date.today()

        # Check renewals
        to_renew = self.search([
            ('stage_category', '=', 'progress'),
            ('next_invoice_date', '<=', today),
            ('is_closed', '=', False)
        ])

        for subscription in to_renew:
            try:
                # Create invoice if auto-invoice enabled
                if subscription.invoice_mode == 'draft_invoice':
                    subscription._create_invoice()

                # Mark for renewal
                subscription.is_to_renew = True
                subscription.send_renewal_alert_mail()

            except Exception as e:
                subscription.message_post(body=_('Error in renewal: %s') % str(e))

        # Check expirations
        to_expire = self.search([
            ('stage_category', '=', 'progress'),
            ('end_date', '<=', today),
            ('is_closed', '=', False)
        ])

        for subscription in to_expire:
            subscription.action_close_subscription(
                reason_id=self.env.ref('odoo_subscription.stop_reason_expired').id,
                closed_by=self.env.ref('base.user_admin').id
            )

    def _create_invoice(self):
        """Create invoice for subscription"""
        self.ensure_one()

        invoice_lines = []
        for line in self.product_line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.product_qty,
                'price_unit': line.unit_price,
                'discount': line.discount,
                'tax_ids': [(6, 0, line.tax_ids.ids)],
                'name': line.product_id.display_name,
            }))

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'subscription_id': self.id,
            'invoice_line_ids': invoice_lines,
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.message_post(body=_('Invoice %s created') % invoice.name)
        return invoice

    def send_renewal_alert_mail(self):
        """Send renewal alert email"""
        template = self.env.ref('odoo_subscription.mail_template_subscription_renewal', raise_if_not_found=False)
        if template:
            for rec in self:
                template.send_mail(rec.id, force_send=True)
