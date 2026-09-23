import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ChatMessage {
  final String role;
  final String content;
  final List<String> toolsUsed;
  final DateTime timestamp;

  ChatMessage({
    required this.role,
    required this.content,
    this.toolsUsed = const [],
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

class ChatApi {
  static const String baseUrl = 'https://h.tailc0256.ts.net';
  static const String pharmacyId = '00000000-0000-0000-0000-000000000001';

  String? _userId;
  String? _sessionId;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _userId = prefs.getString('h1ai_user_id') ?? 'mobile_${DateTime.now().millisecondsSinceEpoch}';
    _sessionId = prefs.getString('h1ai_session_id');
    await prefs.setString('h1ai_user_id', _userId!);
  }

  Future<Map<String, dynamic>> sendMessage(String message) async {
    await init();

    final response = await http.post(
      Uri.parse('$baseUrl/api/chat/message'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'message': message,
        'channel': 'mobile',
        'channel_user_id': _userId,
        'pharmacy_id': pharmacyId,
      }),
    ).timeout(const Duration(seconds: 45));

    if (response.statusCode != 200) {
      throw Exception('HTTP ${response.statusCode}');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes));

    // احفظ session
    if (data['session_id'] != null && data['session_id'] != _sessionId) {
      _sessionId = data['session_id'];
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('h1ai_session_id', _sessionId!);
    }

    return data;
  }

  Future<List<Map<String, dynamic>>> getHistory() async {
    if (_sessionId == null) return [];
    final response = await http.get(
      Uri.parse('$baseUrl/api/chat/sessions/$_sessionId/messages?limit=30'),
    );
    if (response.statusCode != 200) return [];
    final data = jsonDecode(utf8.decode(response.bodyBytes));
    return List<Map<String, dynamic>>.from(data['messages'] ?? []);
  }

  Future<void> clearSession() async {
    _sessionId = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('h1ai_session_id');
  }
}
