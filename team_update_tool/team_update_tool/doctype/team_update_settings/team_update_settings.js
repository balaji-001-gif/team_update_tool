// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Team Update Settings", {
	refresh: function (frm) {
		team_update_tool.show_role_banner(frm);
	},
});
