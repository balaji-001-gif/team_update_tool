import frappe

def execute():
    # Fix module names for all Team Update Tool doctypes
    module_map = {
        "Masters": "masters",
        "Transactions": "transactions",
        "Reports": "reports",
    }
    
    for old_module, new_module in module_map.items():
        frappe.db.sql("""
            UPDATE `tabDocType` 
            SET module = %s 
            WHERE module = %s AND (name LIKE 'Project%%' OR name LIKE 'Team%%' OR name LIKE 'Technology%%' OR name LIKE 'GitHub%%')
        """, (new_module, old_module))
    
    frappe.db.commit()
    frappe.clear_cache()
