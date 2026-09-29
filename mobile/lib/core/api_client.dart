import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import 'env.dart';
import 'secure_storage.dart';

class ApiClient {
  late final Dio dio;
  late final Dio _refreshDio;
  Future<String?>? _refreshFuture;

  // نقاط النهاية العامة (بدون auth required)
  static const List<String> _publicEndpoints = [
    '/v1/auth/login',
    '/v1/auth/register',
    '/v1/auth/refresh',
  ];

  ApiClient() {
    dio = Dio(BaseOptions(
      baseUrl: Env.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      headers: {'Content-Type': 'application/json'},
    ));

    dio.interceptors.add(PrettyDioLogger(compact: true));

    _refreshDio = Dio(BaseOptions(baseUrl: Env.baseUrl));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // ✅ الشرط الصحيح: نضيف token إلا للنقاط العامة
        final isPublic = _publicEndpoints.any(
          (path) => options.path.startsWith(path),
        );

        if (!isPublic) {
          final t = await SecureStorage.getAccessToken();
          if (t != null && t.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $t';
          }
        }

        handler.next(options);
      },
      onError: (err, handler) async {
        // ✅ نحاول refresh فقط إذا لم تكن النقطة عامة
        final isPublic = _publicEndpoints.any(
          (path) => err.requestOptions.path.startsWith(path),
        );

        if (err.response?.statusCode == 401 && !isPublic) {
          final newT = await _refreshToken();
          if (newT != null) {
            err.requestOptions.headers['Authorization'] = 'Bearer $newT';
            try {
              final retry = await dio.fetch(err.requestOptions);
              return handler.resolve(retry);
            } catch (_) {
              return handler.next(err);
            }
          } else {
            // فشل refresh → امسح وارجع
            await SecureStorage.clear();
          }
        }
        handler.next(err);
      },
    ));
  }

  Future<String?> _refreshToken() {
    _refreshFuture ??= _doRefresh();
    return _refreshFuture!.whenComplete(() => _refreshFuture = null);
  }

  Future<String?> _doRefresh() async {
    try {
      final r = await SecureStorage.getRefreshToken();
      if (r == null) return null;

      final res = await _refreshDio.post(
        Env.refreshEndpoint,
        data: {'refresh_token': r},
      );

      final d = res.data as Map<String, dynamic>;
      final u = d['user'] as Map<String, dynamic>;

      await SecureStorage.saveAuth(
        accessToken: d['access_token'] as String,
        refreshToken: d['refresh_token'] as String,
        role: u['role'] as String,
        userId: u['id'] as String,
        username: u['username'] as String,
      );

      return d['access_token'] as String;
    } catch (_) {
      await SecureStorage.clear();
      return null;
    }
  }
}
