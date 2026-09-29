Pages.conditions = {
  async render(el) {
    el.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-actions">
          <button class="btn btn-primary" onclick="Pages.conditions.openCreate()">
            ➕ إضافة حالة
          </button>
        </div>
      </div>
      <div id="conditions-list"></div>
    `;
    await this.load();
  },

  async load() {
    try {
      const conds = await App.api('/v1/admin/conditions');
      const entries = Object.entries(conds);
      if (!entries.length) {
        document.getElementById('conditions-list').innerHTML =
          '<div class="empty-state"><span class="icon">🩺</span>لا توجد حالات</div>';
        return;
      }
      const rows = entries.map(([id, c]) => `
        <tr>
          <td><code>${App.escapeHtml(id)}</code></td>
          <td>${App.escapeHtml(c.display_name || '')}</td>
          <td>${(c.first_line || []).join(', ')}</td>
          <td>${(c.warnings || []).length} تحذير</td>
          <td class="actions">
            <button class="btn btn-danger btn-sm"
                    onclick="Pages.conditions.delete('${id}')">🗑️</button>
          </td>
        </tr>
      `).join('');
      document.getElementById('conditions-list').innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>المعرف</th><th>الاسم</th><th>الخط الأول</th>
              <th>تحذيرات</th><th>إجراءات</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    } catch (e) {
      document.getElementById('conditions-list').innerHTML =
        `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },

  openCreate() {
    const body = `
      <div class="form-group">
        <label>المعرف (بالإنجليزي) *</label>
        <input type="text" id="c-id" placeholder="مثال: headache">
      </div>
      <div class="form-group">
        <label>الاسم المعروض *</label>
        <input type="text" id="c-name" placeholder="مثال: صداع">
      </div>
      <div class="form-group">
        <label>الخط الأول (مفصول بفواصل)</label>
        <input type="text" id="c-first" placeholder="paracetamol, ibuprofen">
      </div>
      <div class="form-group">
        <label>البدائل (مفصولة بفواصل)</label>
        <input type="text" id="c-alts">
      </div>
      <div class="form-group">
        <label>الكلمات المفتاحية بالعربي (مفصولة بفواصل)</label>
        <input type="text" id="c-kw-ar" placeholder="صداع, ألم في الرأس">
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.conditions.save()">حفظ</button>
    `;
    App.openModal('إضافة حالة طبية', body, footer);
  },

  async save() {
    const id = document.getElementById('c-id').value.trim();
    const data = {
      id,
      display_name: document.getElementById('c-name').value.trim(),
      first_line: document.getElementById('c-first').value
        .split(',').map(s => s.trim()).filter(Boolean),
      alternatives: document.getElementById('c-alts').value
        .split(',').map(s => s.trim()).filter(Boolean),
      keywords: {
        ar: document.getElementById('c-kw-ar').value
          .split(',').map(s => s.trim()).filter(Boolean),
      },
      warnings: [],
      avoid: [],
    };
    if (!id || !data.display_name) {
      App.toast('يرجى ملء الحقول المطلوبة', 'error');
      return;
    }
    try {
      await App.api('/v1/admin/conditions', {
        method: 'POST', body: JSON.stringify(data),
      });
      App.toast('تم إضافة الحالة', 'success');
      App.closeModal();
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async delete(id) {
    if (!confirm(`حذف الحالة ${id}؟`)) return;
    try {
      await App.api(`/v1/admin/conditions/${id}`, { method: 'DELETE' });
      App.toast('تم الحذف', 'success');
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },
};
