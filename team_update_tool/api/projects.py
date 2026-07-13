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
    
            "files": files,
            "github_info": github_info,
            "github_repository": project.github_repository
        }
    
    except Exception as e:
        frappe.log_error(f"Error getting gallery data: {str(e)}", "get_project_gallery_data Error")
        return {"error": str(e)}
