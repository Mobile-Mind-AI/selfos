# Onboarding Flow Documentation

## Overview

The SelfOS onboarding flow is a narrative-style, gamified user experience that guides new users through setting up their AI assistant and initial preferences. Following the "Start Your Story" concept, the onboarding creates an engaging introduction to the SelfOS platform while collecting essential user preferences.

## Architecture

### Core Components

#### Backend Integration
- **OnboardingState Model**: Tracks user progress through onboarding steps
- **API Endpoints**: Complete state management and step processing
- **Database Persistence**: User preferences and progress stored permanently
- **MCP Integration**: Onboarding tools available for AI agents

#### Frontend Implementation
- **Flutter Screens**: 6 interactive onboarding steps with animations
- **Provider Architecture**: Riverpod-based state management
- **Route Protection**: Authentication-aware navigation
- **Progress Tracking**: Visual progress indicators and step validation

## User Flow

### The "Start Your Story" Journey

The onboarding follows a narrative structure where the user is the hero creating their AI companion:

```
1. Welcome → 2. Assistant Creation → 3. Personality Setup → 
4. Language Preferences → 5. Life Areas → 6. First Goal → Dashboard
```

## Implementation Details

### 1. Welcome Step (`welcome_step.dart`)
**Purpose**: Introduction to SelfOS with engaging visuals and narrative setup

**Features**:
- Animated SelfOS branding and logo
- Narrative introduction text
- "Start Your Story" call-to-action
- Skip option for returning users
- Smooth transition animations

**UI Elements**:
```dart
// Key components
- Hero animation for logo
- Gradient background with brand colors
- Typography hierarchy with engaging copy
- Primary action button (Continue)
- Secondary action button (Skip)
```

### 2. Assistant Creation (`assistant_creation_step.dart`)
**Purpose**: Personal AI assistant setup with name and avatar selection

**Features**:
- Text input for assistant naming
- Avatar selection gallery with diverse options
- Real-time preview of assistant card
- Name validation and suggestions
- Character limit enforcement (1-100 characters)

**Data Collection**:
```json
{
  "name": "String (1-100 chars)",
  "avatar_url": "String (optional)"
}
```

### 3. Personality Setup (`personality_setup_step.dart`)
**Purpose**: AI assistant personality customization through interactive sliders

**Features**:
- 5-trait personality system with 0-100 scale sliders:
  - **Formality**: Formal (0) ↔ Casual (100)
  - **Directness**: Diplomatic (0) ↔ Direct (100)
  - **Humor**: Serious (0) ↔ Playful (100)
  - **Empathy**: Analytical (0) ↔ Warm (100)
  - **Motivation**: Calm (0) ↔ Energetic (100)
- Real-time personality preview with sample messages
- Visual trait descriptions and examples
- Preset personality templates (optional)

**Data Collection**:
```json
{
  "style": {
    "formality": 60,
    "directness": 70,
    "humor": 40,
    "empathy": 80,
    "motivation": 75
  }
}
```

### 4. Language Preferences (`language_preferences_step.dart`)
**Purpose**: Communication language and interaction preferences

**Features**:
- Multi-language selection (8 supported languages)
- Confirmation preference toggle
- Sample conversation preview in selected language
- Accessibility considerations for language selection

**Supported Languages**:
- English (en), Spanish (es), French (fr), German (de)
- Italian (it), Portuguese (pt), Chinese (zh), Japanese (ja)

**Data Collection**:
```json
{
  "language": "en",
  "requires_confirmation": true
}
```

### 5. Life Areas Selection (`life_areas_step.dart`)
**Purpose**: Personal life area categorization for goal organization

**Features**:
- Grid-based selection interface with visual icons
- Pre-defined life areas with descriptions:
  - Health & Fitness
  - Career & Professional
  - Relationships & Social
  - Finance & Money
  - Personal Development
  - Education & Learning
  - Recreation & Hobbies
  - Spiritual & Mindfulness
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

### 6. First Goal Creation (`first_goal_step.dart`)
**Purpose**: Initial goal setup to demonstrate SelfOS functionality

**Features**:
- Goal title and description input
- Life area association dropdown
- Optional AI task generation toggle
- Goal validation and formatting
- Preview of goal structure
- SMART goal guidance prompts

**Data Collection**:
```json
{
  "title": "Learn Spanish",
  "description": "Become conversational in Spanish within 6 months",
  "life_area_id": 6,
  "generate_tasks": true
}
```

### 7. Completion Step (`completion_step.dart`)
**Purpose**: Celebration and summary of onboarding setup

**Features**:
- Celebration animations and visual feedback
- Summary of created assistant and preferences
- Welcome message from personalized AI assistant
- Dashboard preparation and navigation
- Success metrics and encouragement

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

// Update specific onboarding step
Future<bool> updateOnboardingStep(String step, Map<String, dynamic> data)

// Complete full onboarding flow
Future<bool> completeOnboarding()

// Skip onboarding with defaults
Future<bool> skipOnboarding()
```

### API Integration

#### Backend Endpoints
```http
GET    /api/onboarding/state              # Current user onboarding status
POST   /api/onboarding/step               # Update specific step
POST   /api/onboarding/complete           # Mark onboarding complete
POST   /api/onboarding/skip               # Skip with default setup
GET    /api/onboarding/preview-personality # Preview personality settings
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

#### Route Protection
The onboarding flow is integrated into the app's navigation system with automatic redirects:

```dart
// Route redirect logic in routes.dart
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

## Error Handling

### Frontend Error States
```dart
// Error handling in onboarding screens
try {
  final success = await ref.read(onboardingProvider.notifier).updateOnboardingStep(step, data);
  if (!success) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Failed to save progress. Please try again.')),
    );
  }
} catch (e) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text('Error: $e')),
  );
}
```

### Backend Error Responses
```python
# API error handling
try:
    state = create_onboarding_step(user_id, step_data)
    return OnboardingStepResponse(success=True, current_step=state.current_step)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
except Exception as e:
    logger.error(f"Onboarding error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

## Testing Strategy

### Unit Tests
- Individual step component rendering
- Form validation logic
- State management operations
- API integration functions

### Integration Tests
- Complete onboarding flow end-to-end
- Navigation redirect logic
- Backend API communication
- Database state persistence

### User Acceptance Tests
- Onboarding completion rates
- User experience metrics
- Accessibility compliance
- Cross-platform compatibility

## Performance Considerations

### Optimization Strategies
1. **Lazy Loading**: Screens loaded on-demand during navigation
2. **State Persistence**: Onboarding progress saved after each step
3. **Error Recovery**: Automatic retry and manual refresh options
4. **Network Efficiency**: Minimal API calls with batched updates
5. **Memory Management**: Proper disposal of controllers and animations

### Metrics Tracking
```dart
// Performance metrics collection
class OnboardingMetrics {
  final Duration totalTime;        // Total onboarding completion time
  final Duration stepTimes;        // Individual step completion times
  final int retryAttempts;         // Number of error retries
  final bool skipped;              // Whether user skipped onboarding
  final String completionPath;    // Path through onboarding steps
}
```

## Accessibility Features

### Screen Reader Support
- Semantic labels for all interactive elements
- Screen reader announcements for step transitions
- Alternative text for images and icons
- Keyboard navigation support

### Visual Accessibility
- High contrast color options
- Scalable text with proper typography hierarchy
- Color-blind friendly color schemes
- Reduced motion options for animations

### Internationalization
- Multi-language text support
- Right-to-left language compatibility
- Cultural sensitivity in content and imagery
- Localized number and date formats

## Customization Options

### Developer Configuration
```dart
// Onboarding configuration options
class OnboardingConfig {
  static const bool enableSkipOption = true;
  static const int maxSteps = 6;
  static const Duration stepTimeout = Duration(minutes: 10);
  static const bool enableProgressBar = true;
  static const bool enableAnimations = true;
}
```

### Content Customization
- Welcome message personalization
- Brand color and logo customization
- Step order and optional steps
- Language and locale variants
- Default personality presets

## Future Enhancements

### Planned Features
1. **Dynamic Onboarding**: Adaptive flow based on user type
2. **Progress Resume**: Continue onboarding from any device
3. **Social Integration**: Import preferences from social profiles
4. **Advanced Personalization**: ML-driven recommendation engine
5. **Onboarding Analytics**: Detailed user journey analytics

### Technical Improvements
1. **Micro-animations**: Enhanced visual feedback
2. **Voice Introduction**: Audio-guided onboarding option
3. **AR/VR Support**: Immersive onboarding experience
4. **Progressive Web App**: Enhanced web experience
5. **Offline Capability**: Complete onboarding without internet

## Best Practices

### Development Guidelines
1. **State Immutability**: All state changes through providers
2. **Error Boundaries**: Comprehensive error handling at each step
3. **Progress Persistence**: Save state after each successful step
4. **User Feedback**: Clear success/error messages
5. **Performance Monitoring**: Track completion rates and errors

### UX Guidelines
1. **Clear Progress**: Always show current step and total progress
2. **Easy Navigation**: Allow backward navigation when appropriate
3. **Skip Options**: Provide escape routes for experienced users
4. **Help Context**: Contextual help and tooltips
5. **Celebration**: Acknowledge user completion and achievements

This onboarding implementation provides a comprehensive, engaging user experience that effectively introduces new users to SelfOS while collecting essential personalization data for their AI assistant.