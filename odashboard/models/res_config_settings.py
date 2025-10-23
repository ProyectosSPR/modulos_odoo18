import requests
import uuid
import logging
from werkzeug.urls import url_encode

from odoo import models, fields, api, _
from ..hooks import post_init_hook

_logger = logging.getLogger(__name__)

# Constants
DEFAULT_API_ENDPOINT = 'https://odashboard.app'
API_TIMEOUT = 10
REQUEST_TIMEOUT = 30


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    odashboard_plan = fields.Char(string='Odashboard Plan', config_parameter="odashboard.plan")
    odashboard_key = fields.Char(string="Odashboard Key", config_parameter="odashboard.key")
    odashboard_key_synchronized = fields.Boolean(string="Key Synchronized",
                                                 config_parameter="odashboard.key_synchronized", readonly=True)
    odashboard_uuid = fields.Char(string="Odashboard UUID", config_parameter="odashboard.uuid", readonly=True)
    odashboard_engine_version = fields.Char(string="Current Engine Version", readonly=True)

    def set_values(self):
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        uuid_param = self.env['ir.config_parameter'].sudo().get_param('odashboard.uuid')
        if not uuid_param:
            uuid_param = str(uuid.uuid4())
            self.env['ir.config_parameter'].sudo().set_param('odashboard.uuid', uuid_param)

        engine = self.env['odash.engine'].sudo()._get_single_record()

        res.update({
            'odashboard_uuid': uuid_param,
            'odashboard_engine_version': engine.version,
        })

        return res

    def action_check_engine_updates(self):
        """Check update for Odashboard engine"""
        engine = self.env['odash.engine']._get_single_record()
        result = engine.check_for_updates()

        if result:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Successful update'),
                    'message': _('The Odashboard Engine has been updated to version %s') % engine.version,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Information'),
                    'message': _('No update available. You are already using the latest version (%s)') % engine.version,
                    'type': 'info',
                    'sticky': False,
                }
            }

    def synchronize_key(self):
        """Synchronize the key with the license server"""

        # Automatically save the configuration settings first
        self.set_values()

        if not self.odashboard_key:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Please enter a key before synchronizing'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

        # Get the license API endpoint from config parameters
        api_endpoint = self.env['ir.config_parameter'].sudo().get_param('odashboard.api.endpoint',
                                                                        DEFAULT_API_ENDPOINT)

        # Verify key with external platform
        try:
            response = requests.post(
                f"{api_endpoint}/api/odashboard/license/verify",
                json={
                    'key': self.odashboard_key,
                    'uuid': self.odashboard_uuid,
                    'url': self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                },
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json().get('result')

                if result.get('valid'):
                    self.env['ir.config_parameter'].sudo().set_param('odashboard.key_synchronized', True)
                    self.env["odash.dashboard"].sudo().update_auth_token()

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Error'),
                            'message': result.get('error', _('Invalid key')),
                            'type': 'danger',
                            'sticky': False,
                        }
                    }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _('Error verifying key'),
                        'type': 'danger',
                        'sticky': False,
                    }
                }
        except requests.exceptions.RequestException as e:
            _logger.error("Connection error when verifying license key: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Connection error when verifying license key'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def desynchronize_key(self):
        """De-synchronize the key from the license server"""
        # Check if key is synchronized
        config_model = self.env['ir.config_parameter'].sudo()
        is_synchronized = bool(config_model.get_param('odashboard.key_synchronized', 'False'))
        if not is_synchronized:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('key is not synchronized'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        key = config_model.get_param('odashboard.key')
        uuid_param = config_model.get_param('odashboard.uuid')

        # Get the license API endpoint from config parameters
        api_endpoint = config_model.get_param('odashboard.api.endpoint', DEFAULT_API_ENDPOINT)

        # Notify the license server about desynchronization
        try:
            requests.post(
                f"{api_endpoint}/api/odashboard/license/unlink",
                json={
                    'key': key,
                    'uuid': uuid_param
                },
                timeout=API_TIMEOUT
            )
            self._clear_odashboard_data()
        except Exception as e:
            _logger.error("Error during key desynchronization: %s", str(e))
            self._clear_odashboard_data()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def get_my_key(self):
        """
        Call the post_init_hook to create and sync a demo key
        """
        post_init_hook(self.env)

    def _clear_odashboard_data(self):
        """Clear all odashboard-related configuration data"""
        config_params = self.env['ir.config_parameter'].sudo()
        config_params.set_param('odashboard.key_synchronized', False)
        config_params.set_param('odashboard.key', '')
        config_params.set_param('odashboard.plan', '')
        config_params.set_param('odashboard.api.token', '')

        # Update the current record
        self.write({
            'odashboard_key': '',
            'odashboard_key_synchronized': False,
        })

    def action_manage_plan(self):
        """Open the O'Dashboard billing/plan management page in a new tab."""
        config = self.env['ir.config_parameter'].sudo()
        base = config.get_param('odashboard.api.endpoint', DEFAULT_API_ENDPOINT)
        key = config.get_param('odashboard.key')

        # Use a stable path on the portal for plan management
        url = f"{base.rstrip('/')}/odash/manage-plan?key={key}"

        # Redirect to the URL (open in a new tab)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
