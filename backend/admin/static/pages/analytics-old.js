/**
 * Analytics Dashboard Page
 */
(function () {
    'use strict';

    const API = '';

    window.Pages = window.Pages || {};
    window.Pages.analytics = {
        render: async (container) => {
            container.innerHTML = `
                <style>
                    .an-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); margin-bottom: 20px; }
                    .an-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
                    .an-value { font-size: 28px; font-weight: 800; color: #0ea5e9; }
                    .an-label { font-size: 12px; color: #64748b; margin-top: 4px; }
                    .an-chart { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
                    .an-chart h3 { font-size: 15px; margin-bottom: 12px; color: #0f172a; }
                    .an-list { padding: 8px 0; }
                    .an-item { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
                    .an-item:last-child { border-bottom: none; }
                    .an-badge { background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
                    @media (max-width: 600px) {
                        .an-grid { grid-template-columns: repeat(2, 1fr); }
                    }
                </style>

                <h1 style="font-size:20px;margin-bottom:8px">📊 التحليلات</h1>
                <p style="color:#64748b;font-size:13px;margin-bottom:16px">نظرة عامة على أداء المنصة</p>

                <div class="an-grid" id="an-stats">
                    <div class="an-card"><div class="an-value">—</div><div class="an-label">جاري التحميل...</div></div>
                </div>

                <div class="an-chart">
                    <h3>📈 الرسائل (آخر 7 أيام)</h3>
                    <canvas id="an-chart" height="60"></canvas>
                </div>

                <div class="an-chart">
                    <h3>🛠️ الأدوات الأكثر استخدامًا</h3>
                    <div class="an-list" id="an-tools">
                        <div style="text-align:center;color:#64748b;padding:20px">جاري التحميل...</div>
                    </div>
                </div>

                <div class="an-chart">
                    <h3>💬 آخر الجلسات</h3>
                    <div class="an-list" id="an-sessions">
                        <div style="text-align:center;color:#64748b;padding:20px">جاري التحميل...</div>
                    </div>
                </div>
            `;

            await loadStats();
            await loadTimeseries();
            await loadTools();
            await loadSessions();
        }
    };

    function getToken() {
        return localStorage.getItem('h1ai_token') || '';
    }

    async function fetchAPI(url) {
        const res = await fetch(API + url, {
            headers: { 'Authorization': 'Bearer ' + getToken() },
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    }

    async function loadStats() {
        try {
            const d = await fetchAPI('/api/analytics/overview');
            const el = document.getElementById('an-stats');
            el.innerHTML = `
                <div class="an-card"><div class="an-value">${d.total_sessions}</div><div class="an-label">إجمالي الجلسات</div></div>
                <div class="an-card"><div class="an-value">${d.sessions_24h}</div><div class="an-label">جلسات اليوم</div></div>
                <div class="an-card"><div class="an-value">${d.total_messages}</div><div class="an-label">إجمالي الرسائل</div></div>
                <div class="an-card"><div class="an-value">${d.messages_24h}</div><div class="an-label">رسائل اليوم</div></div>
                <div class="an-card"><div class="an-value">${d.total_drugs}</div><div class="an-label">الأدوية</div></div>
                <div class="an-card"><div class="an-value">${d.total_orders}</div><div class="an-label">الطلبات</div></div>
            `;
        } catch (e) {
            console.error(e);
        }
    }

    async function loadTimeseries() {
        try {
            const data = await fetchAPI('/api/analytics/messages/timeseries?days=7');
            const canvas = document.getElementById('an-chart');
            if (!canvas) return;

            // Simple bar chart without external lib
            const max = Math.max(...data.map(d => d.count), 1);
            const bars = data.map(d => {
                const h = (d.count / max) * 100;
                const day = new Date(d.date).toLocaleDateString('ar-EG', { weekday: 'short' });
                return `
                    <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
                        <div style="font-size:10px;color:#64748b">${d.count}</div>
                        <div style="width:100%;height:100px;background:#f1f5f9;border-radius:6px;display:flex;align-items:flex-end">
                            <div style="width:100%;height:${h}%;background:linear-gradient(to top,#0ea5e9,#38bdf8);border-radius:6px"></div>
                        </div>
                        <div style="font-size:10px;color:#475569">${day}</div>
                    </div>
                `;
            }).join('');

            canvas.parentElement.innerHTML = `
                <h3 style="font-size:15px;margin-bottom:12px;color:#0f172a">📈 الرسائل (آخر 7 أيام)</h3>
                <div style="display:flex;gap:6px;align-items:flex-end;padding:12px 0">${bars}</div>
            `;
        } catch (e) {
            console.error(e);
        }
    }

    async function loadTools() {
        try {
            const data = await fetchAPI('/api/analytics/intents/top?limit=10');
            const el = document.getElementById('an-tools');
            if (!data.length) {
                el.innerHTML = '<div style="text-align:center;color:#64748b;padding:20px">مفيش بيانات لسه</div>';
                return;
            }
            el.innerHTML = data.map(t => `
                <div class="an-item">
                    <span><strong>${t.tool}</strong></span>
                    <span class="an-badge">${t.count}</span>
                </div>
            `).join('');
        } catch (e) {
            console.error(e);
        }
    }

    async function loadSessions() {
        try {
            const data = await fetchAPI('/api/analytics/sessions/recent?limit=10');
            const el = document.getElementById('an-sessions');
            if (!data.length) {
                el.innerHTML = '<div style="text-align:center;color:#64748b;padding:20px">مفيش جلسات لسه</div>';
                return;
            }
            el.innerHTML = data.map(s => `
                <div class="an-item">
                    <span>
                        <strong>${s.channel}</strong> • ${s.user}
                    </span>
                    <span class="an-badge">${s.messages} رسالة</span>
                </div>
            `).join('');
        } catch (e) {
            console.error(e);
        }
    }
})();
