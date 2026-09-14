Pages.settings = {
  async render(el) {
    try {
      const info = await App.api('/v1/whatsapp/info');
      el.innerHTML = `
        <div class="card">
          <div class="card-header"><h2>📱 WhatsApp</h2></div>
          <div class="form-group">
            <label>مُفعّل</label>
            <input type="text" value="${info.enabled ? 'نعم' : 'لا'}" disabled>
          </div>
          <div class="form-group">
            <label>الرقم</label>
            <input type="text" value="${App.escapeHtml(info.phone)}" disabled>
          </div>
          <div class="form-group">
            <label>الوضع</label>
            <input type="text" value="${App.escapeHtml(info.mode)}" disabled>
          </div>
          <p style="color:var(--text-muted);font-size:13px;margin-top:12px">
            💡 لتعديل هذه الإعدادات، حرّر <code>config.production.yaml</code>
            ثم أعد تشغيل Backend.
          </p>
        </div>

        <div class="card">
          <div class="card-header"><h2>📤 استيراد/تصدير</h2></div>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <button class="btn btn-ghost"
                    onclick="Pages.settings.exportFull()">
              📥 تنزيل Backup كامل (JSON)
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><h2>ℹ️ معلومات النظام</h2></div>
          <div class="form-group">
            <label>الإصدار</label>
            <input type="text" value="H1-AI v4.0.0" disabled>
          </div>
          <div class="form-group">
            <label>المستخدم الحالي</label>
            <input type="text" value="${App.escapeHtml(App.state.user?.username || '')}" disabled>
          </div>
        </div>
      `;
    } catch (e) {
      el.innerHTML = `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },

  async exportFull() {
    try {
      const data = await App.api('/v1/admin/export/full');
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `h1ai_backup_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      App.toast('تم تنزيل الـ Backup', 'success');
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },
};
