/**
 * H1-AI — Enhanced Dashboard
 */
Pages.dashboard_enhanced = {
  data: null,

  async render(el) {
    el.innerHTML = `
      <style>
        .dh-header{margin-bottom:24px}
        .dh-header h1{margin:0;font-size:28px}
        .dh-header p{color:#64748B;margin-top:4px;font-size:14px}
        .dh-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}
        .dh-kpi{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;transition:all 0.15s;cursor:pointer}
        .dh-kpi:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.08)}
        .dh-kpi-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
        .dh-kpi-icon{font-size:24px}
        .dh-kpi-trend{font-size:11px;font-weight:600;padding:2px 6px;border-radius:6px}
        .dh-kpi-trend.up{background:#DCFCE7;color:#166534}
        .dh-kpi-trend.down{background:#FEE2E2;color:#991B1B}
        .dh-kpi-value{font-size:32px;font-weight:700;color:#0F172A}
        .dh-kpi-label{font-size:12px;color:#64748B;margin-top:4px}
        .dh-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px;margin-bottom:24px}
        .dh-card{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0}
        .dh-card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
        .dh-card h3{margin:0;font-size:16px}
        .dh-card-action{font-size:12px;color:#0EA5E9;text-decoration:none;font-weight:600}
        .dh-activity{padding:12px 0;border-bottom:1px solid #F1F5F9;display:flex;gap:12px;align-items:flex-start}
        .dh-activity:last-child{border-bottom:none}
        .dh-activity-icon{width:36px;height:36px;border-radius:50%;background:#EFF6FF;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}
        .dh-activity-content{flex:1}
        .dh-activity-title{font-size:13px;font-weight:600;color:#0F172A;margin-bottom:2px}
        .dh-activity-time{font-size:11px;color:#94A3B8}
        .dh-quick-actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
        .dh-action{padding:16px;background:#F8FAFC;border-radius:10px;border:1px solid #E2E8F0;text-align:center;cursor:pointer;transition:all 0.15s;text-decoration:none;color:inherit}
        .dh-action:hover{background:#EFF6FF;border-color:#0EA5E9;transform:translateY(-2px)}
        .dh-action-icon{font-size:28px;margin-bottom:6px}
        .dh-action-label{font-size:13px;font-weight:600}
        .dh-emptydata{text-align:center;padding:30px;color:#94A3B8;font-size:13px}
      </style>

      <div class="dh-header">
        <h1>📊 لوحة المعلومات</h1>
        <p>نظرة عامة على أداء المنصة</p>
      </div>

      <div class="dh-kpis" id="dh-kpis"></div>

      <div class="dh-grid">
        <div class="dh-card">
          <div class="dh-card-header">
            <h3>📈 نشاط آخر 7 أيام</h3>
            <a href="#analytics" class="dh-card-action" onclick="App.navigate('analytics')">التفاصيل ←</a>
          </div>
          <canvas id="dh-chart" style="max-height:220px"></canvas>
        </div>

        <div class="dh-card">
          <div class="dh-card-header">
            <h3>🕐 آخر النشاطات</h3>
            <a href="#activity_log" class="dh-card-action" onclick="App.navigate('activity_log')">الكل ←</a>
          </div>
          <div id="dh-activities"></div>
        </div>
      </div>

      <div class="dh-card" style="margin-bottom:24px">
        <div class="dh-card-header">
          <h3>⚡ إجراءات سريعة</h3>
        </div>
        <div class="dh-quick-actions">
          <a class="dh-action" onclick="App.navigate('pharmacies')">
            <div class="dh-action-icon">🏥</div>
            <div class="dh-action-label">الصيدليات</div>
          </a>
          <a class="dh-action" onclick="App.navigate('whatsapp_sessions')">
            <div class="dh-action-icon">📱</div>
            <div class="dh-action-label">WhatsApp</div>
          </a>
          <a class="dh-action" onclick="App.navigate('live_feed')">
            <div class="dh-action-icon">📡</div>
            <div class="dh-action-label">البث الحي</div>
          </a>
          <a class="dh-action" onclick="App.navigate('analytics')">
            <div class="dh-action-icon">📈</div>
            <div class="dh-action-label">التحليلات</div>
          </a>
          <a class="dh-action" onclick="App.navigate('subscriptions')">
            <div class="dh-action-icon">💳</div>
            <div class="dh-action-label">الاشتراكات</div>
          </a>
          <a class="dh-action" onclick="App.navigate('api_keys')">
            <div class="dh-action-icon">🔑</div>
            <div class="dh-action-label">API Keys</div>
          </a>
        </div>
      </div>
    `;

    // Load Chart.js
    if (!window.Chart) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
      document.head.appendChild(script);
      await new Promise(r => script.onload = r);
    }

    await this.loadData();
    this.renderKPIs();
    this.renderChart();
    this.renderActivities();
  },

  async loadData() {
    try {
      const [analytics, activities] = await Promise.all([
        App.api('/v1/admin/analytics/overview'),
        App.api('/v1/admin/audit/logs?limit=5').catch(() => ({ logs: [] })),
      ]);
      this.data = {
        overview: analytics.overview || {},
        daily: analytics.daily || [],
        activities: activities.logs || [],
      };
    } catch (e) {
      console.error('Dashboard load error:', e);
      this.data = { overview: {}, daily: [], activities: [] };
    }
  },

  renderKPIs() {
    const o = this.data.overview;
    const kpis = [
      { icon: '🏥', label: 'الصيدليات', value: o.total_pharmacies || 0, trend: 'up' },
      { icon: '✅', label: 'نشطة', value: o.active_pharmacies || 0, trend: 'up' },
      { icon: '📱', label: 'WhatsApp', value: o.connected_numbers || 0 },
      { icon: '👥', label: 'المستخدمين', value: o.total_users || 0 },
      { icon: '📨', label: 'الرسائل', value: (o.total_messages || 0).toLocaleString() },
      { icon: '📅', label: 'اليوم', value: o.messages_today || 0 },
    ];

    document.getElementById('dh-kpis').innerHTML = kpis.map(k => `
      <div class="dh-kpi">
        <div class="dh-kpi-header">
          <span class="dh-kpi-icon">${k.icon}</span>
          ${k.trend ? `<span class="dh-kpi-trend ${k.trend}">↑</span>` : ''}
        </div>
        <div class="dh-kpi-value">${k.value}</div>
        <div class="dh-kpi-label">${k.label}</div>
      </div>
    `).join('');
  },

  renderChart() {
    setTimeout(() => {
      const ctx = document.getElementById('dh-chart');
      if (!ctx || !this.data.daily.length) {
        if (ctx) ctx.parentElement.innerHTML = '<div class="dh-emptydata">لا توجد بيانات</div>';
        return;
      }

      new Chart(ctx, {
        type: 'line',
        data: {
          labels: this.data.daily.map(d => d.date),
          datasets: [{
            data: this.data.daily.map(d => d.count),
            borderColor: '#0EA5E9',
            backgroundColor: 'rgba(14, 165, 233, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 3,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } },
        },
      });
    }, 100);
  },

  renderActivities() {
    const c = document.getElementById('dh-activities');
    const activities = this.data.activities;

    if (!activities.length) {
      c.innerHTML = '<div class="dh-emptydata">لا توجد نشاطات</div>';
      return;
    }

    const icons = { create: '➕', update: '✏️', delete: '🗑️', login: '🔐' };

    c.innerHTML = activities.slice(0, 5).map(a => `
      <div class="dh-activity">
        <div class="dh-activity-icon">${icons[a.action] || '📝'}</div>
        <div class="dh-activity-content">
          <div class="dh-activity-title">${a.action} — ${App.escapeHtml(a.entity || '')}</div>
          <div class="dh-activity-time">${App.formatDate(a.created_at)}</div>
        </div>
      </div>
    `).join('');
  },
};
