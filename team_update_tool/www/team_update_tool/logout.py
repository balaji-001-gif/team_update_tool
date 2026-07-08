# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe

no_cache = 1


def get_context(context):
	context.no_breadcrumbs = 1
	context.title = "Sign Out"

	# Logout via Frappe's standard logout
	if frappe.session.user != "Guest":
		frappe.local.login_manager.logout()
		frappe.db.commit()

	frappe.local.flags.redirect_location = "/team_update_tool"
	raise frappe.Redirect
