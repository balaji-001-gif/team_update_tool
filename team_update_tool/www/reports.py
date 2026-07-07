# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	"""Build the reports page context."""
	context.no_sidebar = 1
	context.no_cache = 1
	context.title = "Reports - Team Update Tool"

	context.reports = [
		{
			"name": "Project Status Summary",
			"title": "Project Status Summary",
			"description": "View detailed task status, assignments, and progress for all projects.",
			"route": "/desk#query-report/Project%20Status%20Summary",
		},
	]

	# Add dashboard stats
	roles = frappe.get_roles(frappe.session.user)
	project_doctype = "Team Project Update"

	if "Team Update Admin" in roles or "System Manager" in roles:
		context.stats = {
			"total": frappe.db.count(project_doctype),
			"draft": frappe.db.count(project_doctype, {"status": "Draft"}),
			"assigned": frappe.db.count(project_doctype, {"status": "Assigned"}),
			"in_progress": frappe.db.count(project_doctype, {"status": "In Progress"}),
			"completed": frappe.db.count(project_doctype, {"status": "Completed"}),
			"under_review": frappe.db.count(project_doctype, {"status": "Under Review"}),
			"approved": frappe.db.count(project_doctype, {"status": "Approved"}),
			"rejected": frappe.db.count(project_doctype, {"status": "Rejected"}),
		}
	elif "Team Update Team Leader" in roles:
		f = {"assigned_team_leader": frappe.session.user}
		context.stats = {
			"total": frappe.db.count(project_doctype, f),
			"draft": frappe.db.count(project_doctype, {**f, "status": "Draft"}),
			"in_progress": frappe.db.count(project_doctype, {**f, "status": "In Progress"}),
			"completed": frappe.db.count(project_doctype, {**f, "status": "Completed"}),
			"approved": frappe.db.count(project_doctype, {**f, "status": "Approved"}),
		}
	elif "Team Update Team Member" in roles:
		f = {"assigned_to": frappe.session.user}
		context.stats = {
			"total": frappe.db.count(project_doctype, f),
			"in_progress": frappe.db.count(project_doctype, {**f, "status": "In Progress"}),
			"completed": frappe.db.count(project_doctype, {**f, "status": "Completed"}),
			"approved": frappe.db.count(project_doctype, {**f, "status": "Approved"}),
		}
	elif "Team Update Viewer" in roles:
		context.stats = {
			"approved": frappe.db.count(project_doctype, {"status": "Approved"}),
		}
