# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def _get_default_status():
    """Return the name of a default Project Status (first available, or creates 'Pending')."""
    status = frappe.db.get_value("Project Status", {"status_name": "Pending"}, "name")
    if status:
        return status
    # Fallback to any existing status
    all_statuses = frappe.get_all("Project Status", fields=["name"], limit=1)
    if all_statuses:
        return all_statuses[0].name
    # If no status exists yet, create one
    doc = frappe.get_doc({"doctype": "Project Status", "status_name": "Pending", "color": "#6b7280"})
    doc.insert(ignore_permissions=True)
    return doc.name


def _get_or_create_github_repository(github_url, branch="main"):
    """Find existing GitHub Repository by URL or create a new one."""
    if not github_url:
        return None

    existing = frappe.db.get_value("GitHub Repository", {"repository_url": github_url}, "name")
    if existing:
        return existing

    # Extract repo name from URL
    repo_name = github_url.rstrip("/").split("/")[-1] if github_url else ""

    doc = frappe.get_doc({
        "doctype": "GitHub Repository",
        "repository_url": github_url,
        "repository_name": repo_name,
        "default_branch": branch or "main",
    })
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def create_project():
    """Create a new Project from the create_project page form.

    Expects POST data with:
      - project_title (required)
      - team (required)
      - project_category
      - priority
      - description
      - start_date, due_date
      - technologies (list of Technology names)
      - github_url, github_branch
    """
    data = frappe.local.form_dict

    user = frappe.session.user
    if user == "Guest":
        frappe.throw(_("Please log in to create a project."), frappe.PermissionError)

    # Validate required fields
    project_title = data.get("project_title")
    team = data.get("team")

    if not project_title:
        frappe.throw(_("Project title is required."))
    if not team:
        frappe.throw(_("Team is required."))

    # Get default status
    status = _get_default_status()

    # Handle GitHub repository
    github_url = data.get("github_url")
    github_branch = data.get("github_branch")
    github_repo = _get_or_create_github_repository(github_url, github_branch)

    # Build technologies child table
    technologies = data.get("technologies")
    if isinstance(technologies, str):
        technologies = frappe.parse_json(technologies)
    if not technologies:
        technologies = []

    tech_children = []
    for tech in technologies:
        if frappe.db.exists("Technology", tech):
            tech_children.append({"technology": tech})
        else:
            # Create Technology record if it doesn't exist
            try:
                tech_doc = frappe.get_doc({"doctype": "Technology", "technology_name": tech})
                tech_doc.insert(ignore_permissions=True)
                tech_children.append({"technology": tech_doc.name})
            except Exception:
                pass

    # Create the project
    project = frappe.get_doc({
        "doctype": "Project",
        "project_title": project_title,
        "project_category": data.get("project_category") or None,
        "team": team,
        "status": status,
        "priority": data.get("priority") or "Medium",
        "description": data.get("description") or "",
        "start_date": data.get("start_date") or None,
        "due_date": data.get("due_date") or None,
        "github_repository": github_repo,
        "technologies": tech_children,
    })

    project.insert(ignore_permissions=True, ignore_links=True)

    frappe.db.commit()

    return {
        "name": project.name,
        "project_title": project.project_title,
        "message": _("Project created successfully!"),
    }


@frappe.whitelist()
def add_project_file():
    """Link an uploaded file to a Project.

    Expects POST data with:
      - project_name (required)
      - file_url (required)
      - file_name
    """
    data = frappe.local.form_dict
    project_name = data.get("project_name")
    file_url = data.get("file_url")
    file_name = data.get("file_name")

    if not project_name or not file_url:
        frappe.throw(_("Project name and file URL are required."))

    if not frappe.db.exists("Project", project_name):
        frappe.throw(_("Project not found: {0}").format(project_name))

    # Determine file type from extension
    ext = (file_name or file_url or "").split(".")[-1].lower() if (file_name or file_url) else ""
    file_type_map = {
        "png": "PNG", "jpg": "JPG", "jpeg": "JPEG",
        "pdf": "PDF", "docx": "DOCX",
    }
    file_type = file_type_map.get(ext, "Other")

    doc = frappe.get_doc({
        "doctype": "Project Files",
        "project": project_name,
        "file": file_url,
        "file_name": file_name or file_url.split("/")[-1] if "/" in (file_url or "") else file_name,
        "file_type": file_type,
    })
    doc.insert(ignore_permissions=True, ignore_links=True)
    frappe.db.commit()

    return {
        "name": doc.name,
        "message": _("File linked successfully!"),
    }


@frappe.whitelist()
def create_project_readme():
    """Create or update a Project Readme for a project.

    Expects POST data with:
      - project_name (required)
      - readme_file (file URL of uploaded readme document)
      - readme_content (readme text content)
    """
    data = frappe.local.form_dict
    project_name = data.get("project_name")
    readme_file = data.get("readme_file")
    readme_content = data.get("readme_content")

    if not project_name:
        frappe.throw(_("Project name is required."))

    if not frappe.db.exists("Project", project_name):
        frappe.throw(_("Project not found: {0}").format(project_name))

    # Check if a readme already exists for this project
    existing = frappe.db.get_value("Project Readme", {"project": project_name}, "name")

    if existing:
        doc = frappe.get_doc("Project Readme", existing)
        if readme_file:
            doc.readme_file = readme_file
        if readme_content:
            doc.readme_content = readme_content
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"name": doc.name, "message": _("Readme updated successfully!")}
    else:
        doc_data = {"doctype": "Project Readme", "project": project_name}
        if readme_file:
            doc_data["readme_file"] = readme_file
        if readme_content:
            doc_data["readme_content"] = readme_content
        doc = frappe.get_doc(doc_data)
        doc.insert(ignore_permissions=True, ignore_links=True)
        frappe.db.commit()
        return {"name": doc.name, "message": _("Readme created successfully!")}


@frappe.whitelist()
def get_dashboard_stats():
    """Return dashboard statistics for the current user.

    Called by the dashboard JS (team_update_tool.api.projects.get_dashboard_stats).
    Returns a dict with:
      - total_projects, total_teams, total_technologies, my_projects
      - is_admin, status_counts, recent_projects, recent_repos
    """
    user = frappe.session.user
    if user == "Guest":
        return {"error": _("Please log in to view dashboard stats.")}

    roles = frappe.get_roles(user)
    is_admin = "System Manager" in roles or "Team Update Admin" in roles
    is_viewer = ("Team Update Viewer" in roles or "View-Only User" in roles) and not is_admin

    # Build base filters
    base_filters = {}
    if is_viewer:
        approved = frappe.db.get_value(
            "Project Status", {"status_name": "Approved"}, "name"
        )
        if approved:
            base_filters["status"] = approved

    # Statistics
    total_projects = frappe.db.count("Project", filters=base_filters)
    total_teams = frappe.db.count("Team", filters={"is_active": 1})
    total_technologies = frappe.db.count("Technology")
    my_projects = frappe.db.count("Project", filters={"owner": user})

    # Status counts
    status_counts = []
    statuses = frappe.get_all(
        "Project Status", fields=["name", "status_name", "color"]
    )
    for s in statuses:
        filters = {**base_filters, "status": s.name}
        count = frappe.db.count("Project", filters=filters)
        if count:
            status_counts.append({
                "name": s.status_name,
                "count": count,
                "color": s.color,
            })

    # Recent projects
    recent_projects = frappe.get_all(
        "Project",
        fields=["name", "project_title", "status", "owner", "creation"],
        limit=5,
        order_by="modified desc",
    )
    for p in recent_projects:
        if p.status:
            try:
                s = frappe.get_cached_doc("Project Status", p.status)
                p.status_name = s.status_name
                p.status_color = s.color
            except Exception:
                p.status_name = p.status
                p.status_color = "#6b7280"
        else:
            p.status_name = ""
            p.status_color = "#6b7280"

    # Recent GitHub repos
    recent_repos = []
    try:
        recent_repos = frappe.get_all(
            "GitHub Repository",
            fields=["name", "repository_name", "repository_url", "creation"],
            limit=5,
            order_by="creation desc",
        )
        for r in recent_repos:
            if r.repository_name:
                r.name = r.repository_name
    except Exception:
        recent_repos = []

    return {
        "total_projects": total_projects,
        "total_teams": total_teams,
        "total_technologies": total_technologies,
        "my_projects": my_projects,
        "is_admin": is_admin,
        "status_counts": status_counts,
        "recent_projects": recent_projects,
        "recent_repos": recent_repos,
    }
