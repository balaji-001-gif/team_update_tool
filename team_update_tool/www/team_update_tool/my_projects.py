# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.title = _("My Projects")
	context.no_header = 1
	context.no_breadcrumbs = 1

	user = frappe.session.user
	if user == "Guest":
		frappe.local.flags.redirect_location = "/team_update_tool/login?redirect-to=/team_update_tool/my_projects"
		raise frappe.Redirect

	context.projects = frappe.get_all("Project",
		filters={"owner": user},
		fields=["name", "project_title", "status", "team", "priority",
				"project_category", "creation", "completion_date"],
		order_by="modified desc"
	)

	for p in context.projects:
		if p.status:
			s = frappe.get_cached_doc("Project Status", p.status)
			p.status_name = s.status_name
			p.status_color = s.color

	context.full_name = frappe.utils.get_fullname(user)
