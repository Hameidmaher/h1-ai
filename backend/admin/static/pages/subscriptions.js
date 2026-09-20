/**
 * H1-AI — Subscriptions Management
 */
Pages.subscriptions = {
  subs: [],

  async render(el) {
    el.innerHTML = `
      <style>
        .sub-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}
        .sub-header h1{margin:0;font-size:24px}
        .sub-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}
        .sub-stat{background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0;text-align:center}
        .sub-stat-value{font-size:24px;font-weight:700;color:#0EA5E9}
        .sub-stat-label{font-size:12px;color:#64748B;margin-top:4px}
        .sub-card{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;margin-bottom:12px;display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;align-items:center}
        .sub-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.06)}
        .sub-pharmacy{font-weight:700;color:#0F172A}
        .sub-email{font-size:12px;color:#64748B;margin-top:4px}
        .sub-plan{padding:6px 12px;border-radius:20px;font-size:12px;font-weight:600;text-align:center}
        .sub-plan.basic{background:#F1F5F9;color:#475569}
        .sub-plan.pro{background:#DBEAFE;color:#1E40AF}
        .sub-plan.enterprise{background:#FCE7F3;color:#9F1239}
        .sub-status{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600;text-align:center}
        .sub-status.active{background:#DCFCE7;color:#166534}
        .sub-status.expired{background:#FEE2E2;color:#991B1B}
        .sub-status.cancelled{background:#F1F5F9;color:#475569}
        .sub-price{font-size:16px;font-weight:700;color:#0EA5E9;text-align:center}
        .sub-actions{display:flex;gap:6px}
        .sub-btn{padding:6px 12px;font-size:12px;border-radius:6px;border:none;cursor:pointer;font-weight:600;font-family:inherit}
        .sub-btn-primary{background:#0EA5E9;color:white}
        .sub-btn-ghost{background:transparent;color:#64748B;border:1px solid #E2E8F0}
        .empty-state{text-align:center;padding:60px 20px;color:#94A3B8}
        .empty-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
      </style>

      <div class="sub-header">
        <h1>💳 الاشتراكات</h1>
      </div>

      <div id="sub-stats"></div>
      <div id="sub-list"></div>
    `;

    await this.loadSubs();
    this.renderStats();
    this.renderList();
  },

  async loadSubs() {
    try {
      const res = await App.api('/v1/admin/subscriptions');
      this.subs = res.subscriptions || [];
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
      this.subs = [];
    }
  },

  renderStats() {
    const total = this.subs.length;
    const active = this.subs.filter(s => s.status === 'active').length;
    const pro = this.subs.filter(s => s.plan === 'pro').length;
    const revenue = this.subs.reduce((sum, s) => sum + (parseFloat(s.price_monthly) || 0), 0);

    document.getElementById('sub-stats').innerHTML = `
      <div class="sub-stats">
        <div class="sub-stat"><div class="sub-stat-value">${total}</div><div class="sub-stat-label">إجمالي الاشتراكات</div></div>
        <div class="sub-stat"><div class="sub-stat-value" style="color:#10B981">${active}</div><div class="sub-stat-label">نشط</div></div>
        <div class="sub-stat"><div class="sub-stat-value" style="color:#3B82F6">${pro}</div><div class="sub-stat-label">Pro</div></div>
        <div class="sub-stat"><div class="sub-stat-value">${revenue}</div><div class="sub-stat-label">الإيراد الشهري (EGP)</div></div>
      </div>
    `;
  },

  renderList() {
    const c = document.getElementById('sub-list');
    
    if (!this.subs.length) {
      c.innerHTML = `<div class="empty-state"><div class="empty-icon">💳</div><div>لا توجد اشتراكات</div></div>`;
      return;
    }

    c.innerHTML = this.subs.map(s => `
      <div class="sub-card">
        <div>
          <div class="sub-pharmacy">${App.escapeHtml(s.pharmacy_name || 'Unknown')}</div>
          <div class="sub-email">${s.plan === 'pro' ? '⭐ Pro' : s.plan === 'enterprise' ? '🏆 Enterprise' : '📦 Basic'}</div>
        </div>
        <div class="sub-plan ${s.plan}">${s.plan.toUpperCase()}</div>
        <div class="sub-status ${s.status}">${s.status === 'active' ? '✅ نشط' : s.status}</div>
        <div class="sub-actions">
          <button class="sub-btn sub-btn-primary" onclick="Pages.subscriptions.edit('${s.id}')">✏️</button>
        </div>
      </div>
    `).join('');
  },

  edit(subId) {
    const sub = this.subs.find(x => x.id === subId);
    if (!sub) return;

    const html = `
      <div style="display:flex;flex-direction:column;gap:12px">
        <div>
          <label style="font-weight:600;font-size:13px">الخطة</label>
          <select id="edit-sub-plan" style="width:100%;padding:10px;border:1px solid #E2E8F0;border-radius:8px;font-family:inherit">
            <option value="basic" ${sub.plan==='basic'?'selected':''}>Basic</option>
            <option value="pro" ${sub.plan==='pro'?'selected':''}>Pro</option>
            <option value="enterprise" ${sub.plan==='enterprise'?'selected':''}>Enterprise</option>
          </select>
        </div>
        <div>
          <label style="font-weight:600;font-size:13px">السعر الشهري</label>
          <input type="number" id="edit-sub-price" value="${sub.price_monthly}" style="width:100%;padding:10px;border:1px solid #E2E8F0;border-radius:8px;font-family:inherit">
        </div>
        <div>
          <label style="font-weight:600;font-size:13px">الحالة</label>
          <select id="edit-sub-status" style="width:100%;padding:10px;border:1px solid #E2E8F0;border-radius:8px;font-family:inherit">
            <option value="active" ${sub.status==='active'?'selected':''}>نشط</option>
            <option value="cancelled" ${sub.status==='cancelled'?'selected':''}>ملغي</option>
            <option value="expired" ${sub.status==='expired'?'selected':''}>منتهي</option>
          </select>
        </div>
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.subscriptions.saveEdit('${subId}')">💾 حفظ</button>
    `;
    App.openModal('✏️ تعديل الاشتراك', html, footer);
  },

  async saveEdit(subId) {
    const data = {
      plan: document.getElementById('edit-sub-plan').value,
      price_monthly: parseFloat(document.getElementById('edit-sub-price').value) || 0,
      status: document.getElementById('edit-sub-status').value,
    };

    try {
      await App.api(`/v1/admin/subscriptions/${subId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      App.toast('✅ تم التحديث', 'success');
      App.closeModal();
      await this.loadSubs();
      this.renderStats();
      this.renderList();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },
};
