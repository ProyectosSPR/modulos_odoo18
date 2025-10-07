from odoo import models, fields

class SubscriptionPackage(models.Model):
    # Cambia 'sale.subscription' por 'subscription.package'
    _inherit = 'subscription.package'

    is_provisioned = fields.Boolean(
        string='Acceso Aprovisionado',
        default=False,
        copy=False,
        help="Marca si ya se ha ejecutado la acción de crear/configurar el usuario para esta suscripción."
    )