# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def get_context(context, **kwargs):
	"""Build the teams page context."""
	context.no_sidebar = 1
	context.no_cache = 1
	context.title = "Teams - Team Update Tool"

	roles = frappe.get_roles(frappe.session.user)
	context.is_admin = "Team Update Admin" in roles or "System Manager" in roles

	team_name = kwargs.get("name")

	if team_name:
		# Detail view
		if not frappe.db.exists("Team", team_name):
			context.message = "Team not found."
			context.is_detail = False
			context.teams = frappe.get_all("Team", filters={"is_active": 1}, fields=["name", "team_name", "team_type", "team_lead", "description"])
			return

		team = frappe.get_doc("Team", team_name)
		context.team = team
		context.members = frappe.get_all(
			"Team Member",
			filters={"parent": team_name},
			fields=["user", "role_in_team"]
		)
		context.projects = frappe.get_all(
			"Team Project Update",
			filters={"team": team_name},
			fields=["name", "project_title", "status", "progress_percent"],
			limit=20
		)
		context.is_detail = True
		context.title = f"{team.team_name} - Teams"
	else:
		context.is_detail = False
		context.teams = frappe.get_all(
			"Team",
			filters={"is_active": 1},
			fields=["name", "team_name", "team_type", "team_lead", "description"],
			order_by="team_name asc"
		)
