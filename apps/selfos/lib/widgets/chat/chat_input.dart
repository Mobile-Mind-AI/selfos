import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Chat input widget for sending messages
class ChatInput extends ConsumerStatefulWidget {
  final Function(String) onSendMessage;
  final bool isLoading;
  final String? placeholder;

  const ChatInput({
    super.key,
    required this.onSendMessage,
    this.isLoading = false,
    this.placeholder,
  });

  @override
  ConsumerState<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends ConsumerState<ChatInput> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  bool _canSend = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_updateSendState);
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _updateSendState() {
    final canSend = _controller.text.trim().isNotEmpty && !widget.isLoading;
    if (_canSend != canSend) {
      setState(() {
        _canSend = canSend;
      });
    }
  }

  void _sendMessage() {
    if (_canSend) {
      final message = _controller.text.trim();
      _controller.clear();
      setState(() {
        _canSend = false;
      });
      widget.onSendMessage(message);
      _focusNode.requestFocus();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        border: Border(
          top: BorderSide(
            color: colorScheme.outline.withOpacity(0.2),
            width: 1,
          ),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                focusNode: _focusNode,
                maxLines: null,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: widget.placeholder ?? 'Ask me about your goals...',
                  hintStyle: TextStyle(
                    color: colorScheme.onSurface.withOpacity(0.6),
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(
                      color: colorScheme.outline.withOpacity(0.3),
                    ),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(
                      color: colorScheme.outline.withOpacity(0.3),
                    ),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(
                      color: colorScheme.primary,
                      width: 2,
                    ),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                  suffixIcon: widget.isLoading
                    ? Container(
                        width: 20,
                        height: 20,
                        padding: const EdgeInsets.all(12),
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            colorScheme.primary,
                          ),
                        ),
                      )
                    : null,
                ),
                onSubmitted: (_) => _sendMessage(),
                enabled: !widget.isLoading,
              ),
            ),
            const SizedBox(width: 8),
            FloatingActionButton.small(
              onPressed: _canSend ? _sendMessage : null,
              backgroundColor: _canSend 
                ? colorScheme.primary 
                : colorScheme.outline.withOpacity(0.3),
              foregroundColor: _canSend 
                ? colorScheme.onPrimary 
                : colorScheme.onSurface.withOpacity(0.5),
              elevation: _canSend ? 2 : 0,
              child: Icon(
                Icons.send,
                size: 20,
              ),
            ),
          ],
        ),
      ),
    );
  }
}