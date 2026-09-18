/* ═══════════════════════════════════════════════════════ */
/*  H1-AI Dashboard Logic                                  */
/* ═══════════════════════════════════════════════════════ */

// ─── Navigation ───
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        const page = item.dataset.page;
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const target = document.getElementById(`page-${page}`);
        if (target) target.classList.add('active');
        loadPage(page);
    });
});

function loadPage(page) {
    switch (page) {
        case 'dashboard': loadDashboard(); break;
        case 'team': loadTeamPage(); break;
        case 'reports': loadReports(); break;
        case 'messages': loadMessages(); break;
        case 'live': startLive(); break;
    }
}

// ─── Dashboard ───
async function loadDashboard() {
    try {
        const stats = await API.getStats();
        
        document.getElementById('stat-messages').textContent = stats.messages_24h?.total || 0;
        document.getElementById('stat-reports').textContent = stats.reports?.total || 0;
        document.getElementById('stat-urgent').textContent = stats.reports?.by_priority?.urgent || 0;
        document.getElementById('stat-team').textContent = stats.team?.total || 0;
        
        await Promise.all([
            loadRecentMessages(),
            loadTeamStatus(),
        ]);
    } catch (error) {
        console.error('Dashboard error:', error);
        document.getElementById('recent-messages').innerHTML = 
            `<div class="loading">❌ خطأ: ${error.message}</div>`;
    }
}

async function loadRecentMessages() {
    const container = document.getElementById('recent-messages');
    try {
        const data = await API.getMessages(5);
        const messages = data.messages || [];
        
        if (!messages.length) {
            container.innerHTML = '<div class="loading">لا توجد رسائل</div>';
            return;
        }
        
        container.innerHTML = messages.map(m => {
            const cls = m.classification || 'pending';
            const badgeClass = cls === 'unknown' ? 'spam' : cls;
            return `
                <div class="message-item ${cls}">
                    <div class="message-content">
                        <div class="message-phone">
                            📱 ${m.from_phone || 'مجهول'}
                            <span class="badge badge-${badgeClass}">${cls}</span>
                        </div>
                        <div class="message-text">${escapeHtml((m.content || '').slice(0, 80))}</div>
                    </div>
                    <div class="message-time">${formatTime(m.received_at)}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

async function loadTeamStatus() {
    const container = document.getElementById('team-status');
    try {
        const data = await API.getTeam();
        const members = data.members || [];
        
        if (!members.length) {
            container.innerHTML = '<div class="loading">لا يوجد أعضاء</div>';
            return;
        }
        
        container.innerHTML = members.slice(0, 5).map(m => renderTeamMember(m)).join('');
    } catch (error) {
        container.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

function renderTeamMember(m) {
    const load = m.current_load || 0;
    const max = m.max_concurrent || 10;
    const percent = Math.min(100, (load / max) * 100);
    const level = percent > 80 ? 'danger' : percent > 50 ? 'warning' : '';
    return `
        <div class="team-member">
            <div class="member-info">
                <div class="member-name">${m.name_ar || m.name}</div>
                <div class="member-role">${m.role} · ${m.shift}</div>
            </div>
            <div class="member-load">
                <div class="load-bar">
                    <div class="load-fill ${level}" style="width: ${percent}%"></div>
                </div>
                <span class="load-text">${load}/${max}</span>
            </div>
        </div>
    `;
}

// ─── Team ───
async function loadTeamPage() {
    const container = document.getElementById('team-full-list');
    try {
        const data = await API.getTeam();
        const members = data.members || [];
        container.innerHTML = members.map(m => renderTeamMember(m)).join('');
    } catch (error) {
        container.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

// ─── Reports ───
async function loadReports() {
    const container = document.getElementById('reports-list');
    const status = document.getElementById('filter-status')?.value || '';
    const priority = document.getElementById('filter-priority')?.value || '';
    
    try {
        const data = await API.getReports(status, priority);
        const reports = data.reports || [];
        
        if (!reports.length) {
            container.innerHTML = '<div class="loading">لا توجد تقارير</div>';
            return;
        }
        
        container.innerHTML = reports.map(r => `
            <div class="report-card ${r.priority}">
                <div class="report-header">
                    <div class="report-title">${escapeHtml(r.title)}</div>
                    <span class="badge badge-${r.priority}">${r.priority}</span>
                </div>
                <div class="report-summary">${escapeHtml(r.summary || '')}</div>
                <div class="report-meta">
                    <span>📋 ${r.type}</span>
                    <span>📌 ${r.status}</span>
                    ${r.assigned_to_name ? `<span>👤 ${r.assigned_to_name}</span>` : ''}
                    <span>🕐 ${formatTime(r.created_at)}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

// ─── Messages ───
async function loadMessages() {
    const container = document.getElementById('messages-list');
    const classification = document.getElementById('filter-classification')?.value || '';
    
    try {
        const data = await API.getMessages(100, classification);
        const messages = data.messages || [];
        
        if (!messages.length) {
            container.innerHTML = '<div class="loading">لا توجد رسائل</div>';
            return;
        }
        
        container.innerHTML = messages.map(m => {
            const cls = m.classification || 'pending';
            const badgeClass = cls === 'unknown' ? 'spam' : cls;
            return `
                <div class="message-item ${cls}">
                    <div class="message-content">
                        <div class="message-phone">
                            📱 ${m.from_phone || 'مجهول'}
                            ${m.from_name ? `(${m.from_name})` : ''}
                            <span class="badge badge-${badgeClass}">${cls}</span>
                        </div>
                        <div class="message-text">${escapeHtml(m.content || '')}</div>
                    </div>
                    <div class="message-time">${formatTime(m.received_at)}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

// ─── Live ───
let liveInterval = null;
let lastLiveCount = 0;

function startLive() {
    if (liveInterval) clearInterval(liveInterval);
    loadLive();
    liveInterval = setInterval(loadLive, 5000);
}

async function loadLive() {
    const container = document.getElementById('live-feed');
    try {
        const data = await API.getMessages(20);
        const messages = data.messages || [];
        
        if (messages.length === lastLiveCount) return;
        lastLiveCount = messages.length;
        
        container.innerHTML = messages.map(m => {
            const cls = m.classification || '';
            return `
                <div class="live-item ${cls}">
                    <strong>${formatTime(m.received_at)}</strong> · 
                    <span class="badge badge-${cls === 'unknown' ? 'spam' : cls}">${cls || '—'}</span>
                    📱 ${m.from_phone}
                    <div style="margin-top:0.5rem;">${escapeHtml((m.content || '').slice(0, 100))}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

// ─── Helpers ───
function formatTime(iso) {
    if (!iso) return '—';
    try {
        const d = new Date(iso);
        return d.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });
    } catch { return '—'; }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function logout() {
    localStorage.removeItem('h1ai_token');
    window.location.href = '/admin/';
}

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard loaded');
    loadDashboard();
});

/* ═══════════════════════════════════════════════════════ */
/*  TEAM MANAGEMENT                                        */
/* ═══════════════════════════════════════════════════════ */

let teamCache = [];
let constantsCache = null;

async function loadTeamTable() {
    const tbody = document.getElementById('team-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="8" class="loading">جاري التحميل...</td></tr>';
    
    try {
        const [teamData, constData] = await Promise.all([
            API.getTeam(),
            constantsCache ? Promise.resolve(constantsCache) : fetch('/webhook/v2/constants').then(r => r.json()),
        ]);
        
        constantsCache = constData;
        teamCache = teamData.members || [];
        
        renderTeamTable(teamCache);
    } catch (error) {
        console.error('loadTeamTable error:', error);
        tbody.innerHTML = `<tr><td colspan="8" class="loading">❌ ${error.message}</td></tr>`;
    }
}

function renderTeamTable(members) {
    const tbody = document.getElementById('team-table-body');
    
    if (!members.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">لا يوجد أعضاء</td></tr>';
        return;
    }
    
    tbody.innerHTML = members.map(m => `
        <tr>
            <td>
                <strong>${escapeHtml(m.name_ar || m.name)}</strong>
                ${m.name && m.name_ar ? `<br><small style="color:var(--text-secondary)">${escapeHtml(m.name)}</small>` : ''}
            </td>
            <td>
                <span class="badge-role badge-${m.role}">${escapeHtml(m.role)}</span>
            </td>
            <td>
                ${(m.specialties || []).map(s => 
                    `<span class="badge badge-normal">${escapeHtml(s)}</span>`
                ).join(' ') || '—'}
            </td>
            <td>${escapeHtml(m.shift)}</td>
            <td style="direction:ltr; text-align:right;">${escapeHtml(m.phone)}</td>
            <td>${m.current_load}/${m.max_concurrent}</td>
            <td>
                <span class="${m.is_active ? 'status-active' : 'status-inactive'}">
                    ${m.is_active ? '✅ نشط' : '⏸️ معطّل'}
                </span>
            </td>
            <td>
                <button onclick="editTeamMember('${m.id}')" 
                        class="btn-icon" title="تعديل">✏️</button>
                <button onclick="toggleTeamMember('${m.id}')" 
                        class="btn-icon btn-warning" 
                        title="${m.is_active ? 'تعطيل' : 'تفعيل'}">
                    ${m.is_active ? '⏸️' : '▶️'}
                </button>
                <button onclick="confirmDeleteTeamMember('${m.id}', '${escapeHtml(m.name_ar || m.name)}')" 
                        class="btn-icon btn-danger" title="حذف">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function filterTeamTable() {
    const search = document.getElementById('team-search')?.value.toLowerCase() || '';
    const role = document.getElementById('team-role-filter')?.value || '';
    const shift = document.getElementById('team-shift-filter')?.value || '';
    
    const filtered = teamCache.filter(m => {
        const matchesSearch = !search || 
            (m.name || '').toLowerCase().includes(search) ||
            (m.name_ar || '').includes(search) ||
            (m.phone || '').includes(search);
        const matchesRole = !role || m.role === role;
        const matchesShift = !shift || m.shift === shift;
        return matchesSearch && matchesRole && matchesShift;
    });
    
    renderTeamTable(filtered);
}

function openTeamModal(memberId = null) {
    const modal = document.getElementById('team-modal');
    const form = document.getElementById('team-form');
    const title = document.getElementById('team-modal-title');
    
    form.reset();
    document.getElementById('team-id').value = '';
    
    // Load specialties checkboxes
    const specsContainer = document.getElementById('team-specialties');
    if (constantsCache) {
        specsContainer.innerHTML = constantsCache.specialties.map(s => `
            <label>
                <input type="checkbox" value="${s}" class="spec-checkbox">
                ${s}
            </label>
        `).join('');
    }
    
    if (memberId) {
        title.textContent = '✏️ تعديل عضو';
        const m = teamCache.find(x => x.id === memberId);
        if (m) {
            document.getElementById('team-id').value = m.id;
            document.getElementById('team-name-ar').value = m.name_ar || '';
            document.getElementById('team-name').value = m.name || '';
            document.getElementById('team-phone').value = m.phone || '';
            document.getElementById('team-email').value = m.email || '';
            document.getElementById('team-role').value = m.role || 'pharmacist';
            document.getElementById('team-shift').value = m.shift || 'morning';
            document.getElementById('team-max').value = m.max_concurrent || 10;
            document.getElementById('team-whatsapp').checked = m.whatsapp_enabled !== false;
            
            // Languages
            const langs = m.languages || ['ar'];
            document.getElementById('team-lang-ar').checked = langs.includes('ar');
            document.getElementById('team-lang-en').checked = langs.includes('en');
            
            // Specialties
            (m.specialties || []).forEach(s => {
                const cb = specsContainer.querySelector(`input[value="${s}"]`);
                if (cb) cb.checked = true;
            });
        }
    } else {
        title.textContent = '➕ إضافة عضو جديد';
        document.getElementById('team-role').value = 'pharmacist';
        document.getElementById('team-shift').value = 'morning';
        document.getElementById('team-max').value = 10;
    }
    
    modal.style.display = 'flex';
}

function closeTeamModal() {
    document.getElementById('team-modal').style.display = 'none';
}

async function saveTeamMember(event) {
    event.preventDefault();
    
    const id = document.getElementById('team-id').value;
    const specialties = Array.from(document.querySelectorAll('.spec-checkbox:checked'))
        .map(cb => cb.value);
    
    const languages = [];
    if (document.getElementById('team-lang-ar').checked) languages.push('ar');
    if (document.getElementById('team-lang-en').checked) languages.push('en');
    
    const data = {
        name: document.getElementById('team-name').value || document.getElementById('team-name-ar').value,
        name_ar: document.getElementById('team-name-ar').value,
        phone: document.getElementById('team-phone').value,
        email: document.getElementById('team-email').value || null,
        role: document.getElementById('team-role').value,
        shift: document.getElementById('team-shift').value,
        max_concurrent: parseInt(document.getElementById('team-max').value),
        specialties: specialties,
        languages: languages,
        whatsapp_enabled: document.getElementById('team-whatsapp').checked,
    };
    
    try {
        let result;
        if (id) {
            // Update
            result = await fetch(`/webhook/v2/team/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data),
            }).then(r => r.json());
        } else {
            // Create
            result = await fetch('/webhook/v2/team', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data),
            }).then(r => r.json());
        }
        
        if (result.success) {
            showToast(id ? '✅ تم التعديل' : '✅ تم الإضافة', 'success');
            closeTeamModal();
            await loadTeamTable();
        } else {
            showToast('❌ ' + (result.detail || 'خطأ'), 'error');
        }
    } catch (error) {
        showToast('❌ ' + error.message, 'error');
    }
}

function editTeamMember(id) {
    openTeamModal(id);
}

async function toggleTeamMember(id) {
    try {
        const result = await fetch(`/webhook/v2/team/${id}/toggle`, {
            method: 'POST',
        }).then(r => r.json());
        
        if (result.success) {
            showToast('✅ تم التعديل', 'success');
            await loadTeamTable();
        }
    } catch (error) {
        showToast('❌ ' + error.message, 'error');
    }
}

async function confirmDeleteTeamMember(id, name) {
    if (!confirm(`هل أنت متأكد من حذف "${name}"؟`)) return;
    
    try {
        const result = await fetch(`/webhook/v2/team/${id}`, {
            method: 'DELETE',
        }).then(r => r.json());
        
        if (result.success) {
            showToast('🗑️ تم الحذف', 'success');
            await loadTeamTable();
        }
    } catch (error) {
        showToast('❌ ' + error.message, 'error');
    }
}

// ─── Toast Notification ───
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ─── Override loadTeamPage (from earlier) ───
async function loadTeamPage() {
    await loadTeamTable();
}


// ─── Load team.html content ───
async function ensureTeamPageLoaded() {
    const container = document.getElementById('team-page-container');
    if (!container || container.innerHTML.trim()) return;
    
    try {
        const html = await fetch('/admin/static/pages/team.html').then(r => r.text());
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

// Override loadTeamPage to ensure content first
const originalLoadTeamPage = loadTeamPage;
loadTeamPage = async function() {
    await ensureTeamPageLoaded();
    await loadTeamTable();
};
