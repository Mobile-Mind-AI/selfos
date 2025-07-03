import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/auth_request.dart';
import '../../services/auth_provider.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/loading_overlay.dart';
import '../../widgets/common/social_button.dart';

/// Signup screen for user registration
/// 
/// This screen provides user registration functionality with:
/// - Email/password registration
/// - Form validation with password strength checking
/// - Terms and conditions acceptance
/// - Loading states and error handling
/// - Social registration options
/// - Navigation to login screen
/// 
/// The screen validates password strength and confirms password match
/// before submitting the registration request.
class SignupScreen extends ConsumerStatefulWidget {
  const SignupScreen({super.key});

  @override
  ConsumerState<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends ConsumerState<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _displayNameController = TextEditingController();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();
  final _confirmPasswordFocusNode = FocusNode();
  final _displayNameFocusNode = FocusNode();

  bool _acceptTerms = false;
  bool _acceptPrivacy = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _displayNameController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    _confirmPasswordFocusNode.dispose();
    _displayNameFocusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final authState = ref.watch(authProvider);
    final isLoading = authState is AuthStateLoading;
    final errorMessage = authState is AuthStateError ? authState.message : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sign Up'),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
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
                    padding: const EdgeInsets.all(24),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Header
                  _buildHeader(theme),
                  
                  const SizedBox(height: 24),
                  
                  // Registration form
                  _buildRegistrationForm(),
                  
                  const SizedBox(height: 16),
                  
                  // Terms and conditions
                  _buildTermsSection(theme),
                  
                  const SizedBox(height: 20),
                  
                  // Sign up button
                  _buildSignUpButton(),
                  
                  const SizedBox(height: 12),
                  
                  // Error message
                  if (errorMessage != null) _buildErrorMessage(theme, errorMessage),
                  
                  const SizedBox(height: 20),
                  
                  // Social registration section
                  _buildSocialSignup(),
                  
                  const SizedBox(height: 20),
                  
                  // Sign in link
                  _buildSignInLink(theme),
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
        Text(
          'Create Account',
          style: theme.textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.onSurface,
          ),
        ),
        const SizedBox(height: 8),
        
        Text(
          'Join SelfOS to start your personal growth journey',
          style: theme.textTheme.bodyLarge?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildRegistrationForm() {
    return Column(
      children: [
        // Display name field
        CustomTextField(
          label: 'Display Name',
          hint: 'Enter your display name (optional)',
          controller: _displayNameController,
          focusNode: _displayNameFocusNode,
          type: TextFieldType.text,
          textInputAction: TextInputAction.next,
          prefixIcon: Icons.person_outlined,
          validator: (value) {
            if (value != null && value.isNotEmpty && value.trim().length < 2) {
              return 'Display name must be at least 2 characters';
            }
            return null;
          },
          onSubmitted: (_) => _emailFocusNode.requestFocus(),
        ),
        
        const SizedBox(height: 16),
        
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
          hint: 'Create a strong password',
          controller: _passwordController,
          focusNode: _passwordFocusNode,
          type: TextFieldType.password,
          textInputAction: TextInputAction.next,
          prefixIcon: Icons.lock_outlined,
          isRequired: true,
          validator: FieldValidators.combine([
            (value) => FieldValidators.required(value, fieldName: 'Password'),
            FieldValidators.password,
          ]),
          onSubmitted: (_) => _confirmPasswordFocusNode.requestFocus(),
        ),
        
        const SizedBox(height: 8),
        
        // Password strength indicator
        _buildPasswordStrengthIndicator(),
        
        const SizedBox(height: 16),
        
        // Confirm password field
        CustomTextField(
          label: 'Confirm Password',
          hint: 'Re-enter your password',
          controller: _confirmPasswordController,
          focusNode: _confirmPasswordFocusNode,
          type: TextFieldType.password,
          textInputAction: TextInputAction.done,
          prefixIcon: Icons.lock_outlined,
          isRequired: true,
          validator: FieldValidators.combine([
            (value) => FieldValidators.required(value, fieldName: 'Confirm Password'),
            (value) => FieldValidators.confirmPassword(value, _passwordController.text),
          ]),
          onSubmitted: (_) => _handleSignUp(),
        ),
      ],
    );
  }

  Widget _buildPasswordStrengthIndicator() {
    final password = _passwordController.text;
    final strength = _getPasswordStrength(password);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              'Password strength: ',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              strength.label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: strength.color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        LinearProgressIndicator(
          value: strength.value,
          backgroundColor: Colors.grey.withOpacity(0.3),
          valueColor: AlwaysStoppedAnimation(strength.color),
        ),
        const SizedBox(height: 8),
        Text(
          'Password must contain: uppercase, lowercase, number (8+ chars)',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
          ),
        ),
      ],
    );
  }

  Widget _buildTermsSection(ThemeData theme) {
    return Column(
      children: [
        // Terms of service
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Checkbox(
              value: _acceptTerms,
              onChanged: (value) {
                setState(() {
                  _acceptTerms = value ?? false;
                });
              },
            ),
            Expanded(
              child: GestureDetector(
                onTap: () {
                  setState(() {
                    _acceptTerms = !_acceptTerms;
                  });
                },
                child: RichText(
                  text: TextSpan(
                    text: 'I agree to the ',
                    style: theme.textTheme.bodyMedium,
                    children: [
                      TextSpan(
                        text: 'Terms of Service',
                        style: TextStyle(
                          color: theme.colorScheme.primary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
        
        // Privacy policy
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Checkbox(
              value: _acceptPrivacy,
              onChanged: (value) {
                setState(() {
                  _acceptPrivacy = value ?? false;
                });
              },
            ),
            Expanded(
              child: GestureDetector(
                onTap: () {
                  setState(() {
                    _acceptPrivacy = !_acceptPrivacy;
                  });
                },
                child: RichText(
                  text: TextSpan(
                    text: 'I agree to the ',
                    style: theme.textTheme.bodyMedium,
                    children: [
                      TextSpan(
                        text: 'Privacy Policy',
                        style: TextStyle(
                          color: theme.colorScheme.primary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSignUpButton() {
    final canSignUp = _acceptTerms && _acceptPrivacy;
    
    return CustomButton(
      text: 'Create Account',
      onPressed: canSignUp ? _handleSignUp : null,
      isLoading: ref.watch(authLoadingProvider),
      icon: Icons.person_add,
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

  Widget _buildSocialSignup() {
    return Column(
      children: [
        // Divider with "or sign up with"
        Row(
          children: [
            const Expanded(child: Divider()),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                'or sign up with',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ),
            const Expanded(child: Divider()),
          ],
        ),
        
        const SizedBox(height: 24),
        
        // Social signup buttons
        Row(
          children: [
            Expanded(
              child: SocialButton(
                provider: SocialProvider.google,
                onPressed: () => _handleSocialSignup(SocialProvider.google),
                isLoading: ref.watch(authLoadingProvider),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: SocialButton(
                provider: SocialProvider.apple,
                onPressed: () => _handleSocialSignup(SocialProvider.apple),
                isLoading: ref.watch(authLoadingProvider),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSignInLink(ThemeData theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          'Already have an account? ',
          style: theme.textTheme.bodyMedium,
        ),
        TextButton(
          onPressed: _handleSignIn,
          child: Text(
            'Sign In',
            style: TextStyle(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _handleSignUp() async {
    // Clear any previous errors
    ref.read(authProvider.notifier).clearError();
    
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (!_acceptTerms || !_acceptPrivacy) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please accept the terms and privacy policy'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    final email = _emailController.text.trim();
    final password = _passwordController.text;
    final confirmPassword = _confirmPasswordController.text;
    final displayName = _displayNameController.text.trim();

    final registerRequest = RegisterRequest.emailPassword(
      email: email,
      password: password,
      confirmPassword: confirmPassword,
      displayName: displayName.isNotEmpty ? displayName : null,
    );

    final success = await ref.read(authProvider.notifier).register(registerRequest);
    
    if (success && mounted) {
      // Navigate to home screen or show success message
      Navigator.of(context).pushReplacementNamed('/home');
    }
  }

  Future<void> _handleSocialSignup(SocialProvider provider) async {
    if (!_acceptTerms || !_acceptPrivacy) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please accept the terms and privacy policy'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Clear any previous errors
    ref.read(authProvider.notifier).clearError();

    bool success = false;
    switch (provider) {
      case SocialProvider.google:
        success = await ref.read(authProvider.notifier).signInWithGoogle();
        break;
      case SocialProvider.apple:
        success = await ref.read(authProvider.notifier).signInWithApple();
        break;
    }

    if (success && mounted) {
      // Navigate to home screen
      Navigator.of(context).pushReplacementNamed('/home');
    }
  }

  void _handleSignIn() {
    // Navigate back to login screen
    Navigator.of(context).pop();
  }

  _PasswordStrength _getPasswordStrength(String password) {
    if (password.isEmpty) {
      return _PasswordStrength('Too weak', 0.0, Colors.red);
    }

    int score = 0;
    
    // Length check
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Character type checks
    if (password.contains(RegExp(r'[a-z]'))) score++;
    if (password.contains(RegExp(r'[A-Z]'))) score++;
    if (password.contains(RegExp(r'[0-9]'))) score++;
    if (password.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'))) score++;

    switch (score) {
      case 0:
      case 1:
      case 2:
        return _PasswordStrength('Weak', 0.25, Colors.red);
      case 3:
      case 4:
        return _PasswordStrength('Fair', 0.5, Colors.orange);
      case 5:
        return _PasswordStrength('Good', 0.75, Colors.lightGreen);
      case 6:
      default:
        return _PasswordStrength('Strong', 1.0, Colors.green);
    }
  }
}

class _PasswordStrength {
  final String label;
  final double value;
  final Color color;

  _PasswordStrength(this.label, this.value, this.color);
}