/**
 * H1-AI — Chat UI (Enhanced)
 * Features: Markdown, Copy, History, Rich Meta
 */
Pages.chat = {
  messages: [],
  sessionId: null,
  token: null,
  currentUser: 'admin',
  storageKey: 'h1ai_chat_history',
  maxHistory: 100,

  async render(el) {
    // تحميل marked.js
    if (!window.marked) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
      document.head.appendChild(script);
      await new Promise(r => script.onload = r);
    }

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
          max-width: 75%;
          padding: 12px 16px;
          border-radius: 16px;
          line-height: 1.6;
          font-size: 15px;
          word-wrap: break-word;
          animation: fadeIn 0.3s ease;
          position: relative;
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
        .chat-message.agent:hover .copy-btn {
          opacity: 1;
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
        .chat-message.needs-human {
          border-left: 4px solid #F59E0B;
        }

        /* Markdown styles */
        .chat-message.agent p { margin: 0 0 8px 0; }
        .chat-message.agent p:last-child { margin-bottom: 0; }
        .chat-message.agent code {
          background: #F1F5F9;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: 'Courier New', monospace;
          font-size: 13px;
          direction: ltr;
          display: inline-block;
        }
        .chat-message.agent pre {
          background: #1E293B;
          color: #E2E8F0;
          padding: 12px;
          border-radius: 8px;
          overflow-x: auto;
          direction: ltr;
          text-align: left;
          margin: 8px 0;
        }
        .chat-message.agent pre code {
          background: none;
          padding: 0;
          color: inherit;
        }
        .chat-message.agent ul, .chat-message.agent ol {
          margin: 8px 0;
          padding-right: 20px;
        }
        .chat-message.agent li { margin: 4px 0; }
        .chat-message.agent strong { color: #0EA5E9; }
        .chat-message.agent a {
          color: #0EA5E9;
          text-decoration: underline;
        }
        .chat-message.agent table {
          border-collapse: collapse;
          margin: 8px 0;
          width: 100%;
        }
        .chat-message.agent th, .chat-message.agent td {
          border: 1px solid #E2E8F0;
          padding: 6px 10px;
          text-align: right;
        }
        .chat-message.agent th {
          background: #F8FAFC;
          font-weight: 600;
        }

        .chat-message-meta {
          font-size: 11px;
          opacity: 0.7;
          margin-top: 6px;
          display: flex;
          gap: 8px;
          align-items: center;
          flex-wrap: wrap;
        }
        .meta-badge {
          background: #F1F5F9;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 10px;
        }
        .meta-badge.human { background: #FEF3C7; color: #92400E; }
        .meta-badge.product { background: #DBEAFE; color: #1E40AF; }
        .meta-badge.action { background: #E0E7FF; color: #3730A3; }

        .copy-btn {
          position: absolute;
          top: 8px;
          left: 8px;
          background: white;
          border: 1px solid #E2E8F0;
          border-radius: 6px;
          padding: 4px 8px;
          font-size: 12px;
          cursor: pointer;
          opacity: 0;
          transition: all 0.15s;
        }
        .copy-btn:hover {
          background: #0EA5E9;
          color: white;
          border-color: #0EA5E9;
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
        .chat-message.agent.streaming::after {
          content: '▊';
          animation: blink 1s infinite;
          color: #0EA5E9;
        }
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      </style>

      <div class="chat-container">
        <div class="chat-toolbar">
          <strong>💬 اختبار Chat مع النظام</strong>
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

    // استرجاع الرسائل السابقة
    this.loadHistory();

    // تحميل أول مرة
    await this.switchUser('admin');
  },

  // ──────── History Management ────────
  loadHistory() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) {
        const data = JSON.parse(saved);
        this.messages = data.messages || [];
        this.sessionId = data.sessionId || null;
        this.updateMessages();
      } else {
        this.addSystem('💡 اختر مستخدم وابدأ المحادثة');
      }
    } catch (e) {
      console.warn('Failed to load history:', e);
      this.addSystem('💡 اختر مستخدم وابدأ المحادثة');
    }
  },

  saveHistory() {
    try {
      const data = {
        messages: this.messages.slice(-this.maxHistory),
        sessionId: this.sessionId,
        timestamp: Date.now(),
      };
      localStorage.setItem(this.storageKey, JSON.stringify(data));
    } catch (e) {
      console.warn('Failed to save history:', e);
    }
  },

  // ──────── Token ────────
  async getToken(username) {
    return App.state.token;
  },

  async switchUser(username) {
    this.currentUser = username;
    this.token = await this.getToken(username);

    const info = document.getElementById('chat-session-info');
    if (info) {
      info.textContent = `المستخدم: ${App.state.user?.username || 'admin'}`;
    }

    this.updateMessages();
  },

  addSystem(text) {
    this.messages.push({ type: 'system', text, timestamp: new Date() });
    this.updateMessages();
    this.saveHistory();
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
    // Use streaming
    return this.sendMessageStream(text);
  },

  async sendMessageStream(text) {
    // 1. Add user message
    this.messages.push({ type: 'user', text, timestamp: new Date() });
    
    // 2. Add empty agent message (will be filled)
    const agentIndex = this.messages.length;
    this.messages.push({
      type: 'agent',
      text: '',
      handler: 'agent',
      confidence: 0,
      action: 'answer',
      needsHuman: false,
      productsReferenced: [],
      timestamp: new Date(),
      streaming: true,
    });
    
    this.updateMessages();
    this.saveHistory();

    try {
      const payload = { message: text };
      if (this.sessionId) payload.session_id = this.sessionId;

      const res = await fetch('/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        this.messages[agentIndex].text = `❌ خطأ: ${res.status}`;
        this.messages[agentIndex].streaming = false;
        this.updateMessages();
        this.saveHistory();
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          if (!event.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(event.slice(6));

            if (data.type === 'start') {
              this.sessionId = data.session_id;
            } else if (data.type === 'chunk') {
              this.messages[agentIndex].text += data.text;
              this.updateMessages();
            } else if (data.type === 'done') {
              Object.assign(this.messages[agentIndex], {
                handler: data.handler || 'agent',
                confidence: data.confidence || 0,
                action: data.action || 'answer',
                needsHuman: data.needs_human || false,
                productsReferenced: data.products_referenced || [],
                streaming: false,
              });
              this.updateMessages();
              this.saveHistory();
            } else if (data.type === 'error') {
              this.messages[agentIndex].text = `❌ خطأ: ${data.message}`;
              this.messages[agentIndex].streaming = false;
              this.updateMessages();
              this.saveHistory();
            }
          } catch (parseErr) {
            console.warn('Parse error:', parseErr);
          }
        }
      }
    } catch (e) {
      this.messages[agentIndex].text = `❌ خطأ: ${e.message}`;
      this.messages[agentIndex].streaming = false;
      this.updateMessages();
      this.saveHistory();
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

  renderMarkdown(text) {
    if (!window.marked) return this.escape(text);
    try {
      return marked.parse(text, { breaks: true, gfm: true });
    } catch (e) {
      return this.escape(text);
    }
  },

  renderMeta(m) {
    const parts = [];

    // Handler badge
    const handlerLabel = m.handler === 'chatbot' ? '🎭 ChatBot' :
                        m.handler === 'advisory' ? '🔍 Advisory' :
                        m.handler === 'advisory_emergency' ? '🚨 Emergency' :
                        '🧠 Agent';
    parts.push(`<span>${handlerLabel}</span>`);

    // Confidence
    if (m.confidence !== undefined && m.confidence > 0) {
      parts.push(`<span class="meta-badge">${(m.confidence * 100).toFixed(0)}%</span>`);
    }

    // Action
    if (m.action && m.action !== 'answer') {
      const actionLabel = m.action === 'redirect_to_pharmacist' ? '→ صيدلي' :
                         m.action === 'ask_clarification' ? '؟ توضيح' : m.action;
      parts.push(`<span class="meta-badge action">${actionLabel}</span>`);
    }

    // Needs human
    if (m.needsHuman) {
      parts.push(`<span class="meta-badge human">👤 يحتاج تدخل</span>`);
    }

    // Products
    if (m.productsReferenced && m.productsReferenced.length > 0) {
      const products = m.productsReferenced.slice(0, 3).join(', ');
      parts.push(`<span class="meta-badge product">📦 ${products}</span>`);
    }

    // Time
    parts.push(`<span>${this.formatTime(m.timestamp)}</span>`);

    return parts.join('');
  },

  updateMessages() {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    if (this.messages.length === 0) {
      container.innerHTML = '<div class="chat-message system">💡 ابدأ المحادثة</div>';
      return;
    }

    container.innerHTML = this.messages.map((m, idx) => {
      if (m.type === 'user') {
        return `<div class="chat-message user">
          ${this.escape(m.text)}
          <div class="chat-message-meta">${this.formatTime(m.timestamp)}</div>
        </div>`;
      } else if (m.type === 'agent') {
        const needsHumanClass = m.needsHuman ? ' needs-human' : '';
        const streamingClass = m.streaming ? ' streaming' : '';
        return `<div class="chat-message agent${needsHumanClass}${streamingClass}">
          <button class="copy-btn" onclick="Pages.chat.copyMessage(${idx})" title="نسخ">📋</button>
          <div class="markdown-content">${this.renderMarkdown(m.text)}</div>
          <div class="chat-message-meta">${this.renderMeta(m)}</div>
        </div>`;
      } else if (m.type === 'emergency') {
        return `<div class="chat-message emergency">
          ${this.renderMarkdown(m.text)}
        </div>`;
      } else {
        return `<div class="chat-message system">${this.escape(m.text)}</div>`;
      }
    }).join('');

    container.scrollTop = container.scrollHeight;
  },

  async copyMessage(idx) {
    const m = this.messages[idx];
    if (!m) return;

    try {
      await navigator.clipboard.writeText(m.text);
      App.toast('✅ تم النسخ', 'success');
    } catch (e) {
      // Fallback
      const textarea = document.createElement('textarea');
      textarea.value = m.text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      App.toast('✅ تم النسخ', 'success');
    }
  },

  clearChat() {
    if (!confirm('هل أنت متأكد من مسح المحادثة؟')) return;

    this.messages = [];
    this.sessionId = null;
    localStorage.removeItem(this.storageKey);
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
