# UI Components Documentation

This document describes the reusable UI components in the SelfOS Flutter app.

## Overview

The app uses a consistent design system with reusable components for:
- Forms and inputs
- Buttons and actions
- Loading and error states
- Navigation and layout

All components follow Material Design 3 principles and support both light and dark themes.

## Form Components

### CustomTextField

A reusable text input field with validation and consistent styling.

**Features:**
- Multiple input types (email, password, text, etc.)
- Built-in validation
- Loading states
- Password visibility toggle
- Consistent theming

**Usage:**
```dart
CustomTextField(
  label: 'Email Address',
  hint: 'Enter your email',
  controller: _emailController,
  type: TextFieldType.email,
  isRequired: true,
  validator: FieldValidators.combine([
    (value) => FieldValidators.required(value, fieldName: 'Email'),
    FieldValidators.email,
  ]),
  onChanged: (value) => _updateEmail(value),
)
```

**Properties:**
- `label` (String) - Field label text
- `hint` (String?) - Placeholder text
- `controller` (TextEditingController?) - Text controller
- `type` (TextFieldType) - Input type (email, password, text, etc.)
- `validator` (String? Function(String?)?) - Validation function
- `isRequired` (bool) - Shows required indicator
- `enabled` (bool) - Enables/disables input
- `isLoading` (bool) - Shows loading state
- `maxLength` (int?) - Maximum input length
- `maxLines` (int?) - Number of lines (for multiline)
- `onChanged` (Function(String)?) - Text change callback
- `prefixIcon` (IconData?) - Icon before text
- `suffixIcon` (IconData?) - Icon after text

**Input Types:**
- `TextFieldType.text` - Regular text
- `TextFieldType.email` - Email with keyboard and validation
- `TextFieldType.password` - Password with visibility toggle
- `TextFieldType.phone` - Phone number input
- `TextFieldType.number` - Numeric input
- `TextFieldType.multiline` - Multi-line text
- `TextFieldType.url` - URL input

### FieldValidators

Utility class providing common validation functions.

**Available Validators:**
```dart
// Required field
FieldValidators.required(value, fieldName: 'Email')

// Email format
FieldValidators.email(value)

// Password strength
FieldValidators.password(value, minLength: 8)

// Password confirmation
FieldValidators.confirmPassword(value, originalPassword)

// Length validation
FieldValidators.minLength(value, 3, fieldName: 'Name')
FieldValidators.maxLength(value, 100, fieldName: 'Description')

// Combine multiple validators
FieldValidators.combine([
  (value) => FieldValidators.required(value),
  FieldValidators.email,
  (value) => FieldValidators.minLength(value, 5),
])
```

## Button Components

### CustomButton

A reusable button component with consistent styling and loading states.

**Features:**
- Multiple button variants
- Loading states with spinner
- Icon support
- Disabled state handling
- Consistent theming

**Usage:**
```dart
CustomButton(
  text: 'Sign In',
  onPressed: _handleSignIn,
  isLoading: _isLoading,
  variant: ButtonVariant.primary,
  icon: Icons.login,
  width: double.infinity,
)
```

**Properties:**
- `text` (String) - Button text
- `onPressed` (VoidCallback?) - Press callback
- `isLoading` (bool) - Shows loading spinner
- `variant` (ButtonVariant) - Button style variant
- `icon` (IconData?) - Optional icon
- `width` (double?) - Button width
- `height` (double) - Button height
- `loadingColor` (Color?) - Loading spinner color

**Button Variants:**
- `ButtonVariant.primary` - Filled primary button
- `ButtonVariant.secondary` - Filled secondary button
- `ButtonVariant.outlined` - Outlined button
- `ButtonVariant.text` - Text-only button

### SocialButton

Specialized button for social login providers.

**Usage:**
```dart
SocialButton(
  provider: SocialProvider.google,
  onPressed: _handleGoogleLogin,
  isLoading: _isLoading,
  width: double.infinity,
)
```

**Supported Providers:**
- `SocialProvider.google` - Google Sign-In
- `SocialProvider.apple` - Apple Sign-In
- `SocialProvider.facebook` - Facebook Login
- `SocialProvider.github` - GitHub OAuth

## Loading and State Components

### LoadingOverlay

Full-screen loading overlay with optional message.

**Usage:**
```dart
LoadingOverlay(
  isLoading: _isLoading,
  message: 'Signing in...',
  child: YourContentWidget(),
)
```

**Properties:**
- `child` (Widget) - Content behind overlay
- `isLoading` (bool) - Whether to show overlay
- `message` (String?) - Loading message
- `indicatorColor` (Color?) - Spinner color
- `backgroundColor` (Color?) - Overlay background

### LoadingIndicator

Inline loading indicator with optional message.

**Usage:**
```dart
LoadingIndicator(
  message: 'Loading...',
  size: 32,
  vertical: true,
)
```

**Properties:**
- `message` (String?) - Loading message
- `size` (double) - Indicator size
- `color` (Color?) - Indicator color
- `vertical` (bool) - Layout direction

### ErrorDisplay

Error message display with optional retry button.

**Usage:**
```dart
ErrorDisplay(
  message: 'Something went wrong',
  onRetry: _handleRetry,
  icon: Icons.error_outline,
)
```

**Properties:**
- `message` (String) - Error message
- `onRetry` (VoidCallback?) - Retry callback
- `retryText` (String) - Retry button text
- `icon` (IconData) - Error icon

### EmptyState

Empty state display with icon and optional action.

**Usage:**
```dart
EmptyState(
  message: 'No items found',
  subtitle: 'Try adjusting your search',
  icon: Icons.inbox_outlined,
  actionText: 'Refresh',
  onAction: _handleRefresh,
)
```

**Properties:**
- `message` (String) - Main message
- `subtitle` (String?) - Secondary message
- `icon` (IconData) - Empty state icon
- `actionText` (String?) - Action button text
- `onAction` (VoidCallback?) - Action callback

## Usage Examples

### Login Form

```dart
class LoginForm extends StatefulWidget {
  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          CustomTextField(
            label: 'Email',
            controller: _emailController,
            type: TextFieldType.email,
            isRequired: true,
            validator: FieldValidators.combine([
              (value) => FieldValidators.required(value, fieldName: 'Email'),
              FieldValidators.email,
            ]),
          ),
          
          const SizedBox(height: 16),
          
          CustomTextField(
            label: 'Password',
            controller: _passwordController,
            type: TextFieldType.password,
            isRequired: true,
            validator: (value) => FieldValidators.required(value, fieldName: 'Password'),
          ),
          
          const SizedBox(height: 24),
          
          CustomButton(
            text: 'Sign In',
            onPressed: _handleLogin,
            isLoading: _isLoading,
            width: double.infinity,
          ),
          
          const SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(
                child: SocialButton(
                  provider: SocialProvider.google,
                  onPressed: _handleGoogleLogin,
                  isLoading: _isLoading,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: SocialButton(
                  provider: SocialProvider.apple,
                  onPressed: _handleAppleLogin,
                  isLoading: _isLoading,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      // Perform login
      await AuthService.login(
        email: _emailController.text,
        password: _passwordController.text,
      );
    } catch (error) {
      // Handle error
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }
}
```

### Error Handling Screen

```dart
class ErrorScreen extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const ErrorScreen({
    super.key,
    required this.message,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ErrorDisplay(
        message: message,
        onRetry: onRetry,
      ),
    );
  }
}
```

### Loading States

```dart
class DataScreen extends StatefulWidget {
  @override
  State<DataScreen> createState() => _DataScreenState();
}

class _DataScreenState extends State<DataScreen> {
  bool _isLoading = true;
  String? _error;
  List<DataItem>? _data;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: LoadingOverlay(
        isLoading: _isLoading,
        message: 'Loading data...',
        child: _buildContent(),
      ),
    );
  }

  Widget _buildContent() {
    if (_error != null) {
      return ErrorDisplay(
        message: _error!,
        onRetry: _loadData,
      );
    }

    if (_data?.isEmpty == true) {
      return EmptyState(
        message: 'No data available',
        subtitle: 'Try refreshing to load data',
        actionText: 'Refresh',
        onAction: _loadData,
      );
    }

    return ListView.builder(
      itemCount: _data?.length ?? 0,
      itemBuilder: (context, index) => DataItemWidget(_data![index]),
    );
  }
}
```

## Theming and Customization

### Component Theming

Components automatically adapt to the app's theme:

```dart
// Light theme
ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: Colors.blue,
    brightness: Brightness.light,
  ),
  // Component themes will be applied automatically
)

// Dark theme
ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: Colors.blue,
    brightness: Brightness.dark,
  ),
  // Component themes will be applied automatically
)
```

### Custom Colors

Override component colors when needed:

```dart
CustomButton(
  text: 'Custom Button',
  onPressed: _handlePress,
  // Custom styling through theme variants
  variant: ButtonVariant.primary,
)

CustomTextField(
  label: 'Custom Field',
  // Colors come from theme automatically
  // Override in theme if needed
)
```

## Best Practices

### Validation

1. **Combine validators** for complex requirements:
```dart
validator: FieldValidators.combine([
  (value) => FieldValidators.required(value),
  FieldValidators.email,
  (value) => FieldValidators.minLength(value, 5),
])
```

2. **Use descriptive field names**:
```dart
validator: (value) => FieldValidators.required(value, fieldName: 'Email Address')
```

3. **Real-time validation** for better UX:
```dart
CustomTextField(
  onChanged: (value) => _validateField(value),
  validator: _fieldValidator,
)
```

### Loading States

1. **Use appropriate loading indicators**:
   - `LoadingOverlay` for full-screen operations
   - `LoadingIndicator` for inline loading
   - Button loading states for actions

2. **Provide meaningful messages**:
```dart
LoadingOverlay(
  isLoading: true,
  message: 'Creating your account...',
  child: content,
)
```

### Error Handling

1. **User-friendly error messages**:
```dart
ErrorDisplay(
  message: 'Unable to sign in. Please check your credentials.',
  onRetry: _handleRetry,
)
```

2. **Consistent error display**:
   - Use `ErrorDisplay` for inline errors
   - Use `SnackBar` for temporary messages
   - Use error screens for critical failures

### Accessibility

Components include built-in accessibility features:
- Semantic labels
- Screen reader support
- Keyboard navigation
- High contrast support

Ensure you provide meaningful labels:
```dart
CustomTextField(
  label: 'Email Address', // Used for accessibility
  hint: 'Enter your email address', // Additional context
)
```