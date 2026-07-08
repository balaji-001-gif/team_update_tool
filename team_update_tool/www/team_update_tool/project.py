# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.no_header = 1
	context.no_breadcrumbs = 1
	context.title = _("Project Details")

	project_name = frappe.form_dict.get("name")
	if not project_name:
		frappe.local.flags.redirect_location = "/team_update_tool/projects"
		raise frappe.Redirect

	try:
		project = frappe.get_doc("Project", project_name)
	except frappe.DoesNotExistError:
		context.page_error = "Project not found"
		return

	# Permission check
	user = frappe.session.user
	roles = frappe.get_roles(user)
	is_viewer = "View-Only User" in roles and "Admin" not in roles and "System Manager" not in roles
	if is_viewer:
		approved = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
		if not approved or project.status != approved:
			context.page_error = "You do not have permission to view this project."
			return

	context.project = project
	context.is_logged_in = user != "Guest"
	context.is_viewer = is_viewer
	context.is_owner = project.owner == user

	# Status info
	if project.status:
		s = frappe.get_cached_doc("Project Status", project.status)
		context.status_name = s.status_name
		context.status_color = s.color

	# Get screenshots with full URLs
	context.screenshots = []
	for s in project.screenshots or []:
		context.screenshots.append({
			"screenshot": s.screenshot,
			"caption": s.caption,
			"screenshot_type": s.screenshot_type,
		})

	# Files
	context.files_list = []
	for f in project.project_files or []:
		context.files_list.append({
			"file": f.file,
			"file_name": f.file_name,
			"file_type": f.file_type,
			"description": f.file_description,
		})

	# Updates
	context.updates = []
	for u in project.project_updates or []:
		context.updates.append({
			"name": u.name,
			"update_title": u.update_title,
			"update_description": u.update_description,
			"update_date": u.update_date,
			"updated_by": u.updated_by,
		})

	# Technologies
	context.technologies = [t.technology for t in project.technologies or []]

	# GitHub repo info
	if project.github_repository:
		try:
			repo = frappe.get_cached_doc("GitHub Repository", project.github_repository)
			context.github_repo = repo
		except frappe.DoesNotExistError:
			context.github_repo = None
