# Development Guide

This document provides comprehensive guidelines for developing and contributing to the SelfOS Flutter application.

## Getting Started

### Prerequisites

- **Flutter SDK**: ^3.8.1 or later
- **Dart SDK**: Comes with Flutter
- **IDE**: VS Code, Android Studio, or IntelliJ IDEA
- **Platform Tools**: 
  - Android Studio (for Android development)
  - Xcode (for iOS/macOS development on macOS)
  - Chrome (for web development)

### Installation and Setup

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/selfos.git
cd selfos/apps/selfos
```

2. **Install Flutter dependencies**:
```bash
flutter pub get
```

3. **Generate code files**:
```bash
flutter packages pub run build_runner build --delete-conflicting-outputs
```

4. **Verify installation**:
```bash
flutter doctor
flutter devices
```

### Environment Configuration

#### Firebase Setup
1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Enable Authentication with Email/Password and Google Sign-In
3. Download configuration files:
   - `google-services.json` for Android (place in `android/app/`)
   - `GoogleService-Info.plist` for iOS (place in `ios/Runner/`)
   - `GoogleService-Info.plist` for macOS (place in `macos/Runner/`)

#### API Configuration
Update `lib/config/api_endpoints.dart` with your backend API endpoints:
```dart
class ApiEndpoints {
  static const String baseUrl = 'https://your-api.com';
  // ... other endpoints
}
```

## Development Workflow

### Running the Application

#### Development Mode
```bash
# Run on connected device/emulator
flutter run

# Run on specific device
flutter run -d <device-id>

# Run with hot reload debugging
flutter run --debug
```

#### Platform-Specific Development
```bash
# Web development
flutter run -d chrome
flutter run -d web-server --web-port 8080

# iOS Simulator
flutter run -d ios

# Android Emulator
flutter run -d android

# macOS Desktop
flutter run -d macos

# Windows Desktop
flutter run -d windows
```

### Code Generation

The app uses code generation for:
- JSON serialization/deserialization
- Riverpod providers
- Route generation

#### Running Code Generation
```bash
# One-time generation
flutter packages pub run build_runner build

# Delete conflicting outputs
flutter packages pub run build_runner build --delete-conflicting-outputs

# Watch mode (continuous generation during development)
flutter packages pub run build_runner watch
```

### Project Structure and Conventions

#### File Organization
Follow the established structure:
```
lib/
├── config/          # Configuration and constants
├── models/          # Data models with JSON serialization
├── screens/         # UI screens organized by feature
├── services/        # Business logic and API services
├── widgets/         # Reusable UI components
└── utils/           # Utility functions and helpers
```

#### Naming Conventions
- **Files**: `snake_case.dart`
- **Classes**: `PascalCase`
- **Variables/Functions**: `camelCase`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Private members**: `_privateVariable`

#### Code Organization
```dart
// File structure template
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// External package imports
import 'package:dio/dio.dart';
import 'package:go_router/go_router.dart';

// Internal imports (relative paths)
import '../models/user.dart';
import '../services/auth_service.dart';

/// Class documentation
class MyWidget extends ConsumerWidget {
  // Public members first
  final String title;
  
  // Constructor
  const MyWidget({
    super.key,
    required this.title,
  });

  // Public methods
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Implementation
  }
  
  // Private methods last
  void _privateMethod() {
    // Implementation
  }
}
```

### State Management with Riverpod

#### Provider Types
- **Provider**: For computed/derived state
- **StateProvider**: For simple state (primitive values)
- **StateNotifierProvider**: For complex state with business logic
- **FutureProvider**: For async operations
- **StreamProvider**: For reactive data streams

#### Creating Providers
```dart
// Simple state
final counterProvider = StateProvider<int>((ref) => 0);

// Complex state with business logic
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(
    authService: ref.read(authServiceProvider),
    storageService: ref.read(storageServiceProvider),
  );
});

// Computed state
final isAuthenticatedProvider = Provider<bool>((ref) {
  final authState = ref.watch(authProvider);
  return authState is AuthAuthenticated;
});
```

#### Using Providers in Widgets
```dart
class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Watch for changes
    final authState = ref.watch(authProvider);
    final isAuthenticated = ref.watch(isAuthenticatedProvider);
    
    // Read one-time value
    final authNotifier = ref.read(authProvider.notifier);
    
    return authState.when(
      initial: () => LoadingIndicator(),
      authenticated: (user) => HomeScreen(user: user),
      unauthenticated: () => LoginScreen(),
      loading: (message) => LoadingOverlay(message: message),
      error: (message, _) => ErrorDisplay(message: message),
    );
  }
}
```

### UI Development

#### Component Architecture
Create reusable components in `lib/widgets/common/`:
```dart
class CustomComponent extends StatelessWidget {
  final String title;
  final VoidCallback? onPressed;
  final bool isLoading;
  
  const CustomComponent({
    super.key,
    required this.title,
    this.onPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Container(
      // Component implementation
    );
  }
}
```

#### Theme Usage
```dart
@override
Widget build(BuildContext context) {
  final theme = Theme.of(context);
  final colorScheme = theme.colorScheme;
  
  return Container(
    color: colorScheme.surface,
    child: Text(
      'Hello World',
      style: theme.textTheme.titleLarge?.copyWith(
        color: colorScheme.primary,
      ),
    ),
  );
}
```

#### Responsive Design
```dart
@override
Widget build(BuildContext context) {
  final screenSize = MediaQuery.of(context).size;
  final isWideScreen = screenSize.width > 768;
  final isMobile = screenSize.width < 600;
  
  return Scaffold(
    body: isWideScreen 
      ? Row(children: [sidebar, content])
      : Column(children: [appBar, content]),
  );
}
```

### API Integration

#### Service Layer Pattern
Create services in `lib/services/`:
```dart
class ApiService {
  final Dio _dio;
  final StorageService _storage;
  
  ApiService({
    required Dio dio,
    required StorageService storage,
  }) : _dio = dio, _storage = storage {
    _setupInterceptors();
  }
  
  void _setupInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.getToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            await _handleTokenRefresh();
            // Retry request
          }
          handler.next(error);
        },
      ),
    );
  }
  
  Future<ApiResponse<T>> request<T>({
    required String path,
    required String method,
    Map<String, dynamic>? data,
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    try {
      final response = await _dio.request(
        path,
        data: data,
        options: Options(method: method),
      );
      
      return ApiResponse<T>.success(
        data: fromJson?.call(response.data) ?? response.data,
      );
    } on DioException catch (e) {
      return ApiResponse<T>.error(
        message: _handleError(e),
        exception: e,
      );
    }
  }
}
```

#### Model Serialization
Use JSON serialization for API models:
```dart
import 'package:json_annotation/json_annotation.dart';

part 'user.g.dart';

@JsonSerializable()
class User {
  final String id;
  final String email;
  @JsonKey(name: 'display_name')
  final String? displayName;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;
  
  const User({
    required this.id,
    required this.email,
    this.displayName,
    this.createdAt,
  });
  
  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);
  
  User copyWith({
    String? id,
    String? email,
    String? displayName,
    DateTime? createdAt,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
```

### Testing

#### Unit Testing
Create tests in `test/unit/`:
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';

import '../../lib/services/auth_service.dart';

class MockAuthService extends Mock implements AuthService {}

void main() {
  group('AuthService Tests', () {
    late AuthService authService;
    late MockHttpClient mockClient;
    
    setUp(() {
      mockClient = MockHttpClient();
      authService = AuthService(client: mockClient);
    });
    
    test('should login with valid credentials', () async {
      // Arrange
      when(mockClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockSuccessResponse);
      
      // Act
      final result = await authService.login('email', 'password');
      
      // Assert
      expect(result.isSuccess, true);
      expect(result.data?.accessToken, isNotEmpty);
    });
  });
}
```

#### Widget Testing
Create widget tests in `test/widgets/`:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../lib/widgets/custom_button.dart';

void main() {
  group('CustomButton Tests', () {
    testWidgets('should display text and handle tap', (tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: CustomButton(
                text: 'Test Button',
                onPressed: () => tapped = true,
              ),
            ),
          ),
        ),
      );
      
      expect(find.text('Test Button'), findsOneWidget);
      
      await tester.tap(find.byType(CustomButton));
      await tester.pump();
      
      expect(tapped, true);
    });
  });
}
```

#### Integration Testing
Create integration tests in `integration_test/`:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:selfos/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  
  group('Authentication Flow', () {
    testWidgets('complete login flow', (tester) async {
      app.main();
      await tester.pumpAndSettle();
      
      // Navigate to login
      expect(find.text('Sign In'), findsOneWidget);
      
      // Enter credentials
      await tester.enterText(find.byKey(Key('email_field')), 'test@example.com');
      await tester.enterText(find.byKey(Key('password_field')), 'password123');
      
      // Submit form
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();
      
      // Verify navigation to home
      expect(find.text('Welcome'), findsOneWidget);
    });
  });
}
```

### Building and Deployment

#### Development Builds
```bash
# Debug builds
flutter build apk --debug
flutter build ios --debug
flutter build macos --debug
flutter build web --debug
```

#### Production Builds
```bash
# Release builds
flutter build apk --release
flutter build ios --release
flutter build macos --release
flutter build web --release

# App bundles (recommended for Android)
flutter build appbundle --release
```

#### Build Configuration
Update version in `pubspec.yaml`:
```yaml
version: 1.0.0+1  # version+build_number
```

Platform-specific configuration:
- **Android**: `android/app/build.gradle`
- **iOS**: `ios/Runner.xcodeproj`
- **macOS**: `macos/Runner.xcodeproj`
- **Web**: `web/index.html`

### Performance Optimization

#### General Guidelines
1. **Minimize widget rebuilds**: Use `const` constructors
2. **Optimize lists**: Use `ListView.builder` for large lists
3. **Image optimization**: Use appropriate image formats and sizes
4. **Code splitting**: Lazy load screens and features
5. **Memory management**: Dispose controllers and subscriptions

#### Specific Optimizations
```dart
// Use const constructors
const Text('Static text');

// Optimize list rendering
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemWidget(items[index]),
);

// Cache expensive computations
@override
Widget build(BuildContext context) {
  return Consumer(
    builder: (context, ref, child) {
      final expensiveValue = ref.watch(expensiveProvider);
      return ExpensiveWidget(value: expensiveValue);
    },
    child: const StaticChildWidget(), // Won't rebuild
  );
}
```

### Debugging

#### Debug Tools
- **Flutter Inspector**: Widget tree visualization
- **Debugger**: Breakpoints and step-through debugging
- **Performance Overlay**: FPS and performance metrics
- **Network Debugging**: HTTP request/response monitoring

#### Debug Commands
```bash
# Performance profiling
flutter run --profile

# Debug with additional logging
flutter run --verbose

# Analyze code
flutter analyze

# Format code
flutter format .
```

#### Common Debugging Techniques
```dart
// Debug prints (remove in production)
debugPrint('Debug message: $variable');

// Assert conditions
assert(value != null, 'Value should not be null');

// Debug mode only code
if (kDebugMode) {
  print('Development only logging');
}
```

### Code Quality

#### Linting
The project uses `flutter_lints` for code quality:
```yaml
# analysis_options.yaml
include: package:flutter_lints/flutter.yaml

linter:
  rules:
    prefer_const_constructors: true
    prefer_const_literals_to_create_immutables: true
    avoid_print: true
```

#### Code Formatting
```bash
# Format all files
flutter format .

# Check formatting
flutter format --set-exit-if-changed .
```

#### Documentation
- Document public APIs with `///` comments
- Use meaningful variable and function names
- Add TODO comments for future improvements
- Keep README files updated

### Git Workflow

#### Branch Strategy
- `main`: Production-ready code
- `develop`: Development integration branch
- `feature/*`: Feature development branches
- `hotfix/*`: Critical bug fixes

#### Commit Messages
Follow conventional commit format:
```
type(scope): description

feat(auth): add social login support
fix(ui): resolve button loading state issue
docs(readme): update installation instructions
refactor(api): simplify error handling
```

#### Pull Request Process
1. Create feature branch from `develop`
2. Implement feature with tests
3. Run code quality checks
4. Create pull request with description
5. Code review and approval
6. Merge to `develop`

### Common Issues and Solutions

#### Build Issues
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs

# Clear Xcode derived data (macOS/iOS)
rm -rf ~/Library/Developer/Xcode/DerivedData

# Reset Android build
cd android && ./gradlew clean && cd ..
```

#### Code Generation Issues
```bash
# Delete generated files and regenerate
find . -name "*.g.dart" -delete
flutter packages pub run build_runner build --delete-conflicting-outputs
```

#### Platform-Specific Issues
- **iOS**: Check signing certificates and provisioning profiles
- **Android**: Verify SDK versions and permissions
- **Web**: Check CORS settings and browser compatibility
- **macOS**: Verify entitlements and notarization

This development guide provides a comprehensive foundation for contributing to the SelfOS Flutter application. Follow these guidelines to maintain code quality, consistency, and project standards.