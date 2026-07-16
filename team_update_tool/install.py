# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

ROLES = [
    {
        "role_name": "Team Update Admin",
        "desk_access": 1,
        "home_page": "/team_update_tool/dashboard",
    },
    {
        "role_name": "Team Update Team Leader",
        "desk_access": 1,
        "home_page": "/team_update_tool/dashboard",
    },
    {
        "role_name": "Team Update Team Member",
        "desk_access": 1,
        "home_page": "/team_update_tool/dashboard",
    },
    {
        "role_name": "Team Update Viewer",
        "desk_access": 1,
        "home_page": "/team_update_tool/dashboard",
    },
]


def after_install():
    """Run after the app is installed on a site.

    Creates the four required roles needed by the app.
    """
    create_roles()
    create_team_update_domain()
    print("✓ Team Update Tool installed successfully.")


def create_roles():
    """Create roles if they don't already exist."""
    for role_data in ROLES:
        role_name = role_data["role_name"]
        if not frappe.db.exists("Role", role_name):
            role = frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": role_data["desk_access"],
                    "home_page": role_data.get("home_page", ""),
                }
            )
            role.insert(ignore_permissions=True, ignore_if_duplicate=True)
            print(f"  Created Role: {role_name}")
        else:
            print(f"  Role already exists: {role_name}")

    frappe.db.commit()


def create_team_update_domain():
    """Create the Team Update Tool domain for restrict_to_domain usage."""
    if not frappe.db.exists("Domain", "Team Update Tool"):
        doc = frappe.get_doc({
            "doctype": "Domain",
            "domain": "Team Update Tool",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("  Created Domain: Team Update Tool")


def force_sync_doctypes():
    """Force sync all Team Update Tool doctypes.

    Called from hooks.py as app_setup to ensure all
    doctype JSON files are synced into the database.

    Refreshes fixture DocTypes so the DB matches the JSON
    definitions after an app update.
    """
    from frappe.modules.utils import sync_customizations

    try:
        sync_customizations("team_update_tool")
        print("  Synced Team Update Tool customizations.")
    except Exception as e:
        print(f"  Warning: Could not sync customizations: {e}")

    frappe.clear_cache()


def sync_workspace_and_notifications():
    """Sync workspace and notifications after migration.

    Ensures that custom workspaces and notification records
    are properly synced after a migrate operation.
    """
    # Reload workspace fixture
    workspace_name = "Team Update Tool"
    if frappe.db.exists("Workspace", workspace_name):
        try:
            workspace = frappe.get_doc("Workspace", workspace_name)
            # Reload the content from the JSON fixture
            from frappe.modules.utils import sync_customizations

            sync_customizations("team_update_tool")
            print(f"  Synced Workspace: {workspace_name}")
        except Exception as e:
            frappe.log_error(
                f"Error syncing workspace '{workspace_name}': {str(e)}",
                "sync_workspace_and_notifications",
            )
            print(f"  Warning: Could not sync workspace: {e}")

    # Sync notification fixtures by reloading from disk
    notifications = [
        "New Project Uploaded",
        "Project Approved",
        "Project Status Updated",
    ]
    for notif_name in notifications:
        if frappe.db.exists("Notification", notif_name):
            try:
                # Reload the notification from its JSON fixture
                frappe.reload_doc("team_update_tool", "notification", notif_name.lower().replace(" ", "_"))
                print(f"  Synced Notification: {notif_name}")
            except Exception as e:
                print(f"  Warning: Could not sync notification '{notif_name}': {e}")

    frappe.db.commit()
    frappe.clear_cache()
    print("✓ Workspace and notifications synced successfully.")
