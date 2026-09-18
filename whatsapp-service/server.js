/**
 * H1-AI — WhatsApp Service
 */
import express from "express";
import axios from "axios";
import pino from "pino";
import { CONFIG, WEBHOOK_API_KEY } from "./config.js";
import { BaileysClient } from "./baileys-client.js";

const logger = pino({ level: CONFIG.LOG_LEVEL });
const app = express();
app.use(express.json());

const client = new BaileysClient();

// ═══════════════════════════════════════════════════════════
// Health check
// ═══════════════════════════════════════════════════════════
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "h1ai-whatsapp",
    version: "1.0.0",
    ...client.getStatus(),
  });
});

// ═══════════════════════════════════════════════════════════
// Send message API (called by Backend)
// ═══════════════════════════════════════════════════════════
app.post("/send", async (req, res) => {
  const { to, text } = req.body;

  if (!to || !text) {
    return res.status(400).json({ error: "to and text required" });
  }

  const success = await client.sendMessage(to, text);

  res.json({
    success,
    to,
    timestamp: new Date().toISOString(),
  });
});

// ═══════════════════════════════════════════════════════════
// Handle incoming messages (forward to Backend)
// ═══════════════════════════════════════════════════════════
client.onMessageReceived(async ({ from, phone, text }) => {
  try {
    logger.info({ phone, text: text.substring(0, 60) }, "🚀 إرسال للـ Backend");

    const url = CONFIG.BACKEND_URL + CONFIG.BACKEND_WEBHOOK;

    const res = await axios.post(
      url,
      {
        phone,
        message: text,
        timestamp: new Date().toISOString(),
      },
      { timeout: 20000 }
    );

    const data = res.data;
    logger.info(
      {
        phone,
        classification: data.classification,
        handler: data.handler,
        should_reply: data.should_reply,
      },
      "✅ تصنيف Backend"
    );

    // Reply only if Backend says so
    if (data.should_reply && data.response) {
      await client.sendMessage(from, data.response);
      logger.info({ phone }, "📤 تم الرد");
    } else if (data.for_pharmacist) {
      logger.info({ phone, classification: data.classification }, "📩 تمرير للصيدلي (بدون رد)");
    } else {
      logger.info({ phone }, "🔇 تجاهل");
    }
  } catch (e) {
    logger.error({ error: e.message }, "❌ فشل Webhook");
  }
});

// ═══════════════════════════════════════════════════════════
// Start
// ═══════════════════════════════════════════════════════════
app.listen(CONFIG.PORT, () => {
  console.log("");
  console.log("════════════════════════════════════════════");
  console.log("  🏥 H1-AI WhatsApp Service");
  console.log("  🌐 Port:", CONFIG.PORT);
  console.log("  📡 Backend:", CONFIG.BACKEND_URL);
  console.log("  🔗 Health: http://localhost:" + CONFIG.PORT + "/health");
  console.log("════════════════════════════════════════════");
  console.log("");
});

// Connect to WhatsApp
client.connect().catch((e) => {
  logger.error({ error: e.message }, "❌ فشل الاتصال");
  process.exit(1);
});
