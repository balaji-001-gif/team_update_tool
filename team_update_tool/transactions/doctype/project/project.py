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


def on_project_update(doc, method=None):
	"""Hook called on project update to handle notifications."""
	pass


def send_new_project_notification(doc, method=None):
	"""Send email notification to admin when a new project is created."""
	try:
		# Get all admin users
		admin_users = frappe.get_all("Has Role",
			filters={"role": "Admin"},
			pluck="parent"
		)
		
		if not admin_users:
			# Fallback to System Manager if no Admin users
			admin_users = frappe.get_all("Has Role",
				filters={"role": "System Manager"},
				pluck="parent"
			)
		
		if not admin_users:
			frappe.log_error("No Admin or System Manager users found for notification", "Project Notification Error")
			return
		
		# Get project details
		status_name = ""
		if doc.status:
			status_doc = frappe.get_cached_doc("Project Status", doc.status)
			status_name = status_doc.status_name if hasattr(status_doc, 'status_name') else doc.status
		
		# Get team name
		team_name = doc.team
		if doc.team:
			team_doc = frappe.get_cached_doc("Team", doc.team)
			team_name = team_doc.team_name if hasattr(team_doc, 'team_name') else doc.team
		
		# Prepare notification message
		subject = f"New Project Uploaded: {doc.project_title}"
		message = f"""
<p>A new project has been uploaded:</p>
<p><b>{doc.project_title}</b><br>
Team: {team_name}<br>
Status: {status_name}<br>
Priority: {doc.priority or 'Medium'}<br>
Created by: {doc.owner}</p>
<p><a href="{frappe.utils.get_url(f'/app/project/{doc.name}')}">View Project</a></p>
"""
		
		# Send email to all admin users
		for user in admin_users:
			user_email = frappe.db.get_value("User", user, "email")
			if user_email:
				try:
					frappe.sendmail(
						recipients=[user_email],
						subject=subject,
						message=message,
						reference_doctype="Project",
						reference_name=doc.name,
					)
					frappe.log_error(f"Notification sent to {user_email} for project {doc.name}", "Project Notification")
				except Exception as email_error:
					frappe.log_error(f"Failed to send notification to {user_email}: {str(email_error)}", "Project Notification Error")
		
		# Create system notification - simplified approach
		try:
			for user in admin_users:
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": subject[:140] if len(subject) > 140 else subject,
					"email_content": message,
					"for_user": user,
					"type": "Alert",
					"document_type": "Project",
					"document_name": doc.name,
				                            }).insert(ignore_permissions=True, ignore_links=True)
		except Exception as notification_error:
			frappe.log_error(f"Failed to create system notification", "Project Notification Error")
		
	except Exception as e:
		frappe.log_error(f"Error sending new project notification", "Project Notification Error")


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
