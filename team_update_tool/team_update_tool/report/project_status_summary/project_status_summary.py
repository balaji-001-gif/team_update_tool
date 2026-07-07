# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Project"), "fieldname": "project_title", "fieldtype": "Data", "width": 200},
		{"label": _("Team"), "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 150},
		{"label": _("Team Leader"), "fieldname": "assigned_team_leader", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 90},
		{"label": _("Progress"), "fieldname": "progress_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("Review Status"), "fieldname": "team_leader_review_status", "fieldtype": "Data", "width": 120},
		{"label": _("Completion Date"), "fieldname": "completion_date", "fieldtype": "Date", "width": 120},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("team"):
		conditions.append("team = %(team)s")
		values["team"] = filters.get("team")

	if filters.get("assigned_to"):
		conditions.append("assigned_to = %(assigned_to)s")
		values["assigned_to"] = filters.get("assigned_to")

	if filters.get("from_date"):
		conditions.append("completion_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("completion_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

	rows = frappe.db.sql(
		f"""
		SELECT
			project_title,
			team,
			assigned_team_leader,
			assigned_to,
			status,
			priority,
			progress_percent,
			team_leader_review_status,
			completion_date
		FROM `tabTeam Project Update`
		{where_clause}
		ORDER BY modified DESC
		""",
		values,
		as_dict=True,
	)

	return rows
