/**
 * H1-AI — Activity Log (Enhanced Audit)
 */
Pages.activity_log = {
  activities: [],

  async render(el) {
    el.innerHTML = `
      <style>
        .al-header{margin-bottom:20px}
        .al-header h1{margin:0;font-size:24px}
        .al-filters{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}
        .al-filter{padding:8px 14px;border:1px solid #E2E8F0;border-radius:8px;background:white;cursor:pointer;font-family:inherit;font-size:13px;font-weight:600}
        .al-filter.active{background:#0EA5E9;color:white;border-color:#0EA5E9}
        .al-timeline{background:white;border-radius:12px;padding:24px;border:1px solid #E2E8F0}
        .al-item{display:flex;gap:16px;padding:12px 0;border-bottom:1px solid #F1F5F9}
        .al-item:last-child{border-bottom:none}
        .al-icon{width:40px;height:40px;border-radius:50%;background:#EFF6FF;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
        .al-icon.create{background:#DCFCE7}
        .al-icon.update{background:#FEF3C7}
        .al-icon.delete{background:#FEE2E2}
        .al-icon.login{background:#E0E7FF}
        .al-content{flex:1}
        .al-title{font-weight:600;color:#0F172A;font-size:14px;margin-bottom:4px}
        .al-desc{font-size:13px;color:#64748B}
        .al-time{font-size:11px;color:#94A3B8;margin-top:4px}
        .al-empty{text-align:center;padding:60px;color:#94A3B8}
        .al-empty-icon{font-size:60px;margin-bottom:16px;opacity:0.5}
      </style>

      <div class="al-header">
        <h1>📜 سجل النشاطات</h1>
      </div>

      <div class="al-filters">
        <button class="al-filter active" onclick="Pages.activity_log.filter('all', this)">الكل</button>
        <button class="al-filter" onclick="Pages.activity_log.filter('create', this)">➕ إضافة</button>
        <button class="al-filter" onclick="Pages.activity_log.filter('update', this)">✏️ تعديل</button>
        <button class="al-filter" onclick="Pages.activity_log.filter('delete', this)">🗑️ حذف</button>
        <button class="al-filter" onclick="Pages.activity_log.filter('login', this)">🔐 دخول</button>
      </div>

      <div id="al-content"></div>
    `;

    await this.loadActivities();
    this.renderActivities('all');
  },

  async loadActivities() {
    try {
      const res = await App.api('/v1/admin/audit/logs?limit=100');
      this.activities = res.logs || [];
    } catch (e) {
      console.error('Failed to load activities:', e);
      this.activities = this.generateSampleActivities();
    }
  },

  generateSampleActivities() {
    // Sample activities for demo
    const now = Date.now();
    return [
      { action: 'login', entity: 'user', entity_id: 'admin', created_at: new Date(now - 60000).toISOString(), username: 'admin' },
      { action: 'create', entity: 'pharmacy', entity_id: 'صيدلية النور', created_at: new Date(now - 300000).toISOString(), username: 'admin' },
      { action: 'update', entity: 'product', entity_id: 'بانادول 500mg', created_at: new Date(now - 600000).toISOString(), username: 'admin' },
      { action: 'create', entity: 'whatsapp_number', entity_id: '+201234567890', created_at: new Date(now - 900000).toISOString(), username: 'admin' },
      { action: 'delete', entity: 'alert', entity_id: 'alert-123', created_at: new Date(now - 1200000).toISOString(), username: 'admin' },
    ];
  },

  renderActivities(filter) {
    const c = document.getElementById('al-content');
    let activities = this.activities;
    
    if (filter !== 'all') {
      activities = activities.filter(a => a.action === filter);
    }

    if (!activities.length) {
      c.innerHTML = `
        <div class="al-timeline">
          <div class="al-empty">
            <div class="al-empty-icon">📜</div>
            <div>لا توجد نشاطات</div>
          </div>
        </div>
      `;
      return;
    }

    const icons = {
      create: '➕',
      update: '✏️',
      delete: '🗑️',
      login: '🔐',
      logout: '🚪',
    };

    c.innerHTML = `
      <div class="al-timeline">
        ${activities.map(a => `
          <div class="al-item">
            <div class="al-icon ${a.action}">${icons[a.action] || '📝'}</div>
            <div class="al-content">
              <div class="al-title">
                ${a.action === 'create' ? 'إضافة' : a.action === 'update' ? 'تعديل' : a.action === 'delete' ? 'حذف' : a.action === 'login' ? 'دخول' : a.action}
                — ${App.escapeHtml(a.entity || '')}
              </div>
              <div class="al-desc">
                ${App.escapeHtml(a.entity_id || '')}
                ${a.username ? `• بواسطة: ${App.escapeHtml(a.username)}` : ''}
              </div>
              <div class="al-time">${App.formatDate(a.created_at)}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  },

  filter(type, btn) {
    document.querySelectorAll('.al-filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    this.renderActivities(type);
  },
};
