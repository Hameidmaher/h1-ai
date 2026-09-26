/* ═══════════════════════════════════════════════════════════════
   H1-AI Control Center — Core JavaScript
   ═══════════════════════════════════════════════════════════════ */

const CC = {
  // ═══════════════════════════════════════════════════════════
  // State
  // ═══════════════════════════════════════════════════════════
  state: {
    theme: 'dark',
    density: 'comfortable',
    sidebarPosition: 'left',
    sidebarCollapsed: false,
    activeTab: 'dashboard',
    autoRefresh: true,
    refreshInterval: 2000,
    tableSize: 25,
    accent: '#60a5fa',
    cmdPaletteOpen: false,
    cmdHistory: [],
  },

  // ═══════════════════════════════════════════════════════════
  // Init
  // ═══════════════════════════════════════════════════════════
  init() {
    console.log('🏥 H1-AI Control Center — Init');
    this.loadPrefs();
    this.applyTheme();
    this.applyDensity();
    this.applySidebarPosition();
    this.bindEvents();
    this.bindKeyboard();
    this.updateThemeBtn();
    this.restoreActiveTab();
    this.showToast('✅ تم تحميل Control Center', 'success');
  },

  // ═══════════════════════════════════════════════════════════
  // Preferences
  // ═══════════════════════════════════════════════════════════
  loadPrefs() {
    try {
      const saved = JSON.parse(localStorage.getItem('h1ai_cc_prefs') || '{}');
      Object.assign(this.state, saved);
    } catch (e) {
      console.warn('Failed to load prefs:', e);
    }
  },

  savePrefs() {
    try {
      localStorage.setItem('h1ai_cc_prefs', JSON.stringify(this.state));
      console.log('💾 Prefs saved');
    } catch (e) {
      console.warn('Failed to save prefs:', e);
    }
  },

  // ═══════════════════════════════════════════════════════════
  // Theme
  // ═══════════════════════════════════════════════════════════
  applyTheme() {
    let theme = this.state.theme;
    if (theme === 'auto') {
      theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.setProperty('--cc-accent', this.state.accent);
  },

  setTheme(theme) {
    this.state.theme = theme;
    this.applyTheme();
    this.savePrefs();
    this.updateSettingsUI();
    this.updateThemeBtn();
    this.showToast(`🎨 الثيم: ${theme}`, 'success');
  },

  updateThemeBtn() {
    const icons = { dark: '🌙', light: '☀️', auto: '🖥️', custom: '🎨' };
    document.getElementById('cc-theme-btn').textContent = icons[this.state.theme] || '🌙';
  },

  toggleTheme() {
    const order = ['dark', 'light', 'auto'];
    const idx = order.indexOf(this.state.theme);
    const next = order[(idx + 1) % order.length];
    this.setTheme(next);
  },

  // ═══════════════════════════════════════════════════════════
  // Density
  // ═══════════════════════════════════════════════════════════
  applyDensity() {
    document.documentElement.setAttribute('data-density', this.state.density);
  },

  setDensity(density) {
    this.state.density = density;
    this.applyDensity();
    this.savePrefs();
    this.updateSettingsUI();
    this.showToast(`📐 الكثافة: ${density}`, 'success');
  },

  cycleDensity() {
    const order = ['compact', 'comfortable', 'spacious'];
    const idx = order.indexOf(this.state.density);
    const next = order[(idx + 1) % order.length];
    this.setDensity(next);
  },

  // ═══════════════════════════════════════════════════════════
  // Sidebar
  // ═══════════════════════════════════════════════════════════
  applySidebarPosition() {
    document.documentElement.setAttribute('data-sidebar', this.state.sidebarPosition);
    document.body.classList.toggle('cc-sidebar-collapsed', this.state.sidebarCollapsed);
  },

  setSidebarPosition(pos) {
    this.state.sidebarPosition = pos;
    this.applySidebarPosition();
    this.savePrefs();
    this.updateSettingsUI();
  },

  toggleSidebar() {
    if (window.innerWidth <= 768) {
      document.body.classList.toggle('cc-sidebar-open');
    } else {
      this.state.sidebarCollapsed = !this.state.sidebarCollapsed;
      this.applySidebarPosition();
      this.savePrefs();
    }
  },

  // ═══════════════════════════════════════════════════════════
  // Tabs
  // ═══════════════════════════════════════════════════════════
  switchTab(tab) {
    this.state.activeTab = tab;
    document.querySelectorAll('.cc-nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.tab === tab);
    });
    document.querySelectorAll('.cc-tab-content').forEach(el => {
      el.classList.toggle('hidden', el.dataset.tab !== tab);
    });
    this.savePrefs();
    window.location.hash = tab;
    if (window.innerWidth <= 768) {
      document.body.classList.remove('cc-sidebar-open');
    }
  },

  restoreActiveTab() {
    const hash = window.location.hash.slice(1);
    const tab = hash || this.state.activeTab || 'dashboard';
    this.switchTab(tab);
  },

  // ═══════════════════════════════════════════════════════════
  // Settings Panel
  // ═══════════════════════════════════════════════════════════
  openSettings() {
    document.getElementById('cc-settings-panel').classList.add('open');
    document.getElementById('cc-overlay').classList.add('open');
    this.updateSettingsUI();
  },

  closeSettings() {
    document.getElementById('cc-settings-panel').classList.remove('open');
    document.getElementById('cc-overlay').classList.remove('open');
  },

  updateSettingsUI() {
    document.querySelectorAll('[data-setting]').forEach(group => {
      const setting = group.dataset.setting;
      const value = this.state[setting];
      group.querySelectorAll('button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === String(value));
      });
    });
    const colorInput = document.getElementById('cc-accent-color');
    if (colorInput) colorInput.value = this.state.accent;
  },

  resetSettings() {
    this.state = {
      theme: 'dark', density: 'comfortable', sidebarPosition: 'left',
      sidebarCollapsed: false, activeTab: 'dashboard',
      autoRefresh: true, refreshInterval: 2000, tableSize: 25,
      accent: '#60a5fa', cmdPaletteOpen: false, cmdHistory: [],
    };
    this.applyTheme();
    this.applyDensity();
    this.applySidebarPosition();
    this.updateSettingsUI();
    this.updateThemeBtn();
    this.savePrefs();
    this.showToast('🔄 تمت إعادة التعيين', 'success');
  },

  // ═══════════════════════════════════════════════════════════
  // Command Palette
  // ═══════════════════════════════════════════════════════════
  openCmdPalette() {
    document.getElementById('cc-cmd-palette').classList.add('open');
    document.getElementById('cc-cmd-input').value = '';
    document.getElementById('cc-cmd-input').focus();
    this.renderCmdResults('');
    this.state.cmdPaletteOpen = true;
  },

  closeCmdPalette() {
    document.getElementById('cc-cmd-palette').classList.remove('open');
    this.state.cmdPaletteOpen = false;
  },

  commands: [
    { icon: '🏠', label: 'لوحة التحكم', action: () => CC.switchTab('dashboard'), keywords: ['dashboard', 'home'] },
    { icon: '🎛️', label: 'التحكم', action: () => CC.switchTab('control'), keywords: ['control'] },
    { icon: '📦', label: 'الإدارة', action: () => CC.switchTab('admin'), keywords: ['admin'] },
    { icon: '🤖', label: 'الذكاء الاصطناعي', action: () => CC.switchTab('ai'), keywords: ['ai'] },
    { icon: '📜', label: 'السجلات', action: () => CC.switchTab('logs'), keywords: ['logs'] },
    { icon: '🐳', label: 'البنية التحتية', action: () => CC.switchTab('infra'), keywords: ['infra', 'docker'] },
    { icon: '👥', label: 'المستخدمون', action: () => CC.switchTab('users'), keywords: ['users'] },
    { icon: '⚙️', label: 'الإعدادات', action: () => CC.openSettings(), keywords: ['settings'] },
    { icon: '🌙', label: 'تبديل الثيم', action: () => CC.toggleTheme(), keywords: ['theme', 'dark', 'light'] },
    { icon: '📐', label: 'تبديل الكثافة', action: () => CC.cycleDensity(), keywords: ['density'] },
    { icon: '🔄', label: 'إعادة التعيين', action: () => CC.resetSettings(), keywords: ['reset'] },
    { icon: '📤', label: 'تصدير', action: () => CC.exportData(), keywords: ['export'] },
  ],

  renderCmdResults(query) {
    const q = query.trim().toLowerCase();
    const results = q
      ? this.commands.filter(c => c.label.includes(q) || c.keywords.some(k => k.includes(q)))
      : this.commands;
    const container = document.getElementById('cc-cmd-results');
    if (results.length === 0) {
      container.innerHTML = '<div class="cc-cmd-result">لا نتائج</div>';
      return;
    }
    container.innerHTML = results.map((c, i) => `
      <div class="cc-cmd-result ${i === 0 ? 'active' : ''}" data-idx="${i}">
        <span style="font-size: 20px;">${c.icon}</span>
        <span>${c.label}</span>
      </div>
    `).join('');
    container.querySelectorAll('.cc-cmd-result').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.dataset.idx);
        results[idx].action();
        this.closeCmdPalette();
      });
    });
  },

  // ═══════════════════════════════════════════════════════════
  // Export
  // ═══════════════════════════════════════════════════════════
  exportData() {
    const data = {
      exportedAt: new Date().toISOString(),
      prefs: this.state,
      version: '5.0.0',
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `h1ai-cc-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    this.showToast('📤 تم التصدير', 'success');
  },

  // ═══════════════════════════════════════════════════════════
  // Toast
  // ═══════════════════════════════════════════════════════════
  showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('cc-toasts');
    const toast = document.createElement('div');
    toast.className = `cc-toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  // ═══════════════════════════════════════════════════════════
  // Events
  // ═══════════════════════════════════════════════════════════
  bindEvents() {
    document.getElementById('cc-sidebar-toggle').addEventListener('click', () => this.toggleSidebar());
    document.getElementById('cc-theme-btn').addEventListener('click', () => this.toggleTheme());
    document.getElementById('cc-density-btn').addEventListener('click', () => this.cycleDensity());
    document.getElementById('cc-settings-btn').addEventListener('click', () => this.openSettings());
    document.getElementById('cc-close-settings').addEventListener('click', () => this.closeSettings());
    document.getElementById('cc-overlay').addEventListener('click', () => this.closeSettings());
    document.getElementById('cc-export-btn').addEventListener('click', () => this.exportData());
    document.getElementById('cc-open-search').addEventListener('click', () => this.openCmdPalette());
    document.getElementById('cc-reset-settings').addEventListener('click', () => this.resetSettings());
    document.getElementById('cc-save-settings').addEventListener('click', () => {
      this.savePrefs();
      this.closeSettings();
      this.showToast('💾 تم الحفظ', 'success');
    });

    // Nav items
    document.querySelectorAll('.cc-nav-item').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchTab(el.dataset.tab);
      });
    });

    // Settings options
    document.querySelectorAll('[data-setting]').forEach(group => {
      group.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
          const setting = group.dataset.setting;
          let value = btn.dataset.value;
          if (setting === 'refreshInterval' || setting === 'tableSize') value = parseInt(value);
          this.state[setting] = value;
          if (setting === 'theme') this.applyTheme();
          if (setting === 'density') this.applyDensity();
          if (setting === 'sidebarPosition') this.applySidebarPosition();
          this.updateSettingsUI();
          this.savePrefs();
        });
      });
    });

    // Accent color
    const colorInput = document.getElementById('cc-accent-color');
    if (colorInput) {
      colorInput.addEventListener('input', (e) => {
        this.state.accent = e.target.value;
        this.applyTheme();
        this.savePrefs();
      });
    }

    // Command palette input
    const cmdInput = document.getElementById('cc-cmd-input');
    cmdInput.addEventListener('input', (e) => this.renderCmdResults(e.target.value));
    cmdInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const active = document.querySelector('.cc-cmd-result.active');
        if (active) active.click();
      }
    });
    document.getElementById('cc-cmd-palette').addEventListener('click', (e) => {
      if (e.target.id === 'cc-cmd-palette') this.closeCmdPalette();
    });

    // Window resize
    window.addEventListener('resize', () => {
      if (window.innerWidth > 768) {
        document.body.classList.remove('cc-sidebar-open');
      }
    });

    // Auto theme
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (this.state.theme === 'auto') this.applyTheme();
    });
  },

  bindKeyboard() {
    document.addEventListener('keydown', (e) => {
      // Cmd+K / Ctrl+K → Command Palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        this.openCmdPalette();
        return;
      }
      // Esc → close things
      if (e.key === 'Escape') {
        if (this.state.cmdPaletteOpen) this.closeCmdPalette();
        else this.closeSettings();
        return;
      }
      // Alt+1..8 → switch tabs
      if (e.altKey && /^[1-8]$/.test(e.key)) {
        e.preventDefault();
        const tabs = ['dashboard', 'control', 'admin', 'ai', 'logs', 'infra', 'users', 'settings'];
        this.switchTab(tabs[parseInt(e.key) - 1]);
        return;
      }
      // Alt+T → toggle theme
      if (e.altKey && e.key === 't') { e.preventDefault(); this.toggleTheme(); }
      // Alt+D → cycle density
      if (e.altKey && e.key === 'd') { e.preventDefault(); this.cycleDensity(); }
      // Alt+S → sidebar
      if (e.altKey && e.key === 's') { e.preventDefault(); this.toggleSidebar(); }
    });
  },
};

// ═══ Init on Load ═══
document.addEventListener('DOMContentLoaded', () => CC.init());
window.CC = CC;

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD + CONTROL — Batch 2
   ═══════════════════════════════════════════════════════════════ */

const CC_DATA = {
  responseChart: null,
  toolsChart: null,
  endpointsChart: null,
  refreshTimer: null,
};

// ═══ Init Charts ═══
CC.initCharts = function() {
  const chartOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color: getComputedStyle(document.documentElement).getPropertyValue('--cc-text-secondary').trim(), font: { size: 11 } } } },
    scales: {
      x: { grid: { color: 'rgba(148,163,184,.1)' }, ticks: { color: '#64748b', font: { size: 10 } } },
      y: { grid: { color: 'rgba(148,163,184,.1)' }, ticks: { color: '#64748b', font: { size: 10 } } }
    }
  };
  
  const respCanvas = document.getElementById('cc-chart-response');
  if (respCanvas && !CC_DATA.responseChart) {
    CC_DATA.responseChart = new Chart(respCanvas, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Response Time (ms)', data: [], borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,.1)', fill: true, tension: .3, pointRadius: 2 }] },
      options: chartOpts
    });
  }
  
  const toolsCanvas = document.getElementById('cc-chart-tools');
  if (toolsCanvas && !CC_DATA.toolsChart) {
    CC_DATA.toolsChart = new Chart(toolsCanvas, {
      type: 'doughnut',
      data: { labels: [], datasets: [{ data: [], backgroundColor: ['#60a5fa','#4ade80','#fbbf24','#ef4444','#a78bfa','#f472b6','#22d3ee'] }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 } } } } }
    });
  }
  
  const epCanvas = document.getElementById('cc-chart-endpoints');
  if (epCanvas && !CC_DATA.endpointsChart) {
    CC_DATA.endpointsChart = new Chart(epCanvas, {
      type: 'bar',
      data: { labels: [], datasets: [{ label: 'عدد الطلبات', data: [], backgroundColor: '#4ade80' }] },
      options: { ...chartOpts, indexAxis: 'y' }
    });
  }
};

// ═══ Fetch Helpers ═══
CC.api = async function(path) {
  try {
    const r = await fetch(`/v1/monitoring${path}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch(e) {
    console.error('API error:', path, e);
    return null;
  }
};

CC.controlApi = async function(action) {
  try {
    const r = await fetch(`/v1/control/${action}`, { method: 'POST' });
    return await r.json();
  } catch(e) {
    return { success: false, message: `❌ ${e}` };
  }
};

CC.fmtTime = function(ts) {
  if (!ts) return '—';
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

CC.statusClass = function(code) {
  if (code < 300) return 'cc-status-2xx';
  if (code < 500) return 'cc-status-4xx';
  return 'cc-status-5xx';
};

CC.barColor = function(pct) {
  if (pct < 50) return 'linear-gradient(90deg,#4ade80,#22c55e)';
  if (pct < 80) return 'linear-gradient(90deg,#fbbf24,#f59e0b)';
  return 'linear-gradient(90deg,#ef4444,#dc2626)';
};

// ═══ Update KPI Cards ═══
CC.updateDashboard = async function() {
  // System
  const sys = await this.api('/system');
  if (sys) {
    const setText = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    const setBar = (id, pct) => { const el = document.getElementById(id); if (el) { el.style.width = pct + '%'; el.style.background = CC.barColor(pct); } };
    
    setText('kpi-cpu', sys.cpu.percent_total);
    setBar('kpi-cpu-bar', sys.cpu.percent_total);
    setText('kpi-cpu-sub', `Load: ${sys.cpu.load_avg.map(x => x.toFixed(2)).join(' / ')}`);
    
    setText('kpi-ram', sys.memory.percent);
    setBar('kpi-ram-bar', sys.memory.percent);
    setText('kpi-ram-sub', `${sys.memory.used_gb} / ${sys.memory.total_gb} GB`);
    
    setText('kpi-disk', sys.disk.percent);
    setBar('kpi-disk-bar', sys.disk.percent);
    setText('kpi-disk-sub', `${sys.disk.used_gb} / ${sys.disk.total_gb} GB`);
  }
  
  // Requests
  const req = await this.api('/requests');
  if (req) {
    const setText = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setText('kpi-req', req.last_minute);
    setText('kpi-req-total', req.total);
    setText('kpi-success', req.success);
    setText('kpi-4xx', req.errors_4xx);
    setText('kpi-5xx', req.errors_5xx);
    setText('kpi-avg', req.avg_ms);
    setText('kpi-min', req.min_ms);
    setText('kpi-max', req.max_ms);
    
    // Response chart
    if (CC_DATA.responseChart) {
      const recent = (req.recent || []).slice(-50);
      CC_DATA.responseChart.data.labels = recent.map(r => this.fmtTime(r.ts));
      CC_DATA.responseChart.data.datasets[0].data = recent.map(r => r.duration_ms);
      CC_DATA.responseChart.update('none');
    }
    
    // Endpoints chart
    if (CC_DATA.endpointsChart) {
      const top = (req.top_endpoints || []).slice(0, 8);
      CC_DATA.endpointsChart.data.labels = top.map(e => e.path.length > 25 ? e.path.slice(0, 25) + '…' : e.path);
      CC_DATA.endpointsChart.data.datasets[0].data = top.map(e => e.count);
      CC_DATA.endpointsChart.update('none');
    }
    
    // Recent requests table
    const tbody = document.getElementById('cc-req-table');
    if (tbody) {
      const latest = (req.recent || []).slice(-20).reverse();
      if (latest.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="cc-table-empty">في انتظار البيانات...</td></tr>';
      } else {
        tbody.innerHTML = latest.map(r => `
          <tr>
            <td style="color:#64748b">${this.fmtTime(r.ts)}</td>
            <td><span class="cc-method">${r.method}</span></td>
            <td style="color:#cbd5e1">${r.path.length > 40 ? r.path.slice(0, 40) + '…' : r.path}</td>
            <td class="${this.statusClass(r.status)}">${r.status}</td>
            <td style="color:#94a3b8">${r.duration_ms}ms</td>
          </tr>
        `).join('');
      }
      const cnt = document.getElementById('cc-req-count');
      if (cnt) cnt.textContent = req.total;
    }
  }
  
  // Tools
  const tools = await this.api('/tool-calls');
  if (tools) {
    if (CC_DATA.toolsChart) {
      const byTool = tools.by_tool || {};
      const labels = Object.keys(byTool);
      CC_DATA.toolsChart.data.labels = labels;
      CC_DATA.toolsChart.data.datasets[0].data = labels.map(k => byTool[k].count);
      CC_DATA.toolsChart.update('none');
    }
  }
  
  // Logs
  const logs = await this.api('/logs?lines=100');
  if (logs && logs.lines) {
    const el = document.getElementById('cc-logs');
    if (el) {
      el.innerHTML = logs.lines.slice(-100).map(line => {
        let cls = 'cc-log-line';
        if (/error|exception|fail|traceback/i.test(line)) cls += ' error';
        else if (/warn|warning/i.test(line)) cls += ' warn';
        else if (/info|success/i.test(line)) cls += ' info';
        return `<div class="${cls}">${line.replace(/</g, '&lt;')}</div>`;
      }).join('');
      el.scrollTop = el.scrollHeight;
    }
  }
};

// ═══ Control Action ═══
CC.controlAction = async function(action) {
  const card = document.querySelector(`.cc-control-card[data-action="${action}"]`);
  const btn = card?.querySelector('button');
  const outCard = document.getElementById('cc-control-output-card');
  const outPre = document.getElementById('cc-control-output');
  
  if (btn) { btn.disabled = true; btn.textContent = '⏳ جاري...'; }
  
  let result;
  if (action === 'system-info') {
    const r = await fetch('/v1/control/system-info');
    result = await r.json();
  } else {
    result = await this.controlApi(action);
  }
  
  if (outCard && outPre) {
    outCard.style.display = 'block';
    outPre.textContent = JSON.stringify(result, null, 2);
  }
  
  if (btn) { btn.disabled = false; btn.textContent = 'تنفيذ'; }
  
  const type = result.success ? 'success' : 'error';
  this.showToast(result.message || 'تم', type);
};

// ═══ Auto-refresh Loop ═══
CC.startAutoRefresh = function() {
  if (CC_DATA.refreshTimer) clearInterval(CC_DATA.refreshTimer);
  const interval = this.state.refreshInterval || 2000;
  CC_DATA.refreshTimer = setInterval(() => {
    if (this.state.autoRefresh) this.updateDashboard();
  }, interval);
};

// ═══ Patch Init ═══
const _origInit = CC.init.bind(CC);
CC.init = function() {
  _origInit();
  setTimeout(() => {
    this.initCharts();
    this.updateDashboard();
    this.startAutoRefresh();
  }, 200);
};

/* ═══════════════════════════════════════════════════════════════
   BATCH 3 — Admin + AI + Infrastructure
   ═══════════════════════════════════════════════════════════════ */

CC_DATA.llmChart = null;
CC_DATA.toolUsageChart = null;

// ═══ Admin: Stats ═══
CC.loadAdminStats = async function() {
  try {
    const r = await fetch('/v1/cc/admin/stats');
    const d = await r.json();
    if (d.tables) {
      Object.entries(d.tables).forEach(([k, v]) => {
        const el = document.getElementById(`stat-${k}`);
        if (el) el.textContent = v;
      });
    }
  } catch(e) { console.error(e); }
};

// ═══ Admin: Products ═══
CC.productsState = { page: 1, size: 25, search: '' };
CC.loadProducts = async function(page = 1) {
  this.productsState.page = page;
  const { size, search } = this.productsState;
  const tbody = document.getElementById('admin-products-table');
  tbody.innerHTML = '<tr><td colspan="5" class="cc-table-empty">جاري التحميل...</td></tr>';
  try {
    const r = await fetch(`/v1/cc/admin/products?page=${page}&size=${size}&search=${encodeURIComponent(search)}`);
    const d = await r.json();
    if (d.items && d.items.length) {
      tbody.innerHTML = d.items.map(p => `
        <tr>
          <td style="color:#64748b">${p.ItemCode || p.item_code || '—'}</td>
          <td style="color:#cbd5e1">${p.ItemName || p.item_name || '—'}</td>
          <td style="color:#94a3b8">${p.Category || p.category || '—'}</td>
          <td style="color:#4ade80">${p.Price || p.price || '—'}</td>
          <td style="color:#fbbf24">${p.StockQty || p.stock_qty || '—'}</td>
        </tr>
      `).join('');
      this.renderPagination('admin-products-pagination', d.page, d.pages, 'CC.loadProducts');
    } else {
      tbody.innerHTML = `<tr><td colspan="5" class="cc-table-empty">${d.error || 'لا توجد نتائج'}</td></tr>`;
    }
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="5" class="cc-table-empty">❌ ${e.message}</td></tr>`;
  }
};

// ═══ Admin: Drugs ═══
CC.drugsState = { page: 1, size: 25, search: '' };
CC.loadDrugs = async function(page = 1) {
  this.drugsState.page = page;
  const { size, search } = this.drugsState;
  const tbody = document.getElementById('admin-drugs-table');
  tbody.innerHTML = '<tr><td colspan="4" class="cc-table-empty">جاري التحميل...</td></tr>';
  try {
    const r = await fetch(`/v1/cc/admin/drugs?page=${page}&size=${size}&search=${encodeURIComponent(search)}`);
    const d = await r.json();
    if (d.items && d.items.length) {
      tbody.innerHTML = d.items.map(dr => `
        <tr>
          <td style="color:#64748b">${dr.id || '—'}</td>
          <td style="color:#cbd5e1">${dr.name || '—'}</td>
          <td style="color:#94a3b8">${dr.generic_name || '—'}</td>
          <td style="color:#60a5fa">${dr.category || dr.drug_class || '—'}</td>
        </tr>
      `).join('');
      this.renderPagination('admin-drugs-pagination', d.page, d.pages, 'CC.loadDrugs');
    } else {
      tbody.innerHTML = `<tr><td colspan="4" class="cc-table-empty">${d.error || 'لا توجد نتائج'}</td></tr>`;
    }
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="4" class="cc-table-empty">❌ ${e.message}</td></tr>`;
  }
};

// ═══ Pagination renderer ═══
CC.renderPagination = function(elId, current, total, callbackName) {
  const el = document.getElementById(elId);
  if (!el || total <= 1) { if (el) el.innerHTML = ''; return; }
  const pages = [];
  const start = Math.max(1, current - 2);
  const end = Math.min(total, current + 2);
  for (let i = start; i <= end; i++) pages.push(i);
  el.innerHTML = `
    <button ${current === 1 ? 'disabled' : ''} onclick="${callbackName}(1)">«</button>
    <button ${current === 1 ? 'disabled' : ''} onclick="${callbackName}(${current - 1})">‹</button>
    ${pages.map(p => `<button class="${p === current ? 'active' : ''}" onclick="${callbackName}(${p})">${p}</button>`).join('')}
    <button ${current === total ? 'disabled' : ''} onclick="${callbackName}(${current + 1})">›</button>
    <button ${current === total ? 'disabled' : ''} onclick="${callbackName}(${total})">»</button>
  `;
};

// ═══ AI: Charts init ═══
CC.initAICharts = function() {
  const opts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11 } } } },
    scales: {
      x: { grid: { color: 'rgba(148,163,184,.1)' }, ticks: { color: '#64748b', font: { size: 10 } } },
      y: { grid: { color: 'rgba(148,163,184,.1)' }, ticks: { color: '#64748b', font: { size: 10 } } }
    }
  };
  const llmCanvas = document.getElementById('cc-chart-llm');
  if (llmCanvas && !CC_DATA.llmChart) {
    CC_DATA.llmChart = new Chart(llmCanvas, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'LLM Response (ms)', data: [], borderColor: '#a78bfa', backgroundColor: 'rgba(167,139,250,.1)', fill: true, tension: .3, pointRadius: 2 }] },
      options: opts
    });
  }
  const usageCanvas = document.getElementById('cc-chart-tool-usage');
  if (usageCanvas && !CC_DATA.toolUsageChart) {
    CC_DATA.toolUsageChart = new Chart(usageCanvas, {
      type: 'bar',
      data: { labels: [], datasets: [{ label: 'عدد الاستدعاءات', data: [], backgroundColor: '#4ade80' }] },
      options: { ...opts, indexAxis: 'y' }
    });
  }
};

// ═══ AI: Load data ═══
CC.loadAI = async function() {
  try {
    const r = await fetch('/v1/cc/ai/llm-stats');
    const d = await r.json();
    document.getElementById('ai-llm-total').textContent = d.total || 0;
    document.getElementById('ai-llm-avg').innerHTML = `${d.avg_ms || 0}<span class="cc-kpi-unit">ms</span>`;
    if (CC_DATA.llmChart) {
      const recent = (d.recent || []).slice(-30);
      CC_DATA.llmChart.data.labels = recent.map((c, i) => i + 1);
      CC_DATA.llmChart.data.datasets[0].data = recent.map(c => c.duration_ms || 0);
      CC_DATA.llmChart.update('none');
    }
  } catch(e) { console.error(e); }

  try {
    const r = await fetch('/v1/cc/ai/tool-stats');
    const d = await r.json();
    document.getElementById('ai-tool-total').textContent = d.total || 0;
    if (CC_DATA.toolUsageChart && d.by_tool) {
      const labels = Object.keys(d.by_tool).slice(0, 10);
      CC_DATA.toolUsageChart.data.labels = labels;
      CC_DATA.toolUsageChart.data.datasets[0].data = labels.map(k => d.by_tool[k].count);
      CC_DATA.toolUsageChart.update('none');
    }
    const tbody = document.getElementById('ai-tools-table');
    const recent = (d.recent || []).slice(-20).reverse();
    if (recent.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="cc-table-empty">لا توجد بيانات</td></tr>';
    } else {
      tbody.innerHTML = recent.map(t => `
        <tr>
          <td style="color:#64748b">${this.fmtTime(t.ts)}</td>
          <td><span style="background:#1e40af;color:#93c5fd;padding:2px 8px;border-radius:4px;font-size:10px">${t.tool || '—'}</span></td>
          <td>${t.success ? '✅' : '❌'}</td>
          <td style="color:#94a3b8">${(t.duration_ms || 0).toFixed(0)}ms</td>
        </tr>
      `).join('');
    }
  } catch(e) { console.error(e); }

  try {
    const r = await fetch('/v1/cc/ai/chat-activity?limit=20');
    const d = await r.json();
    document.getElementById('ai-chat-total').textContent = d.total || 0;
    const tbody = document.getElementById('ai-chat-table');
    const recent = (d.recent || []).reverse();
    if (recent.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="cc-table-empty">لا توجد بيانات</td></tr>';
    } else {
      tbody.innerHTML = recent.map(c => `
        <tr>
          <td style="color:#64748b">${this.fmtTime(c.ts)}</td>
          <td style="color:#cbd5e1">${c.user || '—'}</td>
          <td style="color:#94a3b8">${(c.message || '').slice(0, 60)}</td>
          <td>${(c.tools || []).map(t => `<span style="background:#1e40af;color:#93c5fd;padding:1px 6px;border-radius:3px;font-size:10px;margin:1px">${t}</span>`).join('') || '—'}</td>
        </tr>
      `).join('');
    }
  } catch(e) { console.error(e); }
};

// ═══ Infra: Load ═══
CC.loadInfra = async function() {
  // Services
  try {
    const r = await fetch('/v1/cc/infra/services');
    const d = await r.json();
    const el = document.getElementById('infra-services');
    el.innerHTML = Object.entries(d.services || {}).map(([name, status]) => {
      const cls = status === 'active' ? 'active' : 'failed';
      return `<div class="cc-service-item ${cls}"><span>${name}</span><span class="cc-service-status ${cls}">${status}</span></div>`;
    }).join('');
  } catch(e) { console.error(e); }

  // Docker
  try {
    const r = await fetch('/v1/cc/infra/docker');
    const d = await r.json();
    const tbody = document.getElementById('infra-docker-table');
    if (d.containers && d.containers.length) {
      tbody.innerHTML = d.containers.map(c => `
        <tr>
          <td style="color:#cbd5e1">${c.name}</td>
          <td style="color:#94a3b8;font-size:11px">${c.image}</td>
          <td style="color:${c.status.includes('Up') ? '#4ade80' : '#ef4444'}">${c.status}</td>
          <td style="color:#64748b;font-size:11px">${c.ports || '—'}</td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = `<tr><td colspan="4" class="cc-table-empty">${d.error || 'لا توجد containers'}</td></tr>`;
    }
  } catch(e) { console.error(e); }

  // Processes
  try {
    const r = await fetch('/v1/cc/infra/processes');
    const d = await r.json();
    const renderProcs = (procs) => procs.map(p => `
      <tr>
        <td style="color:#64748b">${p.pid}</td>
        <td style="color:#cbd5e1">${p.name}</td>
        <td style="color:#fbbf24">${p.cpu}%</td>
        <td style="color:#60a5fa">${p.mem}%</td>
      </tr>
    `).join('');
    document.getElementById('infra-procs-cpu').innerHTML = renderProcs(d.top_cpu || []);
    document.getElementById('infra-procs-mem').innerHTML = renderProcs(d.top_mem || []);
  } catch(e) { console.error(e); }

  // Ports
  try {
    const r = await fetch('/v1/cc/infra/network');
    const d = await r.json();
    const tbody = document.getElementById('infra-ports-table');
    if (d.ports && d.ports.length) {
      tbody.innerHTML = d.ports.slice(0, 30).map(p => `
        <tr>
          <td style="color:#60a5fa">${p.state}</td>
          <td style="color:#cbd5e1;font-family:monospace">${p.local}</td>
          <td style="color:#94a3b8;font-size:11px">${p.process}</td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = '<tr><td colspan="3" class="cc-table-empty">لا توجد بيانات</td></tr>';
    }
  } catch(e) { console.error(e); }
};

// ═══ Search handlers ═══
document.addEventListener('input', (e) => {
  if (e.target.id === 'admin-products-search') {
    clearTimeout(CC._productsTimer);
    CC._productsTimer = setTimeout(() => {
      CC.productsState.search = e.target.value;
      CC.loadProducts(1);
    }, 300);
  }
  if (e.target.id === 'admin-drugs-search') {
    clearTimeout(CC._drugsTimer);
    CC._drugsTimer = setTimeout(() => {
      CC.drugsState.search = e.target.value;
      CC.loadDrugs(1);
    }, 300);
  }
});

// ═══ Patch: on tab switch, load data ═══
const _origSwitchTab = CC.switchTab.bind(CC);
CC.switchTab = function(tab) {
  _origSwitchTab(tab);
  if (tab === 'admin') {
    this.loadAdminStats();
    this.loadProducts();
    this.loadDrugs();
  }
  if (tab === 'ai') {
    this.initAICharts();
    this.loadAI();
  }
  if (tab === 'infra') {
    this.loadInfra();
  }
};

/* ═══ Users Tab (Batch 4.1) ═══ */
CC.usersState = { page: 1, size: 25, role: '', active: '', search: '' };

CC.loadUsers = async function(page) {
  page = page || 1;
  this.usersState.page = page;
  const s = this.usersState;
  const tbody = document.getElementById('users-table');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="7" class="cc-table-empty">جاري التحميل...</td></tr>';
  try {
    const q = new URLSearchParams({ page: s.page, size: s.size, role: s.role, active: s.active, search: s.search });
    const r = await fetch('/v1/cc/users?' + q);
    const d = await r.json();
    if (d.items && d.items.length) {
      tbody.innerHTML = d.items.map(u => `
        <tr>
          <td style="color:#64748b;font-size:11px">${(u.id||'').slice(0,8)}…</td>
          <td style="color:#cbd5e1">${u.username || '—'}</td>
          <td style="color:#94a3b8;font-size:11px">${u.email || '—'}</td>
          <td><span class="cc-badge role-${u.role}">${u.role}</span></td>
          <td style="color:#94a3b8;font-size:11px">${(u.pharmacy_id||'').slice(0,8) || '—'}</td>
          <td><span class="cc-badge ${u.is_active?'active':'inactive'}">${u.is_active?'✅ نشط':'❌ معطل'}</span></td>
          <td><button class="cc-btn cc-btn-sm cc-btn-secondary" onclick="CC.toggleUser('${u.id}')">🔄</button></td>
        </tr>
      `).join('');
      this.renderPagination('users-pagination', d.page, d.pages, 'CC.loadUsers');
    } else {
      tbody.innerHTML = `<tr><td colspan="7" class="cc-table-empty">${d.error||'لا يوجد مستخدمون'}</td></tr>`;
    }
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="7" class="cc-table-empty">❌ ${e.message}</td></tr>`;
  }
};

CC.loadUsersStats = async function() {
  try {
    const r = await fetch('/v1/cc/users/stats');
    const d = await r.json();
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set('users-total', d.total || 0);
    set('users-active', d.active || 0);
    set('users-inactive', d.inactive || 0);
    const el = document.getElementById('users-roles');
    if (el && d.by_role) {
      el.innerHTML = Object.entries(d.by_role).map(([r,c]) => `<span class="cc-badge role-${r}" style="margin:2px">${r}: ${c}</span>`).join(' ');
    }
  } catch(e) { console.error(e); }
};

CC.toggleUser = async function(userId) {
  try {
    const r = await fetch(`/v1/cc/users/${userId}/toggle`, { method: 'POST' });
    const d = await r.json();
    if (d.success) {
      this.showToast(`✅ ${d.is_active ? 'تم التفعيل' : 'تم التعطيل'}`, 'success');
      this.loadUsers(this.usersState.page);
      this.loadUsersStats();
    } else {
      this.showToast(`❌ ${d.error || 'فشل'}`, 'error');
    }
  } catch(e) {
    this.showToast(`❌ ${e.message}`, 'error');
  }
};

// Filters
document.addEventListener('input', (e) => {
  if (e.target.id === 'users-search') {
    clearTimeout(CC._usT);
    CC._usT = setTimeout(() => { CC.usersState.search = e.target.value; CC.loadUsers(1); }, 300);
  }
});
document.addEventListener('change', (e) => {
  if (e.target.id === 'users-role-filter') { CC.usersState.role = e.target.value; CC.loadUsers(1); }
  if (e.target.id === 'users-active-filter') { CC.usersState.active = e.target.value; CC.loadUsers(1); }
});

// Hook into switchTab
const _origSwitchUsers = CC.switchTab.bind(CC);
CC.switchTab = function(tab) {
  _origSwitchUsers(tab);
  if (tab === 'users') {
    this.loadUsersStats();
    this.loadUsers(1);
  }
};

/* ═══ Users Tab (4.1) ═══ */
CC.usersState = { page: 1, size: 25, role: '', active: '', search: '' };

CC.loadUsers = async function(page) {
  page = page || 1;
  this.usersState.page = page;
  const s = this.usersState;
  const tbody = document.getElementById('users-table');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="7" class="cc-table-empty">جاري التحميل...</td></tr>';
  try {
    const q = new URLSearchParams({ page: s.page, size: s.size, role: s.role, active: s.active, search: s.search });
    const r = await fetch('/v1/cc/users?' + q);
    const d = await r.json();
    if (d.items && d.items.length) {
      tbody.innerHTML = d.items.map(u => `
        <tr>
          <td style="color:#64748b;font-size:11px">${(u.id||'').slice(0,8)}…</td>
          <td style="color:#cbd5e1">${u.username || '—'}</td>
          <td style="color:#94a3b8;font-size:11px">${u.email || '—'}</td>
          <td><span class="cc-badge role-${u.role}">${u.role}</span></td>
          <td style="color:#94a3b8;font-size:11px">${(u.pharmacy_id||'').slice(0,8) || '—'}</td>
          <td><span class="cc-badge ${u.is_active?'active':'inactive'}">${u.is_active?'✅ نشط':'❌ معطل'}</span></td>
          <td><button class="cc-btn cc-btn-sm cc-btn-secondary" onclick="CC.toggleUser('${u.id}')">🔄</button></td>
        </tr>`).join('');
      this.renderPagination('users-pagination', d.page, d.pages, 'CC.loadUsers');
    } else {
      tbody.innerHTML = `<tr><td colspan="7" class="cc-table-empty">${d.error||'لا يوجد مستخدمون'}</td></tr>`;
    }
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="7" class="cc-table-empty">❌ ${e.message}</td></tr>`;
  }
};

CC.loadUsersStats = async function() {
  try {
    const r = await fetch('/v1/cc/users/stats');
    const d = await r.json();
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set('users-total', d.total || 0);
    set('users-active', d.active || 0);
    set('users-inactive', d.inactive || 0);
    const el = document.getElementById('users-roles');
    if (el && d.by_role) el.innerHTML = Object.entries(d.by_role).map(([r,c]) => `<span class="cc-badge role-${r}" style="margin:2px">${r}: ${c}</span>`).join(' ');
  } catch(e) { console.error(e); }
};

CC.toggleUser = async function(userId) {
  try {
    const r = await fetch(`/v1/cc/users/${userId}/toggle`, { method: 'POST' });
    const d = await r.json();
    if (d.success) {
      this.showToast(`✅ ${d.is_active ? 'تم التفعيل' : 'تم التعطيل'}`, 'success');
      this.loadUsers(this.usersState.page);
      this.loadUsersStats();
    } else this.showToast(`❌ ${d.error || 'فشل'}`, 'error');
  } catch(e) { this.showToast(`❌ ${e.message}`, 'error'); }
};

document.addEventListener('input', (e) => {
  if (e.target.id === 'users-search') {
    clearTimeout(CC._usT);
    CC._usT = setTimeout(() => { CC.usersState.search = e.target.value; CC.loadUsers(1); }, 300);
  }
});
document.addEventListener('change', (e) => {
  if (e.target.id === 'users-role-filter') { CC.usersState.role = e.target.value; CC.loadUsers(1); }
  if (e.target.id === 'users-active-filter') { CC.usersState.active = e.target.value; CC.loadUsers(1); }
});
const _orig4a = CC.switchTab.bind(CC);
CC.switchTab = function(tab) {
  _orig4a(tab);
  if (tab === 'users') { this.loadUsersStats(); this.loadUsers(1); }
};

/* ═══ Settings Tab (4.2) ═══ */
CC.loadEnvSettings = async function() {
  try {
    const r = await fetch('/v1/cc/settings/env');
    const d = await r.json();
    const tb = document.getElementById('settings-env-table');
    if (tb && d.settings) {
      tb.innerHTML = Object.entries(d.settings).map(([k,v]) => `
        <tr><td style="color:#60a5fa;font-weight:600">${k}</td>
        <td style="color:#cbd5e1;font-family:monospace;font-size:11px">${v}</td></tr>`).join('');
    } else if (tb) {
      tb.innerHTML = `<tr><td colspan="2" class="cc-table-empty">${d.error||'—'}</td></tr>`;
    }
  } catch(e) { console.error(e); }
};

CC.loadSettings = async function() {
  this.loadEnvSettings();
  try {
    const r = await fetch('/v1/cc/settings/db');
    const d = await r.json();
    const el = document.getElementById('settings-db-info');
    if (el) el.innerHTML = `
      <div class="cc-info-item"><div class="cc-info-label">Database</div><div class="cc-info-value">${d.database||'—'}</div></div>
      <div class="cc-info-item"><div class="cc-info-label">الحجم</div><div class="cc-info-value">${d.size_mb||0} MB</div></div>
      <div class="cc-info-item"><div class="cc-info-label">الاتصالات</div><div class="cc-info-value">${d.connections||0}</div></div>
      <div class="cc-info-item"><div class="cc-info-label">الإصدار</div><div class="cc-info-value" style="font-size:11px">${(d.version||'—').slice(0,50)}</div></div>`;
  } catch(e) { console.error(e); }
  try {
    const r = await fetch('/v1/cc/settings/rate-limits');
    const d = await r.json();
    const el = document.getElementById('settings-rate-limits');
    if (el) el.innerHTML = `
      <div class="cc-info-item"><div class="cc-info-label">Chat</div><div class="cc-info-value">${d.chat||'—'}</div></div>
      <div class="cc-info-item"><div class="cc-info-label">Auth</div><div class="cc-info-value">${d.auth||'—'}</div></div>`;
  } catch(e) { console.error(e); }
  try {
    const r = await fetch('/v1/cc/settings/features');
    const d = await r.json();
    const el = document.getElementById('settings-features');
    if (el) el.innerHTML = Object.entries(d).map(([name, enabled]) => `
      <div class="cc-feature-item">
        <span class="cc-feature-name">${name}</span>
        <button class="cc-feature-toggle ${enabled?'on':''}" onclick="CC.toggleFeature('${name}', this)"></button>
      </div>`).join('');
  } catch(e) { console.error(e); }
};

CC.toggleFeature = async function(name, btn) {
  const enabled = !btn.classList.contains('on');
  try {
    const r = await fetch('/v1/cc/settings/features/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, enabled }),
    });
    const d = await r.json();
    if (d.success) {
      btn.classList.toggle('on', enabled);
      this.showToast(`✅ ${name}: ${enabled?'مفعّل':'معطّل'}`, 'success');
    }
  } catch(e) { this.showToast(`❌ ${e.message}`, 'error'); }
};

const _orig4b = CC.switchTab.bind(CC);
CC.switchTab = function(tab) {
  _orig4b(tab);
  if (tab === 'settings') this.loadSettings();
};

/* ═══ Search + Export (4.3) ═══ */
CC.exportMetricsJSON = async function() {
  try {
    const r = await fetch('/v1/cc/export/metrics');
    const d = await r.json();
    const blob = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `h1ai-metrics-${Date.now()}.json`;
    a.click();
    this.showToast('📄 تم تصدير JSON', 'success');
  } catch(e) { this.showToast('❌ فشل', 'error'); }
};

CC.exportRequestsCSV = async function() {
  try {
    const r = await fetch('/v1/cc/export/metrics');
    const d = await r.json();
    const lines = ['ts,method,path,status,duration_ms'];
    (d.requests || []).forEach(x => lines.push(`${x.ts},${x.method},${x.path},${x.status},${x.duration_ms}`));
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `h1ai-requests-${Date.now()}.csv`;
    a.click();
    this.showToast('📊 تم تصدير CSV', 'success');
  } catch(e) { this.showToast('❌ فشل', 'error'); }
};

CC.exportSettings = function() {
  const data = { exportedAt: new Date().toISOString(), prefs: this.state };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `h1ai-settings-${Date.now()}.json`;
  a.click();
  this.showToast('⚙️ تم التصدير', 'success');
};

// ═══ Notifications ═══
CC.notifications = [];
CC.addNotification = function(msg) {
  this.notifications.unshift({ msg, ts: Date.now() });
  this.notifications = this.notifications.slice(0, 20);
  const badge = document.getElementById('cc-notif-badge');
  if (badge) { badge.textContent = this.notifications.length; badge.style.display = 'block'; }
};

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('cc-notif-btn');
  if (btn) btn.addEventListener('click', () => {
    CC.showToast(`🔔 ${CC.notifications.length} تنبيه`, 'info');
    CC.notifications = [];
    const b = document.getElementById('cc-notif-badge');
    if (b) b.style.display = 'none';
  });
});

/* ═══ Admin Chat ═══ */
CC.adminChatOpen = false;

CC.toggleAdminChat = function() {
  const panel = document.getElementById('cc-chat-panel');
  if (!panel) return;
  CC.adminChatOpen = !CC.adminChatOpen;
  panel.classList.toggle('open', CC.adminChatOpen);
  if (CC.adminChatOpen) {
    setTimeout(() => document.getElementById('cc-chat-input')?.focus(), 300);
  }
};

CC.addAdminMessage = function(role, text) {
  const container = document.getElementById('cc-chat-messages');
  if (!container) return;
  document.querySelector('.cc-chat-welcome')?.remove();
  const el = document.createElement('div');
  el.className = `cc-chat-msg ${role}`;
  el.innerHTML = `
    <div class="cc-chat-msg-avatar">${role === 'user' ? '👑' : '🤖'}</div>
    <div class="cc-chat-msg-content">${(text || '').replace(/</g, '&lt;')}</div>
  `;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
};

CC.addAdminTyping = function() {
  const container = document.getElementById('cc-chat-messages');
  const el = document.createElement('div');
  el.id = 'cc-chat-typing';
  el.className = 'cc-chat-msg bot';
  el.innerHTML = `
    <div class="cc-chat-msg-avatar">🤖</div>
    <div class="cc-chat-msg-content">
      <div class="cc-chat-typing"><span></span><span></span><span></span></div>
    </div>
  `;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
};

CC.removeAdminTyping = function() {
  document.getElementById('cc-chat-typing')?.remove();
};

CC.sendAdminSuggestion = function(text) {
  const input = document.getElementById('cc-chat-input');
  if (!input) return;
  input.value = text;
  CC.sendAdminMessage(new Event('submit'));
};

CC.sendAdminMessage = async function(e) {
  if (e) e.preventDefault();
  const input = document.getElementById('cc-chat-input');
  const msg = input.value.trim();
  if (!msg) return;

  const token = localStorage.getItem('h1ai_admin_token') || localStorage.getItem('h1ai_user_token');

  input.value = '';
  CC.addAdminMessage('user', msg);
  CC.addAdminTyping();

  try {
    const r = await fetch('/v1/admin/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token || ''}`
      },
      body: JSON.stringify({ message: msg })
    });
    CC.removeAdminTyping();
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'فشل');
    CC.addAdminMessage('bot', d.reply || '—');
  } catch(ex) {
    CC.removeAdminTyping();
    CC.addAdminMessage('bot', '❌ ' + ex.message);
  }
};

/* ═══════════════════════════════════════════════════════════════
   Admin Chat — FAB + Drawer
   ═══════════════════════════════════════════════════════════════ */

CC.adminChatOpen = false;

CC.toggleAdminChat = function() {
  const drawer = document.getElementById('cc-chat-drawer');
  if (!drawer) return;
  CC.adminChatOpen = !CC.adminChatOpen;
  drawer.classList.toggle('open', CC.adminChatOpen);
  if (CC.adminChatOpen) {
    setTimeout(() => document.getElementById('cc-chat-input-field')?.focus(), 350);
  }
};

CC.addAdminMsg = function(role, text) {
  const body = document.getElementById('cc-chat-body');
  if (!body) return;
  document.getElementById('cc-chat-intro')?.remove();
  const el = document.createElement('div');
  el.className = `cc-msg ${role}`;
  const avatar = role === 'user' ? '👑' : '🤖';

  // تنسيق بسيط للنص
  let formatted = (text || '').replace(/</g, '&lt;');
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/```([^`]+)```/g, '<code>$1</code>');

  el.innerHTML = `
    <div class="cc-msg-avatar">${avatar}</div>
    <div class="cc-msg-content">${formatted}</div>
  `;
  body.appendChild(el);
  body.scrollTop = body.scrollHeight;
};

CC.addAdminTyping = function() {
  const body = document.getElementById('cc-chat-body');
  if (!body) return;
  const el = document.createElement('div');
  el.id = 'cc-admin-typing';
  el.className = 'cc-msg bot';
  el.innerHTML = `
    <div class="cc-msg-avatar">🤖</div>
    <div class="cc-msg-content">
      <div class="cc-typing"><span></span><span></span><span></span></div>
    </div>
  `;
  body.appendChild(el);
  body.scrollTop = body.scrollHeight;
};

CC.removeAdminTyping = function() {
  document.getElementById('cc-admin-typing')?.remove();
};

CC.sendAdminQuick = function(text) {
  const input = document.getElementById('cc-chat-input-field');
  if (!input) return;
  input.value = text;
  CC.sendAdminMessage(new Event('submit'));
};

CC.sendAdminMessage = async function(e) {
  if (e) e.preventDefault();
  const input = document.getElementById('cc-chat-input-field');
  const btn = document.getElementById('cc-chat-submit');
  if (!input) return;
  const msg = input.value.trim();
  if (!msg) return;

  // جلب التوكن (admin أو user)
  const token = localStorage.getItem('h1ai_admin_token') || localStorage.getItem('h1ai_user_token') || '';

  input.value = '';
  if (btn) btn.disabled = true;

  CC.addAdminMsg('user', msg);
  CC.addAdminTyping();

  try {
    const r = await fetch('/v1/chat/admin/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message: msg }),
    });
    CC.removeAdminTyping();

    if (r.status === 401 || r.status === 403) {
      CC.addAdminMsg('bot', '⚠️ محتاج تسجل دخول كـ Super Admin');
      return;
    }

    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`);
    CC.addAdminMsg('bot', d.reply || '—');
  } catch(ex) {
    CC.removeAdminTyping();
    CC.addAdminMsg('bot', '❌ ' + ex.message);
  }

  if (btn) btn.disabled = false;
  input.focus();
};
