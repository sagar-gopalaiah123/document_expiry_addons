/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class DocumentExpiryDashboard extends Component {
    static template = "document_expiry_engine.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            kpis: {
                total: 0,
                valid: 0,
                expiring_soon: 0,
                expired: 0,
                today: 0,
                in_7: 0,
                in_30: 0,
            },
            statusBreakdown: [],
            typeBreakdown: [],
            timeline: [
                { label: "Today", key: "today", value: 0, domain_max: 0 },
                { label: "Within 7 Days", key: "d7", value: 0, domain_max: 7 },
                { label: "Within 15 Days", key: "d15", value: 0, domain_max: 15 },
                { label: "Within 30 Days", key: "d30", value: 0, domain_max: 30 },
                { label: "Within 60 Days", key: "d60", value: 0, domain_max: 60 },
                { label: "Within 90 Days", key: "d90", value: 0, domain_max: 90 },
            ],
            loading: true,
            lastUpdated: null,
        });

        this.statusMeta = {
            valid: { label: "Valid", color: "#2e7d32", icon: "fa-check-circle" },
            expiring_soon: { label: "Expiring Soon", color: "#ed6c02", icon: "fa-exclamation-triangle" },
            expired: { label: "Expired", color: "#d32f2f", icon: "fa-times-circle" },
            no_expiry: { label: "No Expiry", color: "#78909c", icon: "fa-minus-circle" },
        };

        this.kpiMeta = {
            total: { label: "Total Documents", icon: "fa-folder-open", color: "#3876a3" },
            valid: { label: "Valid", icon: "fa-check-circle", color: "#2e7d32" },
            expiring_soon: { label: "Expiring Soon", icon: "fa-exclamation-triangle", color: "#ed6c02" },
            expired: { label: "Expired", icon: "fa-times-circle", color: "#d32f2f" },
            today: { label: "Expiring Today", icon: "fa-calendar-times-o", color: "#c2185b" },
            in_7: { label: "Expiring in 7 Days", icon: "fa-calendar", color: "#7b1fa2" },
            in_30: { label: "Expiring in 30 Days", icon: "fa-calendar-o", color: "#0277bd" },
        };

        onWillStart(async () => await this.loadData());
    }

    async refresh() {
        await this.loadData();
    }

    async loadData() {
        this.state.loading = true;
        const [total, valid, expiring_soon, expired, today, in_7, in_30] = await Promise.all([
            this.orm.searchCount("document.expiry.document", []),
            this.orm.searchCount("document.expiry.document", [["status", "=", "valid"]]),
            this.orm.searchCount("document.expiry.document", [["status", "=", "expiring_soon"]]),
            this.orm.searchCount("document.expiry.document", [["status", "=", "expired"]]),
            this.orm.searchCount("document.expiry.document", [
                ["status", "!=", "no_expiry"], ["days_remaining", "=", 0]]),
            this.orm.searchCount("document.expiry.document", [
                ["status", "!=", "no_expiry"], ["days_remaining", ">=", 0], ["days_remaining", "<=", 7]]),
            this.orm.searchCount("document.expiry.document", [
                ["status", "!=", "no_expiry"], ["days_remaining", ">=", 0], ["days_remaining", "<=", 30]]),
        ]);
        Object.assign(this.state.kpis, { total, valid, expiring_soon, expired, today, in_7, in_30 });

        const statusGroups = await this.orm.readGroup(
            "document.expiry.document", [], ["status"], ["status"]);
        const statusMaxCount = Math.max(1, ...statusGroups.map((g) => g.status_count || g.__count || 0));
        this.state.statusBreakdown = statusGroups
            .map((g) => {
                const key = g.status || "no_expiry";
                const count = g.status_count || g.__count || 0;
                const meta = this.statusMeta[key] || { label: key, color: "#90a4ae", icon: "fa-file-o" };
                return {
                    key,
                    label: meta.label,
                    color: meta.color,
                    icon: meta.icon,
                    count,
                    pct: total ? Math.round((count / total) * 100) : 0,
                    barPct: Math.round((count / statusMaxCount) * 100),
                };
            })
            .sort((a, b) => b.count - a.count);

        const typeGroups = await this.orm.readGroup(
            "document.expiry.document", [], ["document_type_id"], ["document_type_id"]);
        const typeMaxCount = Math.max(1, ...typeGroups.map((g) => g.document_type_id_count || g.__count || 0));
        this.state.typeBreakdown = typeGroups
            .map((g) => {
                const count = g.document_type_id_count || g.__count || 0;
                return {
                    id: g.document_type_id ? g.document_type_id[0] : false,
                    label: g.document_type_id ? g.document_type_id[1] : "Not Set",
                    count,
                    pct: total ? Math.round((count / total) * 100) : 0,
                    barPct: Math.round((count / typeMaxCount) * 100),
                };
            })
            .sort((a, b) => b.count - a.count);

        const timelineCounts = await Promise.all(
            this.state.timeline.map((t) =>
                this.orm.searchCount("document.expiry.document", [
                    ["status", "!=", "no_expiry"],
                    ["days_remaining", ">=", 0],
                    ["days_remaining", "<=", t.domain_max],
                ])
            )
        );
        const timelineMax = Math.max(1, ...timelineCounts);
        this.state.timeline.forEach((t, i) => {
            t.value = timelineCounts[i];
            t.barPct = Math.round((timelineCounts[i] / timelineMax) * 100);
        });

        this.state.loading = false;
        this.state.lastUpdated = new Date().toLocaleTimeString();
    }

    async openFiltered(domain, name) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: name || "Documents",
            res_model: "document.expiry.document",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    onKpiClick(key) {
        const domainMap = {
            total: [],
            valid: [["status", "=", "valid"]],
            expiring_soon: [["status", "=", "expiring_soon"]],
            expired: [["status", "=", "expired"]],
            today: [["status", "!=", "no_expiry"], ["days_remaining", "=", 0]],
            in_7: [["status", "!=", "no_expiry"], ["days_remaining", ">=", 0], ["days_remaining", "<=", 7]],
            in_30: [["status", "!=", "no_expiry"], ["days_remaining", ">=", 0], ["days_remaining", "<=", 30]],
        };
        this.openFiltered(domainMap[key], this.kpiMeta[key] ? this.kpiMeta[key].label : "Documents");
    }

    onStatusClick(statusKey, label) {
        this.openFiltered([["status", "=", statusKey]], label);
    }

    onTypeClick(typeId, label) {
        const domain = typeId ? [["document_type_id", "=", typeId]] : [["document_type_id", "=", false]];
        this.openFiltered(domain, label);
    }

    onTimelineClick(item) {
        this.openFiltered(
            [["status", "!=", "no_expiry"], ["days_remaining", ">=", 0], ["days_remaining", "<=", item.domain_max]],
            item.label
        );
    }
}

registry.category("actions").add("document_expiry_dashboard", DocumentExpiryDashboard);