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
        # Build SQL query directly to bypass all permission hooks
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        if category:
            conditions.append("project_category = %s")
            params.append(category)
        if team:
            conditions.append("team = %s")
            params.append(team)
        if search:
            conditions.append("(project_title LIKE %s OR description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Count total
        count_sql = f"SELECT COUNT(*) as total FROM `tabProject` WHERE {where_clause}"
        total_result = frappe.db.sql(count_sql, params, as_dict=True)
        total = total_result[0].total if total_result else 0

        # Get projects with pagination
        fields_list = "name, project_title, status, team, priority, project_category, creation, start_date, completion_date, owner, modified"
        limit = min(int(limit) if limit else 20, 100)
        offset = max(int(offset) if offset else 0, 0)
        
        sql = f"SELECT {fields_list} FROM `tabProject` WHERE {where_clause} ORDER BY modified DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        projects = frappe.db.sql(sql, params, as_dict=True)

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
                project_doc = frappe.get_cached_doc("Project", p.name, ignore_permissions=True)
                p.screenshot_preview = ""
                if project_doc.screenshots and len(project_doc.screenshots) > 0:
                    p.screenshot_preview = project_doc.screenshots[0].screenshot
                p.technology_count = len(project_doc.technologies or [])
                p.update_count = len(project_doc.project_updates or [])
            except:
                p.screenshot_preview = ""
                p.technology_count = 0
                p.update_count = 0

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
        # Use get_cached_doc with ignore_permissions to load all child table data
        project = frappe.get_cached_doc("Project", name, ignore_permissions=True)
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

    # Screenshots - query Project Screenshots doctype with 'project' field
    screenshots = []
    try:
        ss_records = frappe.get_all("Project Screenshots",
            fields=["name", "screenshot", "caption", "screenshot_type", "project"],
            filters={"project": name},
            ignore_permissions=True
        )
        for s in ss_records:
            screenshots.append({
                "screenshot": s.screenshot,
                "caption": s.caption,
                "screenshot_type": s.screenshot_type,
            })
    except Exception as e:
        frappe.log_error(f"Error fetching screenshots: {str(e)}", "get_project_detail Error")

    # Files/Documents - Get from project_files child table
    files = []
    for f in project.project_files or []:
        # Build full URL for the file if it's a relative path
        file_url = f.file or ""
        if file_url and not file_url.startswith('http://') and not file_url.startswith('https://'):
            file_url = frappe.request.host_url.rstrip('/') + '/' + file_url.lstrip('/') if hasattr(frappe, 'request') and frappe.request else file_url
        
        files.append({
            "file": file_url,
            "file_name": f.file_name,
            "file_type": f.file_type,
            "description": f.file_description,
        })
    
    # Also check for files in standalone Project Files doctype
    # Check both 'parent' and 'project' fields
    if not files:
        try:
            if frappe.db.exists("DocType", "Project Files"):
                # First try with 'parent' field (child table format)
                file_records = frappe.get_all("Project Files",
                    filters={"parent": name},
                    fields=["file", "file_name", "file_type", "file_description"],
                    ignore_permissions=True
                )
                for f in file_records:
                    file_url = f.file or ""
                    if file_url and not file_url.startswith('http://') and not file_url.startswith('https://'):
                        file_url = frappe.request.host_url.rstrip('/') + '/' + file_url.lstrip('/') if hasattr(frappe, 'request') and frappe.request else file_url
                    
                    files.append({
                        "file": file_url,
                        "file_name": f.file_name,
                        "file_type": f.file_type,
                        "description": f.file_description,
                    })
                
                # If still empty, try with 'project' field (standalone format)
                if not files:
                    file_records = frappe.get_all("Project Files",
                        filters={"project": name},
                        fields=["file", "file_name", "file_type", "file_description"],
                        ignore_permissions=True
                    )
                    for f in file_records:
                        file_url = f.file or ""
                        if file_url and not file_url.startswith('http://') and not file_url.startswith('https://'):
                            file_url = frappe.request.host_url.rstrip('/') + '/' + file_url.lstrip('/') if hasattr(frappe, 'request') and frappe.request else file_url
                        
                        files.append({
                            "file": file_url,
                            "file_name": f.file_name,
                            "file_type": f.file_type,
                            "description": f.file_description,
                        })
        except Exception as e:
            frappe.log_error(f"Error fetching files: {str(e)}", "get_project_detail Error")

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
    github_url = project.github_repository or ""
    
    # Check if it is a URL or a doc link
    if "github.com" in github_url.lower():
        # It is a URL, extract info
        import re
        match = re.search(r'github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)', github_url, re.IGNORECASE)
        if match:
            repo_owner = match.group(1)
            repo_name = match.group(2).replace('.git', '')
            github_info = {
                "name": f"{repo_owner}/{repo_name}",
                "repository_url": github_url,
                "repository_name": repo_name,
                "commit_hash": "",
                "default_branch": "main",
                "languages": "",
            }
    elif github_url:
        # Try to fetch as doc link
        try:
            repo = frappe.get_cached_doc("GitHub Repository", github_url)
            github_info = {
                "name": repo.name,
                "repository_url": repo.repository_url,
                "repository_name": repo.repository_name,
                "commit_hash": repo.commit_hash or "",
                "default_branch": repo.default_branch or "main",
                "languages": repo.languages or "",
            }
        except Exception as e:
            # Return basic info
            github_info = {
                "name": github_url,
                "repository_url": github_url,
                "repository_name": github_url.split('/')[-1] if '/' in github_url else github_url,
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
        # Validate limit and offset
        limit = min(max(int(limit) if limit else 20, 1), 100)
        offset = max(int(offset) if offset else 0, 0)
        
        repos = []
        total = 0
        
        # Method 1: Try to fetch from GitHub Repository doctype
        try:
            repos = frappe.get_all("GitHub Repository",
                fields=["name", "repository_url", "repository_name", "commit_hash",
                        "default_branch", "languages", "creation"],
                limit_page_length=limit,
                ignore_permissions=True
            )
            
            # Get total count
            total = len(frappe.get_all("GitHub Repository", pluck="name", ignore_permissions=True))
        except Exception as repo_error:
            frappe.log_error(f"Error fetching GitHub Repository: {str(repo_error)}", "get_repositories Error")
        
        # Method 2: If no GitHub Repository records, fetch from projects with github_repository field
        if total == 0:
            try:
                projects_with_github = frappe.get_all("Project",
                    fields=["name", "project_title", "github_repository", "creation"],
                    filters={"github_repository": ["is", "set"]},
                    ignore_permissions=True
                )
                
                total = len(projects_with_github)
                
                # Apply pagination manually
                paginated = projects_with_github[offset:offset + limit]
                
                for p in paginated:
                    repo_name = p.github_repository
                    # Try to get the GitHub Repository doc
                    try:
                        repo_doc = frappe.get_cached_doc("GitHub Repository", repo_name, ignore_permissions=True)
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
            except Exception as proj_error:
                frappe.log_error(f"Error fetching projects with github_repository: {str(proj_error)}", "get_repositories Error")
        
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
    import frappe
    
    def build_full_url(screenshot_value):
        """Build a complete URL from screenshot value."""
        if not screenshot_value:
            return None
        
        # If already a full URL, return as is
        if screenshot_value.startswith("http://") or screenshot_value.startswith("https://"):
            return screenshot_value
        
        # Get base URL - try multiple methods
        try:
            base_url = frappe.utils.get_url()
        except:
            base_url = "http://team.update.bizaxl.local"
        
        # Handle private files first
        if "private/files" in screenshot_value:
            # For private files, we need to use the web proxy
            path = screenshot_value.replace("/private/files/", "").replace("private/files/", "")
            return base_url + "/files/" + path
        
        # Remove leading slash if present for joining
        screenshot_value = screenshot_value.lstrip("/")
        
        # Handle files directory - direct file access
        if screenshot_value.startswith("files/"):
            return base_url + "/" + screenshot_value
        elif screenshot_value.startswith("files/"):
            return base_url + "/" + screenshot_value
        else:
            return base_url + "/files/" + screenshot_value
    
    try:
        all_screenshots = []
        debug_info = {}
        
        # Validate limit and offset
        limit = min(max(int(limit) if limit else 30, 1), 100)
        offset = max(int(offset) if offset else 0, 0)
        
        # Get base URL for debug
        try:
            debug_info["base_url"] = frappe.utils.get_url()
        except:
            debug_info["base_url"] = "http://team.update.bizaxl.local"
        
        # Helper function to get project title
        def get_project_title(project_name):
            """Get the display title for a project."""
            if not project_name:
                return "Project"
            try:
                proj_doc = frappe.get_doc("Project", project_name, ignore_permissions=True)
                # Try project_title field first
                title = proj_doc.get("project_title") if proj_doc else None
                if not title:
                    title = proj_doc.get("title") if proj_doc else None
                if not title:
                    title = proj_doc.get("project_name") if proj_doc else None
                if not title:
                    title = proj_doc.get("name") if proj_doc else project_name
                return title
            except Exception as e:
                debug_info["project_error_" + str(project_name)] = str(e)
                return project_name
        
        # Method 1: Fetch from Project Screenshots doctype directly
        try:
            screenshot_records = frappe.db.sql("""
                SELECT name, screenshot, caption, screenshot_type, project
                FROM `tabProject Screenshots`
                WHERE screenshot IS NOT NULL AND screenshot != ''
                ORDER BY creation DESC
            """, as_dict=True)
            
            debug_info["method1_total"] = len(screenshot_records)
            
            for ss in screenshot_records:
                if not ss.screenshot:
                    continue
                
                # Debug: store original screenshot value
                debug_info["method1_screenshot_" + str(ss.name)] = ss.screenshot
                
                # Get project title
                project_id = ss.project or ""
                project_title = get_project_title(project_id) if project_id else "Project"
                
                # Build full URL
                full_url = build_full_url(ss.screenshot)
                debug_info["method1_url_" + str(ss.name)] = full_url
                
                if full_url:
                    debug_info["method1_count"] = debug_info.get("method1_count", 0) + 1
                    all_screenshots.append({
                        "screenshot": full_url,
                        "caption": ss.caption or "",
                        "screenshot_type": ss.screenshot_type or "",
                        "project": project_id,
                        "project_title": project_title,
                        "original_path": ss.screenshot,
                    })
        except Exception as ss_error:
            debug_info["method1_error"] = str(ss_error)
            frappe.log_error("Error in Method 1 get_gallery: " + str(ss_error), "get_gallery Error")
        
        # Method 2: Fetch from Project child table (screenshots)
        try:
            projects = frappe.db.sql("SELECT name, project_title FROM `tabProject`", as_dict=True)
            debug_info["projects_count"] = len(projects)
            debug_info["projects"] = [p.name for p in projects]
            
            for proj in projects:
                p_name = proj.name
                project_title = proj.project_title or p_name
                
                try:
                    doc = frappe.get_doc("Project", p_name, ignore_permissions=True)
                    child_screenshot_count = 0
                    
                    # Check child table screenshots
                    if doc.screenshots:
                        for s in doc.screenshots:
                            if not s.screenshot:
                                continue
                            
                            debug_info["method2_screenshot_" + str(p_name)] = s.screenshot
                            
                            # Build full URL
                            full_url = build_full_url(s.screenshot)
                            debug_info["method2_url_" + str(p_name)] = full_url
                            
                            # Check for duplicates
                            if full_url and not any(ss.get("screenshot") == full_url for ss in all_screenshots):
                                child_screenshot_count += 1
                                all_screenshots.append({
                                    "screenshot": full_url,
                                    "caption": s.caption or "",
                                    "screenshot_type": s.screenshot_type or "",
                                    "project": p_name,
                                    "project_title": project_title,
                                    "original_path": s.screenshot,
                                })
                    
                    if child_screenshot_count > 0:
                        debug_info["method2_count"] = debug_info.get("method2_count", 0) + child_screenshot_count
                        debug_info["project_" + p_name + "_screenshots"] = child_screenshot_count
                except Exception as proj_error:
                    debug_info["project_error_" + p_name] = str(proj_error)
                    continue
        except Exception as proj_error:
            debug_info["method2_error"] = str(proj_error)
            frappe.log_error("Error in Method 2 get_gallery: " + str(proj_error), "get_gallery Error")
        
        # Sort by creation (newest first) and apply pagination
        all_screenshots.reverse()
        total = len(all_screenshots)
        limited = all_screenshots[offset:offset + limit]
        
        debug_info["total_screenshots"] = total
        
        return {
            "screenshots": limited, 
            "total": total, 
            "has_more": (offset + limit) < total,
            "debug": debug_info
        }
    except Exception as e:
        frappe.log_error("Error in get_gallery: " + str(e), "get_gallery Error")
        return {
            "screenshots": [], 
            "total": 0, 
            "has_more": False, 
            "error": str(e),
            "debug": {}
        }



@frappe.whitelist()
def create_project_readme(project_name, readme_file=None, readme_content=None):
    """Create or update Project Readme for a project."""
    try:
        __roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
        if is_viewer and not is_admin and not is_team_member:
            return {"error": "Permission denied"}

        if not project_name:
            return {"error": "Project name is required"}

        if not frappe.db.exists("Project", project_name):
            return {"error": "Project not found"}

        project = frappe.get_doc("Project", project_name)
        
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

        readme.save(ignore_permissions=True)

        return {"message": "Project Readme created.", "success": True}
    except Exception as e:
        frappe.log_error(f"Error creating README: {str(e)}", "create_project_readme Error")
        return {"error": str(e)}


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


@frappe.whitelist(allow_guest=True)
def create_project(project_title, team, project_category=None, description=None, tags=None,
                   status=None, priority=None, start_date=None, due_date=None, completion_date=None,
                   github_repository=None, technologies=None):
    """Create a new project from the website."""
    roles, is_admin, is_team_member, is_viewer = _get_user_role_info()
    
    # Check permission - only Admin and Team Member can create projects
    if is_viewer and not is_admin and not is_team_member:
        frappe.throw(_("You do not have permission to create projects."), frappe.PermissionError)
    
    # Validate required fields
    if not project_title:
        frappe.throw(_("Project title is required."))
    if not team:
        frappe.throw(_("Team is required."))
    
    # Verify team exists
    if not frappe.db.exists("Team", team):
        frappe.throw(_("Team '{0}' does not exist.").format(team))
    
    # Get default status if not provided
    if not status:
        status = frappe.db.get_value("Project Status", {"status_name": "Draft"}, "name")
        if not status:
            status = frappe.db.get_value("Project Status", 1, "name")
    
    # Accept github_url from frontend (which sends github_url instead of github_repository)
    if not github_repository:
        github_repository = frappe.form_dict.get('github_url')
    
    # Create project with explicit name
    import hashlib
    name_hash = hashlib.md5((project_title + str(frappe.utils.now())).encode()).hexdigest()[:10]
    project_name = f"PRJ-{name_hash.upper()}"
    
    # Build the project dict
    project_data = {
        "doctype": "Project",
        "name": project_name,
        "project_title": project_title,
        "team": team,
        "status": status,
        "priority": priority or "Medium",
        "owner": frappe.session.user,
    }
    
    if project_category:
        project_data["project_category"] = project_category
    if description:
        project_data["description"] = description
    if tags:
        project_data["tags"] = tags
    if start_date:
        project_data["start_date"] = start_date
    if due_date:
        project_data["due_date"] = due_date
    if completion_date:
        project_data["completion_date"] = completion_date
    
    # Handle GitHub Repository
    github_repo_value = None
    if github_repository:
        import re
        match = re.search(r'github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)', github_repository)
        if match:
            repo_owner = match.group(1)
            repo_name = match.group(2).replace('.git', '')
            repo_full_name = f"{repo_owner}/{repo_name}"
            
            if not frappe.db.exists("GitHub Repository", repo_full_name):
                try:
                    github_repo = frappe.get_doc({
                        "doctype": "GitHub Repository",
                        "repository_name": repo_full_name,
                        "repository_url": github_repository,
                    })
                    github_repo.insert(ignore_permissions=True, ignore_links=True)
                except Exception as e:
                    frappe.log_error(f"Error creating GitHub Repository: {str(e)}", "GitHub Repo Error")
            
            github_repo_value = repo_full_name
        else:
            github_repo_value = github_repository
    
    if github_repo_value:
        project_data["github_repository"] = github_repo_value
    
    # Create and insert project with explicit name
    # Using ignore_naming_series to preserve the explicitly set project name
    project_doc = frappe.get_doc(project_data)
    project_doc.flags.ignore_validate = True
    project_doc.flags.ignore_mandatory = True
    project_doc.flags.ignore_permissions = True
    project_doc.flags.ignore_naming_series = True
    project_doc.insert()
    
    # Log success
    frappe.log_error(f"Project created: {project_name}", "Project Creation")
    
    # Add technologies if provided
    if technologies:
        if isinstance(technologies, str):
            try:
                technologies = frappe.parse_json(technologies)
            except:
                technologies = []
        if isinstance(technologies, list):
            for tech in technologies:
                if tech:
                    frappe.get_doc({
                        "doctype": "Project Technology",
                        "parent": project_name,
                        "parentfield": "technologies",
                        "parenttype": "Project",
                        "technology": tech,
                        "project": project_name
                    }).insert(ignore_permissions=True, ignore_links=True)
    
    # Commit all changes
    frappe.db.commit()
    
    return {
        "message": _("Project created successfully."),
        "name": project_name,
        "success": True
    }



@frappe.whitelist(allow_guest=True)
def add_project_screenshot(project_name, file_url=None, file_name=None, caption=None, screenshot_type=None):
    """Add a screenshot to an existing project."""
    try:
        if not project_name:
            return {"error": "Project name is required"}
        
        if not file_url:
            return {"error": "File URL is required"}
        
        if not frappe.db.exists("Project", project_name):
            return {"error": "Project not found"}
        
        # Log for debugging
        frappe.log_error(f"Screenshot upload - project: {project_name}, file_url: {file_url}", "Screenshot Debug")
        
        # Add screenshot - use Project Screenshots doctype with 'project' field
        screenshot_doc = frappe.get_doc({
            "doctype": "Project Screenshots",
            "project": project_name,
            "screenshot": file_url,
            "caption": caption or file_name or "",
            "screenshot_type": screenshot_type or "UI Screen"
        })
        screenshot_doc.insert(ignore_permissions=True, ignore_links=True)
        
        # Log success
        frappe.log_error(f"Screenshot added - ID: {screenshot_doc.name}, project: {project_name}", "Screenshot Success")
        
        return {"message": "Screenshot added successfully", "success": True}
    
    except Exception as e:
        frappe.log_error(f"Error adding screenshot: {str(e)}", "add_project_screenshot Error")
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def add_project_file(project_name, file_url=None, file_name=None, file_type=None, file_description=None):
    """Add a file/document to an existing project."""
    try:
        if not project_name:
            return {"error": "Project name is required"}
        
        if not file_url:
            return {"error": "File URL is required"}
        
        if not frappe.db.exists("Project", project_name):
            return {"error": "Project not found"}
        
        # Add file - use Project Files doctype with 'project' field
        file_doc = frappe.get_doc({
            "doctype": "Project Files",
            "project": project_name,
            "file": file_url,
            "file_name": file_name or "Document",
            "file_type": file_type or "",
            "file_description": file_description or ""
        })
        file_doc.insert(ignore_permissions=True, ignore_links=True)
        
        return {"message": "File added successfully", "success": True}
    
    except Exception as e:
        frappe.log_error(f"Error adding file: {str(e)}", "add_project_file Error")
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_project_gallery_data(project_name):
    """Get gallery data for a specific project."""
    try:
        if not project_name:
            return {"error": "Project name is required"}
        
        project = frappe.get_doc("Project", project_name)
        
        # Screenshots
        screenshots = []
        for s in project.screenshots or []:
            full_url = s.screenshot
            if full_url and not full_url.startswith('http'):
                full_url = frappe.request.host_url.rstrip('/') + '/' + full_url.lstrip('/')
            
            screenshots.append({
                "name": s.name,
                "screenshot": full_url,
                "caption": s.caption or "",
                "screenshot_type": s.screenshot_type or ""
            })
        
        # Files
        files = []
        for f in project.project_files or []:
            full_url = f.file
            if full_url and not full_url.startswith('http'):
                full_url = frappe.request.host_url.rstrip('/') + '/' + full_url.lstrip('/')
            
            files.append({
                "name": f.name,
                "file": full_url,
                "file_name": f.file_name or "Document",
                "file_type": f.file_type or "",
                "description": f.file_description or ""
            })
        
        # GitHub info
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
            except:
                github_info = {
                    "name": project.github_repository,
                    "repository_url": "",
                }
        
        return {
            "screenshots": screenshots,
            "files": files,
            "github_info": github_info,
            "github_repository": project.github_repository
        }
    
    except Exception as e:
        frappe.log_error(f"Error getting gallery data: {str(e)}", "get_project_gallery_data Error")
        return {"error": str(e)}
