# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class N8nWorkflowInstance(models.Model):
    _name = 'n8n.workflow.instance'
    _description = 'Instancia de Workflow de N8N'

    name = fields.Char(string="Nombre", required=True)
    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, readonly=True)
    product_id = fields.Many2one('product.product', string="Producto Comprado", readonly=True)
    order_id = fields.Many2one('sale.order', string="Orden de Venta", readonly=True)
    
    # --- ASEGÚRATE DE QUE ESTA LÍNEA EXISTA ---
    template_workflow_id = fields.Char(string="ID de Plantilla N8N", readonly=True)

    n8n_user_id = fields.Char(string="ID de Usuario N8N", readonly=True)
    n8n_invite_url = fields.Char(string="URL de Invitación a N8N", readonly=True)

    # Campos para credenciales de acceso
    n8n_user_email = fields.Char(string="Email de N8N", readonly=True, help="Email para acceder a N8N")
    n8n_user_password = fields.Char(string="Contraseña Temporal", readonly=True, help="Contraseña temporal para usuarios nuevos. Cambie esta contraseña después del primer acceso.")
    is_new_n8n_user = fields.Boolean(string="Usuario Nuevo en N8N", default=False, readonly=True, help="Indica si se creó un nuevo usuario en N8N o se reutilizó uno existente.")
    n8n_login_url = fields.Char(string="URL de Login N8N", compute='_compute_n8n_urls', store=False)
    n8n_invite_url_clean = fields.Char(string="Link de Invitación (limpio)", compute='_compute_n8n_urls', store=False, help="Link de invitación sin el puerto :5678")

    template_json = fields.Text(string="JSON de la Plantilla", readonly=True)
    n8n_instance_id = fields.Char(string="ID del Workflow en N8N", readonly=True, help="ID del workflow una vez sincronizado en la cuenta del cliente.")

    state = fields.Selection([
        ('pending', 'Pendiente de Sincronizar'),
        ('synced', 'Sincronizado')
    ], string="Estado", default='pending', readonly=True)

    # Campos para extensiones
    is_extension = fields.Boolean(string="Es Extensión", readonly=True,
                                   help="Indica si este workflow es una extensión de otro")
    base_workflow_instance_id = fields.Many2one('n8n.workflow.instance', string="Instancia Base",
                                                 readonly=True,
                                                 help="Instancia de workflow base del cual este es extensión")
    has_modifications = fields.Boolean(string="Tiene Modificaciones", readonly=True,
                                        help="Indica si el workflow base del cliente tiene modificaciones")
    merge_strategy = fields.Selection([
        ('full_replace', 'Reemplazo Completo'),
        ('manual_merge', 'Merge Manual')
    ], string="Estrategia de Actualización", readonly=True,
       help="Estrategia usada para actualizar el workflow")

    @api.depends('n8n_user_id', 'n8n_invite_url')
    def _compute_n8n_urls(self):
        """Calcula las URLs limpias de N8N (sin puertos)"""
        import re
        n8n_url = self.env['ir.config_parameter'].sudo().get_param('n8n_sales.n8n_url', '')

        for record in self:
            # Calcular URL de login
            if n8n_url:
                # Removemos /api/v1 si está, el puerto y agregamos /signin
                base_url = n8n_url.replace('/api/v1', '').rstrip('/')
                # Remover puerto si existe (ej: :5678)
                base_url = re.sub(r':\d+', '', base_url)
                record.n8n_login_url = f"{base_url}/signin"
            else:
                record.n8n_login_url = False

            # Limpiar URL de invitación (remover :5678)
            if record.n8n_invite_url:
                # Remover puerto (ej: :5678) del URL de invitación
                clean_url = re.sub(r':\d+/', '/', record.n8n_invite_url)
                record.n8n_invite_url_clean = clean_url
            else:
                record.n8n_invite_url_clean = False

    def action_open_sync_wizard(self):
        """
        Abre el asistente para configurar y sincronizar el workflow.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configurar y Sincronizar Workflow',
            'res_model': 'n8n.sync.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_instance_id': self.id,
            }
        }

    def _detect_workflow_modifications(self):
        """
        Compara el workflow actual del cliente en n8n con la plantilla original.
        Ignora el nodo 'configuracion_cliente' en la comparación.

        Returns:
            tuple: (has_modifications: bool, differences: list)
        """
        self.ensure_one()

        if not self.n8n_instance_id or self.state != 'synced':
            _logger.warning(f"Workflow instance {self.id} no está sincronizado. No se puede detectar modificaciones.")
            return False, []

        # Obtener credenciales de n8n
        params = self.env['ir.config_parameter'].sudo()
        n8n_url = params.get_param('n8n_sales.n8n_url')
        api_key = params.get_param('n8n_sales.n8n_api_key')

        if not n8n_url or not api_key:
            raise UserError("Credenciales maestras de N8N no configuradas.")

        headers = {"X-N8N-API-KEY": api_key}

        try:
            # Obtener workflow actual del cliente desde n8n
            _logger.info(f"Obteniendo workflow actual {self.n8n_instance_id} desde N8N...")
            response = requests.get(f"{n8n_url}/api/v1/workflows/{self.n8n_instance_id}",
                                   headers=headers, timeout=15)
            response.raise_for_status()
            current_workflow = response.json()

            # Obtener plantilla base original
            original_template = json.loads(self.template_json or '{}')

            # Filtrar nodo 'configuracion_cliente' de ambos
            current_nodes = [n for n in current_workflow.get('nodes', [])
                           if n.get('name', '').strip().lower() != 'configuracion_cliente']
            template_nodes = [n for n in original_template.get('nodes', [])
                            if n.get('name', '').strip().lower() != 'configuracion_cliente']

            differences = []

            # 1. Comparar número de nodos
            if len(current_nodes) != len(template_nodes):
                differences.append(f"Número de nodos diferente: {len(current_nodes)} actual vs {len(template_nodes)} plantilla")

            # 2. Crear mapas de nodos por ID para comparación
            current_nodes_map = {n.get('id'): n for n in current_nodes}
            template_nodes_map = {n.get('id'): n for n in template_nodes}

            # 3. Verificar nodos agregados o eliminados
            current_ids = set(current_nodes_map.keys())
            template_ids = set(template_nodes_map.keys())

            added_nodes = current_ids - template_ids
            removed_nodes = template_ids - current_ids

            if added_nodes:
                differences.append(f"Nodos agregados: {len(added_nodes)} nodos nuevos")
            if removed_nodes:
                differences.append(f"Nodos eliminados: {len(removed_nodes)} nodos")

            # 4. Comparar nodos comunes (por tipo y nombre)
            for node_id in (current_ids & template_ids):
                current_node = current_nodes_map[node_id]
                template_node = template_nodes_map[node_id]

                # Comparar tipo de nodo
                if current_node.get('type') != template_node.get('type'):
                    differences.append(f"Nodo {node_id}: tipo cambiado de {template_node.get('type')} a {current_node.get('type')}")

                # Comparar nombre de nodo
                if current_node.get('name') != template_node.get('name'):
                    differences.append(f"Nodo {node_id}: nombre cambiado de '{template_node.get('name')}' a '{current_node.get('name')}'")

                # Comparar parámetros de nodo (profundo)
                current_params = json.dumps(current_node.get('parameters', {}), sort_keys=True)
                template_params = json.dumps(template_node.get('parameters', {}), sort_keys=True)
                if current_params != template_params:
                    differences.append(f"Nodo {node_id} ('{current_node.get('name')}'): parámetros modificados")

            # 5. Comparar conexiones (excluyendo las que involucran configuracion_cliente)
            current_connections = current_workflow.get('connections', {})
            template_connections = original_template.get('connections', {})

            # Filtrar conexiones que involucran configuracion_cliente
            def filter_connections(connections_dict):
                filtered = {}
                for node_name, conn_data in connections_dict.items():
                    if node_name.strip().lower() != 'configuracion_cliente':
                        filtered[node_name] = conn_data
                return filtered

            current_connections_filtered = filter_connections(current_connections)
            template_connections_filtered = filter_connections(template_connections)

            current_conn_str = json.dumps(current_connections_filtered, sort_keys=True)
            template_conn_str = json.dumps(template_connections_filtered, sort_keys=True)

            if current_conn_str != template_conn_str:
                differences.append("Conexiones entre nodos modificadas")

            # Determinar si hay modificaciones
            has_modifications = len(differences) > 0

            if has_modifications:
                _logger.info(f"Workflow {self.id} tiene modificaciones: {differences}")
            else:
                _logger.info(f"Workflow {self.id} no tiene modificaciones respecto a la plantilla")

            return has_modifications, differences

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error al obtener workflow de N8N: {e}")
            raise UserError(f"Error al obtener el workflow desde N8N: {e}")

    def action_apply_extension_full_replace(self):
        """
        Aplica la extensión reemplazando completamente el workflow base del cliente.
        Solo funciona si merge_strategy es 'full_replace'.
        """
        self.ensure_one()

        if not self.is_extension or not self.base_workflow_instance_id:
            raise UserError("Esta instancia no es una extensión válida.")

        if self.merge_strategy != 'full_replace':
            raise UserError("Esta extensión requiere merge manual debido a modificaciones detectadas.")

        # Obtener credenciales
        params = self.env['ir.config_parameter'].sudo()
        n8n_url = params.get_param('n8n_sales.n8n_url')
        api_key = params.get_param('n8n_sales.n8n_api_key')

        if not n8n_url or not api_key:
            raise UserError("Credenciales maestras de N8N no configuradas.")

        headers = {
            "X-N8N-API-KEY": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            # Obtener la nueva plantilla (extensión)
            extension_template = json.loads(self.template_json or '{}')
            base_instance = self.base_workflow_instance_id

            _logger.info(f"Aplicando reemplazo completo: workflow {base_instance.n8n_instance_id}")

            # Preparar payload limpio para actualización
            update_payload = {
                'name': extension_template.get('name', base_instance.name),
                'nodes': extension_template.get('nodes', []),
                'connections': extension_template.get('connections', {}),
                'settings': extension_template.get('settings', {}),
            }

            # Limpiar webhookIds
            for node in update_payload.get('nodes', []):
                node.pop('webhookId', None)

            # Actualizar el workflow del cliente en n8n
            update_url = f"{n8n_url}/api/v1/workflows/{base_instance.n8n_instance_id}"
            response = requests.put(update_url, headers=headers, json=update_payload, timeout=20)
            response.raise_for_status()

            _logger.info(f"Workflow {base_instance.n8n_instance_id} actualizado exitosamente con reemplazo completo")

            # Actualizar la instancia base con la nueva plantilla
            base_instance.write({
                'template_json': self.template_json,
                'template_workflow_id': self.template_workflow_id,
            })

            # Marcar esta instancia de extensión como sincronizada
            self.write({'state': 'synced'})

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Extensión Aplicada',
                    'message': f'El workflow base ha sido actualizado completamente con la extensión {self.name}.',
                    'type': 'success',
                    'sticky': False,
                }
            }

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error al aplicar reemplazo completo: {e}")
            raise UserError(f"Error al actualizar el workflow en N8N: {e}")

    def action_apply_extension_manual_merge(self):
        """
        Aplica la extensión añadiendo solo los nodos nuevos sin conexiones.
        Incluye un Sticky Note con las instrucciones de uso.
        """
        self.ensure_one()

        if not self.is_extension or not self.base_workflow_instance_id:
            raise UserError("Esta instancia no es una extensión válida.")

        # Obtener credenciales
        params = self.env['ir.config_parameter'].sudo()
        n8n_url = params.get_param('n8n_sales.n8n_url')
        api_key = params.get_param('n8n_sales.n8n_api_key')

        if not n8n_url or not api_key:
            raise UserError("Credenciales maestras de N8N no configuradas.")

        headers = {
            "X-N8N-API-KEY": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            # Obtener workflow actual del cliente
            base_instance = self.base_workflow_instance_id
            get_url = f"{n8n_url}/api/v1/workflows/{base_instance.n8n_instance_id}"
            response_get = requests.get(get_url, headers=headers, timeout=15)
            response_get.raise_for_status()
            current_workflow = response_get.json()

            # Obtener plantilla de extensión
            extension_template = json.loads(self.template_json or '{}')

            # Filtrar nodos nuevos (excluir configuracion_cliente y nodos que ya existen)
            current_node_names = {n.get('name', '').strip().lower() for n in current_workflow.get('nodes', [])}
            extension_nodes = extension_template.get('nodes', [])

            new_nodes = [
                n for n in extension_nodes
                if n.get('name', '').strip().lower() != 'configuracion_cliente'
                and n.get('name', '').strip().lower() not in current_node_names
            ]

            if not new_nodes:
                raise UserError("No hay nodos nuevos para añadir de esta extensión.")

            # Ajustar posiciones de los nodos nuevos para evitar solapamiento
            # Los colocamos más a la derecha del workflow actual
            max_x = max([n.get('position', [0, 0])[0] for n in current_workflow.get('nodes', [])] + [0])
            for i, node in enumerate(new_nodes):
                node['position'] = [max_x + 400, i * 150]

            # Crear Sticky Note con instrucciones
            product = self.product_id
            instructions = product.extension_instructions or "Nueva extensión añadida. Conecta los nodos manualmente según tus necesidades."

            sticky_note = {
                "parameters": {
                    "content": f"## 📋 INSTRUCCIONES: {product.name}\n\n{instructions}\n\n---\n**Nodos añadidos:** {len(new_nodes)}\n\n⚠️ Conecta estos nodos manualmente a tu flujo existente.",
                    "height": 400,
                    "width": 400,
                    "color": 5  # Color amarillo/dorado
                },
                "id": f"sticky-{base_instance.id}-{self.id}",
                "name": f"Instrucciones_{product.name.replace(' ', '_')}",
                "type": "n8n-nodes-base.stickyNote",
                "typeVersion": 1,
                "position": [max_x + 400, -200]
            }

            # Añadir el sticky note y los nodos nuevos al workflow actual
            updated_nodes = current_workflow.get('nodes', []) + [sticky_note] + new_nodes

            # Preparar payload de actualización
            update_payload = {
                'name': current_workflow.get('name'),
                'nodes': updated_nodes,
                'connections': current_workflow.get('connections', {}),
                'settings': current_workflow.get('settings', {}),
            }

            # Actualizar el workflow del cliente en n8n
            update_url = f"{n8n_url}/api/v1/workflows/{base_instance.n8n_instance_id}"
            response = requests.put(update_url, headers=headers, json=update_payload, timeout=20)
            response.raise_for_status()

            _logger.info(f"Workflow {base_instance.n8n_instance_id} actualizado con merge manual: {len(new_nodes)} nodos añadidos")

            # Marcar esta instancia de extensión como sincronizada
            self.write({'state': 'synced'})

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Extensión Aplicada (Merge Manual)',
                    'message': f'Se añadieron {len(new_nodes)} nodos nuevos sin conectar. Revisa las instrucciones en el Sticky Note.',
                    'type': 'success',
                    'sticky': False,
                }
            }

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error al aplicar merge manual: {e}")
            raise UserError(f"Error al actualizar el workflow en N8N: {e}")