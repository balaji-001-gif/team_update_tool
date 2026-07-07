// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Team", {
	refresh: function (frm) {
		team_update_tool.show_role_banner(frm);

		if (!frm.is_new()) {
			frm.add_custom_button(__("View Projects"), function () {
				frappe.set_route("List", "Team Project Update", { team: frm.doc.name });
			});
		}
	},
});
