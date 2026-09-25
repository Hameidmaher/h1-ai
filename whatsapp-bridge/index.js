/**
 * H1-AI WhatsApp Bridge — whatsapp-web.js
 * أكثر استقراراً من Baileys
 */
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;
import qrcode from 'qrcode-terminal';
import axios from 'axios';

const API_URL = process.env.H1AI_API || 'http://localhost:8000';
const PHARMACY_ID = process.env.PHARMACY_ID || '00000000-0000-0000-0000-000000000001';
const SESSION_DIR = './auth';

console.log('🚀 Starting WhatsApp Bridge (whatsapp-web.js)...');

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: SESSION_DIR }),
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
            '--disable-gpu',
        ],
    },
});

// ─── QR ─────────────────────────────────────────────────
client.on('qr', (qr) => {
    console.log('\n📱 امسح الـ QR ده من WhatsApp على موبايلك:\n');
    console.log('   WhatsApp → Linked Devices → Link a Device\n');
    qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
    console.log('✅ WhatsApp authenticated!');
});

client.on('auth_failure', (msg) => {
    console.error('❌ Auth failed:', msg);
    console.log('   امسح مجلد auth وأعد التشغيل: rm -rf auth && node index.js');
});

client.on('loading_screen', (percent, message) => {
    console.log(`⏳ Loading... ${percent}% — ${message}`);
});

client.on('ready', () => {
    console.log('✅ WhatsApp Client Ready!');
    console.log(`   Pharmacy: ${PHARMACY_ID}`);
    console.log(`   API: ${API_URL}`);
    console.log('\n📥 في انتظار الرسائل...\n');
});

// ─── Messages ───────────────────────────────────────────
client.on('message', async (msg) => {
    // تجاهل الجروبات
    const chat = await msg.getChat();
    if (chat.isGroup) return;

    // تجاهل من نفسي
    if (msg.fromMe) return;

    const text = msg.body;
    if (!text || !text.trim()) return;

    const phone = msg.from.replace('@c.us', '').replace('@s.whatsapp.net', '');
    const contact = await msg.getContact();
    const name = contact.pushname || contact.name || '';

    console.log(`\n📩 من ${phone} (${name}): ${text}`);

    try {
        const res = await axios.post(`${API_URL}/webhook/whatsapp/chat`, {
            from_phone: phone,
            from_name: name,
            message: text,
            whatsapp_id: msg.id._serialized,
            pharmacy_id: PHARMACY_ID,
        }, { timeout: 45000 });

        const reply = res.data.reply;
        console.log(`💊 الرد: ${reply.substring(0, 100)}...`);

        // ارد
        await msg.reply(reply);
        console.log('✅ تم الإرسال');
    } catch (err) {
        console.error('❌ فشل:', err.message);
        try {
            await msg.reply('معلش، حصلت مشكلة. حاول تاني بعد شوية.');
        } catch (e) {
            console.error('❌ فشل حتى في إرسال الخطأ:', e.message);
        }
    }
});

// ─── Disconnection ──────────────────────────────────────
client.on('disconnected', (reason) => {
    console.log('❌ Disconnected:', reason);
    console.log('🔄 Restarting...');
    setTimeout(() => {
        client.initialize();
    }, 5000);
});

// ─── Init ────────────────────────────────────────────────
client.initialize();

// ─── Graceful shutdown ──────────────────────────────────
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down...');
    await client.destroy();
    process.exit(0);
});
