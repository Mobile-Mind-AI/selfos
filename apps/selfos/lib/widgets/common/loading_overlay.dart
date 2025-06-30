import 'package:flutter/material.dart';

/// Loading overlay widget for full-screen loading states
/// 
/// This widget provides a consistent loading overlay that can be shown
/// over any content. It includes a semi-transparent background with
/// a centered loading indicator and optional message.
/// 
/// Usage:
/// ```dart
/// LoadingOverlay(
///   isLoading: _isLoading,
///   message: 'Signing in...',
///   child: YourContentWidget(),
/// )
/// ```
class LoadingOverlay extends StatelessWidget {
  /// Child widget to show behind the overlay
  final Widget child;
  
  /// Whether to show the loading overlay
  final bool isLoading;
  
  /// Optional loading message
  final String? message;
  
  /// Loading indicator color
  final Color? indicatorColor;
  
  /// Background overlay color
  final Color? backgroundColor;

  const LoadingOverlay({
    super.key,
    required this.child,
    required this.isLoading,
    this.message,
    this.indicatorColor,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Stack(
      children: [
        child,
        if (isLoading)
          Container(
            color: backgroundColor ?? Colors.black.withOpacity(0.5),
            child: Center(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(
                        color: indicatorColor ?? theme.colorScheme.primary,
                      ),
                      if (message != null) ...[
                        const SizedBox(height: 16),
                        Text(
                          message!,
                          style: theme.textTheme.bodyMedium,
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

/// Simple loading indicator widget
/// 
/// A reusable loading indicator with optional message for inline use.
class LoadingIndicator extends StatelessWidget {
  /// Loading message to display
  final String? message;
  
  /// Size of the loading indicator
  final double size;
  
  /// Color of the loading indicator
  final Color? color;
  
  /// Whether to show message below or beside indicator
  final bool vertical;

  const LoadingIndicator({
    super.key,
    this.message,
    this.size = 24,
    this.color,
    this.vertical = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    final indicator = SizedBox(
      width: size,
      height: size,
      child: CircularProgressIndicator(
        strokeWidth: size / 12,
        color: color ?? theme.colorScheme.primary,
      ),
    );

    if (message == null) {
      return indicator;
    }

    final text = Text(
      message!,
      style: theme.textTheme.bodyMedium,
      textAlign: TextAlign.center,
    );

    if (vertical) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          indicator,
          const SizedBox(height: 8),
          text,
        ],
      );
    } else {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          indicator,
          const SizedBox(width: 8),
          text,
        ],
      );
    }
  }
}

/// Error display widget with retry option
/// 
/// Shows error messages with optional retry button.
class ErrorDisplay extends StatelessWidget {
  /// Error message to display
  final String message;
  
  /// Optional retry callback
  final VoidCallback? onRetry;
  
  /// Retry button text
  final String retryText;
  
  /// Error icon
  final IconData icon;

  const ErrorDisplay({
    super.key,
    required this.message,
    this.onRetry,
    this.retryText = 'Retry',
    this.icon = Icons.error_outline,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 48,
              color: theme.colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              message,
              style: theme.textTheme.bodyLarge,
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: onRetry,
                child: Text(retryText),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Empty state widget
/// 
/// Shows empty state with icon, message, and optional action.
class EmptyState extends StatelessWidget {
  /// Empty state message
  final String message;
  
  /// Optional subtitle
  final String? subtitle;
  
  /// Empty state icon
  final IconData icon;
  
  /// Optional action button text
  final String? actionText;
  
  /// Optional action callback
  final VoidCallback? onAction;

  const EmptyState({
    super.key,
    required this.message,
    this.subtitle,
    this.icon = Icons.inbox_outlined,
    this.actionText,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 64,
              color: theme.colorScheme.onSurface.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            Text(
              message,
              style: theme.textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            if (subtitle != null) ...[
              const SizedBox(height: 8),
              Text(
                subtitle!,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
                textAlign: TextAlign.center,
              ),
            ],
            if (actionText != null && onAction != null) ...[
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: onAction,
                child: Text(actionText!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}