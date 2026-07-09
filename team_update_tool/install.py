# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def after_install():
	"""Creates roles and seed data on app install."""
	create_roles()
	create_seed_data()
	frappe.db.commit()


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
