import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers.dart';
import '../../core/secure_storage.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _u = TextEditingController(text: 'customer1');
  final _p = TextEditingController(text: 'customer123');
  bool _loading = false;

  @override
  void dispose() { _u.dispose(); _p.dispose(); super.dispose(); }

  Future<void> _login() async {
    setState(() => _loading = true);
    try {
      final api = ref.read(apiClientProvider);
      final r = await api.dio.post('/v1/auth/login', data: {
        'username': _u.text.trim(),
        'password': _p.text,
      });
      final d = r.data as Map<String, dynamic>;
      final user = d['user'] as Map<String, dynamic>;
      await SecureStorage.saveAuth(
        accessToken: d['access_token'] as String,
        refreshToken: d['refresh_token'] as String,
        role: user['role'] as String,
        userId: user['id'] as String,
        username: user['username'] as String,
      );
      ref.invalidate(authStateProvider);
      if (mounted) context.go('/chat');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('فشل الدخول: ${e.toString().split(":").last.trim()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const Text('H1-AI',
                    style: TextStyle(
                      fontSize: 48,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF0EA5E9),
                      letterSpacing: 4,
                    )),
                const SizedBox(height: 8),
                const Text('Assistant Pharmacy',
                    style: TextStyle(color: Colors.grey)),
                const SizedBox(height: 48),
                TextField(
                  controller: _u,
                  decoration: const InputDecoration(
                    labelText: 'اسم المستخدم',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.person),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _p,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'كلمة المرور',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.lock),
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: _loading ? null : _login,
                    child: _loading
                        ? const SizedBox(
                            height: 20, width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('دخول'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
