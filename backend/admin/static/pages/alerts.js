/**
 * H1-AI — System Alerts
 */
Pages.alerts = {
  alerts: [],

  async render(el) {
    el.innerHTML = `
      <style>
        .al-header{margin-bottom:20px}
        .al-header h1{margin:0;font-size:24px}
        .al-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}
        .al-stat{background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0;text-align:center}
        .al-stat-value{font-size:24px;font-weight:700}
        .al-stat-label{font-size:12px;color:#64748B;margin-top:4px}
        .al-card{background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0;margin-bottom:10px;border-left:4px solid #0EA5E9}
        .al-card.info{border-left-color:#0EA5E9}
        .al-card.warning{border-left-color:#F59E0B}
        .al-card.error{border-left-color:#EF4444}
        .al-card.critical{border-left-color:#991B1B;background:#FEF2F2}
        .al-header-row{display:flex;justify-content:space-between;align-items:start;margin-bottom:8px}
        .al-title{font-weight:700;color:#0F172A;font-size:15px}
        .al-time{font-size:12px;color:#94A3B8}
        .al-msg{font-size:14px;color:#475569;margin:8px 0}
        .al-meta{display:flex;gap:8px;font-size:11px;margin-top:8px}
        .al-badge{padding:2px 8px;border-radius:10px}
        .al-badge.info{background:#DBEAFE;color:#1E40AF}
        .al-badge.warning{background:#FEF3C7;color:#92400E}
        .al-badge.error{background:#FEE2E2;color:#991B1B}
        .al-badge.critical{background:#FEE2E2;color:#991B1B;font-weight:700}
        .al-resolve{padding:4px 10px;background:#10B981;color:white;border:none;border-radius:6px;cursor:pointer;font-size:11px;font-weight:600}
        .empty-state{text-align:center;padding:60px 20px;color:#94A3B8}
        .empty-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
      </style>

      <div class="al-header">
        <h1>🚨 التنبيهات</h1>
      </div>

      <div id="al-stats"></div>
      <div id="al-list"></div>
    `;

    await this.loadAlerts();
    this.renderStats();
    this.renderList();
  },

  async loadAlerts() {
    try {
      const res = await App.api('/v1/admin/alerts?unresolved_only=false');
      this.alerts = res.alerts || [];
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
      this.alerts = [];
    }
  },

  renderStats() {
    const total = this.alerts.length;
    const unresolved = this.alerts.filter(a => !a.is_resolved).length;
    const critical = this.alerts.filter(a => a.severity === 'critical' && !a.is_resolved).length;
    const errors = this.alerts.filter(a => a.severity === 'error' && !a.is_resolved).length;

    document.getElementById('al-stats').innerHTML = `
      <div class="al-stats">
        <div class="al-stat"><div class="al-stat-value">${total}</div><div class="al-stat-label">إجمالي</div></div>
        <div class="al-stat"><div class="al-stat-value" style="color:#F59E0B">${unresolved}</div><div class="al-stat-label">غير محلولة</div></div>
        <div class="al-stat"><div class="al-stat-value" style="color:#EF4444">${critical}</div><div class="al-stat-label">حرجة</div></div>
        <div class="al-stat"><div class="al-stat-value" style="color:#EF4444">${errors}</div><div class="al-stat-label">أخطاء</div></div>
      </div>
    `;
  },

  renderList() {
    const c = document.getElementById('al-list');
    
    if (!this.alerts.length) {
      c.innerHTML = `<div class="empty-state"><div class="empty-icon">🎉</div><div>لا توجد تنبيهات — كل شيء يعمل!</div></div>`;
      return;
    }

    c.innerHTML = this.alerts.map(a => `
      <div class="al-card ${a.severity}">
        <div class="al-header-row">
          <div class="al-title">${App.escapeHtml(a.title)}</div>
          <div class="al-time">${App.formatDate(a.created_at)}</div>
        </div>
        <div class="al-msg">${App.escapeHtml(a.message || '')}</div>
        <div class="al-meta">
          <span class="al-badge ${a.severity}">${a.severity}</span>
          <span class="al-badge info">${a.type}</span>
          ${a.pharmacy_name ? `<span style="color:#64748B">🏥 ${App.escapeHtml(a.pharmacy_name)}</span>` : ''}
        </div>
        ${!a.is_resolved ? `
          <button class="al-resolve" style="margin-top:8px" onclick="Pages.alerts.resolve('${a.id}')">✅ حل</button>
        ` : '<span style="color:#10B981;font-size:12px;font-weight:600">✅ تم الحل</span>'}
      </div>
    `).join('');
  },

  async resolve(alertId) {
    try {
      await App.api(`/v1/admin/alerts/${alertId}/resolve`, { method: 'POST' });
      App.toast('✅ تم الحل', 'success');
      await this.loadAlerts();
      this.renderStats();
      this.renderList();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },
};
