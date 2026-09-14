Pages.audit = {
  async render(el) {
    el.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-actions">
          <button class="btn btn-primary" onclick="Pages.audit.refresh()">
            🔄 تحديث
          </button>
          <button class="btn btn-ghost" onclick="Pages.audit.createBackup()">
            💾 نسخة احتياطية الآن
          </button>
        </div>
      </div>
      <div id="audit-content"></div>
    `;
    await this.load();
  },

  async load() {
    try {
      const logs = await App.api('/v1/admin/audit/log?limit=100');
      if (!logs.length) {
        document.getElementById('audit-content').innerHTML =
          '<div class="empty-state"><span class="icon">📜</span>لا يوجد سجل بعد</div>';
        return;
      }
      const rows = logs.map(l => `
        <tr>
          <td>${App.formatDate(l.timestamp)}</td>
          <td><strong>${App.escapeHtml(l.user)}</strong></td>
          <td><span class="badge badge-info">${App.escapeHtml(l.action)}</span></td>
          <td>${App.escapeHtml(l.entity)}</td>
          <td><code>${App.escapeHtml(l.entity_id || '')}</code></td>
        </tr>
      `).join('');
      document.getElementById('audit-content').innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>التاريخ</th><th>المستخدم</th><th>الإجراء</th>
              <th>الكيان</th><th>المعرّف</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    } catch (e) {
      document.getElementById('audit-content').innerHTML =
        `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },

  refresh() { this.load(); },

  async createBackup() {
    try {
      const res = await App.api('/v1/admin/audit/backups/create', {
        method: 'POST',
      });
      App.toast(`تم إنشاء نسخة احتياطية (${res.backed_up.length} ملف)`, 'success');
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },
};
