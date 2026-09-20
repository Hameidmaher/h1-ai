/**
 * H1-AI — Analytics Dashboard
 */
Pages.analytics = {
  data: null,

  async render(el) {
    el.innerHTML = `
      <style>
        .an-header{margin-bottom:20px}
        .an-header h1{margin:0;font-size:24px}
        .an-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:24px}
        .an-kpi{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;text-align:center;transition:all 0.15s}
        .an-kpi:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.06)}
        .an-kpi-value{font-size:32px;font-weight:700;color:#0EA5E9}
        .an-kpi-label{font-size:12px;color:#64748B;margin-top:4px}
        .an-charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}
        .an-card{background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0}
        .an-card h3{margin:0 0 16px 0;font-size:16px}
        .an-bar{display:flex;align-items:center;gap:8px;margin-bottom:8px}
        .an-bar-label{flex:1;font-size:13px}
        .an-bar-value{font-weight:600;font-size:13px;color:#0EA5E9}
        .an-bar-track{width:100%;height:8px;background:#F1F5F9;border-radius:4px;overflow:hidden}
        .an-bar-fill{height:100%;background:linear-gradient(90deg, #0EA5E9, #10B981);transition:width 0.5s}
        canvas{max-height: 250px}
      </style>

      <div class="an-header">
        <h1>📈 التحليلات</h1>
      </div>

      <div id="an-content">
        <div style="text-align:center;padding:60px">⏳ جاري التحميل...</div>
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
    this.render();
  },

  async loadData() {
    try {
      this.data = await App.api('/v1/admin/analytics/overview');
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
      this.data = null;
    }
  },

  render() {
    const c = document.getElementById('an-content');
    if (!this.data) {
      c.innerHTML = '<div style="text-align:center;padding:60px">❌ فشل تحميل البيانات</div>';
      return;
    }

    const { overview, daily, top_pharmacies } = this.data;

    c.innerHTML = `
      <div class="an-kpis">
        <div class="an-kpi">
          <div class="an-kpi-value">${overview.total_pharmacies || 0}</div>
          <div class="an-kpi-label">🏥 الصيدليات</div>
        </div>
        <div class="an-kpi">
          <div class="an-kpi-value" style="color:#10B981">${overview.active_pharmacies || 0}</div>
          <div class="an-kpi-label">✅ النشطة</div>
        </div>
        <div class="an-kpi">
          <div class="an-kpi-value" style="color:#3B82F6">${overview.connected_numbers || 0}</div>
          <div class="an-kpi-label">📱 WhatsApp</div>
        </div>
        <div class="an-kpi">
          <div class="an-kpi-value">${overview.total_users || 0}</div>
          <div class="an-kpi-label">👥 المستخدمين</div>
        </div>
        <div class="an-kpi">
          <div class="an-kpi-value">${overview.total_messages || 0}</div>
          <div class="an-kpi-label">📨 إجمالي الرسائل</div>
        </div>
        <div class="an-kpi">
          <div class="an-kpi-value" style="color:#F59E0B">${overview.messages_today || 0}</div>
          <div class="an-kpi-label">📅 اليوم</div>
        </div>
      </div>

      <div class="an-charts">
        <div class="an-card">
          <h3>📊 الرسائل (آخر 7 أيام)</h3>
          <canvas id="an-daily-chart"></canvas>
        </div>
        <div class="an-card">
          <h3>🏆 أفضل الصيدليات</h3>
          ${top_pharmacies.map(p => {
            const max = top_pharmacies[0]?.messages || 1;
            const pct = (p.messages / max) * 100;
            return `
              <div style="margin-bottom:12px">
                <div class="an-bar">
                  <span class="an-bar-label">${App.escapeHtml(p.name)}</span>
                  <span class="an-bar-value">${p.messages}</span>
                </div>
                <div class="an-bar-track">
                  <div class="an-bar-fill" style="width:${pct}%"></div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;

    // Render chart
    setTimeout(() => {
      const ctx = document.getElementById('an-daily-chart');
      if (ctx && daily.length) {
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: daily.map(d => d.date),
            datasets: [{
              label: 'الرسائل',
              data: daily.map(d => d.count),
              borderColor: '#0EA5E9',
              backgroundColor: 'rgba(14, 165, 233, 0.1)',
              fill: true,
              tension: 0.4,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true },
            },
          },
        });
      }
    }, 100);
  },
};
