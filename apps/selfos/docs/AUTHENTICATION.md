# Authentication System Documentation

This document describes the authentication implementation in the SelfOS Flutter app.

## Overview

The authentication system provides secure user login and registration with:
- Email/password authentication
- Social login support (Google, Apple)
- JWT token management with secure storage
- Automatic token refresh
- State management with Riverpod
- Form validation and error handling

## Architecture

### Components

1. **Models** (`lib/models/`)
   - `user.dart` - User data model
   - `auth_request.dart` - Login/registration request models
   - `auth_response.dart` - API response models

2. **Services** (`lib/services/`)
   - `auth_service.dart` - HTTP API client for authentication
   - `storage_service.dart` - Secure token storage
   - `auth_provider.dart` - Riverpod state management

3. **UI** (`lib/screens/auth/`, `lib/widgets/common/`)
   - `login_screen.dart` - Login form
   - `signup_screen.dart` - Registration form
   - Custom UI components for forms and loading states

4. **Routing** (`lib/config/routes.dart`)
   - Authentication-aware routing
   - Automatic redirects based on auth state

## Usage

### Basic Authentication Flow

```dart
// Login
final authNotifier = ref.read(authProvider.notifier);
final success = await authNotifier.login(
  LoginRequest.emailPassword(
    email: 'user@example.com',
    password: 'password123',
  ),
);

// Register
final success = await authNotifier.register(
  RegisterRequest.emailPassword(
    email: 'user@example.com',
    password: 'password123',
    confirmPassword: 'password123',
  ),
);

// Logout
await authNotifier.logout();
```

### Watching Authentication State

```dart
class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    
    return authState.when(
      initial: () => SplashScreen(),
      authenticated: (user) => HomeScreen(user: user),
      unauthenticated: () => LoginScreen(),
      loading: (message) => LoadingScreen(message: message),
      error: (message, exception) => ErrorScreen(message: message),
    );
  }
}
```

### Convenience Providers

```dart
// Check if authenticated
final isAuthenticated = ref.watch(isAuthenticatedProvider);

// Get current user
final user = ref.watch(currentUserProvider);

// Check loading state
final isLoading = ref.watch(authLoadingProvider);

// Get error message
final errorMessage = ref.watch(authErrorProvider);
```

## API Integration

### Backend Endpoints

The authentication service integrates with these SelfOS backend endpoints:

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - User logout
- `POST /auth/forgot-password` - Password reset

### Request/Response Format

#### Registration Request
```json
{
  "username": "user@example.com",
  "password": "password123",
  "displayName": "John Doe"
}
```

#### Login Request
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

#### Authentication Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "user": {
    "uid": "user_id_123",
    "email": "user@example.com",
    "displayName": "John Doe",
    "roles": ["user"]
  }
}
```

## Secure Storage

JWT tokens are stored securely using Flutter Secure Storage:

- **iOS**: Keychain Services
- **Android**: Android Keystore/EncryptedSharedPreferences
- **macOS**: Keychain Services
- **Windows**: Windows Credential Store

### Storage Keys

- `auth_token_access` - JWT access token
- `refresh_token` - Refresh token
- `user_data` - User information (JSON)
- `auth_token_expiry` - Token expiration time
- `login_provider` - Authentication provider used

## Form Validation

### Email Validation
- Required field
- Valid email format (regex)
- Real-time validation feedback

### Password Validation
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Password strength indicator
- Confirm password matching

### Example Validator Usage

```dart
CustomTextField(
  label: 'Email',
  controller: _emailController,
  type: TextFieldType.email,
  validator: FieldValidators.combine([
    (value) => FieldValidators.required(value, fieldName: 'Email'),
    FieldValidators.email,
  ]),
)
```

## Social Login Integration

### Supported Providers

1. **Google Sign-In**
   - Uses Google Sign-In SDK
   - Returns Google ID token
   - Automatic account creation

2. **Apple Sign-In**
   - Uses Apple Sign-In SDK
   - Returns Apple ID token
   - Privacy-focused authentication

### Implementation Example

```dart
// Social login button
SocialButton(
  provider: SocialProvider.google,
  onPressed: () async {
    // Get social token from provider SDK
    final socialToken = await GoogleSignIn().signIn();
    
    // Login with social token
    final success = await ref.read(authProvider.notifier).socialLogin(
      provider: 'google',
      socialToken: socialToken.idToken,
      email: socialToken.email,
    );
  },
)
```

## Error Handling

### Error Types

1. **Network Errors**
   - Connection timeout
   - No internet connection
   - Server unreachable

2. **Validation Errors**
   - Invalid email format
   - Weak password
   - Passwords don't match

3. **Authentication Errors**
   - Invalid credentials
   - Account already exists
   - Token expired

### Error Display

Errors are displayed using consistent UI components:

```dart
// Inline error message
if (errorMessage != null) 
  ErrorDisplay(
    message: errorMessage,
    onRetry: () => _handleRetry(),
  )

// Snackbar for temporary messages
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(
    content: Text(errorMessage),
    backgroundColor: Colors.red,
  ),
);
```

## UI Components

### CustomButton
Reusable button with loading states and variants:

```dart
CustomButton(
  text: 'Sign In',
  onPressed: _handleLogin,
  isLoading: isLoading,
  variant: ButtonVariant.primary,
  icon: Icons.login,
)
```

### CustomTextField
Reusable text input with validation:

```dart
CustomTextField(
  label: 'Password',
  hint: 'Enter your password',
  type: TextFieldType.password,
  validator: FieldValidators.password,
  isRequired: true,
)
```

### LoadingOverlay
Full-screen loading indicator:

```dart
LoadingOverlay(
  isLoading: isLoading,
  message: 'Signing in...',
  child: YourContent(),
)
```

## Testing

### Unit Tests
Test authentication logic without UI:

```dart
test('should login with valid credentials', () async {
  final authService = AuthService();
  final request = LoginRequest.emailPassword(
    email: 'test@example.com',
    password: 'password123',
  );
  
  final response = await authService.login(request);
  expect(response.accessToken, isNotEmpty);
});
```

### Widget Tests
Test UI components and interactions:

```dart
testWidgets('should show error on invalid login', (tester) async {
  await tester.pumpWidget(MyApp());
  
  await tester.enterText(find.byType(CustomTextField).first, 'invalid');
  await tester.tap(find.byType(CustomButton));
  await tester.pump();
  
  expect(find.text('Invalid credentials'), findsOneWidget);
});
```

## Security Considerations

1. **Token Storage**
   - Tokens stored in secure platform keystores
   - Automatic token expiration handling
   - Secure token refresh mechanism

2. **Network Security**
   - HTTPS-only communication
   - Certificate pinning (recommended for production)
   - Request/response encryption

3. **Input Validation**
   - Client-side validation for UX
   - Server-side validation for security
   - Sanitization of user inputs

4. **Error Handling**
   - Generic error messages to prevent information leakage
   - Detailed logging for debugging (development only)
   - Rate limiting on authentication attempts

## Future Enhancements

1. **Biometric Authentication**
   - Face ID / Touch ID support
   - Biometric login for returning users
   - Secure biometric storage

2. **Multi-Factor Authentication (MFA)**
   - SMS verification
   - Email verification
   - Authenticator app support

3. **Advanced Social Providers**
   - Facebook Login
   - GitHub OAuth
   - Microsoft OAuth

4. **Offline Support**
   - Cached authentication state
   - Offline token validation
   - Sync when connection restored

## Troubleshooting

### Common Issues

1. **Build Errors**
   - Run `flutter clean && flutter pub get`
   - Regenerate code: `flutter packages pub run build_runner build --delete-conflicting-outputs`

2. **Authentication Failures**
   - Check backend API is running
   - Verify API endpoints in `config/api_endpoints.dart`
   - Check network connectivity

3. **Token Issues**
   - Clear app data to reset stored tokens
   - Check token expiration handling
   - Verify refresh token logic

### Debug Mode

Enable additional logging in development:

```dart
// In auth_service.dart
final dio = Dio();
if (kDebugMode) {
  dio.interceptors.add(LogInterceptor(
    requestBody: true,
    responseBody: true,
  ));
}
```