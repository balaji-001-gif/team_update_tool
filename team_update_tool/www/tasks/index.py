# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def get_context(context, **kwargs):
	"""Build the tasks page context - list or detail view."""
	context.no_sidebar = 1
	context.no_cache = 1
	context.title = "Tasks - Team Update Tool"

	roles = frappe.get_roles(frappe.session.user)
	context.is_admin = "Team Update Admin" in roles or "System Manager" in roles
	context.is_team_leader = "Team Update Team Leader" in roles
	context.is_team_member = "Team Update Team Member" in roles
	context.is_viewer = "Team Update Viewer" in roles

	task_name = kwargs.get("name")

	if task_name:
		try:
			task = frappe.get_doc("Team Project Update", task_name)
			context.task = task
			context.is_detail = True
			context.title = f"{task.project_title} - Tasks"
		except Exception:
			frappe.local.flags.redirect_location = "/tasks"
			raise frappe.Redirect
	else:
		context.is_detail = False
		filters = build_task_filters(roles)

		search = frappe.form_dict.get("search")
		status_filter = frappe.form_dict.get("status")

		if search:
			filters.append(("project_title", "like", f"%{search}%"))
		if status_filter:
			filters.append(("status", "=", status_filter))

		context.tasks = frappe.get_list(
			"Team Project Update",
			filters=filters,
			fields=["name", "project_title", "team", "status", "priority", "progress_percent",
					"assigned_team_leader", "assigned_to", "due_date", "completion_date"],
			order_by="modified desc",
			limit=50,
		)
		context.statuses = ["Draft", "Assigned", "In Progress", "Completed", "Under Review", "Approved", "Rejected"]
		context.active_status = status_filter or ""
		context.search_query = search or ""


def build_task_filters(roles):
	if "Team Update Admin" in roles or "System Manager" in roles:
		return []
	elif "Team Update Team Leader" in roles:
		return [["assigned_team_leader", "=", frappe.session.user]]
	elif "Team Update Team Member" in roles:
		return [["assigned_to", "=", frappe.session.user]]
	elif "Team Update Viewer" in roles:
		return [["status", "=", "Approved"]]
	return []
