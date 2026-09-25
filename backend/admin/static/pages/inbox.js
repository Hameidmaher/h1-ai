/**
 * Inbox Page — Unified conversation inbox
 * Follows the Pages.X.render(content) pattern
 */
(function() {
  'use strict';

  const API = '/v1/admin/inbox';
  let conversations = [];
  let activeConvId = null;
  let refreshTimer = null;

  function getToken() {
    // نفس اسم token المستخدم في app.js
    return localStorage.getItem('h1ai_admin_token') || '';
  }

  function headers() {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + getToken(),
    };
  }

  function formatTime(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const diffMin = Math.floor((now - d) / 60000);
    if (diffMin < 1) return 'الآن';
    if (diffMin < 60) return diffMin + ' د';
    if (diffMin < 1440) return Math.floor(diffMin / 60) + ' س';
    return d.toLocaleDateString('ar-EG');
  }

  function esc(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
  }

  async function fetchConversations(status) {
    const url = status ? API + '/conversations?status=' + status : API + '/conversations';
    const r = await fetch(url, { headers: headers() });
    if (!r.ok) throw new Error(await r.text());
    return (await r.json()).conversations || [];
  }

  async function fetchConversation(id) {
    const r = await fetch(API + '/conversations/' + id, { headers: headers() });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async function fetchStats() {
    const r = await fetch(API + '/stats', { headers: headers() });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async function sendReply(id, content) {
    const r = await fetch(API + '/conversations/' + id + '/reply', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ content }),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async function updateStatus(id, status) {
    const r = await fetch(API + '/conversations/' + id + '/status', {
      method: 'PUT',
      headers: headers(),
      body: JSON.stringify({ status }),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  // ═══════════════════════════════════════════════════════════
  //  Render
  // ═══════════════════════════════════════════════════════════
  function renderLayout(content) {
    content.innerHTML =
      '<div class="inbox-container">' +
        '<aside class="inbox-sidebar">' +
          '<div id="inbox-stats" class="inbox-stats">جاري التحميل...</div>' +
          '<div id="conv-list"></div>' +
        '</aside>' +
        '<main class="inbox-main" id="conv-main">' +
          '<div class="empty">اختر محادثة</div>' +
        '</main>' +
      '</div>';
  }

  function renderConversations() {
    const el = document.getElementById('conv-list');
    if (!el) return;

    if (conversations.length === 0) {
      el.innerHTML = '<div class="empty">لا يوجد محادثات</div>';
      return;
    }

    el.innerHTML = conversations.map(c => {
      const isActive = c.id === activeConvId;
      const unread = c.unread_count > 0 ? '<span class="badge">' + c.unread_count + '</span>' : '';
      const statusIcon = {open:'🟢',assigned:'🔵',pending:'🟡',closed:'⚪',archived:'📦'}[c.status] || '⚪';
      return '<div class="conv-item ' + (isActive?'active':'') + '" data-id="' + c.id + '">' +
        '<div class="conv-header">' +
          '<span class="conv-phone">' + esc(c.contact_name || c.contact_phone) + '</span>' +
          '<span class="conv-time">' + formatTime(c.last_message_at) + '</span>' +
        '</div>' +
        '<div class="conv-preview">' + statusIcon + ' ' +
          esc((c.last_message_preview || '').slice(0, 40)) + ' ' + unread +
        '</div>' +
      '</div>';
    }).join('');

    el.querySelectorAll('.conv-item').forEach(item => {
      item.onclick = () => openConversation(item.dataset.id);
    });
  }

  async function openConversation(id) {
    activeConvId = id;
    renderConversations();
    try {
      const conv = await fetchConversation(id);
      renderConversationDetail(conv);
    } catch (e) {
      console.error('fetch conversation failed', e);
    }
  }

  function renderConversationDetail(conv) {
    const main = document.getElementById('conv-main');
    if (!main) return;

    main.innerHTML =
      '<div class="conv-header-main">' +
        '<div><h3>' + esc(conv.contact_name || conv.contact_phone) + '</h3>' +
        '<small>' + esc(conv.contact_phone) + '</small></div>' +
        '<div class="conv-actions">' +
          '<select id="status-select">' +
            ['open','assigned','pending','closed','archived'].map(s =>
              '<option value="' + s + '" ' + (conv.status===s?'selected':'') + '>' + s + '</option>'
            ).join('') +
          '</select>' +
        '</div>' +
      '</div>' +
      '<div id="messages" class="messages">' +
        (conv.messages || []).map(m =>
          '<div class="msg ' + m.direction + '">' +
            '<div class="msg-bubble">' + esc(m.content) + '</div>' +
            '<small class="msg-time">' + formatTime(m.received_at) + '</small>' +
          '</div>'
        ).join('') +
      '</div>' +
      '<div class="reply-box">' +
        '<textarea id="reply-input" placeholder="اكتب الرد..."></textarea>' +
        '<button id="send-btn" class="btn-primary">إرسال</button>' +
      '</div>';

    const msgs = document.getElementById('messages');
    if (msgs) msgs.scrollTop = msgs.scrollHeight;

    document.getElementById('send-btn').onclick = async () => {
      const input = document.getElementById('reply-input');
      const text = input.value.trim();
      if (!text) return;
      try {
        await sendReply(conv.id, text);
        input.value = '';
        const updated = await fetchConversation(conv.id);
        renderConversationDetail(updated);
      } catch (e) {
        alert('فشل الإرسال: ' + e.message);
      }
    };

    document.getElementById('status-select').onchange = async (e) => {
      try {
        await updateStatus(conv.id, e.target.value);
      } catch (err) {
        alert('فشل التغيير: ' + err.message);
      }
    };

    document.getElementById('reply-input').onkeydown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('send-btn').click();
      }
    };
  }

  function renderStats(stats) {
    const el = document.getElementById('inbox-stats');
    if (!el) return;
    el.innerHTML =
      '<span>📬 ' + (stats.total_conversations || 0) + '</span>' +
      '<span>🟢 ' + (stats.open || 0) + '</span>' +
      '<span>🔵 ' + (stats.assigned || 0) + '</span>' +
      '<span>🔴 ' + (stats.unread_total || 0) + '</span>';
  }

  async function loadData() {
    try {
      const convs = await fetchConversations();
      const stats = await fetchStats();
      conversations = convs;
      renderConversations();
      renderStats(stats);
    } catch (e) {
      console.error('load failed', e);
      const el = document.getElementById('conv-list');
      if (el) el.innerHTML = '<div class="error">فشل التحميل: ' + e.message + '</div>';
    }
  }

  async function render(content) {
    renderLayout(content);
    await loadData();

    // Auto refresh every 15s while page is visible
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(() => {
      if (document.getElementById('conv-list')) {
        loadData();
      } else {
        clearInterval(refreshTimer);
        refreshTimer = null;
      }
    }, 15000);
  }

  // Export as Pages.inbox
  window.Pages = window.Pages || {};
  window.Pages.inbox = { render };
})();
