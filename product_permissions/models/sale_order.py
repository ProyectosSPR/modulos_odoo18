# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_permission_products = fields.Boolean(
        string='Has Permission Products',
        compute='_compute_has_permission_products',
        store=True
    )

    permission_assigned = fields.Boolean(
        string='Permissions Assigned',
        default=False,
        readonly=True,
        copy=False,
        help='Indicates if permissions have been assigned for this order'
    )

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.assign_permissions')
    def _compute_has_permission_products(self):
        """Check if order contains products with permission assignment"""
        for order in self:
            order.has_permission_products = any(
                line.product_id.product_tmpl_id.assign_permissions
                for line in order.order_line
            )

    def action_confirm(self):
        """Override to assign permissions after order confirmation"""
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            if order.has_permission_products and not order.permission_assigned:
                order._assign_product_permissions()
                order.permission_assigned = True

        return res

    def _assign_product_permissions(self):
        """Assign permissions from products to customer user"""
        self.ensure_one()

        # Get customer's user
        partner = self.partner_id
        user = self._get_or_create_user_for_partner(partner)

        if not user:
            self.message_post(
                body=_('⚠️ Could not assign permissions: No user found or created for partner %s') % partner.name,
                message_type='comment'
            )
            return

        # Check if user is administrator - NEVER modify admin permissions
        if user.has_group('base.group_system'):
            self.message_post(
                body=_('ℹ️ Permissions not assigned: User %s is an administrator') % user.name,
                message_type='comment'
            )
            return

        # Collect all groups from permission products
        groups_to_assign = self.env['res.groups']

        for line in self.order_line:
            product = line.product_id.product_tmpl_id
            if product.assign_permissions and product.permission_group_ids:
                groups_to_assign |= product.permission_group_ids

        if not groups_to_assign:
            return

        # Assign permissions (ADDITIVE - preserve existing groups)
        self._apply_groups_to_user(user, groups_to_assign)

        # Log the action
        self.message_post(
            body=_('✅ Permissions assigned to user: <b>%s</b><br/>Groups added: %s') % (
                user.name,
                ', '.join(groups_to_assign.mapped('name'))
            ),
            message_type='notification'
        )

    def _get_or_create_user_for_partner(self, partner):
        """Get existing user or create new one for partner"""
        # Check if partner already has a user
        existing_user = partner.user_ids.filtered(lambda u: u.active)[:1]

        if existing_user:
            return existing_user

        # Create new user for partner
        try:
            user = self.env['res.users'].sudo().create({
                'name': partner.name,
                'login': partner.email or f'{partner.name.lower().replace(" ", ".")}@customer.local',
                'partner_id': partner.id,
                'company_id': self.company_id.id,
                'company_ids': [(6, 0, [self.company_id.id])],
                'groups_id': [(4, self.env.ref('base.group_user').id)],  # Basic internal user
            })

            self.message_post(
                body=_('👤 New user created: %s (Login: %s)') % (user.name, user.login),
                message_type='comment'
            )

            return user

        except Exception as e:
            self.message_post(
                body=_('❌ Error creating user: %s') % str(e),
                message_type='comment'
            )
            return False

    def _apply_groups_to_user(self, user, groups_to_assign):
        """Apply groups to user (ADDITIVE - preserves existing groups)"""
        # Get current groups
        existing_groups = user.groups_id

        # Check if we need to convert Portal user to Internal user
        portal_group = self.env.ref('base.group_portal')
        public_group = self.env.ref('base.group_public')
        internal_group = self.env.ref('base.group_user')

        is_portal = portal_group in existing_groups
        is_public = public_group in existing_groups

        # Check if any group to assign requires internal user
        # Groups that are NOT portal or public typically require internal access
        needs_internal = False
        portal_category = self.env.ref('base.module_category_portal', raise_if_not_found=False)

        for group in groups_to_assign:
            # Skip portal and public groups
            if group in [portal_group, public_group]:
                continue

            # Check if this group implies internal user
            if internal_group in group.implied_ids or group == internal_group:
                needs_internal = True
                break

            # If group is NOT in portal category, it likely requires internal access
            # Most functional groups require internal user access
            if group.category_id and group.category_id != portal_category:
                needs_internal = True
                break

        # If user is Portal/Public but needs Internal groups, convert to Internal
        if (is_portal or is_public) and needs_internal:
            # Remove portal and public groups
            existing_groups = existing_groups - portal_group - public_group

            # Ensure internal user group is included
            if internal_group not in groups_to_assign:
                groups_to_assign = groups_to_assign | internal_group

            self.message_post(
                body=_('ℹ️ User %s converted from Portal/Public to Internal User to receive internal permissions') % user.name
            )

        # Combine existing + new groups (set union to avoid duplicates)
        all_groups = existing_groups | groups_to_assign

        # Update user with combined groups
        user.sudo().write({
            'groups_id': [(6, 0, all_groups.ids)]
        })
