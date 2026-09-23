// ═══════════════════════════════════════════════════════════
// H1-AI Mobile — Environment Config
// ═══════════════════════════════════════════════════════════

class Env {
  // API Base URL — Tailscale
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://h.tailc0256.ts.net',
  );

  // Backup URL
  static const String backupUrl = String.fromEnvironment(
    'API_BACKUP_URL',
    defaultValue: 'http://100.94.32.49:8000',
  );

  // Endpoints
  static const String loginEndpoint = '/v1/auth/login';
  static const String registerEndpoint = '/v1/auth/register';
  static const String refreshEndpoint = '/v1/auth/refresh';
  static const String chatEndpoint = '/v1/chat';
  static const String chatMessageEndpoint = '/api/chat/message';

  // Pharmacy
  static const String pharmacyId = String.fromEnvironment(
    'PHARMACY_ID',
    defaultValue: '00000000-0000-0000-0000-000000000001',
  );

  // App
  static const String appName = 'H1-AI';
  static const String appVersion = '4.0.0';
}
