/* ═══════════════════════════════════════════════════════════════
   H1-AI Design System — Common JS
   ═══════════════════════════════════════════════════════════════ */

window.H1 = {
  // ═══ Utilities ═══
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  formatTime(ts) {
    if (!ts) return '—';
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });
  },

  formatDate(ts) {
    if (!ts) return '—';
    const d = new Date(ts * 1000);
    return d.toLocaleDateString('ar-EG');
  },

  // ═══ Toggle Password ═══
  togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
      input.type = 'text';
      if (btn) btn.textContent = '🙈';
    } else {
      input.type = 'password';
      if (btn) btn.textContent = '👁️';
    }
  },

  // ═══ Show Error ═══
  showError(el, msg, duration = 5000) {
    if (!el) return;
    el.innerHTML = H1.escapeHtml(msg);
    el.classList.add('show');
    if (duration > 0) {
      setTimeout(() => el.classList.remove('show'), duration);
    }
  },

  hideError(el) {
    if (el) el.classList.remove('show');
  },

  // ═══ Toast ═══
  toast(message, type = 'info', duration = 3000) {
    let container = document.getElementById('h1-toasts');
    if (!container) {
      container = document.createElement('div');
      container.id = 'h1-toasts';
      container.className = 'h1-toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `h1-toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  // ═══ Auth ═══
  getToken() {
    return localStorage.getItem('h1ai_user_token') || '';
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('h1ai_user') || 'null');
    } catch { return null; }
  },

  setAuth(token, user) {
    localStorage.setItem('h1ai_user_token', token);
    localStorage.setItem('h1ai_user', JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem('h1ai_user_token');
    localStorage.removeItem('h1ai_user');
  },

  logout() {
    H1.clearAuth();
    window.location.href = '/login';
  },

  isLoggedIn() {
    return !!H1.getToken();
  },

  requireAuth() {
    if (!H1.isLoggedIn()) {
      window.location.href = '/login';
      return false;
    }
    return true;
  },

  // ═══ API ═══
  async api(path, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (H1.isLoggedIn()) {
      headers['Authorization'] = `Bearer ${H1.getToken()}`;
    }
    try {
      const r = await fetch(path, { ...options, headers });
      if (r.status === 401) {
        H1.logout();
        return null;
      }
      const data = await r.json().catch(() => null);
      if (!r.ok) throw new Error(data?.detail || `HTTP ${r.status}`);
      return data;
    } catch(e) {
      console.error('API Error:', path, e);
      throw e;
    }
  },
};

// ═══ Init on DOM ready ═══
document.addEventListener('DOMContentLoaded', () => {
  console.log('🎨 H1-AI Design System loaded');
});
