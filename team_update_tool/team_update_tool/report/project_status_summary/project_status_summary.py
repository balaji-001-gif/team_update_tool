# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Project"), "fieldname": "project_title", "fieldtype": "Data", "width": 200},
		{"label": _("Team"), "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 80},
		{"label": _("Progress"), "fieldname": "progress_percent", "fieldtype": "Percent", "width": 80},
		{"label": _("Submitted By"), "fieldname": "submitted_by", "fieldtype": "Link", "options": "User", "width": 120},
		{"label": _("GitHub URL"), "fieldname": "github_repo_url", "fieldtype": "Data", "width": 200},
		{"label": _("Approved By"), "fieldname": "approved_by", "fieldtype": "Link", "options": "User", "width": 120},
		{"label": _("Completion Date"), "fieldname": "completion_date", "fieldtype": "Date", "width": 100},
	]


def get_data(filters):
	conditions = []
	params = {}

	if filters:
		if filters.get("team"):
			conditions.append("team = %(team)s")
			params["team"] = filters["team"]

		if filters.get("submitted_by"):
			conditions.append("submitted_by = %(submitted_by)s")
			params["submitted_by"] = filters["submitted_by"]

		if filters.get("from_date"):
			conditions.append("completion_date >= %(from_date)s")
			params["from_date"] = filters["from_date"]

		if filters.get("to_date"):
			conditions.append("completion_date <= %(to_date)s")
			params["to_date"] = filters["to_date"]

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(
		f"""SELECT project_title, team, status, priority, progress_percent,
			submitted_by, github_repo_url, approved_by, completion_date
		FROM `tabProject Submission`
		WHERE {where_clause}
		ORDER BY modified DESC""",
		params,
		as_dict=1,
	)

	return data
