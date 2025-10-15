# SaaS Customer Management

## Overview

A comprehensive module for managing SaaS customers, service packages, and Odoo instances.

## Features

### Customer Management

- Complete customer information management (company details, contacts, addresses)
- Support contact management
- Customer status tracking (Prospect, Active, Suspended, Terminated)
- Financial overview with total revenue tracking

### Service Package Management

- Configurable service packages with different features and pricing
- Resource limits (users, storage, backup frequency)
- Feature toggles (custom domain, SSL, API access, priority support)
- Monthly and yearly pricing options

### Instance Management

- Odoo SaaS instance tracking
- Multiple status states (Provisioning, Trial, Active, Suspended, Expired, Terminated)
- Version and server location tracking
- Resource usage monitoring
- Automated status management

### Payment History

- Complete payment tracking
- Multiple payment methods support
- Billing period management
- Transaction status monitoring
- Financial reporting capabilities

### Key Benefits

- **Centralized Management**: All customer, instance, and payment data in one place
- **Automated Workflows**: Status updates and notifications
- **Financial Tracking**: Revenue and payment history
- **Scalable**: Supports multiple service packages and customers
- **User-friendly**: Intuitive interface with dashboards and reports

## Installation

1. Copy the module to your Odoo addons directory
2. Update the apps list
3. Install the "SaaS Customer Management" module

## Usage

### Creating a Customer

1. Go to SaaS Management > Customers > Customers
2. Click "Create" and fill in the customer information
3. Add contact details and support information

### Setting up Service Packages

1. Go to SaaS Management > Configuration > Service Packages
2. Configure your different service tiers
3. Set pricing, features, and resource limits

### Managing Instances

1. Go to SaaS Management > Customers > Instances
2. Create new instances for customers
3. Use action buttons to activate, suspend, or terminate instances

### Recording Payments

1. Go to SaaS Management > Reporting > Payment History
2. Record customer payments with transaction details
3. Track billing periods and payment status

## Technical Details

### Models

- `saas.customer`: Customer information and management
- `saas.service.package`: Service package definitions
- `saas.instance`: Odoo SaaS instance tracking
- `saas.payment.history`: Payment and billing history

### Dependencies

- base
- contacts
- account

## Support

For support and customization, please contact your Odoo partner or developer.

## License

LGPL-3
