from odoo import api, fields, models


class AiProvider(models.Model):
    _name = "ai.provider"
    _description = "AI Provider"
    _order = "id, sequence"

    sequence = fields.Integer(default=1)
    name = fields.Char(required=True)
    code = fields.Char(
        required=True,
        help="Technical code (e.g., openai, anthropic)",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="cascade",
    )
    api_key = fields.Char(
        string="API Key",
    )
    active = fields.Boolean(default=True)


class AiModel(models.Model):
    _name = "ai.model"
    _description = "AI Model"
    _order = "id, sequence"

    sequence = fields.Integer(default=1)
    name = fields.Char(
        required=True,
        help="Human-readable model name",
    )
    provider_id = fields.Many2one(
        comodel_name="ai.provider",
        required=True,
        ondelete="cascade",
    )
    technical_name = fields.Char(
        required=True,
        help="Model identifier in the provider's API",
    )
    files_allowed = fields.Boolean(
        default=False,
        help="Whether the model supports file attachments",
    )
    images_allowed = fields.Boolean(
        default=False,
        help="Whether the model supports image attachments",
    )
    max_files = fields.Integer(
        help="Maximum number of files supported",
    )
    creativity_preset = fields.Selection(
        selection=[
            ("factual", "Factual"),
            ("balanced", "Balanced"),
            ("creative", "Creative"),
        ],
        default="balanced",
        string="Creativity Level",
    )
    length_preset = fields.Selection(
        selection=[
            ("short", "Short"),
            ("long", "Long"),
        ],
        default="long",
        string="Response Length",
        help="- Short (400 tokens)\n- Long (provider's default max)",
    )
    temperature = fields.Float(
        compute="_compute_creativity_preset",
        store=True,
        readonly=False,
    )
    top_p = fields.Float(
        compute="_compute_creativity_preset",
        store=True,
        readonly=False,
        string="top_p",
    )
    top_k = fields.Float(
        compute="_compute_creativity_preset",
        store=True,
        readonly=False,
        string="top_k",
    )
    max_tokens = fields.Integer(
        compute="_compute_max_tokens",
        store=True,
        readonly=False,
    )
    active = fields.Boolean(default=True)

    @api.depends("creativity_preset")
    def _compute_creativity_preset(self):
        for record in self:
            service_mapping = self.env["ai.service.factory"]._get_service_mapping()
            service_class = service_mapping.get(record.provider_id.code)
            provider_defaults = service_class.default_content_config()
            creativity_preset = provider_defaults.get(record.creativity_preset, {})

            record.temperature = creativity_preset.get("temperature")
            record.top_p = creativity_preset.get("top_p")
            record.top_k = creativity_preset.get("top_k")

    @api.depends("length_preset")
    def _compute_max_tokens(self):
        for record in self:
            record.max_tokens = record.length_preset == "short" and 400
