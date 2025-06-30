# SelfOS Flutter App

A cross-platform Flutter application for personal life management, connecting to the SelfOS backend API.

## Setup Complete ✅

The project has been bootstrapped with the following configuration:

### Project Structure
```
lib/
├── config/          # App configuration and constants
├── models/          # Data models and DTOs
├── screens/         # Main screen widgets
├── services/        # API services and business logic
├── utils/           # Utility functions and helpers
└── widgets/         # Reusable UI components
```

### Dependencies Installed
- **flutter_riverpod** (^2.4.9) - State management
- **dio** (^5.4.0) - HTTP client for API communication
- **flutter_secure_storage** (^9.0.0) - Secure token storage
- **go_router** (^12.1.3) - App navigation and routing
- **json_annotation** (^4.8.1) - JSON serialization support

### Platform Support
- ✅ macOS Desktop (primary target)
- ✅ iOS (available)
- ✅ Web (available)
- ⚠️ Android (requires Android Studio setup)

## Quick Start

### Prerequisites
- Flutter SDK 3.32.5+
- Xcode (for macOS/iOS development)
- SelfOS Backend API running on `http://localhost:8000`

### Running the App
```bash
# Ensure you're in the project directory
cd /Users/boris/github.com/selfos/apps/selfos

# Run on macOS
flutter run -d macos

# Run on web
flutter run -d chrome

# Build for macOS
flutter build macos
```

### Development Commands
```bash
# Get dependencies
flutter pub get

# Generate code (for JSON serialization)
flutter packages pub run build_runner build

# Run tests
flutter test

# Check for outdated packages
flutter pub outdated
```

## Backend Connection

The app is configured to connect to the SelfOS backend API:
- **Base URL**: `http://localhost:8000`
- **Authentication**: JWT tokens stored securely
- **Endpoints**: Goals, Tasks, Life Areas, AI Services

## Next Steps

1. Implement authentication screens
2. Create main dashboard UI
3. Build goal management features
4. Add task management functionality
5. Integrate AI-powered features
6. Implement data synchronization
7. Add offline capabilities

## Configuration

App configuration is managed in:
- `lib/config/app_config.dart` - Main app constants
- `lib/config/api_endpoints.dart` - API endpoint definitions