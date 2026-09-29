/**
 * H1-AI — WhatsApp Sessions Management
 */
Pages.whatsapp_sessions = {
  sessions: [],
  refreshInterval: null,
  currentQR: null,

  async render(el) {
    el.innerHTML = `
      <style>
        .wa-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}
        .wa-header h1{margin:0;font-size:24px}
        .wa-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}
        .wa-stat{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;text-align:center}
        .wa-stat-value{font-size:28px;font-weight:700;color:#0EA5E9}
        .wa-stat-value.green{color:#10B981}
        .wa-stat-value.gray{color:#94A3B8}
        .wa-stat-label{font-size:12px;color:#64748B;margin-top:4px}
        .wa-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
        .wa-card{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;transition:all 0.2s;position:relative}
        .wa-card:hover{box-shadow:0 8px 24px rgba(0,0,0,0.06);transform:translateY(-2px)}
        .wa-card.connected{border-left:4px solid #10B981}
        .wa-card.waiting{border-left:4px solid #F59E0B}
        .wa-card.disconnected{border-left:4px solid #EF4444}
        .wa-phone{font-size:18px;font-weight:700;color:#0F172A;direction:ltr;text-align:right;margin-bottom:8px}
        .wa-status{display:inline-block;padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600}
        .wa-status.connected{background:#DCFCE7;color:#166534}
        .wa-status.waiting{background:#FEF3C7;color:#92400E}
        .wa-status.disconnected{background:#FEE2E2;color:#991B1B}
        .wa-status.init{background:#E0E7FF;color:#3730A3}
        .wa-pharmacy{font-size:13px;color:#64748B;margin-top:8px}
        .wa-actions{display:flex;gap:8px;margin-top:12px}
        .wa-btn{padding:8px 14px;border-radius:8px;border:none;cursor:pointer;font-family:inherit;font-size:13px;font-weight:600;transition:all 0.15s;display:inline-flex;align-items:center;gap:6px}
        .wa-btn-primary{background:#0EA5E9;color:white}
        .wa-btn-primary:hover{background:#0284C7}
        .wa-btn-danger{background:transparent;color:#EF4444;border:1px solid #FEE2E2}
        .wa-btn-danger:hover{background:#FEE2E2}
        .wa-btn-ghost{background:transparent;color:#64748B;border:1px solid #E2E8F0}
        .wa-btn-ghost:hover{background:#F8FAFC}
        .wa-qr-container{background:white;border-radius:16px;padding:32px;border:2px solid #0EA5E9;text-align:center;margin-bottom:20px}
        .wa-qr-container h2{color:#0EA5E9;margin-bottom:12px}
        .wa-qr-image{max-width:320px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);margin:16px auto;display:block}
        .wa-qr-hint{font-size:13px;color:#64748B;margin-top:16px;line-height:1.6}
        .wa-qr-hint strong{color:#0EA5E9}
        .wa-empty{text-align:center;padding:60px 20px;color:#94A3B8}
        .wa-empty-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
        .modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px}
        .modal-box{background:white;border-radius:16px;padding:24px;max-width:400px;width:100%;max-height:90vh;overflow-y:auto}
        .modal-box h3{margin-bottom:16px;font-size:18px}
        .modal-field{margin-bottom:12px}
        .modal-field label{display:block;margin-bottom:6px;font-weight:600;font-size:13px;color:#475569}
        .modal-field input,.modal-field select{width:100%;padding:10px 14px;border:1px solid #E2E8F0;border-radius:8px;font-family:inherit;font-size:14px}
        .modal-field input:focus,.modal-field select:focus{outline:none;border-color:#0EA5E9}
        .modal-actions{display:flex;gap:8px;margin-top:20px;justify-content:flex-end}
      </style>

      <div class="wa-header">
        <h1>📱 أرقام WhatsApp المتصلة</h1>
        <button class="wa-btn wa-btn-primary" onclick="Pages.whatsapp_sessions.showAddModal()" style="padding:12px 24px;font-size:14px">
          ➕ إضافة رقم جديد
        </button>
      </div>

      <div id="wa-stats"></div>
      <div id="wa-qr-area"></div>
      <div id="wa-sessions"></div>
    `;

    await this.loadSessions();
    this.renderSessions();
    this.startAutoRefresh();
  },

  async loadSessions() {
    try {
      const [health, sessions] = await Promise.all([
        App.api('/v1/admin/whatsapp-service/health'),
        App.api('/v1/admin/whatsapp-service/sessions'),
      ]);
      this.health = health;
      this.sessions = sessions.sessions || [];
    } catch (e) {
      console.error('Load sessions error:', e);
      this.sessions = [];
    }
  },

  renderSessions() {
    // Stats
    const statsEl = document.getElementById('wa-stats');
    const total = this.sessions.length;
    const connected = this.sessions.filter(s => s.status === 'connected').length;
    const waiting = this.sessions.filter(s => s.status === 'waiting_qr').length;

    statsEl.innerHTML = `
      <div class="wa-stats">
        <div class="wa-stat">
          <div class="wa-stat-value">${total}</div>
          <div class="wa-stat-label">إجمالي الأرقام</div>
        </div>
        <div class="wa-stat">
          <div class="wa-stat-value green">${connected}</div>
          <div class="wa-stat-label">متصلة</div>
        </div>
        <div class="wa-stat">
          <div class="wa-stat-value" style="color:#F59E0B">${waiting}</div>
          <div class="wa-stat-label">بانتظار QR</div>
        </div>
      </div>
    `;

    // Sessions list
    const el = document.getElementById('wa-sessions');
    if (!this.sessions.length) {
      el.innerHTML = `
        <div class="wa-empty">
          <div class="wa-empty-icon">📱</div>
          <div>لا توجد أرقام WhatsApp متصلة</div>
          <button class="wa-btn wa-btn-primary" style="margin-top:20px" onclick="Pages.whatsapp_sessions.showAddModal()">
            ➕ إضافة أول رقم
          </button>
        </div>
      `;
      return;
    }

    el.innerHTML = `<div class="wa-grid">${this.sessions.map(s => this.renderSessionCard(s)).join('')}</div>`;
  },

  renderSessionCard(s) {
    const statusLabels = {
      connected: '✅ متصل',
      waiting_qr: '⏳ بانتظار QR',
      disconnected: '❌ غير متصل',
      suspended: '⏸️ موقوف',
      initializing: '🔄 جاري التهيئة',
      not_found: '⚪ غير موجود',
    };
    const statusClass = {
      connected: 'connected',
      waiting_qr: 'waiting',
      disconnected: 'disconnected',
      suspended: 'suspended',
      initializing: 'init',
    }[s.status] || 'init';

    const cardClass = {
      connected: 'connected',
      waiting_qr: 'waiting',
      disconnected: 'disconnected',
      suspended: 'suspended',
    }[s.status] || '';

    return `
      <div class="wa-card ${cardClass}">
        <div class="wa-phone">${s.phone_number || 'Unknown'}</div>
        <span class="wa-status ${statusClass}">${statusLabels[s.status] || s.status}</span>
        ${s.pharmacy_id ? `<div class="wa-pharmacy">🏥 صيدلية: ${s.pharmacy_id.substring(0, 8)}...</div>` : ''}
        
        <div class="wa-actions">
          ${s.status === 'waiting_qr' ? `
            <button class="wa-btn wa-btn-primary" onclick="Pages.whatsapp_sessions.showQR('${s.phone_number}')">
              📷 عرض QR
            </button>
          ` : ''}
          ${s.status === 'connected' ? `
            <button class="wa-btn wa-btn-ghost" onclick="Pages.whatsapp_sessions.sendTest('${s.phone_number}')">
              📤 اختبار
            </button>
            <button class="wa-btn wa-btn-warning" onclick="Pages.whatsapp_sessions.suspendSession('${s.phone_number}')">
              ⏸️ إيقاف
            </button>
          ` : ''}
          ${s.status === 'suspended' || s.status === 'disconnected' ? `
            <button class="wa-btn wa-btn-success" onclick="Pages.whatsapp_sessions.activateSession('${s.phone_number}')">
              ▶️ تفعيل
            </button>
          ` : ''}
          <button class="wa-btn wa-btn-danger" onclick="Pages.whatsapp_sessions.deleteSessionCompletely('${s.phone_number}')">
            🗑️ حذف نهائي
          </button>
        </div>
      </div>
    `;
  },

  async showQR(phone) {
    const qrArea = document.getElementById('wa-qr-area');
    qrArea.innerHTML = '<div style="text-align:center;padding:20px">⏳ جاري تحميل QR...</div>';

    try {
      const data = await App.api(`/v1/admin/whatsapp-service/sessions/${encodeURIComponent(phone)}/qr`);
      
      if (!data.qr_image) {
        qrArea.innerHTML = `
          <div class="wa-qr-container">
            <h2>⚠️ لم يتم تحميل QR</h2>
            <p style="color:#64748B">حالة: ${data.status || 'غير معروف'}</p>
            <button class="wa-btn wa-btn-ghost" style="margin-top:16px" onclick="document.getElementById('wa-qr-area').innerHTML=''">إغلاق</button>
          </div>
        `;
        return;
      }

      this.currentQR = phone;

      qrArea.innerHTML = `
        <div class="wa-qr-container">
          <h2>📱 امسح QR للاتصال برقم ${phone}</h2>
          <img class="wa-qr-image" src="${data.qr_image}" alt="QR Code">
          <div class="wa-qr-hint">
            <strong>الخطوات:</strong><br>
            1. افتح WhatsApp على الموبايل<br>
            2. اضغط Settings (⚙️) → Linked Devices<br>
            3. اضغط "Link a Device"<br>
            4. امسح الـ QR من الشاشة<br>
            <br>
            <em>⚠️ الـ QR صالح لدقيقة واحدة فقط</em>
          </div>
          <button class="wa-btn wa-btn-ghost" style="margin-top:16px" onclick="Pages.whatsapp_sessions.closeQR()">
            إغلاق
          </button>
        </div>
      `;

      // Scroll to QR
      qrArea.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // Auto-refresh QR every 20 seconds
      setTimeout(() => {
        if (this.currentQR === phone) {
          this.showQR(phone);
        }
      }, 20000);

    } catch (e) {
      qrArea.innerHTML = `<div style="text-align:center;padding:20px;color:#EF4444">❌ ${e.message}</div>`;
    }
  },

  closeQR() {
    this.currentQR = null;
    document.getElementById('wa-qr-area').innerHTML = '';
  },

  showAddModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'wa-add-modal';
    modal.innerHTML = `
      <div class="modal-box">
        <h3>➕ إضافة رقم WhatsApp جديد</h3>
        <div class="modal-field">
          <label>رقم WhatsApp (بصيغة دولية)</label>
          <input type="tel" id="wa-new-phone" placeholder="+201234567890" dir="ltr">
        </div>
        <div class="modal-field">
          <label>الصيدلية (اختياري)</label>
          <select id="wa-new-pharmacy">
            <option value="">— بدون —</option>
            <option value="00000000-0000-0000-0000-000000000001">صيدلية H1-AI الافتراضية</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="wa-btn wa-btn-ghost" onclick="document.getElementById('wa-add-modal').remove()">إلغاء</button>
          <button class="wa-btn wa-btn-primary" onclick="Pages.whatsapp_sessions.createSession()">إنشاء Session</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  },

  async createSession() {
    const phone = document.getElementById('wa-new-phone').value.trim();
    const pharmacy = document.getElementById('wa-new-pharmacy').value;

    if (!phone) {
      App.toast('⚠️ أدخل رقم WhatsApp', 'error');
      return;
    }

    try {
      App.toast('⏳ جاري إنشاء Session...', 'success');
      const result = await App.api('/v1/admin/whatsapp-service/sessions', {
        method: 'POST',
        body: JSON.stringify({
          phone_number: phone,
          pharmacy_id: pharmacy || null,
        }),
      });

      if (result.success) {
        App.toast('✅ تم إنشاء Session — جاري تحميل QR', 'success');
        document.getElementById('wa-add-modal').remove();
        
        // Reload
        await this.loadSessions();
        this.renderSessions();

        // Show QR after 3 seconds
        setTimeout(() => this.showQR(phone), 3000);
      } else {
        App.toast(`❌ ${result.error || 'فشل'}`, 'error');
      }
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async suspendSession(phone) {
    if (!confirm(`⏸️ إيقاف الرقم ${phone}؟\n\nسيتم قطع الاتصال لكن الرقم سيبقى في القائمة لإعادة التفعيل.`)) return;

    try {
      App.toast('⏳ جاري الإيقاف...', 'success');
      await App.api(`/v1/admin/whatsapp-service/sessions/${encodeURIComponent(phone)}/disconnect`, {
        method: 'POST',
      });
      App.toast('⏸️ تم إيقاف الرقم', 'success');
      await this.loadSessions();
      this.renderSessions();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async activateSession(phone) {
    if (!confirm(`▶️ إعادة تفعيل الرقم ${phone}؟\n\nسيتم إنشاء QR جديد لمسحه.`)) return;

    try {
      App.toast('⏳ جاري التفعيل...', 'success');
      await App.api(`/v1/admin/whatsapp-service/sessions/${encodeURIComponent(phone)}/activate`, {
        method: 'POST',
      });
      App.toast('✅ جاري تحميل QR...', 'success');
      await this.loadSessions();
      this.renderSessions();
      
      // Show QR after 3 seconds
      setTimeout(() => this.showQR(phone), 3000);
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async deleteSessionCompletely(phone) {
    if (!confirm(`🗑️ حذف الرقم ${phone} نهائياً؟\n\n⚠️ تحذير: سيتم:\n• قطع الاتصال\n• حذف الملفات\n• حذف السجل من قاعدة البيانات\n\nلا يمكن التراجع!`)) return;

    try {
      App.toast('⏳ جاري الحذف...', 'success');
      await App.api(`/v1/admin/whatsapp-service/sessions/${encodeURIComponent(phone)}/delete-all`, {
        method: 'DELETE',
      });
      App.toast('✅ تم الحذف نهائياً', 'success');
      await this.loadSessions();
      this.renderSessions();
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  async sendTest(phone) {
    const to = prompt('رقم المستقبل (بصيغة دولية):', '+201000000000');
    if (!to) return;

    const message = prompt('نص الرسالة:', 'اختبار من H1-AI ✅');
    if (!message) return;

    try {
      await App.api('/v1/admin/whatsapp-service/send', {
        method: 'POST',
        body: JSON.stringify({
          phone_number: phone,
          to: to,
          message: message,
        }),
      });
      App.toast('✅ تم إرسال الرسالة', 'success');
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  startAutoRefresh() {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    this.refreshInterval = setInterval(async () => {
      // Only refresh if not showing QR
      if (this.currentQR) return;
      await this.loadSessions();
      this.renderSessions();
    }, 10000);
  },

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  },
};
