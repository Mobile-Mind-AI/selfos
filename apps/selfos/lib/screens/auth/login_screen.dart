import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../models/auth_request.dart';
import '../../services/auth_provider.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/loading_overlay.dart';
import '../../widgets/common/social_button.dart';

/// Login screen for user authentication
/// 
/// This screen provides email/password login functionality with:
/// - Form validation
/// - Loading states
/// - Error handling
/// - Social login options
/// - Password reset option
/// - Navigation to registration
/// 
/// The screen uses Riverpod for state management and automatically
/// handles authentication flow including token storage.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();

  bool _rememberMe = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final authState = ref.watch(authProvider);
    final isLoading = authState is AuthStateLoading;
    final errorMessage = authState is AuthStateError ? authState.message : null;

    return Scaffold(
      body: LoadingOverlay(
        isLoading: isLoading,
        message: authState is AuthStateLoading ? authState.message : null,
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                physics: const ClampingScrollPhysics(),
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minHeight: constraints.maxHeight,
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const SizedBox(height: 4),
                  
                          // App logo/title
                          _buildHeader(theme),
                  
                          const SizedBox(height: 16),
                  
                          // Login form
                          _buildLoginForm(),
                  
                          const SizedBox(height: 8),
                  
                          // Remember me and forgot password
                          _buildFormOptions(theme),
                  
                          const SizedBox(height: 12),
                  
                          // Login button
                          _buildLoginButton(),
                  
                          const SizedBox(height: 6),
                  
                  // Error message
                  if (errorMessage != null) _buildErrorMessage(theme, errorMessage),
                  
                  const SizedBox(height: 16),
                  
                  // Social login section
                  _buildSocialLogin(),
                  
                  const SizedBox(height: 16),
                  
                  // Sign up link
                  _buildSignUpLink(theme),
                  
                  const SizedBox(height: 8),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme) {
    return Column(
      children: [
        // App icon/logo placeholder
        Container(
          width: 70,
          height: 70,
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(18),
          ),
          child: Icon(
            Icons.psychology,
            size: 36,
            color: theme.colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),
        
        Text(
          'Welcome to SelfOS',
          style: theme.textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.onSurface,
          ),
        ),
        const SizedBox(height: 6),
        
        Text(
          'Sign in to continue your personal growth journey',
          style: theme.textTheme.bodyLarge?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildLoginForm() {
    return Column(
      children: [
        // Email field
        CustomTextField(
          label: 'Email',
          hint: 'Enter your email address',
          controller: _emailController,
          focusNode: _emailFocusNode,
          type: TextFieldType.email,
          textInputAction: TextInputAction.next,
          prefixIcon: Icons.email_outlined,
          isRequired: true,
          validator: FieldValidators.combine([
            (value) => FieldValidators.required(value, fieldName: 'Email'),
            FieldValidators.email,
          ]),
          onSubmitted: (_) => _passwordFocusNode.requestFocus(),
        ),
        
        const SizedBox(height: 16),
        
        // Password field
        CustomTextField(
          label: 'Password',
          hint: 'Enter your password',
          controller: _passwordController,
          focusNode: _passwordFocusNode,
          type: TextFieldType.password,
          textInputAction: TextInputAction.done,
          prefixIcon: Icons.lock_outlined,
          isRequired: true,
          validator: (value) => FieldValidators.required(value, fieldName: 'Password'),
          onSubmitted: (_) => _handleLogin(),
        ),
      ],
    );
  }

  Widget _buildFormOptions(ThemeData theme) {
    return Row(
      children: [
        // Remember me checkbox
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Checkbox(
              value: _rememberMe,
              onChanged: (value) {
                setState(() {
                  _rememberMe = value ?? false;
                });
              },
            ),
            Text(
              'Remember me',
              style: theme.textTheme.bodyMedium,
            ),
          ],
        ),
        
        const Spacer(),
        
        // Forgot password link
        TextButton(
          onPressed: _handleForgotPassword,
          child: Text(
            'Forgot Password?',
            style: TextStyle(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLoginButton() {
    return CustomButton(
      text: 'Sign In',
      onPressed: _handleLogin,
      isLoading: ref.watch(authLoadingProvider),
      icon: Icons.login,
    );
  }

  Widget _buildErrorMessage(ThemeData theme, String errorMessage) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: theme.colorScheme.error.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.error_outline,
            color: theme.colorScheme.error,
            size: 20,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              errorMessage,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.error,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSocialLogin() {
    return SocialLoginSection(
      providers: const [SocialProvider.google, SocialProvider.apple],
      onProviderTap: _handleSocialLogin,
      isLoading: ref.watch(authLoadingProvider),
      dividerText: 'or continue with',
    );
  }

  Widget _buildSignUpLink(ThemeData theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          "Don't have an account? ",
          style: theme.textTheme.bodyMedium,
        ),
        TextButton(
          onPressed: _handleSignUp,
          child: Text(
            'Sign Up',
            style: TextStyle(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _handleLogin() async {
    // Clear any previous errors
    ref.read(authProvider.notifier).clearError();
    
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final email = _emailController.text.trim();
    final password = _passwordController.text;

    final loginRequest = LoginRequest.emailPassword(
      email: email,
      password: password,
    );

    final success = await ref.read(authProvider.notifier).login(loginRequest);
    
    if (success && mounted) {
      // Let GoRouter handle the redirect automatically based on auth state
      // The router will redirect to home when it detects authenticated state
      if (kDebugMode) {
        print('🔐 LOGIN: Login successful, waiting for router redirect...');
      }
    }
  }

  void _handleForgotPassword() {
    // Show forgot password dialog or navigate to forgot password screen
    showDialog(
      context: context,
      builder: (context) => _ForgotPasswordDialog(),
    );
  }

  Future<void> _handleSocialLogin(SocialProvider provider) async {
    // Clear any previous errors
    ref.read(authProvider.notifier).clearError();
    
    bool success = false;
    
    try {
      switch (provider) {
        case SocialProvider.google:
          success = await ref.read(authProvider.notifier).signInWithGoogle();
          break;
        case SocialProvider.apple:
          success = await ref.read(authProvider.notifier).signInWithApple();
          break;
      }
      
      if (success && mounted) {
        // Let GoRouter handle the redirect automatically based on auth state
        if (kDebugMode) {
          print('🔐 SOCIAL_LOGIN: Social login successful, waiting for router redirect...');
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${provider.displayName} Sign-In failed: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _handleSignUp() {
    // Navigate to sign up screen
    context.go('/signup');
  }
}

/// Forgot password dialog
class _ForgotPasswordDialog extends ConsumerStatefulWidget {
  @override
  ConsumerState<_ForgotPasswordDialog> createState() => _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends ConsumerState<_ForgotPasswordDialog> {
  final _emailController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return AlertDialog(
      title: const Text('Reset Password'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Enter your email address and we\'ll send you a link to reset your password.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            CustomTextField(
              label: 'Email',
              hint: 'Enter your email address',
              controller: _emailController,
              type: TextFieldType.email,
              isRequired: true,
              validator: FieldValidators.combine([
                (value) => FieldValidators.required(value, fieldName: 'Email'),
                FieldValidators.email,
              ]),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        CustomButton(
          text: 'Send Reset Link',
          onPressed: _handlePasswordReset,
          isLoading: ref.watch(authLoadingProvider),
          variant: ButtonVariant.text,
        ),
      ],
    );
  }

  Future<void> _handlePasswordReset() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final email = _emailController.text.trim();
    final success = await ref.read(authProvider.notifier).requestPasswordReset(email);
    
    if (mounted) {
      Navigator.of(context).pop();
      
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Password reset link sent to your email'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        final errorMessage = ref.read(authErrorProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage ?? 'Failed to send reset link'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}