# -*- coding: utf-8 -*-

import uuid
import requests
import logging
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Post-init hook to create and synchronize demo key with O'Solutions system."""
    
    try:

        # Generate UUID4 for the demo key
        demo_key_uuid = str(uuid.uuid4())
        
        # Get database UUID
        odashboard_uuid = env['ir.config_parameter'].sudo().get_param('odashboard.uuid')
        if not odashboard_uuid:
            # Generate database UUID if it doesn't exist
            odashboard_uuid = str(uuid.uuid4())
            env['ir.config_parameter'].sudo().set_param('odashboard.uuid', odashboard_uuid)
        
        # Get instance URL
        base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not base_url:
            _logger.error("Cannot determine instance URL, skipping demo key creation")
            return
        
        # Get O'Solutions API endpoint
        api_endpoint = env['ir.config_parameter'].sudo().get_param('odashboard.api.endpoint')
        # Prepare data for API call
        api_data = {
            'key': demo_key_uuid,
            'uuid': odashboard_uuid,
            'url': base_url,
        }
        
        # Make secure API call to create demo key
        try:
            response = requests.post(
                f"{api_endpoint}/api/get/odashboard_key",
                json=api_data,
                headers={'Content-Type': 'application/json'},
            )
            result = response.json().get('result', {})
            if result.get('error'):
                # TODO : In the hook it seems impossible to raise an User error......
                error_msg = result.get('error')
                _logger.error(f"Error creating demo key: {error_msg}")
                # Store error for later display in UI
                env['ir.config_parameter'].sudo().set_param('odashboard.init_error', error_msg)
                raise UserError(_("Failed to create demo key: %s") % error_msg)

            if result.get('valid'):
                sub_plan = result.get('odash_sub_plan', 'freemium')
                demo_key = result.get('license_key', demo_key_uuid)
                token = result.get('token', False)
                _logger.info(f"Demo key successfully created and synchronized: {demo_key}")
                    
                # Store demo key information in system parameters
                env['ir.config_parameter'].sudo().set_param('odashboard.key', demo_key)
                env['ir.config_parameter'].sudo().set_param('odashboard.plan', sub_plan)
                env['ir.config_parameter'].sudo().set_param('odashboard.key_synchronized', True)
                env['ir.config_parameter'].sudo().set_param('odashboard.api.token', token)
            else:
                _logger.error(f"API call failed with status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"Network error while creating demo key: {str(e)}")
        except Exception as e:
            _logger.error(f"Unexpected error while creating demo key: {str(e)}")
            
    except Exception as e:
        _logger.error(f"Error in post_init_hook: {str(e)}")


def uninstall_hook(env):
    """Uninstall hook to clean up demo key data."""
    
    try:
        # Remove demo key parameters
        env['ir.config_parameter'].sudo().search([
            ('key', 'in', ['odashboard.key', 'odashboard.key_synchronized'])
        ]).unlink()
        
        _logger.info("Demo key parameters cleaned up during uninstall")
        
    except Exception as e:
        _logger.error(f"Error in uninstall_hook: {str(e)}")
