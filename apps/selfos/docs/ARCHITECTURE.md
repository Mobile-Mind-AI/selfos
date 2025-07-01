# Flutter Application Architecture

This document provides a comprehensive overview of the SelfOS Flutter application architecture, design patterns, and implementation details.

## Overview

SelfOS is a personal growth operating system built with Flutter, supporting multiple platforms (iOS, Android, macOS, Windows, Web). The application follows modern Flutter best practices with a focus on maintainability, scalability, and user experience.

## Architecture Principles

### Design Patterns
- **Clean Architecture**: Clear separation between UI, business logic, and data layers
- **Repository Pattern**: Abstracted data access through service layers
- **Provider Pattern**: State management using Riverpod for reactive programming
- **Component-Based UI**: Reusable widgets with consistent design system

### Key Technologies
- **Flutter SDK**: ^3.8.1 with Material Design 3
- **State Management**: Riverpod ^2.4.9 for reactive state management
- **Routing**: GoRouter ^12.1.3 for declarative navigation
- **HTTP Client**: Dio ^5.4.0 for API communication
- **Secure Storage**: Flutter Secure Storage ^9.0.0 for token management
- **Social Auth**: Google Sign-In and Apple Sign-In integration

## Project Structure

```
lib/
├── config/              # Configuration files
│   ├── api_endpoints.dart    # API endpoint definitions
│   ├── app_config.dart       # App configuration
│   └── routes.dart           # Route definitions
├── models/              # Data models
│   ├── auth_request.dart     # Authentication request models
│   ├── auth_response.dart    # Authentication response models
│   ├── chat_message.dart     # Chat message model
│   └── user.dart            # User data model
├── screens/             # UI screens
│   ├── auth/               # Authentication screens
│   ├── chat/               # Chat interface
│   ├── goals/              # Goals management
│   ├── home/               # Today/home screen
│   ├── progress/           # Progress tracking
│   ├── settings/           # App settings
│   ├── tasks/              # Task management
│   ├── main_shell.dart     # Main app shell with navigation
│   └── splash_screen.dart  # Initial loading screen
├── services/            # Business logic and API services
│   ├── auth_provider.dart    # Authentication state management
│   ├── auth_service.dart     # Authentication HTTP client
│   ├── social_login_service.dart # Social login handlers
│   └── storage_service.dart  # Secure storage service
├── utils/               # Utility functions
├── widgets/             # Reusable UI components
│   └── common/             # Common widgets
│       ├── custom_button.dart    # Button component
│       ├── custom_text_field.dart # Text field component
│       ├── loading_overlay.dart   # Loading indicator
│       └── social_button.dart     # Social login button
└── main.dart           # Application entry point
```

## State Management with Riverpod

### Authentication State
The app uses a centralized authentication state management system:

```dart
// Authentication states
sealed class AuthState {
  const AuthState();
}

class AuthInitial extends AuthState {}
class AuthAuthenticated extends AuthState {
  final User user;
}
class AuthUnauthenticated extends AuthState {}
class AuthLoading extends AuthState {
  final String message;
}
class AuthError extends AuthState {
  final String message;
  final Exception? exception;
}
```

### Key Providers
- `authProvider` - Main authentication state
- `isAuthenticatedProvider` - Boolean authentication status  
- `currentUserProvider` - Current user data
- `authLoadingProvider` - Loading state indicator
- `authErrorProvider` - Error message provider

## Navigation Architecture

### Route Structure
The app uses GoRouter with authentication-aware routing:

```dart
// Protected routes wrapped in shell
ShellRoute(
  builder: (context, state, child) => MainShell(child: child),
  routes: [
    GoRoute(path: '/home', builder: (context, state) => TodayScreen()),
    GoRoute(path: '/chat', builder: (context, state) => ChatScreen()),
    GoRoute(path: '/goals', builder: (context, state) => GoalsScreen()),
    GoRoute(path: '/tasks', builder: (context, state) => TasksScreen()),
    GoRoute(path: '/progress', builder: (context, state) => ProgressScreen()),
    GoRoute(path: '/settings', builder: (context, state) => SettingsScreen()),
  ],
)
```

### Authentication Flow
- Unauthenticated users are redirected to login
- Authenticated users access the main app shell
- Automatic token refresh and session management
- Persistent login state across app restarts

## UI Components Architecture

### Design System
The app implements a consistent design system with:
- **Material Design 3** principles
- **Indigo color scheme** (#6366F1 seed color)
- **Responsive layout** adapting to screen sizes
- **Dark/light theme** support with system preference detection

### Component Structure

#### CustomTextField
Comprehensive text input component with:
- Multiple input types (email, password, text, phone, number, multiline, URL)
- Built-in validation system with combinable validators
- Loading states and error display
- Password visibility toggle
- Consistent Material Design theming

#### CustomButton  
Reusable button component with:
- Four variants: primary, secondary, outlined, text
- Loading states with spinner
- Icon support
- Disabled state handling
- Consistent theming

#### Navigation Shell
Responsive navigation with:
- Collapsible sidebar for mobile/tablet
- Full sidebar for desktop
- User profile section
- Dynamic navigation highlighting

## Services Architecture

### Authentication Service
HTTP client service for auth operations:
- Dio-based HTTP client with interceptors
- Automatic token attachment
- Token refresh handling
- Comprehensive error handling
- Support for email/password and social authentication

### Storage Service
Secure token storage across platforms:
- **iOS/macOS**: Keychain Services
- **Android**: Android Keystore/EncryptedSharedPreferences  
- **Windows**: Windows Credential Store
- **Web**: Secure browser storage

### Social Login Service
Integration with social auth providers:
- Google Sign-In with proper scopes
- Apple Sign-In with privacy features
- Token exchange with backend API
- Error handling for auth failures

## Data Models

### User Model
Comprehensive user data structure:
```dart
class User {
  final String uid;           // Firebase Auth UID
  final String email;         // User email
  final String? displayName;  // Display name
  final String? photoUrl;     // Profile photo URL
  final List<String> roles;   // User roles/permissions
  final DateTime? createdAt;  // Account creation
  final DateTime? lastLogin;  // Last login timestamp
  final bool emailVerified;   // Email verification status
}
```

### Request/Response Models
Structured API communication:
- `AuthRequest` for login/registration
- `AuthResponse` for authentication results
- JSON serialization with code generation
- Type-safe API interactions

## Security Considerations

### Token Management
- JWT tokens stored in platform-specific secure storage
- Automatic token refresh before expiration
- Secure token transmission over HTTPS
- Token revocation on logout

### Input Validation
- Client-side validation for user experience
- Server-side validation for security
- Input sanitization and formatting
- Protection against common attacks

### Network Security
- HTTPS-only communication
- Certificate pinning recommended for production
- Request/response encryption
- API rate limiting compliance

## Performance Optimizations

### Efficient Rendering
- Lazy loading of screens and components
- Optimized list rendering for large datasets
- Image caching and optimization
- Minimal rebuilds with proper state management

### Memory Management
- Proper disposal of controllers and streams
- Efficient provider lifecycle management
- Background task optimization
- Memory leak prevention

## Testing Strategy

### Unit Testing
- Model serialization/deserialization
- Service layer business logic
- Validation functions
- State management logic

### Widget Testing
- Component rendering and interaction
- Form validation behavior
- Navigation flow testing
- Error state handling

### Integration Testing
- Authentication flow end-to-end
- API communication testing
- Cross-platform compatibility
- Performance benchmarking

## Build and Deployment

### Development
```bash
# Run in development mode
flutter run

# Web development
flutter run -d chrome

# Build for production
flutter build apk --release
flutter build ios --release
flutter build macos --release
flutter build web --release
```

### Platform-Specific Configuration
- **Android**: Material Design theming, proper permissions
- **iOS**: Human Interface Guidelines compliance, proper entitlements
- **macOS**: Native macOS styling, proper sandboxing
- **Web**: Progressive Web App features, responsive design

## Future Enhancements

### Planned Features
1. **Offline Support**: Local data caching and sync
2. **Push Notifications**: Real-time user notifications
3. **Biometric Authentication**: Face ID/Touch ID support
4. **Advanced Analytics**: User behavior tracking
5. **Internationalization**: Multi-language support

### Technical Improvements
1. **Enhanced Testing**: Increase test coverage
2. **Performance Monitoring**: Real-time performance metrics
3. **Accessibility**: Enhanced screen reader support
4. **Code Generation**: More automated code generation
5. **CI/CD Pipeline**: Automated testing and deployment

## Development Guidelines

### Code Standards
- Follow Dart/Flutter linting rules
- Use meaningful variable and function names
- Implement proper error handling
- Write comprehensive documentation
- Maintain consistent code formatting

### Git Workflow
- Feature branch development
- Code review requirements
- Automated testing on pull requests
- Semantic versioning for releases

### Documentation
- Inline code documentation
- Architecture decision records
- API documentation
- User guide maintenance

## Troubleshooting

### Common Issues
1. **Build Failures**: Run `flutter clean && flutter pub get`
2. **Code Generation**: Run `flutter packages pub run build_runner build --delete-conflicting-outputs`
3. **Platform Issues**: Check platform-specific configuration
4. **Authentication Problems**: Verify API endpoints and Firebase config

### Debug Tools
- Flutter Inspector for widget debugging
- Network debugging with Charles/Proxy tools
- Firebase Auth debugging console
- Platform-specific debugging tools

This architecture provides a solid foundation for a scalable, maintainable Flutter application while following modern development best practices.