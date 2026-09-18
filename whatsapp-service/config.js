export const CONFIG = {
  // Service Port
  PORT: 3001,

  // H1-AI Backend
  BACKEND_URL: "http://localhost:8000",
  BACKEND_WEBHOOK: "/webhook/v2/incoming",

  // Session storage
  SESSION_DIR: "./sessions",

  // Logging
  LOG_LEVEL: "info",
};

// Webhook API key (must match backend)
export const WEBHOOK_API_KEY = process.env.WEBHOOK_API_KEY || 'change_me_webhook_key_min_16_chars';
