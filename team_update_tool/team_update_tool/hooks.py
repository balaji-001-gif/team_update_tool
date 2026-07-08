app_name = "team_update_tool"
app_title = "Team Update Tool"
app_publisher = "Your Company"
app_description = "Team Update Dashboard - Track completed team projects with GitHub integration and role-based access control for Frappe v15+"
app_email = "admin@example.com"
app_license = "MIT"
app_icon = "octicon octicon-repo"
app_color = "#2E8B57"

# Includes in <head>
app_include_css = "/assets/team_update_tool/css/team_update_tool.css"
app_include_js = "/assets/team_update_tool/js/team_update_tool.js"

# Installation
after_install = "team_update_tool.install.after_install"

# Fixtures - exportable via bench export-fixtures
fixtures = [
	{"dt": "Role", "filters": [["role_name", "in", [
		"Project Admin",
		"Project Contributor",
		"Project Viewer"
	]]]},
	{"dt": "Page", "filters": [["name", "=", "team-update-dashboard"]]},
	{"dt": "Workspace", "filters": [["name", "=", "Team Update Tool"]]},
]

# Document Events
doc_events = {
	"Project Submission": {
		"validate": "team_update_tool.team_update_tool.doctype.project_submission.project_submission.fetch_github_metadata_on_validate",
	}
}

# Permission query conditions
permission_query_conditions = {
	"Project Submission": "team_update_tool.team_update_tool.doctype.project_submission.project_submission.get_permission_query_conditions",
}

# Console Commands
# Run: bench --site yoursitename execute team_update_tool.demo.seed_demo_data
