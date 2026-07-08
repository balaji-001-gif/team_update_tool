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

website_route_rules = []

fixtures = [
	{"dt": "Role", "filters": [["role_name", "in", ["Admin", "View-Only User"]]]},
	{"dt": "Workspace", "filters": [["name", "=", "Team Update Tool"]]},
]

# Permission query conditions
permission_query_conditions = {
	"Project": "team_update_tool.transactions.doctype.project.project.get_permission_query_conditions",
}
