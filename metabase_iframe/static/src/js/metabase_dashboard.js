/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MetabaseDashboardViewer extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            dashboard: null,
            loading: true,
            error: null,
        });

        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        try {
            const dashboardId = this.props.action.params.dashboard_id;

            const dashboards = await this.orm.searchRead(
                "metabase.dashboard",
                [["id", "=", dashboardId]],
                ["name", "iframe_url", "description", "height"]
            );

            if (dashboards.length > 0) {
                this.state.dashboard = dashboards[0];
            } else {
                this.state.error = "Dashboard not found";
            }
        } catch (error) {
            console.error("Error loading dashboard:", error);
            this.state.error = "Error loading dashboard";
        } finally {
            this.state.loading = false;
        }
    }

    get iframeStyle() {
        const height = this.state.dashboard?.height || 800;
        return `width: 100%; height: ${height}px; border: none;`;
    }
}

MetabaseDashboardViewer.template = "metabase_iframe.MetabaseDashboardViewer";

registry.category("actions").add("metabase_dashboard_viewer", MetabaseDashboardViewer);
