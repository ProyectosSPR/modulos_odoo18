# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class AIAgentProfile(models.Model):
    _name = 'ai.agent.profile'
    _description = 'Perfil de Agente de IA'
    _order = 'is_default desc, active desc, name'

    # ========== IDENTIFICACIÓN ==========
    name = fields.Char(
        string="Nombre del Agente",
        required=True,
        help="Nombre descriptivo del perfil del agente"
    )

    code = fields.Char(
        string="Código Único",
        required=True,
        help="Identificador único para este perfil (usado por N8N)"
    )

    description = fields.Text(
        string="Descripción",
        help="Descripción detallada de qué hace este agente"
    )

    # ========== PROPIETARIO Y MULTI-TENANT ==========
    company_id = fields.Many2one(
        'res.company',
        string="Empresa",
        required=True,
        default=lambda self: self.env.company,
        help="Empresa propietaria de esta configuración"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Propietario",
        help="Usuario propietario de esta configuración. Si está vacío, es global para la empresa."
    )

    created_by = fields.Many2one(
        'res.users',
        string="Creado Por",
        default=lambda self: self.env.user,
        readonly=True,
        help="Usuario que creó esta configuración"
    )

    # ========== CONTROL DE VISIBILIDAD Y USO ==========
    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desactivado, no se usará ni aparecerá en consultas de N8N"
    )

    shared_globally = fields.Boolean(
        string="Compartir con Todos",
        default=False,
        help="Si está activado, TODOS los usuarios pueden ver y usar este perfil (solo administradores)"
    )

    is_template = fields.Boolean(
        string="Es Template",
        default=False,
        help="Indica si este perfil es una plantilla base proporcionada por Automateai"
    )

    is_default = fields.Boolean(
        string="Configuración por Defecto",
        default=False,
        help="Marca esta configuración como la predeterminada para este usuario"
    )

    # ========== CONFIGURACIÓN DEL AGENTE IA ==========
    system_prompt = fields.Text(
        string="System Prompt",
        required=True,
        help="Prompt principal del sistema que define el comportamiento del agente",
        default="Eres un asistente útil y amigable."
    )

    context_instructions = fields.Text(
        string="Instrucciones Adicionales",
        help="Instrucciones de contexto adicionales que se añaden al prompt"
    )

    # ========== RELACIONES ==========
    action_ids = fields.One2many(
        'ai.action',
        'agent_profile_id',
        string="Acciones Disponibles",
        help="Acciones que este agente puede ejecutar"
    )

    action_count = fields.Integer(
        string="# Acciones",
        compute='_compute_action_count',
        store=True
    )

    variable_ids = fields.One2many(
        'ai.config.variable',
        'agent_profile_id',
        string="Variables de Configuración",
        help="Variables que se pasarán a N8N como config_variables en formato JSON"
    )

    config_variables_json = fields.Text(
        string="Config Variables (JSON)",
        compute='_compute_config_variables_json',
        store=False,
        help="JSON generado automáticamente a partir de las variables configuradas"
    )

    # ========== METADATOS Y ANALYTICS ==========
    usage_count = fields.Integer(
        string="Veces Usado",
        default=0,
        readonly=True,
        help="Número de veces que este perfil ha sido usado"
    )

    last_used_date = fields.Datetime(
        string="Último Uso",
        readonly=True,
        help="Fecha y hora del último uso"
    )

    # ========== COMPUTED FIELDS ==========
    display_name_with_owner = fields.Char(
        string="Nombre Completo",
        compute='_compute_display_name_with_owner',
        store=False
    )

    # ========== CONSTRAINTS ==========
    _sql_constraints = [
        ('code_company_partner_unique',
         'UNIQUE(code, company_id, partner_id)',
         'El código debe ser único por empresa y usuario!')
    ]

    @api.depends('action_ids')
    def _compute_action_count(self):
        for record in self:
            record.action_count = len(record.action_ids)

    @api.depends('variable_ids', 'variable_ids.name', 'variable_ids.value')
    def _compute_config_variables_json(self):
        """Construye el JSON de config_variables a partir de las variables configuradas"""
        import json
        for record in self:
            if record.variable_ids:
                config_vars = {var.name: var.value for var in record.variable_ids}
                record.config_variables_json = json.dumps({"config_variables": config_vars}, indent=2)
            else:
                record.config_variables_json = json.dumps({"config_variables": {}}, indent=2)

    @api.depends('name', 'partner_id', 'shared_globally', 'is_template')
    def _compute_display_name_with_owner(self):
        for record in self:
            if record.is_template:
                record.display_name_with_owner = f"[Template] {record.name}"
            elif record.shared_globally:
                record.display_name_with_owner = f"[Compartido] {record.name}"
            elif record.partner_id:
                record.display_name_with_owner = f"{record.name} ({record.partner_id.name})"
            else:
                record.display_name_with_owner = record.name

    @api.constrains('is_default', 'partner_id', 'company_id')
    def _check_only_one_default(self):
        """Asegurar que solo haya una configuración por defecto por usuario"""
        for record in self:
            if record.is_default:
                other_defaults = self.search([
                    ('id', '!=', record.id),
                    ('partner_id', '=', record.partner_id.id if record.partner_id else False),
                    ('company_id', '=', record.company_id.id),
                    ('is_default', '=', True)
                ])
                if other_defaults:
                    raise ValidationError(
                        "Ya existe una configuración por defecto para este usuario. "
                        "Desactiva la otra primero."
                    )

    @api.constrains('shared_globally')
    def _check_shared_globally_permission(self):
        """Solo administradores pueden marcar como compartido globalmente"""
        for record in self:
            if record.shared_globally and not self.env.user.has_group('base.group_system'):
                raise ValidationError(
                    "Solo los administradores pueden crear configuraciones compartidas globalmente."
                )

    def action_clone_template(self):
        """Clona este template para crear una configuración personal"""
        self.ensure_one()

        if not self.shared_globally and not self.is_template:
            raise UserError("Solo puedes clonar templates compartidos.")

        # Crear copia personal
        new_profile = self.copy({
            'name': f"{self.name} (Mi Copia)",
            'code': f"{self.code}_copy_{self.env.user.id}",
            'partner_id': self.env.user.partner_id.id,
            'shared_globally': False,
            'is_template': False,
            'is_default': False,
            'created_by': self.env.user.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Mi Configuración Clonada',
            'res_model': 'ai.agent.profile',
            'res_id': new_profile.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_set_as_default(self):
        """Marca esta configuración como la por defecto del usuario"""
        self.ensure_one()

        # Desactivar otras configuraciones por defecto del mismo usuario
        other_defaults = self.search([
            ('id', '!=', self.id),
            ('partner_id', '=', self.partner_id.id if self.partner_id else False),
            ('company_id', '=', self.company_id.id),
            ('is_default', '=', True)
        ])
        other_defaults.write({'is_default': False})

        # Activar esta como por defecto
        self.write({'is_default': True, 'active': True})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Configuración Actualizada',
                'message': f'{self.name} es ahora tu configuración por defecto.',
                'type': 'success',
                'sticky': False,
            }
        }

    def increment_usage(self):
        """Incrementa el contador de uso"""
        self.ensure_one()
        self.sudo().write({
            'usage_count': self.usage_count + 1,
            'last_used_date': fields.Datetime.now()
        })

    def action_view_actions(self):
        """Abre la vista de acciones de este perfil"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Acciones de {self.name}',
            'res_model': 'ai.action',
            'view_mode': 'list,form',
            'domain': [('agent_profile_id', '=', self.id)],
            'context': {'default_agent_profile_id': self.id},
        }

    @api.model
    def get_config_for_api(self, company_id, partner_id=None):
        """
        Método para API: Obtiene la configuración activa para un usuario/empresa.
        Lógica de búsqueda:
        1. Config por defecto del usuario (is_default=True)
        2. Config activa del usuario
        3. Template compartido globalmente
        """
        domain_base = [('active', '=', True)]

        # Primero: Buscar config por defecto del usuario
        if partner_id:
            user_default = self.search(
                domain_base + [
                    ('partner_id', '=', partner_id),
                    ('company_id', '=', company_id),
                    ('is_default', '=', True)
                ],
                limit=1
            )
            if user_default:
                user_default.increment_usage()
                return user_default._format_config_for_api()

        # Segundo: Buscar cualquier config activa del usuario
        if partner_id:
            user_config = self.search(
                domain_base + [
                    ('partner_id', '=', partner_id),
                    ('company_id', '=', company_id)
                ],
                limit=1,
                order='last_used_date desc'
            )
            if user_config:
                user_config.increment_usage()
                return user_config._format_config_for_api()

        # Tercero: Buscar template compartido globalmente
        shared_config = self.search(
            domain_base + [('shared_globally', '=', True)],
            limit=1,
            order='usage_count desc'
        )
        if shared_config:
            shared_config.increment_usage()
            return shared_config._format_config_for_api()

        return None

    def _format_config_for_api(self):
        """Formatea la configuración para respuesta de API"""
        self.ensure_one()

        # Construir config_variables
        config_vars = {var.name: var.value for var in self.variable_ids}

        return {
            'agent_profile': {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'description': self.description or '',
                'system_prompt': self.system_prompt,
                'context_instructions': self.context_instructions or '',
                'is_template': self.is_template,
                'is_shared': self.shared_globally,
            },
            'config_variables': config_vars,
            'actions': [action._format_for_api() for action in self.action_ids if action.active]
        }
