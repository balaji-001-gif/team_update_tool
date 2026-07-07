const BASE_URL = import.meta.env.DEV ? '' : ''

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

async function request(method, url, data = null) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Frappe-CSRF-Token': getCookie('csrf_token') || window.csrf_token || '',
  }
  const options = { method, headers, credentials: 'include' }
  if (data) options.body = JSON.stringify(data)
  const res = await fetch(BASE_URL + url, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }))
    throw new Error(err.message || err.exception || 'Request failed')
  }
  return res.json()
}

export const api = {
  get: (url) => request('GET', url),
  post: (url, data) => request('POST', url, data),
  put: (url, data) => request('PUT', url, data),
  delete: (url) => request('DELETE', url),

  async getDashboardData() {
    return this.post(
      '/api/method/team_update_tool.team_update_tool.page.team_update_dashboard.team_update_dashboard.get_dashboard_data'
    )
  },

  async getProjects(params = {}) {
    const args = {
      doctype: 'Team Project Update',
      fields: '["*"]',
      limit_page_length: params.limit || 20,
      order_by: params.order_by || 'modified desc',
    }
    if (params.filters) args.filters = JSON.stringify(params.filters)
    const query = Object.entries(args).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
    return this.get(`/api/resource/Team%20Project%20Update?${query}`)
  },

  async getTeams(params = {}) {
    const args = {
      doctype: 'Team',
      fields: '["*"]',
      limit_page_length: params.limit || 20,
    }
    const query = Object.entries(args).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
    return this.get(`/api/resource/Team?${query}`)
  },

  async getTeamMembers(teamName) {
    const args = {
      doctype: 'Team Member',
      fields: '["*"]',
      filters: JSON.stringify([['parent', '=', teamName]]),
    }
    const query = Object.entries(args).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
    return this.get(`/api/resource/Team%20Member?${query}`)
  },

  async createDoc(doctype, data) {
    return this.post(`/api/resource/${encodeURIComponent(doctype)}`, data)
  },

  async updateDoc(doctype, name, data) {
    return this.put(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`, data)
  },

  async deleteDoc(doctype, name) {
    return this.delete(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`)
  },

  async getDoc(doctype, name) {
    return this.get(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`)
  },

  async uploadFile(file, doctype, docname, fieldname = 'file_attachment') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('doctype', doctype)
    formData.append('docname', docname)
    formData.append('fieldname', fieldname)
    formData.append('is_private', '0')
    const res = await fetch(BASE_URL + '/api/method/upload_file', {
      method: 'POST',
      headers: {
        'X-Frappe-CSRF-Token': getCookie('csrf_token') || window.csrf_token || '',
      },
      credentials: 'include',
      body: formData,
    })
    return res.json()
  },

  async getNotifications() {
    return this.get('/api/method/frappe.desk.notifications.get_notifications')
  },

  async runReport(reportName, filters = {}) {
    const params = Object.entries(filters).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
    return this.get(`/api/method/frappe.desk.query_report.run?report_name=${encodeURIComponent(reportName)}&${params}`)
  },
}
