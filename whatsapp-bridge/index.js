/**
 * WhatsApp Bridge — Baileys → H1-AI Chatbot
 */
import makeWASocket, { DisconnectReason, useMultiFileAuthState } from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import axios from 'axios';
import pino from 'pino';

const API_URL = process.env.H1AI_API || 'http://localhost:8000';
const PHARMACY_ID = '00000000-0000-0000-0000-000000000001';
const logger = pino({ level: 'warn' });

async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('./auth');

    const sock = makeWASocket({
        auth: state,
        logger,
        printQRInTerminal: false,
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
        if (qr) {
            console.log('\n📱 Scan this QR with WhatsApp:\n');
            qrcode.generate(qr, { small: true });
        }
        if (connection === 'close') {
            const code = lastDisconnect?.error?.output?.statusCode;
            if (code !== DisconnectReason.loggedOut) {
                console.log('🔁 Reconnecting...');
                setTimeout(startWhatsApp, 3000);
            } else {
                console.log('❌ Logged out. Delete ./auth and restart.');
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp connected!');
        }
    });

    sock.ev.on('messages.upsert', async ({ messages }) => {
        const msg = messages[0];
        if (!msg.message || msg.key.fromMe) return;

        const from = msg.key.remoteJid;
        if (!from || from.includes('@g.us')) return; // تجاهل الجروبات

        const text = msg.message.conversation
            || msg.message.extendedTextMessage?.text
            || '';
        if (!text.trim()) return;

        const phone = from.replace('@s.whatsapp.net', '');
        console.log(`📩 من ${phone}: ${text}`);

        try {
            const res = await axios.post(`${API_URL}/webhook/whatsapp/chat`, {
                from_phone: phone,
                from_name: msg.pushName || '',
                message: text,
                whatsapp_id: msg.key.id,
                pharmacy_id: PHARMACY_ID,
            }, { timeout: 30000 });

            const reply = res.data.reply;
            console.log(`💊 الرد: ${reply.substring(0, 80)}...`);

            await sock.sendMessage(from, { text: reply });
        } catch (err) {
            console.error('❌ فشل:', err.message);
            await sock.sendMessage(from, { text: 'معلش، حصلت مشكلة. حاول تاني.' });
        }
    });
}

startWhatsApp().catch(err => {
    console.error('❌ Fatal:', err);
    process.exit(1);
});
