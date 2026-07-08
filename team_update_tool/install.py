# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def after_install():
	"""Runs once when the app is installed on a site.
	Creates three roles: Project Admin, Project Contributor, Project Viewer.
	"""
	create_roles()
	create_default_settings()
	frappe.db.commit()


def create_roles():
	roles = [
		{
			"role_name": "Project Admin",
			"desk_access": 1,
			"description": "Full CRUD access on all Team Update Tool DocTypes. Can approve/reject submissions and manage teams.",
		},
		{
			"role_name": "Project Contributor",
			"desk_access": 1,
			"description": "Can create submissions, upload files, edit own records. Read-only on Teams.",
		},
		{
			"role_name": "Project Viewer",
			"desk_access": 1,
			"description": "Strict read-only access. Can only see Approved submissions. Enforced server-side.",
		},
	]

	for role in roles:
		if not frappe.db.exists("Role", role["role_name"]):
			doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": role["role_name"],
				"desk_access": role["desk_access"],
				"description": role["description"],
			})
			doc.insert(ignore_permissions=True)


def create_default_settings():
	if not frappe.db.exists("DocType", "Team Update Settings"):
		return
	if not frappe.db.exists("Team Update Settings", "Team Update Settings"):
		return
	settings = frappe.get_single("Team Update Settings")
	if not settings.enable_email_notification:
		settings.enable_email_notification = 1
		settings.save(ignore_permissions=True)
