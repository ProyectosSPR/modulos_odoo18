# saas_access_management/models/product_template.py
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Creamos nuestro propio campo para controlar la lógica.
    # Esto nos independiza de otros módulos.
    saas_creation_policy = fields.Selection([
        ('nothing', 'No Hacer Nada'),
        ('create_user', 'Crear Usuario y Privilegios'),
    ], string="Política de Creación SaaS", default='nothing')

    # El campo para los grupos de acceso ahora se asocia a nuestro nuevo campo.
    access_group_ids = fields.Many2many(
        'res.groups',
        string='Grupos de Acceso SaaS',
        help='Selecciona los grupos que se asignarán al usuario cuando se compre este producto.'
    )