# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def _get_user_role_info():
	"""Helper to get role info for current user.
	Returns: roles, is_admin, is_team_member, is_viewer
	"""
	roles = frappe.get_roles(frappe.session.user)
	is_admin = "Admin" in roles or "System Manager" in roles
	is_team_member = "Team Member" in roles and not is_admin
	is_viewer = "View-Only User" in roles and not is_admin and not is_team_member
	return roles, is_admin, is_team_member, is_viewer


def _get_visible_filters():
	"""Get base filters for View-Only Users."""
	roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	filters = {}
	if is_viewer:
		approved = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
		if approved:
			filters["status"] = approved
	return filters, is_admin, is_viewer


@frappe.whitelist(allow_guest=True)
def get_projects(status=None, category=None, team=None, technology=None,
				 search=None, limit=20, offset=0):
	"""Get list of projects with advanced filters and search."""
	try:
		filters, is_admin, is_viewer = _get_visible_filters()

		if status:
			filters["status"] = status
		if category:
			filters["project_category"] = category
		if team:
			filters["team"] = team

		# Build OR filters for search
		or_filters = None
		if search:
			or_filters = [
				["Project", "project_title", "like", f"%{search}%"],
				["Project", "description", "like", f"%{search}%"],
			]

		projects = frappe.get_all("Project",
			filters=filters,
			or_filters=or_filters,
			fields=["name", "project_title", "status", "team", "priority",
					"project_category", "creation", "start_date", "completion_date",
					"owner", "modified"],
			limit=limit,
			start=offset,
			order_by="modified desc"
		)

		# Enrich with names, screenshot preview, technology count
		for p in projects:
			if p.status:
				try:
					status_doc = frappe.get_cached_doc("Project Status", p.status)
					p.status_name = status_doc.status_name
					p.status_color = status_doc.color
				except:
					p.status_name = p.status
					p.status_color = "#6b7280"
			if p.project_category:
				try:
					cat = frappe.get_cached_doc("Project Category", p.project_category)
					p.category_name = cat.category_name
				except:
					p.category_name = p.project_category

			# Get first screenshot as preview
			try:
				project_doc = frappe.get_cached_doc("Project", p.name)
				p.screenshot_preview = ""
				if project_doc.screenshots and len(project_doc.screenshots) > 0:
					p.screenshot_preview = project_doc.screenshots[0].screenshot
				p.technology_count = len(project_doc.technologies or [])
				p.update_count = len(project_doc.project_updates or [])
			except:
				p.screenshot_preview = ""
				p.technology_count = 0
				p.update_count = 0

		total = frappe.db.count("Project", filters=filters)

		return {
			"projects": projects,
			"total": total,
			"limit": limit,
			"offset": offset,
			"has_more": (offset + limit) < total,
		}
	except Exception as e:
		frappe.log_error(f"Error in get_projects: {str(e)}", "get_projects API Error")
		return {
			"projects": [],
			"total": 0,
			"limit": limit,
			"offset": offset,
			"has_more": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def get_project_detail(name):
	"""Get full project details including all child tables."""
	if not name:
		frappe.throw(_("Project name is required."))

	try:
		project = frappe.get_doc("Project", name)
	except Exception as e:
		frappe.log_error(f"Error loading project {name}: {str(e)}", "get_project_detail Error")
		frappe.throw(_(f"Error loading project: {str(e)}"))

	# Permission check
	__roles, is_admin, __is_team_member, is_viewer = _get_user_role_info()
	if is_viewer:
		approved = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
		can_view = (approved and project.status == approved) or is_admin
		if not can_view:
			frappe.throw(_("You do not have permission to view this project."), frappe.PermissionError)

	# Screenshots
	screenshots = []
	for s in project.screenshots or []:
		screenshots.append({
			"screenshot": s.screenshot,
			"caption": s.caption,
			"screenshot_type": s.screenshot_type,
		})

	# Files
	files = []
	for f in project.project_files or []:
		files.append({
			"file": f.file,
			"file_name": f.file_name,
			"file_type": f.file_type,
			"description": f.file_description,
		})

	# Updates
	updates = []
	for u in project.project_updates or []:
		updates.append({
			"name": u.name,
			"update_title": u.update_title,
			"update_description": u.update_description,
			"update_date": str(u.update_date) if u.update_date else "",
			"updated_by": u.updated_by,
		})

	# Technologies
	technologies = [t.technology for t in project.technologies or []]

	# Status info
	status_info = {}
	if project.status:
		status_doc = frappe.get_cached_doc("Project Status", project.status)
		status_info = {
			"name": status_doc.name,
			"status_name": status_doc.status_name,
			"color": status_doc.color,
		}

	# GitHub repo info
	github_info = None
	if project.github_repository:
		try:
			repo = frappe.get_cached_doc("GitHub Repository", project.github_repository)
			github_info = {
				"name": repo.name,
				"repository_url": repo.repository_url,
				"repository_name": repo.repository_name,
				"commit_hash": repo.commit_hash,
				"default_branch": repo.default_branch,
				"languages": repo.languages,
			}
		except frappe.DoesNotExistError:
			pass

	# Team name
	team_name = project.team
	try:
		team_doc = frappe.get_cached_doc("Team", project.team)
		team_name = team_doc.team_name
	except Exception:
		pass

	# README content
	readme = None
	try:
		readme_doc = frappe.db.get_value("Project Readme", {"project": name}, "*", as_dict=1)
		if readme_doc:
			readme = {
				"readme_content": readme_doc.readme_content or "",
				"readme_file": readme_doc.readme_file or "",
			}
	except Exception:
		pass

	return {
		"name": project.name,
		"project_title": project.project_title,
		"status": status_info,
		"team": project.team,
		"team_name": team_name,
		"priority": project.priority,
		"project_category": project.project_category,
		"description": project.description,
		"tags": project.tags,
		"github_repository": project.github_repository,
		"github_info": github_info,
		"start_date": str(project.start_date) if project.start_date else "",
		"due_date": str(project.due_date) if project.due_date else "",
		"completion_date": str(project.completion_date) if project.completion_date else "",
		"approved_by": project.approved_by or "",
		"approval_date": str(project.approval_date) if project.approval_date else "",
		"review_remarks": project.review_remarks or "",
		"creation": str(project.creation),
		"modified": str(project.modified),
		"owner": project.owner,
		"screenshots": screenshots,
		"files": files,
		"updates": updates,
		"technologies": technologies,
		"readme": readme,
		"is_owner": project.owner == frappe.session.user,
	}


@frappe.whitelist(allow_guest=True)
def get_dashboard_stats():
	"""Get comprehensive dashboard statistics."""
	filters, is_admin, is_viewer = _get_visible_filters()

	total_projects = frappe.db.count("Project", filters=filters)

	# Status-wise counts (even zero)
	status_counts = []
	statuses = frappe.get_all("Project Status", fields=["name", "status_name", "color"], order_by="status_name asc")
	for s in statuses:
		f = dict(filters)
		f["status"] = s.name
		count = frappe.db.count("Project", filters=f)
		status_counts.append({
			"name": s.status_name,
			"slug": s.name,
			"count": count,
			"color": s.color,
		})

	# Category counts
	cat_filters = dict(filters)
	categories = frappe.get_all("Project Category", fields=["name", "category_name"])
	category_counts = []
	for c in categories:
		f = dict(filters)
		f["project_category"] = c.name
		count = frappe.db.count("Project", filters=f)
		if count:
			category_counts.append({
				"name": c.category_name,
				"count": count,
			})

	# Latest projects
	recent = frappe.get_all("Project",
		filters=filters,
		fields=["name", "project_title", "status", "owner", "creation", "modified"],
		limit=6,
		order_by="modified desc"
	)
	for p in recent:
		if p.status:
			s = frappe.get_cached_doc("Project Status", p.status)
			p.status_name = s.status_name
			p.status_color = s.color

	# Recent GitHub uploads
	recent_repos = frappe.get_all("GitHub Repository",
		fields=["name", "repository_name", "repository_url", "creation"],
		limit=5,
		order_by="creation desc"
	)

	# Recent screenshots
	projects = frappe.get_all("Project", filters=filters, pluck="name")
	recent_screenshots = []
	for p_name in projects[:10]:
		doc = frappe.get_cached_doc("Project", p_name)
		for s in doc.screenshots or []:
			recent_screenshots.append({
				"screenshot": s.screenshot,
				"caption": s.caption or "",
				"project": p_name,
				"project_title": doc.project_title,
			})
			if len(recent_screenshots) >= 6:
				break
		if len(recent_screenshots) >= 6:
			break
	recent_screenshots.reverse()

	# Team and technology counts
	total_teams = frappe.db.count("Team", filters={"is_active": 1})
	total_technologies = frappe.db.count("Technology")
	total_categories = frappe.db.count("Project Category")

	# User's own projects
	my_projects = 0
	if frappe.session.user != "Guest" and not is_viewer:
		my_projects = frappe.db.count("Project", filters={"owner": frappe.session.user})

	# Recent documents (files)
	recent_documents = []
	for p_name in projects[:10]:
		doc = frappe.get_cached_doc("Project", p_name)
		for f in doc.project_files or []:
			recent_documents.append({
				"file": f.file,
				"file_name": f.file_name or f.file,
				"file_type": f.file_type or "",
				"project": p_name,
				"project_title": doc.project_title,
			})
			if len(recent_documents) >= 5:
				break
		if len(recent_documents) >= 5:
			break
	recent_documents.reverse()

	return {
		"total_projects": total_projects,
		"total_teams": total_teams,
		"total_technologies": total_technologies,
		"total_categories": total_categories,
		"my_projects": my_projects,
		"status_counts": status_counts,
		"category_counts": category_counts,
		"recent_projects": recent,
		"recent_repos": recent_repos,
		"recent_screenshots": recent_screenshots,
		"recent_documents": recent_documents,
		"is_admin": is_admin,
		"is_viewer": is_viewer,
	}


@frappe.whitelist()
def get_projects_for_user(user=None):
	"""Get projects owned by a specific user."""
	if not user:
		user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please login to view your projects."))
	projects = frappe.get_all("Project",
		filters={"owner": user},
		fields=["name", "project_title", "status", "team", "priority",
				"project_category", "creation", "completion_date", "modified"],
		order_by="modified desc"
	)
	for p in projects:
		if p.status:
			s = frappe.get_cached_doc("Project Status", p.status)
			p.status_name = s.status_name
			p.status_color = s.color
	return projects


@frappe.whitelist(allow_guest=True)
def get_repositories(limit=20, offset=0):
	"""Get GitHub repositories."""
	try:
		repos = frappe.get_all("GitHub Repository",
			fields=["name", "repository_url", "repository_name", "commit_hash",
					"default_branch", "languages", "creation"],
			limit=limit,
			start=offset,
			order_by="creation desc"
		)
		total = frappe.db.count("GitHub Repository")
		return {"repositories": repos, "total": total, "has_more": (offset + limit) < total}
	except Exception as e:
		frappe.log_error(f"Error fetching repositories: {str(e)}", "get_repositories Error")
		return {"repositories": [], "total": 0, "has_more": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_documents(limit=20, offset=0):
	"""Get all project files/documents grouped by project."""
	try:
		filters, is_admin, is_viewer = _get_visible_filters()
		projects = frappe.get_all("Project", filters=filters, pluck="name")

		all_files = []
		for p_name in projects:
			doc = frappe.get_cached_doc("Project", p_name)
			for f in doc.project_files or []:
				all_files.append({
					"file": f.file,
					"file_name": f.file_name or f.file,
					"file_type": f.file_type or "",
					"description": f.file_description or "",
					"project": p_name,
					"project_title": doc.project_title,
				})

		all_files.reverse()
		total = len(all_files)
		limited = all_files[offset:offset + limit]

		return {"documents": limited, "total": total, "has_more": (offset + limit) < total}
	except Exception as e:
		frappe.log_error(f"Error in get_documents: {str(e)}", "get_documents Error")
		return {"documents": [], "total": 0, "has_more": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_gallery(limit=30, offset=0):
	"""Get all screenshots from visible projects."""
	try:
		filters, is_admin, is_viewer = _get_visible_filters()
		projects = frappe.get_all("Project", filters=filters, pluck="name")

		all_screenshots = []
		for p_name in projects:
			doc = frappe.get_cached_doc("Project", p_name)
			for s in doc.screenshots or []:
				all_screenshots.append({
					"screenshot": s.screenshot,
					"caption": s.caption or "",
					"screenshot_type": s.screenshot_type or "",
					"project": p_name,
					"project_title": doc.project_title,
				})

		all_screenshots.reverse()
		total = len(all_screenshots)
		limited = all_screenshots[offset:offset + limit]

		return {"screenshots": limited, "total": total, "has_more": (offset + limit) < total}
	except Exception as e:
		frappe.log_error(f"Error in get_gallery: {str(e)}", "get_gallery Error")
		return {"screenshots": [], "total": 0, "has_more": False, "error": str(e)}


@frappe.whitelist()
def create_project(project_title, team, status=None, project_category=None,
				   priority="Medium", description=None, tags=None,
				   start_date=None, due_date=None,
				   technologies=None, github_url=None,
				   github_repo_name=None, github_branch=None):
	"""Create a new project from the website.
	Supports multi-step form with technologies, GitHub repo, screenshots, and files.
	"""
	__roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	if is_viewer and not is_admin and not is_team_member:
		frappe.throw(_("You do not have permission to create projects."), frappe.PermissionError)

	if not project_title:
		frappe.throw(_("Project title is required."))
	if not team:
		frappe.throw(_("Team is required."))
	if not github_url:
		frappe.throw(_("GitHub repository URL is required. Every project must have a linked GitHub repository."))

	if not status:
		# Default to "Pending Review" for new projects
		pending_review = frappe.db.get_value("Project Status", {"status_name": "Pending Review"}, "name")
		if not pending_review:
			# Fallback to first available status
			statuses = frappe.db.get_all("Project Status", fields=["name"], order_by="creation asc", limit=1)
			if statuses:
				status = statuses[0].name
		else:
			status = pending_review

	# Validate GitHub URL
	import re
	github_pattern = r'^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(\/.*)?$'
	if not re.match(github_pattern, github_url.strip()):
		frappe.throw(_("Invalid GitHub URL. Must be like https://github.com/user/repo"))

	# Create or find GitHub Repository
	repo_name = github_repo_name or github_url.strip().rstrip('/').split('/')[-1]
	existing_repo = frappe.db.exists("GitHub Repository", {"repository_url": github_url.strip()})
	if existing_repo:
		github_repo_link = existing_repo
	else:
		# Generate a unique name for the GitHub Repository
		# The autoname format in doctype is broken, so we insert directly using SQL
		import hashlib
		hash_suffix = hashlib.md5(github_url.strip().encode()).hexdigest()[:8].upper()
		repo_name_unique = f"GR-{hash_suffix}"
		
		# Ensure uniqueness in case of hash collision
		while frappe.db.exists("GitHub Repository", repo_name_unique):
			hash_suffix = hashlib.md5((github_url.strip() + frappe.generate_hash(length=8)).encode()).hexdigest()[:8].upper()
			repo_name_unique = f"GR-{hash_suffix}"
		
		# Insert directly using SQL to bypass broken autoname
		now = frappe.utils.now()
		frappe.db.sql("""
			INSERT INTO `tabGitHub Repository` 
			(name, repository_url, repository_name, default_branch, creation, modified, owner, modified_by)
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
		""", (
			repo_name_unique,
			github_url.strip(),
			repo_name,
			github_branch or "main",
			now, now, frappe.session.user, frappe.session.user
		))
		frappe.db.commit()
		github_repo_link = repo_name_unique

	# Validate technologies
	tech_list = []
	if technologies:
		if isinstance(technologies, str):
			import json
			technologies = json.loads(technologies)
		tech_list = technologies if isinstance(technologies, list) else []

		for tech in tech_list:
			if not frappe.db.exists("Technology", tech):
				frappe.throw(_(f"Technology '{tech}' does not exist."))

	if not tech_list:
		frappe.throw(_("At least one technology must be selected."))

	# Generate a unique name for the Project
	# The autoname format in doctype is broken, so we insert directly using SQL
	import hashlib
	hash_suffix = hashlib.md5((project_title + team + frappe.session.user).encode()).hexdigest()[:8].upper()
	proj_name_unique = f"PRJ-{hash_suffix}"
	
	# Ensure uniqueness in case of hash collision
	while frappe.db.exists("Project", proj_name_unique):
		hash_suffix = hashlib.md5((project_title + team + frappe.session.user + frappe.generate_hash(length=8)).encode()).hexdigest()[:8].upper()
		proj_name_unique = f"PRJ-{hash_suffix}"

	# Insert directly using SQL to bypass broken autoname
	now = frappe.utils.now()
	frappe.db.sql("""
		INSERT INTO `tabProject` 
		(name, project_title, team, project_category, status, priority, description, tags, 
		 start_date, due_date, github_repository, creation, modified, owner, modified_by)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
	""", (
		proj_name_unique,
		project_title,
		team,
		project_category or None,
		status or None,
		priority,
		description or "",
		tags or "",
		start_date or None,
		due_date or None,
		github_repo_link,
		now, now, frappe.session.user, frappe.session.user
	))
	
	# Add technologies to child table
	for tech in tech_list:
		tech_hash = hashlib.md5((proj_name_unique + tech).encode()).hexdigest()[:10].upper()
		tech_name = f"PROJTECH-{tech_hash}"
		frappe.db.sql("""
			INSERT INTO `tabProject Technology` 
			(name, parent, parentfield, parenttype, technology, idx, creation, modified, owner, modified_by)
			VALUES (%s, %s, 'technologies', 'Project', %s, %s, %s, %s, %s, %s)
		""", (
			tech_name,
			proj_name_unique,
			tech,
			1,  # idx
			now, now, frappe.session.user, frappe.session.user
		))
	
	frappe.db.commit()

	return {
		"message": _("Project created successfully."),
		"name": proj_name_unique,
		"route": f"/team_update_tool/project/{proj_name_unique}",
	}


@frappe.whitelist()
def add_project_screenshot(project_name, file_url, caption=None):
	"""Attach a screenshot to a project's child table after file upload."""
	__roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	if is_viewer and not is_admin and not is_team_member:
		frappe.throw(_("Permission denied."), frappe.PermissionError)

	if not project_name or not file_url:
		frappe.throw(_("Project name and file URL are required."))

	project = frappe.get_doc("Project", project_name)
	if not is_admin and project.owner != frappe.session.user:
		frappe.throw(_("You can only modify your own projects."), frappe.PermissionError)

	project.append("screenshots", {
		"screenshot": file_url,
		"caption": caption or "",
		"screenshot_type": "UI Screen",
	})
	project.save(ignore_permissions=is_admin)

	return {"message": _("Screenshot added."), "success": True}


@frappe.whitelist()
def add_project_file(project_name, file_url, file_name=None, file_type=None):
	"""Attach a file to a project's child table after upload."""
	__roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	if is_viewer and not is_admin and not is_team_member:
		frappe.throw(_("Permission denied."), frappe.PermissionError)

	if not project_name or not file_url:
		frappe.throw(_("Project name and file URL are required."))

	project = frappe.get_doc("Project", project_name)
	if not is_admin and project.owner != frappe.session.user:
		frappe.throw(_("You can only modify your own projects."), frappe.PermissionError)

	project.append("project_files", {
		"file": file_url,
		"file_name": file_name or file_url.split("/")[-1],
		"file_type": file_type or "Other",
	})
	project.save(ignore_permissions=is_admin)

	return {"message": _("File added."), "success": True}


@frappe.whitelist()
def create_project_readme(project_name, readme_file=None, readme_content=None):
	"""Create or update Project Readme for a project."""
	__roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	if is_viewer and not is_admin and not is_team_member:
		frappe.throw(_("Permission denied."), frappe.PermissionError)

	if not project_name:
		frappe.throw(_("Project name is required."))

	project = frappe.get_doc("Project", project_name)
	if not is_admin and project.owner != frappe.session.user:
		frappe.throw(_("You can only modify your own projects."), frappe.PermissionError)

	# Check if Project Readme already exists for this project
	existing = frappe.db.get_value("Project Readme", {"project": project_name}, "name")
	if existing:
		# Update existing
		readme = frappe.get_doc("Project Readme", existing)
	else:
		# Create new
		readme = frappe.new_doc("Project Readme")
		readme.project = project_name

	if readme_file:
		readme.readme_file = readme_file
	if readme_content:
		readme.readme_content = readme_content

	readme.save(ignore_permissions=is_admin)

	return {"message": _("Project Readme created."), "success": True}


@frappe.whitelist()
def update_project(name, project_title=None, description=None, tags=None,
				   priority=None, project_category=None, team=None,
				   start_date=None, due_date=None):
	"""Update an existing project from the website."""
	__roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	if is_viewer and not is_admin and not is_team_member:
		frappe.throw(_("You do not have permission to edit projects."), frappe.PermissionError)

	project = frappe.get_doc("Project", name)
	if not is_admin and project.owner != frappe.session.user:
		frappe.throw(_("You can only edit your own projects."), frappe.PermissionError)

	if project_title:
		project.project_title = project_title
	if description is not None:
		project.description = description
	if tags is not None:
		project.tags = tags
	if priority:
		project.priority = priority
	if project_category:
		project.project_category = project_category
	if team:
		project.team = team
	if start_date is not None:
		project.start_date = start_date or None
	if due_date is not None:
		project.due_date = due_date or None

	project.save(ignore_permissions=is_admin)

	return {"message": _("Project updated successfully."), "name": project.name}


@frappe.whitelist()
def update_project_status(name, status):
	"""Update project status."""
	__roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	if is_viewer and not is_admin and not is_team_member:
		frappe.throw(_("You do not have permission to update status."), frappe.PermissionError)

	if not name or not status:
		frappe.throw(_("Project name and status are required."))

	project = frappe.get_doc("Project", name)
	if not is_admin and project.owner != frappe.session.user:
		frappe.throw(_("You can only update your own projects."), frappe.PermissionError)

	project.status = status
	project.save(ignore_permissions=is_admin)

	return {"message": _("Project status updated successfully."), "name": project.name}


@frappe.whitelist()
def add_project_update(name, update_title, update_description=None, status=None):
	"""Add a project update."""
	__roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	if is_viewer and not is_admin and not is_team_member:
		frappe.throw(_("You do not have permission to add updates."), frappe.PermissionError)

	if not name or not update_title:
		frappe.throw(_("Project name and update title are required."))

	project = frappe.get_doc("Project", name)
	if not is_admin and project.owner != frappe.session.user:
		frappe.throw(_("You can only update your own projects."), frappe.PermissionError)

	update = project.append("project_updates", {
		"update_title": update_title,
		"update_description": update_description or "",
		"update_date": frappe.utils.today(),
		"updated_by": frappe.session.user,
	})
	project.save(ignore_permissions=is_admin)

	return {"message": _("Project update added successfully."), "update_name": update.name}


@frappe.whitelist(allow_guest=True)
def get_all_public_stats():
	"""Get public stats for landing page (no login required)."""
	approved = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
	filters = {}
	if approved:
		filters["status"] = approved

	total_projects = frappe.db.count("Project", filters=filters)
	total_teams = frappe.db.count("Team", filters={"is_active": 1})
	total_technologies = frappe.db.count("Technology")
	total_categories = frappe.db.count("Project Category")

	featured = frappe.get_all("Project",
		filters=filters,
		fields=["name", "project_title", "status", "team", "project_category", "creation"],
		limit=6,
		order_by="creation desc"
	)
	for p in featured:
		if p.status:
			s = frappe.get_cached_doc("Project Status", p.status)
			p.status_name = s.status_name
			p.status_color = s.color

	categories = frappe.get_all("Project Category",
		fields=["name", "category_name", "description"])
	technologies = frappe.get_all("Technology",
		fields=["name", "technology_name", "description"])
	statuses = frappe.get_all("Project Status",
		fields=["name", "status_name", "color"])

	return {
		"total_projects": total_projects,
		"total_teams": total_teams,
		"total_technologies": total_technologies,
		"total_categories": total_categories,
		"featured_projects": featured,
		"categories": categories,
		"technologies": technologies,
		"statuses": statuses,
	}


@frappe.whitelist(allow_guest=True)
def get_reports():
	"""Get report data for the Reports page."""
	try:
		filters, is_admin, is_viewer = _get_visible_filters()

		# Project Summary
		statuses = frappe.get_all("Project Status", fields=["name", "status_name", "color"])
		status_summary = []
		for s in statuses:
			f = dict(filters)
			f["status"] = s.name
			count = frappe.db.count("Project", filters=f)
			status_summary.append({
				"status": s.status_name,
				"count": count,
				"color": s.color,
			})

		# Category summary
		categories = frappe.get_all("Project Category", fields=["name", "category_name"])
		category_summary = []
		for c in categories:
			f = dict(filters)
			f["project_category"] = c.name
			count = frappe.db.count("Project", filters=f)
			if count:
				category_summary.append({"category": c.category_name, "count": count})

		# Team summary
		teams = frappe.get_all("Team", fields=["name", "team_name"])
		team_summary = []
		for t in teams:
			count = frappe.db.count("Project", filters={**filters, "team": t.name})
			if count:
				team_summary.append({"team": t.team_name, "count": count})

		# Completed projects
		completed = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
		completed_projects = []
		if completed:
			f = dict(filters)
			f["status"] = completed
			completed_projects = frappe.get_all("Project",
				filters=f,
				fields=["name", "project_title", "team", "completion_date", "owner",
						"project_category", "priority"],
				order_by="completion_date desc",
				limit=50
			)

		# GitHub report
		repos = frappe.get_all("GitHub Repository",
			fields=["repository_name", "repository_url", "default_branch", "languages", "creation"],
			order_by="creation desc",
			limit=50
		)

		return {
			"status_summary": status_summary,
			"category_summary": category_summary,
			"team_summary": team_summary,
			"completed_projects": completed_projects,
			"github_repos": repos,
			"total_projects": frappe.db.count("Project", filters=filters),
		}
	except Exception as e:
		frappe.log_error(f"Error in get_reports: {str(e)}", "get_reports Error")
		return {
			"status_summary": [],
			"category_summary": [],
			"team_summary": [],
			"completed_projects": [],
			"github_repos": [],
			"total_projects": 0,
			"error": str(e)
		}


# Upload utilities
@frappe.whitelist()
def upload_file():
	"""Handle file upload via Frappe's upload API."""
	from frappe.handler import upload_file as frappe_upload
	return frappe_upload()


@frappe.whitelist()
def get_user_notifications():
	"""Get notifications for the current user."""
	user = frappe.session.user
	if user == "Guest":
		return {"notifications": []}

	__roles_user, is_admin, __roles_user_tm, __roles_user2 = _get_user_role_info()
	notifications = []

	# Updates on user's projects
	my_projects = frappe.get_all("Project", filters={"owner": user}, pluck="name")
	if my_projects:
		updates = frappe.db.get_all("Project Update",
			filters={"parent": ["in", my_projects]},
			fields=["name", "parent", "update_title", "update_description",
					"update_date", "updated_by"],
			order_by="update_date desc",
			limit=10
		)
		for u in updates:
			title = frappe.db.get_value("Project", u.parent, "project_title")
			notifications.append({
				"type": "update",
				"title": f"Update on \"{title}\": {u.update_title}",
				"description": u.update_description or "",
				"date": str(u.update_date) if u.update_date else "",
				"project": u.parent,
			})

	if is_admin:
		recent = frappe.get_all("Project",
			fields=["name", "project_title", "owner", "creation"],
			limit=10,
			order_by="creation desc"
		)
		for p in recent:
			notifications.append({
				"type": "submission",
				"title": f"New project: \"{p.project_title}\" by {p.owner}",
				"description": "",
				"date": str(p.creation) if p.creation else "",
				"project": p.name,
			})

	notifications.sort(key=lambda n: n.get("date", ""), reverse=True)
	return {"notifications": notifications[:20]}
