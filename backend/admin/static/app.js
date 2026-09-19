/**
 * H1-AI Admin Dashboard — Core JS
 */

const App = {
  state: {
    token: localStorage.getItem('h1ai_admin_token') || '',
    user: JSON.parse(localStorage.getItem('h1ai_admin_user') || 'null'),
    currentPage: 'dashboard',
  },

  // ──────── Init ────────
  init() {
    document.getElementById('login-form')
      .addEventListener('submit', (e) => this.handleLogin(e));
    document.getElementById('logout-btn')
      .addEventListener('click', () => this.handleLogout());
    document.getElementById('modal-close')
      .addEventListener('click', () => this.closeModal());

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        this.navigate(page);
      });
    });

    // Check auth
    if (this.state.token) {
      this.showApp();
    } else {
      this.showLogin();
    }
  },

  // ──────── Auth ────────
  async handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';

    try {
      const res = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        errEl.textContent = 'بيانات الدخول غير صحيحة';
        return;
      }

      const data = await res.json();
      if (data.user.role !== 'admin') {
        errEl.textContent = 'هذا الحساب ليس مديراً';
        return;
      }

      this.state.token = data.access_token;
      this.state.user = data.user;
      localStorage.setItem('h1ai_admin_token', data.access_token);
      localStorage.setItem('h1ai_admin_user', JSON.stringify(data.user));

      this.showApp();
    } catch (err) {
      errEl.textContent = 'فشل الاتصال بالخادم';
    }
  },

  handleLogout() {
    this.state.token = '';
    this.state.user = null;
    localStorage.removeItem('h1ai_admin_token');
    localStorage.removeItem('h1ai_admin_user');
    this.showLogin();
  },

  showLogin() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app').classList.add('hidden');
  },

  showApp() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    document.getElementById('user-name').textContent =
      this.state.user?.username || 'admin';
    this.navigate('dashboard');
  },

  // ──────── Navigation ────────
  navigate(page) {
    this.state.currentPage = page;

    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.page === page);
    });

    const titles = {
      dashboard: 'لوحة التحكم',
      products: 'إدارة المنتجات',
      drugs: 'إدارة الأدوية',
      conditions: 'الحالات الطبية',
      interactions: 'التداخلات الدوائية',
      synonyms: 'المرادفات',
      audit: 'سجل التعديلات',
      chat: 'محادثة تجريبية',
      settings: 'الإعدادات',
    };
    document.getElementById('page-title').textContent = titles[page] || page;

    const content = document.getElementById('content');
    content.innerHTML = '<div class="empty-state"><span class="icon">⏳</span>جاري التحميل...</div>';

    switch (page) {
      case 'dashboard':   Pages.dashboard.render(content); break;
      case 'products':    Pages.products.render(content); break;
      case 'drugs':       Pages.drugs.render(content); break;
      case 'conditions':  Pages.conditions.render(content); break;
      case 'interactions':Pages.interactions.render(content); break;
      case 'synonyms':    Pages.synonyms.render(content); break;
      case 'audit':       Pages.audit.render(content); break;
      case 'chat':        Pages.chat.render(content); break;
      case 'settings':    Pages.settings.render(content); break;
      default: content.innerHTML = '<div class="empty-state">صفحة غير معروفة</div>';
    }
  },

  // ──────── API ────────
  async api(path, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.state.token}`,
      ...(options.headers || {}),
    };

    const res = await fetch(path, { ...options, headers });

    if (res.status === 401) {
      this.handleLogout();
      throw new Error('انتهت الجلسة');
    }

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API Error ${res.status}: ${text}`);
    }

    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return res.json();
    }
    return res.text();
  },

  // ──────── UI Helpers ────────
  toast(message, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = message;
    el.className = `toast show ${type}`;
    setTimeout(() => el.className = 'toast', 3000);
  },

  openModal(title, bodyHtml, footerHtml) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHtml;
    document.getElementById('modal-footer').innerHTML = footerHtml || '';
    document.getElementById('modal').classList.remove('hidden');
  },

  closeModal() {
    document.getElementById('modal').classList.add('hidden');
  },

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text ?? '';
    return div.innerHTML;
  },

  formatDate(iso) {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('ar-EG');
    } catch { return iso; }
  },
};

// ════════════════════════════════════════════════════════════
// PAGES
// ════════════════════════════════════════════════════════════

const Pages = {};

// ──────── Dashboard ────────
Pages.dashboard = {
  async render(el) {
    try {
      const stats = await App.api('/v1/admin/products/stats');
      const html = `
        <div id="dashboard-charts"></div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="label">المنتجات</div>
            <div class="value">${stats.products_count}</div>
          </div>
          <div class="stat-card success">
            <div class="label">الأدوية</div>
            <div class="value">${stats.drugs_count}</div>
          </div>
          <div class="stat-card">
            <div class="label">الحالات</div>
            <div class="value">${stats.conditions_count}</div>
          </div>
          <div class="stat-card">
            <div class="label">التداخلات</div>
            <div class="value">${stats.interactions_count}</div>
          </div>
          <div class="stat-card">
            <div class="label">المرادفات</div>
            <div class="value">${stats.synonyms_count}</div>
          </div>
          <div class="stat-card warning">
            <div class="label">مخزون منخفض</div>
            <div class="value">${stats.low_stock_count}</div>
          </div>
          <div class="stat-card danger">
            <div class="label">قريبة الانتهاء</div>
            <div class="value">${stats.expiring_soon_count}</div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><h2>روابط سريعة</h2></div>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <button class="btn btn-primary" onclick="App.navigate('products')">📦 المنتجات</button>
            <button class="btn btn-primary" onclick="App.navigate('drugs')">💊 الأدوية</button>
            <button class="btn btn-primary" onclick="App.navigate('audit')">📜 السجل</button>
            <button class="btn btn-primary" onclick="App.navigate('settings')">⚙️ الإعدادات</button>
          </div>
        </div>
      `;
      el.innerHTML = html;
      // Render charts after DOM is ready
      setTimeout(() => {
        if (window.Charts) Charts.renderDashboardCharts(stats);
      }, 100);
    } catch (e) {
      el.innerHTML = `<div class="empty-state">خطأ: ${e.message}</div>`;
    }
  },
};
