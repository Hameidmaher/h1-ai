/**
 * H1-AI — Pharmacies & WhatsApp Numbers
 */
Pages.pharmacies = {
  pharmacies: [],
  allNumbers: [],

  async render(el) {
    el.innerHTML = `
      <style>
        .ph-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}
        .ph-header h1{margin:0;font-size:24px}
        .ph-tabs{display:flex;gap:4px;border-bottom:2px solid #E2E8F0;margin-bottom:20px;overflow-x:auto}
        .ph-tab{padding:10px 20px;background:none;border:none;cursor:pointer;font-family:inherit;font-size:14px;font-weight:600;color:#64748B;border-bottom:2px solid transparent;margin-bottom:-2px;white-space:nowrap}
        .ph-tab.active{color:#0EA5E9;border-bottom-color:#0EA5E9}
        .ph-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
        .ph-card{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;transition:all 0.2s}
        .ph-card:hover{box-shadow:0 8px 24px rgba(0,0,0,0.06);transform:translateY(-2px)}
        .ph-card-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}
        .ph-name{font-size:17px;font-weight:700;color:#0F172A}
        .ph-phone{font-size:13px;color:#64748B;margin-top:2px;direction:ltr;text-align:right}
        .ph-status{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600}
        .ph-status.active{background:#DCFCE7;color:#166534}
        .ph-status.inactive{background:#FEE2E2;color:#991B1B}
        .ph-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0;padding:12px 0;border-top:1px solid #F1F5F9;border-bottom:1px solid #F1F5F9}
        .ph-stat{text-align:center}
        .ph-stat-value{font-size:20px;font-weight:700;color:#0EA5E9}
        .ph-stat-label{font-size:11px;color:#64748B;margin-top:2px}
        .ph-actions{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
        .ph-btn{padding:6px 12px;font-size:12px;border-radius:6px;border:none;cursor:pointer;font-family:inherit;font-weight:600;transition:all 0.15s}
        .ph-btn-primary{background:#0EA5E9;color:white}
        .ph-btn-primary:hover{background:#0284C7}
        .ph-btn-ghost{background:transparent;color:#64748B;border:1px solid #E2E8F0}
        .ph-btn-ghost:hover{background:#F8FAFC}
        .ph-btn-danger{background:transparent;color:#EF4444;border:1px solid #FEE2E2}
        .ph-btn-danger:hover{background:#FEE2E2}
        .wa-number{display:flex;justify-content:space-between;align-items:center;padding:12px;background:#F8FAFC;border-radius:8px;margin-bottom:8px;border:1px solid #E2E8F0}
        .wa-number.primary{background:#EFF6FF;border-color:#BFDBFE}
        .wa-phone{font-weight:700;font-size:14px;direction:ltr;text-align:right;color:#0F172A}
        .wa-name{font-size:12px;color:#64748B;margin-top:2px}
        .wa-mode{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;margin-top:4px}
        .wa-mode.link{background:#DBEAFE;color:#1E40AF}
        .wa-mode.qr{background:#FEF3C7;color:#92400E}
        .wa-mode.api{background:#DCFCE7;color:#166534}
        .wa-primary-badge{background:#0EA5E9;color:white;font-size:10px;padding:2px 8px;border-radius:10px;margin-right:6px}
        .wa-actions{display:flex;gap:4px;flex-shrink:0}
        .wa-actions button{width:32px;height:32px;border-radius:6px;border:1px solid #E2E8F0;background:white;cursor:pointer;font-size:14px}
        .wa-actions button:hover{background:#F1F5F9}
        .empty-state{text-align:center;padding:60px 20px;color:#94A3B8}
        .empty-state-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
      </style>

      <div class="ph-header">
        <h1>🏥 الصيدليات وأرقام WhatsApp</h1>
        <button class="ph-btn ph-btn-primary" onclick="Pages.pharmacies.showAddPharmacy()" style="padding:10px 20px;font-size:14px">
          ➕ إضافة صيدلية
        </button>
      </div>

      <div class="ph-tabs">
        <button class="ph-tab active" onclick="Pages.pharmacies.switchTab('pharmacies')" id="tab-pharmacies">🏥 الصيدليات</button>
        <button class="ph-tab" onclick="Pages.pharmacies.switchTab('whatsapp')" id="tab-whatsapp">📱 كل أرقام WhatsApp</button>
      </div>

      <div id="ph-content"></div>
    `;

    await this.loadAll();
    this.renderPharmacies();
  },

  async loadAll() {
    try {
      const [phRes, waRes] = await Promise.all([
        App.api('/v1/admin/pharmacies'),
        App.api('/v1/admin/whatsapp'),
      ]);
      this.pharmacies = phRes.pharmacies || [];
      this.allNumbers = waRes.numbers || [];
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  switchTab(tab) {
    document.querySelectorAll('.ph-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');
    if (tab === 'pharmacies') this.renderPharmacies();
    else this.renderAllWhatsApp();
  },

  renderPharmacies() {
    const c = document.getElementById('ph-content');
    if (!this.pharmacies.length) {
      c.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🏥</div><div>لا توجد صيدليات</div></div>`;
      return;
    }
    c.innerHTML = `<div class="ph-grid">${this.pharmacies.map(p => `
      <div class="ph-card">
        <div class="ph-card-header">
          <div>
            <div class="ph-name">${App.escapeHtml(p.name_ar || p.name)}</div>
            ${p.phone ? `<div class="ph-phone">${p.phone}</div>` : ''}
          </div>
          <span class="ph-status ${p.is_active ? 'active' : 'inactive'}">
            ${p.is_active ? '✅ نشط' : '⏸️ معطّل'}
          </span>
        </div>
        <div class="ph-stats">
          <div class="ph-stat"><div class="ph-stat-value">${p.numbers_count || 0}</div><div class="ph-stat-label">أرقام</div></div>
          <div class="ph-stat"><div class="ph-stat-value">${p.products_count || 0}</div><div class="ph-stat-label">منتجات</div></div>
          <div class="ph-stat"><div class="ph-stat-value">${p.messages_count || 0}</div><div class="ph-stat-label">رسائل</div></div>
        </div>
        <div class="ph-actions">
          <button class="ph-btn ph-btn-primary" onclick="Pages.pharmacies.showNumbers('${p.id}')">📱 الأرقام</button>
          <button class="ph-btn ph-btn-ghost" onclick="Pages.pharmacies.showAddNumber('${p.id}')">➕ رقم</button>
          <button class="ph-btn ph-btn-danger" onclick="Pages.pharmacies.deletePharmacy('${p.id}', '${App.escapeHtml(p.name_ar || p.name)}')">🗑️</button>
        </div>
      </div>
    `).join('')}</div>`;
  },

  renderAllWhatsApp() {
    const c = document.getElementById('ph-content');
    if (!this.allNumbers.length) {
      c.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📱</div><div>لا توجد أرقام</div></div>`;
      return;
    }
    // Stats header
    const total = this.allNumbers.length;
    const active = this.allNumbers.filter(n => n.is_active).length;
    const byMode = { link: 0, qr: 0, api: 0 };
    this.allNumbers.forEach(n => { byMode[n.mode] = (byMode[n.mode] || 0) + 1; });

    // Group by pharmacy
    const grouped = {};
    this.allNumbers.forEach(n => {
      const k = n.pharmacy_name || 'غير محدد';
      if (!grouped[k]) grouped[k] = [];
      grouped[k].push(n);
    });

    c.innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px">
        <div class="ph-card" style="text-align:center">
          <div class="ph-stat-value">${total}</div>
          <div class="ph-stat-label">إجمالي الأرقام</div>
        </div>
        <div class="ph-card" style="text-align:center">
          <div class="ph-stat-value" style="color:#10B981">${active}</div>
          <div class="ph-stat-label">نشط</div>
        </div>
        <div class="ph-card" style="text-align:center">
          <div class="ph-stat-value">${byMode.link || 0}</div>
          <div class="ph-stat-label">🔗 Link</div>
        </div>
        <div class="ph-card" style="text-align:center">
          <div class="ph-stat-value">${byMode.qr || 0}</div>
          <div class="ph-stat-label">📷 QR</div>
        </div>
        <div class="ph-card" style="text-align:center">
          <div class="ph-stat-value">${byMode.api || 0}</div>
          <div class="ph-stat-label">🔌 API</div>
        </div>
      </div>

      ${Object.entries(grouped).map(([ph, numbers]) => `
        <div style="margin-bottom:24px">
          <h3 style="margin-bottom:12px;font-size:16px;color:#475569">
            🏥 ${App.escapeHtml(ph)}
            <span style="font-size:12px;color:#94A3B8;font-weight:normal">(${numbers.length} رقم)</span>
          </h3>
          ${numbers.map(n => this.renderNumberCard(n)).join('')}
        </div>
      `).join('')}
    `;
  },

  renderNumberCard(n) {
    const modeLabel = { link: '🔗 Link', qr: '📷 QR', api: '🔌 API' };
    return `
      <div class="wa-number ${n.is_primary ? 'primary' : ''}">
        <div style="flex:1">
          <div class="wa-phone">
            ${n.is_primary ? '<span class="wa-primary-badge">⭐ رئيسي</span>' : ''}
            ${n.phone_number}
          </div>
          <div class="wa-name">${App.escapeHtml(n.display_name || 'بدون اسم')}</div>
          <span class="wa-mode ${n.mode}">${modeLabel[n.mode] || n.mode}</span>
          ${!n.is_active ? '<span style="color:#EF4444;font-size:11px;margin-right:6px">⏸️ معطّل</span>' : ''}
        </div>
        <div class="wa-actions">
          <button onclick="Pages.pharmacies.toggleActive('${n.id}', ${n.is_active})" title="${n.is_active ? 'تعطيل' : 'تفعيل'}">
            ${n.is_active ? '⏸️' : '▶️'}
          </button>
          <button onclick="Pages.pharmacies.deleteNumber('${n.id}', '${n.phone_number}')" title="حذف">🗑️</button>
        </div>
      </div>
    `;
  },

  showAddPharmacy() {
    const html = `
      <div style="display:flex;flex-direction:column;gap:12px">
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">الاسم (عربي)</label>
          <input type="text" id="new-ph-name-ar" class="settings-input" style="width:100%" placeholder="صيدلية النور"></div>
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">الاسم (English)</label>
          <input type="text" id="new-ph-name" class="settings-input" style="width:100%" placeholder="Al-Nour Pharmacy" dir="ltr"></div>
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">الهاتف</label>
          <input type="tel" id="new-ph-phone" class="settings-input" style="width:100%" placeholder="+201234567890" dir="ltr"></div>
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">المدينة</label>
          <input type="text" id="new-ph-city" class="settings-input" style="width:100%" placeholder="القاهرة"></div>
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">البريد الإلكتروني</label>
          <input type="email" id="new-ph-email" class="settings-input" style="width:100%" placeholder="info@pharmacy.com" dir="ltr"></div>
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.pharmacies.createPharmacy()">💾 حفظ</button>
    `;
    App.openModal('➕ إضافة صيدلية', html, footer);
  },

  async createPharmacy() {
    const data = {
      name: document.getElementById('new-ph-name').value.trim(),
      name_ar: document.getElementById('new-ph-name-ar').value.trim(),
      phone: document.getElementById('new-ph-phone').value.trim(),
      city: document.getElementById('new-ph-city').value.trim(),
      email: document.getElementById('new-ph-email').value.trim(),
    };
    if (!data.name && !data.name_ar) {
      App.toast('⚠️ املأ الاسم على الأقل', 'error');
      return;
    }
    try {
      await App.api('/v1/admin/pharmacies', { method: 'POST', body: JSON.stringify(data) });
      App.toast('✅ تم إنشاء الصيدلية', 'success');
      App.closeModal();
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  showAddNumber(pharmacyId) {
    const html = `
      <div style="display:flex;flex-direction:column;gap:12px">
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">رقم WhatsApp</label>
          <input type="tel" id="new-wa-phone" class="settings-input" style="width:100%" placeholder="+201234567890" dir="ltr"></div>
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">اسم الرقم (اختياري)</label>
          <input type="text" id="new-wa-name" class="settings-input" style="width:100%" placeholder="الفرع الرئيسي"></div>
        <div><label style="display:block;margin-bottom:4px;font-weight:600;font-size:14px">الوضع</label>
          <select id="new-wa-mode" class="settings-input" style="width:100%">
            <option value="link">🔗 Link (رابط)</option>
            <option value="qr">📷 QR Code</option>
            <option value="api">🔌 API</option>
          </select></div>
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.pharmacies.createNumber('${pharmacyId}')">💾 حفظ</button>
    `;
    App.openModal('➕ إضافة رقم WhatsApp', html, footer);
  },

  async createNumber(pharmacyId) {
    const data = {
      phone_number: document.getElementById('new-wa-phone').value.trim(),
      display_name: document.getElementById('new-wa-name').value.trim(),
      mode: document.getElementById('new-wa-mode').value,
    };
    if (!data.phone_number) {
      App.toast('⚠️ أدخل رقم WhatsApp', 'error');
      return;
    }
    try {
      await App.api(`/v1/admin/pharmacies/${pharmacyId}/whatsapp`, {
        method: 'POST', body: JSON.stringify(data)
      });
      App.toast('✅ تم إضافة الرقم', 'success');
      App.closeModal();
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async showNumbers(pharmacyId) {
    const pharmacy = this.pharmacies.find(p => p.id === pharmacyId);
    const numbers = this.allNumbers.filter(n => n.pharmacy_id === pharmacyId);
    
    if (!numbers.length) {
      App.toast('لا توجد أرقام لهذه الصيدلية', 'success');
      return;
    }

    const html = numbers.map(n => this.renderNumberCard(n)).join('');
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إغلاق</button>
      <button class="btn btn-primary" onclick="App.closeModal(); Pages.pharmacies.showAddNumber('${pharmacyId}')">➕ إضافة رقم</button>
    `;
    App.openModal(`📱 أرقام ${pharmacy?.name_ar || pharmacy?.name || 'الصيدلية'}`, html, footer);
  },

  async toggleActive(numberId, isActive) {
    try {
      await App.api(`/v1/admin/whatsapp/${numberId}`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: !isActive }),
      });
      App.toast(isActive ? '⏸️ تم التعطيل' : '✅ تم التفعيل', 'success');
      await this.loadAll();
      if (document.getElementById('tab-whatsapp').classList.contains('active')) {
        this.renderAllWhatsApp();
      } else {
        this.renderPharmacies();
      }
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async deleteNumber(numberId, phone) {
    if (!confirm(`حذف الرقم ${phone}؟`)) return;
    try {
      await App.api(`/v1/admin/whatsapp/${numberId}`, { method: 'DELETE' });
      App.toast('✅ تم الحذف', 'success');
      await this.loadAll();
      if (document.getElementById('tab-whatsapp').classList.contains('active')) {
        this.renderAllWhatsApp();
      } else {
        this.renderPharmacies();
      }
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async deletePharmacy(id, name) {
    if (!confirm(`حذف الصيدلية "${name}"؟`)) return;
    try {
      await App.api(`/v1/admin/pharmacies/${id}`, { method: 'DELETE' });
      App.toast('✅ تم الحذف', 'success');
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },
};
