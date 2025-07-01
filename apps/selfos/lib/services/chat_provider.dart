import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../config/app_config.dart';
import '../models/chat_message.dart';
import 'chat_service.dart';
import 'storage_service.dart';

/// Chat state management
class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? error;

  const ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.error,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? error,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Chat state notifier
class ChatNotifier extends StateNotifier<ChatState> {
  final ChatService _chatService;

  ChatNotifier({required ChatService chatService}) 
    : _chatService = chatService,
      super(const ChatState()) {
    // Note: Chat history loading disabled until backend implements GET /api/ai/chat
    // _loadChatHistory();
  }

  /// Load chat history from the server (currently disabled)
  Future<void> _loadChatHistory() async {
    try {
      final history = await _chatService.getChatHistory();
      state = state.copyWith(messages: history);
    } catch (e) {
      // Silently fail for history loading - not critical
      print('💬 Chat history loading failed (expected): $e');
    }
  }

  /// Send a message to the AI
  Future<void> sendMessage(String message) async {
    if (message.trim().isEmpty) return;

    // Add user message immediately
    final userMessage = ChatMessage.user(text: message.trim());
    state = state.copyWith(
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    );

    try {
      // Send to AI service
      final aiResponse = await _chatService.sendMessage(message.trim());
      
      // Add AI response
      state = state.copyWith(
        messages: [...state.messages, aiResponse],
        isLoading: false,
      );
    } catch (e) {
      // Add error message as AI response
      final errorMessage = ChatMessage.ai(
        text: e.toString().contains('ChatException:') 
          ? e.toString().replaceFirst('ChatException: ', '')
          : 'Sorry, I encountered an error. Please try again.',
      );
      
      state = state.copyWith(
        messages: [...state.messages, errorMessage],
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Clear chat history
  void clearChat() {
    state = const ChatState();
  }

  /// Retry last message if there was an error
  void retryLastMessage() {
    if (state.messages.length >= 2 && !state.messages.last.isUser) {
      // Get the last user message
      final messages = List<ChatMessage>.from(state.messages);
      final lastUserMessage = messages.reversed
          .firstWhere((msg) => msg.isUser, orElse: () => ChatMessage.user(text: ''));
      
      if (lastUserMessage.text.isNotEmpty) {
        // Remove the last AI response and retry
        state = state.copyWith(
          messages: messages.sublist(0, messages.length - 1),
          error: null,
        );
        sendMessage(lastUserMessage.text);
      }
    }
  }
}

/// Providers
final chatServiceProvider = Provider<ChatService>((ref) {
  // Create a new Dio instance with similar configuration to AuthService
  final dio = Dio(BaseOptions(
    baseUrl: AppConfig.baseUrl,
    connectTimeout: AppConfig.connectTimeout,
    receiveTimeout: AppConfig.apiTimeout,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  ));
  
  // Add token interceptor for authenticated requests
  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        print('🚀 CHAT REQUEST: ${options.method} ${options.uri}');
        print('📦 REQUEST DATA: ${options.data}');
        try {
          final authHeader = await StorageService.getAuthorizationHeader();
          if (authHeader != null) {
            options.headers['Authorization'] = authHeader;
            print('✅ Auth header added successfully');
          } else {
            print('⚠️ No auth header found in storage');
          }
        } catch (e) {
          print('❌ Error getting auth header: $e');
        }
        handler.next(options);
      },
      onResponse: (response, handler) async {
        print('✅ CHAT RESPONSE: ${response.statusCode} ${response.requestOptions.uri}');
        print('📄 Response data: ${response.data}');
        handler.next(response);
      },
      onError: (error, handler) async {
        print('❌ CHAT ERROR: ${error.type} - ${error.message}');
        print('🔗 URL: ${error.requestOptions.uri}');
        print('📄 Response: ${error.response?.data}');
        print('📊 Status Code: ${error.response?.statusCode}');
        handler.next(error);
      },
    ),
  );
  
  return ChatService(dio: dio);
});

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  return ChatNotifier(chatService: ref.read(chatServiceProvider));
});

/// Convenience providers
final chatMessagesProvider = Provider<List<ChatMessage>>((ref) {
  return ref.watch(chatProvider).messages;
});

final isChatLoadingProvider = Provider<bool>((ref) {
  return ref.watch(chatProvider).isLoading;
});

final chatErrorProvider = Provider<String?>((ref) {
  return ref.watch(chatProvider).error;
});