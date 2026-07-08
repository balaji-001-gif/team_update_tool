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
// Website: Navigation Enhancement
// ==============================

frappe.ready(function() {
	// Add active class to current page link in web navigation
	const path = window.location.pathname;
	document.querySelectorAll('.navbar-nav a, .web-sidebar a, .tut-sidebar-nav a').forEach(function(link) {
		if (link.getAttribute('href') === path) {
			link.classList.add('active');
		}
	});
});
