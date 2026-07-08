# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

"""
Custom login page handler for Frappe 15.

This overrides any broken custom login pages (e.g. from other apps) that
try to call `frappe.www.login.login` which does not exist in Frappe 15.

The correct login RPC endpoint is `frappe.auth.login_and_redirect` or
simply using the `/api/method/login` endpoint.
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
    """Set up context for the login page."""
    redirect_to = frappe.local.request.args.get("redirect-to", "")

    if frappe.session.user != "Guest":
        if redirect_to:
            frappe.local.flags.redirect_location = redirect_to
        else:
            frappe.local.flags.redirect_location = "/app"
        raise frappe.Redirect

    context.no_header = True
    context.for_test = "login.html"
    context.title = _("Login")
    context.redirect_to = redirect_to

    # Provide the login_and_redirect method for backward compatibility
    context.login_url = "/api/method/login"


@frappe.whitelist(allow_guest=True)
def login(usr=None, pwd=None):
    """
    Backward-compatible login method.
    
    This exists to fix the AttributeError:
    'module frappe.www.login has no attribute login'
    
    Other apps may call `/api/method/frappe.www.login.login` which
    does not exist in Frappe 15. This custom www/login.py provides
    that method so the call resolves correctly.
    
    It delegates to Frappe's built-in LoginManager.
    """
    from frappe.auth import LoginManager

    if not usr or not pwd:
        frappe.throw(_("Please provide email and password"), frappe.AuthenticationError)

    login_manager = LoginManager()
    login_manager.authenticate(usr, pwd)
    login_manager.post_login()

    if frappe.response.get("message") != "No App":
        frappe.response["message"] = "Logged In"

    return "Logged In"
