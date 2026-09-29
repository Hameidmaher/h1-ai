/**
 * H1-AI — Customer Chat
 */

const Chat = {
  messages: [],
  sessionId: null,
  token: null,
  isStreaming: false,

  init() {
    this.loadTheme();
    this.loadHistory();
    this.autoResize();
    this.bindEvents();

    // Auto-login as guest (customer)
    this.loginAsGuest();
  },

  async loginAsGuest() {
    // For demo: use customer1 account
    // In production: use OTP via WhatsApp or phone number
    try {
      const res = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'customer1',
          password: 'customer123',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        this.token = data.access_token;
        console.log('✅ Logged in as guest');
      } else {
        console.warn('Guest login failed — using public mode');
      }
    } catch (e) {
      console.warn('Guest login error:', e);
    }
  },

  bindEvents() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 120) + 'px';
      sendBtn.disabled = !input.value.trim();
    });

    // Enter to send (Shift+Enter for new line)
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    sendBtn.disabled = true;
  },

  autoResize() {
    const input = document.getElementById('chat-input');
    if (input) input.focus();
  },

  async sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || this.isStreaming) return;

    input.value = '';
    input.style.height = 'auto';
    document.getElementById('send-btn').disabled = true;

    // Add user message
    this.addMessage('user', text);

    // Show typing
    this.showTyping();

    // Send to API
    try {
      const payload = { message: text };
      if (this.sessionId) payload.session_id = this.sessionId;

      const headers = { 'Content-Type': 'application/json' };
      if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

      const res = await fetch('/v1/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      this.hideTyping();

      if (!res.ok) {
        this.addMessage('system', `❌ خطأ: ${res.status}`);
        return;
      }

      const data = await res.json();
      this.sessionId = data.session_id;

      const handler = data.handler || 'agent';
      const isEmergency = handler === 'advisory_emergency';

      this.addMessage(isEmergency ? 'emergency' : 'agent', data.data.text);
    } catch (e) {
      this.hideTyping();
      this.addMessage('system', `❌ خطأ: ${e.message}`);
    }
  },

  sendQuick(text) {
    const input = document.getElementById('chat-input');
    if (input) input.value = text;
    this.sendMessage();
  },

  addMessage(type, text) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-message ${type}`;
    div.innerHTML = type === 'user' ? this.escape(text) : this.renderMarkdown(text);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    this.messages.push({ type, text, timestamp: Date.now() });
    this.saveHistory();
  },

  showTyping() {
    const container = document.getElementById('chat-messages');
    if (document.getElementById('typing-indicator')) return;

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
    if (!text) return '';
    if (window.marked) {
      try {
        return marked.parse(text, { breaks: true, gfm: true });
      } catch (e) {}
    }
    return this.escape(text).replace(/\n/g, '<br>');
  },

  escape(text) {
    const div = document.createElement('div');
    div.textContent = text ?? '';
    return div.innerHTML;
  },

  clearChat() {
    if (!confirm('هل أنت متأكد من مسح المحادثة؟')) return;
    document.getElementById('chat-messages').innerHTML = '';
    this.messages = [];
    this.sessionId = null;
    localStorage.removeItem('h1ai_customer_chat');
    this.addMessage('system', '🗑️ تم مسح المحادثة');
  },

  saveHistory() {
    try {
      localStorage.setItem('h1ai_customer_chat', JSON.stringify({
        messages: this.messages.slice(-50),
        sessionId: this.sessionId,
      }));
    } catch (e) {}
  },

  loadHistory() {
    try {
      const saved = localStorage.getItem('h1ai_customer_chat');
      if (saved) {
        const data = JSON.parse(saved);
        // Skip auto-load to keep welcome message clean
        if (data.messages && data.messages.length > 0) {
          // Optional: restore previous conversation
          // this.messages = data.messages;
          // this.sessionId = data.sessionId;
        }
      }
    } catch (e) {}
  },

  toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('h1ai_customer_theme', isDark ? 'dark' : 'light');
    document.getElementById('theme-btn').textContent = isDark ? '☀️' : '🌙';
  },

  loadTheme() {
    const saved = localStorage.getItem('h1ai_customer_theme');
    if (saved === 'dark') {
      document.body.classList.add('dark-mode');
      document.getElementById('theme-btn').textContent = '☀️';
    }
  },
};

// ─── Initialize ───
document.addEventListener('DOMContentLoaded', () => {
  // Load marked.js for markdown
  if (!window.marked) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    document.head.appendChild(script);
  }

  Chat.init();
});
