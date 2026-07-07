// Team Update Tool - global client side helpers
// Supports 4 roles: Admin, Team Leader, Team Member, Viewer

frappe.provide("team_update_tool");

/**
 * Get the current user's roles.
 */
team_update_tool.get_roles = function () {
	return frappe.user_roles || [];
};

/**
 * Check which roles the current user has.
 */
team_update_tool.is_admin = function () {
	const roles = team_update_tool.get_roles();
	return roles.includes("Team Update Admin") || roles.includes("System Manager");
};

team_update_tool.is_team_leader = function () {
	const roles = team_update_tool.get_roles();
	return roles.includes("Team Update Team Leader") && !team_update_tool.is_admin();
};

team_update_tool.is_team_member = function () {
	const roles = team_update_tool.get_roles();
	return roles.includes("Team Update Team Member") && !team_update_tool.is_admin() && !roles.includes("Team Update Team Leader");
};

team_update_tool.is_viewer = function () {
	const roles = team_update_tool.get_roles();
	return roles.includes("Team Update Viewer") && !team_update_tool.is_admin() && !roles.includes("Team Update Team Leader") && !roles.includes("Team Update Team Member");
};

/**
 * Shows role-based banner on forms.
 */
team_update_tool.show_role_banner = function (frm) {
	if (team_update_tool.is_viewer()) {
		frm.dashboard.set_headline_alert(
			'<div class="tut-readonly-banner">👁 View Only Access - Editing is disabled for your role</div>'
		);
		frm.disable_form();
	} else if (team_update_tool.is_team_member()) {
		frm.dashboard.set_headline_alert(
			'<div class="tut-member-banner">🔧 Team Member - You can update progress and upload files</div>'
		);
	} else if (team_update_tool.is_team_leader()) {
		frm.dashboard.set_headline_alert(
			'<div class="tut-leader-banner">👥 Team Leader - You can assign tasks and review work</div>'
		);
	} else if (team_update_tool.is_admin()) {
		frm.dashboard.set_headline_alert(
			'<div class="tut-admin-banner">⚙️ Admin - Full access to all tasks</div>'
		);
	}
};

/**
 * Adds a "View on GitHub" button.
 */
team_update_tool.add_github_button = function (frm) {
	if (frm.doc.github_repo_url && !frm.is_new()) {
		frm.add_custom_button(__("Open GitHub Repo"), function () {
			window.open(frm.doc.github_repo_url, "_blank");
		}, __("View"));
	}
};

/**
 * Adds a "View Live Demo" button.
 */
team_update_tool.add_demo_button = function (frm) {
	if (frm.doc.live_demo_url && !frm.is_new()) {
		frm.add_custom_button(__("Open Live Demo"), function () {
			window.open(frm.doc.live_demo_url, "_blank");
		}, __("View"));
	}
};

/**
 * Sets the status indicator color on the form.
 */
team_update_tool.set_status_indicator = function (frm) {
	const colors = {
		Draft: "grey",
		Assigned: "purple",
		"In Progress": "orange",
		Completed: "green",
		"Under Review": "blue",
		Approved: "darkgreen",
		Rejected: "red",
	};
	if (frm.doc.status) {
		frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "grey");
	}
};

/**
 * Apply role-based field states on the Team Project Update form.
 * Hides or disables fields based on the user's role.
 */
team_update_tool.apply_role_field_states = function (frm) {
	if (frm.is_new()) return;

	if (team_update_tool.is_viewer()) {
		// Viewer - everything disabled via disable_form()
		return;
	}

	if (team_update_tool.is_team_member()) {
		// Team Member can only update progress, status, files, screenshots, description
		frm.set_df_property("assigned_team_leader", "read_only", 1);
		frm.set_df_property("assigned_by_admin", "read_only", 1);
		frm.set_df_property("assigned_to", "read_only", 1);
		frm.set_df_property("assigned_by_team_leader", "read_only", 1);
		frm.set_df_property("team_leader_review_status", "read_only", 1);
		frm.set_df_property("team_leader_review_remarks", "read_only", 1);
		frm.set_df_property("team_leader_review_date", "read_only", 1);
		frm.set_df_property("reviewed_by", "read_only", 1);
		frm.set_df_property("approved_by", "read_only", 1);
		frm.set_df_property("approval_date", "read_only", 1);
		frm.set_df_property("review_remarks", "read_only", 1);
		frm.set_df_property("project_owner", "read_only", 1);
	}

	if (team_update_tool.is_team_leader()) {
		// Team Leader can assign members, review, but not modify admin fields
		frm.set_df_property("assigned_by_admin", "read_only", 1);
		frm.set_df_property("assigned_by_team_leader", "read_only", 1);
		frm.set_df_property("reviewed_by", "read_only", 1);
		frm.set_df_property("approved_by", "read_only", 1);
		frm.set_df_property("approval_date", "read_only", 1);
		frm.set_df_property("project_owner", "read_only", 1);
	}
};

/**
 * Add role-appropriate custom buttons on the form.
 */
team_update_tool.add_role_actions = function (frm) {
	if (frm.is_new()) return;

	// Admin can approve/reject
	if (team_update_tool.is_admin()) {
		if (frm.doc.status === "Under Review" || frm.doc.status === "Completed") {
			frm.add_custom_button(__("Approve Task"), function () {
				frm.set_value("status", "Approved");
				frm.set_value("approved_by", frappe.session.user);
				frm.set_value("approval_date", frappe.datetime.get_today());
				frm.save();
			}, __("Actions"));
			frm.add_custom_button(__("Reject Task"), function () {
				frm.set_value("status", "Rejected");
				frm.save();
			}, __("Actions"));
		}
	}

	// Team Leader can review
	if (team_update_tool.is_team_leader() && frm.doc.status === "Completed") {
		frm.add_custom_button(__("Mark Reviewed"), function () {
			frm.set_value("team_leader_review_status", "Reviewed");
			frm.set_value("team_leader_review_date", frappe.datetime.get_today());
			frm.save();
		}, __("Actions"));
	}

	// Team Member can mark as completed
	if (team_update_tool.is_team_member() && frm.doc.progress_percent < 100 && frm.doc.status !== "Completed") {
		frm.add_custom_button(__("Mark 100% Complete"), function () {
			frm.set_value("progress_percent", 100);
			frm.set_value("status", "Completed");
			frm.save();
		}, __("Actions"));
	}
};
