import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/chat_provider.dart';
import '../../widgets/chat/chat_input.dart';
import '../../widgets/chat/message_bubble.dart';

/// Main chat screen for AI conversations
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();
  bool _isInitialLoad = true;

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final messages = ref.watch(chatMessagesProvider);
    final isLoading = ref.watch(isChatLoadingProvider);
    final chatNotifier = ref.read(chatProvider.notifier);

    // Auto-scroll to bottom when new messages arrive
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients && 
          (messages.isNotEmpty || !_isInitialLoad)) {
        _scrollToBottom();
        _isInitialLoad = false;
      }
    });

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Assistant'),
        centerTitle: true,
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
        actions: [
          if (messages.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear_all),
              onPressed: () => _showClearChatDialog(context, chatNotifier),
              tooltip: 'Clear chat',
            ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _buildMessagesList(messages, isLoading, chatNotifier),
          ),
          ChatInput(
            onSendMessage: (message) => _sendMessage(message, chatNotifier),
            isLoading: isLoading,
            placeholder: 'Tell me about a goal you want to achieve...',
          ),
        ],
      ),
    );
  }

  Widget _buildMessagesList(
    List<dynamic> messages,
    bool isLoading,
    dynamic chatNotifier,
  ) {
    if (messages.isEmpty && !isLoading) {
      return _buildEmptyState();
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 16),
      itemCount: messages.length + (isLoading ? 1 : 0),
      itemBuilder: (context, index) {
        // Show loading indicator at the end if loading
        if (index == messages.length && isLoading) {
          return _buildTypingIndicator();
        }

        final message = messages[index];
        final isLastMessage = index == messages.length - 1;
        
        return MessageBubble(
          message: message,
          showTimestamp: _shouldShowTimestamp(messages, index),
          onRetry: !message.isUser && isLastMessage 
            ? () => chatNotifier.retryLastMessage()
            : null,
        );
      },
    );
  }

  Widget _buildEmptyState() {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: colorScheme.primaryContainer.withOpacity(0.3),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.psychology,
                size: 40,
                color: colorScheme.primary,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'AI Goal Assistant',
              style: theme.textTheme.headlineSmall?.copyWith(
                color: colorScheme.onSurface,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Tell me about a goal you want to achieve, and I\'ll help you break it down into actionable steps.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: colorScheme.onSurface.withOpacity(0.7),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            _buildSuggestedPrompts(),
          ],
        ),
      ),
    );
  }

  Widget _buildSuggestedPrompts() {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final chatNotifier = ref.read(chatProvider.notifier);

    final prompts = [
      'I want to learn a new programming language',
      'Help me get healthier and more fit',
      'I want to start a side business',
      'Help me improve my work-life balance',
    ];

    return Column(
      children: prompts.map((prompt) {
        return Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 8),
          child: OutlinedButton(
            onPressed: () => _sendMessage(prompt, chatNotifier),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              side: BorderSide(
                color: colorScheme.outline.withOpacity(0.3),
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: Text(
              prompt,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: colorScheme.onSurface.withOpacity(0.8),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildTypingIndicator() {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      margin: const EdgeInsets.only(top: 4, bottom: 4, left: 16, right: 48),
      child: Row(
        children: [
          CircleAvatar(
            radius: 16,
            backgroundColor: colorScheme.secondaryContainer,
            child: Icon(
              Icons.psychology,
              size: 18,
              color: colorScheme.onSecondaryContainer,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: colorScheme.surfaceVariant,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
                bottomRight: Radius.circular(20),
                bottomLeft: Radius.circular(4),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      colorScheme.onSurfaceVariant.withOpacity(0.6),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  'AI is thinking...',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: colorScheme.onSurfaceVariant.withOpacity(0.8),
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  bool _shouldShowTimestamp(List<dynamic> messages, int index) {
    if (index == 0) return true;
    
    final currentMessage = messages[index];
    final previousMessage = messages[index - 1];
    
    final timeDiff = currentMessage.timestamp.difference(previousMessage.timestamp);
    return timeDiff.inMinutes > 5;
  }

  void _sendMessage(String message, dynamic chatNotifier) {
    chatNotifier.sendMessage(message);
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void _showClearChatDialog(BuildContext context, dynamic chatNotifier) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear Chat'),
        content: const Text(
          'Are you sure you want to clear all messages? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              chatNotifier.clearChat();
              Navigator.pop(context);
            },
            child: const Text('Clear'),
          ),
        ],
      ),
    );
  }
}