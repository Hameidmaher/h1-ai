/**
 * Tunnel Management Page — Cloudflare Tunnel Control
 */
(function () {
    'use strict';
    window.Pages = window.Pages || {};

    let statusInterval = null;

    window.Pages.tunnel = {
        render: async (container) => {
            container.innerHTML = `
                <style>
                    .tunnel-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
                    .tunnel-status { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
                    .tunnel-dot { width: 12px; height: 12px; border-radius: 50%; }
                    .tunnel-dot.running { background: #10b981; animation: pulse 2s infinite; }
                    .tunnel-dot.stopped { background: #ef4444; }
                    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
                    .tunnel-url-box { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 14px; margin: 16px 0; word-break: break-all; direction: ltr; text-align: left; font-family: monospace; font-size: 13px; color: #0369a1; }
                    .tunnel-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
                    .tunnel-info { font-size: 13px; color: #64748b; margin: 8px 0; }
                </style>

                <h1 style="font-size:20px;margin-bottom:8px">🔗 النفق العام (Tunnel)</h1>
                <p style="color:#64748b;font-size:13px;margin-bottom:16px">شارك مشروعك مع الأصدقاء عبر رابط عام</p>

                <div class="tunnel-card" id="tunnel-main">
                    <div class="tunnel-status">
                        <div class="tunnel-dot stopped" id="tunnel-dot"></div>
                        <div>
                            <strong id="tunnel-status-text">جاري التحميل...</strong>
                            <div class="tunnel-info" id="tunnel-info">الرجاء الانتظار</div>
                        </div>
                    </div>
                    <div class="tunnel-actions">
                        <button class="btn btn-primary" id="tunnel-start" onclick="Pages.tunnel.start()">▶️ تشغيل النفق</button>
                        <button class="btn" id="tunnel-stop" onclick="Pages.tunnel.stop()" style="background:#ef4444;color:#fff">⏹️ إيقاف النفق</button>
                        <button class="btn" id="tunnel-restart" onclick="Pages.tunnel.restart()">🔄 إعادة تشغيل</button>
                    </div>
                    <div id="tunnel-url-section" style="display:none">
                        <h3 style="font-size:14px;margin:16px 0 8px">🔗 الرابط العام:</h3>
                        <div class="tunnel-url-box" id="tunnel-url"></div>
                        <div style="display:flex;gap:8px;flex-wrap:wrap">
                            <button class="btn" onclick="Pages.tunnel.copyUrl()" style="background:#10b981;color:#fff">📋 نسخ الرابط</button>
                            <button class="btn" onclick="Pages.tunnel.openUrl()">🌐 فتح في المتصفح</button>
                        </div>
                    </div>
                </div>

                <div class="tunnel-card">
                    <h3 style="font-size:14px;margin-bottom:8px">ℹ️ كيف يعمل هذا؟</h3>
                    <ul style="font-size:13px;color:#475569;padding-right:20px;line-height:2">
                        <li>يتم تشغيل حاوية <code>cloudflared</code> لإنشاء نفق آمن إلى الإنترنت.</li>
                        <li>الرابط الذي يظهر أعلاه هو رابط دائم لا يتغير عند إعادة التشغيل.</li>
                        <li>يمكنك مشاركة هذا الرابط مع أي شخص في العالم.</li>
                        <li>النفق آمن - لا يتم فتح أي منافذ على جهازك.</li>
                    </ul>
                </div>
            `;

            await Pages.tunnel.refresh();
            // تحديث تلقائي كل 10 ثوانٍ
            if (statusInterval) clearInterval(statusInterval);
            statusInterval = setInterval(() => Pages.tunnel.refresh(), 10000);
        },

        refresh: async () => {
            try {
                const res = await fetch('/api/tunnel/status', {
                    headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('h1ai_token') || '') },
                });
                const data = await res.json();

                const dot = document.getElementById('tunnel-dot');
                const statusText = document.getElementById('tunnel-status-text');
                const info = document.getElementById('tunnel-info');
                const urlSection = document.getElementById('tunnel-url-section');
                const urlEl = document.getElementById('tunnel-url');

                if (data.running) {
                    dot.className = 'tunnel-dot running';
                    statusText.textContent = '✅ النفق يعمل';
                    info.textContent = 'يمكن للأصدقاء الوصول للمشروع عبر الرابط أدناه';
                    if (data.url) {
                        urlSection.style.display = 'block';
                        urlEl.textContent = data.url;
                    } else {
                        urlSection.style.display = 'none';
                    }
                } else {
                    dot.className = 'tunnel-dot stopped';
                    statusText.textContent = '⏹️ النفق متوقف';
                    info.textContent = 'قم بتشغيل النفق للسماح بالوصول العام';
                    urlSection.style.display = 'none';
                }
            } catch (e) {
                console.error('Tunnel status error:', e);
            }
        },

        start: async () => {
            try {
                await fetch('/api/tunnel/start', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('h1ai_token') || '') },
                });
                setTimeout(() => Pages.tunnel.refresh(), 3000);
            } catch (e) {
                alert('فشل تشغيل النفق');
            }
        },

        stop: async () => {
            if (!confirm('هل أنت متأكد من إيقاف النفق؟ لن يتمكن الأصدقاء من الوصول.')) return;
            try {
                await fetch('/api/tunnel/stop', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('h1ai_token') || '') },
                });
                setTimeout(() => Pages.tunnel.refresh(), 2000);
            } catch (e) {
                alert('فشل إيقاف النفق');
            }
        },

        restart: async () => {
            if (!confirm('إعادة تشغيل النفق؟')) return;
            try {
                await fetch('/api/tunnel/restart', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('h1ai_token') || '') },
                });
                setTimeout(() => Pages.tunnel.refresh(), 5000);
            } catch (e) {
                alert('فشل إعادة التشغيل');
            }
        },

        copyUrl: () => {
            const url = document.getElementById('tunnel-url').textContent;
            navigator.clipboard.writeText(url).then(() => {
                alert('✅ تم نسخ الرابط!');
            });
        },

        openUrl: () => {
            const url = document.getElementById('tunnel-url').textContent;
            window.open(url, '_blank');
        },
    };
})();
