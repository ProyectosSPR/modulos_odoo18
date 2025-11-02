# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SubscriptionUpgradeWizard(models.TransientModel):
    _name = 'subscription.upgrade.wizard'
    _description = 'Subscription Upgrade/Downgrade Wizard'

    subscription_id = fields.Many2one('subscription.package', string='Subscription', required=True, readonly=True)
    current_plan_id = fields.Many2one('subscription.plan', related='subscription_id.plan_id', string='Current Plan', readonly=True)
    new_plan_id = fields.Many2one('subscription.plan', string='New Plan', required=True)
    apply_prorate = fields.Boolean(string='Apply Prorating', default=True)
    upgrade_date = fields.Date(string='Upgrade Date', default=fields.Date.today, required=True)
    notes = fields.Text(string='Notes')

    def action_upgrade(self):
        """Upgrade/downgrade the subscription plan"""
        self.ensure_one()

        if self.new_plan_id == self.current_plan_id:
            raise UserError(_('New plan must be different from current plan'))

        # Update plan
        self.subscription_id.plan_id = self.new_plan_id

        # Recalculate next invoice date based on new plan
        self.subscription_id._compute_next_invoice_date()

        # Post message
        message = _('Plan changed from %s to %s') % (self.current_plan_id.name, self.new_plan_id.name)
        if self.notes:
            message += '<br/>' + self.notes
        self.subscription_id.message_post(body=message)

        # TODO: Implement prorating logic if needed
        if self.apply_prorate:
            # Calculate prorated amount
            pass

        return {'type': 'ir.actions.act_window_close'}
