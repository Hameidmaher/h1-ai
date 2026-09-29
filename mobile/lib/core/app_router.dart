import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers.dart';
import '../features/auth/login_screen.dart';
import '../features/chat/chat_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: _ValueNotifier(auth),
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const _Splash()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/chat', builder: (_, __) => const ChatScreen()),
    ],
    redirect: (context, state) {
      final loading = auth.isLoading;
      final logged = auth.valueOrNull ?? false;
      final loc = state.matchedLocation;
      if (loading) return loc == '/splash' ? null : '/splash';
      if (loc == '/splash') return logged ? '/chat' : '/login';
      if (!logged && loc != '/login') return '/login';
      if (logged && loc == '/login') return '/chat';
      return null;
    },
  );
});

class _ValueNotifier extends ChangeNotifier {
  _ValueNotifier(AsyncValue<dynamic> value) {
    value.whenData((_) => notifyListeners());
  }
}

class _Splash extends StatelessWidget {
  const _Splash();
  @override
  Widget build(BuildContext context) => Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('H1-AI',
                  style: TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF0EA5E9),
                    letterSpacing: 4,
                  )),
              const SizedBox(height: 8),
              const Text('Assistant Pharmacy'),
              const SizedBox(height: 32),
              const CircularProgressIndicator(),
            ],
          ),
        ),
      );
}
