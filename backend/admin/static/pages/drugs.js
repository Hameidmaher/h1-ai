Pages.drugs = {
  async render(el) {
    el.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-actions">
          <button class="btn btn-primary" onclick="Pages.drugs.openCreate()">
            ➕ إضافة دواء
          </button>
        </div>
      </div>
      <div id="drugs-list"></div>
    `;
    await this.load();
  },

  async load() {
    try {
      const drugs = await App.api('/v1/admin/drugs');
      const entries = Object.entries(drugs);
      if (!entries.length) {
        document.getElementById('drugs-list').innerHTML =
          '<div class="empty-state"><span class="icon">💊</span>لا توجد أدوية</div>';
        return;
      }
      const rows = entries.map(([id, d]) => `
        <tr>
          <td><code>${App.escapeHtml(id)}</code></td>
          <td>${App.escapeHtml(d.name_ar || '')}</td>
          <td>${App.escapeHtml(d.name_en || '')}</td>
          <td><span class="badge badge-info">${App.escapeHtml(d.class || '')}</span></td>
          <td>${d.safe_pregnancy ? '✅' : '❌'}</td>
          <td>${d.safe_children ? '✅' : '❌'}</td>
          <td class="actions">
            <button class="btn btn-danger btn-sm"
                    onclick="Pages.drugs.delete('${id}')">🗑️</button>
          </td>
        </tr>
      `).join('');
      document.getElementById('drugs-list').innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>المعرف</th><th>عربي</th><th>إنجليزي</th>
              <th>الفئة</th><th>حمل</th><th>أطفال</th><th>إجراءات</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    } catch (e) {
      document.getElementById('drugs-list').innerHTML =
        `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },

  openCreate() {
    const body = `
      <div class="form-group">
        <label>المعرف (بالإنجليزي) *</label>
        <input type="text" id="d-id" placeholder="مثال: paracetamol">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>الاسم بالعربي *</label>
          <input type="text" id="d-name-ar">
        </div>
        <div class="form-group">
          <label>الاسم بالإنجليزي *</label>
          <input type="text" id="d-name-en">
        </div>
      </div>
      <div class="form-group">
        <label>الفئة</label>
        <input type="text" id="d-class" placeholder="analgesic, nsaid, ...">
      </div>
      <div class="form-group">
        <label>الاستخدامات (مفصولة بفواصل)</label>
        <input type="text" id="d-indications" placeholder="headache, fever">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>
            <input type="checkbox" id="d-safe-pregnancy" checked>
            آمن للحمل
          </label>
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" id="d-safe-children" checked>
            آمن للأطفال
          </label>
        </div>
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.drugs.save()">حفظ</button>
    `;
    App.openModal('إضافة دواء', body, footer);
  },

  async save() {
    const id = document.getElementById('d-id').value.trim();
    const data = {
      id,
      name_ar: document.getElementById('d-name-ar').value.trim(),
      name_en: document.getElementById('d-name-en').value.trim(),
      class: document.getElementById('d-class').value.trim(),
      indications: document.getElementById('d-indications').value
        .split(',').map(s => s.trim()).filter(Boolean),
      safe_pregnancy: document.getElementById('d-safe-pregnancy').checked,
      safe_children: document.getElementById('d-safe-children').checked,
    };
    if (!id || !data.name_ar || !data.name_en) {
      App.toast('يرجى ملء الحقول المطلوبة', 'error');
      return;
    }
    try {
      await App.api('/v1/admin/drugs', {
        method: 'POST', body: JSON.stringify(data),
      });
      App.toast('تم إضافة الدواء', 'success');
      App.closeModal();
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async delete(id) {
    if (!confirm(`حذف الدواء ${id}؟`)) return;
    try {
      await App.api(`/v1/admin/drugs/${id}`, { method: 'DELETE' });
      App.toast('تم الحذف', 'success');
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },
};
