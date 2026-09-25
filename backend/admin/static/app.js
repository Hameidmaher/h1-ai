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
    // Load saved theme
    this.loadTheme();
    
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
        // Auto-close mobile menu
        if (window.innerWidth <= 768) {
          this.toggleMobileMenu();
        }
      });
    });

    // Check auth
    if (this.state.token) {
      this.showApp();
    } else {
      this.showLogin();
    }

    // Login page enhancements (Phase 2)
    this.initLoginEnhancements();
  },
  // ──────── Auth ────────
  async handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errEl = document.getElementById('login-error');
    const attemptsEl = document.getElementById('login-attempts');
    const btn = document.getElementById('login-btn');
    const btnText = btn.querySelector('.btn-text');
    const btnSpinner = btn.querySelector('.btn-spinner');
    const rememberMe = document.getElementById('remember-me')?.checked;

    // Reset messages
    errEl.textContent = '';
    attemptsEl.textContent = '';
    attemptsEl.classList.remove('warning');

    // Client-side validation
    if (username.length < 3) {
      errEl.textContent = '⚠️ اسم المستخدم قصير جدًا';
      document.getElementById('username').focus();
      return;
    }
    if (password.length < 6) {
      errEl.textContent = '⚠️ كلمة المرور قصيرة جدًا';
      document.getElementById('password').focus();
      return;
    }

    // Loading state
    btn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';

    try {
      const res = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (res.status === 401 || res.status === 403) {
        errEl.textContent = '❌ اسم المستخدم أو كلمة المرور غير صحيحة';
        document.getElementById('password').value = '';
        document.getElementById('password').focus();
        this.trackLoginAttempt();
        return;
      }

      if (res.status === 429) {
        errEl.textContent = '⏸️ محاولات كثيرة — انتظر دقيقة ثم حاول مرة أخرى';
        this.trackLoginAttempt();
        return;
      }

      if (!res.ok) {
        errEl.textContent = `❌ خطأ غير متوقع (${res.status})`;
        return;
      }

      const data = await res.json();

      if (!data.user || data.user.role !== 'admin') {
        errEl.textContent = '🚫 هذا الحساب ليس مديرًا';
        this.trackLoginAttempt();
        return;
      }

      // Success
      this.state.token = data.access_token;
      this.state.user = data.user;
      localStorage.setItem('h1ai_admin_token', data.access_token);
      localStorage.setItem('h1ai_admin_user', JSON.stringify(data.user));

      // Remember me
      if (rememberMe) {
        localStorage.setItem('h1ai_remember_username', username);
      } else {
        localStorage.removeItem('h1ai_remember_username');
      }

      // Reset attempts counter
      localStorage.removeItem('h1ai_login_attempts');

      this.showApp();

    } catch (err) {
      console.error('Login error:', err);
      errEl.textContent = '🌐 فشل الاتصال بالخادم — تأكد من الإنترنت';
    } finally {
      btn.disabled = false;
      btnText.style.display = 'inline';
      btnSpinner.style.display = 'none';
    }
  },

  // Track failed attempts
  trackLoginAttempt() {
    const attempts = parseInt(localStorage.getItem('h1ai_login_attempts') || '0') + 1;
    localStorage.setItem('h1ai_login_attempts', attempts);

    if (attempts >= 3) {
      const attemptsEl = document.getElementById('login-attempts');
      attemptsEl.textContent = `⚠️ ${attempts} محاولات فاشلة — قد يتم حظر IP مؤقتًا`;
      attemptsEl.classList.add('warning');
    }
  },

  // Toggle password visibility
  togglePassword() {
    const pwd = document.getElementById('password');
    const btn = document.getElementById('toggle-password');
    if (!pwd || !btn) return;
    if (pwd.type === 'password') {
      pwd.type = 'text';
      btn.textContent = '🙈';
    } else {
      pwd.type = 'password';
      btn.textContent = '👁️';
    }
    pwd.focus();
  },

  // Init login page enhancements
  initLoginEnhancements() {
    // Auto-focus
    setTimeout(() => {
      const usernameInput = document.getElementById('username');
      const rememberedUser = localStorage.getItem('h1ai_remember_username');
      if (rememberedUser && usernameInput) {
        usernameInput.value = rememberedUser;
        document.getElementById('remember-me').checked = true;
        document.getElementById('password').focus();
      } else if (usernameInput) {
        usernameInput.focus();
      }
    }, 100);

    // Password toggle
    const toggleBtn = document.getElementById('toggle-password');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.togglePassword());
    }

    // Reset error on typing
    ['username', 'password'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', () => {
          const errEl = document.getElementById('login-error');
          if (errEl) errEl.textContent = '';
        });
      }
    });
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

  toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('h1ai_theme', isDark ? 'dark' : 'light');
    const btn = document.querySelector('.theme-toggle');
    if (btn) btn.textContent = isDark ? '☀️' : '🌙';
  },

  loadTheme() {
    const saved = localStorage.getItem('h1ai_theme');
    if (saved === 'dark') {
      document.body.classList.add('dark-mode');
      const btn = document.querySelector('.theme-toggle');
      if (btn) btn.textContent = '☀️';
    }
  },

  // ──────── Notifications ────────
  notifications: [],
  notifCount: 0,

  async loadNotifications() {
    try {
      const data = await this.api('/webhook/v2/messages?limit=5');
      const messages = data.messages || [];
      this.notifications = messages.slice(0, 5);
      this.notifCount = this.notifications.length;
      this.updateNotifBadge();
    } catch (e) {
      console.warn('Notifications failed:', e);
    }
  },

  updateNotifBadge() {
    const badge = document.getElementById('notif-badge');
    if (!badge) return;
    if (this.notifCount > 0) {
      badge.textContent = this.notifCount;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  },

  showNotifications() {
    if (!this.notifications.length) {
      App.toast('لا توجد إشعارات جديدة', 'success');
      return;
    }
    
    const items = this.notifications.map(n => 
      `<div style="padding:10px;border-bottom:1px solid #E2E8F0">
        <div style="font-size:12px;color:#64748B">${n.from_phone || 'مجهول'}</div>
        <div style="font-size:14px;margin-top:4px">${this.escapeHtml((n.content || '').slice(0, 60))}</div>
      </div>`
    ).join('');

    this.openModal('🔔 الإشعارات', items, 
      '<button class="btn btn-ghost" onclick="App.closeModal()">إغلاق</button>');
    
    this.notifCount = 0;
    this.updateNotifBadge();
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
      activity_log: 'سجل النشاطات',
      api_keys: 'مفاتيح API',
      alerts: 'التنبيهات',
      feature_flags: 'ميزات النظام',
      subscriptions: 'الاشتراكات',
      analytics: 'التحليلات',
      pharmacies: 'الصيدليات والأرقام',
      whatsapp_sessions: 'أرقام WhatsApp المتصلة',
      live_feed: 'البث الحي للرسائل',
      settings: 'الإعدادات',
    };
    document.getElementById('page-title').textContent = titles[page] || page;

    const content = document.getElementById('content');
    content.innerHTML = '<div class="empty-state"><span class="icon">⏳</span>جاري التحميل...</div>';

    switch (page) {
      case 'dashboard':   Pages.dashboard_enhanced.render(content); break;
      case 'products':    Pages.products.render(content); break;
      case 'drugs':       Pages.drugs.render(content); break;
      case 'conditions':  Pages.conditions.render(content); break;
      case 'interactions':Pages.interactions.render(content); break;
      case 'synonyms':    Pages.synonyms.render(content); break;
      case 'audit':       Pages.audit.render(content); break;
      case 'chat':        Pages.chat.render(content); break;
      case 'inbox':       Pages.inbox.render(content); break;
      case 'pharmacies':  Pages.pharmacies.render(content); break;
      case 'whatsapp_sessions': Pages.whatsapp_sessions.render(content); break;
      case 'live_feed': Pages.live_feed.render(content); break;
      case 'settings':    Pages.settings.render(content); break;
      case 'analytics':  Pages.analytics.render(content); break;
      case 'subscriptions':  Pages.subscriptions.render(content); break;
      case 'feature_flags':  Pages.feature_flags.render(content); break;
      case 'alerts':  Pages.alerts.render(content); break;
      case 'api_keys':  Pages.api_keys.render(content); break;
      case 'activity_log': Pages.activity_log.render(content); break;
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

// ═══════════════════════════════════════════════════════════
//  Mobile Sidebar Toggle — موحد
// ═══════════════════════════════════════════════════════════
(function setupMobileSidebar() {
    function toggleMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.mobile-overlay');
        if (!sidebar) return;

        const isOpen = sidebar.classList.toggle('open');
        document.body.classList.toggle('sidebar-open', isOpen);
        if (overlay) {
            overlay.classList.toggle('active', isOpen);
        }
    }

    function closeMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.mobile-overlay');
        sidebar?.classList.remove('open');
        overlay?.classList.remove('active');
        document.body.classList.remove('sidebar-open');
    }

    // expose globally
    window.App = window.App || {};
    window.App.toggleMobileMenu = toggleMobileMenu;
    window.App.closeMobileMenu = closeMobileMenu;

    // Event listeners
    document.addEventListener('DOMContentLoaded', () => {
        // زر المنيو
        const menuBtn = document.querySelector('.mobile-menu-btn');
        menuBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleMobileMenu();
        });

        // overlay يقفل
        const overlay = document.querySelector('.mobile-overlay');
        overlay?.addEventListener('click', closeMobileMenu);

        // nav item click → اقفل الـ sidebar
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    setTimeout(closeMobileMenu, 150);
                }
            });
        });

        // ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeMobileMenu();
        });

        // على resize للديسكتوب — اقفل
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (window.innerWidth > 768) closeMobileMenu();
            }, 150);
        });
    });
})();
