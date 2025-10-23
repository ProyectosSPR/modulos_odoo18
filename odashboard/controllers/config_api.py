import uuid
import logging
from odoo import http, _
from odoo.http import request

from .api_helper import ApiHelper

_logger = logging.getLogger(__name__)

def check_access(config, user):

    if user.has_group('odashboard.group_odashboard_editor'):
        return True
    
    can_access = False

    if not config.is_page_config:
        return True
    
    if not config.security_group_ids and not config.user_ids:
        can_access = True
    else:
        if user in config.user_ids:
            can_access = True

        if not can_access:
            for group in config.security_group_ids:
                if user in group.user_ids:
                    can_access = True
                    break
    return can_access


def check_category_access(category, user):
    """
    Check if a user has access to a category based on security groups.
    Editors have access to all categories.
    """
    if user.has_group('odashboard.group_odashboard_editor'):
        return True
    
    # If no security groups defined, everyone can access
    if not category.security_group_ids and not category.user_ids:
        return True

    if user in category.user_ids:
        return True
    
    # Check if user is in any of the category's security groups
    for group in category.security_group_ids:
        if user in group.user_ids:
            return True
    
    return False


class OdashConfigAPI(http.Controller):
    """
    Controller for CRUD operations on Odash Configuration.
    Provides two sets of endpoints:
    - /api/odash/pages/* for page configurations
    - /api/odash/data/* for data configurations
    - /api/odash/categories for page categories
    """

    # ---- Categories ----
    
    @http.route('/api/odash/categories', type='http', auth='api_key_dashboard', methods=['GET'], csrf=False, cors="*")
    def categories_collection(self, **kw):
        """
        Get all page categories (filtered by user access)
        """
        try:
            categories = request.env['odash.category'].sudo().search([('active', '=', True)], order='sequence asc')
            result = []
            
            for category in categories:
                # Check if user has access to this category
                if check_category_access(category, request.env.user):
                    result.append({
                        'id': category.id,
                        'name': category.name,
                        'description': category.description or '',
                        'icon': category.icon or '',
                        'sequence': category.sequence,
                        'page_count': category.page_count,
                    })
                
            return ApiHelper.json_valid_response(result, 200)
            
        except Exception as e:
            _logger.error(f"Error getting categories: {e}")
            return ApiHelper.json_error_response(e, 500)
    
    @http.route('/api/odash/categories/create', type='http', auth='api_key_dashboard', methods=['POST'], csrf=False, cors="*")
    def categories_create(self, **kw):
        """
        Create a new page category
        """
        try:
            data = ApiHelper.load_json_data(request)
            
            if not data.get('name'):
                return ApiHelper.json_error_response(_("Category name is required"), 400)
            
            # Get the highest sequence number and add 10
            last_category = request.env['odash.category'].sudo().search([], order='sequence desc', limit=1)
            next_sequence = (last_category.sequence + 10) if last_category else 10
            
            # Create the category
            category = request.env['odash.category'].sudo().create({
                'name': data.get('name'),
                'description': data.get('description', ''),
                'icon': data.get('icon', ''),
                'sequence': next_sequence,
                'active': True,
            })
            
            result = {
                'id': category.id,
                'name': category.name,
                'description': category.description or '',
                'icon': category.icon or '',
                'sequence': category.sequence,
                'page_count': 0,
            }
            
            return ApiHelper.json_valid_response(result, 201)
            
        except Exception as e:
            _logger.error(f"Error creating category: {e}")
            return ApiHelper.json_error_response(str(e), 500)

    # ---- Page Configurations ----

    @http.route('/api/odash/pages', type='http', auth='api_key_dashboard', methods=['GET', 'POST'], csrf=False, cors="*")
    def pages_collection(self, **kw):
        """
        Handle page configurations collection
        GET: Get all page configurations
        POST: Create a new page configuration
        """

        method = request.httprequest.method
        odash_config = request.env['odash.config'].sudo()
        page_id = request.env.context.get('page_id')

        try:
            if method == 'GET':
                # Get all page configurations
                if page_id:
                    return ApiHelper.json_valid_response([page_id.config], 200)

                configs = odash_config.sudo().search([('is_page_config', '=', True)], order='sequence asc')
                result = []
                
                for config in configs:
                    if config.config and check_access(config, request.env.user):
                        # Also check category access if page has a category
                        if config.category_id and not check_category_access(config.category_id, request.env.user):
                            continue
                        
                        page_data = config.config.copy() if isinstance(config.config, dict) else config.config

                        page_data['category_id'] = config.category_id.id or None
                        page_data['category_name'] = config.category_id.name or None
                        
                        # Also add category_id to root.props for Puck editor
                        if 'root' in page_data and isinstance(page_data['root'], dict):
                            if 'props' not in page_data['root']:
                                page_data['root']['props'] = {}
                            page_data['root']['props']['category_id'] = page_data['category_id']
                        
                        result.append(page_data)
                        
                return ApiHelper.json_valid_response(result, 200)
            
            elif method == 'POST':
                # Create a new page configuration
                data = ApiHelper.load_json_data(request)
                
                # Generate UUID if id not provided
                if not data.get('id'):
                    data['id'] = str(uuid.uuid4())
                
                # Extract category_id from data
                category_id = data.pop('category_id', None)
                    
                # Create new config record
                config_vals = {
                    'is_page_config': True,
                    'config_id': data.get('id'),
                    'config': data
                }
                
                # Add category if provided
                if category_id:
                    config_vals['category_id'] = category_id
                
                config = odash_config.sudo().create(config_vals)

                odash_config.clean_unused_config()
                
                # Return config with category info
                result = config.config.copy() if isinstance(config.config, dict) else config.config
                if config.category_id:
                    result['category_id'] = config.category_id.id
                    result['category_name'] = config.category_id.name
                else:
                    result['category_id'] = None
                    result['category_name'] = None
                
                return ApiHelper.json_valid_response(result, 201)
                
        except Exception as e:
            operation = "getting" if method == 'GET' else "creating"
            _logger.error(f"Error {operation} page configs: {e}")
            return ApiHelper.json_error_response(e, 500)

    @http.route('/api/odash/pages/<string:config_id>', type='http', auth='api_key_dashboard', methods=['GET', 'PUT', 'DELETE'], csrf=False, cors="*")
    def page_resource(self, config_id, **kw):
        """
        Handle individual page configuration
        GET: Get a specific page configuration by ID
        PUT: Update an existing page configuration
        DELETE: Delete a page configuration
        """

        method = request.httprequest.method
        
        try:
            # Get the configuration record first (common for all methods)
            config = request.env['odash.config'].sudo().search([
                ('is_page_config', '=', True),
                ('config_id', '=', config_id)
            ], limit=1)
            
            if not config or not check_access(config, request.env.user):
                return ApiHelper.json_error_response("Page configuration not found", 404)
            
            if method == 'GET':
                # Return the configuration with category info
                result = config.config.copy() if isinstance(config.config, dict) else config.config
                
                # Add category info at top level
                if config.category_id:
                    result['category_id'] = config.category_id.id
                    result['category_name'] = config.category_id.name
                else:
                    result['category_id'] = None
                    result['category_name'] = None
                
                # Also add category_id to root.props for Puck editor
                if 'root' in result and isinstance(result['root'], dict):
                    if 'props' not in result['root']:
                        result['root']['props'] = {}
                    result['root']['props']['category_id'] = result['category_id']
                
                return ApiHelper.json_valid_response(result, 200)
                
            elif method == 'PUT':
                # Update the configuration
                data = ApiHelper.load_json_data(request)
                
                # Check if category_id is in the data before we modify it
                has_category_id = 'category_id' in data
                category_id = data.get('category_id')
                
                # Ensure ID remains the same
                updated_data = data.copy()
                updated_data['id'] = config_id
                
                # Remove category_id from config data (it's stored separately)
                updated_data.pop('category_id', None)
                
                # Prepare update values
                update_vals = {'config': updated_data}
                
                # Update category if provided (including None to remove category)
                if has_category_id:
                    update_vals['category_id'] = category_id
                
                # Update the configuration
                config.sudo().write(update_vals)
                
                # Return config with category info
                result = config.config.copy() if isinstance(config.config, dict) else config.config
                if config.category_id:
                    result['category_id'] = config.category_id.id
                    result['category_name'] = config.category_id.name
                else:
                    result['category_id'] = None
                    result['category_name'] = None
                
                return ApiHelper.json_valid_response(result, 200)
                
            elif method == 'DELETE':
                # Delete the configuration
                config.sudo().unlink()
                request.env['odash.config'].clean_unused_config()
                
                return ApiHelper.json_valid_response({"success": True}, 200)
                
        except Exception as e:
            operation = "getting" if method == 'GET' else ("updating" if method == 'PUT' else "deleting")
            _logger.error(f"Error {operation} page config: {e}")
            return ApiHelper.json_error_response(e, 500)

    @http.route('/api/odash/pages/<string:config_id>/pdf', type='http', auth='api_key_dashboard',
                methods=['GET'], csrf=False, cors="*")
    def page_pdf(self, config_id, **kw):
        method = request.httprequest.method

        try:
            # Get the configuration record first (common for all methods)
            config = request.env['odash.config'].sudo().search([
                ('is_page_config', '=', True),
                ('config_id', '=', config_id)
            ], limit=1)

            if not config or not check_access(config, request.env.user):
                return ApiHelper.json_error_response("Page configuration not found", 404)

            if method == 'GET':
                # Return the configuration
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                return ApiHelper.json_valid_response({
                    "url": f"{base_url}/dashboard/public/{config.id}/{config.secret_access_token}/pdf"
                }, 200)

        except Exception as e:
            operation = "getting" if method == 'GET' else ("updating" if method == 'PUT' else "deleting")
            _logger.error(f"Error {operation} page config: {e}")
            return ApiHelper.json_error_response(e, 500)

    @http.route('/api/odash/pages/<string:config_id>/configure', type='http', auth='api_key_dashboard',
                methods=['POST'], csrf=False, cors="*")
    def page_configuration(self, config_id, **kw):
        method = request.httprequest.method

        try:
            # Get the configuration record first (common for all methods)
            config = request.env['odash.config'].sudo().search([
                ('is_page_config', '=', True),
                ('config_id', '=', config_id)
            ], limit=1)
            data = ApiHelper.load_json_data(request)
            new_config = data.get('config', {}).get('config', {})
            new_config["root"]["props"]["title"] = data.get("name")
            new_config["title"] = data.get("name")
            new_config["id"] = str(config.config["id"])

            config.write({
                'name': data.get("name"),
                'config': new_config
            })

            configs = data.get('configs', [])
            configs_to_create = []

            for config in configs:
                configs_to_create.append({
                    'is_page_config': False,
                    'config': config.get("config", {}),
                    'config_id': config.get("config_id"),
                    'name': config.get("name"),
                })

            request.env['odash.config'].sudo().create(configs_to_create)

            return ApiHelper.json_valid_response("ok", 200)



        except Exception as e:
            operation = "getting" if method == 'GET' else ("updating" if method == 'PUT' else "deleting")
            _logger.error(f"Error {operation} page config: {e}")
            return ApiHelper.json_error_response(e, 500)

    # ---- Data Configurations ----

    @http.route('/api/odash/data', type='http', auth='api_key_dashboard', methods=['GET', 'POST'], csrf=False, cors="*")
    def data_collection(self, **kw):
        """
        Handle data configurations collection
        GET: Get all data configurations
        POST: Create a new data configuration
        """
        method = request.httprequest.method

        try:
            if method == 'GET':
                # Get all data configurations
                configs = request.env['odash.config'].sudo().search([('is_page_config', '=', False)])
                result = []
                
                for config in configs:
                    if config.config:
                        result.append(config.config)
                        
                return ApiHelper.json_valid_response(result, 200)
            
            elif method == 'POST':
                # Create a new data configuration
                data = ApiHelper.load_json_data(request)
                
                # Generate UUID if id not provided
                if not data.get('id'):
                    data['id'] = str(uuid.uuid4())
                    
                # Create new config record
                config = request.env['odash.config'].sudo().create({
                    'is_page_config': False,
                    'config_id': data.get('id'),
                    'config': data
                })
                
                return ApiHelper.json_valid_response(config.config, 201)
                
        except Exception as e:
            operation = "getting" if method == 'GET' else "creating"
            _logger.error(f"Error {operation} data configs: {e}")
            return ApiHelper.json_error_response(e, 500)

    @http.route('/api/odash/data/<string:config_id>', type='http', auth='api_key_dashboard', methods=['GET', 'PUT', 'DELETE'], csrf=False, cors="*")
    def data_resource(self, config_id, **kw):
        """
        Handle individual data configuration
        GET: Get a specific data configuration by ID
        PUT: Update an existing data configuration
        DELETE: Delete a data configuration
        """
        method = request.httprequest.method

        try:
            # Get the configuration record first (common for all methods)
            config = request.env['odash.config'].sudo().search([
                ('is_page_config', '=', False),
                ('config_id', '=', config_id)
            ], limit=1)
            
            if not config:
                return ApiHelper.json_error_response("Data configuration not found", 404)
            
            if method == 'GET':
                # Return the configuration
                return ApiHelper.json_valid_response(config.config, 200)
                
            elif method == 'PUT':
                # Update the configuration
                data = ApiHelper.load_json_data(request)
                
                # Ensure ID remains the same
                updated_data = data.copy()
                updated_data['id'] = config_id
                
                # Update the configuration
                config.sudo().write({
                    'config': updated_data
                })
                
                return ApiHelper.json_valid_response(config.config, 200)
                
            elif method == 'DELETE':
                # Delete the configuration
                config.sudo().unlink()
                
                return ApiHelper.json_valid_response({"success": True}, 200)
                
        except Exception as e:
            operation = "getting" if method == 'GET' else ("updating" if method == 'PUT' else "deleting")
            _logger.error(f"Error {operation} data config: {e}")
            return ApiHelper.json_error_response(e, 500)
