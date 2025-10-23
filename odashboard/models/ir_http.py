from odoo import models, api, _
from odoo.http import request
from odoo.tools import get_lang
from werkzeug.exceptions import Unauthorized


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_api_key_dashboard(cls):
        if request.httprequest.method == "OPTIONS":
            return

        api_key = request.httprequest.headers.get("Authorization")
        if not api_key or len(api_key) < 8:
            raise Unauthorized("Authorization header with API key missing")
        api_key = api_key[7:]

        # Make sure the lang in the context always match lang installed in the Odoo System
        context_lang = request.context.get("lang") or "en_US"
        lang_code = get_lang(request.env, context_lang).code
        request.session.context["lang"] = lang_code
        request.update_context(lang=lang_code)

        dashboard = request.env['odash.dashboard'].sudo().search([('token', '=', api_key)], limit=1)

        if not dashboard:
            raise Unauthorized(_("Invalid token"))

        request.update_env(
            user=dashboard.user_id,
            context=dict(request.context, page_id=dashboard.page_id, dashboard_id=dashboard)
        )
