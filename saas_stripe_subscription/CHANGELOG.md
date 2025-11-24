# Changelog

## [18.0.1.0.0] - 2025-01-24

### Added
- Initial release
- Automatic subscription synchronization between Odoo and Stripe
- Customer creation and management in Stripe
- Product and price synchronization
- Support for subscription lifecycle: create, update, cancel
- Automatic detection of test vs production mode
- Manual sync action for subscription status
- Configuration settings for default behavior
- Comprehensive error handling and logging
- Support for recurring intervals (day, week, month, year)

### Features
- Inherit `subscription.package` model to add Stripe fields
- Inherit `product.template` to add Stripe product sync
- Integration with `payment_stripe` provider for API credentials
- Automatic customer creation in Stripe when starting subscription
- Automatic product/price creation in Stripe when adding to subscription
- Subscription update when products/quantities change
- Subscription cancellation sync when closing in Odoo
- Status synchronization from Stripe
- Support for metadata to link Odoo and Stripe records

### Technical
- Compatible with Odoo 18.0
- Depends on: subscription_package, payment_stripe, saas_management
- Uses Stripe API v1
- LGPL-3 License
