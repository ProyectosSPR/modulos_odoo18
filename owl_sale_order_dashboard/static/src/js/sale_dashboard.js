/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, useState, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

// Main Dashboard Component
class SaleDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            total_orders: 0,
            total_revenue: 0,
            best_products: [],
            top_salespersons: [],
            status_overview: {},
            payment_summary: {},
            total_canceled: 0,
            total_not_invoiced: 0,
            start_date: "",
            end_date: "",
        });

        this.charts = {};

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            // Set default date range to last 30 days
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 30);

            this.state.end_date = endDate.toISOString().split('T')[0];
            this.state.start_date = startDate.toISOString().split('T')[0];

            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
            this.resizeHandler = () => this.renderCharts();
            window.addEventListener('resize', this.resizeHandler);
        });

        onWillUnmount(() => {
            if (this.resizeHandler) {
                window.removeEventListener('resize', this.resizeHandler);
            }
            this.destroyCharts();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "sale.order",
                "get_dashboard_data",
                [],
                {
                    start_date: this.state.start_date,
                    end_date: this.state.end_date
                }
            );
            this.state.total_orders = data.total_orders || 0;
            this.state.total_revenue = data.total_revenue || 0;
            this.state.total_canceled = data.total_canceled || 0;
            this.state.total_not_invoiced = data.total_not_invoiced || 0;
            this.state.best_products = data.best_products || [];
            this.state.top_salespersons = data.top_salespersons || [];
            this.state.status_overview = data.status_overview || {};
            this.state.payment_summary = data.payment_summary || {};
        } catch (error) {
            console.error("Error loading dashboard data:", error);
        } finally {
            this.state.loading = false;
        }
    }

    refreshDashboard() {
        this.loadData().then(() => {
            this.destroyCharts();
            this.renderCharts();
        });
    }

    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    renderCharts() {
        if (typeof Chart === 'undefined') {
            console.error("Chart.js is not loaded");
            return;
        }

        this.destroyCharts();

        // Best Products Bar Chart
        if (this.state.best_products.length) {
            this.charts.bestProducts = new Chart(document.getElementById("bestProductsChart"), {
                type: "bar",
                data: {
                    labels: this.state.best_products.map(p => p.name),
                    datasets: [{
                        label: "Units Sold",
                        data: this.state.best_products.map(p => p.qty),
                        backgroundColor: "rgba(54, 162, 235, 0.6)",
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    }
                }
            });
        }

        // Top Salespersons Horizontal Bar
        if (this.state.top_salespersons.length) {
            this.charts.topSalespersons = new Chart(document.getElementById("topSalespersonsChart"), {
                type: "bar",
                data: {
                    labels: this.state.top_salespersons.map(s => s.name),
                    datasets: [{
                        label: "Total Sales ($)",
                        data: this.state.top_salespersons.map(s => s.total_sales),
                        backgroundColor: "rgba(255, 99, 132, 0.6)",
                    }],
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    }
                }
            });
        }

        // Status Overview Pie
        if (Object.keys(this.state.status_overview).length) {
            const data = Object.values(this.state.status_overview);
            const total = data.reduce((a, b) => a + b, 0);
            this.charts.statusOverview = new Chart(document.getElementById("statusOverviewChart"), {
                type: "pie",
                data: {
                    labels: Object.keys(this.state.status_overview),
                    datasets: [{
                        data: data,
                        backgroundColor: ["#6c757d", "#0dcaf0", "#0d6efd", "#198754", "#dc3545"],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        }

        // Payment Summary Doughnut
        if (Object.keys(this.state.payment_summary).length) {
            this.charts.paymentSummary = new Chart(document.getElementById("paymentSummaryChart"), {
                type: "doughnut",
                data: {
                    labels: Object.keys(this.state.payment_summary),
                    datasets: [{
                        data: Object.values(this.state.payment_summary),
                        backgroundColor: ["#198754", "#ffc107", "#0dcaf0", "#dc3545"],
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        }
    }
}

SaleDashboard.template = "owl_sale_order_dashboard.SaleDashboard";
registry.category("actions").add("owl_sale_dashboard_tag", SaleDashboard);
