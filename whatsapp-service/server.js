/**
 * H1-AI — WhatsApp Multi-Session Bridge
 * Manages multiple WhatsApp numbers (one per pharmacy)
 */
require('dotenv').config();
const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode');
const pino = require('pino');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json({ limit: '10mb' }));

const PORT = process.env.PORT || 3001;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const WEBHOOK_API_KEY = process.env.WEBHOOK_API_KEY || '';
const SESSIONS_DIR = path.join(__dirname, 'sessions');

// Ensure sessions directory
if (!fs.existsSync(SESSIONS_DIR)) {
    fs.mkdirSync(SESSIONS_DIR, { recursive: true });
}

// ─── Sessions Storage ───
// sessions = { [phone_number]: { sock, qr, status, pharmacy_id } }
const sessions = {};

// ─── Logger ───
const logger = pino({ level: 'silent' });

// ─── Create Session ───
async function createSession(phoneNumber, pharmacyId) {
    const sessionPath = path.join(SESSIONS_DIR, `session-${phoneNumber}`);
    
    // If already exists
    if (sessions[phoneNumber] && sessions[phoneNumber].status === 'connected') {
        return { 
            status: 'already_connected',
            phone_number: phoneNumber,
        };
    }

    console.log(`\n🔄 Creating session for ${phoneNumber}...`);

    const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
    const { version } = await fetchLatestBaileysVersion();

    const sock = makeWASocket({
        version,
        logger,
        printQRInTerminal: false,
        auth: state,
        browser: ['H1-AI', 'Chrome', '1.0.0'],
    });

    sessions[phoneNumber] = {
        sock,
        qr: null,
        status: 'initializing',
        pharmacy_id: pharmacyId,
        phone_number: phoneNumber,
    };

    // ─── QR Code ───
    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            sessions[phoneNumber].qr = qr;
            sessions[phoneNumber].status = 'waiting_qr';
            
            console.log(`\n📱 QR Code generated for ${phoneNumber}`);
            console.log(`   View at: http://localhost:${PORT}/sessions/${phoneNumber}/qr`);
            
            // Print small QR to terminal
            const QRCode = require('qrcode-terminal');
            QRCode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log(`❌ Connection closed for ${phoneNumber}, reconnect: ${shouldReconnect}`);
            
            if (shouldReconnect) {
                delete sessions[phoneNumber];
                setTimeout(() => createSession(phoneNumber, pharmacyId), 5000);
            } else {
                sessions[phoneNumber].status = 'disconnected';
            }
        } else if (connection === 'open') {
            sessions[phoneNumber].status = 'connected';
            sessions[phoneNumber].qr = null;
            console.log(`\n✅ ${phoneNumber} — WhatsApp Connected!`);
            
            // Update backend
            try {
                await axios.put(
                    `${BACKEND_URL}/v1/admin/whatsapp/${phoneNumber}/connect`,
                    { connected: true, connected_at: new Date().toISOString() },
                    { headers: { 'X-API-Key': WEBHOOK_API_KEY } }
                );
            } catch (e) {
                console.log(`   ⚠️  Backend update failed: ${e.message}`);
            }
        }
    });

    // ─── Save credentials ───
    sock.ev.on('creds.update', saveCreds);

    // ─── Incoming Messages ───
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            if (msg.key.fromMe) continue;
            if (!msg.message) continue;

            const from = msg.key.remoteJid;
            const text = msg.message.conversation 
                || msg.message.extendedTextMessage?.text 
                || '';

            if (!text) continue;

            console.log(`\n📩 [${phoneNumber}] From ${from}: ${text.substring(0, 50)}`);

            try {
                // Send to backend
                const response = await axios.post(
                    `${BACKEND_URL}/v1/whatsapp/incoming`,
                    {
                        message: text,
                        session_id: `${phoneNumber}:${from}`,
                        pharmacy_phone: phoneNumber,
                    },
                    {
                        headers: {
                            'Content-Type': 'application/json',
                            'X-API-Key': WEBHOOK_API_KEY,
                        },
                        timeout: 30000,
                    }
                );

                const reply = response.data?.response || 'عذراً، حدث خطأ';
                const isEmergency = response.data?.handler === 'advisory_emergency';

                // Send reply
                await sock.sendMessage(from, { text: reply });
                console.log(`📤 [${phoneNumber}] Replied`);

                if (isEmergency) {
                    console.log(`🚨 [${phoneNumber}] EMERGENCY handled`);
                }

            } catch (error) {
                console.error(`❌ Error: ${error.message}`);
                
                try {
                    await sock.sendMessage(from, { 
                        text: 'عذراً، حدث خطأ مؤقت. حاول تاني.' 
                    });
                } catch (e) {}
            }
        }
    });

    return sessions[phoneNumber];
}

// ─── API Endpoints ───

// Health
app.get('/health', (req, res) => {
    const activeSessions = Object.entries(sessions).map(([num, s]) => ({
        phone_number: num,
        status: s.status,
        pharmacy_id: s.pharmacy_id,
        has_qr: !!s.qr,
    }));

    res.json({
        status: 'running',
        total_sessions: activeSessions.length,
        connected: activeSessions.filter(s => s.status === 'connected').length,
        sessions: activeSessions,
    });
});

// List all sessions
app.get('/sessions', (req, res) => {
    const list = Object.entries(sessions).map(([num, s]) => ({
        phone_number: num,
        status: s.status,
        pharmacy_id: s.pharmacy_id,
        has_qr: !!s.qr,
    }));
    res.json({ sessions: list });
});

// Get QR for specific session (as PNG)
app.get('/sessions/:phone/qr', async (req, res) => {
    const { phone } = req.params;
    const session = sessions[phone];

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    if (session.status === 'connected') {
        return res.json({ status: 'connected', message: 'Already connected' });
    }

    if (!session.qr) {
        return res.json({ status: session.status, message: 'QR not ready yet' });
    }

    // Return QR as PNG image
    const qrDataURL = await qrcode.toDataURL(session.qr);
    res.json({
        status: 'waiting_qr',
        phone_number: phone,
        qr_image: qrDataURL,
        qr_raw: session.qr,
    });
});

// Start new session
app.post('/sessions', async (req, res) => {
    const { phone_number, pharmacy_id } = req.body;

    if (!phone_number) {
        return res.status(400).json({ error: 'phone_number required' });
    }

    try {
        await createSession(phone_number, pharmacy_id);
        
        // Wait a bit for QR to generate
        await new Promise(r => setTimeout(r, 3000));

        const session = sessions[phone_number];
        res.json({
            success: true,
            phone_number,
            status: session?.status || 'initializing',
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Stop session
app.delete('/sessions/:phone', async (req, res) => {
    const { phone } = req.params;
    const session = sessions[phone];

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    try {
        await session.sock.logout();
        delete sessions[phone];
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Send message
app.post('/send', async (req, res) => {
    const { phone_number, to, message } = req.body;

    const session = sessions[phone_number];
    if (!session || session.status !== 'connected') {
        return res.status(503).json({ error: 'Session not connected' });
    }

    try {
        const jid = to.includes('@') ? to : `${to}@s.whatsapp.net`;
        await session.sock.sendMessage(jid, { text: message });
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// ─── Start Server ───
app.listen(PORT, () => {
    console.log(`\n🚀 WhatsApp Multi-Session Bridge`);
    console.log(`   Port: ${PORT}`);
    console.log(`   Backend: ${BACKEND_URL}`);
    console.log(`   Health: http://localhost:${PORT}/health`);
    console.log(`   Sessions: http://localhost:${PORT}/sessions\n`);
});

// ─── Restore existing sessions ───
async function restoreSessions() {
    const dirs = fs.readdirSync(SESSIONS_DIR).filter(d => d.startsWith('session-'));
    
    for (const dir of dirs) {
        const phone = dir.replace('session-', '');
        console.log(`🔄 Restoring session: ${phone}`);
        try {
            await createSession(phone, null);
        } catch (e) {
            console.log(`   ❌ Failed: ${e.message}`);
        }
    }
}

restoreSessions();
