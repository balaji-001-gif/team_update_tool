app_name = "team_update_tool"
app_title = "Team Update Tool"
app_publisher = "Your Company"
app_description = "Team Update Tool - Track completed team projects with GitHub integration and role-based access control for Frappe v15+"
app_email = "admin@example.com"
app_license = "MIT"
app_icon = "octicon octicon-repo"
app_color = "#2E8B57"

app_include_css = "/assets/team_update_tool/css/team_update_tool.css"
app_include_js = "/assets/team_update_tool/js/team_update_tool.js"

after_install = "team_update_tool.install.after_install"

website_route_rules = [
	# Dynamic route for project detail page (path-based URL)
	{"from_route": "/team_update_tool/project/<name>", "to_route": "team_update_tool/project"},
]

fixtures = [
	{"dt": "Role", "filters": [["role_name", "in", ["Admin", "Team Member", "View-Only User"]]]},
	{"dt": "DocType", "filters": [["name", "in", ["Team", "Team Member", "Technology", "Project Category", "Project Status", "Project", "Project Update", "Project Files", "Project Screenshots", "Project Technology", "GitHub Repository"]]]},
]

