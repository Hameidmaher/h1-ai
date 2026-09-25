/**
 * Pharmacy Admin — Per-tenant management
 */
(function() {
  'use strict';

  const API_BASE = '/v1/pharmacy';

  const state = {
    token: null,
    user: null,
    pharmacy: null,
    currentPage: 'dashboard',
    products: [],
    team: [],
  };

  // ═══ Helpers ═══
  function api(path, options = {}) {
    return fetch(API_BASE + path, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (state.token || ''),
        ...(options.headers || {}),
      },
    }).then(async (r) => {
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
      return data;
    });
  }

  function toast(msg, type = 'info') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'toast show ' + type;
    setTimeout(() => { el.className = 'toast'; }, 3000);
  }

  function esc(s) {
    const div = document.createElement('div');
    div.textContent = s || '';
    return div.innerHTML;
  }

  function fmtDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('ar-EG');
  }

  function openModal(title, bodyHtml, footerHtml) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHtml;
    document.getElementById('modal-foot').innerHTML = footerHtml;
    document.getElementById('modal').classList.remove('hidden');
  }

  function closeModal() {
    document.getElementById('modal').classList.add('hidden');
  }

  // ═══ Navigate ═══
  function navigate(page) {
    state.currentPage = page;
    document.querySelectorAll('.ph-nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.page === page);
    });

    const titles = {
      dashboard: 'لوحة التحكم',
      products: 'المنتجات',
      drugs: 'الأدوية',
      whatsapp: 'WhatsApp',
      orders: 'الطلبات',
      team: 'الفريق',
      settings: 'الإعدادات',
    };
    document.getElementById('page-title').textContent = titles[page] || page;

    const content = document.getElementById('page-content');
    content.innerHTML = '<div class="loading">⏳ جاري التحميل...</div>';

    switch (page) {
      case 'dashboard': renderDashboard(content); break;
      case 'products': renderProducts(content); break;
      case 'drugs': renderDrugs(content); break;
      case 'whatsapp': renderWhatsApp(content); break;
      case 'orders': renderOrders(content); break;
      case 'team': renderTeam(content); break;
      case 'settings': renderSettings(content); break;
    }
  }

  // ═══ Dashboard ═══
  async function renderDashboard(content) {
    try {
      const stats = await api('/stats');
      content.innerHTML = `
        <div class="stats-grid">
          <div class="stat-card blue">
            <span class="stat-icon">👥</span>
            <div class="stat-label">المستخدمين</div>
            <div class="stat-value">${stats.users}</div>
          </div>
          <div class="stat-card green">
            <span class="stat-icon">💊</span>
            <div class="stat-label">الصيادلة</div>
            <div class="stat-value">${stats.pharmacists}</div>
          </div>
          <div class="stat-card orange">
            <span class="stat-icon">💬</span>
            <div class="stat-label">إجمالي الرسائل</div>
            <div class="stat-value">${(stats.total_messages || 0).toLocaleString('ar-EG')}</div>
          </div>
          <div class="stat-card purple">
            <span class="stat-icon">📅</span>
            <div class="stat-label">رسائل اليوم</div>
            <div class="stat-value">${stats.messages_today}</div>
          </div>
          <div class="stat-card pink">
            <span class="stat-icon">📬</span>
            <div class="stat-label">المحادثات</div>
            <div class="stat-value">${stats.conversations}</div>
          </div>
          <div class="stat-card orange">
            <span class="stat-icon">🔴</span>
            <div class="stat-label">غير مقروءة</div>
            <div class="stat-value">${stats.unread_conversations}</div>
          </div>
          <div class="stat-card blue">
            <span class="stat-icon">📦</span>
            <div class="stat-label">المنتجات</div>
            <div class="stat-value">${stats.products}</div>
          </div>
          <div class="stat-card green">
            <span class="stat-icon">📊</span>
            <div class="stat-label">المخزون</div>
            <div class="stat-value">${stats.inventory_items}</div>
          </div>
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  // ═══ Products ═══
  async function renderProducts(content) {
    try {
      const data = await api('/products?limit=200');
      state.products = data.products;

      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>📦 المنتجات (${data.products.length})</h2>
            <div class="table-actions">
              <button class="btn btn-primary" onclick="Pharmacy.openProductModal()">➕ إضافة منتج</button>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>الاسم</th>
                <th>الفئة</th>
                <th>السعر</th>
                <th>الكمية</th>
                <th>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              ${data.products.map(p => `
                <tr>
                  <td><strong>${esc(p.name)}</strong></td>
                  <td>${esc(p.category || '—')}</td>
                  <td>${p.price} EGP</td>
                  <td>${p.stock_qty}</td>
                  <td>
                    <button class="btn btn-ghost btn-sm" onclick="Pharmacy.editProduct('${p.id}')">✏️</button>
                    <button class="btn btn-danger btn-sm" onclick="Pharmacy.deleteProduct('${p.id}')">🗑️</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  function openProductModal(productId = null) {
    const p = productId ? state.products.find(x => x.id === productId) : null;
    const title = p ? '✏️ تعديل منتج' : '➕ إضافة منتج';

    const body = `
      <div class="form-group">
        <label>الاسم</label>
        <input id="p-name" value="${esc(p?.name || '')}" required>
      </div>
      <div class="form-group">
        <label>الفئة</label>
        <input id="p-category" value="${esc(p?.category || '')}">
      </div>
      <div class="form-group">
        <label>السعر</label>
        <input id="p-price" type="number" step="0.01" value="${p?.price || 0}">
      </div>
      <div class="form-group">
        <label>الكمية</label>
        <input id="p-stock" type="number" value="${p?.stock_qty || 0}">
      </div>
      <div class="form-group">
        <label>الوصف</label>
        <textarea id="p-desc" rows="2">${esc(p?.description || '')}</textarea>
      </div>
    `;

    const footer = `
      <button class="btn btn-ghost" onclick="Pharmacy.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pharmacy.saveProduct('${productId || ''}')">حفظ</button>
    `;

    openModal(title, body, footer);
  }

  async function saveProduct(productId) {
    const data = {
      name: document.getElementById('p-name').value.trim(),
      category: document.getElementById('p-category').value.trim() || null,
      price: parseFloat(document.getElementById('p-price').value) || 0,
      stock_qty: parseInt(document.getElementById('p-stock').value) || 0,
      description: document.getElementById('p-desc').value.trim() || null,
    };

    if (!data.name) { toast('الاسم مطلوب', 'error'); return; }

    try {
      if (productId) {
        await api('/products/' + productId, { method: 'PUT', body: JSON.stringify(data) });
        toast('✅ تم التحديث', 'success');
      } else {
        await api('/products', { method: 'POST', body: JSON.stringify(data) });
        toast('✅ تمت الإضافة', 'success');
      }
      closeModal();
      navigate('products');
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  async function deleteProduct(id) {
    if (!confirm('حذف المنتج؟')) return;
    try {
      await api('/products/' + id, { method: 'DELETE' });
      toast('✅ تم الحذف', 'success');
      navigate('products');
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  // ═══ Drugs ═══
  async function renderDrugs(content) {
    try {
      const data = await api('/drugs?limit=200');
      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>💊 الأدوية (${data.drugs.length})</h2>
            <div class="table-actions">
              <input type="text" id="drug-search" placeholder="🔍 بحث..."
                     style="padding:0.4rem 0.8rem;border-radius:8px;border:1px solid #d1d5db"
                     onkeypress="if(event.key==='Enter') Pharmacy.searchDrugs()">
              <button class="btn btn-primary" onclick="Pharmacy.searchDrugs()">بحث</button>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>الاسم</th>
                <th>الاسم الإنجليزي</th>
                <th>الاسم العلمي</th>
                <th>الفئة</th>
                <th>الشكل</th>
                <th>التركيز</th>
                <th>السعر</th>
              </tr>
            </thead>
            <tbody>
              ${data.drugs.map(d => `
                <tr>
                  <td><strong>${esc(d.trade_name)}</strong></td>
                  <td>${esc(d.trade_name_en || '—')}</td>
                  <td>${esc(d.scientific_name || '—')}</td>
                  <td>${esc(d.category || '—')}</td>
                  <td>${esc(d.form || '—')}</td>
                  <td>${esc(d.strength || '—')}</td>
                  <td>${d.price_egp || '—'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  async function searchDrugs() {
    const q = document.getElementById('drug-search')?.value.trim() || '';
    const content = document.getElementById('page-content');
    content.innerHTML = '<div class="loading">⏳ جاري البحث...</div>';
    try {
      const data = await api('/drugs?search=' + encodeURIComponent(q) + '&limit=200');
      const drugs = data.drugs;
      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>💊 نتائج البحث (${drugs.length})</h2>
          </div>
          <table>
            <thead>
              <tr>
                <th>الاسم</th>
                <th>الاسم الإنجليزي</th>
                <th>الاسم العلمي</th>
                <th>الفئة</th>
                <th>السعر</th>
              </tr>
            </thead>
            <tbody>
              ${drugs.map(d => `
                <tr>
                  <td><strong>${esc(d.trade_name)}</strong></td>
                  <td>${esc(d.trade_name_en || '—')}</td>
                  <td>${esc(d.scientific_name || '—')}</td>
                  <td>${esc(d.category || '—')}</td>
                  <td>${d.price_egp || '—'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  // ═══ WhatsApp ═══
  async function renderWhatsApp(content) {
    try {
      const [numbers, health] = await Promise.all([
        api('/whatsapp'),
        api('/whatsapp/health').catch(() => ({})),
      ]);

      content.innerHTML = `
        <div class="stats-grid" style="grid-template-columns:repeat(3,1fr)">
          <div class="stat-card ${health.status === 'ok' ? 'green' : 'orange'}">
            <span class="stat-icon">📱</span>
            <div class="stat-label">حالة الخدمة</div>
            <div class="stat-value">${health.status || 'غير معروف'}</div>
          </div>
          <div class="stat-card blue">
            <span class="stat-icon">🔢</span>
            <div class="stat-label">عدد الأرقام</div>
            <div class="stat-value">${numbers.count}</div>
          </div>
          <div class="stat-card purple">
            <span class="stat-icon">✅</span>
            <div class="stat-label">المتصلة</div>
            <div class="stat-value">${numbers.numbers.filter(n => n.status === 'connected').length}</div>
          </div>
        </div>

        <div class="table-container">
          <div class="table-header">
            <h2>📱 أرقام WhatsApp</h2>
          </div>
          ${numbers.numbers.length === 0 ? `
            <div class="loading">لا يوجد أرقام مسجلة</div>
          ` : `
            <table>
              <thead>
                <tr>
                  <th>الرقم</th>
                  <th>الحالة</th>
                  <th>أساسي</th>
                  <th>متصل منذ</th>
                </tr>
              </thead>
              <tbody>
                ${numbers.numbers.map(n => `
                  <tr>
                    <td><strong>${esc(n.phone_number)}</strong></td>
                    <td>${n.status === 'connected' ? '✅ متصل' : '❌ ' + esc(n.status)}</td>
                    <td>${n.is_primary ? '⭐ نعم' : 'لا'}</td>
                    <td>${fmtDate(n.connected_at)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `}
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  // ═══ Orders ═══
  async function renderOrders(content) {
    try {
      const data = await api('/orders');
      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>🛒 الطلبات (${data.count})</h2>
          </div>
          ${data.count === 0 ? `
            <div class="loading">لا يوجد طلبات</div>
          ` : `
            <table>
              <thead>
                <tr>
                  <th>العميل</th>
                  <th>الهاتف</th>
                  <th>الحالة</th>
                  <th>الإجمالي</th>
                  <th>التاريخ</th>
                </tr>
              </thead>
              <tbody>
                ${data.orders.map(o => `
                  <tr>
                    <td>${esc(o.customer_name || '—')}</td>
                    <td>${esc(o.customer_phone || '—')}</td>
                    <td><span class="badge">${esc(o.status)}</span></td>
                    <td>${o.total_amount || 0} EGP</td>
                    <td>${fmtDate(o.created_at)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `}
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading">لا يوجد طلبات (${esc(e.message)})</div>`;
    }
  }

  // ═══ Team ═══
  async function renderTeam(content) {
    try {
      const data = await api('/team');
      state.team = data.members;

      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>👥 الفريق (${data.members.length})</h2>
            <div class="table-actions">
              <button class="btn btn-primary" onclick="Pharmacy.openTeamModal()">➕ إضافة عضو</button>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>اسم المستخدم</th>
                <th>الاسم الكامل</th>
                <th>الدور</th>
                <th>البريد</th>
                <th>الحالة</th>
                <th>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              ${data.members.map(m => `
                <tr>
                  <td><strong>${esc(m.username)}</strong></td>
                  <td>${esc(m.full_name || '—')}</td>
                  <td><span class="badge">${esc(m.role)}</span></td>
                  <td>${esc(m.email || '—')}</td>
                  <td>${m.is_active ? '✅' : '❌'}</td>
                  <td>
                    <button class="btn btn-danger btn-sm" onclick="Pharmacy.removeTeam('${m.id}')">🗑️</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  function openTeamModal() {
    const body = `
      <div class="form-group">
        <label>اسم المستخدم</label>
        <input id="t-username" required>
      </div>
      <div class="form-group">
        <label>كلمة المرور</label>
        <input id="t-password" type="password" required>
      </div>
      <div class="form-group">
        <label>الاسم الكامل</label>
        <input id="t-fullname">
      </div>
      <div class="form-group">
        <label>الدور</label>
        <select id="t-role">
          <option value="pharmacist">Pharmacist</option>
          <option value="customer">Customer</option>
        </select>
      </div>
      <div class="form-group">
        <label>البريد الإلكتروني</label>
        <input id="t-email" type="email">
      </div>
      <div class="form-group">
        <label>الهاتف</label>
        <input id="t-phone">
      </div>
    `;

    const footer = `
      <button class="btn btn-ghost" onclick="Pharmacy.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Pharmacy.saveTeam()">حفظ</button>
    `;

    openModal('➕ إضافة عضو للفريق', body, footer);
  }

  async function saveTeam() {
    const data = {
      username: document.getElementById('t-username').value.trim(),
      password: document.getElementById('t-password').value,
      full_name: document.getElementById('t-fullname').value.trim(),
      role: document.getElementById('t-role').value,
      email: document.getElementById('t-email').value.trim() || null,
      phone: document.getElementById('t-phone').value.trim() || null,
    };

    if (!data.username || !data.password) {
      toast('اسم المستخدم وكلمة المرور مطلوبان', 'error');
      return;
    }

    try {
      await api('/team', { method: 'POST', body: JSON.stringify(data) });
      toast('✅ تمت الإضافة', 'success');
      closeModal();
      navigate('team');
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  async function removeTeam(id) {
    if (!confirm('حذف العضو من الفريق؟')) return;
    try {
      await api('/team/' + id, { method: 'DELETE' });
      toast('✅ تم الحذف', 'success');
      navigate('team');
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  // ═══ Settings ═══
  async function renderSettings(content) {
    try {
      const ph = await api('/me');
      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>⚙️ إعدادات الصيدلية</h2>
          </div>
          <div style="padding:1.5rem">
            <div class="form-group">
              <label>الاسم (English)</label>
              <input id="s-name" value="${esc(ph.name || '')}">
            </div>
            <div class="form-group">
              <label>الاسم (عربي)</label>
              <input id="s-name-ar" value="${esc(ph.name_ar || '')}">
            </div>
            <div class="form-group">
              <label>الهاتف</label>
              <input id="s-phone" value="${esc(ph.phone || '')}">
            </div>
            <div class="form-group">
              <label>البريد الإلكتروني</label>
              <input id="s-email" type="email" value="${esc(ph.email || '')}">
            </div>
            <div class="form-group">
              <label>العنوان</label>
              <textarea id="s-address" rows="2">${esc(ph.address || '')}</textarea>
            </div>
            <div class="form-group">
              <label>المدينة</label>
              <input id="s-city" value="${esc(ph.city || '')}">
            </div>
            <div class="form-group">
              <label>شعار (URL)</label>
              <input id="s-logo" value="${esc(ph.logo_url || '')}">
            </div>
            <button class="btn btn-primary" onclick="Pharmacy.saveSettings()">💾 حفظ</button>
          </div>
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  async function saveSettings() {
    const data = {
      name: document.getElementById('s-name').value.trim() || null,
      name_ar: document.getElementById('s-name-ar').value.trim() || null,
      phone: document.getElementById('s-phone').value.trim() || null,
      email: document.getElementById('s-email').value.trim() || null,
      address: document.getElementById('s-address').value.trim() || null,
      city: document.getElementById('s-city').value.trim() || null,
      logo_url: document.getElementById('s-logo').value.trim() || null,
    };

    try {
      await api('/settings', { method: 'PUT', body: JSON.stringify(data) });
      toast('✅ تم الحفظ', 'success');
      loadPharmacyInfo();
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  // ═══ Auth ═══
  function getToken() {
    return localStorage.getItem('h1ai_admin_token') || '';
  }

  function logout() {
    localStorage.removeItem('h1ai_admin_token');
    localStorage.removeItem('h1ai_admin_user');
    window.location.href = '/admin';
  }

  async function loadPharmacyInfo() {
    try {
      const ph = await api('/me');
      state.pharmacy = ph;
      document.getElementById('pharmacy-name').textContent = ph.name_ar || ph.name;
    } catch (e) {
      console.error('loadPharmacyInfo:', e);
    }
  }

  async function init() {
    state.token = getToken();

    if (!state.token) {
      toast('يجب تسجيل الدخول أولاً', 'error');
      setTimeout(() => window.location.href = '/admin', 1500);
      return;
    }

    try {
      const me = await fetch('/v1/auth/me', {
        headers: { 'Authorization': 'Bearer ' + state.token },
      }).then(r => r.json());

      state.user = me;

      if (me.role === 'super_admin') {
        toast('Super Admin — استخدم /super', 'info');
        setTimeout(() => window.location.href = '/super', 1500);
        return;
      }

      if (!me.pharmacy_id) {
        toast('مستخدم بدون صيدلية', 'error');
        setTimeout(() => window.location.href = '/admin', 1500);
        return;
      }

      document.getElementById('ph-user-name').textContent = me.full_name || me.username;
      document.getElementById('ph-user-role').textContent = me.role;
    } catch (e) {
      toast('فشل التحقق: ' + e.message, 'error');
      logout();
      return;
    }

    await loadPharmacyInfo();

    document.querySelectorAll('.ph-nav-item').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        navigate(el.dataset.page);
      });
    });

    document.getElementById('ph-logout').addEventListener('click', logout);
    document.getElementById('modal-close').addEventListener('click', closeModal);

    navigate('dashboard');
  }

  window.Pharmacy = {
    navigate,
    openProductModal,
    saveProduct,
    editProduct: openProductModal,
    deleteProduct,
    searchDrugs,
    openTeamModal,
    saveTeam,
    removeTeam,
    saveSettings,
    closeModal,
  };

  document.addEventListener('DOMContentLoaded', init);
})();
