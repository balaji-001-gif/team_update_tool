import frappe

def clear_all_data():
    """Clear all data from team_update_tool related doctypes"""
    
    print("Starting data cleanup...")
    
    # List of doctypes to clear (in order of dependencies)
    doctypes_to_clear = [
        "Project Readme",
        "Project File", 
        "Project",
        "GitHub Repository",
    ]
    
    cleared_counts = {}
    
    for doctype in doctypes_to_clear:
        try:
            if frappe.db.exists("DocType", doctype):
                count = frappe.db.count(doctype)
                if count > 0:
                    frappe.db.sql(f"DELETE FROM `tab{doctype}`")
                    cleared_counts[doctype] = count
                    print(f"Cleared {count} records from {doctype}")
                else:
                    print(f"{doctype} - no records to clear")
            else:
                print(f"{doctype} - doctype does not exist")
        except Exception as e:
            print(f"Error clearing {doctype}: {str(e)}")
    
    frappe.db.commit()
    
    print("\n=== Cleanup Complete ===")
    print("Cleared records:")
    for doctype, count in cleared_counts.items():
        print(f"  - {doctype}: {count} records")
    
    return cleared_counts

# Run the cleanup
if __name__ == "__main__":
    clear_all_data()
