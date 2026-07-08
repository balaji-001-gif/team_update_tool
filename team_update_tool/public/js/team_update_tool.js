// Team Update Tool - global client side helpers

frappe.provide("team_update_tool");

team_update_tool.show_viewer_banner = function (frm) {
	const roles = frappe.user_roles || [];
	const is_admin = roles.includes("Admin") || roles.includes("System Manager");
	const is_viewer = roles.includes("View-Only User");

	if (is_viewer && !is_admin) {
		frm.dashboard.set_headline_alert(
			'<div class="tut-readonly-banner">👁 View Only Access - You cannot create, edit, or delete records</div>'
		);
		frm.disable_form();
	}
};
