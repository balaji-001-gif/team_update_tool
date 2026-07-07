app_name = "team_update_tool"
app_title = "Team Update Tool"
app_publisher = "Your Company"
app_description = "Team Project Update Tool - Role-based task management with Admin, Team Leader, Team Member and Viewer access. Built for Frappe Framework and ERPNext v15+."
app_email = "admin@example.com"
app_license = "MIT"
app_icon = "octicon octicon-repo"
app_color = "#2E8B57"

# Includes in <head>
# ------------------
app_include_css = "/assets/team_update_tool/css/team_update_tool.css"
app_include_js = "/assets/team_update_tool/js/team_update_tool.js"

# Home Pages
# ----------
# application home page (will override Website Settings)
# home_page = "login"

# Installation
# ------------
after_install = "team_update_tool.install.after_install"

# Fixtures
# --------
fixtures = [
	{
		"dt": "Role",
		"filters": [["role_name", "in", [
			"Team Update Admin",
			"Team Update Team Leader",
			"Team Update Team Member",
			"Team Update Viewer"
		]]],
	}
]

# Document Events
# ---------------
doc_events = {
	"Team Project Update": {
		"after_insert": "team_update_tool.team_update_tool.doctype.team_project_update.team_project_update.after_insert_handler",
		"on_update": "team_update_tool.team_update_tool.doctype.team_project_update.team_project_update.on_update_handler",
	}
}

# Permission query conditions
# ----------------------------
permission_query_conditions = {
	"Team Project Update": "team_update_tool.team_update_tool.doctype.team_project_update.team_project_update.get_permission_query_conditions",
}

# Console Commands
# -------------------------------------------------------
# Run: bench --site yoursitename execute team_update_tool.demo.seed_demo_data

# Website route rules
# --------------------
website_route_rules = [
	# Dashboard landing
	{"from_route": "/dashboard", "to_route": "dashboard"},
	{"from_route": "/team-update", "to_route": "dashboard"},

	# Projects list and detail
	{"from_route": "/projects", "to_route": "projects/index"},
	{"from_route": "/projects/<name>", "to_route": "projects/index"},

	# Tasks list and detail
	{"from_route": "/tasks", "to_route": "tasks/index"},
	{"from_route": "/tasks/<name>", "to_route": "tasks/index"},

	# Teams list and detail
	{"from_route": "/teams", "to_route": "teams/index"},
	{"from_route": "/teams/<name>", "to_route": "teams/index"},

	# Notifications, profile, reports
	{"from_route": "/notifications", "to_route": "notifications"},
	{"from_route": "/profile", "to_route": "profile"},
	{"from_route": "/reports", "to_route": "reports"},

	# Aliases under /team-update/
	{"from_route": "/team-update/dashboard", "to_route": "dashboard"},
	{"from_route": "/team-update/projects", "to_route": "projects/index"},
	{"from_route": "/team-update/tasks", "to_route": "tasks/index"},
	{"from_route": "/team-update/teams", "to_route": "teams/index"},
	{"from_route": "/team-update/notifications", "to_route": "notifications"},
	{"from_route": "/team-update/profile", "to_route": "profile"},
	{"from_route": "/team-update/reports", "to_route": "reports"},
]
