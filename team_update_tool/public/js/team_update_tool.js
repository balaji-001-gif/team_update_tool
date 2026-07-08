// Team Update Tool — Complete Client-side JavaScript

frappe.provide("team_update_tool");

// ==============================
// Desk: View-Only Banner
// ==============================

team_update_tool.show_viewer_banner = function (frm) {
	const roles = frappe.user_roles || [];
	const is_admin = roles.includes("Admin") || roles.includes("System Manager");
	const is_viewer = roles.includes("View-Only User");

	if (is_viewer && !is_admin) {
		frm.dashboard.set_headline_alert(
			'<div class="tut-readonly-banner">👁 View Only Access — You cannot create, edit, or delete records</div>'
		);
		frm.disable_form();
	}
};

// ==============================
// Website: Toast Notifications
// ==============================

function tutToast(message, type) {
	if (typeof type === 'undefined') type = 'info';
	var container = document.querySelector('.tut-toast-container');
	if (!container) {
		container = document.createElement('div');
		container.className = 'tut-toast-container';
		document.body.appendChild(container);
	}
	var toast = document.createElement('div');
	toast.className = 'tut-toast tut-toast-' + type;
	toast.textContent = message;
	container.appendChild(toast);
	setTimeout(function() {
		toast.style.animation = 'tutToastOut 0.3s ease forwards';
		setTimeout(function() { toast.remove(); }, 300);
	}, 4000);
}

// ==============================
// Website: Confirm Dialog
// ==============================

function tutConfirm(message, title) {
	if (typeof title === 'undefined') title = 'Confirm';
	return new Promise(function(resolve) {
		var overlay = document.createElement('div');
		overlay.className = 'tut-modal-overlay';
		overlay.innerHTML =
			'<div class="tut-modal"><h3>' + title + '</h3><p>' + message + '</p>' +
			'<div class="tut-modal-actions">' +
			'<button class="tut-btn tut-btn-ghost tut-btn-sm" id="tutConfirmNo">Cancel</button>' +
			'<button class="tut-btn tut-btn-primary tut-btn-sm" id="tutConfirmYes">Confirm</button>' +
			'</div></div>';
		document.body.appendChild(overlay);
		document.getElementById('tutConfirmYes').addEventListener('click', function() { overlay.remove(); resolve(true); });
		document.getElementById('tutConfirmNo').addEventListener('click', function() { overlay.remove(); resolve(false); });
		overlay.addEventListener('click', function(e) { if (e.target === overlay) { overlay.remove(); resolve(false); } });
	});
}

// ==============================
// Website: Escape HTML
// ==============================

function escHtml(s) {
	if (!s) return '';
	return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ==============================
// Website: Format Date
// ==============================

function formatDate(d) {
	if (!d) return '';
	return d.substring(0,10);
}

// ==============================
// Website: Navbar (JS-injected)
// ==============================

function tutRenderNavbar() {
	// Avoid double-render
	if (document.querySelector('.tut-navbar')) return;

	var html = '' +
	'<nav class="tut-navbar"><div class="container">' +
	'<a href="/team_update_tool" class="tut-navbar-brand">' +
	'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' +
	'<span>Team Update Tool</span></a>' +
	'<button class="tut-navbar-toggle" id="navToggle"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button>' +
	'<div class="tut-navbar-nav" id="navMenu">' +
	'<a href="/team_update_tool" class="tut-nav-link">Home</a>' +
	'<a href="/team_update_tool/dashboard" class="tut-nav-link">Dashboard</a>' +
	'<a href="/team_update_tool/projects" class="tut-nav-link">Projects</a>' +
	'<a href="/team_update_tool/repositories" class="tut-nav-link">Repositories</a>' +
	'<a href="/team_update_tool/gallery" class="tut-nav-link">Gallery</a>' +
	'<a href="/team_update_tool/documents" class="tut-nav-link">Documents</a>' +
	'<a href="/team_update_tool/reports" class="tut-nav-link">Reports</a>' +
	'<div class="tut-navbar-right">' +
	'<span id="navUser" style="display:none;">' +
	'<a href="/team_update_tool/profile" class="tut-nav-link tut-nav-icon" title="Profile"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></a>' +
	'<a href="/team_update_tool/notifications" class="tut-nav-link tut-nav-icon" title="Notifications"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></a>' +
	'<a href="/team_update_tool/settings" class="tut-nav-link tut-nav-icon" title="Settings"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></a>' +
	'<a href="/team_update_tool/logout" class="tut-nav-link tut-nav-icon" title="Sign Out" style="color:#dc2626;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg></a>' +
	'</span>' +
	'<span id="navGuest"><a href="/team_update_tool/login" class="tut-btn tut-btn-primary tut-btn-sm">Sign In</a> <a href="/team_update_tool/signup" class="tut-btn tut-btn-ghost tut-btn-sm">Sign Up</a></span>' +
	'</div></div></div></nav>';

	// Inject at the top of page content
	var target = document.querySelector('.page-content') || document.querySelector('.container:first-child') || document.body;
	target.insertAdjacentHTML('afterbegin', html);

	// Mobile toggle
	var toggle = document.getElementById('navToggle');
	if (toggle) {
		toggle.addEventListener('click', function() {
			document.getElementById('navMenu').classList.toggle('tut-navbar-open');
		});
	}

	// Show/hide user nav based on login state
	fetch('/api/method/team_update_tool.api.auth.get_current_user')
		.then(function(r) { return r.json(); })
		.then(function(d) {
			if (d.message && !d.message.guest) {
				var u = document.getElementById('navUser');
				var g = document.getElementById('navGuest');
				if (u) u.style.display = 'inline-flex';
				if (g) g.style.display = 'none';
			}
		})
		.catch(function() {});

	// Active nav link
	var path = window.location.pathname;
	document.querySelectorAll('.tut-nav-link').forEach(function(link) {
		var href = link.getAttribute('href');
		if (href && path.startsWith(href) && href !== '/team_update_tool') {
			link.classList.add('tut-nav-active');
		} else if (href === '/team_update_tool' && path === '/team_update_tool') {
			link.classList.add('tut-nav-active');
		}
	});
}

// Render navbar on every page
frappe.ready(function() {
	tutRenderNavbar();
});
