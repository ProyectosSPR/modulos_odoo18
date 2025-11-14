# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json


class SaasK8sDeploymentTemplate(models.Model):
    _name = 'saas.k8s.deployment.template'
    _description = 'Kubernetes Deployment Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # Basic Information
    name = fields.Char(
        string='Template Name',
        required=True,
        tracking=True
    )
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    code = fields.Char(
        string='Template Code',
        required=True,
        help='Unique code for this template (e.g., odoo-18-standard)'
    )

    description = fields.Text(string='Description')

    # Cluster
    cluster_id = fields.Many2one(
        'saas.k8s.cluster',
        string='Kubernetes Cluster',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    # Template Type
    template_type = fields.Selection([
        ('deployment', 'Deployment'),
        ('statefulset', 'StatefulSet'),
        ('helm', 'Helm Chart'),
    ], string='Template Type', default='deployment', required=True)

    # Odoo Configuration
    odoo_version = fields.Char(
        string='Odoo Version',
        default='18.0',
        required=True,
        help='Odoo version for this template (e.g., 16.0, 17.0, 18.0)'
    )

    odoo_image = fields.Char(
        string='Odoo Docker Image',
        required=True,
        help='Full Docker image name (e.g., odoo:18.0 or your-registry/odoo:18.0-custom)'
    )

    # Resource Specifications
    cpu_request = fields.Char(
        string='CPU Request',
        default='500m',
        help='CPU request for the pod (e.g., 500m, 1, 2)'
    )

    cpu_limit = fields.Char(
        string='CPU Limit',
        default='2',
        help='CPU limit for the pod'
    )

    memory_request = fields.Char(
        string='Memory Request',
        default='1Gi',
        help='Memory request for the pod (e.g., 512Mi, 1Gi, 2Gi)'
    )

    memory_limit = fields.Char(
        string='Memory Limit',
        default='2Gi',
        help='Memory limit for the pod'
    )

    replicas = fields.Integer(
        string='Replicas',
        default=1,
        help='Number of pod replicas'
    )

    # Storage Configuration
    enable_persistent_storage = fields.Boolean(
        string='Enable Persistent Storage',
        default=True,
        help='Create PersistentVolumeClaim for filestore'
    )

    storage_size = fields.Char(
        string='Storage Size',
        default='10Gi',
        help='Size of persistent volume for filestore'
    )

    storage_class = fields.Char(
        string='Storage Class',
        help='StorageClass name (leave empty to use cluster default)'
    )

    # Database Configuration
    enable_database_sidecar = fields.Boolean(
        string='Deploy Database Sidecar',
        default=False,
        help='Deploy PostgreSQL as sidecar container (for testing/demo)'
    )

    postgres_image = fields.Char(
        string='PostgreSQL Image',
        default='postgres:15',
        help='PostgreSQL Docker image'
    )

    postgres_storage_size = fields.Char(
        string='DB Storage Size',
        default='10Gi',
        help='Size of database persistent volume'
    )

    # Service Configuration
    service_type = fields.Selection([
        ('ClusterIP', 'ClusterIP'),
        ('NodePort', 'NodePort'),
        ('LoadBalancer', 'LoadBalancer'),
    ], string='Service Type', default='ClusterIP', required=True)

    service_port = fields.Integer(
        string='Service Port',
        default=8069,
        help='Odoo HTTP port'
    )

    # Ingress Configuration
    enable_ingress = fields.Boolean(
        string='Enable Ingress',
        default=True,
        help='Create Ingress resource for external access'
    )

    ingress_class = fields.Char(
        string='Ingress Class',
        help='Ingress class name (leave empty to use cluster default)'
    )

    enable_tls = fields.Boolean(
        string='Enable TLS',
        default=True,
        help='Enable HTTPS with automatic certificate'
    )

    # Environment Variables
    env_variables = fields.Text(
        string='Environment Variables',
        help='Additional environment variables in KEY=VALUE format (one per line)'
    )

    # ConfigMaps & Secrets
    configmap_data = fields.Text(
        string='ConfigMap Data',
        help='ConfigMap data in YAML format'
    )

    # YAML Templates (for advanced users)
    deployment_yaml = fields.Text(
        string='Deployment YAML Template',
        help='Custom Kubernetes Deployment YAML template. Use {variables} for placeholders.'
    )

    service_yaml = fields.Text(
        string='Service YAML Template',
        help='Custom Kubernetes Service YAML template'
    )

    ingress_yaml = fields.Text(
        string='Ingress YAML Template',
        help='Custom Kubernetes Ingress YAML template'
    )

    pvc_yaml = fields.Text(
        string='PVC YAML Template',
        help='Custom PersistentVolumeClaim YAML template'
    )

    # Helm Configuration (if template_type = 'helm')
    helm_chart_name = fields.Char(
        string='Helm Chart Name',
        help='Name of the Helm chart (e.g., bitnami/odoo)'
    )

    helm_chart_version = fields.Char(
        string='Helm Chart Version',
        help='Version of the Helm chart'
    )

    helm_values = fields.Text(
        string='Helm Values (YAML)',
        help='values.yaml content for Helm deployment'
    )

    # Addon Modules
    default_addons = fields.Char(
        string='Default Addons',
        help='Comma-separated list of addons to install by default (e.g., sale,crm,website)'
    )

    # Relationships
    instance_ids = fields.One2many(
        'saas.instance',
        'k8s_template_id',
        string='Instances Using This Template'
    )

    # Statistics
    instance_count = fields.Integer(
        string='Instances',
        compute='_compute_instance_count'
    )

    # Other
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('code_cluster_unique', 'UNIQUE(code, cluster_id)', 'Template code must be unique per cluster!'),
    ]

    @api.depends('instance_ids')
    def _compute_instance_count(self):
        """Count instances using this template"""
        for record in self:
            record.instance_count = len(record.instance_ids)

    @api.constrains('env_variables')
    def _check_env_variables_format(self):
        """Validate environment variables format"""
        for record in self:
            if record.env_variables:
                lines = record.env_variables.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and '=' not in line:
                        raise ValidationError(
                            _('Invalid environment variable format. Use KEY=VALUE format (one per line).\nInvalid line: %s') % line
                        )

    def action_preview_manifests(self):
        """Preview generated Kubernetes manifests (placeholder)"""
        self.ensure_one()

        # TODO: Implement manifest generation preview
        message = _("""
        Manifest Preview (Implementation Pending)

        This will show the generated Kubernetes manifests for:
        - Deployment/StatefulSet
        - Service
        - Ingress
        - PersistentVolumeClaim
        - ConfigMap
        - Secrets

        Template: %s
        Cluster: %s
        Odoo Version: %s
        """) % (self.name, self.cluster_id.name, self.odoo_version)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Manifest Preview'),
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }

    def action_view_instances(self):
        """View instances using this template"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Instances Using This Template'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('k8s_template_id', '=', self.id)],
            'context': {'default_k8s_template_id': self.id},
        }

    def action_generate_default_yamls(self):
        """Generate default YAML templates"""
        self.ensure_one()

        # Generate basic deployment YAML
        deployment_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: odoo-{instance_id}
  namespace: {namespace}
  labels:
    app: odoo
    instance: {instance_id}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: odoo
      instance: {instance_id}
  template:
    metadata:
      labels:
        app: odoo
        instance: {instance_id}
    spec:
      containers:
      - name: odoo
        image: {odoo_image}
        ports:
        - containerPort: 8069
          name: http
        - containerPort: 8072
          name: longpolling
        env:
        - name: HOST
          value: "{db_host}"
        - name: PORT
          value: "{db_port}"
        - name: USER
          value: "{db_user}"
        - name: PASSWORD
          valueFrom:
            secretKeyRef:
              name: odoo-{instance_id}-secret
              key: db-password
        resources:
          requests:
            cpu: "{cpu_request}"
            memory: "{memory_request}"
          limits:
            cpu: "{cpu_limit}"
            memory: "{memory_limit}"
        volumeMounts:
        - name: filestore
          mountPath: /var/lib/odoo
      volumes:
      - name: filestore
        persistentVolumeClaim:
          claimName: odoo-{instance_id}-filestore
"""

        service_yaml = """apiVersion: v1
kind: Service
metadata:
  name: odoo-{instance_id}
  namespace: {namespace}
  labels:
    app: odoo
    instance: {instance_id}
spec:
  type: {service_type}
  ports:
  - port: 8069
    targetPort: 8069
    name: http
  - port: 8072
    targetPort: 8072
    name: longpolling
  selector:
    app: odoo
    instance: {instance_id}
"""

        ingress_yaml = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: odoo-{instance_id}
  namespace: {namespace}
  labels:
    app: odoo
    instance: {instance_id}
  annotations:
    cert-manager.io/cluster-issuer: "{cert_issuer}"
spec:
  ingressClassName: {ingress_class}
  tls:
  - hosts:
    - {subdomain}.{base_domain}
    secretName: odoo-{instance_id}-tls
  rules:
  - host: {subdomain}.{base_domain}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: odoo-{instance_id}
            port:
              number: 8069
      - path: /longpolling
        pathType: Prefix
        backend:
          service:
            name: odoo-{instance_id}
            port:
              number: 8072
"""

        pvc_yaml = """apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: odoo-{instance_id}-filestore
  namespace: {namespace}
  labels:
    app: odoo
    instance: {instance_id}
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: {storage_size}
  storageClassName: {storage_class}
"""

        self.write({
            'deployment_yaml': deployment_yaml,
            'service_yaml': service_yaml,
            'ingress_yaml': ingress_yaml,
            'pvc_yaml': pvc_yaml,
        })

        self.message_post(body=_('Default YAML templates generated successfully'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Default YAML templates have been generated. You can now customize them as needed.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def name_get(self):
        """Display version and name"""
        result = []
        for record in self:
            name = f"[{record.odoo_version}] {record.name}"
            result.append((record.id, name))
        return result
