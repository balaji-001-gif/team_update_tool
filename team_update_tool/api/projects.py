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
	"""Get base filters for View-Only Users.
	Returns empty filters for all user types so all projects are visible to everyone.
	"""
	roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
	# Don't filter by status - show all projects to all users (admin, team member, and view-only)
	filters = {}
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
			order_by="modified desc",
			ignore_permissions=True
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

		total = len(frappe.get_all("Project", filters=filters, pluck="name", ignore_permissions=True))

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
		except Exception as e:
			frappe.log_error(f"Error loading GitHub repo {project.github_repository}: {str(e)}", "get_project_detail GitHub Error")
			# Return basic info from the field if doc not found
			github_info = {
				"name": project.github_repository,
				"repository_url": "",
				"repository_name": "GitHub Repository",
				"commit_hash": "",
				"default_branch": "main",
				"languages": "",
			}

	# Team name
	team_name = project.team
	try:
		team_doc = frappe.get_cached_doc("Team", project.team)
		team_name = team_doc.team_name
	except Exception:
		pass

	# README content - Fetch for all users (admin and view-only)
	readme = {"readme_content": "", "readme_file": ""}
	try:
		# Try direct SQL query to bypass any permission issues
		readme_doc = frappe.db.sql("""
			SELECT readme_content, readme_file 
			FROM `tabProject Readme` 
			WHERE project = %s 
			LIMIT 1
		""", (name,), as_dict=1)
		
		if readme_doc and len(readme_doc) > 0:
			readme = {
				"readme_content": readme_doc[0].get("readme_content") or "",
				"readme_file": readme_doc[0].get("readme_file") or "",
			}
	except Exception as e:
		frappe.log_error(f"Error getting README: {str(e)}", "get_project_detail README Error")
	
	# Also check for readme_content directly in project (if stored as field)
	if not readme.get("readme_content") and hasattr(project, 'readme_content') and project.readme_content:
		readme["readme_content"] = project.readme_content

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
	try:
		filters, is_admin, is_viewer = _get_visible_filters()

		total_projects = len(frappe.get_all("Project", filters=filters, pluck="name", ignore_permissions=True))

		# Status-wise counts (even zero)
		status_counts = []
		try:
			statuses = frappe.get_all("Project Status", fields=["name", "status_name", "color"], order_by="status_name asc", ignore_permissions=True)
			for s in statuses:
				f = dict(filters)
				f["status"] = s.name
				count = len(frappe.get_all("Project", filters=f, pluck="name", ignore_permissions=True))
				status_counts.append({
					"name": s.status_name,
					"slug": s.name,
					"count": count,
					"color": s.color,
				})
		except Exception:
			status_counts = []

		# Category counts
		category_counts = []
		try:
			categories = frappe.get_all("Project Category", fields=["name", "category_name"], ignore_permissions=True)
			for c in categories:
				f = dict(filters)
				f["project_category"] = c.name
				count = len(frappe.get_all("Project", filters=f, pluck="name", ignore_permissions=True))
				if count:
					category_counts.append({
						"name": c.category_name,
						"count": count,
					})
		except Exception:
			pass

		# Latest projects
		recent = []
		try:
			recent = frappe.get_all("Project",
				filters=filters,
				fields=["name", "project_title", "status", "owner", "creation", "modified"],
				limit=6,
				order_by="modified desc",
				ignore_permissions=True
			)
			for p in recent:
				if p.status:
					try:
						s = frappe.get_cached_doc("Project Status", p.status)
						p.status_name = s.status_name
						p.status_color = s.color
					except Exception:
						pass
		except Exception:
			recent = []

		# Recent GitHub uploads
		recent_repos = []
		try:
			recent_repos = frappe.get_all("GitHub Repository",
				fields=["name", "repository_name", "repository_url", "creation"],
				limit=5,
				order_by="creation desc",
				ignore_permissions=True
			)
		except Exception:
			recent_repos = []

		# Recent screenshots
		recent_screenshots = []
		try:
			projects = frappe.get_all("Project", filters=filters, pluck="name", ignore_permissions=True)
			for p_name in projects[:10]:
				try:
					doc = frappe.get_cached_doc("Project", p_name)
					for s in doc.screenshots or []:
						recent_screenshots.append({
							"screenshot": s.screenshot,
							"caption": s.caption or "",
							"project": p_name,
							"project_title": getattr(doc, "project_title", p_name),
						})
						if len(recent_screenshots) >= 6:
							break
					if len(recent_screenshots) >= 6:
						break
				except Exception:
					continue
			recent_screenshots.reverse()
		except Exception:
			recent_screenshots = []

		# Team and technology counts
		total_teams = 0
		total_technologies = 0
		total_categories = 0
		try:
			total_teams = len(frappe.get_all("Team", filters={"is_active": 1}, pluck="name", ignore_permissions=True))
			total_technologies = len(frappe.get_all("Technology", pluck="name", ignore_permissions=True))
			total_categories = len(frappe.get_all("Project Category", pluck="name", ignore_permissions=True))
		except Exception:
			pass

		# User's own projects
		my_projects = 0
		if frappe.session.user != "Guest" and not is_viewer:
			try:
				my_projects = len(frappe.get_all("Project", filters={"owner": frappe.session.user}, pluck="name", ignore_permissions=True))
			except Exception:
				pass

		# Recent documents (files)
		recent_documents = []
		try:
			for p_name in projects[:10]:
				try:
					doc = frappe.get_cached_doc("Project", p_name)
					for f in doc.project_files or []:
						recent_documents.append({
							"file": f.file,
							"file_name": f.file_name or f.file,
							"file_type": f.file_type or "",
							"project": p_name,
							"project_title": getattr(doc, "project_title", p_name),
						})
						if len(recent_documents) >= 5:
							break
					if len(recent_documents) >= 5:
						break
				except Exception:
					continue
			recent_documents.reverse()
		except Exception:
			recent_documents = []

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
	except Exception as e:
		frappe.log_error(f"Error in get_dashboard_stats: {str(e)}", "get_dashboard_stats Error")
		return {
			"total_projects": 0,
			"total_teams": 0,
			"total_technologies": 0,
			"total_categories": 0,
			"my_projects": 0,
			"status_counts": [],
			"category_counts": [],
			"recent_projects": [],
			"recent_repos": [],
			"recent_screenshots": [],
			"recent_documents": [],
			"is_admin": False,
			"is_viewer": False,
			"error": str(e),
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
		order_by="modified desc",
		ignore_permissions=True
	)
	for p in projects:
		if p.status:
			s = frappe.get_cached_doc("Project Status", p.status)
			p.status_name = s.status_name
			p.status_color = s.color
	return projects


@frappe.whitelist(allow_guest=True)
def get_repositories(limit=20, offset=0):
	"""Get GitHub repositories - fetches from GitHub Repository doctype or Project.github_repository field."""
	try:
		repos = frappe.get_all("GitHub Repository",
			fields=["name", "repository_url", "repository_name", "commit_hash",
					"default_branch", "languages", "creation"],
			limit=limit,
			start=offset,
			order_by="creation desc",
			ignore_permissions=True
		)
		total = len(frappe.get_all("GitHub Repository", pluck="name", ignore_permissions=True))
		
		# If no GitHub Repository records, fetch from projects with github_repository field
		if total == 0:
			projects_with_github = frappe.get_all("Project",
				fields=["name", "project_title", "github_repository", "creation"],
				filters={"github_repository": ["is", "set"]},
				limit=limit,
				start=offset,
				order_by="creation desc",
				ignore_permissions=True
			)
			repos = []
			for p in projects_with_github:
				repo_name = p.github_repository
				# Try to get the GitHub Repository doc
				try:
					repo_doc = frappe.get_cached_doc("GitHub Repository", repo_name)
					repos.append({
						"name": repo_doc.name,
						"repository_url": repo_doc.repository_url or "",
						"repository_name": repo_doc.repository_name or p.project_title,
						"commit_hash": repo_doc.commit_hash or "",
						"default_branch": repo_doc.default_branch or "main",
						"languages": repo_doc.languages or "",
						"creation": str(p.creation),
					})
				except Exception:
					# GitHub Repository doc doesn't exist, use project info
					repos.append({
						"name": repo_name,
						"repository_url": "",
						"repository_name": p.project_title or "GitHub Repository",
						"commit_hash": "",
						"default_branch": "main",
						"languages": "",
						"creation": str(p.creation),
					})
			total = len(repos)
		
		return {"repositories": repos, "total": total, "has_more": (offset + limit) < total}
	except Exception as e:
		frappe.log_error(f"Error fetching repositories: {str(e)}", "get_repositories Error")
		return {"repositories": [], "total": 0, "has_more": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_documents(limit=20, offset=0):
	"""Get all project files/documents and README files grouped by project."""
	try:
		roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
		
		# Validate limit and offset
		limit = min(max(int(limit) if limit else 20, 1), 100)
		offset = max(int(offset) if offset else 0, 0)
		
		# Check if Project doctype exists
		if not frappe.db.exists("DocType", "Project"):
			frappe.log_error("Project DocType does not exist in database", "get_documents Error")
			return {"documents": [], "total": 0, "has_more": False, "error": "Project doctype not found"}
		
		# Build filters - show all projects to all users (no status restriction)
		filters = {}
		# Removed: No status filtering for view-only users - everyone can see all documents
		
		all_files = []
		
		# Method 1: Fetch from Project Files doctype directly
		try:
			file_records = frappe.get_all("Project Files",
				fields=["name", "file", "file_name", "file_type", "file_description", "project"],
				ignore_permissions=True
			)
			
			for fr in file_records:
				# Get project title and status
				project_title = fr.project or ""
				status_name = "Unknown"
				status_color = "#6b7280"
				is_approved = False
				
				try:
					if fr.project:
						proj_doc = frappe.get_cached_doc("Project", fr.project)
						project_title = getattr(proj_doc, "project_title", fr.project)
						if proj_doc.status:
							try:
								status_doc = frappe.get_cached_doc("Project Status", proj_doc.status)
								status_name = status_doc.status_name
								status_color = status_doc.color
								is_approved = (status_name.lower() == "approved")
							except:
								status_name = proj_doc.status
				except:
					pass
				
				if fr.file:
					all_files.append({
						"file": fr.file,
						"file_name": fr.file_name or fr.file,
						"file_type": fr.file_type or "",
						"description": fr.file_description or "",
						"project": fr.project or "",
						"project_title": project_title,
						"status": status_name,
						"status_color": status_color,
						"is_approved": is_approved,
						"document_type": "file",
					})
		except Exception as file_error:
			frappe.log_error(f"Error fetching from Project Files: {str(file_error)}", "get_documents Error")
		
		# Method 2: Fetch from Project Readme doctype directly
		try:
			readme_records = frappe.get_all("Project Readme",
				fields=["name", "readme_content", "readme_file", "project"],
				ignore_permissions=True
			)
			
			for rm in readme_records:
				# Get project title and status
				project_title = rm.project or ""
				status_name = "Unknown"
				status_color = "#6b7280"
				is_approved = False
				
				try:
					if rm.project:
						proj_doc = frappe.get_cached_doc("Project", rm.project)
						project_title = getattr(proj_doc, "project_title", rm.project)
						if proj_doc.status:
							try:
								status_doc = frappe.get_cached_doc("Project Status", proj_doc.status)
								status_name = status_doc.status_name
								status_color = status_doc.color
								is_approved = (status_name.lower() == "approved")
							except:
								status_name = proj_doc.status
				except:
					pass
				
				readme_desc = ""
				if rm.readme_content:
					readme_desc = rm.readme_content[:200] + "..." if len(rm.readme_content) > 200 else rm.readme_content
				readme_name = rm.readme_file.split("/")[-1] if rm.readme_file else "README - " + project_title
				
				all_files.append({
					"file": rm.readme_file or "",
					"file_name": readme_name,
					"file_type": "md",
					"description": readme_desc,
					"project": rm.project or "",
					"project_title": project_title,
					"status": status_name,
					"status_color": status_color,
					"is_approved": is_approved,
					"document_type": "readme",
					"readme_content": rm.readme_content or "",
				})
		except Exception as readme_error:
			frappe.log_error(f"Error fetching from Project Readme: {str(readme_error)}", "get_documents Error")
		
		# Method 3: Also check for files in Project child tables as fallback
		projects = frappe.get_all("Project", filters=filters, pluck="name", ignore_permissions=True)
		for p_name in projects:
			try:
				doc = frappe.get_cached_doc("Project", p_name)
					
				# Get project status info
				status_name = "Unknown"
				status_color = "#6b7280"
				is_approved = False
				if doc.status:
					try:
						status_doc = frappe.get_cached_doc("Project Status", doc.status)
						status_name = status_doc.status_name
						status_color = status_doc.color
						is_approved = (status_name.lower() == "approved")
					except:
						status_name = doc.status
				
				project_title = getattr(doc, "project_title", p_name)
					
				# Get project files
				for f in doc.project_files or []:
					all_files.append({
						"file": f.file,
						"file_name": f.file_name or f.file,
						"file_type": f.file_type or "",
						"description": f.file_description or "",
						"project": p_name,
						"project_title": project_title,
						"status": status_name,
						"status_color": status_color,
						"is_approved": is_approved,
						"document_type": "file",
					})
				
				# Get README files from Project Readme doctype
				try:
					readme_list = frappe.get_all("Project Readme",
						filters={"project": p_name},
						fields=["name", "readme_content", "readme_file"],
                                                ignore_permissions=True
					)
					for rm in readme_list:
						readme_desc = ""
						if rm.readme_content:
							readme_desc = rm.readme_content[:200] + "..." if len(rm.readme_content) > 200 else rm.readme_content
						readme_name = rm.readme_file.split("/")[-1] if rm.readme_file else "README - " + project_title
						all_files.append({
							"file": rm.readme_file or "",
							"file_name": readme_name,
							"file_type": "md",
							"description": readme_desc,
							"project": p_name,
							"project_title": project_title,
							"status": status_name,
							"status_color": status_color,
							"is_approved": is_approved,
							"document_type": "readme",
							"readme_content": rm.readme_content or "",
						})
				except Exception:
					pass
						
			except Exception as proj_error:
				frappe.log_error(f"Error loading project {p_name}: {str(proj_error)}", "get_documents Project Error")
				continue

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
		roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
		
		# Validate limit and offset
		limit = min(max(int(limit) if limit else 30, 1), 100)
		offset = max(int(offset) if offset else 0, 0)
		
		# Check if Project doctype exists
		if not frappe.db.exists("DocType", "Project"):
			frappe.log_error("Project DocType does not exist in database", "get_gallery Error")
			return {"screenshots": [], "total": 0, "has_more": False, "error": "Project doctype not found"}
		
		all_screenshots = []
		
		# Method 1: Try to fetch from Project Screenshots doctype directly
		try:
			# Get all screenshots from Project Screenshots doctype
			screenshot_records = frappe.get_all("Project Screenshots",
				fields=["name", "screenshot", "caption", "screenshot_type", "project"]
			)
			
			for ss in screenshot_records:
				# Get project title
				project_title = ss.project
				try:
					if ss.project:
						proj_doc = frappe.get_cached_doc("Project", ss.project)
						project_title = getattr(proj_doc, "project_title", ss.project)
				except:
					pass
				
				if ss.screenshot:
					all_screenshots.append({
						"screenshot": ss.screenshot,
						"caption": ss.caption or "",
						"screenshot_type": ss.screenshot_type or "",
						"project": ss.project or "",
						"project_title": project_title,
					})
		except Exception as ss_error:
			frappe.log_error(f"Error fetching from Project Screenshots: {str(ss_error)}", "get_gallery Error")
		
		# Method 2: Also check for screenshots in Project child table
		try:
			projects = frappe.get_all("Project", pluck="name", ignore_permissions=True)
			for p_name in projects:
				try:
					doc = frappe.get_cached_doc("Project", p_name)
					for s in doc.screenshots or []:
						# Check if this screenshot is already added
						screenshot_url = s.screenshot
						if screenshot_url and not any(ss.get('screenshot') == screenshot_url for ss in all_screenshots):
							all_screenshots.append({
								"screenshot": s.screenshot,
								"caption": s.caption or "",
								"screenshot_type": s.screenshot_type or "",
								"project": p_name,
								"project_title": getattr(doc, "project_title", p_name),
							})
				except Exception as proj_error:
					continue
		except Exception as proj_error:
			frappe.log_error(f"Error loading project screenshots: {str(proj_error)}", "get_gallery Error")
		
		all_screenshots.reverse()
		total = len(all_screenshots)
		limited = all_screenshots[offset:offset + limit]
		
		return {"screenshots": limited, "total": total, "has_more": (offset + limit) < total}
	except Exception as e:
		frappe.log_error(f"Error in get_gallery: {str(e)}", "get_gallery Error")
		return {"screenshots": [], "total": 0, "has_more": False, "error": str(e)}

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
	# Don't filter by status - show all projects to all users
	filters = {}

	total_projects = len(frappe.get_all("Project", filters=filters, pluck="name", ignore_permissions=True))
	total_teams = len(frappe.get_all("Team", filters={"is_active": 1}, pluck="name", ignore_permissions=True))
	total_technologies = len(frappe.get_all("Technology", pluck="name", ignore_permissions=True))
	total_categories = len(frappe.get_all("Project Category", pluck="name", ignore_permissions=True))

	featured = frappe.get_all("Project",
		filters=filters,
		fields=["name", "project_title", "status", "team", "project_category", "creation"],
		limit=6,
		order_by="creation desc",
		ignore_permissions=True
	)
	for p in featured:
		if p.status:
			s = frappe.get_cached_doc("Project Status", p.status)
			p.status_name = s.status_name
			p.status_color = s.color

	categories = frappe.get_all("Project Category",
		fields=["name", "category_name", "description"],
		ignore_permissions=True)
	technologies = frappe.get_all("Technology",
		fields=["name", "technology_name", "description"],
		ignore_permissions=True)
	statuses = frappe.get_all("Project Status",
		fields=["name", "status_name", "color"],
		ignore_permissions=True)
	teams = frappe.get_all("Team",
		fields=["name", "team_name"],
		filters={"is_active": 1},
		ignore_permissions=True)

	return {
		"total_projects": total_projects,
		"total_teams": total_teams,
		"total_technologies": total_technologies,
		"total_categories": total_categories,
		"featured_projects": featured,
		"categories": categories,
		"technologies": technologies,
		"statuses": statuses,
		"teams": teams,
	}


@frappe.whitelist(allow_guest=True)
def get_reports():
	"""Get report data for the Reports page."""
	try:
		filters, is_admin, is_viewer = _get_visible_filters()

		# Project Summary
		status_summary = []
		try:
			statuses = frappe.get_all("Project Status", fields=["name", "status_name", "color"], ignore_permissions=True)
			for s in statuses:
				f = dict(filters)
				f["status"] = s.name
				count = len(frappe.get_all("Project", filters=f, pluck="name", ignore_permissions=True))
				status_summary.append({
					"status": s.status_name or s.name,
					"count": count,
					"color": s.color or "#6b7280",
				})
		except Exception as e:
			frappe.log_error(f"Error getting status summary: {str(e)}", "get_reports Error")

		# Category summary
		category_summary = []
		try:
			categories = frappe.get_all("Project Category", fields=["name", "category_name"], ignore_permissions=True)
			for c in categories:
				f = dict(filters)
				f["project_category"] = c.name
				count = len(frappe.get_all("Project", filters=f, pluck="name", ignore_permissions=True))
				if count:
					category_summary.append({"category": c.category_name or c.name, "count": count})
		except Exception as e:
			frappe.log_error(f"Error getting category summary: {str(e)}", "get_reports Error")

		# Team summary
		team_summary = []
		try:
			teams = frappe.get_all("Team", fields=["name", "team_name"], ignore_permissions=True)
			for t in teams:
				count = len(frappe.get_all("Project", filters={**filters, "team": t.name}, pluck="name", ignore_permissions=True))
				if count:
					team_summary.append({"team": t.team_name or t.name, "count": count})
		except Exception as e:
			frappe.log_error(f"Error getting team summary: {str(e)}", "get_reports Error")

		# Completed projects
		completed_projects = []
		try:
			completed = frappe.db.get_value("Project Status", {"status_name": "Approved"}, "name")
			if completed:
				f = dict(filters)
				f["status"] = completed
				completed_projects = frappe.get_all("Project",
					filters=f,
					fields=["name", "project_title", "team", "completion_date", "owner",
							"project_category", "priority"],
					order_by="completion_date desc",
					limit=50,
					ignore_permissions=True
				)
		except Exception as e:
			frappe.log_error(f"Error getting completed projects: {str(e)}", "get_reports Error")

		# GitHub report
		github_repos = []
		try:
			repos = frappe.get_all("GitHub Repository",
				fields=["name", "repository_name", "repository_url", "default_branch", "languages", "commit_hash", "creation"],
				order_by="creation desc",
				limit=50,
				ignore_permissions=True
			)
			for r in repos:
				github_repos.append({
					"name": r.name,
					"repository_name": r.repository_name or r.name,
					"repository_url": r.repository_url or "",
					"default_branch": r.default_branch or "main",
					"languages": r.languages or "",
					"commit_hash": r.commit_hash[:8] if r.commit_hash else "",
					"creation": str(r.creation) if r.creation else ""
				})
		except Exception as e:
			frappe.log_error(f"Error getting GitHub repos: {str(e)}", "get_reports Error")

		# Total projects
		total_projects = 0
		try:
			total_projects = len(frappe.get_all("Project", filters=filters, pluck="name", ignore_permissions=True))
		except Exception as e:
			frappe.log_error(f"Error counting projects: {str(e)}", "get_reports Error")

		return {
			"status_summary": status_summary,
			"category_summary": category_summary,
			"team_summary": team_summary,
			"completed_projects": completed_projects,
			"github_repos": github_repos,
			"total_projects": total_projects,
		}
	except Exception as e:
		frappe.log_error(f"Error in get_reports: {str(e)}", "get_reports Error")
		# Return empty data instead of error to show empty state gracefully
		return {
			"status_summary": [],
			"category_summary": [],
			"team_summary": [],
			"completed_projects": [],
			"github_repos": [],
			"total_projects": 0,
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
	my_projects = frappe.get_all("Project", filters={"owner": user}, pluck="name", ignore_permissions=True)
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
			order_by="creation desc",
                        ignore_permissions=True
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
