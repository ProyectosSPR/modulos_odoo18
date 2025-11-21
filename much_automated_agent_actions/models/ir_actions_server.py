import base64
import logging
import threading
from typing import Any, Dict, List, Optional

from pytz import timezone  # NOSONAR

from odoo import _, api, fields, models, tools as odoo_tools
from odoo.tools.mail import html_to_inner_content

from ..tools import _async_notify, merge_dict, new_environment, parse_markdown
from .ai_service import AIFiles

_logger = logging.getLogger(__name__)


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("generative_ai", "Generative AI")],
        ondelete={"generative_ai": "set default"},
    )

    ai_model_id = fields.Many2one(
        comodel_name="ai.model",
        domain="[('active', '=', True)]",
        ondelete="restrict",
        string="AI Model",
    )
    prompt_template = fields.Text(
        help="Jinja2-style template for prompt generation",
    )
    include_report_id = fields.Many2one(
        comodel_name="ir.actions.report",
        domain="[('model', '=', model_name)]",
        help="Optional report to include",
    )
    include_all_attachments = fields.Boolean(
        default=False, help="Include all attachments"
    )
    include_chatter = fields.Selection(
        selection=[
            ("none", "None"),
            ("mails", "Mails"),
            ("mails_notes", "Mails & Notes"),
            ("all", "All Chatter"),
        ],
        default="none",
        required=True,
    )
    include_full_object_data = fields.Boolean(
        default=False,
        help="Include full object data in JSON format at the end of the prompt",
    )
    output_destination = fields.Selection(
        selection=[
            ("chatter", "Chatter"),
            ("field", "Field"),
            ("activity", "Create Activity"),
        ],
        default="chatter",
        required=True,
    )
    output_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        domain="[('model', '=', model_name), "
        "('ttype', 'in', ('html', 'text', 'char'))]",
        help="Field to store the output",
    )
    output_activity_type_id = fields.Many2one(
        comodel_name="mail.activity.type",
        string="Activity Type",
    )
    output_activity_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned to",
    )

    def _get_action_name(self):
        if automation := self.base_automation_id:
            return automation.name
        return self.name

    def _run_action_generative_ai(self, eval_context=None) -> bool:  # NOSONAR
        """Execute the generative AI action."""
        self.ensure_one()

        if not self.ai_model_id:
            return False

        # Get the AI service
        provider_code = self.ai_model_id.provider_id.code
        company_id = self.ai_model_id.provider_id.company_id.id
        try:
            ai_service = self.env["ai.service.factory"].get_service(
                provider_code, company_id
            )
        except Exception as exc:  # noqa
            self._notify_error(
                _("AI Service Error"),
                _("Error getting AI service\n") + str(exc),
                summary="Error getting AI service",
            )
            return False

        # Set up a clean context for records
        res_ids = self._context.get("active_ids", [self._context.get("active_id")])
        cleaned_ctx = self._prepare_clean_context()
        records = self.env[self.model_name].with_context(**cleaned_ctx).browse(res_ids)

        for record in records:
            if not record.exists():
                continue

            self.env.user.notify_success(
                message=_(
                    "Agent '%(action_name)s' is working on it!",
                    action_name=self._get_action_name(),
                ),
                title=_("AI service triggered"),
            )
            _logger.info("Offload to AI thread")
            # Execute the AI processing in a separate thread
            thread = threading.Thread(
                target=self._process_record_in_thread,
                args=(
                    self.id,
                    record.id,
                    ai_service,
                    self.env.cr.dbname,
                    self.env.uid,
                    cleaned_ctx,
                ),
            )
            thread.start()

        return False

    def _process_record_in_thread(
        self, server_action_id, record_id, ai_service, dbname, uid, context
    ):
        """Process a record in a separate thread."""
        # Create a new environment with the same credentials
        with new_environment(dbname, uid=uid, context=context) as env:
            new_cr = env.cr
            try:
                server_action = env["ir.actions.server"].sudo().browse(server_action_id)
                record = env[server_action.model_name].sudo().browse(record_id)

                if not record.exists():
                    return

                if not (prompt := server_action._prepare_ai_prompt(record)):
                    return

                files = server_action._prepare_ai_files(record)

                if not (
                    response := server_action._generate_ai_response(
                        ai_service, prompt, files
                    )
                ):
                    return

                server_action._process_ai_response(record, response, context=context)

                new_cr.commit()

                _async_notify(
                    uid=uid,
                    type_="success",
                    title="AI Service",
                    message="AI Service is done",
                )

                _logger.info("AI Thread execution done")

            except Exception as e:
                new_cr.rollback()
                _logger.exception("Error processing record in thread: %s", e)
            finally:
                new_cr.close()

    def _notify_error(self, title: str, message: str, summary: str = None) -> None:
        """Helper to show error notification to the user and log the error.

        Args:
            title: The error title
            message: The error message
        """
        _async_notify(
            uid=self.env.uid,
            type_="danger",
            title=title,
            message=message,
            show_refresh_button=False,
        )
        if summary is None:
            summary = message.split("\n")[0] if message else ""

        try:
            self.env["ai.log"].log_msg(
                level="error",
                summary=summary,
                res_model=self._context.get("active_model"),
                res_id=self._context.get("active_id"),
            )
        except Exception as exc:
            _logger.error(f"Failed to log error: {exc}", exc_info=True)

    def _prepare_clean_context(self) -> Dict[str, Any]:
        """Prepare a clean context for record operations."""
        cleaned_ctx = dict(self.env.context)
        cleaned_ctx.pop("default_type", None)
        cleaned_ctx.pop("default_parent_id", None)
        cleaned_ctx["mail_create_nosubscribe"] = True
        cleaned_ctx["mail_post_autofollow"] = False
        return cleaned_ctx

    @api.model
    def _get_prompt_eval_context(self, record=None) -> Dict[str, Any]:
        """Prompt evaluation context."""
        return {
            "env": self.env,
            "model": record._name,
            "uid": self._uid,
            "user": self.env.user,
            "self": record,
            "time": odoo_tools.safe_eval.time,
            "datetime": odoo_tools.safe_eval.datetime,
            "dateutil": odoo_tools.safe_eval.dateutil,
            "timezone": timezone,
            "float_compare": odoo_tools.float_compare,
            "b64encode": base64.b64encode,
            "b64decode": base64.b64decode,
            "merge_dict": merge_dict,
            "Command": fields.Command,
            "object": record,
            "record": record,
        }

    def _prepare_ai_prompt(self, record) -> str | bool:
        """Prepare and render the AI prompt template."""
        if not self.prompt_template:
            return False

        try:
            eval_context = self._get_prompt_eval_context(record)
            result = self.env["mail.render.mixin"]._render_template(
                self.prompt_template,
                record._name,
                record.ids,
                engine="inline_template",
                add_context=eval_context,
            )
            return result[record.id]

        except Exception as exc:  # noqa
            self._notify_error(
                _("AI Action Error"),
                _("Error rendering prompt template\n") + str(exc),
                summary="Error rendering prompt template",
            )
            return False

    def _prepare_ai_files(self, record: Any) -> AIFiles:
        """Prepare files and chatter content for AI processing.

        Args:
            record: The record being processed

        Returns:
            AIFiles: A dictionary containing files and chatter content
        """
        result: AIFiles = AIFiles(
            file_data=[],
            chatter="",
            record_data={},
        )

        # Process report, attachments, and chatter
        self._prepare_report_file(record, result)
        self._prepare_attachment_files(record, result)
        result["chatter"] = self._prepare_chatter_content(record)
        result["record_data"] = self._prepare_record_data(record)

        return result

    def _prepare_report_file(self, record: Any, result: AIFiles) -> None:
        """Add a report PDF to the result if specified and allowed.

        Args:
            record: The record being processed
            result: The AIFiles object to update
        """
        if not (self.include_report_id and self.ai_model_id.files_allowed):
            return

        try:
            report_content, report_format = self.include_report_id._render_qweb_pdf(
                self.include_report_id, res_ids=record.id
            )
            if report_format == "pdf":
                result["file_data"].append(
                    {
                        "filename": f"{self.include_report_id.name}.pdf",
                        "data": base64.b64encode(report_content).decode("utf-8"),
                    }
                )
        except Exception as exc:  # noqa
            self._notify_error(
                _("AI Report Error"),
                _("Error rendering report\n") + str(exc),
                summary="Error rendering report",
            )

    def _prepare_attachment_files(self, record: Any, result: AIFiles) -> None:
        """Add attachment files to the result if specified and allowed.

        Args:
            record: The record being processed
            result: The AIFiles object to update
        """
        if not self.include_all_attachments:
            return

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", record._name),
                ("res_id", "=", record.id),
                ("mimetype", "in", ["application/pdf", "image/jpeg", "image/png"]),
            ]
        )

        file_count = len(result["file_data"])
        for attachment in attachments:
            if file_count >= self.ai_model_id.max_files:
                break

            try:
                self._add_attachment_to_result(attachment, result)
                file_count += 1
            except Exception as exc:  # noqa
                self._notify_error(
                    _("AI Attachment Error"),
                    _(
                        "Error processing attachment "
                        "'%(attachment_name)s'\n%(exception)s",
                        attachment_name=attachment.name,
                        exception=str(exc),
                    ),
                    summary=f"Error processing attachment '{attachment.name}'",
                )

    def _add_attachment_to_result(self, attachment: Any, result: AIFiles) -> bool:
        """Add a single attachment to the result.

        Args:
            attachment: The attachment record
            result: The AIFiles object to update

        Returns:
            bool: True if attachment was added, False otherwise
        """
        if attachment.mimetype == "application/pdf" and self.ai_model_id.files_allowed:
            result["file_data"].append(
                {
                    "filename": attachment.name,
                    "data": attachment.datas,
                }
            )
            return True
        elif (
            attachment.mimetype in ["image/jpeg", "image/png"]
            and self.ai_model_id.images_allowed
        ):
            result["file_data"].append(
                {
                    "filename": attachment.name,
                    "data": attachment.datas,
                    "mimetype": attachment.mimetype,
                }
            )
            return True
        return False

    def _prepare_chatter_content(self, record: Any) -> str:
        """Prepare chatter content from record messages.

        Args:
            record: The record being processed

        Returns:
            str: Formatted chatter content
        """
        if self.include_chatter == "none" or not hasattr(record, "message_ids"):
            return ""

        messages = record.message_ids
        chatter_text: List[str] = []

        for message in messages:
            if not self._should_include_message(message):
                continue

            author = message.author_id.name or message.email_from or "System"
            date = message.date.strftime("%Y-%m-%d %H:%M:%S")
            body = self._clean_message_body(message.body)

            chatter_text.append(f"[{date}] {author}: {body}")

        return "\n\n".join(chatter_text) if chatter_text else ""

    def _should_include_message(self, message: Any) -> bool:
        """Determine if a message should be included in chatter content.

        Args:
            message: The message record

        Returns:
            bool: True if a message should be included, False otherwise
        """
        if self.include_chatter == "all":
            return True
        if self.include_chatter == "mails" and message.message_type == "email":
            return True
        if self.include_chatter == "mails_notes" and message.message_type in [
            "email",
            "comment",
        ]:
            return True
        return False

    def _clean_message_body(self, body: str) -> str:
        """Clean HTML tags from the message body.

        Args:
            body: The HTML body text

        Returns:
            str: Cleaned body text
        """
        return html_to_inner_content(body)

    def _prepare_record_data(self, record: Any) -> Dict[str, Any]:
        record_data: Dict[str, Any] = {}
        if self.include_full_object_data:
            try:
                record_data = record.read([], load="_classic_write")[0]
                return record_data
            except Exception as data_exc:
                self._notify_error(
                    _("AI Data Error"),
                    _("Error adding record data to prompt\n") + str(data_exc),
                    summary="Error adding record data to prompt",
                )
                return record_data

        return record_data

    def _generate_ai_response(
        self, ai_service: Any, prompt: str, files: Optional[AIFiles] = None
    ) -> str | bool:
        """Generate text response from AI service."""
        try:
            ai_model = self.ai_model_id
            return ai_service.generate_text(
                prompt=prompt,
                model_name=ai_model.technical_name,
                files=files,
                temperature=ai_model.temperature,
                top_p=ai_model.top_p,
                top_k=ai_model.top_k,
                max_tokens=ai_model.max_tokens,
            )
        except Exception as exc:  # noqa
            self._notify_error(
                _("AI Generation Error"),
                _("Error generating text\n") + str(exc),
                summary="Error generating text",
            )
            return False

    def _process_ai_response(
        self, record: Any, response: str, context: dict = None
    ) -> bool:
        """Process the AI-generated response based on output configuration."""
        if self.output_destination == "chatter":
            response_ = parse_markdown(response)
            record.message_post(
                body=response_,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )
            return True

        if self.output_destination == "activity":
            context = context or {}
            response_ = parse_markdown(response)
            activity_type = self.output_activity_type_id
            date_deadline = activity_type._get_date_deadline()
            summary = _(
                "Agent '%(action_name)s' created an activity!",
                action_name=self._get_action_name(),
            )
            with new_environment(
                self.env.cr.dbname, uid=self.env.uid, context=context
            ) as env:
                new_cr = env.cr
                env["mail.activity"].create(
                    {
                        "activity_type_id": activity_type.id,
                        "automated": True,
                        "date_deadline": date_deadline,
                        "note": response_,
                        "res_id": record.id,
                        "res_model_id": self.model_id.id,
                        "summary": summary,
                        "user_id": self.output_activity_user_id.id,
                    }
                )
                new_cr.commit()
            return True

        if self.output_destination == "field" and self.output_field_id:
            if self.output_field_id.model_id.model != self.model_id.model:
                self._notify_error(
                    _("AI Output Error"),
                    _(
                        "Output field '%(field_name)s' "
                        "does not exist on model '%(model_name)s'",
                        field_name=self.output_field_id.name,
                        model_name=self.model_id.model,
                    ),
                    summary=f"Output field '{self.output_field_id.name}' "
                    f"does not exist on model '{self.model_id.model}'",
                )
                return False

            try:
                response_ = (
                    parse_markdown(response)
                    if self.output_field_id.ttype == "html"
                    else response
                )
                record.write({self.output_field_id.name: response_})
                return True
            except Exception as exc:  # noqa
                self._notify_error(
                    _("AI Output Error"),
                    _(
                        "Error writing to field '%(field_name)s'\n%(exception)s",
                        field_name=self.output_field_id.name,
                        exception=str(exc),
                    ),
                    summary=f"Error writing to field '{self.output_field_id.name}'",
                )
                return False

        return True

    def action_preview_prompt(self) -> Dict[str, Any]:
        """Open a wizard to preview the prompt for the selected record."""
        self.ensure_one()

        return {
            "name": "Preview Prompt",
            "type": "ir.actions.act_window",
            "res_model": "preview.prompt",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_server_action_id": self.id,
                "default_object_model": self.model_name,
            },
        }
