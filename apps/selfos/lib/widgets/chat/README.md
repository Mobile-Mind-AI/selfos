# Chat Widgets

This directory contains reusable UI components for the chat interface.

## Components

### ChatInput
- Text input field for sending messages to the AI
- Loading states and send button
- Auto-focus and keyboard handling
- Customizable placeholder text

### MessageBubble
- Message display component for both user and AI messages
- Timestamp display with smart formatting
- Retry functionality for failed messages
- Copy to clipboard support
- Error state handling

## Usage

These components are designed to work together to create a complete chat interface. They integrate with the chat provider for state management and API communication.

```dart
// Example usage in chat screen
ChatInput(
  onSendMessage: (message) => chatNotifier.sendMessage(message),
  isLoading: isLoading,
  placeholder: 'Ask me anything...',
)

MessageBubble(
  message: chatMessage,
  showTimestamp: true,
  onRetry: () => chatNotifier.retryLastMessage(),
)
```