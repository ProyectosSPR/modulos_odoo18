import logging
import sys
import traceback
from typing import Literal

from odoo import _, api, fields, models

from ..tools.env_utils import new_environment

_logger = logging.getLogger(__name__)


class AiLog(models.Model):
    _name = "ai.log"
    _description = "AI Log"

    name = fields.Char(
        string="Summary",
        required=True,
        index="trigram",
    )
    res_model = fields.Char(
        string="Resource Model",
    )
    res_id = fields.Many2oneReference(
        string="Resource ID",
        model_field="res_model",
    )
    description = fields.Text()
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        default=lambda self: self.env.user,
    )
    date = fields.Datetime()
    level = fields.Selection(
        selection=[
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("success", "Success"),
        ],
    )
    active = fields.Boolean(default=True)

    @api.autovacuum
    def _archive_ai_log(self):
        """Archive logs."""
        self.sudo().search(
            [
                ("active", "=", True),
                ("date", "<", fields.Datetime.subtract(fields.Datetime.now(), days=30)),
            ]
        ).active = False

    def action_view_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Record"),
            "view_mode": "form",
            "res_model": self.res_model,
            "res_id": self.res_id,
        }

    @api.model
    def log_msg(
        self,
        level: Literal["info", "warning", "error", "success"],
        summary: str,
        description: str = None,
        res_model: str = None,
        res_id: int = None,
        user_id: int = None,
    ):
        if description is None:
            description = ""

        if res_model is None:
            res_model = self._name

        if res_id is None:
            res_id = self.id

        if user_id is None:
            user_id = self.env.user.id

        exc_info = False
        if level == "error":
            exc_info = True
            info = sys.exc_info()
            formatted_info = "".join(traceback.format_exception(*info))
            if description:
                description += "\n" + formatted_info
            else:
                description = formatted_info
        with new_environment(self.env.cr.dbname) as new_env:
            new_cr = new_env.cr
            new_cr.execute(
                """
                INSERT INTO ai_log (date,
                                    active,
                                    name,
                                    res_model,
                                    res_id,
                                    description,
                                    user_id,
                                    level
                                    )
                     VALUES (now() AT TIME ZONE 'UTC',
                            TRUE,
                            %(name)s,
                            %(res_model)s,
                            %(res_id)s,
                            %(description)s,
                            %(user_id)s,
                            %(level)s
                            )
                  RETURNING "id";
                """,
                {
                    "name": summary,
                    "res_model": res_model,
                    "res_id": res_id,
                    "description": description,
                    "user_id": user_id,
                    "level": level,
                },
            )

            msg = summary
            if description:
                msg = f"{msg}\n\n{description}"

            if hasattr(_logger, level):
                getattr(_logger, level)(msg, exc_info=exc_info)

            ids = [id_ for (id_,) in new_cr.fetchall()]
            records = new_env["ai.log"].browse(ids)
            return records
