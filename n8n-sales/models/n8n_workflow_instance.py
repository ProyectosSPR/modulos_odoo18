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
    
    template_json = fields.Text(string="JSON de la Plantilla", readonly=True)
    n8n_instance_id = fields.Char(string="ID del Workflow en N8N", readonly=True, help="ID del workflow una vez sincronizado en la cuenta del cliente.")
    
    state = fields.Selection([
        ('pending', 'Pendiente de Sincronizar'),
        ('synced', 'Sincronizado')
    ], string="Estado", default='pending', readonly=True)

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