import 'package:flutter/material.dart';

/// Custom button widget with consistent styling and loading states
/// 
/// This widget provides a reusable button component with:
/// - Consistent styling across the app
/// - Loading state with spinner
/// - Disabled state handling
/// - Multiple button variants (primary, secondary, outlined)
/// - Icon support
/// 
/// Usage:
/// ```dart
/// CustomButton(
///   text: 'Sign In',
///   onPressed: () => _handleLogin(),
///   isLoading: _isLoading,
/// )
/// ```
class CustomButton extends StatelessWidget {
  /// Button text
  final String text;
  
  /// Callback when button is pressed
  final VoidCallback? onPressed;
  
  /// Whether button is in loading state
  final bool isLoading;
  
  /// Button variant
  final ButtonVariant variant;
  
  /// Optional icon
  final IconData? icon;
  
  /// Button width (null for auto width)
  final double? width;
  
  /// Button height
  final double height;
  
  /// Loading indicator color
  final Color? loadingColor;

  const CustomButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.variant = ButtonVariant.primary,
    this.icon,
    this.width,
    this.height = 48.0,
    this.loadingColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDisabled = onPressed == null || isLoading;

    Widget child = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (isLoading) ...[
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: loadingColor ?? _getLoadingColor(theme),
            ),
          ),
          const SizedBox(width: 8),
        ] else if (icon != null) ...[
          Icon(icon, size: 18),
          const SizedBox(width: 8),
        ],
        Text(
          text,
          style: _getTextStyle(theme),
        ),
      ],
    );

    Widget button;
    switch (variant) {
      case ButtonVariant.primary:
        button = ElevatedButton(
          onPressed: isDisabled ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: theme.colorScheme.primary,
            foregroundColor: theme.colorScheme.onPrimary,
            disabledBackgroundColor: theme.colorScheme.primary.withOpacity(0.5),
            disabledForegroundColor: theme.colorScheme.onPrimary.withOpacity(0.5),
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
          child: child,
        );
        break;

      case ButtonVariant.secondary:
        button = ElevatedButton(
          onPressed: isDisabled ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: theme.colorScheme.secondary,
            foregroundColor: theme.colorScheme.onSecondary,
            disabledBackgroundColor: theme.colorScheme.secondary.withOpacity(0.5),
            disabledForegroundColor: theme.colorScheme.onSecondary.withOpacity(0.5),
            elevation: 1,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
          child: child,
        );
        break;

      case ButtonVariant.outlined:
        button = OutlinedButton(
          onPressed: isDisabled ? null : onPressed,
          style: OutlinedButton.styleFrom(
            foregroundColor: theme.colorScheme.primary,
            disabledForegroundColor: theme.colorScheme.primary.withOpacity(0.5),
            side: BorderSide(
              color: isDisabled 
                ? theme.colorScheme.primary.withOpacity(0.5)
                : theme.colorScheme.primary,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
          child: child,
        );
        break;

      case ButtonVariant.text:
        button = TextButton(
          onPressed: isDisabled ? null : onPressed,
          style: TextButton.styleFrom(
            foregroundColor: theme.colorScheme.primary,
            disabledForegroundColor: theme.colorScheme.primary.withOpacity(0.5),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
          child: child,
        );
        break;
    }

    return SizedBox(
      width: width,
      height: height,
      child: button,
    );
  }

  TextStyle _getTextStyle(ThemeData theme) {
    return theme.textTheme.labelLarge?.copyWith(
      fontWeight: FontWeight.w600,
    ) ?? const TextStyle(fontWeight: FontWeight.w600);
  }

  Color _getLoadingColor(ThemeData theme) {
    switch (variant) {
      case ButtonVariant.primary:
      case ButtonVariant.secondary:
        return theme.colorScheme.onPrimary;
      case ButtonVariant.outlined:
      case ButtonVariant.text:
        return theme.colorScheme.primary;
    }
  }
}

/// Button variants for different styles
enum ButtonVariant {
  /// Primary button with filled background
  primary,
  
  /// Secondary button with filled background
  secondary,
  
  /// Outlined button with border
  outlined,
  
  /// Text button without background
  text,
}

