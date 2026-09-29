/**
 * Products Admin Page
 */
Pages.products = {
  state: { page: 1, pageSize: 20, total: 0, items: [] },

  async render(el) {
    el.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-actions">
          <button class="btn btn-primary" onclick="Pages.products.openCreate()">
            ➕ إضافة منتج
          </button>
          <button class="btn btn-ghost" onclick="Pages.products.exportCsv()">
            📤 تصدير CSV
          </button>
        </div>
        <input type="text" class="search-input" placeholder="🔍 بحث..."
               oninput="Pages.products.filter(this.value)" id="products-search">
      </div>
      <div id="products-table"></div>
      <div id="products-pagination" class="pagination"></div>
    `;
    await this.load();
  },

  async load() {
    try {
      const data = await App.api(
        `/v1/admin/products?page=${this.state.page}&page_size=${this.state.pageSize}`
      );
      this.state.items = data.items;
      this.state.total = data.total;
      this.renderTable(data.items);
      this.renderPagination(data.total_pages);
    } catch (e) {
      document.getElementById('products-table').innerHTML =
        `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },

  renderTable(items) {
    if (!items.length) {
      document.getElementById('products-table').innerHTML =
        '<div class="empty-state"><span class="icon">📦</span>لا توجد منتجات</div>';
      return;
    }

    const rows = items.map(p => `
      <tr>
        <td><code>${App.escapeHtml(p.ItemCode)}</code></td>
        <td>${App.escapeHtml(p.ItemName)}</td>
        <td><span class="badge badge-info">${App.escapeHtml(p.Category)}</span></td>
        <td>${parseFloat(p.Price).toFixed(2)} ج</td>
        <td>${p.StockQty}</td>
        <td>${App.escapeHtml(p.ExpiryDate)}</td>
        <td class="actions">
          <button class="btn btn-warning btn-sm"
                  onclick="Pages.products.openEdit('${p.ItemCode}')">✏️</button>
          <button class="btn btn-danger btn-sm"
                  onclick="Pages.products.delete('${p.ItemCode}')">🗑️</button>
        </td>
      </tr>
    `).join('');

    document.getElementById('products-table').innerHTML = `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>الكود</th><th>الاسم</th><th>الفئة</th>
              <th>السعر</th><th>الكمية</th><th>الصلاحية</th><th>إجراءات</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  },

  renderPagination(totalPages) {
    const el = document.getElementById('products-pagination');
    let html = '';
    html += `<button ${this.state.page <= 1 ? 'disabled' : ''}
             onclick="Pages.products.goTo(${this.state.page - 1})">السابق</button>`;
    for (let i = 1; i <= Math.min(totalPages, 7); i++) {
      html += `<button class="${i === this.state.page ? 'active' : ''}"
               onclick="Pages.products.goTo(${i})">${i}</button>`;
    }
    html += `<button ${this.state.page >= totalPages ? 'disabled' : ''}
             onclick="Pages.products.goTo(${this.state.page + 1})">التالي</button>`;
    el.innerHTML = html;
  },

  goTo(page) {
    this.state.page = page;
    this.load();
  },

  filter(query) {
    if (!query) { this.renderTable(this.state.items); return; }
    const q = query.toLowerCase();
    const filtered = this.state.items.filter(p =>
      (p.ItemName || '').toLowerCase().includes(q) ||
      (p.Category || '').toLowerCase().includes(q) ||
      (p.ItemCode || '').includes(q)
    );
    this.renderTable(filtered);
  },

  openCreate() {
    const body = `
      <div class="form-group">
        <label>اسم المنتج *</label>
        <input type="text" id="p-name" placeholder="مثال: Paracetamol 500mg">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>الفئة *</label>
          <select id="p-category">
            <option>Analgesic</option>
            <option>Antibiotic</option>
            <option>Vitamin</option>
            <option>Gastrointestinal</option>
            <option>Cardiovascular</option>
            <option>Diabetes</option>
            <option>Respiratory</option>
            <option>Antihistamine</option>
            <option>OTC</option>
            <option>Topical</option>
            <option>Cosmetic</option>
            <option>Eye/Ear</option>
            <option>Device</option>
            <option>First Aid</option>
          </select>
        </div>
        <div class="form-group">
          <label>السعر (جنيه) *</label>
          <input type="number" id="p-price" step="0.01" min="0" value="0">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>الكمية *</label>
          <input type="number" id="p-stock" min="0" value="0">
        </div>
        <div class="form-group">
          <label>تاريخ الانتهاء *</label>
          <input type="date" id="p-expiry">
        </div>
      </div>
      <div class="form-group">
        <label>الوصف</label>
        <textarea id="p-desc" rows="2"></textarea>
      </div>
    `;
    const footer = `
      <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pages.products.saveCreate()">حفظ</button>
    `;
    App.openModal('إضافة منتج جديد', body, footer);
  },

  async saveCreate() {
    const data = {
      name: document.getElementById('p-name').value.trim(),
      category: document.getElementById('p-category').value,
      price: parseFloat(document.getElementById('p-price').value),
      stock_qty: parseInt(document.getElementById('p-stock').value),
      expiry_date: document.getElementById('p-expiry').value,
      description: document.getElementById('p-desc').value.trim(),
    };

    if (!data.name || !data.expiry_date) {
      App.toast('يرجى ملء كل الحقول المطلوبة', 'error');
      return;
    }

    try {
      await App.api('/v1/admin/products', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      App.toast('تم إضافة المنتج بنجاح', 'success');
      App.closeModal();
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async openEdit(code) {
    try {
      const p = await App.api(`/v1/admin/products/${code}`);
      const body = `
        <div class="form-group">
          <label>اسم المنتج *</label>
          <input type="text" id="p-name" value="${App.escapeHtml(p.ItemName)}">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>السعر (جنيه) *</label>
            <input type="number" id="p-price" step="0.01" value="${p.Price}">
          </div>
          <div class="form-group">
            <label>الكمية *</label>
            <input type="number" id="p-stock" value="${p.StockQty}">
          </div>
        </div>
        <div class="form-group">
          <label>تاريخ الانتهاء</label>
          <input type="date" id="p-expiry" value="${p.ExpiryDate}">
        </div>
        <div class="form-group">
          <label>الوصف</label>
          <textarea id="p-desc" rows="2">${App.escapeHtml(p.Description || '')}</textarea>
        </div>
      `;
      const footer = `
        <button class="btn btn-ghost" onclick="App.closeModal()">إلغاء</button>
        <button class="btn btn-primary"
                onclick="Pages.products.saveEdit('${code}')">حفظ</button>
      `;
      App.openModal('تعديل منتج', body, footer);
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async saveEdit(code) {
    const data = {
      name: document.getElementById('p-name').value.trim(),
      price: parseFloat(document.getElementById('p-price').value),
      stock_qty: parseInt(document.getElementById('p-stock').value),
      expiry_date: document.getElementById('p-expiry').value,
      description: document.getElementById('p-desc').value.trim(),
    };
    try {
      await App.api(`/v1/admin/products/${code}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      App.toast('تم تحديث المنتج', 'success');
      App.closeModal();
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async delete(code) {
    if (!confirm(`حذف المنتج ${code}؟`)) return;
    try {
      await App.api(`/v1/admin/products/${code}`, { method: 'DELETE' });
      App.toast('تم الحذف', 'success');
      this.load();
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },

  async exportCsv() {
    try {
      const res = await fetch('/v1/admin/export/products.csv', {
        headers: { 'Authorization': `Bearer ${App.state.token}` },
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'products.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      App.toast(`خطأ: ${e.message}`, 'error');
    }
  },
};
