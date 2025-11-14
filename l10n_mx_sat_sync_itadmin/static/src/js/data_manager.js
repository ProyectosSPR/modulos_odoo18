/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ActionContainer } from "@web/webclient/actions/action_container";
import { user } from "@web/core/user";

patch(ActionContainer.prototype, {
    /**
     * Override to add allowed_company_ids to additional context
     */
    async executeAction(actionRequest, options = {}) {
        if (options.additionalContext === undefined) {
            options.additionalContext = {};
        }
        if (user.context && user.context.allowed_company_ids) {
            options.additionalContext.allowed_company_ids = user.context.allowed_company_ids;
        }
        return super.executeAction(actionRequest, options);
    }
});
