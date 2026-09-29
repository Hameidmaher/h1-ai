/**
 * H1-AI — Settings Page (Interactive)
 */
Pages.settings = {
  originalWhatsApp: null,

  async render(el) {
    el.innerHTML = `
      <style>
        .settings-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.06);
          border: 1px solid #E2E8F0;
        }
        .settings-section h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
          color: #0F172A;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .settings-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #F1F5F9;
        }
        .settings-row:last-child { border-bottom: none; }
        .settings-label {
          font-weight: 500;
          color: #475569;
          font-size: 14px;
        }
        .settings-value {
          color: #0F172A;
          font-family: 'Courier New', monospace;
          font-size: 13px;
          direction: ltr;
        }
        .settings-input {
          padding: 8px 12px;
          border: 1px solid #E2E8F0;
          border-radius: 8px;
          font-size: 14px;
          font-family: inherit;
          width: 300px;
          max-width: 100%;
          transition: border-color 0.15s;
        }
        .settings-input:focus {
          outline: none;
          border-color: #0EA5E9;
          box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
        }
        .settings-toggle {
          position: relative;
          display: inline-block;
          width: 52px;
          height: 28px;
        }
        .settings-toggle input {
          opacity: 0;
          width: 0;
          height: 0;
        }
        .settings-toggle-slider {
          position: absolute;
          cursor: pointer;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: #CBD5E1;
          border-radius: 28px;
          transition: 0.3s;
        }
        .settings-toggle-slider::before {
          content: "";
          position: absolute;
          height: 22px;
          width: 22px;
          left: 3px;
          bottom: 3px;
          background-color: white;
          border-radius: 50%;
          transition: 0.3s;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .settings-toggle input:checked + .settings-toggle-slider {
          background-color: #10B981;
        }
        .settings-toggle input:checked + .settings-toggle-slider::before {
          transform: translateX(24px);
        }
        .settings-actions {
          display: flex;
          gap: 12px;
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid #F1F5F9;
        }
        .btn-save {
          padding: 10px 24px;
          background: #0EA5E9;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s;
        }
        .btn-save:hover:not(:disabled) {
          background: #0284C7;
          transform: translateY(-1px);
        }
        .btn-save:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .btn-reset {
          padding: 10px 24px;
          background: white;
          color: #64748B;
          border: 1px solid #E2E8F0;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
        }
        .btn-reset:hover {
          background: #F8FAFC;
          border-color: #CBD5E1;
        }
        .settings-hint {
          font-size: 12px;
          color: #94A3B8;
          margin-top: 8px;
          font-style: italic;
        }
        .settings-badge {
          padding: 3px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 600;
        }
        .settings-badge.on {
          background: #DCFCE7;
          color: #166534;
        }
        .settings-badge.off {
          background: #FEE2E2;
          color: #991B1B;
        }
      </style>

      <h1>⚙️ الإعدادات</h1>
      <p class="settings-hint">💡 يمكنك تعديل الإعدادات وحفظها مباشرة (بدون إعادة تشغيل)</p>

      <div id="settings-content">
        <div class="settings-section">
          <h3>⏳ جاري التحميل...</h3>
        </div>
      </div>
    `;

    await this.loadSettings();
  },

  async loadSettings() {
    const container = document.getElementById('settings-content');
    try {
      const settings = await App.api('/v1/admin/settings/whatsapp');
      this.originalWhatsApp = JSON.parse(JSON.stringify(settings));

      container.innerHTML = `
        <div class="settings-section">
          <h3>📱 WhatsApp</h3>

          <div class="settings-row">
            <span class="settings-label">مُفعّل</span>
            <label class="settings-toggle">
              <input type="checkbox" id="wa-enabled" ${settings.enabled ? 'checked' : ''}>
              <span class="settings-toggle-slider"></span>
            </label>
          </div>

          <div class="settings-row">
            <span class="settings-label">رقم الواتس</span>
            <input type="tel" id="wa-phone" class="settings-input"
                   value="${settings.phone || ''}"
                   placeholder="+201234567890"
                   dir="ltr">
          </div>

          <div class="settings-row">
            <span class="settings-label">رقم العرض</span>
            <input type="text" id="wa-display-phone" class="settings-input"
                   value="${settings.display_phone || ''}"
                   placeholder="0123 456 7890"
                   dir="rtl">
          </div>

          <div class="settings-row">
            <span class="settings-label">الوضع</span>
            <select id="wa-mode" class="settings-input">
              <option value="link" ${settings.mode === 'link' ? 'selected' : ''}>🔗 Link (رابط)</option>
              <option value="qr" ${settings.mode === 'qr' ? 'selected' : ''}>📷 QR Code</option>
              <option value="api" ${settings.mode === 'api' ? 'selected' : ''}>🔌 API</option>
            </select>
          </div>

          <div class="settings-hint">
            ⚠️ الرقم لازم يبدأ بـ + أو يكون أرقام فقط
          </div>

          <div class="settings-actions">
            <button class="btn-save" id="btn-save-wa" onclick="Pages.settings.saveWhatsApp()">
              💾 حفظ
            </button>
            <button class="btn-reset" onclick="Pages.settings.resetWhatsApp()">
              ↺ إعادة تعيين
            </button>
          </div>
        </div>

        <div class="settings-section">
          <h3>ℹ️ معلومات النظام</h3>
          <div class="settings-row">
            <span class="settings-label">الإصدار</span>
            <span class="settings-value">H1-AI v5.0.0</span>
          </div>
          <div class="settings-row">
            <span class="settings-label">المستخدم</span>
            <span class="settings-value">${App.state.user?.username || 'admin'}</span>
          </div>
          <div class="settings-row">
            <span class="settings-label">الدور</span>
            <span class="settings-value">${App.state.user?.role || 'admin'}</span>
          </div>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `
        <div class="settings-section">
          <h3>❌ خطأ</h3>
          <p>${e.message}</p>
        </div>
      `;
    }
  },

  async saveWhatsApp() {
    const btn = document.getElementById('btn-save-wa');
    btn.disabled = true;
    btn.textContent = '⏳ جاري الحفظ...';

    const updates = {
      enabled: document.getElementById('wa-enabled').checked,
      phone: document.getElementById('wa-phone').value.trim(),
      display_phone: document.getElementById('wa-display-phone').value.trim(),
      mode: document.getElementById('wa-mode').value,
    };

    // Validation
    if (updates.phone && !updates.phone.startsWith('+') && !/^\d+$/.test(updates.phone)) {
      App.toast('❌ الرقم لازم يبدأ بـ + أو أرقام فقط', 'error');
      btn.disabled = false;
      btn.textContent = '💾 حفظ';
      return;
    }

    try {
      const result = await App.api('/v1/admin/settings/whatsapp', {
        method: 'PUT',
        body: JSON.stringify(updates),
      });

      if (result.success) {
        App.toast('✅ تم حفظ الإعدادات بنجاح', 'success');
        this.originalWhatsApp = JSON.parse(JSON.stringify(result.whatsapp));
      } else {
        App.toast('❌ فشل الحفظ', 'error');
      }
    } catch (e) {
      App.toast(`❌ خطأ: ${e.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '💾 حفظ';
    }
  },

  resetWhatsApp() {
    if (!this.originalWhatsApp) return;
    document.getElementById('wa-enabled').checked = this.originalWhatsApp.enabled;
    document.getElementById('wa-phone').value = this.originalWhatsApp.phone || '';
    document.getElementById('wa-display-phone').value = this.originalWhatsApp.display_phone || '';
    document.getElementById('wa-mode').value = this.originalWhatsApp.mode || 'link';
    App.toast('↺ تم إعادة التعيين', 'success');
  },
};
