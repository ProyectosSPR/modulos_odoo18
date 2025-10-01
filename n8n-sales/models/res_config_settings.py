# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Campo para la URL base de tu instancia maestra de n8n
    n8n_url = fields.Char(
        string='URL Maestra de n8n',
        config_parameter='n8n_sales.n8n_url',
        help="La URL base de tu instancia maestra de n8n (ej. https://n8n.midominio.com)"
    )
    
    # Campo para la API Key con permisos de administrador de esa instancia
    n8n_api_key = fields.Char(
        string='API Key Maestra de n8n',
        config_parameter='n8n_sales.n8n_api_key',
        help="API Key con permisos de administrador de tu instancia maestra de n8n."
    )