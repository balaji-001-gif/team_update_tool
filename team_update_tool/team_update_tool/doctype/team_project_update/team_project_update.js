// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Team Project Update", {
	refresh: function (frm) {
		team_update_tool.show_role_banner(frm);
		team_update_tool.add_github_button(frm);
		team_update_tool.add_demo_button(frm);
		team_update_tool.set_status_indicator(frm);
		team_update_tool.apply_role_field_states(frm);
		team_update_tool.add_role_actions(frm);
	},

	status: function (frm) {
		team_update_tool.set_status_indicator(frm);
	},

	assigned_team_leader: function (frm) {
		if (frm.doc.assigned_team_leader && !frm.is_new()) {
			frm.set_value("assigned_by_admin", 1);
			if (frm.doc.status === "Draft") {
				frm.set_value("status", "Assigned");
			}
		}
	},

	assigned_to: function (frm) {
		if (frm.doc.assigned_to && !frm.is_new()) {
			frm.set_value("assigned_by_team_leader", 1);
			if (frm.doc.status === "Assigned") {
				frm.set_value("status", "In Progress");
			}
		}
	},

	team_leader_review_status: function (frm) {
		if (frm.doc.team_leader_review_status === "Reviewed") {
			if (!frm.doc.team_leader_review_date) {
				frm.set_value("team_leader_review_date", frappe.datetime.get_today());
			}
			frm.set_value("status", "Under Review");
		}
	},

	progress_percent: function (frm) {
		if (frm.doc.progress_percent === 100) {
			frm.set_value("status", "Completed");
		}
	},
});
