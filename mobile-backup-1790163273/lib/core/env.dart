class Env {
  static String get baseUrl {
    return const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000',
    );
  }

  static const String apiVersion = '/v1';
  static String get chatEndpoint => '$apiVersion/chat';
  static String get loginEndpoint => '$apiVersion/auth/login';
  static String get registerEndpoint => '$apiVersion/auth/register';
  static String get refreshEndpoint => '$apiVersion/auth/refresh';
  static String get meEndpoint => '$apiVersion/auth/me';
  static String get whatsappInfoEndpoint => '$apiVersion/whatsapp/info';
}
