// Dashboard page controller for Team Update Tool
// Professional ERPNext v15 style dashboard with charts, stats, and activity feed

frappe.pages["dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Team Update Tool Dashboard",
		single_column: true,
	});

	// Set page icon
	page.set_title(__("📊 Team Update Tool Dashboard"));

	// Add sidebar actions
	page.add_menu_item(__("⚙️ Settings"), function () {
		frappe.set_route("Form", "Team Update Settings");
	});

	page.add_menu_item(__("📋 New Task"), function () {
		frappe.set_route("List", "Team Project Update", { is_new: 1 });
	});

	page.add_menu_item(__("👥 New Team"), function () {
		frappe.set_route("List", "Team", { is_new: 1 });
	});

	// Add sidebar menu (left navigation)
	add_sidebar_menu(page);

	// Render dashboard
	render_dashboard(page);

	// Load data
	load_dashboard_data(page);
};

// ───────────────────────────── SIDEBAR MENU ─────────────────────────────

function add_sidebar_menu(page) {
	var sidebar_html = `
		<div class="tut-sidebar-menu">
			<div class="tut-sidebar-section">
				<div class="tut-sidebar-title">Team Update Tool</div>
				<a class="tut-sidebar-item active" href="/app/dashboard">
					<span>📊</span> Dashboard
				</a>
				<a class="tut-sidebar-item" href="/app/team-project-update">
					<span>📁</span> Projects
				</a>
				<a class="tut-sidebar-item" href="/app/team-project-update">
					<span>✅</span> Tasks
				</a>
				<a class="tut-sidebar-item" href="/app/team">
					<span>👥</span> Teams
				</a>
			</div>
			<div class="tut-sidebar-section">
				<div class="tut-sidebar-title">Reports</div>
				<a class="tut-sidebar-item" href="/app/query-report/Project%20Status%20Summary">
					<span>📈</span> Status Summary
				</a>
			</div>
			<div class="tut-sidebar-section">
				<div class="tut-sidebar-title">Settings</div>
				<a class="tut-sidebar-item" href="/app/team-update-settings">
					<span>⚙️</span> Team Settings
				</a>
				<a class="tut-sidebar-item" href="/app/notification-log">
					<span>🔔</span> Notifications
				</a>
			</div>
		</div>
	`;

	// Add sidebar to the page
	$(wrapper).find(".page-container").prepend(sidebar_html);
}

// ───────────────────────────── DASHBOARD RENDER ─────────────────────────────

function render_dashboard(page) {
	var dashboard_html = `
		<div class="tut-dashboard-container">
			<!-- Stats Cards Row -->
			<div class="tut-stats-grid" id="tut-stats">
				<div class="tut-stat-card-modern tut-stat-blue">
					<div class="tut-stat-icon-modern">📋</div>
					<div class="tut-stat-body">
						<div class="tut-stat-number" id="stat-total">0</div>
						<div class="tut-stat-label">Total Projects</div>
					</div>
				</div>
				<div class="tut-stat-card-modern tut-stat-green">
					<div class="tut-stat-icon-modern">✅</div>
					<div class="tut-stat-body">
						<div class="tut-stat-number" id="stat-completed">0</div>
						<div class="tut-stat-label">Completed</div>
					</div>
				</div>
				<div class="tut-stat-card-modern tut-stat-orange">
					<div class="tut-stat-icon-modern">⏳</div>
					<div class="tut-stat-body">
						<div class="tut-stat-number" id="stat-in-progress">0</div>
						<div class="tut-stat-label">In Progress</div>
					</div>
				</div>
				<div class="tut-stat-card-modern tut-stat-red">
					<div class="tut-stat-icon-modern">🔍</div>
					<div class="tut-stat-body">
						<div class="tut-stat-number" id="stat-pending-review">0</div>
						<div class="tut-stat-label">Pending Review</div>
					</div>
				</div>
				<div class="tut-stat-card-modern tut-stat-purple">
					<div class="tut-stat-icon-modern">👥</div>
					<div class="tut-stat-body">
						<div class="tut-stat-number" id="stat-teams">0</div>
						<div class="tut-stat-label">Active Teams</div>
					</div>
				</div>
				<div class="tut-stat-card-modern tut-stat-blue">
					<div class="tut-stat-icon-modern">👤</div>
					<div class="tut-stat-body">
						<div class="tut-stat-number" id="stat-members">0</div>
						<div class="tut-stat-label">Team Members</div>
					</div>
				</div>
			</div>

			<!-- Charts Row -->
			<div class="tut-charts-row">
				<div class="tut-chart-card">
					<div class="tut-chart-header">
						<h4>📊 Project Status</h4>
					</div>
					<div class="tut-chart-body">
						<canvas id="statusChart" height="250"></canvas>
					</div>
				</div>
				<div class="tut-chart-card">
					<div class="tut-chart-header">
						<h4>📈 Monthly Completed</h4>
					</div>
					<div class="tut-chart-body">
						<canvas id="monthlyChart" height="250"></canvas>
					</div>
				</div>
			</div>

			<!-- Bottom Row -->
			<div class="tut-bottom-row">
				<!-- Recent Activities -->
				<div class="tut-bottom-card">
					<div class="tut-bottom-header">
						<h4>🔄 Recent Activities</h4>
					</div>
					<div class="tut-bottom-body">
						<table class="tut-data-table" id="tut-activities-table">
							<thead>
								<tr>
									<th>Project</th>
									<th>Team</th>
									<th>Status</th>
									<th>Progress</th>
								</tr>
							</thead>
							<tbody id="tut-activities-body">
								<tr><td colspan="4" class="text-muted text-center">Loading...</td></tr>
							</tbody>
						</table>
					</div>
				</div>

				<!-- Team Performance -->
				<div class="tut-bottom-card">
					<div class="tut-bottom-header">
						<h4>🏆 Team Performance</h4>
					</div>
					<div class="tut-bottom-body">
						<table class="tut-data-table" id="tut-teams-table">
							<thead>
								<tr>
									<th>Team</th>
									<th>Projects</th>
									<th>Completed</th>
									<th>Rate</th>
								</tr>
							</thead>
							<tbody id="tut-teams-body">
								<tr><td colspan="4" class="text-muted text-center">Loading...</td></tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- Notifications -->
			<div class="tut-section-card">
				<div class="tut-section-header">
					<h4>🔔 Recent Notifications</h4>
				</div>
				<div class="tut-section-body" id="tut-notifications-body">
					<p class="text-muted">Loading...</p>
				</div>
			</div>
		</div>
	`;

	// Append to page content
	$(wrapper).find(".page-content").append(dashboard_html);
}

// ───────────────────────────── LOAD DATA ─────────────────────────────

function load_dashboard_data(page) {
	frappe.call({
		method: "team_update_tool.team_update_tool.page.dashboard.dashboard.get_dashboard_data",
		callback: function (r) {
			if (r.message) {
				var data = r.message;
				update_stats(data.stats);
				render_status_chart(data.status_chart);
				render_monthly_chart(data.monthly_chart);
				render_activities_table(data.recent_activities);
				render_teams_table(data.team_performance);
				render_notifications(data.notifications);
			}
		},
	});
}

// ───────────────────────────── UPDATE STATS ─────────────────────────────

function update_stats(stats) {
	$("#stat-total").text(stats.total_projects || 0);
	$("#stat-completed").text(stats.completed || 0);
	$("#stat-in-progress").text(stats.in_progress || 0);
	$("#stat-pending-review").text(stats.pending_review || 0);
	$("#stat-teams").text(stats.active_teams || 0);
	$("#stat-members").text(stats.total_members || 0);
}

// ───────────────────────────── CHARTS ─────────────────────────────

function render_status_chart(chart_data) {
	if (!chart_data || !chart_data.labels || chart_data.labels.length === 0) return;

	new frappe.Chart("#statusChart", {
		data: {
			labels: chart_data.labels,
			datasets: [{ name: "Projects", values: chart_data.values }],
		},
		type: "donut",
		height: 250,
		colors: ["#6c757d", "#8b5cf6", "#f59e0b", "#10b981", "#3b82f6", "#059669", "#ef4444"],
	});
}

function render_monthly_chart(chart_data) {
	if (!chart_data || !chart_data.labels || chart_data.labels.length === 0) return;

	new frappe.Chart("#monthlyChart", {
		data: {
			labels: chart_data.labels,
			datasets: [{ name: "Completed", values: chart_data.values }],
		},
		type: "bar",
		height: 250,
		colors: ["#10b981"],
		barOptions: { spaceRatio: 0.5 },
	});
}

// ───────────────────────────── ACTIVITIES TABLE ─────────────────────────────

function render_activities_table(activities) {
	if (!activities || activities.length === 0) {
		$("#tut-activities-body").html('<tr><td colspan="4" class="text-muted text-center">No recent activities</td></tr>');
		return;
	}

	var html = "";
	activities.forEach(function (a) {
		var status_class = a.status ? a.status.toLowerCase().replace(/ /g, "-") : "draft";
		var progress = a.progress_percent || 0;
		html += `
			<tr onclick="frappe.set_route('Form', 'Team Project Update', '${a.name}')" style="cursor:pointer;">
				<td><strong>${a.project_title}</strong></td>
				<td>${a.team}</td>
				<td><span class="tut-status-pill tut-status-${status_class}">${a.status}</span></td>
				<td>
					<div class="tut-progress-mini">
						<div class="tut-progress-track">
							<div class="tut-progress-fill-mini" style="width:${progress}%"></div>
						</div>
						<span>${progress}%</span>
					</div>
				</td>
			</tr>
		`;
	});

	$("#tut-activities-body").html(html);
}

// ───────────────────────────── TEAMS TABLE ─────────────────────────────

function render_teams_table(teams) {
	if (!teams || teams.length === 0) {
		$("#tut-teams-body").html('<tr><td colspan="4" class="text-muted text-center">No teams found</td></tr>');
		return;
	}

	var html = "";
	teams.forEach(function (t) {
		var rate_class = t.completion_rate >= 80 ? "green" : t.completion_rate >= 50 ? "orange" : "red";
		html += `
			<tr>
				<td><strong>${t.team}</strong></td>
				<td>${t.total}</td>
				<td>${t.completed}</td>
				<td><span class="tut-rate-pill tut-rate-${rate_class}">${t.completion_rate}%</span></td>
			</tr>
		`;
	});

	$("#tut-teams-body").html(html);
}

// ───────────────────────────── NOTIFICATIONS ─────────────────────────────

function render_notifications(notifications) {
	if (!notifications || notifications.length === 0) {
		$("#tut-notifications-body").html('<p class="text-muted">No notifications</p>');
		return;
	}

	var html = '<div class="tut-notif-list">';
	notifications.forEach(function (n) {
		html += `
			<div class="tut-notif-row">
				<span class="tut-notif-icon">🔔</span>
				<span class="tut-notif-text">${n.subject}</span>
				<span class="tut-notif-time">${fraetime(n.creation)}</span>
			</div>
		`;
	});
	html += "</div>";

	$("#tut-notifications-body").html(html);
}

function fraetime(date_str) {
	if (!date_str) return "";
	return frappe.datetime.pretty_date(date_str);
}
