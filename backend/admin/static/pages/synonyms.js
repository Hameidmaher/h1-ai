Pages.synonyms = {
  async render(el) {
    el.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-actions">
          <button class="btn btn-primary" onclick="Pages.synonyms.openCreate()">
            ➕ إضافة مرادف
          </button>
        </div>
      </div>
      <div id="synonyms-list"></div>
    `;
    await this.load();
  },

  async load() {
    try {
      const data = await App.api('/v1/admin/synonyms');
      const syns = data.synonyms || {};
      const entries = Object.entries(syns);
      if (!entries.length) {
        document.getElementById('synonyms-list').innerHTML =
          '<div class="empty-state"><span class="icon">📚</span>لا توجد مرادفات</div>';
        return;
      }
      const rows = entries.map(([term, aliases]) => `
        <tr>
          <td><strong>${App.escapeHtml(term)}</strong></td>
          <td>${aliases.map(a => `<span class="badge badge-info">${App.escapeHtml(a)}</span>`).join(' ')}</td>
          <td class="actions">
            <button class="btn btn-danger btn-sm"
                    onclick="Pages.synonyms.delete('${App.escapeHtml(term)}')">🗑️</button>
          </td>
        </tr>
      `).join('');
      document.getElementById('synonyms-list').innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>المصطلح</th><th>المرادفات</th><th>إجراءات</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    } catch (e) {
      document.getElementById('synonyms-list').innerHTML =
        `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },

  openCreate() {
    const body = `
      <div class="form-group">
        <label>المصطلح الأساسي *</label>
        <input type="text" id="s-term" placeholder="مثال: صداع">
      </div>
      <div class="form-group">
        <label>المرادفات (مفصولة بفواصل) *</label>
        <input type="text" id="s-syns" placeholder="headache, وجع راس">
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.synonyms.save()">حفظ</button>
    `;
    App.openModal('إضافة مرادف', body, footer);
  },

  async save() {
    const term = document.getElementById('s-term').value.trim();
    const synonyms = document.getElementById('s-syns').value
      .split(',').map(s => s.trim()).filter(Boolean);
    if (!term || !synonyms.length) {
      App.toast('يرجى ملء الحقول', 'error');
      return;
    }
    try {
      await App.api('/v1/admin/synonyms', {
        method: 'POST',
        body: JSON.stringify({ term, synonyms }),
      });
      App.toast('تم إضافة المرادف', 'success');
      App.closeModal();
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async delete(term) {
    if (!confirm(`حذف "${term}"؟`)) return;
    try {
      await App.api(`/v1/admin/synonyms/${encodeURIComponent(term)}`, {
        method: 'DELETE',
      });
      App.toast('تم الحذف', 'success');
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },
};
