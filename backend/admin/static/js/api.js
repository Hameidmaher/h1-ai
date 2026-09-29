/* ═══════════════════════════════════════════════════════ */
/*  H1-AI API Client                                       */
/* ═══════════════════════════════════════════════════════ */

const API = {
    baseURL: window.location.origin,
    
    async fetch(path, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        };
        
        try {
            const response = await fetch(this.baseURL + path, {
                ...options,
                headers,
            });
            
            if (!response.ok) {
                const error = await response.text();
                console.error(`API Error ${response.status}:`, error);
                throw new Error(`HTTP ${response.status}`);
            }
            
            return response.json();
        } catch (err) {
            console.error('API fetch error:', err);
            throw err;
        }
    },
    
    async getStats() {
        return this.fetch('/webhook/v2/stats');
    },
    
    async getMessages(limit = 50, classification = '') {
        let url = `/webhook/v2/messages?limit=${limit}`;
        if (classification) url += `&classification=${classification}`;
        return this.fetch(url);
    },
    
    async getReports(status = '', priority = '') {
        let url = `/webhook/v2/reports?limit=50`;
        if (status) url += `&status=${status}`;
        if (priority) url += `&priority=${priority}`;
        return this.fetch(url);
    },
    
    async getTeam() {
        return this.fetch('/webhook/v2/team');
    },
    
    async getAssignments() {
        return this.fetch('/webhook/v2/assignments');
    },
};

// ─── Add Webhook API Key support ───
const WEBHOOK_API_KEY = localStorage.getItem('h1ai_webhook_key') || '';

// Patch fetch to include webhook key for /webhook/ paths
const originalFetch = API.fetch.bind(API);
API.fetch = async function(path, options = {}) {
    if (path.startsWith('/webhook/')) {
        options.headers = {
            ...(options.headers || {}),
            'X-API-Key': WEBHOOK_API_KEY,
        };
    }
    return originalFetch(path, options);
};
