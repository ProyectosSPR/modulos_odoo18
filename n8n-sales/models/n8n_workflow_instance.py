# -*- coding: utf-8 -*-
from odoo import models, fields, api

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
    n8n_login_url = fields.Char(string="URL de Login N8N", compute='_compute_n8n_login_url', store=False)

    template_json = fields.Text(string="JSON de la Plantilla", readonly=True)
    n8n_instance_id = fields.Char(string="ID del Workflow en N8N", readonly=True, help="ID del workflow una vez sincronizado en la cuenta del cliente.")

    state = fields.Selection([
        ('pending', 'Pendiente de Sincronizar'),
        ('synced', 'Sincronizado')
    ], string="Estado", default='pending', readonly=True)

    @api.depends('n8n_user_id')
    def _compute_n8n_login_url(self):
        """Calcula la URL de login base de N8N"""
        n8n_url = self.env['ir.config_parameter'].sudo().get_param('n8n_sales.n8n_url', '')
        for record in self:
            if n8n_url:
                # Removemos /api/v1 si está y agregamos /signin
                base_url = n8n_url.replace('/api/v1', '').rstrip('/')
                record.n8n_login_url = f"{base_url}/signin"
            else:
                record.n8n_login_url = False

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