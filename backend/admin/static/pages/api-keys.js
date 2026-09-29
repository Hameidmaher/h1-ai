/**
 * H1-AI — API Keys Management
 */
Pages.api_keys = {
  keys: [],

  async render(el) {
    el.innerHTML = `
      <style>
        .ak-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}
        .ak-header h1{margin:0;font-size:24px}
        .ak-btn{padding:10px 20px;background:#0EA5E9;color:white;border:none;border-radius:8px;font-family:inherit;font-size:14px;font-weight:600;cursor:pointer}
        .ak-btn:hover{background:#0284C7}
        .ak-card{background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0;margin-bottom:10px;display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;align-items:center}
        .ak-name{font-weight:700;color:#0F172A}
        .ak-prefix{font-family:monospace;font-size:12px;color:#64748B;direction:ltr;text-align:right;margin-top:4px}
        .ak-pharmacy{font-size:12px;color:#64748B}
        .ak-date{font-size:11px;color:#94A3B8}
        .ak-status{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600}
        .ak-status.active{background:#DCFCE7;color:#166534}
        .ak-status.inactive{background:#FEE2E2;color:#991B1B}
        .ak-delete{padding:6px 12px;background:#FEE2E2;color:#991B1B;border:none;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600}
        .empty-state{text-align:center;padding:60px 20px;color:#94A3B8}
        .empty-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
        .key-display{background:#F0FDF4;border:2px solid #10B981;padding:16px;border-radius:8px;margin:16px 0}
        .key-value{font-family:monospace;font-size:14px;word-break:break-all;background:white;padding:10px;border-radius:6px;margin-top:8px;direction:ltr;text-align:left}
      </style>

      <div class="ak-header">
        <h1>🔑 مفاتيح API</h1>
        <button class="ak-btn" onclick="Pages.api_keys.showAdd()">➕ مفتاح جديد</button>
      </div>

      <div id="ak-list"></div>
    `;

    await this.loadKeys();
    this.renderList();
  },

  async loadKeys() {
    try {
      const res = await App.api('/v1/admin/api-keys');
      this.keys = res.keys || [];
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
      this.keys = [];
    }
  },

  renderList() {
    const c = document.getElementById('ak-list');
    
    if (!this.keys.length) {
      c.innerHTML = `<div class="empty-state"><div class="empty-icon">🔑</div><div>لا توجد مفاتيح API</div></div>`;
      return;
    }

    c.innerHTML = this.keys.map(k => `
      <div class="ak-card">
        <div>
          <div class="ak-name">${App.escapeHtml(k.name)}</div>
          <div class="ak-prefix">${App.escapeHtml(k.key_prefix)}...</div>
        </div>
        <div>
          ${k.pharmacy_name ? `<div class="ak-pharmacy">🏥 ${App.escapeHtml(k.pharmacy_name)}</div>` : '<div class="ak-pharmacy">Global</div>'}
          <div class="ak-date">${App.formatDate(k.created_at)}</div>
        </div>
        <div class="ak-status ${k.is_active ? 'active' : 'inactive'}">${k.is_active ? '✅ نشط' : '⏸️ معطّل'}</div>
        <button class="ak-delete" onclick="Pages.api_keys.delete('${k.id}', '${App.escapeHtml(k.name)}')">🗑️ حذف</button>
      </div>
    `).join('');
  },

  showAdd() {
    const html = `
      <div style="display:flex;flex-direction:column;gap:12px">
        <div>
          <label style="font-weight:600;font-size:13px">الاسم</label>
          <input type="text" id="new-key-name" placeholder="API Key for Mobile App" style="width:100%;padding:10px;border:1px solid #E2E8F0;border-radius:8px;font-family:inherit">
        </div>
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.api_keys.create()">🔑 إنشاء</button>
    `;
    App.openModal('➕ مفتاح API جديد', html, footer);
  },

  async create() {
    const name = document.getElementById('new-key-name').value.trim() || 'API Key';

    try {
      const res = await App.api('/v1/admin/api-keys', {
        method: 'POST',
        body: JSON.stringify({ name }),
      });

      // Show the key once
      const html = `
        <div class="key-display">
          <strong style="color:#10B981">✅ تم إنشاء المفتاح بنجاح!</strong>
          <p style="margin:8px 0;font-size:13px">احفظ هذا المفتاح الآن — لن يظهر مرة أخرى!</p>
          <div class="key-value">${res.key}</div>
          <button class="btn btn-primary" style="margin-top:12px;width:100%" onclick="navigator.clipboard.writeText('${res.key}'); App.toast('✅ تم النسخ','success')">
            📋 نسخ المفتاح
          </button>
        </div>
      `;
      App.openModal('🔑 المفتاح الجديد', html, '<button class="btn btn-primary" onclick="App.closeModal(); Pages.api_keys.refresh()">تم</button>');
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async refresh() {
    await this.loadKeys();
    this.renderList();
  },

  async delete(keyId, name) {
    if (!confirm(`حذف المفتاح "${name}"؟`)) return;

    try {
      await App.api(`/v1/admin/api-keys/${keyId}`, { method: 'DELETE' });
      App.toast('✅ تم الحذف', 'success');
      await this.loadKeys();
      this.renderList();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },
};
