/**
 * H1-AI — Chat UI
 */
Pages.chat = {
  messages: [],
  sessionId: null,
  token: null,
  currentUser: 'customer1',

  async render(el) {
    el.innerHTML = `
      <style>
        .chat-container {
          display: flex;
          flex-direction: column;
          height: calc(100vh - 180px);
          min-height: 500px;
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .chat-toolbar {
          padding: 12px 20px;
          background: #F8FAFC;
          border-bottom: 1px solid #E2E8F0;
          display: flex;
          gap: 12px;
          align-items: center;
          flex-wrap: wrap;
        }
        .chat-toolbar select, .chat-toolbar input {
          padding: 8px 12px;
          border: 1px solid #E2E8F0;
          border-radius: 8px;
          font-size: 14px;
          font-family: inherit;
        }
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          background: #F8FAFC;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .chat-message {
          max-width: 70%;
          padding: 12px 16px;
          border-radius: 16px;
          line-height: 1.5;
          font-size: 15px;
          word-wrap: break-word;
          animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .chat-message.user {
          align-self: flex-end;
          background: linear-gradient(135deg, #0EA5E9, #0284C7);
          color: white;
          border-bottom-right-radius: 4px;
        }
        .chat-message.agent {
          align-self: flex-start;
          background: white;
          color: #0F172A;
          border: 1px solid #E2E8F0;
          border-bottom-left-radius: 4px;
        }
        .chat-message.system {
          align-self: center;
          background: #FEF3C7;
          color: #92400E;
          font-size: 13px;
          padding: 8px 14px;
          border-radius: 20px;
        }
        .chat-message.emergency {
          align-self: center;
          background: #FEE2E2;
          color: #991B1B;
          border: 2px solid #EF4444;
          font-weight: 600;
        }
        .chat-message-meta {
          font-size: 11px;
          opacity: 0.7;
          margin-top: 4px;
        }
        .chat-input-bar {
          padding: 12px 16px;
          background: white;
          border-top: 1px solid #E2E8F0;
          display: flex;
          gap: 8px;
        }
        .chat-input-bar input {
          flex: 1;
          padding: 12px 16px;
          border: 1px solid #E2E8F0;
          border-radius: 24px;
          font-size: 15px;
          font-family: inherit;
          outline: none;
          transition: border 0.15s;
        }
        .chat-input-bar input:focus {
          border-color: #0EA5E9;
        }
        .chat-input-bar button {
          padding: 12px 24px;
          background: #0EA5E9;
          color: white;
          border: none;
          border-radius: 24px;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s;
        }
        .chat-input-bar button:hover:not(:disabled) {
          background: #0284C7;
          transform: translateY(-1px);
        }
        .chat-input-bar button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .typing-indicator {
          align-self: flex-start;
          padding: 12px 18px;
          background: white;
          border: 1px solid #E2E8F0;
          border-radius: 16px;
          display: flex;
          gap: 4px;
        }
        .typing-indicator span {
          width: 8px;
          height: 8px;
          background: #94A3B8;
          border-radius: 50%;
          animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
          0%, 60%, 100% { opacity: 0.3; }
          30% { opacity: 1; }
        }
        .quick-actions {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          padding: 10px 16px;
          background: white;
          border-bottom: 1px solid #F1F5F9;
        }
        .quick-action {
          padding: 6px 12px;
          background: #F1F5F9;
          border: 1px solid #E2E8F0;
          border-radius: 16px;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .quick-action:hover {
          background: #0EA5E9;
          color: white;
          border-color: #0EA5E9;
        }
      </style>

      <div class="chat-container">
        <div class="chat-toolbar">
          <strong>💬 اختبار Chat مع النظام</strong>
          <select id="chat-user" onchange="Pages.chat.switchUser(this.value)">
            <option value="customer1">👤 customer1 (عميل)</option>
            <option value="pharmacist1">💊 pharmacist1 (صيدلي)</option>
            <option value="admin">🎛️ admin (مدير)</option>
          </select>
          <span id="chat-session-info" style="color:#64748B;font-size:13px"></span>
          <button class="btn btn-ghost btn-sm" onclick="Pages.chat.clearChat()" style="margin-right:auto">🗑️ مسح</button>
        </div>

        <div class="quick-actions">
          <span class="quick-action" onclick="Pages.chat.sendQuick('السلام عليكم')">👋 السلام عليكم</span>
          <span class="quick-action" onclick="Pages.chat.sendQuick('عندي صداع')">🤕 عندي صداع</span>
          <span class="quick-action" onclick="Pages.chat.sendQuick('بكام البانادول')">💰 بكام البانادول</span>
          <span class="quick-action" onclick="Pages.chat.sendQuick('عندي ألم في الصدر')">🚨 عندي ألم في الصدر</span>
          <span class="quick-action" onclick="Pages.chat.sendQuick('عايز فيتامين سي')">💊 عايز فيتامين سي</span>
          <span class="quick-action" onclick="Pages.chat.sendQuick('اعملي تقرير المخزون')">📊 تقرير المخزون</span>
        </div>

        <div class="chat-messages" id="chat-messages">
          <div class="chat-message system">
            💡 اختر مستخدم وابدأ المحادثة
          </div>
        </div>

        <div class="chat-input-bar">
          <input
            type="text"
            id="chat-input"
            placeholder="اكتب رسالتك..."
            onkeypress="if(event.key==='Enter') Pages.chat.send()"
            autofocus>
          <button id="chat-send-btn" onclick="Pages.chat.send()">
            📤 إرسال
          </button>
        </div>
      </div>
    `;

    // تحميل أول مرة
    await this.switchUser('customer1');
  },

  async getToken(username) {
    const passwords = {
      'customer1': 'customer123',
      'pharmacist1': 'pharma123',
      'admin': 'admin123',
    };
    try {
      const res = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          password: passwords[username] || 'customer123',
        }),
      });
      if (!res.ok) return null;
      const data = await res.json();
      return data.access_token;
    } catch (e) {
      return null;
    }
  },

  async switchUser(username) {
    this.currentUser = username;
    this.token = await this.getToken(username);
    this.messages = [];
    this.sessionId = null;

    const info = document.getElementById('chat-session-info');
    if (info) {
      info.textContent = `المستخدم: ${username}`;
    }

    this.updateMessages();

    // رسالة ترحيبية
    this.addSystem(`✅ تم تسجيل الدخول كـ ${username}`);

    if (username === 'pharmacist1' || username === 'admin') {
      this.addSystem('💊 ستُوجَّه الآن كـ صيدلي — يمكنك طلب تقارير المخزون');
    }
  },

  addSystem(text) {
    this.messages.push({ type: 'system', text });
    this.updateMessages();
  },

  async send() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    this.sendMessage(text);
  },

  sendQuick(text) {
    this.sendMessage(text);
  },

  async sendMessage(text) {
    // أضف رسالة المستخدم
    this.messages.push({ type: 'user', text, timestamp: new Date() });
    this.updateMessages();

    // أظهر "يكتب..."
    this.showTyping();

    // أرسل للـ API
    try {
      const payload = { message: text };
      if (this.sessionId) payload.session_id = this.sessionId;

      const res = await fetch('/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`,
        },
        body: JSON.stringify(payload),
      });

      this.hideTyping();

      if (!res.ok) {
        const err = await res.text();
        this.messages.push({
          type: 'system',
          text: `❌ خطأ: ${res.status}`,
        });
        this.updateMessages();
        return;
      }

      const data = await res.json();
      this.sessionId = data.session_id;

      // اعرض الرد
      const handler = data.handler || 'agent';
      const isEmergency = handler === 'advisory_emergency';

      this.messages.push({
        type: isEmergency ? 'emergency' : 'agent',
        text: data.data.text,
        handler,
        confidence: data.data.confidence,
        timestamp: new Date(),
      });

      this.updateMessages();
    } catch (e) {
      this.hideTyping();
      this.messages.push({
        type: 'system',
        text: `❌ خطأ: ${e.message}`,
      });
      this.updateMessages();
    }
  },

  showTyping() {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const existing = document.getElementById('typing-indicator');
    if (existing) return;

    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  },

  hideTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  },

  updateMessages() {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    container.innerHTML = this.messages.map(m => {
      if (m.type === 'user') {
        return `<div class="chat-message user">
          ${this.escape(m.text)}
          <div class="chat-message-meta">${this.formatTime(m.timestamp)}</div>
        </div>`;
      } else if (m.type === 'agent') {
        return `<div class="chat-message agent">
          ${this.escape(m.text)}
          <div class="chat-message-meta">
            ${m.handler === 'chatbot' ? '🎭 ChatBot' :
              m.handler === 'advisory' ? '🔍 Advisory' :
              '🧠 Agent'} • ${(m.confidence * 100).toFixed(0)}%
            • ${this.formatTime(m.timestamp)}
          </div>
        </div>`;
      } else if (m.type === 'emergency') {
        return `<div class="chat-message emergency">
          ${this.escape(m.text)}
        </div>`;
      } else {
        return `<div class="chat-message system">${this.escape(m.text)}</div>`;
      }
    }).join('');

    container.scrollTop = container.scrollHeight;
  },

  clearChat() {
    this.messages = [];
    this.sessionId = null;
    this.updateMessages();
    this.addSystem('🗑️ تم مسح المحادثة');
  },

  formatTime(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });
  },

  escape(text) {
    const div = document.createElement('div');
    div.textContent = text ?? '';
    return div.innerHTML.replace(/\n/g, '<br>');
  },
};
