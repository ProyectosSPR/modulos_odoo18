from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound
import requests
from .api_helper import ApiHelper


class Main(http.Controller):

    @http.route('/dashboard/public/<string:page_id>/<string:access_token>', type='http', auth='public', website=True)
    def dashboard_public_page(self, page_id, access_token, **kwargs):
        page = request.env['odash.config'].sudo().search([('is_page_config', '=', True), ('id', '=', page_id)], limit=1)
        if not page or page.access_token != access_token or not page.allow_public_access:
            raise NotFound()
        connection_url = request.env['odash.dashboard'].sudo().get_public_dashboard(page.id)
        return request.render('odashboard.dashboard_public_view', {
            'connection_url': connection_url,
        })

    @http.route('/dashboard/public/<string:page_id>/<string:access_token>/pdf', type='http', auth='public', website=True)
    def dashboard_public_page_pdf(self, page_id, access_token, **kwargs):
        page = request.env['odash.config'].sudo().search([('is_page_config', '=', True), ('id', '=', page_id)], limit=1)
        if not page or page.secret_access_token != access_token:
            raise NotFound()
        connection_url = request.env['odash.dashboard'].sudo().get_public_dashboard(page.id)

        pdf_url = request.env['ir.config_parameter'].sudo().get_param('odashboard.pdf.url', 'https://pdf.odashboard.app')
        payload = {"url": f"{connection_url}&is_pdf=true"}

        try:
            resp = requests.post(f"{pdf_url}/render", json=payload, timeout=120)
        except requests.RequestException as e:
            return request.make_response(
                '{"error":"PDF service unreachable","detail":"%s"}' % str(e).replace('"', '\\"'),
                headers=[('Content-Type', 'application/json')],
            )

        if resp.status_code != 200 or resp.headers.get('Content-Type', '').startswith('application/json'):
            return request.make_response(
                resp.content or b'{"error":"PDF service returned an error"}',
                headers=[('Content-Type', resp.headers.get('Content-Type', 'application/json'))],
            )

            # Success: return the PDF inline
        return request.make_response(
            resp.content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="odashboard.pdf"'),
            ],
        )

    @http.route(["/api/odash/refresh-dashboard"], type='http', auth='api_key_dashboard', csrf=False, methods=['post'],
                cors="*")
    def refresh_dashboard(self, **kw):
        dashboard_id = request.env.context.get('dashboard_id')
        data = ApiHelper.load_json_data(request)
        dashboard_id.ask_refresh(data.get("company_ids"))
        return ApiHelper.json_valid_response("ok", 200)
