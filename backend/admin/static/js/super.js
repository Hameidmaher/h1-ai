/**
 * Super Admin — Multi-tenant management
 */
(function() {
  'use strict';

  // ═══ State ═══
  const state = {
    token: null,
    user: null,
    currentPage: 'dashboard',
    pharmacies: [],
    users: [],
    subscriptions: [],
    flags: [],
  };

  // ═══ Helpers ═══
  function api(path, options = {}) {
    return fetch(path, {
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

  // ═══ Modal ═══
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

    document.querySelectorAll('.super-nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.page === page);
    });

    const titles = {
      dashboard: 'لوحة التحكم',
      pharmacies: 'إدارة الصيدليات',
      users: 'إدارة المستخدمين',
      subscriptions: 'الاشتراكات',
      flags: 'Feature Flags',
      logs: 'السجلات',
      settings: 'الإعدادات',
    };
    document.getElementById('page-title').textContent = titles[page] || page;

    const content = document.getElementById('page-content');
    content.innerHTML = '<div class="loading">⏳ جاري التحميل...</div>';

    switch (page) {
      case 'dashboard': renderDashboard(content); break;
      case 'pharmacies': renderPharmacies(content); break;
      case 'users': renderUsers(content); break;
      case 'subscriptions': renderSubscriptions(content); break;
      case 'flags': renderFlags(content); break;
      case 'logs': renderLogs(content); break;
      case 'settings': renderSettings(content); break;
      default: content.innerHTML = '<div class="loading">صفحة غير موجودة</div>';
    }
  }

  // ═══ Dashboard ═══
  async function renderDashboard(content) {
    try {
      const stats = await api('/v1/super/stats');

      content.innerHTML = `
        <div class="stats-grid">
          <div class="stat-card blue">
            <span class="stat-icon">🏥</span>
            <div class="stat-label">الصيدليات</div>
            <div class="stat-value">${stats.total_pharmacies}</div>
          </div>
          <div class="stat-card green">
            <span class="stat-icon">✅</span>
            <div class="stat-label">الصيدليات النشطة</div>
            <div class="stat-value">${stats.active_pharmacies}</div>
          </div>
          <div class="stat-card orange">
            <span class="stat-icon">👥</span>
            <div class="stat-label">إجمالي المستخدمين</div>
            <div class="stat-value">${stats.total_users}</div>
          </div>
          <div class="stat-card purple">
            <span class="stat-icon">💊</span>
            <div class="stat-label">الصيادلة</div>
            <div class="stat-value">${stats.pharmacists}</div>
          </div>
          <div class="stat-card blue">
            <span class="stat-icon">💬</span>
            <div class="stat-label">إجمالي الرسائل</div>
            <div class="stat-value">${stats.total_messages.toLocaleString('ar-EG')}</div>
          </div>
          <div class="stat-card green">
            <span class="stat-icon">📅</span>
            <div class="stat-label">رسائل اليوم</div>
            <div class="stat-value">${stats.messages_today}</div>
          </div>
          <div class="stat-card pink">
            <span class="stat-icon">📬</span>
            <div class="stat-label">المحادثات</div>
            <div class="stat-value">${stats.total_conversations}</div>
          </div>
          <div class="stat-card orange">
            <span class="stat-icon">🔴</span>
            <div class="stat-label">غير مقروءة</div>
            <div class="stat-value">${stats.unread_conversations}</div>
          </div>
        </div>
      `;

      // تحديث الـ badges
      document.getElementById('pharmacies-count').textContent = stats.total_pharmacies;
      document.getElementById('users-count').textContent = stats.total_users;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  // ═══ Pharmacies ═══
  async function renderPharmacies(content) {
    try {
      const data = await api('/v1/super/pharmacies');
      state.pharmacies = data.pharmacies;

      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>🏥 الصيدليات (${data.pharmacies.length})</h2>
            <div class="table-actions">
              <button class="btn btn-primary" onclick="Super.openPharmacyModal()">➕ إضافة صيدلية</button>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>الاسم</th>
                <th>الهاتف</th>
                <th>المدينة</th>
                <th>الخطة</th>
                <th>الحالة</th>
                <th>أُضيفت</th>
                <th>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              ${data.pharmacies.map(p => `
                <tr>
                  <td><strong>${esc(p.name_ar || p.name)}</strong></td>
                  <td>${esc(p.phone || '—')}</td>
                  <td>${esc(p.city || '—')}</td>
                  <td><span class="badge">${esc(p.subscription_plan)}</span></td>
                  <td>${p.is_active ? '✅ نشطة' : '❌ موقوفة'}</td>
                  <td>${fmtDate(p.created_at)}</td>
                  <td>
                    <button class="btn btn-ghost btn-sm" onclick="Super.editPharmacy('${p.id}')">✏️</button>
                    <button class="btn btn-danger btn-sm" onclick="Super.deletePharmacy('${p.id}')">🗑️</button>
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

  // ═══ Users ═══
  async function renderUsers(content) {
    try {
      const data = await api('/v1/super/users?limit=200');
      state.users = data.users;

      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>👥 المستخدمين (${data.users.length})</h2>
            <div class="table-actions">
              <button class="btn btn-primary" onclick="Super.openUserModal()">➕ إضافة مستخدم</button>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>اسم المستخدم</th>
                <th>الاسم الكامل</th>
                <th>الدور</th>
                <th>الصيدلية</th>
                <th>الحالة</th>
                <th>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              ${data.users.map(u => {
                let pharmacyName = '—';
                if (!u.pharmacy_id) {
                  pharmacyName = '<span class="badge" style="background:#fbbf24;color:#78350f">Super Admin</span>';
                } else {
                  const p = state.pharmacies.find(x => x.id === u.pharmacy_id);
                  pharmacyName = esc(p ? (p.name_ar || p.name) : u.pharmacy_id.slice(0,8));
                }
                const roleColors = {
                  super_admin: '#fbbf24',
                  admin: '#3b82f6',
                  pharmacist: '#10b981',
                  customer: '#6b7280',
                };
                return `
                  <tr>
                    <td><strong>${esc(u.username)}</strong></td>
                    <td>${esc(u.full_name || '—')}</td>
                    <td><span class="badge" style="background:${roleColors[u.role] || '#6b7280'}">${esc(u.role)}</span></td>
                    <td>${pharmacyName}</td>
                    <td>${u.is_active ? '✅' : '❌'}</td>
                    <td>
                      <button class="btn btn-ghost btn-sm" onclick="Super.editUser('${u.id}')">✏️</button>
                      <button class="btn btn-danger btn-sm" onclick="Super.deleteUser('${u.id}')">🗑️</button>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (e) {
      content.innerHTML = `<div class="loading" style="color:#ef4444">❌ ${esc(e.message)}</div>`;
    }
  }

  // ═══ Subscriptions ═══
  async function renderSubscriptions(content) {
    try {
      const data = await api('/v1/super/subscriptions');
      content.innerHTML = `
        <div class="table-container">
          <div class="table-header">
            <h2>💳 الاشتراكات (${data.subscriptions.length})</h2>
          </div>
          <table>
            <thead>
              <tr>
                <th>الصيدلية</th>
                <th>الخطة</th>
                <th>الحالة</th>
                <th>السعر</th>
                <th>ينتهي</th>
                <th>تجديد تلقائي</th>
              </tr>
            </thead>
            <tbody>
              ${data.subscriptions.map(s => `
                <tr>
                  <td>${esc(s.pharmacy_name || '—')}</td>
                  <td><span class="badge">${esc(s.plan)}</span></td>
                  <td>${s.status === 'active' ? '✅ نشط' : '❌ ' + esc(s.status)}</td>
                  <td>${s.price_monthly} ${esc(s.currency)}</td>
                  <td>${fmtDate(s.expires_at)}</td>
                  <td>${s.auto_renew ? '✅' : '❌'}</td>
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

  // ═══ Flags ═══
  async function renderFlags(content) {
    content.innerHTML = `
      <div class="table-container">
        <div class="table-header">
          <h2>🎛️ Feature Flags</h2>
        </div>
        <div class="loading">قريباً...</div>
      </div>
    `;
  }

  // ═══ Logs ═══
  async function renderLogs(content) {
    content.innerHTML = `
      <div class="table-container">
        <div class="table-header">
          <h2>📜 السجلات</h2>
        </div>
        <div class="loading">قريباً...</div>
      </div>
    `;
  }

  // ═══ Settings ═══
  async function renderSettings(content) {
    content.innerHTML = `
      <div class="table-container">
        <div class="table-header">
          <h2>⚙️ الإعدادات</h2>
        </div>
        <div class="loading">قريباً...</div>
      </div>
    `;
  }

  // ═══ Pharmacy Modal ═══
  function openPharmacyModal(pharmacyId = null) {
    const p = pharmacyId ? state.pharmacies.find(x => x.id === pharmacyId) : null;
    const title = p ? '✏️ تعديل صيدلية' : '➕ إضافة صيدلية';

    const body = `
      <div class="form-group">
        <label>الاسم (English)</label>
        <input id="ph-name" value="${esc(p?.name || '')}" required>
      </div>
      <div class="form-group">
        <label>الاسم (عربي)</label>
        <input id="ph-name-ar" value="${esc(p?.name_ar || '')}">
      </div>
      <div class="form-group">
        <label>الهاتف</label>
        <input id="ph-phone" value="${esc(p?.phone || '')}">
      </div>
      <div class="form-group">
        <label>البريد الإلكتروني</label>
        <input id="ph-email" type="email" value="${esc(p?.email || '')}">
      </div>
      <div class="form-group">
        <label>المدينة</label>
        <input id="ph-city" value="${esc(p?.city || '')}">
      </div>
      <div class="form-group">
        <label>الخطة</label>
        <select id="ph-plan">
          <option value="basic" ${p?.subscription_plan === 'basic' ? 'selected' : ''}>Basic</option>
          <option value="pro" ${p?.subscription_plan === 'pro' ? 'selected' : ''}>Pro</option>
          <option value="enterprise" ${p?.subscription_plan === 'enterprise' ? 'selected' : ''}>Enterprise</option>
        </select>
      </div>
      <div class="form-group">
        <label>
          <input type="checkbox" id="ph-active" ${p?.is_active !== false ? 'checked' : ''}>
          نشطة
        </label>
      </div>
    `;

    const footer = `
      <button class="btn btn-ghost" onclick="Super.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Super.savePharmacy('${pharmacyId || ''}')">حفظ</button>
    `;

    openModal(title, body, footer);
  }

  async function savePharmacy(pharmacyId) {
    const data = {
      name: document.getElementById('ph-name').value.trim(),
      name_ar: document.getElementById('ph-name-ar').value.trim() || null,
      phone: document.getElementById('ph-phone').value.trim() || null,
      email: document.getElementById('ph-email').value.trim() || null,
      city: document.getElementById('ph-city').value.trim() || null,
      subscription_plan: document.getElementById('ph-plan').value,
      is_active: document.getElementById('ph-active').checked,
    };

    if (!data.name) {
      toast('الاسم مطلوب', 'error');
      return;
    }

    try {
      if (pharmacyId) {
        await api(`/v1/super/pharmacies/${pharmacyId}`, {
          method: 'PUT',
          body: JSON.stringify(data),
        });
        toast('✅ تم التحديث', 'success');
      } else {
        await api('/v1/super/pharmacies', {
          method: 'POST',
          body: JSON.stringify(data),
        });
        toast('✅ تمت الإضافة', 'success');
      }
      closeModal();
      navigate('pharmacies');
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  async function deletePharmacy(id) {
    if (!confirm('هل أنت متأكد من حذف الصيدلية؟')) return;
    try {
      await api(`/v1/super/pharmacies/${id}`, { method: 'DELETE' });
      toast('✅ تم الحذف', 'success');
      navigate('pharmacies');
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  // ═══ User Modal ═══
  function openUserModal(userId = null) {
    const u = userId ? state.users.find(x => x.id === userId) : null;
    const title = u ? '✏️ تعديل مستخدم' : '➕ إضافة مستخدم';

    const pharmacyOptions = state.pharmacies.map(p =>
      `<option value="${p.id}" ${u?.pharmacy_id === p.id ? 'selected' : ''}>${esc(p.name_ar || p.name)}</option>`
    ).join('');

    const body = `
      ${!u ? `
        <div class="form-group">
          <label>اسم المستخدم</label>
          <input id="u-username" required>
        </div>
        <div class="form-group">
          <label>كلمة المرور</label>
          <input id="u-password" type="password" required>
        </div>
      ` : ''}
      <div class="form-group">
        <label>الاسم الكامل</label>
        <input id="u-fullname" value="${esc(u?.full_name || '')}">
      </div>
      <div class="form-group">
        <label>البريد الإلكتروني</label>
        <input id="u-email" type="email" value="${esc(u?.email || '')}">
      </div>
      <div class="form-group">
        <label>الهاتف</label>
        <input id="u-phone" value="${esc(u?.phone || '')}">
      </div>
      <div class="form-group">
        <label>الدور</label>
        <select id="u-role">
          <option value="customer" ${u?.role === 'customer' ? 'selected' : ''}>Customer</option>
          <option value="pharmacist" ${u?.role === 'pharmacist' ? 'selected' : ''}>Pharmacist</option>
          <option value="admin" ${u?.role === 'admin' ? 'selected' : ''}>Admin</option>
          <option value="super_admin" ${u?.role === 'super_admin' ? 'selected' : ''}>Super Admin</option>
        </select>
      </div>
      <div class="form-group">
        <label>الصيدلية (اترك فارغ لـ Super Admin)</label>
        <select id="u-pharmacy">
          <option value="">— لا يوجد (Super Admin) —</option>
          ${pharmacyOptions}
        </select>
      </div>
      ${u ? `
        <div class="form-group">
          <label>
            <input type="checkbox" id="u-active" ${u.is_active ? 'checked' : ''}>
            نشط
          </label>
        </div>
      ` : ''}
    `;

    const footer = `
      <button class="btn btn-ghost" onclick="Super.closeModal()">إلغاء</button>
      <button class="btn btn-primary" onclick="Super.saveUser('${userId || ''}')">حفظ</button>
    `;

    openModal(title, body, footer);
  }

  async function saveUser(userId) {
    const data = {
      full_name: document.getElementById('u-fullname').value.trim(),
      email: document.getElementById('u-email').value.trim() || null,
      phone: document.getElementById('u-phone').value.trim() || null,
      role: document.getElementById('u-role').value,
      pharmacy_id: document.getElementById('u-pharmacy').value || null,
    };

    try {
      if (userId) {
        data.is_active = document.getElementById('u-active').checked;
        await api(`/v1/super/users/${userId}`, {
          method: 'PUT',
          body: JSON.stringify(data),
        });
        toast('✅ تم التحديث', 'success');
      } else {
        data.username = document.getElementById('u-username').value.trim();
        data.password = document.getElementById('u-password').value;
        if (!data.username || !data.password) {
          toast('اسم المستخدم وكلمة المرور مطلوبان', 'error');
          return;
        }
        await api('/v1/super/users', {
          method: 'POST',
          body: JSON.stringify(data),
        });
        toast('✅ تمت الإضافة', 'success');
      }
      closeModal();
      navigate('users');
    } catch (e) {
      toast('❌ ' + e.message, 'error');
    }
  }

  async function deleteUser(id) {
    if (!confirm('هل أنت متأكد من حذف المستخدم؟')) return;
    try {
      await api(`/v1/super/users/${id}`, { method: 'DELETE' });
      toast('✅ تم الحذف', 'success');
      navigate('users');
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

  function redirectToAdmin() {
    window.location.href = '/admin';
  }

  async function init() {
    console.log('🚀 [super.js] init...');

    // ═══ Auto-login من /api/super/config ═══
    try {
      const config = await fetch('/api/super/config').then(r => r.json());

      if (!config.auto_login) {
        toast('Super Admin غير مفعّل', 'error');
        return;
      }

      console.log('🔐 Auto-login as:', config.username);

      const res = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          username: config.username,
          password: 'admin123',
        }),
      }).then(r => r.json());

      if (!res.access_token) {
        toast('فشل الدخول التلقائي', 'error');
        console.error('Login failed:', res);
        return;
      }

      state.token = res.access_token;
      state.user = res.user;

      localStorage.setItem('h1ai_admin_token', res.access_token);
      localStorage.setItem('h1ai_admin_user', JSON.stringify(res.user));

      console.log('✅ Super Admin confirmed:', res.user.username, '(' + res.user.role + ')');

      document.getElementById('super-user-name').textContent =
        res.user.full_name || res.user.username;
      document.getElementById('super-user-role').textContent = 'Super Admin';
    } catch (e) {
      toast('فشل التحميل: ' + e.message, 'error');
      console.error('Init error:', e);
      return;
    }

    // Events
    document.querySelectorAll('.super-nav-item').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        navigate(el.dataset.page);
      });
    });

    document.getElementById('super-logout').addEventListener('click', logout);
    document.getElementById('modal-close').addEventListener('click', closeModal);

    // Start
    navigate('dashboard');
  }

  // ═══ Export API ═══
  window.Super = {
    navigate,
    openPharmacyModal,
    savePharmacy,
    editPharmacy: openPharmacyModal,
    deletePharmacy,
    openUserModal,
    saveUser,
    editUser: openUserModal,
    deleteUser,
    closeModal,
  };

  // Auto-init
  document.addEventListener('DOMContentLoaded', init);
})();
