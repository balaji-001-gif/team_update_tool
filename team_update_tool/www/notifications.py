# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	"""Build the notifications page context."""
	context.no_sidebar = 1
	context.no_cache = 1
	context.title = "Notifications - Team Update Tool"

	context.notifications = frappe.get_all(
		"Notification Log",
		filters={"for_user": frappe.session.user},
		fields=["subject", "creation", "document_type", "document_name", "from_user"],
		order_by="creation desc",
		limit=100,
	)
