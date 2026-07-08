# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.title = _("Dashboard")
	context.no_header = 1
	context.no_breadcrumbs = 1

	user = frappe.session.user
	if user == "Guest":
		frappe.local.flags.redirect_location = "/team_update_tool/login?redirect-to=/team_update_tool/dashboard"
		raise frappe.Redirect

	roles = frappe.get_roles(user)
	is_admin = "Admin" in roles or "System Manager" in roles
	is_viewer = "View-Only User" in roles and not is_admin

	context.is_admin = is_admin
	context.is_viewer = is_viewer
	context.full_name = frappe.utils.get_fullname(user)

	# Build base filters
	base_filters = {}
	if is_viewer:
		approved = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
		if approved:
			base_filters["status"] = approved

	# Stats
	context.total_projects = frappe.db.count("Project", filters=base_filters)
	context.total_teams = frappe.db.count("Team", filters={"is_active": 1})
	context.my_projects = frappe.db.count("Project", filters={"owner": user})

	# Status counts
	context.status_counts = []
	statuses = frappe.get_all("Project Status", fields=["name", "status_name", "color"])
	for s in statuses:
		f = {**base_filters, "status": s.name}
		count = frappe.db.count("Project", filters=f)
		if count:
			context.status_counts.append({
				"name": s.status_name,
				"count": count,
				"color": s.color,
			})

	# Your recent projects
	context.recent_projects = frappe.get_all("Project",
		filters={"owner": user},
		fields=["name", "project_title", "status", "creation"],
		limit=5,
		order_by="modified desc"
	)
	for p in context.recent_projects:
		if p.status:
			s = frappe.get_cached_doc("Project Status", p.status)
			p.status_name = s.status_name
			p.status_color = s.color

	# All recent projects (for admin)
	if is_admin:
		context.all_recent = frappe.get_all("Project",
			fields=["name", "project_title", "status", "owner", "creation"],
			limit=5,
			order_by="modified desc"
		)
		for p in context.all_recent:
			if p.status:
				s = frappe.get_cached_doc("Project Status", p.status)
				p.status_name = s.status_name
				p.status_color = s.color
