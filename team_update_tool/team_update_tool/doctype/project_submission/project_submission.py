# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ProjectSubmission(Document):
	def validate(self):
		self.validate_role_permissions()
		if not self.submitted_by:
			self.submitted_by = frappe.session.user
		self.set_reviewed_by()
		self.set_approved_by()

	def validate_role_permissions(self):
		"""Server-side permission enforcement.
		Project Viewer cannot write. Project Contributor can only edit own submissions.
		"""
		roles = frappe.get_roles(frappe.session.user)
		is_admin = "Project Admin" in roles or "System Manager" in roles
		is_contributor = "Project Contributor" in roles
		is_viewer_only = "Project Viewer" in roles and not is_admin and not is_contributor

		# Viewer cannot write
		if is_viewer_only:
			frappe.throw(
				_("Viewers cannot create or edit submissions."),
				frappe.PermissionError,
			)

		# Contributor can only edit their own submissions
		if is_contributor and not is_admin and not self.is_new():
			if self.submitted_by != frappe.session.user:
				frappe.throw(
					_("You can only edit your own submissions."),
					frappe.PermissionError,
				)
			# Cannot change approval fields
			if self.has_value_changed("approved_by") or self.has_value_changed("reviewed_by"):
				frappe.throw(
					_("You cannot modify approval fields."),
					frappe.PermissionError,
				)

	def on_trash(self):
		"""Only Admin can delete submissions."""
		roles = frappe.get_roles(frappe.session.user)
		if "Project Admin" not in roles and "System Manager" not in roles:
			frappe.throw(
				_("Only Project Admin can delete submissions."),
				frappe.PermissionError,
			)

	def set_reviewed_by(self):
		if self.status == "Under Review" and not self.reviewed_by:
			self.reviewed_by = frappe.session.user

	def set_approved_by(self):
		if self.status == "Approved":
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approval_date:
				self.approval_date = frappe.utils.today()


# Permission query conditions for list view filtering
def get_permission_query_conditions(user):
	"""Server-enforced list view filtering per role.
	Viewers: only see Approved submissions.
	Contributors: only see their own submissions.
	"""
	if not user:
		return ""

	user_doc = frappe.get_doc("User", user)
	roles = [r.role for r in user_doc.roles]

	if "System Manager" in roles or "Project Admin" in roles:
		return ""

	conditions = []

	if "Project Viewer" in roles:
		conditions.append("`tabProject Submission`.`status` = 'Approved'")
		return "(" + " OR ".join(conditions) + ")"

	if "Project Contributor" in roles:
		conditions.append(
			"`tabProject Submission`.`submitted_by` = " + frappe.db.escape(user)
		)
		return "(" + " OR ".join(conditions) + ")"

	return ""


def has_permission(doc, ptype, user):
	"""Doc-level permission check for read operations."""
	if ptype == "read":
		roles = frappe.get_roles(user)
		if "Project Viewer" in roles and "Project Admin" not in roles and "Project Contributor" not in roles:
			return doc.status == "Approved"
	return True


# GitHub metadata auto-fetch (hooked via doc_events in hooks.py)
def fetch_github_metadata_on_validate(doc, method=None):
	"""Auto-fetch GitHub repo metadata when github_repo_url is provided."""
	if not doc.github_repo_url:
		return

	import re
	match = re.search(r"github\.com/([^/]+)/([^/]+)", doc.github_repo_url)
	if not match:
		return

	owner, repo_name = match.group(1), match.group(2).rstrip("/").replace(".git", "")

	try:
		import requests
		api = f"https://api.github.com/repos/{owner}/{repo_name}"
		headers = {}
		token = frappe.conf.get("github_api_token")
		if token:
			headers["Authorization"] = f"Bearer {token}"

		# Get default branch info
		repo_data = requests.get(api, headers=headers, timeout=10).json()
		default_branch = repo_data.get("default_branch", "main")

		# Get commit SHA from default branch
		branch_data = requests.get(
			f"{api}/branches/{default_branch}", headers=headers, timeout=10
		).json()
		doc.github_commit_hash = branch_data.get("commit", {}).get("sha", "")

		# Get languages
		langs = requests.get(f"{api}/languages", headers=headers, timeout=10).json()
		sorted_langs = sorted(langs.keys(), key=lambda k: langs[k], reverse=True)[:5]
		doc.github_languages = ", ".join(sorted_langs)

		doc.repo_metadata_last_fetched = frappe.utils.now()
	except Exception as e:
		frappe.log_error(f"GitHub API fetch error: {str(e)}", "GitHub Metadata")
