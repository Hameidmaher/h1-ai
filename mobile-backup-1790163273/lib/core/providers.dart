import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_client.dart';
import 'secure_storage.dart';

final apiClientProvider = Provider<ApiClient>((_) => ApiClient());

final authStateProvider = FutureProvider<bool>((_) async {
  final has = await SecureStorage.hasTokens();
  if (!has) return false;
  try {
    final api = ApiClient();
    await api.dio.get('/v1/auth/me');
    return true;
  } catch (_) {
    await SecureStorage.clear();
    return false;
  }
});

final whatsAppInfoProvider =
    FutureProvider<Map<String, dynamic>>((_) async {
  try {
    final api = ApiClient();
    final r = await api.dio.get('/v1/whatsapp/info');
    return r.data as Map<String, dynamic>;
  } catch (_) {
    return {'enabled': false, 'phone': '', 'mode': 'link'};
  }
});
