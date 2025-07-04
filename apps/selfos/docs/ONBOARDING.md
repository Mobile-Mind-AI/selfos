# Onboarding Flow Documentation

## Overview

The SelfOS onboarding flow is a streamlined, engaging user experience that guides new users through setting up their AI assistant and initial preferences. The flow follows a "Start Your Story" narrative concept, creating an engaging introduction to the SelfOS platform while collecting essential user preferences.

## Architecture

### Core Components

#### Backend Integration
- **OnboardingState Model**: Tracks user progress through onboarding steps with database persistence
- **API Endpoints**: Complete state management and step processing with error handling
- **Database Persistence**: User preferences and progress stored permanently with step validation
- **MCP Integration**: Onboarding tools available for AI agents

#### Frontend Implementation
- **Flutter Screens**: 5 interactive onboarding steps with animations and validation
- **Provider Architecture**: Riverpod-based state management with rate limiting
- **Route Protection**: Authentication-aware navigation with automatic redirects
- **Progress Tracking**: Visual progress indicators and step validation

## User Flow

### The "Start Your Story" Journey

The onboarding follows a narrative structure where the user creates their AI companion:

```
1. Welcome → 2. Assistant Creation → 3. Life Areas → 4. First Goal → 5. Completion → Dashboard
```

**Total Steps**: 5 (reduced from original 6-step design for better user experience)

## Implementation Details

### 1. Welcome Step (`welcome_step.dart`)
**Purpose**: Introduction to SelfOS with engaging visuals and narrative setup

**Features**:
- Animated SelfOS branding with hero section
- Hero animation with orbiting particles and brain icon
- Time-based greeting messages with text rotation
- Interactive feature cards highlighting SelfOS capabilities
- "Start Your Story" narrative introduction
- Smooth transition animations and hover effects

**UI Components**:
```dart
// Key animated components
- HeroSection (animated brain icon with orbiting dots)
- WelcomeText (time-based greetings with rotation)
- FeatureCards (interactive SelfOS feature highlights)
- StoryIntroduction (narrative "Start Your Story" section)
- WelcomeActions (dual-action buttons with animations)
```

**No Data Collection**: This is purely an introductory screen

### 2. Assistant Creation (`assistant_creation_step.dart`)
**Purpose**: Comprehensive AI assistant setup with name, avatar, personality, and language preferences

**Features**:
- **Assistant Naming**: Text input with validation (1-100 characters)
- **Avatar Selection**: Gallery with predefined options plus custom avatar upload
- **Language Preferences**: 8 supported languages with confirmation settings
- **Personality Setup**: 5-trait personality system with real-time preview:
  - **Formality**: Formal (0) ↔ Casual (100) - Default: 50
  - **Humor**: Serious (0) ↔ Playful (100) - Default: 30  
  - **Motivation**: Calm (0) ↔ Energetic (100) - Default: 60
- **Real-time Preview**: Live assistant preview with personality-based sample messages
- **Auto-save**: Debounced saves every 2 seconds to prevent data loss

**Supported Languages**:
- English (en), Spanish (es), French (fr), German (de)
- Italian (it), Portuguese (pt), Chinese (zh), Japanese (ja)

**Data Collection**:
```json
{
  "name": "String (1-100 chars)",
  "avatar_url": "String (optional)",
  "language": "en",
  "requires_confirmation": true,
  "style": {
    "formality": 50,
    "humor": 30,
    "motivation": 60
  }
}
```

**Backend Integration**: Maps to `assistant_creation` step, which automatically marks personality and language steps as complete

### 3. Life Areas Selection (`life_areas_step.dart`)
**Purpose**: Personal life area categorization for goal organization

**Features**:
- Grid-based selection interface with visual icons
- Pre-defined life areas with descriptions:
  - Health & Fitness 🏃‍♂️
  - Career & Professional 💼
  - Relationships & Social 👥
  - Finance & Money 💰
  - Personal Development 🌱
  - Education & Learning 📚
  - Recreation & Hobbies 🎨
  - Spiritual & Mindfulness 🧘
- Custom life area creation with text input
- Multi-selection with visual feedback
- Minimum selection requirement (at least 1 area)

**Data Collection**:
```json
{
  "life_area_ids": [1, 3, 5],
  "custom_life_areas": ["Custom Area Name"]
}
```

**Backend Integration**: Maps to `life_areas` step

### 4. First Goal Creation (`first_goal_step.dart`)
**Purpose**: Initial goal setup to demonstrate SelfOS functionality

**Features**:
- Goal title and description input with validation
- Life area association dropdown (from selected areas)
- Optional AI task generation toggle
- Skip option for users who want to explore first
- Goal preview with SMART goal guidance
- Form validation and error handling

**Data Collection**:
```json
{
  "skip_goal_creation": false,
  "title": "Learn Spanish",
  "description": "Become conversational in Spanish within 6 months",
  "life_area_id": 6,
  "generate_tasks": true
}
```

**Backend Integration**: Maps to `first_goal` step

### 5. Completion Step (`completion_step.dart`)
**Purpose**: Celebration and summary of onboarding setup

**Features**:
- Celebration animations and visual feedback
- Summary of created assistant and preferences
- Welcome message from personalized AI assistant
- Dashboard access button
- Success metrics and encouragement
- Automatic onboarding completion in backend

## Technical Implementation

### State Management

#### OnboardingProvider (`onboarding_provider.dart`)
```dart
// Core provider for onboarding state management
final onboardingProvider = StateNotifierProvider<OnboardingNotifier, AsyncValue<OnboardingStatus>>();

// Onboarding status tracking
enum OnboardingStatus {
  unknown,      // Initial state
  notStarted,   // User hasn't begun onboarding
  inProgress,   // Onboarding in progress  
  completed,    // Onboarding finished
}
```

#### Key Methods
```dart
// Check current onboarding status
Future<bool> checkOnboardingStatus()

// Update specific onboarding step with rate limiting
Future<bool> updateOnboardingStep(String step, Map<String, dynamic> data)

// Complete full onboarding flow
Future<bool> completeOnboarding()

// Reset onboarding (for settings)
Future<bool> resetOnboarding()
```

#### Rate Limiting & Error Handling
```dart
// Built-in rate limiting to prevent API abuse
final Map<String, DateTime> _lastSaveTime = {};
static const Duration _saveThrottle = Duration(seconds: 2);

// Auto-retry logic for failed API calls
Future<bool> _retryApiCall(Function apiCall, {int maxRetries = 3})
```

### API Integration

#### Backend Endpoints
```http
GET    /api/onboarding/state              # Current user onboarding status
POST   /api/onboarding/step               # Update specific step
POST   /api/onboarding/complete           # Mark onboarding complete
POST   /api/onboarding/reset              # Reset onboarding (settings)
```

#### Request/Response Schemas
```dart
// Step update request
class OnboardingStepRequest {
  final OnboardingStep step;
  final Map<String, dynamic> data;
}

// Onboarding state response
class OnboardingStateOut {
  final String id;
  final String userId;
  final int currentStep;
  final List<int> completedSteps;
  final bool onboardingCompleted;
  final String? assistantProfileId;
  final List<int> selectedLifeAreas;
  final int? firstGoalId;
  final int? firstTaskId;
}
```

### Navigation Integration

#### Route Protection (`routes.dart`)
```dart
// Automatic redirect logic
redirect: (context, state) {
  final isAuthenticated = authState is AuthStateAuthenticated;
  final onboardingCompleted = onboardingStatus.when(
    data: (status) => status == OnboardingStatus.completed,
    loading: () => false,
    error: (_, __) => false,
  );

  // Redirect to onboarding if not completed
  if (isAuthenticated && !onboardingCompleted && !isOnboardingRoute) {
    return RoutePaths.onboarding;
  }

  // Allow access to main app if completed
  if (isAuthenticated && onboardingCompleted) {
    return RoutePaths.home;
  }
}
```

## Database Schema

### OnboardingState Model
```sql
CREATE TABLE onboarding_states (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR UNIQUE NOT NULL,
    current_step INTEGER NOT NULL DEFAULT 1,
    completed_steps JSON NOT NULL DEFAULT '[]',
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    assistant_profile_id VARCHAR REFERENCES assistant_profiles(id),
    selected_life_areas JSON NOT NULL DEFAULT '[]',
    first_goal_id INTEGER REFERENCES goals(id),
    first_task_id INTEGER REFERENCES tasks(id),
    theme_preference VARCHAR,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temp_data JSON NOT NULL DEFAULT '{}',
    skip_intro BOOLEAN NOT NULL DEFAULT FALSE
);
```

### Step Mapping
The frontend uses a 5-step flow that maps to backend steps:
- **Frontend Step 1** (Welcome): No backend step (intro only)
- **Frontend Step 2** (Assistant Creation): Backend steps 2, 3, 4 (assistant, personality, language)
- **Frontend Step 3** (Life Areas): Backend step 5
- **Frontend Step 4** (First Goal): Backend step 6
- **Frontend Step 5** (Completion): Triggers onboarding completion

## Error Handling

### Frontend Error States
```dart
// Comprehensive error handling in onboarding screens
try {
  final success = await ref.read(onboardingProvider.notifier).updateOnboardingStep(step, data);
  if (!success) {
    _showErrorSnackBar('Failed to save progress. Please try again.');
    return;
  }
} catch (e) {
  print('Onboarding step error: $e');
  _showErrorSnackBar('Something went wrong. Please check your connection.');
}
```

### Network Error Recovery
```dart
// Auto-retry for network issues
Future<bool> _saveWithRetry(String step, Map<String, dynamic> data) async {
  for (int attempt = 1; attempt <= 3; attempt++) {
    try {
      final success = await updateOnboardingStep(step, data);
      if (success) return true;
    } catch (e) {
      if (attempt == 3) {
        print('Failed to save after 3 attempts: $e');
        return false;
      }
      await Future.delayed(Duration(seconds: attempt));
    }
  }
  return false;
}
```

## Performance Optimizations

### Rate Limiting
- **API Throttling**: Maximum 1 save per 2 seconds per step
- **Debounced Saves**: Input changes debounced to prevent excessive API calls
- **Local State Caching**: Form data cached locally until successful save

### Memory Management
- **Custom Avatar Storage**: Global storage cleared after onboarding completion
- **Animation Controllers**: Properly disposed to prevent memory leaks
- **Timer Management**: All timers properly cancelled on widget disposal

## User Experience Features

### Progressive Enhancement
- **Graceful Degradation**: App works with limited API connectivity
- **Offline State Handling**: Clear messaging when API is unavailable
- **Loading States**: Visual feedback during save operations
- **Error Recovery**: User-friendly error messages with retry options

### Accessibility
- **Focus Management**: Proper tab order and focus handling
- **Screen Reader Support**: Semantic labels and descriptions
- **High Contrast**: Color choices meet accessibility standards
- **Touch Targets**: Minimum 48dp touch targets for all interactive elements

### Animation & Transitions
- **Smooth Transitions**: Page transitions with proper curve animations
- **Loading Indicators**: Visual feedback during API operations
- **Celebration Effects**: Positive reinforcement on completion
- **Hover Effects**: Interactive feedback on hover (desktop)

## Development Guidelines

### Testing Strategy
```dart
// Widget testing for onboarding steps
testWidgets('Assistant creation step validates name input', (tester) async {
  await tester.pumpWidget(makeTestableWidget(AssistantCreationStep()));
  
  // Test name validation
  await tester.enterText(find.byType(TextField), '');
  expect(find.text('Please enter a name'), findsOneWidget);
});
```

### State Debugging
```dart
// Debug logging for onboarding state changes
void _logStateChange(String step, Map<String, dynamic> data) {
  if (kDebugMode) {
    print('Onboarding: $step updated with data: $data');
  }
}
```

### Code Organization
- **Single Responsibility**: Each step handles only its specific data
- **Reusable Components**: Shared widgets in `widgets/` directory
- **Error Boundaries**: Comprehensive error handling at component level
- **Type Safety**: Strong typing for all data models and API responses

## Future Enhancements

### Planned Features
1. **Enhanced Personalization**: More personality traits and customization options
2. **Skip Patterns**: Smart skip logic based on user behavior
3. **Progress Analytics**: Track completion rates and drop-off points
4. **A/B Testing**: Framework for testing different onboarding flows
5. **Multi-language Support**: Full internationalization support

### Technical Improvements
1. **Offline Support**: Local storage with sync when online
2. **Enhanced Animations**: More sophisticated animation system
3. **Performance Monitoring**: Real-time performance metrics
4. **Advanced Error Recovery**: More sophisticated retry logic
5. **State Persistence**: Better handling of app state restoration

## Troubleshooting

### Common Issues

#### API Connection Problems
```bash
# Check backend connectivity
curl http://localhost:8000/api/onboarding/state

# Verify authentication token
flutter logs | grep "auth"
```

#### State Synchronization Issues
```dart
// Force refresh onboarding state
await ref.read(onboardingProvider.notifier).checkOnboardingStatus();

// Reset onboarding if corrupted
await ref.read(onboardingProvider.notifier).resetOnboarding();
```

#### Build Issues
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs
```

### Debug Commands
```bash
# Run with debug logging
flutter run -d macos --debug

# Test specific onboarding screens
flutter test test/screens/onboarding/

# Check network calls
flutter logs | grep "API"
```

This onboarding implementation provides a comprehensive, engaging user experience that effectively introduces new users to SelfOS while collecting essential personalization data for their AI assistant. The system is production-ready with robust error handling, rate limiting, and accessibility features.