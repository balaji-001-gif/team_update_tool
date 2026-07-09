-- Delete old doctype records so they re-sync from JSON files
DELETE FROM `tabDocType` WHERE name IN (
    'Team', 'Team Member', 'Technology', 'Project Category', 'Project Status',
    'Project', 'Project Update', 'Project Files', 'Project Screenshots', 'Project Technology',
    'GitHub Repository',
    'Project Summary Report', 'Team Activity Report', 'Completed Projects Report', 'GitHub Repository Report',
    'New Project Uploaded', 'Project Approved', 'Project Status Updated'
);

-- Clear cache
DELETE FROM `tabCacheControl`;
