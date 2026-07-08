frappe.pages["team-update-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Team Update Dashboard",
		single_column: true,
	});

	page.main.html('<div id="tud-app"></div>');
	wrapper.tud_page = page;

	new TeamUpdateDashboard(page);
};

class TeamUpdateDashboard {
	constructor(page) {
		this.page = page;
		this.container = page.main.find("#tud-app");
		this.data = null;
		this.init();
	}

	init() {
		this.page.set_secondary_action("Refresh", () => this.loadData(), "refresh");
		this.showLoading();
		this.loadData();
	}

	showLoading() {
		this.container.html(`
			<div class="tud-loading">
				<div class="tud-loading-grid">
					${Array(7).fill('<div class="tud-skeleton"></div>').join("")}
				</div>
			</div>
		`);
	}

	async loadData() {
		try {
			const res = await frappe.xcall("team_update_tool.api.get_dashboard_data");
			this.data = res;
			this.render();
		} catch (e) {
			this.container.html(`
				<div class="tud-error">
					<div class="tud-error-icon">⚠️</div>
					<h3>Failed to load dashboard</h3>
					<p>${frappe.utils.xss_sanitise(e.message || "Unknown error")}</p>
					<button class="btn btn-primary btn-sm" onclick="cur_page && cur_page.tud_page && cur_page.tud_page.main.find('#tud-app').data('tud') && cur_page.tud_page.main.find('#tud-app').data('tud').loadData()">
						Retry
					</button>
				</div>
			`);
			console.error("Dashboard load error:", e);
		}
	}

	render() {
		if (!this.data) return;
		const d = this.data;
		const s = d.stats || {};

		this.container.html(`
			<!-- Welcome Banner -->
			<div class="tud-welcome">
				<div class="tud-welcome-content">
					<h2>Welcome back, ${frappe.utils.xss_sanitise(d.user?.full_name || "User")} 👋</h2>
					<p>Here's what's happening with your projects today.</p>
				</div>
			</div>

			<!-- Stats Cards -->
			<div class="tud-stats-grid">
				${this.renderStatCard("📊", "Total Projects", s.total_projects || 0, "blue")}
				${this.renderStatCard("✅", "Completed", s.completed || 0, "green")}
				${this.renderStatCard("🔄", "Under Review", s.under_review || 0, "orange")}
				${this.renderStatCard("📋", "Submitted", s.submitted || 0, "yellow")}
				${this.renderStatCard("❌", "Rejected", s.rejected || 0, "red")}
				${this.renderStatCard("👥", "Active Teams", s.active_teams || 0, "cyan")}
				${this.renderStatCard("🏢", "All Teams", s.total_teams || 0, "gray")}
			</div>

			<!-- Charts Row -->
			<div class="tud-charts-row">
				<div class="tud-card">
					<div class="tud-card-header"><h3>Project Status Distribution</h3></div>
					<div class="tud-card-body"><div id="tud-chart-status" style="height: 260px;"></div></div>
				</div>
				<div class="tud-card">
					<div class="tud-card-header"><h3>Monthly Completed Projects</h3></div>
					<div class="tud-card-body"><div id="tud-chart-monthly" style="height: 260px;"></div></div>
				</div>
			</div>

			<div class="tud-charts-row">
				<div class="tud-card">
					<div class="tud-card-header"><h3>Team Performance</h3></div>
					<div class="tud-card-body"><div id="tud-chart-teams" style="height: 260px;"></div></div>
				</div>
				<div class="tud-card">
					<div class="tud-card-header"><h3>Progress Distribution</h3></div>
					<div class="tud-card-body"><div id="tud-chart-progress" style="height: 260px;"></div></div>
				</div>
			</div>

			<!-- Recent Projects -->
			<div class="tud-card">
				<div class="tud-card-header">
					<h3>Recent Projects</h3>
					<a href="/app/project-submission" class="tud-link">View All →</a>
				</div>
				<div class="tud-card-body tud-no-padding">
					${this.renderProjectsTable(d.recent_projects || [])}
				</div>
			</div>

			<!-- Two Column: Teams + GitHub -->
			<div class="tud-two-col">
				<div class="tud-card">
					<div class="tud-card-header">
						<h3>Teams</h3>
						<a href="/app/team" class="tud-link">View All →</a>
					</div>
					<div class="tud-card-body">${this.renderTeamsList(d.teams || [])}</div>
				</div>
				<div class="tud-card">
					<div class="tud-card-header"><h3>GitHub Repositories</h3></div>
					<div class="tud-card-body">${this.renderGitHubList(d.github_projects || [])}</div>
				</div>
			</div>

			<!-- Notifications -->
			<div class="tud-card">
				<div class="tud-card-header"><h3>Recent Notifications</h3></div>
				<div class="tud-card-body">${this.renderNotifications(d.notifications || [])}</div>
			</div>
		`);

		setTimeout(() => this.renderCharts(), 100);
	}

	renderStatCard(icon, label, value, color) {
		return `<div class="tud-stat-card tud-stat-${color}">
			<div class="tud-stat-icon">${icon}</div>
			<div class="tud-stat-info">
				<div class="tud-stat-value">${value}</div>
				<div class="tud-stat-label">${label}</div>
			</div>
		</div>`;
	}

	renderProjectsTable(projects) {
		if (!projects.length) {
			return '<div class="tud-empty">No projects found. <a href="/app/project-submission/new">Create your first project</a></div>';
		}
		const statusColors = { Submitted: "yellow", "Under Review": "orange", Approved: "green", Rejected: "red" };
		let rows = projects.slice(0, 10).map((p) => {
			const pct = p.progress_percent || 0;
			const sc = statusColors[p.status] || "gray";
			return `<tr class="tud-table-row" onclick="frappe.set_route('project-submission', '${frappe.utils.xss_sanitise(p.name)}')" style="cursor:pointer;">
				<td class="tud-table-cell"><span class="tud-project-title">${frappe.utils.xss_sanitise(p.project_title || p.name)}</span></td>
				<td class="tud-table-cell"><span class="tud-badge tud-badge-${sc}">${frappe.utils.xss_sanitise(p.status || "Submitted")}</span></td>
				<td class="tud-table-cell tud-text-muted">${frappe.utils.xss_sanitise(p.team || "-")}</td>
				<td class="tud-table-cell"><div class="tud-progress-wrap"><div class="tud-progress-bar"><div class="tud-progress-fill tud-progress-${pct >= 100 ? "green" : pct >= 50 ? "blue" : "orange"}" style="width: ${pct}%"></div></div><span class="tud-progress-text">${pct}%</span></div></td>
				<td class="tud-table-cell tud-text-muted">${frappe.datetime.prettyDate(p.modified)}</td>
			</tr>`;
		}).join("");

		return `<table class="tud-table"><thead><tr>
			<th class="tud-table-head">Title</th><th class="tud-table-head">Status</th>
			<th class="tud-table-head">Team</th><th class="tud-table-head">Progress</th><th class="tud-table-head">Modified</th>
		</tr></thead><tbody>${rows}</tbody></table>`;
	}

	renderTeamsList(teams) {
		if (!teams.length) return '<div class="tud-empty">No teams found.</div>';
		return teams.slice(0, 8).map((t) =>
			`<div class="tud-list-item" onclick="frappe.set_route('team', '${frappe.utils.xss_sanitise(t.name)}')" style="cursor:pointer;">
				<div class="tud-list-left">
					<div class="tud-team-avatar">${(t.team_name || "T").charAt(0).toUpperCase()}</div>
					<div><div class="tud-list-title">${frappe.utils.xss_sanitise(t.team_name)}</div>
					<div class="tud-list-sub">${frappe.utils.xss_sanitise(t.team_lead || "No lead")} · ${t.member_count || 0} members</div></div>
				</div>
				<div class="tud-list-right">
					<span class="tud-badge tud-badge-blue">${t.project_count || 0} projects</span>
					${t.is_active ? '<span class="tud-dot tud-dot-green"></span>' : '<span class="tud-dot tud-dot-gray"></span>'}
				</div>
			</div>`
		).join("");
	}

	renderGitHubList(projects) {
		if (!projects.length) return '<div class="tud-empty">No GitHub repositories linked yet.</div>';
		return projects.slice(0, 8).map((g) =>
			`<div class="tud-list-item">
				<div class="tud-list-left">
					<div class="tud-github-icon"><svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg></div>
					<div><div class="tud-list-title">${frappe.utils.xss_sanitise(g.project_title)}</div>
					<div class="tud-list-sub">${frappe.utils.xss_sanitise(g.github_commit_hash ? "SHA: " + g.github_commit_hash.substring(0, 7) : "")} ${frappe.utils.xss_sanitise(g.team || "")}</div></div>
				</div>
				<div class="tud-list-right">
					<a href="${frappe.utils.xss_sanitise(g.github_repo_url)}" target="_blank" class="tud-link-btn">Open ↗</a>
				</div>
			</div>`
		).join("");
	}

	renderNotifications(notifications) {
		if (!notifications.length) return '<div class="tud-empty">No recent notifications.</div>';
		return notifications.slice(0, 8).map((n) =>
			`<div class="tud-list-item">
				<div class="tud-list-left">
					<div class="tud-notif-icon">🔔</div>
					<div><div class="tud-list-title">${frappe.utils.xss_sanitise(n.subject || "Notification")}</div>
					<div class="tud-list-sub">${frappe.datetime.prettyDate(n.creation)}</div></div>
				</div>
			</div>`
		).join("");
	}

	renderCharts() {
		if (!this.data || !this.data.charts) return;
		const c = this.data.charts;

		if (c.status_counts && c.status_counts.length) {
			const colors = { Submitted: "#eab308", "Under Review": "#f59e0b", Approved: "#22c55e", Rejected: "#ef4444" };
			try {
				new frappe.Chart("#tud-chart-status", {
					data: { labels: c.status_counts.map((s) => s.status), datasets: [{ name: "Projects", values: c.status_counts.map((s) => s.count) }] },
					type: "donut", height: 230,
					colors: c.status_counts.map((s) => colors[s.status] || "#6b7280"),
				});
			} catch (e) { console.warn("Chart error:", e); }
		}
		if (c.monthly_completed && c.monthly_completed.length) {
			try {
				new frappe.Chart("#tud-chart-monthly", {
					data: { labels: c.monthly_completed.map((m) => m.month), datasets: [{ name: "Completed", values: c.monthly_completed.map((m) => m.count), chartType: "bar" }] },
					type: "bar", height: 230, colors: ["#22c55e"],
				});
			} catch (e) { console.warn("Chart error:", e); }
		}
		if (c.team_performance && c.team_performance.length) {
			try {
				new frappe.Chart("#tud-chart-teams", {
					data: { labels: c.team_performance.map((t) => t.team || "Unassigned"), datasets: [{ name: "Projects", values: c.team_performance.map((t) => t.count), chartType: "bar" }] },
					type: "bar", height: 230, colors: ["#8b5cf6"],
				});
			} catch (e) { console.warn("Chart error:", e); }
		}
		if (c.progress_ranges && c.progress_ranges.length) {
			try {
				new frappe.Chart("#tud-chart-progress", {
					data: { labels: c.progress_ranges.map((p) => p.range), datasets: [{ name: "Projects", values: c.progress_ranges.map((p) => p.count), chartType: "bar" }] },
					type: "bar", height: 230, colors: ["#3b82f6"],
				});
			} catch (e) { console.warn("Chart error:", e); }
		}
	}
}
