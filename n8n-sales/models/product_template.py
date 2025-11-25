# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Este es el campo de datos real, donde se guarda el ID en la base de datos.
    n8n_workflow_template_id = fields.Char(string="ID de Plantilla N8N", copy=False)

    # Este campo es solo para la interfaz. No se guarda en la base de datos.
    n8n_template_selection = fields.Selection(
        selection='_get_n8n_workflow_templates',
        string="Plantilla de Workflow N8N",
        help="Selecciona el workflow de la instancia maestra de n8n que se usará como plantilla para este producto."
    )

    def _get_n8n_workflow_templates(self):
        params = self.env['ir.config_parameter'].sudo()
        n8n_url = params.get_param('n8n_sales.n8n_url')
        n8n_api_key = params.get_param('n8n_sales.n8n_api_key')
        
        if not n8n_url or not n8n_api_key:
            return [('', 'Configura las credenciales maestras en Ajustes')]

        request_url = f"{n8n_url.rstrip('/')}/api/v1/workflows"
        headers = {'X-N8N-API-KEY': n8n_api_key, 'Accept': 'application/json'}
        payload = {'limit': 200}

        try:
            response = requests.get(request_url, headers=headers, params=payload, timeout=15)
            response.raise_for_status()
            
            response_data = response.json()
            workflows = response_data.get('data', [])
            
            # Creamos la lista de opciones a partir de la respuesta de la API
            options = [(wf['id'], wf['name']) for wf in workflows]

            # --- CAMBIO CLAVE: Aseguramos que el valor guardado siempre sea una opción válida ---
            # Esto evita que Odoo borre un valor guardado si ya no viene de la API.
            if self.n8n_workflow_template_id:
                current_id = self.n8n_workflow_template_id
                current_name = self.name # Usamos el nombre del producto como fallback
                # Verificamos si el ID guardado ya está en la lista de opciones
                if current_id not in [opt[0] for opt in options]:
                    # Si no está, lo añadimos para que no se pierda
                    options.append((current_id, f"[ID: {current_id}] {current_name}"))
            
            if not options:
                return [('', 'Conexión OK, pero no hay workflows')]

            return options

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error de conexión a N8N al obtener plantillas: {e}")
            return [('', 'Error de conexión a la API. Ver logs.')]

    # Usamos un onchange para actualizar el campo de datos real cuando el usuario elige una opción.
    @api.onchange('n8n_template_selection')
    def _onchange_n8n_template_selection(self):
        if self.n8n_template_selection:
            self.n8n_workflow_template_id = self.n8n_template_selection
        # No necesitamos un 'else' para que no borre el valor si la lista de selección está vacía.

    # Método write para asegurar que el valor se guarda correctamente
    def write(self, vals):
        # Si se está actualizando la selección, copiar el valor al campo real
        if 'n8n_template_selection' in vals and vals.get('n8n_template_selection'):
            vals['n8n_workflow_template_id'] = vals['n8n_template_selection']
        return super(ProductTemplate, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        # Si se está creando con una selección, copiar el valor al campo real
        for vals in vals_list:
            if 'n8n_template_selection' in vals and vals.get('n8n_template_selection'):
                vals['n8n_workflow_template_id'] = vals['n8n_template_selection']
        return super(ProductTemplate, self).create(vals_list)
