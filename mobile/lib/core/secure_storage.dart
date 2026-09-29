import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  static const _s = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );
  static const _kAccess = 'access_token';
  static const _kRefresh = 'refresh_token';
  static const _kRole = 'user_role';
  static const _kUid = 'user_id';
  static const _kUname = 'username';

  static Future<void> saveAuth({
    required String accessToken, required String refreshToken,
    required String role, required String userId, required String username,
  }) async {
    await Future.wait([
      _s.write(key: _kAccess, value: accessToken),
      _s.write(key: _kRefresh, value: refreshToken),
      _s.write(key: _kRole, value: role),
      _s.write(key: _kUid, value: userId),
      _s.write(key: _kUname, value: username),
    ]);
  }

  static Future<String?> getAccessToken() => _s.read(key: _kAccess);
  static Future<String?> getRefreshToken() => _s.read(key: _kRefresh);
  static Future<String?> getUserRole() => _s.read(key: _kRole);
  static Future<String?> getUsername() => _s.read(key: _kUname);
  static Future<void> clear() => _s.deleteAll();
  static Future<bool> hasTokens() async {
    final t = await getAccessToken();
    return t != null && t.isNotEmpty;
  }
}
