########################################################################
#                                                                      #
#     ------------------------ODOO WAVES----------------------         #
#     --------------odoowaves.solution@gmail.com--------------         #
#                                                                      #
########################################################################
from odoo import fields, models


class MessageWizard(models.TransientModel):
    _name = 'message.wizard'
    _description = "Message Wizard"

    message = fields.Html('Message', required=True, readonly=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}