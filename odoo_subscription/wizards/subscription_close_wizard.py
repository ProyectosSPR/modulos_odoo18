# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SubscriptionCloseWizard(models.TransientModel):
    _name = 'subscription.close.wizard'
    _description = 'Close Subscription Wizard'

    subscription_id = fields.Many2one('subscription.package', string='Subscription', required=True, readonly=True)
    close_reason_id = fields.Many2one('subscription.stop.reason', string='Close Reason', required=True)
    closed_by = fields.Many2one('res.users', string='Closed By', default=lambda self: self.env.user, readonly=True)
    close_date = fields.Date(string='Close Date', default=fields.Date.today, required=True)
    notes = fields.Text(string='Additional Notes')

    def action_close_subscription(self):
        """Close the subscription"""
        self.ensure_one()
        self.subscription_id.action_close_subscription(
            reason_id=self.close_reason_id.id,
            closed_by=self.closed_by.id
        )

        # Add notes if provided
        if self.notes:
            self.subscription_id.message_post(body=self.notes)

        return {'type': 'ir.actions.act_window_close'}
