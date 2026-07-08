# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_months


@frappe.whitelist()
def get_dashboard_data():
	"""Returns all dashboard data: stats, charts, recent projects, teams, GitHub repos."""
	user = frappe.session.user

	# Stats
	total_projects = frappe.db.count("Project Submission")
	completed = frappe.db.count("Project Submission", {"status": "Approved"})
	under_review = frappe.db.count("Project Submission", {"status": "Under Review"})
	submitted = frappe.db.count("Project Submission", {"status": "Submitted"})
	rejected = frappe.db.count("Project Submission", {"status": "Rejected"})
	total_teams = frappe.db.count("Team")
	active_teams = frappe.db.count("Team", {"is_active": 1})

	team_leaders = frappe.db.sql(
		"SELECT COUNT(DISTINCT team_lead) FROM `tabTeam` WHERE team_lead IS NOT NULL AND team_lead != ''"
	)[0][0] or 0

	team_members = frappe.db.count("Team Member")

	# Chart: Status Distribution
	status_counts = frappe.db.sql(
		"SELECT status, COUNT(*) as count FROM `tabProject Submission` GROUP BY status ORDER BY count DESC",
		as_dict=1,
	)

	# Chart: Monthly Completed (last 6 months)
	six_months_ago = add_months(today(), -6)
	monthly_completed = frappe.db.sql(
		"""SELECT DATE_FORMAT(COALESCE(completion_date, modified), '%%Y-%%m') as month,
			COUNT(*) as count
		FROM `tabProject Submission`
		WHERE status = 'Approved' AND COALESCE(completion_date, modified) >= %s
		GROUP BY month ORDER BY month ASC""",
		(six_months_ago,),
		as_dict=1,
	)

	# Chart: Team Performance
	team_performance = frappe.db.sql(
		"SELECT team, COUNT(*) as count FROM `tabProject Submission` GROUP BY team ORDER BY count DESC LIMIT 10",
		as_dict=1,
	)

	# Chart: Progress Distribution
	progress_ranges = frappe.db.sql(
		"""SELECT
			CASE
				WHEN progress_percent = 0 THEN 'Not Started'
				WHEN progress_percent <= 25 THEN '0-25%%'
				WHEN progress_percent <= 50 THEN '26-50%%'
				WHEN progress_percent <= 75 THEN '51-75%%'
				WHEN progress_percent < 100 THEN '76-99%%'
				WHEN progress_percent = 100 THEN '100%%'
			END as `range`,
			COUNT(*) as count
		FROM `tabProject Submission`
		GROUP BY `range`
		ORDER BY FIELD(`range`, 'Not Started', '0-25%%', '26-50%%', '51-75%%', '76-99%%', '100%%')""",
		as_dict=1,
	)

	# Recent Projects (last 15)
	recent_projects = frappe.get_all(
		"Project Submission",
		fields=["name", "project_title", "status", "team", "submitted_by", "priority", "progress_percent", "modified"],
		order_by="modified desc",
		limit=15,
	)

	# Teams with project and member counts
	teams = frappe.get_all("Team", fields=["name", "team_name", "team_lead", "team_type", "is_active"])
	teams_data = []
	for t in teams:
		project_count = frappe.db.count("Project Submission", {"team": t.name})
		member_count = frappe.db.count("Team Member", {"parent": t.name})
		teams_data.append({
			"name": t.name,
			"team_name": t.team_name,
			"team_lead": t.team_lead,
			"team_type": t.team_type,
			"is_active": t.is_active,
			"project_count": project_count,
			"member_count": member_count,
		})

	# GitHub-linked projects
	github_projects = frappe.get_all(
		"Project Submission",
		fields=["name", "project_title", "github_repo_url", "github_commit_hash", "github_languages", "team", "modified"],
		filters={"github_repo_url": ["!=", ""]},
		order_by="modified desc",
		limit=8,
	)

	# Recent Notifications
	notifications = frappe.get_all(
		"Notification Log",
		fields=["name", "subject", "creation", "document_name", "type"],
		filters={"for_user": user},
		order_by="creation desc",
		limit=10,
	)

	# User Info
	user_info = frappe.get_value("User", user, ["full_name", "email", "user_image"], as_dict=1)
	roles = frappe.get_roles(user)

	return {
		"stats": {
			"total_projects": total_projects,
			"completed": completed,
			"under_review": under_review,
			"submitted": submitted,
			"rejected": rejected,
			"total_teams": total_teams,
			"active_teams": active_teams,
			"team_leaders": team_leaders,
			"team_members": team_members,
		},
		"charts": {
			"status_counts": status_counts,
			"monthly_completed": monthly_completed,
			"team_performance": team_performance,
			"progress_ranges": progress_ranges,
		},
		"recent_projects": recent_projects,
		"teams": teams_data,
		"github_projects": github_projects,
		"notifications": notifications,
		"user": {
			"name": user,
			"full_name": user_info.full_name if user_info else user,
			"email": user_info.email if user_info else "",
			"user_image": user_info.user_image if user_info else "",
			"roles": [r for r in roles if r not in ("All", "Guest", "System Manager")],
		},
	}


@frappe.whitelist()
def get_stats():
	"""Returns dashboard statistics only."""
	total_projects = frappe.db.count("Project Submission")
	completed = frappe.db.count("Project Submission", {"status": "Approved"})
	under_review = frappe.db.count("Project Submission", {"status": "Under Review"})
	submitted = frappe.db.count("Project Submission", {"status": "Submitted"})
	rejected = frappe.db.count("Project Submission", {"status": "Rejected"})
	total_teams = frappe.db.count("Team")
	active_teams = frappe.db.count("Team", {"is_active": 1})

	return {
		"total_projects": total_projects,
		"completed": completed,
		"under_review": under_review,
		"submitted": submitted,
		"rejected": rejected,
		"total_teams": total_teams,
		"active_teams": active_teams,
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
