# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def get_context(context, **kwargs):
	"""Build the projects page context - list or detail view."""
	context.no_sidebar = 1
	context.no_cache = 1
	context.title = "Projects - Team Update Tool"

	roles = frappe.get_roles(frappe.session.user)
	context.is_admin = "Team Update Admin" in roles or "System Manager" in roles
	context.is_team_leader = "Team Update Team Leader" in roles
	context.is_team_member = "Team Update Team Member" in roles
	context.is_viewer = "Team Update Viewer" in roles

	project_name = kwargs.get("name")

	if project_name:
		# Detail view
		if not frappe.db.exists("Team Project Update", project_name):
			context.message = "Project not found."
			context.is_detail = False
			context.projects = []
			return

		project = frappe.get_doc("Team Project Update", project_name)

		# Permission check
		if not has_project_access(project, roles):
			context.message = "You do not have permission to view this project."
			context.is_detail = False
			context.projects = []
			return

		context.project = project
		context.is_detail = True
		context.title = f"{project.project_title} - Team Update Tool"

		# Get screenshots
		context.screenshots = frappe.get_all(
			"Project Screenshot",
			filters={"parent": project_name},
			fields=["screenshot", "caption", "screenshot_type"]
		)

		# Get files
		context.project_files = frappe.get_all(
			"Project File",
			filters={"parent": project_name},
			fields=["file_attachment", "file_description"]
		)
	else:
		# List view
		context.is_detail = False
		filters = build_list_filters(roles)

		search = frappe.form_dict.get("search")
		status_filter = frappe.form_dict.get("status")

		if search:
			filters.append(("project_title", "like", f"%{search}%"))
		if status_filter:
			filters.append(("status", "=", status_filter))

		context.projects = frappe.get_list(
			"Team Project Update",
			filters=filters,
			fields=["name", "project_title", "team", "status", "priority", "progress_percent",
					"assigned_team_leader", "assigned_to", "due_date", "completion_date", "modified"],
			order_by="modified desc",
			limit=50,
		)
		context.statuses = ["Draft", "Assigned", "In Progress", "Completed", "Under Review", "Approved", "Rejected"]
		context.active_status = status_filter or ""
		context.search_query = search or ""


def build_list_filters(roles):
	"""Build filters based on user role."""
	if "Team Update Admin" in roles or "System Manager" in roles:
		return []
	elif "Team Update Team Leader" in roles:
		return [["assigned_team_leader", "=", frappe.session.user]]
	elif "Team Update Team Member" in roles:
		return [["assigned_to", "=", frappe.session.user]]
	elif "Team Update Viewer" in roles:
		return [["status", "=", "Approved"]]
	return []


def has_project_access(project, roles):
	"""Check if user has access to view this project."""
	if "Team Update Admin" in roles or "System Manager" in roles:
		return True
	if "Team Update Viewer" in roles and project.status == "Approved":
		return True
	if "Team Update Team Leader" in roles and project.assigned_team_leader == frappe.session.user:
		return True
	if "Team Update Team Member" in roles and project.assigned_to == frappe.session.user:
		return True
	return False
