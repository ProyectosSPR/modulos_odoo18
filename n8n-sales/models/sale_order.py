# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError
import requests
import json
import random
import string
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            user_data = self._get_or_create_n8n_user(order.partner_id)
            if not user_data or not user_data.get('user_id'):
                self.message_post(body="No se pudo obtener o crear un usuario de N8N. La creación de la instancia de workflow ha sido abortada.")
                continue
            order._create_workflow_instances(user_data)
        return res

    def _get_or_create_n8n_user(self, partner):
        """
        Busca un usuario en n8n por email. Si no existe, lo crea.
        Retorna un diccionario con: user_id, email, password, invite_url, is_new_user
        """
        params = self.env['ir.config_parameter'].sudo()
        n8n_url = params.get_param('n8n_sales.n8n_url')
        api_key = params.get_param('n8n_sales.n8n_api_key')

        if not n8n_url or not api_key:
            raise UserError("Credenciales maestras de N8N no configuradas en Ajustes.")

        headers = {
            "X-N8N-API-KEY": api_key,
            "Accept": "application/json",
        }

        try:
            # --- LÓGICA CORRECTA: Obtenemos TODOS los usuarios ---
            _logger.info(f"Obteniendo lista de usuarios de N8N para buscar a {partner.email}")
            get_users_url = f"{n8n_url}/api/v1/users" # URL sin ?email=
            response_get = requests.get(get_users_url, headers=headers, timeout=20)
            response_get.raise_for_status()

            response_data = response_get.json()

            # --- LÓGICA CORRECTA: Extraemos la lista de la clave "data" ---
            all_users = response_data.get('data', [])

            # Filtramos la lista en Python
            found_user = next((user for user in all_users if isinstance(user, dict) and user.get('email') == partner.email), None)

            if found_user:
                user_id = found_user['id']
                is_pending = found_user.get('isPending', False)
                _logger.info(f"Usuario encontrado en N8N con ID: {user_id}, isPending: {is_pending}")

                # Construir link de invitación si el usuario está pendiente
                invite_url = None
                if is_pending:
                    # Obtener el owner/admin ID (primer usuario no pending)
                    owner = next((u for u in all_users if not u.get('isPending')), None)
                    if owner:
                        owner_id = owner['id']
                        # Construir el link de invitación manualmente
                        invite_url = f"{n8n_url}/signup?inviterId={owner_id}&inviteeId={user_id}"
                        _logger.info(f"Link de invitación construido para usuario existente: {invite_url}")

                self.message_post(body=f"Cliente {partner.name} ya tiene un usuario en N8N. Reutilizando ID.")
                return {
                    'user_id': user_id,
                    'email': partner.email,
                    'password': None,
                    'invite_url': invite_url,
                    'is_new_user': False
                }

            # --- PASO 2: Si no se encontró, lo creamos ---
            _logger.info(f"Usuario no encontrado. Creando nuevo usuario en N8N para: {partner.email}")
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            user_data = [{
                "firstName": partner.name.split(' ')[0] if partner.name else 'Usuario',
                "lastName": ' '.join(partner.name.split(' ')[1:]) if partner.name and ' ' in partner.name else 'Odoo',
                "email": partner.email,
                "password": password
            }]
            create_url = f"{n8n_url}/api/v1/users"
            create_headers = headers.copy()
            create_headers['Content-Type'] = 'application/json'
            response_create = requests.post(create_url, headers=create_headers, json=user_data, timeout=20)
            response_create.raise_for_status()

            create_data = response_create.json()
            if create_data and isinstance(create_data, list) and create_data[0].get('user'):
                user_info = create_data[0]['user']
                self.message_post(body=f"Usuario de N8N creado exitosamente para {partner.name}.")
                return {
                    'user_id': user_info.get('id'),
                    'email': partner.email,
                    'password': password,
                    'invite_url': user_info.get('inviteAcceptUrl', ''),
                    'is_new_user': True
                }

            _logger.error(f"La API de creación de N8N devolvió una respuesta inesperada: {create_data}")
            return None

        except requests.exceptions.RequestException as e:
            error_body = f"Error crítico de comunicación con N8N para {partner.name}: {e}"
            _logger.error(error_body, exc_info=True)
            self.message_post(body=error_body)
            return None

    def _create_workflow_instances(self, user_data):
        self.ensure_one()
        _logger.info(f"Iniciando creación de instancias para la orden {self.name}")

        params = self.env['ir.config_parameter'].sudo()
        n8n_url = params.get_param('n8n_sales.n8n_url')
        api_key = params.get_param('n8n_sales.n8n_api_key')
        if not n8n_url or not api_key:
            _logger.warning("Credenciales maestras de N8N no configuradas. Abortando.")
            return

        headers = {"X-N8N-API-KEY": api_key}
        lines_to_process = self.order_line.filtered(lambda l: l.product_id.n8n_workflow_template_id)

        for line in lines_to_process:
            product = line.product_id
            template_id = product.n8n_workflow_template_id

            if self.env['n8n.workflow.instance'].search_count([('order_id', '=', self.id), ('product_id', '=', product.id)]):
                _logger.info(f"Instancia para producto {product.name} en orden {self.name} ya existe. Saltando.")
                continue

            try:
                _logger.info(f"Descargando plantilla {template_id} desde N8N...")
                response = requests.get(f"{n8n_url}/api/v1/workflows/{template_id}", headers=headers, timeout=10)
                response.raise_for_status()
                template_json = response.json()

                self.env['n8n.workflow.instance'].create({
                    'name': f"{product.name} - {self.partner_id.name}",
                    'partner_id': self.partner_id.id,
                    'product_id': product.id,
                    'order_id': self.id,
                    'template_workflow_id': template_id,
                    'n8n_user_id': user_data.get('user_id'),
                    'n8n_invite_url': user_data.get('invite_url'),
                    'n8n_user_email': user_data.get('email'),
                    'n8n_user_password': user_data.get('password'),
                    'is_new_n8n_user': user_data.get('is_new_user', False),
                    'template_json': json.dumps(template_json, indent=2),
                })
                _logger.info(f"¡ÉXITO! Instancia para {product.name} creada para la orden {self.name}.")

            except requests.exceptions.RequestException as e:
                _logger.error(f"Error al descargar plantilla {template_id} de N8N: {e}")
                self.message_post(body=f"Error al descargar plantilla {product.name} de N8N: {e}")
