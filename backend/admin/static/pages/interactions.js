Pages.interactions = {
  async render(el) {
    el.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-actions">
          <button class="btn btn-primary" onclick="Pages.interactions.openCreate()">
            ➕ إضافة تداخل
          </button>
        </div>
      </div>
      <div id="interactions-list"></div>
    `;
    await this.load();
  },

  async load() {
    try {
      const items = await App.api('/v1/admin/interactions');
      if (!items.length) {
        document.getElementById('interactions-list').innerHTML =
          '<div class="empty-state"><span class="icon">⚠️</span>لا توجد تداخلات</div>';
        return;
      }
      const rows = items.map((it, i) => {
        const sevClass = {
          major: 'badge-danger', moderate: 'badge-warning', minor: 'badge-info',
        }[it.severity] || 'badge-info';
        return `
          <tr>
            <td>${App.escapeHtml(it.drug1)}</td>
            <td>↔️</td>
            <td>${App.escapeHtml(it.drug2)}</td>
            <td><span class="badge ${sevClass}">${it.severity}</span></td>
            <td>${App.escapeHtml(it.effect)}</td>
            <td class="actions">
              <button class="btn btn-danger btn-sm"
                      onclick="Pages.interactions.delete(${i})">🗑️</button>
            </td>
          </tr>
        `;
      }).join('');
      document.getElementById('interactions-list').innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>دواء 1</th><th></th><th>دواء 2</th>
              <th>الخطورة</th><th>التأثير</th><th>إجراءات</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    } catch (e) {
      document.getElementById('interactions-list').innerHTML =
        `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },

  openCreate() {
    const body = `
      <div class="form-row">
        <div class="form-group">
          <label>دواء 1 *</label>
          <input type="text" id="i-d1" placeholder="warfarin">
        </div>
        <div class="form-group">
          <label>دواء 2 *</label>
          <input type="text" id="i-d2" placeholder="aspirin">
        </div>
      </div>
      <div class="form-group">
        <label>الخطورة *</label>
        <select id="i-sev">
          <option value="minor">بسيط</option>
          <option value="moderate" selected>متوسط</option>
          <option value="major">خطير</option>
        </select>
      </div>
      <div class="form-group">
        <label>التأثير *</label>
        <input type="text" id="i-effect" placeholder="زيادة خطر النزيف">
      </div>
      <div class="form-group">
        <label>الإجراء الموصى به *</label>
        <input type="text" id="i-action" placeholder="لا تتناولهما معاً">
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.interactions.save()">حفظ</button>
    `;
    App.openModal('إضافة تداخل دوائي', body, footer);
  },

  async save() {
    const data = {
      drug1: document.getElementById('i-d1').value.trim(),
      drug2: document.getElementById('i-d2').value.trim(),
      severity: document.getElementById('i-sev').value,
      effect: document.getElementById('i-effect').value.trim(),
      action: document.getElementById('i-action').value.trim(),
    };
    if (!data.drug1 || !data.drug2 || !data.effect || !data.action) {
      App.toast('يرجى ملء كل الحقول', 'error');
      return;
    }
    try {
      await App.api('/v1/admin/interactions', {
        method: 'POST', body: JSON.stringify(data),
      });
      App.toast('تم إضافة التداخل', 'success');
      App.closeModal();
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async delete(index) {
    if (!confirm('حذف هذا التداخل؟')) return;
    try {
      await App.api(`/v1/admin/interactions/${index}`, { method: 'DELETE' });
      App.toast('تم الحذف', 'success');
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },
};
