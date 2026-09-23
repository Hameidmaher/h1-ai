// ═══════════════════════════════════════════════════════════
// H1-AI Mobile — Configuration
// ═══════════════════════════════════════════════════════════
import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  // API
  static String get apiBaseUrl => 
      dotenv.env['API_BASE_URL'] ?? 'https://h.tailc0256.ts.net';
  
  static String get apiBackupUrl => 
      dotenv.env['API_BACKUP_URL'] ?? 'http://100.94.32.49:8000';

  // Pharmacy
  static String get pharmacyId => 
      dotenv.env['PHARMACY_ID'] ?? '00000000-0000-0000-0000-000000000001';

  // App
  static String get appName => 
      dotenv.env['APP_NAME'] ?? 'H1-AI';
  
  static String get appVersion => 
      dotenv.env['APP_VERSION'] ?? '4.0.0';

  // Features
  static bool get enablePush => 
      dotenv.env['ENABLE_PUSH'] == 'true';
  
  static bool get enableDarkMode => 
      dotenv.env['ENABLE_DARK_MODE'] == 'true';
  
  static bool get enableOfflineCache => 
      dotenv.env['ENABLE_OFFLINE_CACHE'] == 'true';
}
