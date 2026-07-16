# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


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
