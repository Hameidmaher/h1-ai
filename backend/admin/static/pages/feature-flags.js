/**
 * H1-AI — Feature Flags Management
 */
Pages.feature_flags = {
  flags: [],

  async render(el) {
    el.innerHTML = `
      <style>
        .ff-header{margin-bottom:20px}
        .ff-header h1{margin:0;font-size:24px}
        .ff-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
        .ff-card{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;transition:all 0.15s}
        .ff-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.06)}
        .ff-card.enabled{border-left:4px solid #10B981}
        .ff-card.disabled{border-left:4px solid #CBD5E1}
        .ff-name{font-size:16px;font-weight:700;color:#0F172A;margin-bottom:4px}
        .ff-key{font-size:11px;color:#94A3B8;font-family:monospace;direction:ltr;text-align:right;margin-bottom:8px}
        .ff-desc{font-size:13px;color:#64748B;margin-bottom:12px;line-height:1.5}
        .ff-toggle{display:flex;justify-content:space-between;align-items:center}
        .ff-status{font-size:12px;font-weight:600}
        .ff-status.on{color:#10B981}
        .ff-status.off{color:#94A3B8}
        .switch{position:relative;display:inline-block;width:48px;height:26px}
        .switch input{opacity:0;width:0;height:0}
        .slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background-color:#CBD5E1;transition:.3s;border-radius:26px}
        .slider:before{position:absolute;content:"";height:20px;width:20px;left:3px;bottom:3px;background-color:white;transition:.3s;border-radius:50%}
        input:checked + .slider{background-color:#10B981}
        input:checked + .slider:before{transform:translateX(22px)}
        .empty-state{text-align:center;padding:60px 20px;color:#94A3B8}
        .empty-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
      </style>

      <div class="ff-header">
        <h1>🎛️ ميزات النظام</h1>
      </div>

      <div id="ff-list"></div>
    `;

    await this.loadFlags();
    this.renderList();
  },

  async loadFlags() {
    try {
      const res = await App.api('/v1/admin/feature-flags');
      this.flags = res.flags || [];
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
      this.flags = [];
    }
  },

  renderList() {
    const c = document.getElementById('ff-list');
    
    if (!this.flags.length) {
      c.innerHTML = `<div class="empty-state"><div class="empty-icon">🎛️</div><div>لا توجد ميزات</div></div>`;
      return;
    }

    c.innerHTML = `<div class="ff-grid">${this.flags.map(f => `
      <div class="ff-card ${f.is_enabled ? 'enabled' : 'disabled'}">
        <div class="ff-name">${App.escapeHtml(f.name)}</div>
        <div class="ff-key">${App.escapeHtml(f.key)}</div>
        <div class="ff-desc">${App.escapeHtml(f.description || 'بدون وصف')}</div>
        <div class="ff-toggle">
          <span class="ff-status ${f.is_enabled ? 'on' : 'off'}">
            ${f.is_enabled ? '✅ مُفعّل' : '⏸️ معطّل'}
          </span>
          <label class="switch">
            <input type="checkbox" ${f.is_enabled ? 'checked' : ''} onchange="Pages.feature_flags.toggle('${f.key}', this.checked)">
            <span class="slider"></span>
          </label>
        </div>
      </div>
    `).join('')}</div>`;
  },

  async toggle(key, enabled) {
    try {
      await App.api(`/v1/admin/feature-flags/${key}`, {
        method: 'PUT',
        body: JSON.stringify({ is_enabled: enabled }),
      });
      App.toast(enabled ? `✅ تم تفعيل ${key}` : `⏸️ تم تعطيل ${key}`, 'success');
      await this.loadFlags();
      this.renderList();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },
};
