/**
 * H1-AI — Dashboard Charts (Chart.js)
 */

const Charts = {
  instances: {},
  
  async renderDashboardCharts(stats) {
    // Wait for Chart.js to load
    if (!window.Chart) {
      await this.loadChartJS();
    }
    
    const container = document.getElementById('dashboard-charts');
    if (!container) return;
    
    container.innerHTML = `
      <div class="chart-grid">
        <div class="chart-card">
          <h3>📊 التقارير حسب الحالة</h3>
          <canvas id="chart-reports-status"></canvas>
        </div>
        <div class="chart-card">
          <h3>🎯 التقارير حسب الأولوية</h3>
          <canvas id="chart-reports-priority"></canvas>
        </div>
        <div class="chart-card">
          <h3>📥 الرسائل (آخر 7 أيام)</h3>
          <canvas id="chart-messages-trend"></canvas>
        </div>
        <div class="chart-card">
          <h3>👥 حالة الفريق</h3>
          <canvas id="chart-team-status"></canvas>
        </div>
      </div>
    `;
    
    // Add styles
    if (!document.getElementById('chart-styles')) {
      const style = document.createElement('style');
      style.id = 'chart-styles';
      style.textContent = `
        .chart-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin: 20px 0;
        }
        .chart-card {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.06);
          border: 1px solid #E2E8F0;
        }
        .chart-card h3 {
          font-size: 16px;
          margin-bottom: 16px;
          color: #0F172A;
        }
        .chart-card canvas {
          max-height: 250px;
        }
      `;
      document.head.appendChild(style);
    }
    
    // Render each chart
    this.renderReportsStatus(stats);
    this.renderReportsPriority(stats);
    this.renderMessagesTrend(stats);
    this.renderTeamStatus(stats);
  },
  
  loadChartJS() {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
      script.onload = resolve;
      document.head.appendChild(script);
    });
  },
  
  destroy(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },
  
  renderReportsStatus(stats) {
    const id = 'chart-reports-status';
    this.destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    
    const byStatus = stats.reports?.by_status || {
      'pending': 42,
      'assigned': 28,
      'resolved': 95,
      'escalated': 5,
    };
    
    this.instances[id] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(byStatus).map(s => ({
          'pending': 'معلّق',
          'assigned': 'موزّع',
          'resolved': 'محلول',
          'escalated': 'مُصعّد',
        }[s] || s)),
        datasets: [{
          data: Object.values(byStatus),
          backgroundColor: ['#F59E0B', '#0EA5E9', '#10B981', '#EF4444'],
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { font: { family: 'Cairo' }, padding: 12 },
          },
        },
      },
    });
  },
  
  renderReportsPriority(stats) {
    const id = 'chart-reports-priority';
    this.destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    
    const byPriority = stats.reports?.by_priority || {
      'urgent': 8,
      'high': 25,
      'normal': 95,
      'low': 42,
    };
    
    this.instances[id] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['🚨 عاجل', 'عالي', 'عادي', 'منخفض'],
        datasets: [{
          label: 'عدد التقارير',
          data: [
            byPriority.urgent || 0,
            byPriority.high || 0,
            byPriority.normal || 0,
            byPriority.low || 0,
          ],
          backgroundColor: ['#EF4444', '#F97316', '#0EA5E9', '#10B981'],
          borderRadius: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { font: { family: 'Cairo' } } },
          x: { ticks: { font: { family: 'Cairo' } } },
        },
      },
    });
  },
  
  renderMessagesTrend(stats) {
    const id = 'chart-messages-trend';
    this.destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    
    // Sample data (can be replaced with real data from API)
    const days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'];
    const messages = stats.messages_24h?.trend || [120, 145, 98, 167, 203, 178, 145];
    
    this.instances[id] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: days,
        datasets: [{
          label: 'الرسائل',
          data: messages,
          borderColor: '#0EA5E9',
          backgroundColor: 'rgba(14, 165, 233, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointRadius: 5,
          pointBackgroundColor: '#0EA5E9',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { font: { family: 'Cairo' } } },
          x: { ticks: { font: { family: 'Cairo' } } },
        },
      },
    });
  },
  
  renderTeamStatus(stats) {
    const id = 'chart-team-status';
    this.destroy(id);
    const ctx = document.getElementById(id);
    if (!ctx) return;
    
    const team = stats.team || { available: 6, busy: 3, offline: 1 };
    
    this.instances[id] = new Chart(ctx, {
      type: 'polarArea',
      data: {
        labels: ['متاح', 'مشغول', 'غير متصل'],
        datasets: [{
          data: [
            team.available || 6,
            team.busy || 3,
            team.offline || 1,
          ],
          backgroundColor: [
            'rgba(16, 185, 129, 0.7)',
            'rgba(249, 115, 22, 0.7)',
            'rgba(148, 163, 184, 0.7)',
          ],
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { font: { family: 'Cairo' }, padding: 12 },
          },
        },
      },
    });
  },
};
