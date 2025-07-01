/// Chat message model for AI conversations
class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final String? id;

  ChatMessage({
    required this.text,
    required this.isUser,
    DateTime? timestamp,
    this.id,
  }) : timestamp = timestamp ?? DateTime.now();

  /// Creates a user message
  ChatMessage.user({
    required this.text,
    DateTime? timestamp,
    this.id,
  }) : isUser = true,
       timestamp = timestamp ?? DateTime.now();

  /// Creates an AI message
  ChatMessage.ai({
    required this.text,
    DateTime? timestamp,
    this.id,
  }) : isUser = false,
       timestamp = timestamp ?? DateTime.now();

  @override
  String toString() => 'ChatMessage(text: $text, isUser: $isUser, timestamp: $timestamp)';
}