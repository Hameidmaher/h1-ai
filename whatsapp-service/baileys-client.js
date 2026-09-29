/**
 * H1-AI — Baileys WhatsApp Client
 */
import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} from "@whiskeysockets/baileys";
import { Boom } from "@hapi/boom";
import pino from "pino";
import qrcode from "qrcode-terminal";
import axios from "axios";
import { CONFIG } from "./config.js";

const logger = pino({ level: CONFIG.LOG_LEVEL });

export class BaileysClient {
  constructor() {
    this.sock = null;
    this.isReady = false;
    this.onMessage = null;
  }

  /**
   * Set message handler
   */
  onMessageReceived(handler) {
    this.onMessage = handler;
  }

  /**
   * Connect to WhatsApp
   */
  async connect() {
    logger.info("🔌 بدء الاتصال بـ WhatsApp...");

    const { state, saveCreds } = await useMultiFileAuthState(
      CONFIG.SESSION_DIR
    );
    const { version } = await fetchLatestBaileysVersion();

    this.sock = makeWASocket({
      version,
      logger: pino({ level: "silent" }),
      printQRInTerminal: false,
      auth: state,
      browser: ["H1-AI", "Chrome", "1.0.0"],
    });

    // Save credentials
    this.sock.ev.on("creds.update", saveCreds);

    // Connection updates
    this.sock.ev.on("connection.update", (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        console.log("");
        console.log("════════════════════════════════════════════");
        console.log("  📱 امسح QR Code من WhatsApp:");
        console.log("     Settings → Linked Devices → Link a Device");
        console.log("════════════════════════════════════════════");
        console.log("");
        qrcode.generate(qr, { small: true });
        console.log("");
      }

      if (connection === "close") {
        const shouldReconnect =
          new Boom(lastDisconnect?.error)?.output?.statusCode !==
          DisconnectReason.loggedOut;

        if (shouldReconnect) {
          logger.warn("🔄 انقطع الاتصال — إعادة المحاولة...");
          setTimeout(() => this.connect(), 3000);
        } else {
          logger.error("❌ تم تسجيل الخروج");
        }
      } else if (connection === "open") {
        this.isReady = true;
        console.log("");
        console.log("════════════════════════════════════════════");
        console.log("  ✅ H1-AI WhatsApp جاهز!");
        console.log("  📱 الرقم:", this.sock.user?.id?.split(":")[0]);
        console.log("  📥 في انتظار الرسائل...");
        console.log("════════════════════════════════════════════");
        console.log("");
      }
    });

    // Messages
    this.sock.ev.on("messages.upsert", async (m) => {
      if (m.type !== "notify") return;

      for (const msg of m.messages) {
        // Ignore own messages
        if (msg.key.fromMe) continue;

        // Ignore groups (optional)
        if (msg.key.remoteJid?.endsWith("@g.us")) continue;
        // تجاهل broadcasts و status@
        if (msg.key.remoteJid === "status@broadcast") continue;

        // Get text
        const text =
          msg.message?.conversation ||
          msg.message?.extendedTextMessage?.text ||
          msg.message?.imageMessage?.caption ||
          "";

        if (!text) continue;

        const from = msg.key.remoteJid;
        // تصفية @s.whatsapp.net أو @lid
        const phone = from
          .replace("@s.whatsapp.net", "")
          .replace("@lid", "");

        logger.info({ from: phone, text }, "📥 رسالة واردة");

        if (this.onMessage) {
          await this.onMessage({ from, phone, text, msg });
        }
      }
    });

    return this.sock;
  }

  /**
   * Send message to number
   */
  async sendMessage(to, text) {
    if (!this.isReady || !this.sock) {
      logger.warn("⚠️ WhatsApp غير جاهز");
      return false;
    }

    try {
      // Format JID
      let jid = to;
      if (!jid.includes("@")) {
        jid = jid.replace(/\D/g, "");
        if (jid.startsWith("0")) jid = "20" + jid.substring(1); // Egyptian
        jid = jid + "@s.whatsapp.net";
      }

      await this.sock.sendMessage(jid, { text });
      logger.info({ to: jid, text: text.substring(0, 50) }, "📤 رسالة صادرة");
      return true;
    } catch (e) {
      logger.error({ error: e.message }, "❌ فشل الإرسال");
      return false;
    }
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      connected: this.isReady,
      phone: this.sock?.user?.id?.split(":")[0] || null,
    };
  }
}
