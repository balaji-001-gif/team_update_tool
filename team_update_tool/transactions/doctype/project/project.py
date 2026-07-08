# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Project(Document):
	def validate(self):
		self.validate_role_permissions()
		self.validate_duplicate_project()

	def validate_role_permissions(self):
		roles = frappe.get_roles(frappe.session.user)
		if "View-Only User" in roles and "Admin" not in roles and "System Manager" not in roles:
			if not self.is_new():
				frappe.throw(_("View-Only Users cannot edit projects."), frappe.PermissionError)

	def validate_duplicate_project(self):
		if self.project_title:
			filters = {"project_title": self.project_title}
			if not self.is_new():
				filters["name"] = ["!=", self.name]
			if frappe.db.exists("Project", filters):
				frappe.throw(_("A project with this title already exists. Duplicate project titles are not allowed."))

	def on_trash(self):
		roles = frappe.get_roles(frappe.session.user)
		if "Admin" not in roles and "System Manager" not in roles:
			frappe.throw(_("Only Admin can delete projects."), frappe.PermissionError)


def validate_project(doc, method=None):
	"""Hook for doc_events in hooks.py."""
	# This is called via the doc_events hook in addition to the validate method
	pass


def get_permission_query_conditions(user):
	"""Server-enforced list view filtering. View-Only Users see only projects with status 'Approved'."""
	if not user:
		return ""
	roles = frappe.get_roles(user)
	if "View-Only User" in roles and "Admin" not in roles:
		approved_status = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
		if approved_status:
			return "`tabProject`.`status` = " + frappe.db.escape(approved_status)
	return ""


def has_permission(doc, ptype, user):
	"""Doc-level permission check."""
	if ptype == "read":
		roles = frappe.get_roles(user)
		if "View-Only User" in roles and "Admin" not in roles:
			approved_status = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
			if approved_status and doc.status != approved_status:
				return False
	return True
