/**
 * H1-AI — WhatsApp Web Bridge
 * Bridges WhatsApp messages to H1-AI backend
 */
require('dotenv').config();
const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const app = express();
app.use(express.json({ limit: '10mb' }));

const PORT = process.env.PORT || 3001;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const WEBHOOK_API_KEY = process.env.WEBHOOK_API_KEY || '';

// ─── WhatsApp Client ───
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './sessions' }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    }
});

let clientReady = false;
let qrCode = null;
let clientInfo = null;

// ─── QR Code ───
client.on('qr', (qr) => {
    qrCode = qr;
    console.log('\n═══════════════════════════════════════════════════');
    console.log('  📱 SCAN THIS QR CODE WITH WHATSAPP');
    console.log('═══════════════════════════════════════════════════\n');
    qrcode.generate(qr, { small: true });
    console.log('\n  WhatsApp → Settings → Linked Devices → Link a Device');
    console.log('═══════════════════════════════════════════════════\n');
});

// ─── Ready ───
client.on('ready', () => {
    clientReady = true;
    clientInfo = client.info;
    console.log('\n═══════════════════════════════════════════════════');
    console.log('  ✅ WhatsApp Client READY!');
    console.log(`  📱 Number: ${client.info.wid.user}`);
    console.log(`  👤 Name: ${client.info.pushname}`);
    console.log('═══════════════════════════════════════════════════\n');
});

// ─── Disconnected ───
client.on('disconnected', (reason) => {
    console.log('❌ WhatsApp disconnected:', reason);
    clientReady = false;
    clientInfo = null;
});

// ─── Auth Failure ───
client.on('auth_failure', (msg) => {
    console.error('❌ Auth failure:', msg);
});

// ─── Incoming Message ───
client.on('message', async (message) => {
    console.log(`📩 [${message.from}] ${message.body.substring(0, 50)}...`);

    // Skip groups unless mentioned
    const chat = await message.getChat();
    if (chat.isGroup) return;

    // Skip own messages
    if (message.fromMe) return;

    try {
        // Send to backend
        const response = await axios.post(
            `${BACKEND_URL}/v1/chat`,
            {
                message: message.body,
                session_id: message.from,
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': WEBHOOK_API_KEY,
                },
                timeout: 30000,
            }
        );

        const reply = response.data?.data?.text || 'عذراً، حدث خطأ';

        // Send reply
        await message.reply(reply);
        console.log(`📤 Replied to ${message.from}`);

        // Handle emergency
        if (response.data?.handler === 'advisory_emergency') {
            console.log('🚨 EMERGENCY detected!');
        }

    } catch (error) {
        console.error('❌ Error processing message:', error.message);
        
        // Fallback message
        try {
            await message.reply('عذراً، حدث خطأ مؤقت. حاول تاني.');
        } catch (e) {
            console.error('Failed to send fallback:', e.message);
        }
    }
});

// ─── HTTP API ───
app.get('/health', (req, res) => {
    res.json({
        status: clientReady ? 'ready' : 'initializing',
        connected: clientReady,
        info: clientInfo ? {
            number: clientInfo.wid.user,
            name: clientInfo.pushname,
        } : null,
    });
});

app.get('/qr', (req, res) => {
    if (clientReady) {
        return res.json({ status: 'ready', message: 'Already connected' });
    }
    res.json({ qr: qrCode });
});

app.post('/send', async (req, res) => {
    const { to, message } = req.body;
    
    if (!clientReady) {
        return res.status(503).json({ error: 'WhatsApp not ready' });
    }
    
    try {
        const chatId = to.includes('@') ? to : `${to}@c.us`;
        await client.sendMessage(chatId, message);
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/status', (req, res) => {
    res.json({
        ready: clientReady,
        info: clientInfo,
    });
});

// ─── Start ───
app.listen(PORT, () => {
    console.log(`\n🚀 WhatsApp Bridge running on port ${PORT}`);
    console.log(`   Backend URL: ${BACKEND_URL}`);
    console.log(`   Health: http://localhost:${PORT}/health`);
    console.log(`   QR Code: http://localhost:${PORT}/qr\n`);
});

client.initialize();
