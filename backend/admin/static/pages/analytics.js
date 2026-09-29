/**
 * Advanced Analytics — Chart.js
 */
(function () {
    'use strict';
    window.Pages = window.Pages || {};

    window.Pages.analytics = {
        render: async (container) => {
            container.innerHTML = `
                <style>
                    .ap-grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); margin-bottom: 16px; }
                    .ap-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; }
                    .ap-kpi { display: flex; justify-content: space-between; align-items: center; }
                    .ap-value { font-size: 32px; font-weight: 800; color: #0ea5e9; line-height: 1; }
                    .ap-label { font-size: 12px; color: #64748b; margin-top: 6px; }
                    .ap-icon { font-size: 28px; }
                    .ap-chart { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 14px; }
                    .ap-chart h3 { font-size: 15px; margin-bottom: 14px; color: #0f172a; font-weight: 700; }
                    .ap-chart canvas { max-height: 300px; }
                    .ap-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
                    @media (max-width: 600px) {
                        .ap-grid { grid-template-columns: 1fr; }
                        .ap-value { font-size: 26px; }
                    }
                </style>

                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:16px">
                    <div>
                        <h1 style="font-size:20px;margin:0 0 4px">📊 التحليلات المتقدمة</h1>
                        <p style="color:#64748b;font-size:13px;margin:0">رؤية شاملة لأداء المنصة</p>
                    </div>
                    <div class="ap-actions">
                        <button class="btn btn-primary" onclick="Pages.analytics.download('pdf')">📄 PDF</button>
                        <button class="btn" onclick="Pages.analytics.download('csv')" style="background:#10b981;color:#fff">📊 CSV</button>
                        <button class="btn" onclick="Pages.analytics.refresh()">🔄 تحديث</button>
                    </div>
                </div>

                <div class="ap-grid" id="ap-kpis">
                    <div class="ap-card"><div class="ap-kpi"><div><div class="ap-value">—</div><div class="ap-label">تحميل...</div></div></div></div>
                </div>

                <div class="ap-chart"><h3>📈 الرسائل (آخر 14 يوم)</h3><canvas id="ap-timeseries"></canvas></div>

                <div class="ap-grid">
                    <div class="ap-chart"><h3>🛠️ الأدوات الأكثر استخدامًا</h3><canvas id="ap-tools"></canvas></div>
                    <div class="ap-chart"><h3>📊 القنوات</h3><canvas id="ap-channels"></canvas></div>
                </div>

                <div class="ap-chart"><h3>💬 آخر الجلسات</h3><div id="ap-sessions" style="padding:8px 0"></div></div>
            `;

            // حمّل Chart.js إذا مش موجود
            if (typeof Chart === 'undefined') {
                const s = document.createElement('script');
                s.src = '/admin/static/lib/chart.min.js';
                s.onload = () => Pages.analytics.refresh();
                document.head.appendChild(s);
            } else {
                Pages.analytics.refresh();
            }
        },

        refresh: async () => {
            await Promise.all([
                loadKPIs(),
                loadTimeseries(),
                loadTools(),
                loadChannels(),
                loadSessions(),
            ]);
        },

        download: async (format) => {
            const data = await fetchAPI('/api/analytics/overview');
            if (format === 'csv') {
                const csv = 'Metric,Value\n' + Object.entries(data).map(([k, v]) => `${k},${v}`).join('\n');
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `h1ai-analytics-${new Date().toISOString().slice(0, 10)}.csv`;
                a.click();
            } else {
                window.print();
            }
        },
    };

    function getToken() { return localStorage.getItem('h1ai_token') || ''; }

    async function fetchAPI(url) {
        const res = await fetch(url, { headers: { 'Authorization': 'Bearer ' + getToken() } });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    }

    async function loadKPIs() {
        try {
            const d = await fetchAPI('/api/analytics/overview');
            document.getElementById('ap-kpis').innerHTML = `
                <div class="ap-card"><div class="ap-kpi"><div><div class="ap-value">${d.total_sessions}</div><div class="ap-label">إجمالي الجلسات</div></div><div class="ap-icon">💬</div></div></div>
                <div class="ap-card"><div class="ap-kpi"><div><div class="ap-value">${d.total_messages}</div><div class="ap-label">إجمالي الرسائل</div></div><div class="ap-icon">✉️</div></div></div>
                <div class="ap-card"><div class="ap-kpi"><div><div class="ap-value">${d.messages_24h}</div><div class="ap-label">رسائل 24 ساعة</div></div><div class="ap-icon">⚡</div></div></div>
                <div class="ap-card"><div class="ap-kpi"><div><div class="ap-value">${d.total_drugs}</div><div class="ap-label">الأدوية</div></div><div class="ap-icon">💊</div></div></div>
                <div class="ap-card"><div class="ap-kpi"><div><div class="ap-value">${d.total_customers}</div><div class="ap-label">العملاء</div></div><div class="ap-icon">👥</div></div></div>
                <div class="ap-card"><div class="ap-kpi"><div><div class="ap-value">${d.total_orders}</div><div class="ap-label">الطلبات</div></div><div class="ap-icon">🛒</div></div></div>
            `;
        } catch (e) { console.error(e); }
    }

    async function loadTimeseries() {
        try {
            const data = await fetchAPI('/api/analytics/messages/timeseries?days=14');
            const ctx = document.getElementById('ap-timeseries');
            if (!ctx || typeof Chart === 'undefined') return;
            if (window.__ap_ts_chart) window.__ap_ts_chart.destroy();

            window.__ap_ts_chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => d.date.substring(5)),
                    datasets: [{
                        label: 'الرسائل',
                        data: data.map(d => d.count),
                        borderColor: '#0ea5e9',
                        backgroundColor: 'rgba(14,165,233,0.1)',
                        tension: 0.4,
                        fill: true,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { font: { size: 11 } } },
                        x: { ticks: { font: { size: 11 } } },
                    },
                },
            });
        } catch (e) { console.error(e); }
    }

    async function loadTools() {
        try {
            const data = await fetchAPI('/api/analytics/intents/top?limit=6');
            const ctx = document.getElementById('ap-tools');
            if (!ctx || typeof Chart === 'undefined') return;
            if (window.__ap_tools_chart) window.__ap_tools_chart.destroy();

            window.__ap_tools_chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.map(d => d.tool),
                    datasets: [{
                        data: data.map(d => d.count),
                        backgroundColor: ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { font: { size: 11 } } },
                    },
                },
            });
        } catch (e) { console.error(e); }
    }

    async function loadChannels() {
        try {
            const sessions = await fetchAPI('/api/analytics/sessions/recent?limit=100');
            const counts = {};
            sessions.forEach(s => { counts[s.channel] = (counts[s.channel] || 0) + 1; });

            const ctx = document.getElementById('ap-channels');
            if (!ctx || typeof Chart === 'undefined') return;
            if (window.__ap_ch_chart) window.__ap_ch_chart.destroy();

            window.__ap_ch_chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(counts),
                    datasets: [{
                        label: 'الجلسات',
                        data: Object.values(counts),
                        backgroundColor: '#0ea5e9',
                        borderRadius: 8,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } },
                },
            });
        } catch (e) { console.error(e); }
    }

    async function loadSessions() {
        try {
            const data = await fetchAPI('/api/analytics/sessions/recent?limit=10');
            const el = document.getElementById('ap-sessions');
            if (!data.length) { el.innerHTML = '<p style="color:#64748b;text-align:center;padding:16px">مفيش بيانات</p>'; return; }
            el.innerHTML = data.map(s => `
                <div style="padding:10px 12px;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;font-size:13px">
                    <span><strong>${s.channel}</strong> • ${s.user}</span>
                    <span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">${s.messages} رسالة</span>
                </div>
            `).join('');
        } catch (e) { console.error(e); }
    }
})();
