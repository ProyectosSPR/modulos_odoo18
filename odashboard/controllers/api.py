import json
import logging
import hmac
import hashlib
import time
from datetime import datetime, date

from odoo import http, _
from odoo.http import request, Response

from .api_helper import ApiHelper

_logger = logging.getLogger(__name__)


class OdashboardJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(OdashboardJSONEncoder, self).default(obj)


class OdashboardAPI(http.Controller):

    @http.route(['/api/osolutions/subscription-update'], type='http', auth='none', csrf=False, methods=['POST'], cors="*")
    def subscription_update_webhook(self):
        """
        Secure webhook endpoint for O'Solutions to push subscription updates to Odashboard.
        Uses HMAC signature validation to prevent unauthorized access.
        
        Expected payload:
        {
            "uuid": "license-uuid",
            "key": "license-key", 
            "plan": "pro|freemium|partner",
            "timestamp": 1234567890
            "token" : JWT Token
        }
        
        Expected headers:
        {
            "X-OSolutions-Signature": "sha256=<hmac_signature>"
        }
        """
        try:
            # Get raw payload for signature verification
            raw_payload = request.httprequest.data
            data = json.loads(raw_payload.decode('utf-8'))
            
            # Validate HMAC signature first (security check)
            if not self._validate_webhook_signature(raw_payload):
                _logger.warning(f"Invalid webhook signature from IP: {request.httprequest.environ.get('REMOTE_ADDR')}")
                return ApiHelper.json_error_response("Unauthorized", 401)
            
            # Validate required fields
            required_fields = ['uuid', 'key', 'plan', 'timestamp']
            for field in required_fields:
                if field not in data:
                    return ApiHelper.json_error_response(f"Missing required field: {field}", 400)
            
            uuid = data['uuid']
            key = data['key']
            plan = data['plan']
            timestamp = data['timestamp']
            token = data['token']
            
            # Validate timestamp (prevent replay attacks)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:  # 5 minutes tolerance
                return ApiHelper.json_error_response("Request timestamp too old or invalid", 400)

            # Validate that the UUID and key match our configuration
            stored_uuid = request.env['ir.config_parameter'].sudo().get_param('odashboard.uuid')
            stored_key = request.env['ir.config_parameter'].sudo().get_param('odashboard.key')
            
            if uuid != stored_uuid or key != stored_key:
                _logger.warning(f"Invalid UUID/key in webhook request: UUID={uuid}")
                return ApiHelper.json_error_response(_("Invalid credentials"), 401)
            
            # Update system parameters with new plan
            request.env['ir.config_parameter'].sudo().set_param('odashboard.plan', plan)
            request.env['ir.config_parameter'].sudo().set_param('odashboard.api.token', token)

            return ApiHelper.json_valid_response({
                'message': _('Subscription plan updated successfully'),
                'uuid': uuid,
                'plan': plan
            }, 200)
            
        except json.JSONDecodeError:
            return ApiHelper.json_error_response("Invalid JSON payload", 400)
        except Exception as e:
            _logger.error(f"Error in subscription update webhook: {str(e)}")
            return ApiHelper.json_error_response("Internal server error", 500)

    def _validate_webhook_signature(self, payload):
        """
        Validate HMAC signature using license key as secret.
        This eliminates the need for manual webhook secret configuration.
        """
        try:
            # Get signature from headers
            signature_header = request.httprequest.headers.get('X-OSolutions-Signature')
            if not signature_header:
                return False
            
            # Extract signature (format: "sha256=<signature>")
            if not signature_header.startswith('sha256='):
                return False
            
            received_signature = signature_header[7:]  # Remove "sha256=" prefix
            
            # Use license key as webhook secret (already available in system parameters)
            webhook_secret = request.env['ir.config_parameter'].sudo().get_param('odashboard.key')
            if not webhook_secret:
                _logger.error("License key not found in system parameters")
                return False
            
            # Calculate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (use hmac.compare_digest to prevent timing attacks)
            return hmac.compare_digest(received_signature, expected_signature)
            
        except Exception as e:
            _logger.error(f"Error validating webhook signature: {str(e)}")
            return False

    @http.route(['/api/odash/execute'], type='http', auth='api_key_dashboard', csrf=False, methods=['POST'], cors="*")
    def unified_execute(self):
        """
        Unified entry point for all odashboard requests.
        
        Expected payload format:
        {
            "action": "get_models|get_model_fields|get_model_records|get_model_search|process_dashboard_request",
            "parameters": {
                // Action-specific parameters
            }
        }
        
        Returns:
        {
            "success": true/false,
            "data": {...},
            "error": "error message if any"
        }
        """
        try:
            # Parse request data
            request_data = json.loads(request.httprequest.data.decode('utf-8'))
            
            # Validate required fields
            action = request_data.get('action')
            parameters = request_data.get('parameters', {})
            
            if not action:
                return ApiHelper.json_error_response(_("Missing 'action' parameter"), 400)
            
            # Get engine instance
            engine = request.env['odash.engine'].sudo()._get_single_record()
            
            # Dispatch to engine with unified interface
            result = engine.execute_unified_request(action, parameters, request.env, request)
            
            if result.get('success'):
                return ApiHelper.json_valid_response(result.get('data'), 200)
            else:
                return ApiHelper.json_error_response(result.get('error', _('Unknown error')), 500)
                
        except json.JSONDecodeError:
            return ApiHelper.json_error_response(_("Invalid JSON payload"), 400)
        except Exception as e:
            _logger.exception("Error in unified_execute: %s", e)
            return ApiHelper.json_error_response(str(e), 500)

    @http.route(['/api/odash/access'], type='http', auth='api_key_dashboard', csrf=False, methods=['GET'], cors="*")
    def get_access(self):
        token = request.env['ir.config_parameter'].sudo().get_param('odashboard.api.token')
        return ApiHelper.json_valid_response(token, 200)

    @http.route(['/api/osolution/refresh-token/<string:uuid>/<string:key>'], type='http', auth='none', csrf=False,
                methods=['GET'], cors="*")
    def refresh_token(self, uuid, key):
        ConfigParameter = request.env['ir.config_parameter'].sudo()

        uuid_param = ConfigParameter.get_param('odashboard.uuid')
        key_param = ConfigParameter.get_param('odashboard.key')

        if uuid_param == uuid and key_param == key:
            request.env["odash.dashboard"].sudo().update_auth_token()
        return ApiHelper.json_valid_response("ok", 200)

    @http.route(['/api/get/models'], type='http', auth='api_key_dashboard', csrf=False, methods=['GET'], cors="*")
    def get_models(self):
        """
        Return a list of models relevant for analytics, automatically filtering out technical models
        
        DEPRECATED: Use /api/odash/execute with action='get_models' instead.
        This route is maintained for backward compatibility.

        :return: JSON response with list of analytically relevant models
        """
        # Delegate to unified entry point
        engine = request.env['odash.engine'].sudo()._get_single_record()
        result = engine.execute_unified_request('get_models', {}, request.env)

        if result.get('success'):
            return ApiHelper.json_valid_response(result.get('data', []), 200)
        else:
            return ApiHelper.json_error_response(result.get('error', _('Unknown error')), 500)

    @http.route(['/api/get/model_fields/<string:model_name>'], type='http', auth='api_key_dashboard', csrf=False,
                methods=['GET'], cors="*")
    def get_model_fields(self, model_name, **kw):
        """
        Retrieve information about the fields of a specific Odoo model.
        
        DEPRECATED: Use /api/odash/execute with action='get_model_fields' instead.
        This route is maintained for backward compatibility.

        :param model_name: Name of the Odoo model (example: 'sale.order')
        :return: JSON with information about the model's fields
        """
        # Delegate to unified entry point
        engine = request.env['odash.engine'].sudo()._get_single_record()
        result = engine.execute_unified_request('get_model_fields', {'model_name': model_name}, request.env)

        if result.get('success'):
            return self._build_response(result.get('data', {}), 200)
        else:
            return ApiHelper.json_error_response(result.get('error', _('Unknown error')), 500)

    @http.route(['/api/get/model_records/<string:model_name>'], type='http', auth='none', csrf=False,
                methods=['GET'], cors="*")
    def get_model_records(self, model_name, **kw):
        """
        Retrieve records of a specific Odoo model with pagination and search functionality.
        
        DEPRECATED: Use /api/odash/execute with action='get_model_records' instead.
        This route is maintained for backward compatibility.

        :param model_name: Name of the Odoo model (example: 'sale.order')
        :return: JSON with model records
        """
        # Delegate to unified entry point
        engine = request.env['odash.engine'].sudo()._get_single_record()
        parameters = dict(kw)
        parameters['model_name'] = model_name
        result = engine.execute_unified_request('get_model_records', parameters, request.env)

        if result.get('success'):
            return self._build_response(result.get('data', {}), 200)
        else:
            return ApiHelper.json_error_response(result.get('error', _('Unknown error')), 500)

    @http.route(['/api/get/model_search/<string:model_name>'], type='http', auth='api_key_dashboard', csrf=False,
                methods=['GET'], cors="*")
    def get_model_search(self, model_name, **kw):
        """
        Search records of a specific Odoo model.
        
        DEPRECATED: Use /api/odash/execute with action='get_model_search' instead.
        This route is maintained for backward compatibility.
        """
        # Delegate to unified entry point
        engine = request.env['odash.engine'].sudo()._get_single_record()
        parameters = dict(kw)
        parameters['model_name'] = model_name
        result = engine.execute_unified_request('get_model_search', parameters, request.env, request)

        if result.get('success'):
            return self._build_response({'results': result.get('data', {})}, 200)
        else:
            return ApiHelper.json_error_response(result.get('error', _('Unknown error')), 500)

    @http.route('/api/get/dashboard', type='http', auth='api_key_dashboard', csrf=False, methods=['POST'], cors='*')
    def get_dashboard_data(self):
        """
        Main endpoint to get dashboard visualization data.
        Accepts JSON configurations for blocks, graphs, and tables.
        
        DEPRECATED: Use /api/odash/execute with action='process_dashboard_request' instead.
        This route is maintained for backward compatibility.
        """
        try:
            with request.env.cr.savepoint():
                engine = request.env['odash.engine'].sudo()._get_single_record()

                # Check update if there is no code
                if not engine.code:
                    engine.check_for_updates()

                request_data = json.loads(request.httprequest.data.decode('utf-8'))

                # Delegate to unified entry point
                result = engine.execute_unified_request('process_dashboard_request', 
                                                      {'request_data': request_data}, 
                                                      request.env)

                if result.get('success'):
                    return self._build_response([result.get('data')], 200)
                else:
                    return ApiHelper.json_error_response(result.get('error', _('Unknown error')), 500)
                    
        except json.JSONDecodeError:
            return ApiHelper.json_error_response(_("Invalid JSON payload"), 400)
        except Exception as e:
            _logger.exception("Error in get_dashboard_data: %s", e)
            return ApiHelper.json_error_response(str(e), 500)

    def _build_response(self, data, status=200):
        """Build a consistent JSON response with the given data and status."""
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(data, cls=OdashboardJSONEncoder),
                        status=status,
                        headers=headers)
