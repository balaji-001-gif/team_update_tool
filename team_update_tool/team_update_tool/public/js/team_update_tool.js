// Team Update Tool - global client side helpers

frappe.provide("team_update_tool");

/**
 * Shows a small "read only" banner on forms for users who only
 * hold the "Project Viewer" role, as a friendly visual reminder
 * that the record cannot be edited (actual enforcement is done via
 * DocType permissions on the server).
 */
team_update_tool.show_viewer_banner = function (frm) {
	const roles = frappe.user_roles || [];
	const is_admin = roles.includes("Project Admin") || roles.includes("System Manager");
	const is_viewer = roles.includes("Project Viewer");

	if (is_viewer && !is_admin) {
		frm.dashboard.set_headline_alert(
			'<div class="tut-readonly-banner">👁 View Only Access - Editing is disabled for your role</div>'
		);
		frm.disable_form();
	}
};
