# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_months


@frappe.whitelist()
def get_stats():
	"""Returns dashboard statistics for the SPA frontend."""
	total_projects = frappe.db.count("Team Project Update")
	completed = frappe.db.count("Team Project Update", {"status": "Approved"})
	in_progress = frappe.db.count("Team Project Update", {"status": "In Progress"})
	assigned = frappe.db.count("Team Project Update", {"status": "Assigned"})
	draft = frappe.db.count("Team Project Update", {"status": "Draft"})
	pending_review = frappe.db.count(
		"Team Project Update", {"status": ["in", ["Under Review", "Completed"]]}
	)
	rejected = frappe.db.count("Team Project Update", {"status": "Rejected"})
	total_teams = frappe.db.count("Team")
	active_teams = frappe.db.count("Team", {"is_active": 1})

	return {
		"total_projects": total_projects,
		"completed": completed,
		"in_progress": in_progress,
		"assigned": assigned,
		"draft": draft,
		"pending_review": pending_review,
		"rejected": rejected,
		"total_teams": total_teams,
		"active_teams": active_teams,
	}


@frappe.whitelist()
def get_chart_data():
	"""Returns chart data for the SPA dashboard."""
	# Project Status Distribution
	status_counts = frappe.db.sql(
		"""SELECT status, COUNT(*) as count
		FROM `tabTeam Project Update` GROUP BY status ORDER BY count DESC""",
		as_dict=1,
	)

	# Monthly Completed
	six_months_ago = add_months(today(), -6)
	monthly_completed = frappe.db.sql(
		"""SELECT DATE_FORMAT(COALESCE(completion_date, modified), '%%Y-%%m') as month,
			COUNT(*) as count
		FROM `tabTeam Project Update`
		WHERE status = 'Approved' AND COALESCE(completion_date, modified) >= %s
		GROUP BY month ORDER BY month ASC""",
		(six_months_ago,),
		as_dict=1,
	)

	# Team Performance
	team_performance = frappe.db.sql(
		"""SELECT team, COUNT(*) as count
		FROM `tabTeam Project Update` GROUP BY team ORDER BY count DESC LIMIT 10""",
		as_dict=1,
	)

	return {
		"status_counts": status_counts,
		"monthly_completed": monthly_completed,
		"team_performance": team_performance,
	}


@frappe.whitelist()
def get_recent_activity():
	"""Returns recent projects, notifications, and GitHub uploads."""
	recent_projects = frappe.get_all(
		"Team Project Update",
		fields=["name", "project_title", "status", "team", "progress_percent", "modified"],
		order_by="modified desc",
		limit=10,
	)

	notifications = frappe.get_all(
		"Notification Log",
		fields=["name", "subject", "creation", "document_name"],
		filters={"for_user": frappe.session.user},
		order_by="creation desc",
		limit=10,
	)

	github_projects = frappe.get_all(
		"Team Project Update",
		fields=["name", "project_title", "github_repo_url", "team", "modified"],
		filters={"github_repo_url": ["!=", ""]},
		order_by="modified desc",
		limit=8,
	)

	return {
		"recent_projects": recent_projects,
		"notifications": notifications,
		"github_projects": github_projects,
	}


@frappe.whitelist()
def get_user_info():
	"""Returns current user information."""
	user = frappe.session.user
	user_info = frappe.get_value("User", user, ["full_name", "email", "user_image"], as_dict=1)
	roles = frappe.get_roles(user)
	return {
		"name": user,
		"full_name": user_info.full_name if user_info else user,
		"email": user_info.email if user_info else "",
		"user_image": user_info.user_image if user_info else "",
		"roles": [r for r in roles if r not in ("All", "Guest", "System Manager")],
	}
