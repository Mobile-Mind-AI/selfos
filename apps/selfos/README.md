# SelfOS Flutter App

A cross-platform Flutter application for personal life management, connecting to the SelfOS backend API.

## ✅ Authentication System Complete

The SelfOS Flutter app now includes a fully functional authentication system with:

### 🔐 Authentication Features
- **Email/Password Authentication** - Secure login and registration
- **Social Login Support** - Google and Apple Sign-In (framework ready)
- **JWT Token Management** - Automatic token storage and refresh
- **Secure Storage** - Tokens stored in platform keystores (iOS Keychain, Android Keystore)
- **Form Validation** - Real-time validation with password strength checking
- **Error Handling** - Comprehensive error states and user feedback
- **Loading States** - Smooth loading indicators and overlays

### 🏗️ Project Structure
```
lib/
├── config/
│   ├── app_config.dart      # App configuration and constants
│   ├── api_endpoints.dart   # API endpoint definitions
│   └── routes.dart          # App routing with authentication guards
├── models/
│   ├── user.dart           # User data model
│   ├── auth_request.dart   # Login/registration request models
│   └── auth_response.dart  # API response models
├── screens/
│   └── auth/
│       ├── login_screen.dart    # Login form with validation
│       └── signup_screen.dart   # Registration form with validation
├── services/
│   ├── auth_service.dart       # HTTP API client for authentication
│   ├── storage_service.dart    # Secure token storage service
│   └── auth_provider.dart      # Riverpod state management
├── widgets/
│   └── common/
│       ├── custom_button.dart      # Reusable button components
│       ├── custom_text_field.dart  # Form input components
│       └── loading_overlay.dart    # Loading and error state components
└── main.dart               # App entry point with theming
```

### 📦 Dependencies
- **flutter_riverpod** (^2.6.1) - State management
- **dio** (^5.8.0) - HTTP client for API communication
- **flutter_secure_storage** (^9.2.4) - Secure token storage
- **go_router** (^12.1.3) - App navigation and routing
- **json_annotation** (^4.9.0) - JSON serialization support

### 🖥️ Platform Support
- ✅ **macOS Desktop** (primary target)
- ✅ **iOS** (available)
- ✅ **Web** (available)
- ⚠️ **Android** (requires Android Studio setup)

## 🚀 Quick Start

### Prerequisites
- Flutter SDK 3.32.5+
- Xcode (for macOS/iOS development)
- SelfOS Backend API running on `http://localhost:8000`

### Running the App
```bash
# Ensure you're in the project directory
cd /Users/boris/github.com/selfos/apps/selfos

# Get dependencies
flutter pub get

# Generate JSON serialization code
flutter packages pub run build_runner build

# Run on macOS
flutter run -d macos

# Run on web
flutter run -d chrome

# Build for macOS
flutter build macos
```

### Development Commands
```bash
# Analyze code for issues
flutter analyze

# Run tests
flutter test

# Check for outdated packages
flutter pub outdated

# Clean build artifacts
flutter clean
```

## 🔌 Backend Integration

The app is configured to connect to the SelfOS backend API:

### API Endpoints
- **Base URL**: `http://localhost:8000`
- **Authentication**: `/auth/login`, `/auth/register`, `/auth/me`
- **Goals**: `/api/goals` (coming soon)
- **Tasks**: `/api/tasks` (coming soon)
- **AI Services**: `/api/ai` (coming soon)

### Authentication Flow
1. User enters credentials in login/signup form
2. App validates input client-side
3. Credentials sent to backend API
4. JWT tokens stored securely in platform keystore
5. Automatic token refresh on expiration
6. Protected routes require valid authentication

## 📖 Documentation

### Detailed Documentation
- [**Authentication System**](docs/AUTHENTICATION.md) - Complete auth implementation guide
- [**UI Components**](docs/COMPONENTS.md) - Reusable component documentation

### Key Components

#### Authentication
```dart
// Login with email/password
final success = await ref.read(authProvider.notifier).login(
  LoginRequest.emailPassword(
    email: 'user@example.com',
    password: 'password123',
  ),
);

// Check authentication state
final isAuthenticated = ref.watch(isAuthenticatedProvider);
final user = ref.watch(currentUserProvider);
```

#### UI Components
```dart
// Custom button with loading state
CustomButton(
  text: 'Sign In',
  onPressed: _handleLogin,
  isLoading: _isLoading,
  variant: ButtonVariant.primary,
)

// Form field with validation
CustomTextField(
  label: 'Email',
  type: TextFieldType.email,
  validator: FieldValidators.combine([
    (value) => FieldValidators.required(value, fieldName: 'Email'),
    FieldValidators.email,
  ]),
)
```

## 🎨 UI/UX Features

### Design System
- **Material Design 3** - Modern, accessible design
- **Light/Dark Theme** - Automatic theme switching
- **Consistent Styling** - Reusable components with unified theming
- **Responsive Layout** - Works on desktop, mobile, and web

### User Experience
- **Real-time Validation** - Immediate feedback on form inputs
- **Loading States** - Clear loading indicators and progress feedback
- **Error Handling** - User-friendly error messages and retry options
- **Accessibility** - Screen reader support and keyboard navigation

## 🔒 Security Features

### Secure Storage
- **iOS**: Keychain Services
- **Android**: Android Keystore/EncryptedSharedPreferences  
- **macOS**: Keychain Services
- **Windows**: Windows Credential Store

### Authentication Security
- **JWT Tokens** - Secure token-based authentication
- **Automatic Refresh** - Seamless token renewal
- **Secure Transmission** - HTTPS-only API communication
- **Input Validation** - Client and server-side validation

## ✅ Completed Features

- [x] **Project Setup** - Flutter project with dependencies
- [x] **Authentication Models** - User, request/response models
- [x] **Secure Storage** - JWT token management
- [x] **Authentication Service** - API integration with error handling
- [x] **State Management** - Riverpod providers for auth state
- [x] **Login Screen** - Form validation and error handling
- [x] **Signup Screen** - Registration with password strength
- [x] **UI Components** - Reusable buttons, inputs, loading states
- [x] **Routing** - Authentication-aware navigation
- [x] **Social Login Framework** - Ready for Google/Apple integration
- [x] **Documentation** - Comprehensive guides and examples

## 🚧 Next Steps

1. **Social Login Implementation** - Integrate Google/Apple Sign-In SDKs
2. **Dashboard Screen** - Main user interface after login
3. **Goal Management** - CRUD operations for user goals
4. **Task Management** - Task creation and tracking
5. **AI Integration** - Chat interface and goal decomposition
6. **Offline Support** - Local data caching and sync
7. **Push Notifications** - Real-time updates and reminders

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/services/auth_service_test.dart
```

### Widget Tests
```bash
# Test authentication screens
flutter test test/screens/auth/
```

### Integration Tests
```bash
# Test full authentication flow
flutter test integration_test/
```

## 🐛 Troubleshooting

### Common Issues

#### Build Errors
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs
```

#### Authentication Issues
- Ensure backend API is running on `http://localhost:8000`
- Check network connectivity
- Verify API endpoints in `lib/config/api_endpoints.dart`

#### Platform-Specific Issues
- **macOS**: Ensure Xcode is installed and up-to-date
- **iOS**: Check iOS Simulator is available
- **Web**: Try Chrome browser for development
- **Android**: Install Android Studio and accept licenses

### Debug Mode
Enable detailed logging in development:
```dart
// Set environment variable for debug logging
const bool isDebug = bool.fromEnvironment('DEBUG', defaultValue: false);
```

## 📄 License

SelfOS Flutter App - Part of the SelfOS Personal Growth Operating System.

---

**Ready for Development** 🎉

The authentication system is fully implemented and ready for use. You can now:
1. Run the app and test login/signup flows
2. Integrate with the backend API
3. Build additional features on top of the auth foundation
4. Deploy to your target platforms

For detailed implementation guides, see the [documentation](docs/) directory.