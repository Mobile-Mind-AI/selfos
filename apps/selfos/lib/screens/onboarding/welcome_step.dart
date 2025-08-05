import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../widgets/welcome/hero_section.dart';
import '../../widgets/welcome/welcome_text.dart';
import '../../widgets/welcome/feature_cards.dart';
import '../../widgets/welcome/story_introduction.dart';
import '../../widgets/welcome/welcome_actions.dart';
import '../../services/auth_service.dart';
import '../../services/storage_service.dart';
import '../../services/auth_provider.dart';

/// Represents the Welcome step in the onboarding process.
///
/// This widget is a stateful consumer widget that builds the UI for the
/// welcome step of the onboarding process. It includes various sections
/// such as a hero section, welcome text, feature cards, and bottom actions.
///
/// Parameters:
/// - `onNext`: A callback function triggered when the user proceeds to the next step.
class WelcomeStep extends ConsumerStatefulWidget {
  final VoidCallback onNext;

  const WelcomeStep({
    super.key,
    required this.onNext,
  });

  @override
  ConsumerState<WelcomeStep> createState() => _WelcomeStepState();
}
/// Represents the state for the `WelcomeStep` widget in the onboarding process.
///
/// This class manages the state and behavior of the `WelcomeStep` widget,
/// including initialization, event handling, and building the UI components.
///
/// State Variables:
/// - `_isHeroHovered`: A `bool` indicating whether the hero section is being hovered.
/// - `_isInitialized`: A `bool` indicating whether the step has been initialized.
///
/// Methods:
/// - `initState`: Initializes the state and calls `_initializeStep`.
/// - `_initializeStep`: Marks the step as initialized and updates the state.
/// - `build`: Constructs the widget tree for the `WelcomeStep` screen.
/// - `_buildLoadingState`: Builds a loading indicator widget.
/// - `_buildMainContent`: Builds the main content of the screen.
/// - `_buildHeroSection`: Builds the hero section widget.
/// - `_buildWelcomeText`: Builds the welcome text widget.
/// - `_buildFeatureCards`: Builds the feature cards widget.
/// - `_buildStoryIntroduction`: Builds the story introduction widget.
/// - `_buildBottomActions`: Builds the bottom actions widget.
/// - `_handleHeroHover`: Handles the hover event for the hero section.
/// - `_handleHeroHoverExit`: Handles the hover exit event for the hero section.
/// - `_handleMessageChange`: Handles the event when the welcome message changes.
/// - `_handleStoryTap`: Handles the tap event for the story introduction.
/// - `componentStates`: Provides the current state information as a map.
class _WelcomeStepState extends ConsumerState<WelcomeStep> {

  // State tracking
  bool _isHeroHovered = false;
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    _initializeStep();
  }

  void _initializeStep() {
    // Mark as initialized immediately for this simple case
    // In a more complex scenario, you might load user preferences here
    setState(() {
      _isInitialized = true;
    });
  }

  /// Builds the widget tree for the `WelcomeStep` screen.
  ///
  /// This method constructs the UI for the welcome step in the onboarding process.
  /// It includes:
  /// - A loading state if the step is not initialized.
  /// - A scrollable main content area with sections such as hero, welcome text, feature cards, and story introduction.
  /// - Bottom actions for navigation.
  ///
  /// Parameters:
  /// - `context`: The `BuildContext` object that provides access to the widget tree and theme.
  ///
  /// Returns:
  ///   A `Widget` representing the complete screen layout.
  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final isWideScreen = screenSize.width > 768;

    if (!_isInitialized) {
      return _buildLoadingState();
    }

    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: isWideScreen ? 48.0 : 24.0,
        vertical: 24.0,
      ),
      child: Column(
        children: [
          // Main content scrollable
          Expanded(
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              child: Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: _buildMainContent(isWideScreen),
              ),
            ),
          ),

          // Add space before bottom actions
          const SizedBox(height: 40),

          // Bottom actions
          _buildBottomActions(),
        ],
      ),
    );
  }

  Widget _buildLoadingState() {
    return const Center(
      child: CircularProgressIndicator(),
    );
  }
  /// Builds the main content for the `WelcomeStep` screen.
  ///
  /// This method constructs the primary UI components for the welcome step,
  /// including sections such as the hero, welcome text, feature cards, and story introduction.
  /// It also includes a temporary logout button for debugging purposes.
  ///
  /// Parameters:
  /// - `isWideScreen`: A `bool` indicating whether the screen width exceeds 768 pixels,
  ///   which affects the layout and responsiveness of the content.
  ///
  /// Returns:
  ///   A `Widget` representing the main content layout.
  Widget _buildMainContent(bool isWideScreen) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // TEMPORARY: Logout button for testing
        TextButton(
          onPressed: () async {
            print('🔴 DEBUG: Force logout initiated');
            
            // Properly logout through the auth provider
            await ref.read(authProvider.notifier).logout();
            
            print('✅ DEBUG: Logout completed');
            
            // The router will automatically redirect based on auth state change
            // No need to manually navigate
          },
          child: const Text('DEBUG: Force Logout', style: TextStyle(color: Colors.red)),
        ),
        
        // Add space at top to move hero higher
        const SizedBox(height: 20),

        // Hero section with animated brain and orbiting dots
        _buildHeroSection(),

        const SizedBox(height: 40),

        // Welcome text with time-based greetings and rotating messages
        _buildWelcomeText(),

        const SizedBox(height: 32),

        // Interactive feature highlights
        _buildFeatureCards(isWideScreen),

        const SizedBox(height: 24),

        // Story introduction section
        _buildStoryIntroduction(),
      ],
    );
  }
  /// Builds the hero section for the `WelcomeStep` screen.
  ///
  /// This method constructs the hero section widget, which includes an animated
  /// brain with orbiting dots and hover effects. It provides interactivity through
  /// hover event handlers.
  ///
  /// Returns:
  ///   A `HeroSection` widget configured with animation durations, hover effects,
  ///   and event handlers.
  Widget _buildHeroSection() {
    return HeroSection(
      size: 280,
      orbitDuration: const Duration(seconds: 8),
      pulseDuration: const Duration(seconds: 2),
      enableHoverEffect: true,
      onHover: _handleHeroHover,
      onHoverExit: _handleHeroHoverExit,
    );
  }
  /// Builds the welcome text section for the `WelcomeStep` screen.
  ///
  /// This method constructs a `WelcomeText` widget that displays a custom title,
  /// subtitle, and rotating messages. It includes configurable rotation intervals,
  /// entrance delays, and an event handler for message changes.
  ///
  /// Returns:
  ///   A `WelcomeText` widget configured with custom text, rotation settings,
  ///   and interactivity.
  Widget _buildWelcomeText() {
    return WelcomeText(
      customTitle: "Welcome to SelfOS",
      customSubtitle: "Just 2 simple steps to personalize your experience",
      customMessages: [
        "You'll configure your AI assistant and tell us about yourself",
        "Get ready for a personalized journey towards your goals",
        "Your AI companion will learn and grow with you",
      ],
      rotationInterval: const Duration(seconds: 4),
      entranceDelay: const Duration(milliseconds: 200),
      enableRotation: true,
      onMessageChange: _handleMessageChange,
    );
  }
  /// Builds the feature cards section for the `WelcomeStep` screen.
  ///
  /// This method constructs a `FeatureCards` widget that highlights the key features
  /// of SelfOS. It includes responsive design and hover effects for interactivity.
  ///
  /// Parameters:
  /// - `isWideScreen`: A `bool` indicating whether the screen width exceeds 768 pixels,
  ///   which affects the layout and responsiveness of the feature cards.
  ///
  /// Returns:
  ///   A `FeatureCards` widget configured with default features, hover effects,
  ///   and responsive design.
  Widget _buildFeatureCards(bool isWideScreen) {
    return FeatureCards.defaultFeatures(
      sectionTitle: "What makes SelfOS special?",
      isResponsive: true,
      enableHoverEffects: true,
    );
  }
  /// Builds the story introduction section for the `WelcomeStep` screen.
  ///
  /// This method constructs a `StoryIntroduction` widget that provides a brief
  /// overview of the onboarding process and encourages the user to begin their journey.
  /// It includes a title, description, icon, and entrance delay for animations.
  ///
  /// Returns:
  ///   A `StoryIntroduction` widget configured with text, icon, and interactivity.
  Widget _buildStoryIntroduction() {
    return StoryIntroduction(
      title: "Ready to Begin?",
      description: "In just 2 steps, you'll have a personalized AI assistant that understands your goals and helps you achieve them.",
      icon: Icons.rocket_launch,
      entranceDelay: const Duration(milliseconds: 600),
      onTap: _handleStoryTap,
    );
  }
  /// Builds the bottom actions section for the `WelcomeStep` screen.
  ///
  /// This method constructs a `WelcomeActions` widget that provides navigation
  /// options for the user. It includes a primary button to start the journey
  /// and disables the secondary button for skipping the step.
  ///
  /// Returns:
  ///   A `WelcomeActions` widget configured with text, icons, and interactivity.
  Widget _buildBottomActions() {
    return WelcomeActions(
      primaryText: 'Start Journey',
      secondaryText: '', // No secondary button
      primaryIcon: Icons.rocket_launch,
      onPrimaryPressed: () {
        print('🚀 WELCOME: Start Journey button pressed');
        widget.onNext();
      },
      onSecondaryPressed: null, // Disable skip
      secondaryEnabled: false,
      enableHoverEffects: true,
      enableIconAnimation: true,
      entranceDelay: Duration.zero, // Remove entrance delay to enable immediate clicks
    );
  }

  // Event handlers
  void _handleHeroHover() {
    setState(() {
      _isHeroHovered = true;
    });
  }

  void _handleHeroHoverExit() {
    setState(() {
      _isHeroHovered = false;
    });
  }

  void _handleMessageChange() {
    // Could add analytics tracking here
    // debugPrint('Welcome message changed');
  }

  void _handleStoryTap() {
    // Could trigger additional animations or info
    debugPrint('Story introduction tapped');
  }

  // Public methods for external control

  /// Get current state information
  Map<String, dynamic> get componentStates => {
    'isHeroHovered': _isHeroHovered,
    'isInitialized': _isInitialized,
  };
}