# COMPLETE FIX INSTRUCTIONS

Run these commands in order on your server:

## Step 1: Pull latest changes
```bash
cd ~/frappe-bench-v15/apps/team_update_tool
git pull origin main
cd ../..
```

## Step 2: Delete all old doctype records using SQL (run as single command)
```bash
bench --site [your-site-name] console
```

Then paste this and press Enter:
```python
frappe.db.sql("""
DELETE FROM `tabDocType` WHERE name IN (
    'Team', 'Team Member', 'Technology', 'Project Category', 'Project Status',
    'Project', 'Project Update', 'Project Files', 'Project Screenshots', 'Project Technology',
    'GitHub Repository',
    'Project Summary Report', 'Team Activity Report', 'Completed Projects Report', 'GitHub Repository Report',
    'New Project Uploaded', 'Project Approved', 'Project Status Updated',
    'Team Update Tool'
)
""")
frappe.db.commit()
exit()
```

## Step 3: Migrate to re-sync all doctypes
```bash
bench --site [your-site-name] migrate
```

## Step 4: Restart
```bash
bench restart
```

## Step 5: Clear browser cache
Press Ctrl+Shift+R (or Cmd+Shift+R on Mac) in your browser

---

## Alternative: If Step 2 doesn't work

Try running this directly in MySQL:
```bash
mysql -u root -p [your_password] [sitename]
```
Then:
```sql
USE [databasename];
DELETE FROM `tabDocType` WHERE name IN (
    'Team', 'Team Member', 'Technology', 'Project Category', 'Project Status',
    'Project', 'Project Update', 'Project Files', 'Project Screenshots', 'Project Technology',
    'GitHub Repository',
    'Project Summary Report', 'Team Activity Report', 'Completed Projects Report', 'GitHub Repository Report',
    'New Project Uploaded', 'Project Approved', 'Project Status Updated',
    'Team Update Tool'
);
DELETE FROM `tabPropertySetter` WHERE doc_type IN (
    'Team', 'Team Member', 'Technology', 'Project Category', 'Project Status',
    'Project', 'Project Update', 'Project Files', 'Project Screenshots', 'Project Technology',
    'GitHub Repository',
    'Project Summary Report', 'Team Activity Report', 'Completed Projects Report', 'GitHub Repository Report',
    'New Project Uploaded', 'Project Approved', 'Project Status Updated',
    'Team Update Tool'
);
FLUSH TABLES;
EXIT;
```

Then run migrate.
