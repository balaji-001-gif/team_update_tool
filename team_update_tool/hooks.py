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
# Restrict list view so each role only sees records they are permitted to see
permission_query_conditions = {
	"Team Project Update": "team_update_tool.team_update_tool.doctype.team_project_update.team_project_update.get_permission_query_conditions",
}

# Website route rules
# --------------------
website_route_rules = []
