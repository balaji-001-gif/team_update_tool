# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TeamProjectUpdate(Document):
	def validate(self):
		self.validate_role_permissions()
		self.validate_github_url()
		self.set_reviewed_by()
		self.set_approved_by()
		self.handle_assignment_events()

	def before_insert(self):
		if not self.project_owner:
			self.project_owner = frappe.session.user

	# ───────────────────────── Role-Based Permission Guards ─────────────────────────

	def validate_role_permissions(self):
		"""Validate that the current user's role permits the action being taken."""
		roles = frappe.get_roles(frappe.session.user)
		is_admin = "Team Update Admin" in roles or "System Manager" in roles
		is_team_leader = "Team Update Team Leader" in roles
		is_team_member = "Team Update Team Member" in roles
		is_viewer_only = "Team Update Viewer" in roles and not is_admin

		# Viewer cannot do anything
		if is_viewer_only:
			frappe.throw(
				_("You have View Only access to Team Update Tool. You are not permitted to create, edit or delete project updates."),
				frappe.PermissionError,
			)

		# Team Member restrictions
		if is_team_member and not is_admin and not is_team_leader:
			if self.is_new():
				# Team members can only create tasks assigned to them
				pass
			else:
				# Can only modify their own assigned tasks
				if self.assigned_to != frappe.session.user:
					frappe.throw(
						_("You can only update tasks assigned to you."),
						frappe.PermissionError,
					)
				# Cannot change assignment fields
				if self.has_value_changed("assigned_team_leader") or self.has_value_changed("assigned_to"):
					frappe.throw(
						_("Team Members cannot change task assignments."),
						frappe.PermissionError,
					)
				# Cannot change review/approval fields
				if self.has_value_changed("team_leader_review_status") or self.has_value_changed("approved_by"):
					frappe.throw(
						_("Team Members cannot modify review or approval fields."),
						frappe.PermissionError,
					)

		# Team Leader restrictions
		if is_team_leader and not is_admin:
			if not self.is_new():
				# Can only modify their own team's tasks
				if self.assigned_team_leader != frappe.session.user:
					frappe.throw(
						_("You can only update tasks assigned to you as Team Leader."),
						frappe.PermissionError,
					)
				# Cannot delete
				# Cannot modify admin-level fields
				if self.has_value_changed("approved_by") or self.has_value_changed("approval_date"):
					frappe.throw(
						_("Team Leaders cannot modify approval fields."),
						frappe.PermissionError,
					)

	def on_trash(self):
		roles = frappe.get_roles(frappe.session.user)
		if "Team Update Admin" not in roles and "System Manager" not in roles:
			frappe.throw(
				_("Only Team Update Admin can delete project updates."), frappe.PermissionError
			)

	# ───────────────────────── Assignment Event Handlers ─────────────────────────

	def handle_assignment_events(self):
		"""Detect assignment changes and trigger notifications."""
		if self.is_new():
			return

		if self.has_value_changed("assigned_team_leader") and self.assigned_team_leader:
			self.assigned_by_admin = 1
			if self.status == "Draft":
				self.status = "Assigned"
			notify_task_assigned(
				doc=self,
				assigned_user=self.assigned_team_leader,
				role="Team Leader",
				assigned_by=frappe.session.user,
			)

		if self.has_value_changed("assigned_to") and self.assigned_to:
			self.assigned_by_team_leader = 1
			if self.status == "Assigned":
				self.status = "In Progress"
			notify_task_assigned(
				doc=self,
				assigned_user=self.assigned_to,
				role="Team Member",
				assigned_by=frappe.session.user,
			)

	# ───────────────────────── Auto-Set Fields ─────────────────────────

	def validate_github_url(self):
		if self.github_repo_url and "github.com" not in self.github_repo_url.lower():
			frappe.msgprint(
				_("The link entered does not look like a GitHub URL. Please double check it."),
				alert=True,
				indicator="orange",
			)

	def set_reviewed_by(self):
		if self.team_leader_review_status == "Reviewed" and not self.team_leader_review_date:
			self.team_leader_review_date = frappe.utils.today()

	def set_approved_by(self):
		if self.status == "Approved":
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approval_date:
				self.approval_date = frappe.utils.today()


# ───────────────────────── Permission Query Conditions ─────────────────────────

def get_permission_query_conditions(user):
	"""Return SQL conditions so each role sees only their permitted records."""
	if not user:
		return ""

	user_doc = frappe.get_doc("User", user)
	roles = [r.role for r in user_doc.roles]

	if "System Manager" in roles or "Team Update Admin" in roles:
		return ""

	conditions = []

	if "Team Update Team Leader" in roles:
		conditions.append(f"`tabTeam Project Update`.`assigned_team_leader` = {frappe.db.escape(user)}")

	if "Team Update Team Member" in roles:
		if "Team Update Team Leader" in roles:
			conditions.append(f"`tabTeam Project Update`.`assigned_to` = {frappe.db.escape(user)}")
		else:
			conditions.append(f"`tabTeam Project Update`.`assigned_to` = {frappe.db.escape(user)}")

	if "Team Update Viewer" in roles:
		conditions.append(f"`tabTeam Project Update`.`status` = 'Approved'")

	if conditions:
		return "(" + " OR ".join(conditions) + ")"
	return ""


# ───────────────────────── Notification Functions ─────────────────────────

def after_insert_handler(doc, method=None):
	"""Handles after_insert events. Notifies about new task creation."""
	if doc.assigned_team_leader:
		notify_task_assigned(
			doc=doc,
			assigned_user=doc.assigned_team_leader,
			role="Team Leader",
			assigned_by=doc.project_owner,
		)


def on_update_handler(doc, method=None):
	"""Handles on_update events - status changes, completions, approvals."""
	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	# Task completed by team member
	if doc.status == "Completed" and old_doc.status != "Completed":
		notify_task_completed(doc)
		# Auto-set review status
		if doc.team_leader_review_status == "Pending Review":
			doc.db_set("team_leader_review_status", "Pending Review")

	# Status changed to Under Review (Team Leader reviewing)
	if doc.status == "Under Review" and old_doc.status != "Under Review":
		notify_under_review(doc)

	# Team Leader reviewed
	if doc.team_leader_review_status == "Reviewed" and old_doc.team_leader_review_status != "Reviewed":
		notify_review_completed(doc)

	# Admin approved
	if doc.status == "Approved" and old_doc.status != "Approved":
		notify_task_approved(doc)

	# Task rejected
	if doc.status == "Rejected" and old_doc.status != "Rejected":
		notify_task_rejected(doc)

	# Progress updated
	if doc.has_value_changed("progress_percent") and doc.progress_percent > old_doc.progress_percent:
		notify_progress_update(doc)


def notify_task_assigned(doc, assigned_user, role, assigned_by):
	"""Send notification when a task is assigned to a user."""
	if not assigned_user or assigned_user == frappe.session.user:
		return

	subject = f"New Task Assigned: {doc.project_title}"
	message = (
		f"<p>A new task has been assigned to you as <b>{role}</b>.</p>"
		f"<p><b>Project:</b> {doc.project_title}<br>"
		f"<b>Team:</b> {doc.team}<br>"
		f"<b>Assigned by:</b> {frappe.utils.get_fullname(assigned_by)}<br>"
		f"<b>Status:</b> {doc.status}<br>"
		f"<b>Priority:</b> {doc.priority}</p>"
	)

	_create_notification_log(doc, assigned_user, subject, message)


def notify_task_completed(doc):
	"""Notify Team Leader and Admin when a task is completed by the team member."""
	subject = f"Task Completed: {doc.project_title}"
	message = (
		f"<p>The task <b>{doc.project_title}</b> has been marked as <b>Completed</b> by "
		f"{frappe.utils.get_fullname(frappe.session.user)}.</p>"
		f"<p><b>Team:</b> {doc.team}<br>"
		f"<b>GitHub:</b> {doc.github_repo_url or '-'}</p>"
		f"<p>Please review and provide feedback.</p>"
	)

	# Notify Team Leader
	if doc.assigned_team_leader and doc.assigned_team_leader != frappe.session.user:
		_create_notification_log(doc, doc.assigned_team_leader, subject, message)

	# Notify Admin
	notify_admins(doc, subject, message)


def notify_under_review(doc):
	"""Notify Admin that Team Leader is reviewing."""
	subject = f"Task Under Review: {doc.project_title}"
	message = (
		f"<p>The task <b>{doc.project_title}</b> is now under review by "
		f"{frappe.utils.get_fullname(frappe.session.user)} (Team Leader).</p>"
	)
	notify_admins(doc, subject, message)


def notify_review_completed(doc):
	"""Notify Admin that Team Leader has completed the review."""
	subject = f"Task Reviewed: {doc.project_title}"
	message = (
		f"<p>The task <b>{doc.project_title}</b> has been reviewed by "
		f"{frappe.utils.get_fullname(frappe.session.user)} (Team Leader).</p>"
		f"<p><b>Review:</b> {doc.team_leader_review_remarks or 'No remarks'}</p>"
		f"<p>Please review and provide final approval.</p>"
	)
	notify_admins(doc, subject, message)


def notify_task_approved(doc):
	"""Notify Team Leader and Team Member that the task has been approved."""
	subject = f"Task Approved: {doc.project_title}"
	message = (
		f"<p>The task <b>{doc.project_title}</b> has been <b>Approved</b> by "
		f"{frappe.utils.get_fullname(frappe.session.user)}.</p>"
		f"<p><b>Team:</b> {doc.team}<br>"
		f"<b>GitHub:</b> {doc.github_repo_url or '-'}</p>"
	)

	# Notify Team Leader
	if doc.assigned_team_leader:
		_create_notification_log(doc, doc.assigned_team_leader, subject, message)

	# Notify Team Member
	if doc.assigned_to:
		_create_notification_log(doc, doc.assigned_to, subject, message)


def notify_task_rejected(doc):
	"""Notify Team Leader and Team Member that the task was rejected."""
	subject = f"Task Rejected: {doc.project_title}"
	message = (
		f"<p>The task <b>{doc.project_title}</b> has been <b>Rejected</b>.</p>"
		f"<p><b>Remarks:</b> {doc.review_remarks or 'No remarks provided'}</p>"
	)

	# Notify Team Leader
	if doc.assigned_team_leader:
		_create_notification_log(doc, doc.assigned_team_leader, subject, message)

	# Notify Team Member
	if doc.assigned_to:
		_create_notification_log(doc, doc.assigned_to, subject, message)


def notify_progress_update(doc):
	"""Notify Team Leader when a Team Member updates progress."""
	if not doc.assigned_team_leader or doc.assigned_team_leader == frappe.session.user:
		return

	subject = f"Progress Update: {doc.project_title}"
	message = (
		f"<p><b>{frappe.utils.get_fullname(frappe.session.user)}</b> updated the progress on "
		f"<b>{doc.project_title}</b> to <b>{doc.progress_percent}%</b>.</p>"
	)
	_create_notification_log(doc, doc.assigned_team_leader, subject, message)


# ───────────────────────── Helper Functions ─────────────────────────

def _create_notification_log(doc, for_user, subject, message):
	"""Create an in-app Notification Log entry."""
	if not for_user or for_user == frappe.session.user:
		return

	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"subject": subject,
			"for_user": for_user,
			"type": "Alert",
			"document_type": doc.doctype,
			"document_name": doc.name,
			"from_user": frappe.session.user,
		}
	).insert(ignore_permissions=True)

	# Send email if enabled
	try:
		settings = frappe.get_single("Team Update Settings")
		if settings.enable_email_notification:
			email = frappe.db.get_value("User", for_user, "email")
			if email:
				frappe.sendmail(recipients=email, subject=subject, message=message)
	except Exception:
		pass


def notify_admins(doc, subject, message):
	"""Send notification to all users with Team Update Admin role."""
	admin_users = frappe.get_all(
		"Has Role",
		filters={"role": "Team Update Admin", "parenttype": "User"},
		pluck="parent",
	)
	for user in admin_users:
		_create_notification_log(doc, user, subject, message)
