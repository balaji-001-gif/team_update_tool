# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def get_context(context):
	"""Build the dashboard context with role-based data."""
	context.no_sidebar = 1
	context.no_cache = 1
	context.title = "Team Update Tool - Dashboard"

	roles = frappe.get_roles(frappe.session.user)
	context.is_admin = "Team Update Admin" in roles or "System Manager" in roles
	context.is_team_leader = "Team Update Team Leader" in roles
	context.is_team_member = "Team Update Team Member" in roles
	context.is_viewer = "Team Update Viewer" in roles

	context.stats = get_dashboard_stats(roles)
	context.recent_projects = get_recent_projects(roles)
	context.recent_notifications = get_recent_notifications()
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.user_email = frappe.session.user


def get_dashboard_stats(roles):
	"""Get dashboard statistics based on user role."""
	stats = {
		"total_projects": 0,
		"completed_projects": 0,
		"pending_tasks": 0,
		"active_teams": 0,
		"total_members": 0,
	}

	project_doctype = "Team Project Update"
	team_doctype = "Team"

	# Count based on permissions
	if "Team Update Admin" in roles or "System Manager" in roles:
		stats["total_projects"] = frappe.db.count(project_doctype)
		stats["completed_projects"] = frappe.db.count(project_doctype, {"status": "Approved"})
		stats["pending_tasks"] = stats["total_projects"] - stats["completed_projects"]
		stats["active_teams"] = frappe.db.count(team_doctype, {"is_active": 1})
	elif "Team Update Team Leader" in roles:
		stats["total_projects"] = frappe.db.count(project_doctype, {"assigned_team_leader": frappe.session.user})
		stats["completed_projects"] = frappe.db.count(project_doctype, {"assigned_team_leader": frappe.session.user, "status": "Approved"})
		stats["pending_tasks"] = stats["total_projects"] - stats["completed_projects"]
	elif "Team Update Team Member" in roles:
		stats["total_projects"] = frappe.db.count(project_doctype, {"assigned_to": frappe.session.user})
		stats["completed_projects"] = frappe.db.count(project_doctype, {"assigned_to": frappe.session.user, "status": "Approved"})
		stats["pending_tasks"] = stats["total_projects"] - stats["completed_projects"]
	elif "Team Update Viewer" in roles:
		stats["total_projects"] = frappe.db.count(project_doctype, {"status": "Approved"})
		stats["completed_projects"] = stats["total_projects"]

	# Count teams
	stats["active_teams"] = frappe.db.count(team_doctype, {"is_active": 1})

	# Count team members
	total = frappe.db.sql("SELECT COUNT(DISTINCT user) FROM `tabTeam Member`")
	stats["total_members"] = total[0][0] if total else 0

	return stats


def get_recent_projects(roles):
	"""Get recent projects based on user role."""
	filters = {}
	if "Team Update Team Leader" in roles:
		filters["assigned_team_leader"] = frappe.session.user
	elif "Team Update Team Member" in roles:
		filters["assigned_to"] = frappe.session.user
	elif "Team Update Viewer" in roles:
		filters["status"] = "Approved"

	return frappe.get_all(
		"Team Project Update",
		filters=filters,
		fields=["name", "project_title", "team", "status", "priority", "progress_percent", "modified", "assigned_team_leader", "assigned_to"],
		order_by="modified desc",
		limit=10,
	)


def get_recent_notifications():
	"""Get recent notifications for the current user."""
	return frappe.get_all(
		"Notification Log",
		filters={"for_user": frappe.session.user},
		fields=["subject", "creation", "document_type", "document_name"],
		order_by="creation desc",
		limit=5,
	)
