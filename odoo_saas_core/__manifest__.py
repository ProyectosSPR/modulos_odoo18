# -*- coding: utf-8 -*-
{
    'name': 'Odoo SaaS Core',
    'version': '18.0.1.0.0',
    'category': 'Sales/SaaS',
    'summary': 'Core SaaS Management - Customers, Instances, Service Packages & Auto-Provisioning',
    'description': """
        Unified SaaS Management Module for Odoo 18
        ===========================================

        This module provides a complete SaaS management solution including:

        * Customer lifecycle management (Prospect → Active → Suspended → Terminated)
        * Odoo instance provisioning and monitoring
        * Service package configuration with pricing tiers
        * Automatic user and company provisioning
        * Security group assignment based on purchased products
        * Multi-company security rules
        * Trial period management
        * Storage and user usage monitoring
        * Integration with subscription management
        * **Kubernetes Integration** (New in v1.1.0):
          - Kubernetes cluster configuration
          - Deployment template management
          - Automated manifest generation
          - Infrastructure management interface

        Perfect for companies offering Odoo as a Service to their customers.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'account',
        'contacts',
    ],
    'data': [
        # Security
        'security/saas_security_groups.xml',
        'security/ir.model.access.csv',
        'security/saas_security_rules.xml',

        # Data
        'data/saas_instance_status_data.xml',
        'data/saas_service_package_data.xml',
        'data/automated_actions.xml',
        'data/sequences.xml',

        # Views
        'views/saas_customer_views.xml',
        'views/saas_instance_views.xml',
        'views/saas_service_package_views.xml',
        'views/saas_k8s_cluster_views.xml',
        'views/saas_k8s_deployment_template_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/saas_menus.xml',

        # Wizards
        'wizards/saas_instance_wizard_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
