/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component, onMounted, onWillUnmount} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class OdashboardIframeWidget extends Component {
    setup() {
        // Retrieve the URL from the record's data to use as the iframe's src
        this.companyService = useService("company");
        const companyIds = this.companyService.activeCompanyIds;
        // Build the iframe URL with the company_ids parameter
        const baseUrl = this.props.record.data.connection_url || "";
        const companiesParam = `&company_ids=${companyIds.join(",")}`;

        this.iframeSrc = baseUrl + companiesParam;
        // Services
        this.actionService = useService("action");
        this.orm = useService("orm");

        // Method to handle messages from iframe
        this.handleMessage = this.handleMessage.bind(this);

        // Add event listener when component is mounted
        onMounted(() => {
            window.addEventListener("message", this.handleMessage, false);
            this.adjustIframePosition();
        });

        // Remove event listener when component is unmounted
        onWillUnmount(() => {
            window.removeEventListener("message", this.handleMessage, false);
        });
    }

    /**
     * Adjust iframe position based on neutralize banner presence
     */
    adjustIframePosition() {
        // Check if specific neutralize banner element is present
        const neutralizeBanner = document.querySelector('span#oe_neutralize_banner');
        const body = document.body;

        if (neutralizeBanner) {
            // Add class to body to indicate banner is active (for fallback browsers)
            body.classList.add('o_neutralize_banner_active');
        } else {
            // Remove class if banner is not present
            body.classList.remove('o_neutralize_banner_active');
        }
    }

    /**
     * Handle messages received from the iframe
     * @param {MessageEvent} event - The message event
     */
    handleMessage(event) {
        // Basic security check to validate message origin if needed
        // if (event.origin !== 'https://trusted-source.com') return;

        const message = event.data;

        // Process the message if it has the expected format
        if (message && typeof message === "object") {

            // Handle navigation request
            if (message.type === "navigate") {
                this.handleNavigation(message);
            } else if (message.type === "refresh") {
                window.location.reload()
            } else if (message.type === "openUrl") {
                if (message.target === "_self") {
                    window.location.href = message.url
                } else {
                    window.open(message.url)
                }
            }
        }
    }

    /**
     * Handle navigation requests from iframe
     * @param {Object} message - The navigation message
     */
    handleNavigation(message) {
        if (!message.model) {
            console.error("Navigation request missing model");
            return;
        }

        // Default action is to open a list view
        const action = {
            type: "ir.actions.act_window",
            res_model: message.model,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: message.target || "current",
            name: message.name || message.model,
        };

        // If domain is provided, add it to the action
        if (message.domain) {
            action.domain = message.domain;
        }

        // If record ID is provided, open form view instead
        if (message.res_id) {
            action.res_id = message.res_id;
            action.views = [[false, "form"]];
        }

        // Execute the action
        this.actionService.doAction(action);
    }
}

OdashboardIframeWidget.template = "OdashboardIframeWidgetTemplate";

export const OdashboardIframeWidgetDef = {
    component: OdashboardIframeWidget,
};

// Register the widget in the view_widgets registry
registry
    .category("view_widgets")
    .add("odashboard_iframe_widget", OdashboardIframeWidgetDef);
