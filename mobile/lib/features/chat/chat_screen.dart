import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:uuid/uuid.dart';
import '../../core/providers.dart';
import '../../core/secure_storage.dart';

class _Msg {
  final String text;
  final bool isUser;
  const _Msg(this.text, this.isUser);
}

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});
  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _input = TextEditingController();
  final _messages = <_Msg>[];
  bool _loading = false;
  String? _sessionId;

  Future<void> _send() async {
    final text = _input.text.trim();
    if (text.isEmpty || _loading) return;
    _input.clear();
    setState(() {
      _messages.add(_Msg(text, true));
      _loading = true;
    });

    try {
      final api = ref.read(apiClientProvider);
      final r = await api.dio.post('/v1/chat', data: {
        'message': text,
        if (_sessionId != null) 'session_id': _sessionId,
      });
      final d = r.data as Map<String, dynamic>;
      _sessionId = d['session_id'] as String?;
      final data = d['data'] as Map<String, dynamic>;
      setState(() {
        _messages.add(_Msg(data['text'] as String, false));
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add(_Msg('عذراً، حدث خطأ: ${e.toString()}', false));
        _loading = false;
      });
    }
  }

  Future<void> _openWhatsApp() async {
    final info = ref.read(whatsAppInfoProvider).valueOrNull;
    if (info == null) return;
    final phone = (info['phone'] as String? ?? '').replaceAll(RegExp(r'\D'), '');
    if (phone.isEmpty) return;
    final url = Uri.parse('https://wa.me/$phone?text=${Uri.encodeComponent("مرحباً، أحتاج مساعدة")}');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _logout() async {
    await SecureStorage.clear();
    ref.invalidate(authStateProvider);
    if (mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('H1-AI — المساعد الذكي'),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat, color: Color(0xFF25D366)),
            onPressed: _openWhatsApp,
            tooltip: 'WhatsApp',
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.local_pharmacy, size: 64, color: Colors.grey),
                        SizedBox(height: 12),
                        Text('اسألني عن أي منتج في الصيدلية',
                            style: TextStyle(color: Colors.grey)),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (_, i) {
                      final m = _messages[i];
                      return Align(
                        alignment: m.isUser
                            ? Alignment.centerRight
                            : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.symmetric(vertical: 4),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 10),
                          constraints: BoxConstraints(
                            maxWidth: MediaQuery.of(context).size.width * 0.75,
                          ),
                          decoration: BoxDecoration(
                            color: m.isUser
                                ? const Color(0xFF0EA5E9)
                                : Colors.grey.shade200,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Text(
                            m.text,
                            style: TextStyle(
                              color: m.isUser ? Colors.white : Colors.black87,
                              fontSize: 15,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(8),
              child: LinearProgressIndicator(),
            ),
          Container(
            padding: const EdgeInsets.all(8),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    decoration: const InputDecoration(
                      hintText: 'اكتب رسالتك...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.all(Radius.circular(24)),
                      ),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12,
                      ),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _loading ? null : _send,
                  icon: const Icon(Icons.send),
                  color: const Color(0xFF0EA5E9),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
