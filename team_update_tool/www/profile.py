# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	"""Build the profile page context."""
	context.no_sidebar = 1
	context.no_cache = 1
	context.title = "Profile - Team Update Tool"

	user = frappe.get_doc("User", frappe.session.user)
	context.user_profile = user
	context.user_roles = frappe.get_roles(frappe.session.user)

	# Get user's teams
	context.user_teams = frappe.get_all(
		"Team Member",
		filters={"user": frappe.session.user},
		fields=["parent", "role_in_team"]
	)

	# Get user's task stats
	roles = frappe.get_roles(frappe.session.user)
	if "Team Update Admin" in roles or "System Manager" in roles:
		context.my_tasks = frappe.db.count("Team Project Update")
		context.completed_tasks = frappe.db.count("Team Project Update", {"status": "Approved"})
	elif "Team Update Team Leader" in roles:
		context.my_tasks = frappe.db.count("Team Project Update", {"assigned_team_leader": frappe.session.user})
		context.completed_tasks = frappe.db.count("Team Project Update", {"assigned_team_leader": frappe.session.user, "status": "Approved"})
	elif "Team Update Team Member" in roles:
		context.my_tasks = frappe.db.count("Team Project Update", {"assigned_to": frappe.session.user})
		context.completed_tasks = frappe.db.count("Team Project Update", {"assigned_to": frappe.session.user, "status": "Approved"})
	else:
		context.my_tasks = 0
		context.completed_tasks = 0
