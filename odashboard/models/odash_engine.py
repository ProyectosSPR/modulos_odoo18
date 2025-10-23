from odoo import models, fields, api, _, tools
import logging
import requests
import ast
import hashlib

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DashboardEngine(models.Model):
    """
    This model manages the Odashboard visualization engine code and its updates.
    It can automatically check for updates on GitHub and apply them when available.
    Singleton pattern enforced via create() method override.
    """
    _name = 'odash.engine'
    _description = 'Dashboard Engine'
    _order = 'create_date desc'

    name = fields.Char(string='Name', default='Dashboard Engine', readonly=True)
    version = fields.Char(string='Version', default='1.0.0', readonly=True)
    code = fields.Text(string='Engine Code', readonly=True, 
                      help="Python code for the dashboard visualization engine")
    previous_code = fields.Text(string='Previous Engine Code', readonly=True,
                               help="Previous version of the engine code (for fallback)")
    update_log = fields.Text(string='Update Log', readonly=True,
                            help="Log of update attempts and results")

    @api.model
    def _get_github_base_url(self):
        """Get the base URL for GitHub repository."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odashboard.github_base_url', 
            'https://raw.githubusercontent.com/osolutionscompany/odashboard.engine/main/'
        )
    @api.model
    def _get_versions_url(self):
        """Get the URL for versions.json file."""
        base_url = self._get_github_base_url()
        return f"{base_url}versions.json"

    @api.model
    def _get_single_record(self):
        """Get or create the single engine record with proper locking.

        Handles race conditions using double-checked locking.
        Assumes PostgreSQL backend; falls back to simple creation if not.
        """
        # First, try a simple search (no lock needed for reads)
        engine = self.search([], limit=1)
        if engine:
            return engine

        # Generate a unique lock ID based on model name to avoid collisions
        lock_id = int(hashlib.sha256(self._name.encode()).hexdigest()[:10], 16)  # Truncate to fit int64

        # Only use locking when we need to create
        try:
            if self.env.cr.dbname.startswith('postgres'):  # Rough check for PostgreSQL
                # Acquire advisory lock
                self.env.cr.execute("SELECT pg_advisory_xact_lock(%s)", (lock_id,))

            # Double-check after acquiring lock (if applicable)
            engine = self.search([], limit=1)
            if engine:
                return engine

            # Safe to create now
            engine = self.create({
                'name': 'Dashboard Engine',
                'version': '0.0.0',
                'code': False,
                'previous_code': False,
            })
            engine.check_for_updates()
            return engine

        except Exception as e:
            _logger.error(f"Error in _get_single_record: {str(e)}", exc_info=True)
            # Fallback: one more search attempt
            engine = self.search([], limit=1)
            if engine:
                return engine
            raise ValueError("Failed to get or create engine record") from e  # Wrap with more context

    def _add_to_log(self, message):
        """Add a timestamped message to the update log."""
        timestamp = fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_log = self.update_log or ''
        self.update_log = f"{current_log}\n[{timestamp}] {message}" if current_log else f"[{timestamp}] {message}"

    def check_for_updates(self):
        """
        Check GitHub for engine updates.
        Returns True if an update is available and successfully applied.
        """
        self.ensure_one()
        engine = self
        
        try:
            # Fetch versions.json from GitHub
            versions_url = self._get_versions_url()
            _logger.info(f"Checking for updates at: {versions_url}")
            
            response = requests.get(versions_url, timeout=10)
            if response.status_code != 200:
                message = f"Failed to fetch versions.json: HTTP {response.status_code}"
                _logger.error(message)
                self._add_to_log(message)
                return False
            
            versions_data = response.json()
            latest_version = versions_data.get('latest')
            
            if not latest_version:
                message = "No 'latest' version found in versions.json"
                _logger.error(message)
                self._add_to_log(message)
                return False
            
            # Compare versions
            current_version = engine.version
            _logger.info(f"Current version: {current_version}, Latest version: {latest_version}")
            
            if current_version == latest_version and engine.code:
                message = f"Already at the latest version ({latest_version})"
                _logger.info(message)
                self._add_to_log(message)
                return False
            
            # Get version details
            version_info = versions_data.get('versions', {}).get(latest_version)
            if not version_info or not version_info.get('path'):
                message = f"No path information for version {latest_version}"
                _logger.error(message)
                self._add_to_log(message)
                return False
            
            # Download the update
            code_path = version_info.get('path')
            code_url = f"{self._get_github_base_url()}{code_path}"
            
            return self._download_update(code_url, latest_version, version_info)
            
        except Exception as e:
            message = f"Error checking for updates: {str(e)}"
            _logger.exception(message)
            self._add_to_log(message)
            return False

    def _download_update(self, code_url, new_version, version_info):
        """
        Download and apply an engine update.
        Returns True if successful, False otherwise.
        """
        self.ensure_one()
        engine = self
        
        try:
            _logger.info(f"Downloading update from: {code_url}")
            response = requests.get(code_url, timeout=15)
            
            if response.status_code != 200:
                message = f"Failed to download update: HTTP {response.status_code}"
                _logger.error(message)
                self._add_to_log(message)
                return False
            
            new_code = response.text
            
            # Validate Python syntax
            try:
                ast.parse(new_code)
            except SyntaxError as e:
                message = f"Invalid Python syntax in downloaded code: {str(e)}"
                _logger.error(message)
                self._add_to_log(message)
                return False
            
            # Save previous code for fallback
            current_code = engine.code
            
            # Update the engine
            engine.write({
                'previous_code': current_code,
                'code': new_code,
                'version': new_version,
            })
            
            message = f"Successfully updated to version {new_version}: {version_info.get('description', 'No description')}"
            _logger.info(message)
            self._add_to_log(message)
            return True
            
        except Exception as e:
            message = f"Error downloading update: {str(e)}"
            _logger.exception(message)
            self._add_to_log(message)
            return False

    def execute_engine_code(self, method_name, *args, **kwargs):
        """
        Execute a method from the engine code.
        If execution fails, fall back to the previous version.
        In development mode, it will try to load code from the local file system first.
        """
        self.ensure_one()
        engine = self

        code = engine.code
        if not code:
            _logger.error("No engine code available")
            return {'error': _('No engine code available')}
        
        # Try to execute the current code
        try:
            shared_namespace = {}
            
            # Execute the code in the shared namespace
            exec(code, shared_namespace, shared_namespace)
            # Check if the method exists in the namespace
            if method_name in shared_namespace:
                func = shared_namespace[method_name]
                result = func(*args, **kwargs)
                return result
            else:
                _logger.error(f"Method '{method_name}' not found in engine code")
                return {'error': f"Method '{method_name}' not found in engine code"}
                
        except Exception as e:
            _logger.exception(f"Error executing '{method_name}': {str(e)}")
            
            # Try with previous code as a fallback
            if engine.previous_code and engine.previous_code != code:
                try:
                    _logger.info(f"Attempting fallback execution of '{method_name}'")
                    
                    # Create a shared namespace for fallback
                    fallback_namespace = {}
                    
                    # Execute the previous code with shared namespace
                    exec(engine.previous_code, fallback_namespace, fallback_namespace)
                    
                    # Check if the method exists in the fallback namespace
                    if method_name in fallback_namespace:
                        func = fallback_namespace[method_name]
                        result = func(*args, **kwargs)
                    else:
                        return {'error': f"Method '{method_name}' not found in fallback code"}
                
                    # Log the fallback
                    self._add_to_log(f"Executed '{method_name}' using fallback code due to error: {str(e)}")
                    
                    return result
                    
                except Exception as fallback_error:
                    _logger.exception(f"Error executing fallback for '{method_name}': {str(fallback_error)}")
                    return {'error': f"Error in engine execution: {str(e)}. Fallback also failed: {str(fallback_error)}"}
            
            return {'error': f"Error in engine execution: {str(e)}"}

    def execute_unified_request(self, action, parameters, env, request=None):
        """
        Unified request dispatcher that routes requests to appropriate engine methods.
        
        This method dynamically dispatches requests to the engine without requiring
        hardcoded action mappings, making it fully extensible through engine updates.
        
        Args:
            action (str): The action to perform (method name in engine)
            parameters (dict): Action-specific parameters
            env: Odoo environment
            request: HTTP request object (optional, needed for some actions)
            
        Returns:
            dict: Standardized response with 'success', 'data', and 'error' keys
        """
        self.ensure_one()
        
        try:
            # First, try to get action configuration from the engine itself
            # This allows the engine to define its own action mappings
            engine_config = self.execute_engine_code('get_action_config', action)
            
            if engine_config and engine_config.get('success'):
                # Engine provides action configuration
                config = engine_config.get('data', {})
                method_name = config.get('method', action)
                
                # Build arguments based on engine configuration
                args = self._build_engine_args(config, parameters, env, request)
                
                # Validate parameters if engine specifies requirements
                validation_error = self._validate_engine_parameters(config, parameters)
                if validation_error:
                    return validation_error
                    
            else:
                # Fallback to legacy action mapping for backward compatibility
                legacy_config = self._get_legacy_action_config(action, parameters, env, request)
                if not legacy_config:
                    return {
                        'success': False,
                        'error': _("Unsupported action: %s") % action
                    }
                
                method_name = legacy_config['method']
                args = legacy_config['args']
                
                # Legacy parameter validation
                validation_error = self._validate_legacy_parameters(action, parameters)
                if validation_error:
                    return validation_error
            
            # Execute the engine method
            result = self.execute_engine_code(method_name, *args)
            
            # Standardize the response format
            return self._standardize_response(result)
                
        except Exception as e:
            _logger.exception("Error in execute_unified_request: %s", e)
            return {
                'success': False,
                'error': str(e)
            }

    def _build_engine_args(self, config, parameters, env, request):
        """Build arguments for engine method based on configuration."""
        args = []
        arg_specs = config.get('args', [])
        
        for arg_spec in arg_specs:
            if arg_spec == 'env':
                args.append(env)
            elif arg_spec == 'request':
                args.append(request)
            elif arg_spec == 'parameters':
                args.append(parameters)
            elif isinstance(arg_spec, dict):
                # Parameter mapping: {'param': 'model_name', 'default': None}
                param_name = arg_spec.get('param')
                default_value = arg_spec.get('default')
                args.append(parameters.get(param_name, default_value))
            else:
                # Direct parameter name
                args.append(parameters.get(arg_spec))
        
        return args

    def _validate_engine_parameters(self, config, parameters):
        """Validate parameters based on engine configuration."""
        required_params = config.get('required_params', [])
        
        for param in required_params:
            if not parameters.get(param):
                return {
                    'success': False,
                    'error': _("Missing required parameter: %s") % param
                }
        
        return None

    def _get_legacy_action_config(self, action, parameters, env, request):
        """Get legacy action configuration for backward compatibility."""
        legacy_map = {
            'get_models': {
                'method': 'get_models',
                'args': [env]
            },
            'get_model_fields': {
                'method': 'get_model_fields', 
                'args': [parameters.get('model_name'), env]
            },
            'get_model_records': {
                'method': 'get_model_records',
                'args': [parameters.get('model_name'), parameters, env]
            },
            'get_model_search': {
                'method': 'get_model_search',
                'args': [parameters.get('model_name'), parameters, request]
            },
            'process_dashboard_request': {
                'method': 'process_dashboard_request',
                'args': [parameters.get('request_data', parameters), env]
            }
        }
        
        return legacy_map.get(action)

    def _validate_legacy_parameters(self, action, parameters):
        """Validate parameters for legacy actions."""
        if action in ['get_model_fields', 'get_model_records', 'get_model_search'] and not parameters.get('model_name'):
            return {'success': False, 'error': _("Missing required parameter: model_name")}
        elif action == 'process_dashboard_request' and not parameters.get('request_data'):
            return {'success': False, 'error': _("Missing required parameter: request_data")}
        
        return None

    def _standardize_response(self, result):
        """Standardize engine response format."""
        if isinstance(result, dict):
            if 'success' in result:
                # Already in standardized format
                return result
            elif 'error' in result:
                # Error format from engine
                return {
                    'success': False,
                    'error': result['error']
                }
            elif 'data' in result:
                # Data format from engine
                return {
                    'success': True,
                    'data': result['data']
                }
            else:
                # Raw data format
                return {
                    'success': True,
                    'data': result
                }
        else:
            # Raw result
            return {
                'success': True,
                'data': result
            }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to enforce singleton pattern."""
        existing = self.search([], limit=1)
        if existing:
            raise ValidationError(_(
                'Cannot create Dashboard Engine record. '
                'Only one engine record is allowed and one already exists (ID: %s). '
                'Use _get_single_record() method instead.'
            ) % existing.id)
        if len(vals_list) > 1:
            raise ValidationError(_("Only one Dashboard Engine record can be created at a time"))
        return super(DashboardEngine, self).create(vals_list)
