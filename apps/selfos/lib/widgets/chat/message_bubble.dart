import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../models/chat_message.dart';

/// Message bubble widget for displaying chat messages
class MessageBubble extends StatelessWidget {
  final ChatMessage message;
  final bool showTimestamp;
  final VoidCallback? onRetry;

  const MessageBubble({
    super.key,
    required this.message,
    this.showTimestamp = false,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isUser = message.isUser;

    return Container(
      margin: EdgeInsets.only(
        top: 4,
        bottom: 4,
        left: isUser ? 48 : 16,
        right: isUser ? 16 : 48,
      ),
      child: Column(
        crossAxisAlignment: isUser 
          ? CrossAxisAlignment.end 
          : CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: isUser 
              ? MainAxisAlignment.end 
              : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (!isUser) ...[
                _buildAvatar(colorScheme, isUser),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: _buildMessageContainer(theme, colorScheme, isUser),
              ),
              if (isUser) ...[
                const SizedBox(width: 8),
                _buildAvatar(colorScheme, isUser),
              ],
            ],
          ),
          if (showTimestamp) ...[
            const SizedBox(height: 4),
            _buildTimestamp(theme, isUser),
          ],
        ],
      ),
    );
  }

  Widget _buildAvatar(ColorScheme colorScheme, bool isUser) {
    return CircleAvatar(
      radius: 16,
      backgroundColor: isUser 
        ? colorScheme.primary
        : colorScheme.secondaryContainer,
      child: Icon(
        isUser ? Icons.person : Icons.psychology,
        size: 18,
        color: isUser 
          ? colorScheme.onPrimary
          : colorScheme.onSecondaryContainer,
      ),
    );
  }

  Widget _buildMessageContainer(ThemeData theme, ColorScheme colorScheme, bool isUser) {
    return GestureDetector(
      onLongPress: () => _copyToClipboard(theme),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isUser 
            ? colorScheme.primary
            : colorScheme.surfaceVariant,
          borderRadius: BorderRadius.circular(20).copyWith(
            bottomLeft: isUser ? const Radius.circular(20) : const Radius.circular(4),
            bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(20),
          ),
          boxShadow: [
            BoxShadow(
              color: colorScheme.shadow.withOpacity(0.1),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.text,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: isUser 
                  ? colorScheme.onPrimary
                  : colorScheme.onSurfaceVariant,
                height: 1.4,
              ),
            ),
            if (!isUser && onRetry != null && _isErrorMessage(message.text)) ...[
              const SizedBox(height: 8),
              _buildRetryButton(theme, colorScheme),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRetryButton(ThemeData theme, ColorScheme colorScheme) {
    return InkWell(
      onTap: onRetry,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: colorScheme.error.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: colorScheme.error.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.refresh,
              size: 16,
              color: colorScheme.error,
            ),
            const SizedBox(width: 4),
            Text(
              'Retry',
              style: theme.textTheme.bodySmall?.copyWith(
                color: colorScheme.error,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimestamp(ThemeData theme, bool isUser) {
    return Padding(
      padding: EdgeInsets.only(
        left: isUser ? 0 : 40,
        right: isUser ? 40 : 0,
      ),
      child: Text(
        _formatTimestamp(message.timestamp),
        style: theme.textTheme.bodySmall?.copyWith(
          color: theme.colorScheme.onSurface.withOpacity(0.6),
        ),
      ),
    );
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else {
      return '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}';
    }
  }

  bool _isErrorMessage(String text) {
    return text.contains('error') || 
           text.contains('failed') || 
           text.contains('Sorry, I encountered an error');
  }

  void _copyToClipboard(ThemeData theme) {
    Clipboard.setData(ClipboardData(text: message.text));
    // Note: In a real app, you'd show a snackbar here
    // ScaffoldMessenger.of(context).showSnackBar(...)
  }
}