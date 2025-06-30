import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Custom text field widget with validation and consistent styling
/// 
/// This widget provides a reusable text input component with:
/// - Consistent styling across the app
/// - Built-in validation support
/// - Password visibility toggle
/// - Various input types (email, password, etc.)
/// - Error state handling
/// - Loading state
/// 
/// Usage:
/// ```dart
/// CustomTextField(
///   label: 'Email',
///   hint: 'Enter your email',
///   controller: _emailController,
///   type: TextFieldType.email,
///   validator: (value) => value?.isEmpty == true ? 'Email is required' : null,
/// )
/// ```
class CustomTextField extends StatefulWidget {
  /// Text field label
  final String label;
  
  /// Placeholder text
  final String? hint;
  
  /// Text controller
  final TextEditingController? controller;
  
  /// Initial value (if controller is not provided)
  final String? initialValue;
  
  /// Text field type
  final TextFieldType type;
  
  /// Validation function
  final String? Function(String?)? validator;
  
  /// Whether field is required
  final bool isRequired;
  
  /// Whether field is enabled
  final bool enabled;
  
  /// Whether field is in loading state
  final bool isLoading;
  
  /// Maximum length of input
  final int? maxLength;
  
  /// Maximum number of lines
  final int? maxLines;
  
  /// Callback when text changes
  final void Function(String)? onChanged;
  
  /// Callback when editing is complete
  final void Function(String)? onSubmitted;
  
  /// Focus node
  final FocusNode? focusNode;
  
  /// Text input action
  final TextInputAction? textInputAction;
  
  /// Prefix icon
  final IconData? prefixIcon;
  
  /// Suffix icon
  final IconData? suffixIcon;
  
  /// Suffix icon callback
  final VoidCallback? onSuffixIconPressed;

  const CustomTextField({
    super.key,
    required this.label,
    this.hint,
    this.controller,
    this.initialValue,
    this.type = TextFieldType.text,
    this.validator,
    this.isRequired = false,
    this.enabled = true,
    this.isLoading = false,
    this.maxLength,
    this.maxLines = 1,
    this.onChanged,
    this.onSubmitted,
    this.focusNode,
    this.textInputAction,
    this.prefixIcon,
    this.suffixIcon,
    this.onSuffixIconPressed,
  });

  @override
  State<CustomTextField> createState() => _CustomTextFieldState();
}

class _CustomTextFieldState extends State<CustomTextField> {
  bool _isObscured = true;
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController(text: widget.initialValue);
  }

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Label
        RichText(
          text: TextSpan(
            text: widget.label,
            style: theme.textTheme.labelMedium?.copyWith(
              fontWeight: FontWeight.w500,
              color: theme.colorScheme.onSurface,
            ),
            children: [
              if (widget.isRequired)
                TextSpan(
                  text: ' *',
                  style: TextStyle(color: theme.colorScheme.error),
                ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        
        // Text field
        TextFormField(
          controller: _controller,
          focusNode: widget.focusNode,
          enabled: widget.enabled && !widget.isLoading,
          obscureText: widget.type == TextFieldType.password && _isObscured,
          keyboardType: _getKeyboardType(),
          textInputAction: widget.textInputAction ?? _getDefaultInputAction(),
          maxLength: widget.maxLength,
          maxLines: widget.maxLines,
          inputFormatters: _getInputFormatters(),
          validator: widget.validator,
          onChanged: widget.onChanged,
          onFieldSubmitted: widget.onSubmitted,
          style: theme.textTheme.bodyLarge,
          decoration: InputDecoration(
            hintText: widget.hint,
            hintStyle: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
            prefixIcon: widget.prefixIcon != null
                ? Icon(
                    widget.prefixIcon,
                    color: theme.colorScheme.onSurface.withOpacity(0.7),
                  )
                : null,
            suffixIcon: _buildSuffixIcon(theme),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(
                color: theme.colorScheme.outline,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(
                color: theme.colorScheme.outline,
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(
                color: theme.colorScheme.primary,
                width: 2,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(
                color: theme.colorScheme.error,
              ),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(
                color: theme.colorScheme.error,
                width: 2,
              ),
            ),
            disabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(
                color: theme.colorScheme.outline.withOpacity(0.5),
              ),
            ),
            filled: true,
            fillColor: widget.enabled && !widget.isLoading
                ? theme.colorScheme.surface
                : theme.colorScheme.surface.withOpacity(0.5),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 12,
            ),
            counterText: '', // Hide character counter
          ),
        ),
        
        // Loading indicator
        if (widget.isLoading)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: LinearProgressIndicator(
              backgroundColor: theme.colorScheme.surface,
              valueColor: AlwaysStoppedAnimation(theme.colorScheme.primary),
            ),
          ),
      ],
    );
  }

  Widget? _buildSuffixIcon(ThemeData theme) {
    if (widget.isLoading) {
      return Padding(
        padding: const EdgeInsets.all(12),
        child: SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            color: theme.colorScheme.primary,
          ),
        ),
      );
    }

    if (widget.type == TextFieldType.password) {
      return IconButton(
        icon: Icon(
          _isObscured ? Icons.visibility : Icons.visibility_off,
          color: theme.colorScheme.onSurface.withOpacity(0.7),
        ),
        onPressed: () {
          setState(() {
            _isObscured = !_isObscured;
          });
        },
      );
    }

    if (widget.suffixIcon != null) {
      return IconButton(
        icon: Icon(
          widget.suffixIcon,
          color: theme.colorScheme.onSurface.withOpacity(0.7),
        ),
        onPressed: widget.onSuffixIconPressed,
      );
    }

    return null;
  }

  TextInputType _getKeyboardType() {
    switch (widget.type) {
      case TextFieldType.email:
        return TextInputType.emailAddress;
      case TextFieldType.password:
        return TextInputType.visiblePassword;
      case TextFieldType.phone:
        return TextInputType.phone;
      case TextFieldType.number:
        return TextInputType.number;
      case TextFieldType.multiline:
        return TextInputType.multiline;
      case TextFieldType.url:
        return TextInputType.url;
      case TextFieldType.text:
      default:
        return TextInputType.text;
    }
  }

  TextInputAction _getDefaultInputAction() {
    if (widget.maxLines != null && widget.maxLines! > 1) {
      return TextInputAction.newline;
    }
    return TextInputAction.next;
  }

  List<TextInputFormatter>? _getInputFormatters() {
    switch (widget.type) {
      case TextFieldType.phone:
        return [FilteringTextInputFormatter.digitsOnly];
      case TextFieldType.number:
        return [FilteringTextInputFormatter.digitsOnly];
      default:
        return null;
    }
  }
}

/// Text field types for different input scenarios
enum TextFieldType {
  /// Regular text input
  text,
  
  /// Email address input
  email,
  
  /// Password input (with visibility toggle)
  password,
  
  /// Phone number input
  phone,
  
  /// Numeric input
  number,
  
  /// Multi-line text input
  multiline,
  
  /// URL input
  url,
}

/// Validation utility class for common validations
class FieldValidators {
  /// Validates required fields
  static String? required(String? value, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) {
      return '${fieldName ?? 'This field'} is required';
    }
    return null;
  }

  /// Validates email format
  static String? email(String? value) {
    if (value == null || value.isEmpty) return null;
    
    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!emailRegex.hasMatch(value)) {
      return 'Please enter a valid email address';
    }
    return null;
  }

  /// Validates password strength
  static String? password(String? value, {int minLength = 8}) {
    if (value == null || value.isEmpty) return null;
    
    if (value.length < minLength) {
      return 'Password must be at least $minLength characters';
    }
    
    if (!value.contains(RegExp(r'[A-Z]'))) {
      return 'Password must contain at least one uppercase letter';
    }
    
    if (!value.contains(RegExp(r'[a-z]'))) {
      return 'Password must contain at least one lowercase letter';
    }
    
    if (!value.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain at least one number';
    }
    
    return null;
  }

  /// Validates password confirmation
  static String? confirmPassword(String? value, String? originalPassword) {
    if (value == null || value.isEmpty) return null;
    
    if (value != originalPassword) {
      return 'Passwords do not match';
    }
    return null;
  }

  /// Validates minimum length
  static String? minLength(String? value, int minLength, {String? fieldName}) {
    if (value == null || value.isEmpty) return null;
    
    if (value.length < minLength) {
      return '${fieldName ?? 'This field'} must be at least $minLength characters';
    }
    return null;
  }

  /// Validates maximum length
  static String? maxLength(String? value, int maxLength, {String? fieldName}) {
    if (value == null || value.isEmpty) return null;
    
    if (value.length > maxLength) {
      return '${fieldName ?? 'This field'} must be no more than $maxLength characters';
    }
    return null;
  }

  /// Combines multiple validators
  static String? Function(String?) combine(List<String? Function(String?)> validators) {
    return (String? value) {
      for (final validator in validators) {
        final result = validator(value);
        if (result != null) return result;
      }
      return null;
    };
  }
}