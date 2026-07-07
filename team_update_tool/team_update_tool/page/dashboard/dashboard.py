# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, add_days, add_months, getdate


@frappe.whitelist()
def get_dashboard_data():
	"""Returns all dashboard data for charts and stats."""
	roles = frappe.get_roles(frappe.session.user)
	filters = get_role_filters(roles)

	data = {
		"stats": get_stats(filters, roles),
		"status_chart": get_status_chart_data(filters),
		"monthly_chart": get_monthly_chart_data(filters),
		"team_performance": get_team_performance(),
		"recent_activities": get_recent_activities(filters),
		"notifications": get_recent_notifications(),
	}
	return data


def get_role_filters(roles):
	"""Get filters based on user role."""
	if "Team Update Admin" in roles or "System Manager" in roles:
		return {}
	elif "Team Update Team Leader" in roles:
		return {"assigned_team_leader": frappe.session.user}
	elif "Team Update Team Member" in roles:
		return {"assigned_to": frappe.session.user}
	elif "Team Update Viewer" in roles:
		return {"status": "Approved"}
	return {}


def get_stats(filters, roles):
	"""Get summary stats for dashboard cards."""
	doctype = "Team Project Update"
	base_filter = filters.copy() if filters else {}

	stats = {
		"total_projects": frappe.db.count(doctype, base_filter),
		"completed": frappe.db.count(doctype, {**base_filter, "status": "Approved"}),
		"in_progress": frappe.db.count(doctype, {**base_filter, "status": "In Progress"}),
		"pending_review": frappe.db.count(doctype, {**base_filter, "status": "Under Review"}),
		"active_teams": frappe.db.count("Team", {"is_active": 1}),
		"total_members": frappe.db.sql("SELECT COUNT(DISTINCT user) FROM `tabTeam Member`")[0][0] or 0,
	}

	# Team leaders count
	stats["team_leaders"] = len(frappe.get_all("Team", fields=["team_lead"], pluck="team_lead", filters=[["team_lead", "!=", ""]]))

	# Pending tasks
	stats["pending"] = stats["total_projects"] - stats["completed"]

	return stats


def get_status_chart_data(filters):
	"""Get data for the project status pie/donut chart."""
	doctype = "Team Project Update"
	statuses = ["Draft", "Assigned", "In Progress", "Completed", "Under Review", "Approved", "Rejected"]
	labels = []
	values = []

	for status in statuses:
		count = frappe.db.count(doctype, {**filters, "status": status}) if filters else frappe.db.count(doctype, {"status": status})
		if count > 0:
			labels.append(status)
			values.append(count)

	return {"labels": labels, "values": values}


def get_monthly_chart_data(filters):
	"""Get data for monthly completed projects chart."""
	doctype = "Team Project Update"
	months = []
	values = []

	today_date = getdate(today())
	for i in range(5, -1, -1):
		month_start = add_months(today_date.replace(day=1), -i)
		month_end = add_months(today_date.replace(day=1), -i + 1)
		month_name = frappe.utils.format_date(month_start, "MMM YYYY")

		count_filter = {
			"status": "Approved",
			"completion_date": [">=", month_start],
			"completion_date": ["<", month_end],
		}
		if filters:
			count_filter.update(filters)

		count = frappe.db.count(doctype, count_filter)
		months.append(month_name)
		values.append(count)

	return {"labels": months, "values": values}


def get_team_performance():
	"""Get team performance data."""
	teams = frappe.get_all("Team", filters={"is_active": 1}, fields=["name", "team_name"])
	performance = []

	for team in teams:
		total = frappe.db.count("Team Project Update", {"team": team.name})
		completed = frappe.db.count("Team Project Update", {"team": team.name, "status": "Approved"})
		members = frappe.db.count("Team Member", {"parent": team.name})

		performance.append({
			"team": team.team_name,
			"total": total,
			"completed": completed,
			"completion_rate": round((completed / total * 100), 1) if total > 0 else 0,
			"members": members,
		})

	return performance


def get_recent_activities(filters):
	"""Get recent project activities."""
	fields = ["name", "project_title", "team", "status", "progress_percent", "modified"]
	if filters:
		return frappe.get_all("Team Project Update", filters=filters, fields=fields, order_by="modified desc", limit=10)
	return frappe.get_all("Team Project Update", fields=fields, order_by="modified desc", limit=10)


def get_recent_notifications():
	"""Get recent notifications."""
	return frappe.get_all(
		"Notification Log",
		filters={"for_user": frappe.session.user},
		fields=["subject", "creation", "document_type", "document_name"],
		order_by="creation desc",
		limit=5,
	)
