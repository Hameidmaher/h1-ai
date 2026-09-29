/**
 * H1-AI — Live Feed (Real-time Messages)
 */
Pages.live_feed = {
  eventSource: null,
  events: [],
  maxEvents: 200,
  autoScroll: true,

  async render(el) {
    // Close existing connection
    this.disconnect();

    el.innerHTML = `
      <style>
        .lf-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px}
        .lf-header h1{margin:0;font-size:24px}
        .lf-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
        .lf-status{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:#F1F5F9;border-radius:20px;font-size:13px;font-weight:600}
        .lf-status-dot{width:8px;height:8px;border-radius:50%;background:#94A3B8}
        .lf-status.connected{background:#DCFCE7;color:#166534}
        .lf-status.connected .lf-status-dot{background:#10B981;animation:pulse 1.5s infinite}
        .lf-status.disconnected{background:#FEE2E2;color:#991B1B}
        .lf-status.disconnected .lf-status-dot{background:#EF4444}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
        .lf-btn{padding:8px 14px;border-radius:8px;border:none;font-family:inherit;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.15s}
        .lf-btn-primary{background:#0EA5E9;color:white}
        .lf-btn-primary:hover{background:#0284C7}
        .lf-btn-ghost{background:transparent;color:#64748B;border:1px solid #E2E8F0}
        .lf-btn-ghost:hover{background:#F8FAFC}
        .lf-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:16px}
        .lf-stat{background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0;text-align:center}
        .lf-stat-value{font-size:24px;font-weight:700;color:#0EA5E9}
        .lf-stat-value.green{color:#10B981}
        .lf-stat-value.red{color:#EF4444}
        .lf-stat-label{font-size:12px;color:#64748B;margin-top:4px}
        .lf-feed{background:white;border-radius:12px;border:1px solid #E2E8F0;overflow:hidden}
        .lf-feed-header{padding:12px 20px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;display:flex;justify-content:space-between;align-items:center;font-size:14px;font-weight:600}
        .lf-feed-body{max-height:calc(100vh - 400px);min-height:400px;overflow-y:auto;padding:16px;background:#F8FAFC}
        .lf-event{background:white;border-radius:10px;padding:14px 16px;margin-bottom:12px;border-left:4px solid #0EA5E9;box-shadow:0 1px 3px rgba(0,0,0,0.05);animation:slideIn 0.3s ease}
        @keyframes slideIn{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}
        .lf-event.emergency{border-left-color:#EF4444;background:#FEF2F2}
        .lf-event.needs-human{border-left-color:#F59E0B;background:#FFFBEB}
        .lf-event.test{border-left-color:#10B981;background:#F0FDF4}
        .lf-event-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:12px}
        .lf-from{font-weight:700;color:#0F172A}
        .lf-time{color:#94A3B8}
        .lf-message{background:#F1F5F9;padding:10px 12px;border-radius:8px;margin:8px 0;font-size:14px;line-height:1.5;direction:rtl;word-break:break-word}
        .lf-message.user{background:#EFF6FF;border-right:3px solid #0EA5E9}
        .lf-message.ai{background:#F0FDF4;border-right:3px solid #10B981}
        .lf-badge{display:inline-block;padding:3px 8px;border-radius:6px;font-size:10px;font-weight:600;margin-left:6px}
        .lf-badge.emergency{background:#FEE2E2;color:#991B1B}
        .lf-badge.human{background:#FEF3C7;color:#92400E}
        .lf-badge.handler{background:#E0E7FF;color:#3730A3}
        .lf-empty{text-align:center;padding:60px 20px;color:#94A3B8}
        .lf-empty-icon{font-size:60px;margin-bottom:12px;opacity:0.5}
      </style>

      <div class="lf-header">
        <h1>📡 البث الحي للرسائل</h1>
        <div class="lf-controls">
          <span class="lf-status" id="lf-status">
            <span class="lf-status-dot"></span>
            <span id="lf-status-text">جاري الاتصال...</span>
          </span>
          <button class="lf-btn lf-btn-ghost" onclick="Pages.live_feed.toggleAutoScroll()">
            <span id="lf-autoscroll-label">⬇️ تثبيت الأسفل</span>
          </button>
          <button class="lf-btn lf-btn-ghost" onclick="Pages.live_feed.clearFeed()">
            🗑️ مسح
          </button>
          <button class="lf-btn lf-btn-primary" onclick="Pages.live_feed.testEvent()">
            🔔 اختبار
          </button>
        </div>
      </div>

      <div class="lf-stats" id="lf-stats">
        <div class="lf-stat">
          <div class="lf-stat-value" id="lf-total">0</div>
          <div class="lf-stat-label">إجمالي الأحداث</div>
        </div>
        <div class="lf-stat">
          <div class="lf-stat-value green" id="lf-whatsapp">0</div>
          <div class="lf-stat-label">رسائل WhatsApp</div>
        </div>
        <div class="lf-stat">
          <div class="lf-stat-value" id="lf-clients">0</div>
          <div class="lf-stat-label">عملاء متصلين</div>
        </div>
      </div>

      <div class="lf-feed">
        <div class="lf-feed-header">
          <span>📥 آخر الرسائل</span>
          <span style="color:#94A3B8;font-weight:normal" id="lf-count">0 رسالة</span>
        </div>
        <div class="lf-feed-body" id="lf-feed-body">
          <div class="lf-empty" id="lf-empty">
            <div class="lf-empty-icon">📡</div>
            <div>في انتظار الرسائل...</div>
            <div style="font-size:13px;margin-top:8px">الرسائل الجديدة هتظهر هنا فوراً</div>
          </div>
        </div>
      </div>
    `;

    // Start connection
    this.connect();
  },

  connect() {
    const el = document.getElementById('lf-feed-body');
    if (!el) return;

    try {
      // Get token from App state
      const token = App.state.token;
      if (!token) {
        this.setStatus('disconnected', 'غير متصل — سجّل الدخول');
        return;
      }

      // SSE doesn't support headers, so we use query param
      const url = `/v1/admin/live-feed`;
      
      // Use fetch with Authorization (SSE via fetch)
      this.connectViaFetch(url, token);
      
    } catch (e) {
      this.setStatus('disconnected', `خطأ: ${e.message}`);
    }
  },

  async connectViaFetch(url, token) {
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
        },
      });

      if (!response.ok) {
        this.setStatus('disconnected', `HTTP ${response.status}`);
        return;
      }

      this.setStatus('connected', 'متصل — في انتظار الرسائل');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          this.setStatus('disconnected', 'انتهى الاتصال');
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            this.handleEvent(event);
          } catch (e) {
            console.warn('Parse error:', e);
          }
        }
      }
    } catch (e) {
      console.error('SSE error:', e);
      this.setStatus('disconnected', 'فقد الاتصال');
      
      // Retry after 5 seconds
      setTimeout(() => this.connect(), 5000);
    }
  },

  handleEvent(event) {
    if (event.type === 'connected') {
      document.getElementById('lf-clients').textContent = event.clients || 0;
      return;
    }

    // Add to events
    this.events.unshift(event);
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(0, this.maxEvents);
    }

    this.updateStats();
    this.renderEvents();
  },

  updateStats() {
    const total = this.events.length;
    const whatsapp = this.events.filter(e => e.type === 'whatsapp_message').length;

    document.getElementById('lf-total').textContent = total;
    document.getElementById('lf-whatsapp').textContent = whatsapp;
    document.getElementById('lf-count').textContent = `${total} رسالة`;
  },

  renderEvents() {
    const body = document.getElementById('lf-feed-body');
    if (!body) return;

    if (!this.events.length) {
      body.innerHTML = `
        <div class="lf-empty">
          <div class="lf-empty-icon">📡</div>
          <div>في انتظار الرسائل...</div>
        </div>
      `;
      return;
    }

    body.innerHTML = this.events.map(e => this.renderEvent(e)).join('');
    
    if (this.autoScroll) {
      body.scrollTop = 0; // Since we unshift, scroll to top
    }
  },

  renderEvent(e) {
    if (e.type === 'test') {
      return `
        <div class="lf-event test">
          <div class="lf-event-header">
            <span class="lf-from">🧪 ${e.from || 'system'}</span>
            <span class="lf-time">${this.formatTime(e.timestamp)}</span>
          </div>
          <div class="lf-message">${this.escape(e.message)}</div>
        </div>
      `;
    }

    if (e.type === 'whatsapp_message') {
      const isEmergency = e.action === 'redirect_to_pharmacist';
      const needsHuman = e.needs_human;
      const cls = isEmergency ? 'emergency' : (needsHuman ? 'needs-human' : '');
      
      return `
        <div class="lf-event ${cls}">
          <div class="lf-event-header">
            <span class="lf-from">
              📱 ${this.escape(e.phone || 'unknown')}
              ${isEmergency ? '<span class="lf-badge emergency">🚨 طوارئ</span>' : ''}
              ${needsHuman ? '<span class="lf-badge human">👤 يحتاج تدخل</span>' : ''}
              ${e.handler ? `<span class="lf-badge handler">${e.handler}</span>` : ''}
            </span>
            <span class="lf-time">${this.formatTime(e.timestamp)}</span>
          </div>
          
          <div class="lf-message user">
            <strong>👤 العميل:</strong><br>
            ${this.escape(e.message)}
          </div>
          
          <div class="lf-message ai">
            <strong>🤖 الرد:</strong><br>
            ${this.escape(e.response)}
          </div>
        </div>
      `;
    }

    return '';
  },

  setStatus(status, text) {
    const el = document.getElementById('lf-status');
    const textEl = document.getElementById('lf-status-text');
    if (el) el.className = `lf-status ${status}`;
    if (textEl) textEl.textContent = text;
  },

  formatTime(ts) {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return ts;
    }
  },

  escape(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
  },

  toggleAutoScroll() {
    this.autoScroll = !this.autoScroll;
    const label = document.getElementById('lf-autoscroll-label');
    if (label) {
      label.textContent = this.autoScroll ? '⬇️ تثبيت الأسفل' : '⏸️ إيقاف التثبيت';
    }
    App.toast(this.autoScroll ? '✅ تثبيت الأسفل مفعّل' : '⏸️ التثبيت موقوف', 'success');
  },

  clearFeed() {
    if (!confirm('مسح كل الأحداث من العرض؟')) return;
    this.events = [];
    this.renderEvents();
    this.updateStats();
    App.toast('✅ تم المسح', 'success');
  },

  async testEvent() {
    try {
      await App.api('/v1/admin/live-feed/test', { method: 'POST' });
      App.toast('🔔 تم إرسال حدث اختباري', 'success');
    } catch (e) {
      App.toast(`❌ ${e.message}`, 'error');
    }
  },

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.events = [];
  },
};
