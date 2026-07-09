# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def signup(email, first_name, last_name=None, password=None):
	"""Self-registration for new Team Members."""
	if not email or not first_name:
		frappe.throw(_("Email and First Name are required."))

	if frappe.db.exists("User", email):
		frappe.throw(_("A user with this email already exists."))

	if not password:
		import secrets
		password = secrets.token_urlsafe(12)

	user = frappe.get_doc({
		"doctype": "User",
		"email": email,
		"first_name": first_name,
		"last_name": last_name or "",
		"send_welcome_email": 1,
		"enabled": 1,
		"roles": [
			{"role": "Team Member"}
		],
		"user_type": "Website User",
	})
	user.insert(ignore_permissions=True)

	return {
		"message": _("Account created successfully. Please check your email for login details."),
		"user": user.name,
	}


@frappe.whitelist()
def get_current_user():
	"""Get current logged-in user details."""
	user = frappe.session.user
	if user == "Guest":
		return {"guest": True}

	roles = frappe.get_roles(user)
	is_admin = "Admin" in roles or "System Manager" in roles
	is_team_member = "Team Member" in roles and not is_admin
	is_viewer = "View-Only User" in roles and not is_admin and not is_team_member

	return {
		"guest": False,
		"user": user,
		"full_name": frappe.utils.get_fullname(user),
		"is_admin": is_admin,
		"is_team_member": is_team_member,
		"is_viewer": is_viewer,
		"roles": roles,
	}
