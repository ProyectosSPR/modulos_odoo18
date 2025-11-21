from typing import List, Tuple

from odoo import _, api, fields, models


class PreviewPrompt(models.TransientModel):
    """Wizard to preview the prompt for a selected record."""

    _name = "preview.prompt"
    _description = "Preview Prompt"

    server_action_id = fields.Many2one(
        comodel_name="ir.actions.server",
        string="Server Action",
        required=True,
        readonly=True,
    )
    object_ref = fields.Reference(
        string="Record",
        selection="_selection_target_model",
        compute="_compute_object_ref",
        readonly=False,
        store=True,
    )
    object_model = fields.Char(
        string="Model Name",
        readonly=True,
    )
    preview_text = fields.Text(
        string="Preview",
        readonly=True,
    )

    @api.model
    def _selection_target_model(self) -> List[Tuple[str, str]]:
        """Get the list of models for the reference field."""
        res_models = self.env["ir.model"].search([])
        return [(model.model, model.name) for model in res_models]

    @api.depends("object_model")
    def _compute_object_ref(self) -> None:
        for record in self:
            model = record.object_model
            if not model:
                record.object_ref = None
                continue
            res = self.env[model].search([], limit=1)
            record.object_ref = f"{model},{res.id}" if res else None

    @api.onchange("object_ref")
    def _onchange_object_ref(self) -> None:
        """Update the preview text when the record changes."""
        self.preview_text = False
        if self.object_ref and self.server_action_id:
            preview = self.server_action_id._prepare_ai_prompt(self.object_ref)
            if preview:
                self.preview_text = preview
            else:
                self.preview_text = _(
                    "Error generating preview. Check the template for errors."
                )
