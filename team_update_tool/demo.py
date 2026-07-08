# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

"""
Demo Data Seeding Script for Team Update Tool.

Run this script on your Frappe site to create sample demo data.

How to run:
    bench --site yoursite execute team_update_tool.demo.seed_demo_data
"""

import frappe
from frappe.utils import today, add_days


def seed_demo_data():
	"""Main function to seed all demo data."""
	print("=" * 60)
	print("Seeding Demo Data for Team Update Tool...")
	print("=" * 60)

	create_demo_users()
	create_demo_team()
	create_demo_submissions()

	print("\n" + "=" * 60)
	print("Demo data seeding complete!")
	print("Users: admin@demo.com, contributor@demo.com, viewer@demo.com")
	print("Team: Development Team")
	print("Submissions: 3 sample submissions in different statuses")
	print("=" * 60)


def create_demo_users():
	"""Create 3 demo users with different roles."""
	print("\n1. Creating demo users...")

	users_data = [
		{
			"email": "admin@demo.com",
			"first_name": "Admin",
			"last_name": "User",
			"role": "Project Admin",
			"send_welcome_email": 0,
		},
		{
			"email": "contributor@demo.com",
			"first_name": "Contributor",
			"last_name": "User",
			"role": "Project Contributor",
			"send_welcome_email": 0,
		},
		{
			"email": "viewer@demo.com",
			"first_name": "Viewer",
			"last_name": "User",
			"role": "Project Viewer",
			"send_welcome_email": 0,
		},
	]

	for ud in users_data:
		if frappe.db.exists("User", ud["email"]):
			print(f"  Skipping {ud['email']} (already exists)")
			continue

		user = frappe.get_doc({
			"doctype": "User",
			"email": ud["email"],
			"first_name": ud["first_name"],
			"last_name": ud["last_name"],
			"send_welcome_email": ud["send_welcome_email"],
			"roles": [{"role": ud["role"]}],
		})
		user.insert(ignore_permissions=True)
		print(f"  Created: {ud['email']} -> {ud['role']}")

	frappe.db.commit()


def create_demo_team():
	"""Create a sample team."""
	print("\n2. Creating demo team...")

	if frappe.db.exists("Team", "Development Team"):
		print("  Team 'Development Team' already exists, skipping")
		return

	team = frappe.get_doc({
		"doctype": "Team",
		"team_name": "Development Team",
		"team_type": "Development",
		"team_lead": "admin@demo.com",
		"is_active": 1,
		"description": "Sample development team for demo purposes",
		"members": [
			{"user": "contributor@demo.com", "role_in_team": "Full Stack Developer"},
		],
	})
	team.insert(ignore_permissions=True)
	print("  Created team: Development Team")
	frappe.db.commit()


def create_demo_submissions():
	"""Create sample submissions in different workflow stages."""
	print("\n3. Creating demo submissions...")

	submissions_data = [
		{
			"project_title": "Customer Dashboard Enhancement",
			"team": "Development Team",
			"submitted_by": "contributor@demo.com",
			"status": "Submitted",
			"priority": "High",
			"progress_percent": 60,
			"start_date": add_days(today(), -10),
			"due_date": add_days(today(), 5),
			"description": "<p>Enhancing the customer dashboard with new charts, filters, and export functionality.</p>",
			"github_repo_url": "https://github.com/demo-org/customer-dashboard",
			"tags": "dashboard, UI, charts",
		},
		{
			"project_title": "REST API Integration Module",
			"team": "Development Team",
			"submitted_by": "contributor@demo.com",
			"status": "Under Review",
			"priority": "Urgent",
			"progress_percent": 100,
			"start_date": add_days(today(), -20),
			"completion_date": add_days(today(), -2),
			"description": "<p>Built a complete REST API integration module connecting with third-party services.</p>",
			"github_repo_url": "https://github.com/demo-org/api-payment-module",
			"tags": "API, integration",
			"reviewed_by": "admin@demo.com",
		},
		{
			"project_title": "Mobile App Profile Screen",
			"team": "Development Team",
			"submitted_by": "contributor@demo.com",
			"status": "Approved",
			"priority": "Medium",
			"progress_percent": 100,
			"start_date": add_days(today(), -30),
			"completion_date": add_days(today(), -10),
			"description": "<p>Designed and developed the user profile screen for the mobile application.</p>",
			"github_repo_url": "https://github.com/demo-org/mobile-app-profile",
			"tags": "mobile, UI, profile",
			"reviewed_by": "admin@demo.com",
			"approved_by": "admin@demo.com",
			"approval_date": add_days(today(), -9),
		},
	]

	created_count = 0
	for sd in submissions_data:
		if frappe.db.exists("Project Submission", {"project_title": sd["project_title"]}):
			print(f"  Skipping '{sd['project_title']}' (already exists)")
			continue

		submission = frappe.get_doc({
			"doctype": "Project Submission",
			**sd,
		})
		submission.insert(ignore_permissions=True)
		created_count += 1
		print(f"  Created: {sd['project_title']} -> Status: {sd['status']}")

	if created_count > 0:
		frappe.db.commit()
