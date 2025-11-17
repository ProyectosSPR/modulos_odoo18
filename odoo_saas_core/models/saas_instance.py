# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class SaasInstance(models.Model):
    _name = 'saas.instance'
    _description = 'SaaS Odoo Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'

    # Basic Information
    name = fields.Char(string='Instance Name', required=True, tracking=True)
    subdomain = fields.Char(string='Subdomain', required=True, tracking=True)
    full_url = fields.Char(string='Full URL', compute='_compute_full_url', store=True)
    database_id = fields.Char(string='Database ID', readonly=True, copy=False)

    # Technical Details
    odoo_version = fields.Selection([
        ('16.0', 'Odoo 16.0'),
        ('17.0', 'Odoo 17.0'),
        ('18.0', 'Odoo 18.0'),
    ], string='Odoo Version', required=True, default='18.0', tracking=True)

    server_location = fields.Selection([
        ('us_east', 'US East'),
        ('eu_west', 'EU West'),
        ('asia_pacific', 'Asia Pacific'),
    ], string='Server Location', default='us_east')

    # Customer & Package
    customer_id = fields.Many2one(
        'saas.customer',
        string='Customer',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_partner_id',
        string='Partner',
        store=True,
        readonly=True
    )
    service_package_id = fields.Many2one(
        'saas.service.package',
        string='Service Package',
        required=True,
        tracking=True,
        index=True
    )

    # Status Management
    status = fields.Selection([
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='trial', required=True, tracking=True)

    # Dates
    date_created = fields.Datetime(
        string='Created On',
        default=fields.Datetime.now,
        readonly=True
    )
    date_activated = fields.Datetime(string='Activated On', readonly=True)
    trial_end_date = fields.Datetime(
        string='Trial End Date',
        compute='_compute_trial_end_date',
        store=True
    )
    subscription_end_date = fields.Date(string='Subscription End Date', tracking=True)

    # Billing
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string='Billing Cycle', default='monthly', tracking=True)

    # Resource Usage
    current_users = fields.Integer(string='Current Users', default=1)
    max_users = fields.Integer(
        string='Max Users',
        related='service_package_id.max_users',
        store=True,
        readonly=True
    )
    storage_used_gb = fields.Float(string='Storage Used (GB)', default=0.0)
    max_storage_gb = fields.Float(
        string='Max Storage (GB)',
        related='service_package_id.storage_gb',
        store=True,
        readonly=True
    )

    # Computed Fields
    days_until_expiry = fields.Integer(
        string='Days Until Expiry',
        compute='_compute_days_until_expiry'
    )
    storage_percentage = fields.Float(
        string='Storage Usage %',
        compute='_compute_storage_percentage'
    )
    users_percentage = fields.Float(
        string='Users Usage %',
        compute='_compute_users_percentage'
    )

    # Provisioning Status
    is_provisioned = fields.Boolean(
        string='Access Provisioned',
        default=False,
        readonly=True,
        copy=False,
        help='Indicates if user access has been provisioned for this instance'
    )
    provisioned_company_id = fields.Many2one(
        'res.company',
        string='Provisioned Company',
        readonly=True,
        help='Company created for this SaaS instance'
    )

    # Subscription Link
    subscription_id = fields.Many2one(
        'subscription.package',
        string='Subscription',
        readonly=True
    )

    # ============================================================================
    # KUBERNETES INTEGRATION
    # ============================================================================

    # Cluster Configuration
    k8s_cluster_id = fields.Many2one(
        'saas.k8s.cluster',
        string='Kubernetes Cluster',
        tracking=True,
        help='Kubernetes cluster where this instance is/will be deployed'
    )

    k8s_template_id = fields.Many2one(
        'saas.k8s.deployment.template',
        string='Deployment Template',
        domain="[('cluster_id', '=', k8s_cluster_id)]",
        tracking=True,
        help='Kubernetes deployment template to use for this instance'
    )

    # Deployment Details
    k8s_namespace = fields.Char(
        string='K8s Namespace',
        help='Kubernetes namespace for this instance'
    )

    k8s_deployment_name = fields.Char(
        string='Deployment Name',
        help='Kubernetes Deployment resource name'
    )

    k8s_service_name = fields.Char(
        string='Service Name',
        help='Kubernetes Service resource name'
    )

    k8s_ingress_name = fields.Char(
        string='Ingress Name',
        help='Kubernetes Ingress resource name'
    )

    k8s_pvc_name = fields.Char(
        string='PVC Name',
        help='PersistentVolumeClaim name for filestore'
    )

    # Deployment Status
    k8s_deployed = fields.Boolean(
        string='Deployed to K8s',
        default=False,
        readonly=True,
        help='Indicates if this instance has been deployed to Kubernetes'
    )

    k8s_deployment_date = fields.Datetime(
        string='K8s Deployment Date',
        readonly=True,
        help='When the instance was deployed to Kubernetes'
    )

    k8s_pod_status = fields.Selection([
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('unknown', 'Unknown'),
    ], string='Pod Status', readonly=True, help='Status of Kubernetes pods')

    k8s_pod_count = fields.Integer(
        string='Running Pods',
        readonly=True,
        help='Number of running pods for this instance'
    )

    # Database Configuration (K8s)
    k8s_db_host = fields.Char(
        string='Database Host',
        help='PostgreSQL host (within K8s cluster or external)'
    )

    k8s_db_port = fields.Integer(
        string='Database Port',
        default=5432,
        help='PostgreSQL port'
    )

    k8s_db_name = fields.Char(
        string='Database Name',
        help='PostgreSQL database name'
    )

    k8s_db_user = fields.Char(
        string='Database User',
        help='PostgreSQL username'
    )

    k8s_db_password = fields.Char(
        string='Database Password',
        groups='base.group_system',
        help='PostgreSQL password (stored in Kubernetes Secret)'
    )

    # Manifest Storage
    k8s_manifests = fields.Text(
        string='Generated Manifests',
        readonly=True,
        help='Last generated Kubernetes YAML manifests for this instance'
    )

    # Health & Monitoring
    k8s_last_health_check = fields.Datetime(
        string='Last K8s Health Check',
        readonly=True
    )

    k8s_health_message = fields.Text(
        string='K8s Health Message',
        readonly=True
    )

    # Other
    company_id = fields.Many2one(
        'res.company',
        string='Odoo Company',
        default=lambda self: self.env.company
    )
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('subdomain_unique', 'UNIQUE(subdomain)', 'Subdomain must be unique!'),
        ('database_id_unique', 'UNIQUE(database_id)', 'Database ID must be unique!'),
    ]

    @api.depends('subdomain')
    def _compute_full_url(self):
        base_domain = self.env['ir.config_parameter'].sudo().get_param(
            'saas.base_domain', 'odoo.cloud'
        )
        for record in self:
            if record.subdomain:
                record.full_url = f"https://{record.subdomain}.{base_domain}"
            else:
                record.full_url = False

    @api.depends('customer_id', 'customer_id.partner_id')
    def _compute_partner_id(self):
        """Compute partner_id from customer_id"""
        for record in self:
            record.partner_id = record.customer_id.partner_id if record.customer_id else False

    @api.depends('date_created')
    def _compute_trial_end_date(self):
        for record in self:
            if record.date_created:
                record.trial_end_date = record.date_created + timedelta(days=7)
            else:
                record.trial_end_date = False

    @api.depends('subscription_end_date')
    def _compute_days_until_expiry(self):
        today = fields.Date.today()
        for record in self:
            if record.subscription_end_date:
                delta = record.subscription_end_date - today
                record.days_until_expiry = delta.days
            else:
                record.days_until_expiry = 0

    @api.depends('storage_used_gb', 'max_storage_gb')
    def _compute_storage_percentage(self):
        for record in self:
            if record.max_storage_gb > 0:
                record.storage_percentage = (record.storage_used_gb / record.max_storage_gb) * 100
            else:
                record.storage_percentage = 0.0

    @api.depends('current_users', 'max_users')
    def _compute_users_percentage(self):
        for record in self:
            if record.max_users > 0:
                record.users_percentage = (record.current_users / record.max_users) * 100
            else:
                record.users_percentage = 0.0

    @api.constrains('current_users', 'max_users')
    def _check_users_limit(self):
        for record in self:
            if record.current_users > record.max_users:
                raise ValidationError(
                    _('Current users (%s) cannot exceed max users (%s)') %
                    (record.current_users, record.max_users)
                )

    @api.constrains('storage_used_gb', 'max_storage_gb')
    def _check_storage_limit(self):
        for record in self:
            if record.storage_used_gb > record.max_storage_gb:
                raise ValidationError(
                    _('Storage used (%.2f GB) cannot exceed max storage (%.2f GB)') %
                    (record.storage_used_gb, record.max_storage_gb)
                )

    def action_activate(self):
        """Activate instance from trial"""
        for record in self:
            record.write({
                'status': 'active',
                'date_activated': fields.Datetime.now()
            })
            record.message_post(body=_('Instance activated successfully'))

    def action_suspend(self):
        """Suspend instance"""
        for record in self:
            record.status = 'suspended'
            record.message_post(body=_('Instance suspended'))

    def action_terminate(self):
        """Terminate instance"""
        for record in self:
            record.write({
                'status': 'terminated',
                'is_provisioned': False
            })
            record.message_post(body=_('Instance terminated'))

    def action_extend_trial(self):
        """Extend trial by 7 days"""
        for record in self:
            if record.status == 'trial' and record.trial_end_date:
                new_end_date = record.trial_end_date + timedelta(days=7)
                record.trial_end_date = new_end_date
                record.message_post(
                    body=_('Trial period extended to %s') % new_end_date.strftime('%Y-%m-%d')
                )

    def action_provision_access(self):
        """Manually trigger provisioning (normally done by automation)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Provision Access'),
            'res_model': 'saas.provision.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_instance_id': self.id},
        }

    @api.model
    def _cron_check_trial_expiry(self):
        """Cron job to check trial expiry"""
        today = fields.Datetime.now()
        trial_instances = self.search([
            ('status', '=', 'trial'),
            ('trial_end_date', '<=', today)
        ])
        for instance in trial_instances:
            instance.write({'status': 'expired'})
            instance.message_post(body=_('Trial period expired'))

    @api.model
    def _cron_check_subscription_expiry(self):
        """Cron job to check subscription expiry"""
        today = fields.Date.today()
        active_instances = self.search([
            ('status', '=', 'active'),
            ('subscription_end_date', '<=', today)
        ])
        for instance in active_instances:
            instance.write({'status': 'expired'})
            instance.message_post(body=_('Subscription expired'))

    # ============================================================================
    # KUBERNETES ACTIONS (Placeholder - Implement logic in phase 2)
    # ============================================================================

    def action_deploy_to_k8s(self):
        """Deploy this instance to Kubernetes"""
        self.ensure_one()

        if not self.k8s_cluster_id:
            raise ValidationError(_('Please select a Kubernetes cluster first'))

        if not self.k8s_template_id:
            raise ValidationError(_('Please select a deployment template first'))

        if self.k8s_deployed:
            raise ValidationError(_('Instance already deployed to Kubernetes'))

        # TODO: Implement actual deployment logic
        # This is a placeholder - the actual implementation will:
        # 1. Generate manifests from template
        # 2. Apply manifests to cluster using kubectl/API
        # 3. Create database
        # 4. Update instance status

        self.message_post(body=_('Kubernetes deployment initiated (implementation pending)'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Deployment Initiated'),
                'message': _('Kubernetes deployment logic pending implementation. Configuration saved.'),
                'type': 'info',
                'sticky': False,
            }
        }

    def action_undeploy_from_k8s(self):
        """Remove this instance from Kubernetes"""
        self.ensure_one()

        if not self.k8s_deployed:
            raise ValidationError(_('Instance is not deployed to Kubernetes'))

        # TODO: Implement actual un-deployment logic
        # This will delete K8s resources: Deployment, Service, Ingress, PVC, etc.

        self.write({
            'k8s_deployed': False,
            'k8s_pod_status': 'unknown',
            'k8s_pod_count': 0,
        })

        self.message_post(body=_('Kubernetes resources removed (placeholder)'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Undeployment Completed'),
                'message': _('Instance removed from Kubernetes (placeholder).'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_check_k8s_status(self):
        """Check Kubernetes deployment status"""
        self.ensure_one()

        if not self.k8s_deployed:
            raise ValidationError(_('Instance is not deployed to Kubernetes'))

        # TODO: Implement actual K8s status check
        # This will query K8s API for pod status, service endpoints, etc.

        self.write({
            'k8s_last_health_check': fields.Datetime.now(),
            'k8s_health_message': _('Health check not yet implemented'),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Status Check'),
                'message': _('Kubernetes status check pending implementation.'),
                'type': 'info',
                'sticky': False,
            }
        }

    def action_view_k8s_manifests(self):
        """View/generate Kubernetes manifests for this instance"""
        self.ensure_one()

        if not self.k8s_template_id:
            raise ValidationError(_('Please select a deployment template first'))

        # TODO: Generate actual manifests using template
        # For now, show a placeholder message

        return {
            'type': 'ir.actions.act_window',
            'name': _('Kubernetes Manifests'),
            'res_model': 'saas.instance',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'show_k8s_manifests': True}
        }

    def action_open_k8s_config_wizard(self):
        """Open wizard to configure Kubernetes deployment"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Configure Kubernetes Deployment'),
            'res_model': 'saas.k8s.config.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_instance_id': self.id},
        }

    def action_restart_k8s_pods(self):
        """Restart Kubernetes pods for this instance"""
        self.ensure_one()

        if not self.k8s_deployed:
            raise ValidationError(_('Instance is not deployed to Kubernetes'))

        # TODO: Implement pod restart (kubectl rollout restart deployment/<name>)

        self.message_post(body=_('Pod restart initiated (placeholder)'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Restart Initiated'),
                'message': _('Kubernetes pods restart pending implementation.'),
                'type': 'info',
                'sticky': False,
            }
        }
