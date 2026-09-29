/**
 * H1-AI — Pharmacies Management (Full CRUD)
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
        .ph-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
        .ph-card{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;transition:all 0.2s;position:relative}
        .ph-card:hover{box-shadow:0 8px 24px rgba(0,0,0,0.06);transform:translateY(-2px)}
        .ph-card.inactive{opacity:0.6;background:#F8FAFC}
        .ph-card-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;gap:8px}
        .ph-name{font-size:17px;font-weight:700;color:#0F172A;line-height:1.3}
        .ph-phone{font-size:13px;color:#64748B;margin-top:4px;direction:ltr;text-align:right;font-family:monospace}
        .ph-status{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap}
        .ph-status.active{background:#DCFCE7;color:#166534}
        .ph-status.inactive{background:#FEE2E2;color:#991B1B}
        .ph-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0;padding:12px 0;border-top:1px solid #F1F5F9;border-bottom:1px solid #F1F5F9}
        .ph-stat{text-align:center}
        .ph-stat-value{font-size:20px;font-weight:700;color:#0EA5E9}
        .ph-stat-label{font-size:11px;color:#64748B;margin-top:2px}
        .ph-actions{display:flex;gap:6px;margin-top:12px;flex-wrap:wrap}
        .ph-btn{padding:7px 12px;font-size:12px;border-radius:6px;border:none;cursor:pointer;font-family:inherit;font-weight:600;transition:all 0.15s;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
        .ph-btn-primary{background:#0EA5E9;color:white}
        .ph-btn-primary:hover{background:#0284C7}
        .ph-btn-ghost{background:transparent;color:#64748B;border:1px solid #E2E8F0}
        .ph-btn-ghost:hover{background:#F8FAFC}
        .ph-btn-warning{background:#FEF3C7;color:#92400E;border:1px solid #FDE68A}
        .ph-btn-warning:hover{background:#FDE68A}
        .ph-btn-success{background:#DCFCE7;color:#166534;border:1px solid #BBF7D0}
        .ph-btn-success:hover{background:#BBF7D0}
        .ph-btn-danger{background:transparent;color:#EF4444;border:1px solid #FEE2E2}
        .ph-btn-danger:hover{background:#FEE2E2}
        .empty-state{text-align:center;padding:60px 20px;color:#94A3B8}
        .empty-state-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
        /* Modal */
        .modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px}
        .modal-box{background:white;border-radius:16px;padding:24px;max-width:480px;width:100%;max-height:90vh;overflow-y:auto}
        .modal-box h3{margin:0 0 20px 0;font-size:20px}
        .modal-field{margin-bottom:14px}
        .modal-field label{display:block;margin-bottom:6px;font-weight:600;font-size:13px;color:#475569}
        .modal-field input,.modal-field select,.modal-field textarea{width:100%;padding:10px 14px;border:1px solid #E2E8F0;border-radius:8px;font-family:inherit;font-size:14px;transition:all 0.15s}
        .modal-field input:focus,.modal-field select:focus,.modal-field textarea:focus{outline:none;border-color:#0EA5E9;box-shadow:0 0 0 3px rgba(14,165,233,0.1)}
        .modal-actions{display:flex;gap:8px;margin-top:20px;justify-content:flex-end}
        .btn{padding:10px 20px;border-radius:8px;border:none;cursor:pointer;font-family:inherit;font-size:14px;font-weight:600;transition:all 0.15s}
        .btn-primary{background:#0EA5E9;color:white}
        .btn-primary:hover{background:#0284C7}
        .btn-ghost{background:transparent;color:#64748B;border:1px solid #E2E8F0}
        .btn-ghost:hover{background:#F8FAFC}
        .btn-danger{background:#EF4444;color:white}
        .btn-danger:hover{background:#DC2626}
      </style>

      <div class="ph-header">
        <h1>🏥 إدارة الصيدليات</h1>
        <button class="ph-btn ph-btn-primary" onclick="Pages.pharmacies.showAddModal()" style="padding:10px 20px;font-size:14px">
          ➕ إضافة صيدلية
        </button>
      </div>

      <div id="ph-content">
        <div class="empty-state">
          <div class="empty-state-icon">⏳</div>
          <div>جاري التحميل...</div>
        </div>
      </div>
    `;

    await this.loadAll();
    this.renderPharmacies();
  },

  async loadAll() {
    try {
      const res = await App.api('/v1/admin/pharmacies');
      this.pharmacies = res.pharmacies || [];
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
      this.pharmacies = [];
    }
  },

  renderPharmacies() {
    const c = document.getElementById('ph-content');
    
    if (!this.pharmacies.length) {
      c.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🏥</div>
          <div>لا توجد صيدليات</div>
          <button class="ph-btn ph-btn-primary" style="margin-top:16px" onclick="Pages.pharmacies.showAddModal()">
            ➕ إضافة أول صيدلية
          </button>
        </div>
      `;
      return;
    }

    c.innerHTML = `<div class="ph-grid">${this.pharmacies.map(p => this.renderCard(p)).join('')}</div>`;
  },

  renderCard(p) {
    const isActive = p.is_active !== false;
    const esc = (s) => App.escapeHtml(s || '');
    
    return `
      <div class="ph-card ${!isActive ? 'inactive' : ''}" data-id="${p.id}">
        <div class="ph-card-header">
          <div style="flex:1;min-width:0">
            <div class="ph-name">${esc(p.name_ar || p.name)}</div>
            ${p.phone ? `<div class="ph-phone">${esc(p.phone)}</div>` : ''}
          </div>
          <span class="ph-status ${isActive ? 'active' : 'inactive'}">
            ${isActive ? '✅ نشط' : '⏸️ معطّل'}
          </span>
        </div>

        <div class="ph-stats">
          <div class="ph-stat">
            <div class="ph-stat-value">${p.numbers_count || 0}</div>
            <div class="ph-stat-label">أرقام</div>
          </div>
          <div class="ph-stat">
            <div class="ph-stat-value">${p.products_count || 0}</div>
            <div class="ph-stat-label">منتجات</div>
          </div>
          <div class="ph-stat">
            <div class="ph-stat-value">${p.messages_count || 0}</div>
            <div class="ph-stat-label">رسائل</div>
          </div>
        </div>

        <div class="ph-actions">
          <button class="ph-btn ph-btn-primary" onclick="Pages.pharmacies.editPharmacy('${p.id}')">
            ✏️ تعديل
          </button>
          ${isActive ? `
            <button class="ph-btn ph-btn-warning" onclick="Pages.pharmacies.suspendPharmacy('${p.id}', '${esc(p.name_ar || p.name)}')">
              ⏸️ تعطيل
            </button>
          ` : `
            <button class="ph-btn ph-btn-success" onclick="Pages.pharmacies.activatePharmacy('${p.id}', '${esc(p.name_ar || p.name)}')">
              ▶️ تفعيل
            </button>
          `}
          <button class="ph-btn ph-btn-danger" onclick="Pages.pharmacies.deletePharmacy('${p.id}', '${esc(p.name_ar || p.name)}')">
            🗑️ حذف
          </button>
        </div>
      </div>
    `;
  },

  // ═══ EDIT ═══
  editPharmacy(pharmacyId) {
    const p = this.pharmacies.find(x => x.id === pharmacyId);
    if (!p) {
      App.toast('❌ الصيدلية غير موجودة', 'error');
      return;
    }

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'ph-modal';
    modal.innerHTML = `
      <div class="modal-box">
        <h3>✏️ تعديل بيانات الصيدلية</h3>
        
        <div class="modal-field">
          <label>الاسم (عربي)</label>
          <input type="text" id="edit-name-ar" value="${App.escapeHtml(p.name_ar || '')}" placeholder="صيدلية النور">
        </div>
        
        <div class="modal-field">
          <label>الاسم (English)</label>
          <input type="text" id="edit-name" value="${App.escapeHtml(p.name || '')}" placeholder="Al-Nour Pharmacy" dir="ltr">
        </div>
        
        <div class="modal-field">
          <label>الهاتف</label>
          <input type="tel" id="edit-phone" value="${App.escapeHtml(p.phone || '')}" placeholder="+201234567890" dir="ltr">
        </div>
        
        <div class="modal-field">
          <label>البريد الإلكتروني</label>
          <input type="email" id="edit-email" value="${App.escapeHtml(p.email || '')}" placeholder="info@pharmacy.com" dir="ltr">
        </div>
        
        <div class="modal-field">
          <label>المدينة</label>
          <input type="text" id="edit-city" value="${App.escapeHtml(p.city || '')}" placeholder="القاهرة">
        </div>
        
        <div class="modal-field">
          <label>العنوان</label>
          <textarea id="edit-address" rows="2" placeholder="العنوان الكامل">${App.escapeHtml(p.address || '')}</textarea>
        </div>
        
        <div class="modal-field">
          <label>خطة الاشتراك</label>
          <select id="edit-plan">
            <option value="basic" ${p.subscription_plan === 'basic' ? 'selected' : ''}>Basic</option>
            <option value="pro" ${p.subscription_plan === 'pro' ? 'selected' : ''}>Pro</option>
            <option value="enterprise" ${p.subscription_plan === 'enterprise' ? 'selected' : ''}>Enterprise</option>
          </select>
        </div>

        <div class="modal-actions">
          <button class="btn btn-ghost" onclick="document.getElementById('ph-modal').remove()">إلغاء</button>
          <button class="btn btn-primary" onclick="Pages.pharmacies.saveEdit('${pharmacyId}')">💾 حفظ</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  },

  async saveEdit(pharmacyId) {
    const data = {
      name_ar: document.getElementById('edit-name-ar').value.trim(),
      name: document.getElementById('edit-name').value.trim(),
      phone: document.getElementById('edit-phone').value.trim(),
      email: document.getElementById('edit-email').value.trim(),
      city: document.getElementById('edit-city').value.trim(),
      address: document.getElementById('edit-address').value.trim(),
      subscription_plan: document.getElementById('edit-plan').value,
    };

    if (!data.name_ar && !data.name) {
      App.toast('⚠️ أدخل الاسم على الأقل', 'error');
      return;
    }

    try {
      await App.api(`/v1/admin/pharmacies/${pharmacyId}/full-update`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      App.toast('✅ تم تحديث البيانات', 'success');
      document.getElementById('ph-modal').remove();
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  // ═══ SUSPEND ═══
  async suspendPharmacy(pharmacyId, name) {
    if (!confirm(`⏸️ تعطيل "${name}"؟\n\n• الرقم هيتوقف عن العمل\n• البيانات هتتحفظ\n• يمكن إعادة التفعيل`)) return;

    try {
      await App.api(`/v1/admin/pharmacies/${pharmacyId}/suspend`, { method: 'POST' });
      App.toast('⏸️ تم التعطيل', 'success');
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  // ═══ ACTIVATE ═══
  async activatePharmacy(pharmacyId, name) {
    if (!confirm(`▶️ تفعيل "${name}"؟`)) return;

    try {
      await App.api(`/v1/admin/pharmacies/${pharmacyId}/activate`, { method: 'POST' });
      App.toast('✅ تم التفعيل', 'success');
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  // ═══ DELETE (HARD) ═══
  async deletePharmacy(pharmacyId, name) {
    const confirmText = `🗑️ حذف "${name}" نهائياً؟\n\n⚠️ تحذير: هذا الإجراء لا يمكن التراجع عنه!\n\nسيتم:\n• إيقاف كل أرقام WhatsApp\n• حذف كل المنتجات\n• حذف كل الرسائل والتقارير\n• حذف كل الصيادلة\n• حذف الحساب بالكامل\n\nللتأكيد، اكتب اسم الصيدلية:`;

    const typed = prompt(confirmText);
    if (typed !== name) {
      App.toast('❌ الإلغاء — الاسم غير مطابق', 'error');
      return;
    }

    try {
      App.toast('⏳ جاري الحذف...', 'success');
      const result = await App.api(`/v1/admin/pharmacies/${pharmacyId}/hard-delete`, {
        method: 'DELETE',
      });
      
      App.toast(`✅ تم حذف "${name}" و ${result.sessions_disconnected || 0} رقم WhatsApp`, 'success');
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  // ═══ ADD ═══
  showAddModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'ph-modal';
    modal.innerHTML = `
      <div class="modal-box">
        <h3>➕ إضافة صيدلية جديدة</h3>
        
        <div class="modal-field">
          <label>الاسم (عربي) *</label>
          <input type="text" id="add-name-ar" placeholder="صيدلية النور">
        </div>
        
        <div class="modal-field">
          <label>الاسم (English)</label>
          <input type="text" id="add-name" placeholder="Al-Nour Pharmacy" dir="ltr">
        </div>
        
        <div class="modal-field">
          <label>الهاتف</label>
          <input type="tel" id="add-phone" placeholder="+201234567890" dir="ltr">
        </div>
        
        <div class="modal-field">
          <label>البريد الإلكتروني</label>
          <input type="email" id="add-email" placeholder="info@pharmacy.com" dir="ltr">
        </div>
        
        <div class="modal-field">
          <label>المدينة</label>
          <input type="text" id="add-city" placeholder="القاهرة">
        </div>

        <div class="modal-actions">
          <button class="btn btn-ghost" onclick="document.getElementById('ph-modal').remove()">إلغاء</button>
          <button class="btn btn-primary" onclick="Pages.pharmacies.createPharmacy()">💾 إنشاء</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  },

  async createPharmacy() {
    const data = {
      name_ar: document.getElementById('add-name-ar').value.trim(),
      name: document.getElementById('add-name').value.trim(),
      phone: document.getElementById('add-phone').value.trim(),
      email: document.getElementById('add-email').value.trim(),
      city: document.getElementById('add-city').value.trim(),
    };

    if (!data.name_ar && !data.name) {
      App.toast('⚠️ أدخل الاسم على الأقل', 'error');
      return;
    }

    try {
      await App.api('/v1/admin/pharmacies', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      App.toast('✅ تم إنشاء الصيدلية', 'success');
      document.getElementById('ph-modal').remove();
      await this.loadAll();
      this.renderPharmacies();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },
};
