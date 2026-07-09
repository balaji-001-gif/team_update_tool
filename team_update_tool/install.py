# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def after_install():
	"""Creates roles, domain, and seed data on app install."""
	force_sync_doctypes()
	create_domain()
	create_roles()
	create_seed_data()
	frappe.db.commit()


def create_domain():
	"""Create Team Update Tool domain for restrict_to_domain usage."""
	if not frappe.db.exists("Domain", "Team Update Tool"):
		doc = frappe.get_doc({
			"doctype": "Domain",
			"domain": "Team Update Tool",
		})
		doc.insert(ignore_permissions=True)


def force_sync_doctypes():
	"""Delete old doctype records and let them re-sync from JSON files."""
	from frappe.modules.import_file import import_file_by_path
	import os
	
	app_path = frappe.get_app_path("team_update_tool")
	
	# Sync Doctypes
	doctype_list = [
		("masters/doctype/team/team.json", "Team"),
		("masters/doctype/team_member/team_member.json", "Team Member"),
		("masters/doctype/technology/technology.json", "Technology"),
		("masters/doctype/project_category/project_category.json", "Project Category"),
		("masters/doctype/project_status/project_status.json", "Project Status"),
		("transactions/doctype/project/project.json", "Project"),
		("transactions/doctype/project_readme/project_readme.json", "Project Readme"),
		("transactions/doctype/project_update/project_update.json", "Project Update"),
		("transactions/doctype/project_files/project_files.json", "Project Files"),
		("transactions/doctype/project_screenshots/project_screenshots.json", "Project Screenshots"),
		("transactions/doctype/project_technology/project_technology.json", "Project Technology"),
		("transactions/doctype/github_repository/github_repository.json", "GitHub Repository"),
	]
	
	for json_path, dt_name in doctype_list:
		full_path = os.path.join(app_path, json_path)
		if frappe.db.exists("DocType", dt_name):
			frappe.delete_doc("DocType", dt_name, force=True)
		import_file_by_path(full_path)
		frappe.db.commit()
	
	# Sync Reports
	report_list = [
		"reports/project_summary_report/project_summary_report.json",
		"reports/team_activity_report/team_activity_report.json",
		"reports/completed_projects_report/completed_projects_report.json",
		"reports/github_repository_report/github_repository_report.json",
	]
	
	for json_path in report_list:
		full_path = os.path.join(app_path, json_path)
		import_file_by_path(full_path)
		frappe.db.commit()
	
	# Sync Workspace - Force delete and recreate
	workspace_path = os.path.join(app_path, "masters/workspace/team_update_tool.json")
	
	# Delete existing workspace completely
	if frappe.db.exists("Workspace", "Team Update Tool"):
		frappe.delete_doc("Workspace", "Team Update Tool", force=True)
	frappe.db.commit()
	
	# Delete any orphaned workspace links
	frappe.db.delete("Workspace Link", {"parent": "Team Update Tool"})
	frappe.db.commit()
	
	# Import fresh workspace from JSON
	import_file_by_path(workspace_path, force=True)
	frappe.db.commit()
	
	frappe.clear_cache()
	frappe.publish_realtime("clear_cache")


def create_roles():
	roles = [
		{
			"role_name": "Admin",
			"desk_access": 1,
			"description": "Full CRUD access. Can create, read, update, delete, approve, reject projects, manage teams, configure settings.",
		},
		{
			"role_name": "Team Member",
			"desk_access": 1,
			"description": "Can create projects, upload GitHub repositories, upload screenshots and documents, edit own projects, and track project status. Cannot approve, reject, or delete approved projects.",
		},
		{
			"role_name": "View-Only User",
			"desk_access": 1,
			"description": "Read-only access. Can view approved projects, GitHub links, screenshots, documents, and reports. Cannot create, edit, delete, or upload.",
		},
	]
	for role in roles:
		if not frappe.db.exists("Role", role["role_name"]):
			doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": role["role_name"],
				"desk_access": role["desk_access"],
				"description": role["description"],
			})
			doc.insert(ignore_permissions=True)


def create_seed_data():
	"""Create default master data so the app works out of the box."""
	# Project Statuses
	statuses = [
		{"status_name": "Draft", "color": "#64748b"},
		{"status_name": "Pending Review", "color": "#f59e0b"},
		{"status_name": "Under Review", "color": "#3b82f6"},
		{"status_name": "In Progress", "color": "#8b5cf6"},
		{"status_name": "Approved", "color": "#16a34a"},
		{"status_name": "Rejected", "color": "#dc2626"},
		{"status_name": "Completed", "color": "#16a34a"},
		{"status_name": "On Hold", "color": "#f97316"},
	]
	for s in statuses:
		if not frappe.db.exists("Project Status", {"status_name": s["status_name"]}):
			doc = frappe.get_doc({
				"doctype": "Project Status",
				"status_name": s["status_name"],
				"color": s["color"],
			})
			doc.insert(ignore_permissions=True)

	# Project Categories
	categories = [
		"Web Application",
		"Mobile App",
		"API Integration",
		"ERPNext Customization",
		"Frappe App",
		"Data Analysis",
		"Infrastructure",
		"Research",
	]
	for cat_name in categories:
		if not frappe.db.exists("Project Category", {"category_name": cat_name}):
			doc = frappe.get_doc({
				"doctype": "Project Category",
				"category_name": cat_name,
			})
			doc.insert(ignore_permissions=True)

	# Technologies
	technologies = [
		"Python",
		"JavaScript",
		"TypeScript",
		"React",
		"Vue.js",
		"Node.js",
		"Frappe Framework",
		"ERPNext",
		"Django",
		"PostgreSQL",
		"MySQL",
		"Redis",
		"Docker",
		"Linux",
		"HTML/CSS",
		"Bootstrap",
		"Tailwind CSS",
		"Next.js",
		"REST API",
		"GraphQL",
	]
	for tech_name in technologies:
		if not frappe.db.exists("Technology", {"technology_name": tech_name}):
			doc = frappe.get_doc({
				"doctype": "Technology",
				"technology_name": tech_name,
			})
			doc.insert(ignore_permissions=True)
