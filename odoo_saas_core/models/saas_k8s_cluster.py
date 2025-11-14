# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaasK8sCluster(models.Model):
    _name = 'saas.k8s.cluster'
    _description = 'Kubernetes Cluster Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # Basic Information
    name = fields.Char(
        string='Cluster Name',
        required=True,
        tracking=True,
        help='Friendly name for this Kubernetes cluster'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # Connection Details
    api_server_url = fields.Char(
        string='API Server URL',
        required=True,
        tracking=True,
        help='Kubernetes API server endpoint (e.g., https://k8s.example.com:6443)'
    )

    # Authentication
    auth_method = fields.Selection([
        ('token', 'Bearer Token'),
        ('certificate', 'Client Certificate'),
        ('kubeconfig', 'Kubeconfig File'),
    ], string='Authentication Method', default='token', required=True, tracking=True)

    bearer_token = fields.Text(
        string='Bearer Token',
        groups='base.group_system',
        help='Service account token for authentication'
    )

    client_certificate = fields.Text(
        string='Client Certificate',
        groups='base.group_system',
        help='PEM-encoded client certificate'
    )

    client_key = fields.Text(
        string='Client Key',
        groups='base.group_system',
        help='PEM-encoded client key'
    )

    ca_certificate = fields.Text(
        string='CA Certificate',
        groups='base.group_system',
        help='PEM-encoded cluster CA certificate'
    )

    kubeconfig = fields.Text(
        string='Kubeconfig Content',
        groups='base.group_system',
        help='Full kubeconfig file content'
    )

    # Cluster Information
    cluster_version = fields.Char(
        string='Kubernetes Version',
        help='Current Kubernetes version (e.g., v1.28.0)'
    )

    provider = fields.Selection([
        ('gke', 'Google Kubernetes Engine (GKE)'),
        ('eks', 'Amazon Elastic Kubernetes Service (EKS)'),
        ('aks', 'Azure Kubernetes Service (AKS)'),
        ('digitalocean', 'DigitalOcean Kubernetes'),
        ('linode', 'Linode Kubernetes Engine'),
        ('on_premise', 'On-Premise / Self-Hosted'),
        ('other', 'Other'),
    ], string='Provider', default='on_premise', tracking=True)

    region = fields.Char(
        string='Region/Zone',
        help='Cloud provider region or datacenter location'
    )

    # Default Settings for Deployments
    default_namespace = fields.Char(
        string='Default Namespace',
        default='odoo-saas',
        required=True,
        help='Default namespace for new deployments'
    )

    default_storage_class = fields.Char(
        string='Default Storage Class',
        help='Default StorageClass for PersistentVolumeClaims'
    )

    # Resource Limits
    max_instances = fields.Integer(
        string='Max Instances',
        default=0,
        help='Maximum number of instances allowed on this cluster (0 = unlimited)'
    )

    current_instances = fields.Integer(
        string='Current Instances',
        compute='_compute_current_instances',
        store=True
    )

    # Network Configuration
    ingress_class = fields.Char(
        string='Ingress Class',
        default='nginx',
        help='Ingress controller class name (nginx, traefik, etc.)'
    )

    base_domain = fields.Char(
        string='Base Domain',
        help='Base domain for instance subdomains (e.g., saas.example.com)'
    )

    enable_tls = fields.Boolean(
        string='Enable TLS/SSL',
        default=True,
        help='Enable automatic TLS certificate provisioning'
    )

    cert_manager_issuer = fields.Char(
        string='Cert-Manager Issuer',
        help="Cert-manager ClusterIssuer name (e.g., 'letsencrypt-prod')"
    )

    # Container Registry
    container_registry = fields.Char(
        string='Container Registry',
        help='Docker registry URL for Odoo images (e.g., docker.io, gcr.io)'
    )

    registry_username = fields.Char(
        string='Registry Username',
        groups='base.group_system'
    )

    registry_password = fields.Char(
        string='Registry Password',
        groups='base.group_system'
    )

    # Database Configuration
    db_host_template = fields.Char(
        string='Database Host Template',
        help='Template for DB host. Use {instance_id} for dynamic value. E.g., postgres-{instance_id}.default.svc.cluster.local'
    )

    db_port = fields.Integer(
        string='Database Port',
        default=5432
    )

    db_user_template = fields.Char(
        string='DB User Template',
        help='Template for DB username. Use {instance_id}. E.g., odoo_{instance_id}'
    )

    # Relationships
    instance_ids = fields.One2many(
        'saas.instance',
        'k8s_cluster_id',
        string='Instances'
    )

    deployment_template_ids = fields.One2many(
        'saas.k8s.deployment.template',
        'cluster_id',
        string='Deployment Templates'
    )

    # Status & Health
    status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('unknown', 'Unknown'),
    ], string='Status', default='unknown', tracking=True)

    last_health_check = fields.Datetime(
        string='Last Health Check',
        readonly=True
    )

    health_message = fields.Text(
        string='Health Status Message',
        readonly=True
    )

    # Other
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Cluster name must be unique!'),
    ]

    @api.depends('instance_ids')
    def _compute_current_instances(self):
        """Count instances deployed on this cluster"""
        for record in self:
            record.current_instances = len(
                record.instance_ids.filtered(lambda i: i.status in ['trial', 'active'])
            )

    @api.constrains('current_instances', 'max_instances')
    def _check_instance_limit(self):
        """Validate instance limits"""
        for record in self:
            if record.max_instances > 0 and record.current_instances > record.max_instances:
                raise ValidationError(
                    _('Cluster instance limit exceeded! Current: %s, Max: %s') %
                    (record.current_instances, record.max_instances)
                )

    def action_test_connection(self):
        """Test Kubernetes cluster connection (placeholder for future implementation)"""
        self.ensure_one()

        # TODO: Implement actual K8s API connection test
        # For now, just update status
        self.write({
            'status': 'unknown',
            'last_health_check': fields.Datetime.now(),
            'health_message': _('Connection test not yet implemented. Please configure Kubernetes integration.')
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connection Test'),
                'message': _('Kubernetes integration is pending implementation. Configuration saved.'),
                'type': 'info',
                'sticky': False,
            }
        }

    def action_view_instances(self):
        """View instances on this cluster"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cluster Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('k8s_cluster_id', '=', self.id)],
            'context': {'default_k8s_cluster_id': self.id},
        }

    def action_view_templates(self):
        """View deployment templates for this cluster"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deployment Templates'),
            'res_model': 'saas.k8s.deployment.template',
            'view_mode': 'list,form',
            'domain': [('cluster_id', '=', self.id)],
            'context': {'default_cluster_id': self.id},
        }

    def name_get(self):
        """Display provider and name"""
        result = []
        for record in self:
            provider_name = dict(self._fields['provider'].selection).get(record.provider, '')
            if provider_name:
                name = f"[{provider_name}] {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result
