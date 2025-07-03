import 'package:flutter/material.dart';
import '../../widgets/welcome/hero_section.dart';
import '../../widgets/welcome/welcome_text.dart';
import '../../widgets/welcome/feature_cards.dart';
import '../../widgets/welcome/story_introduction.dart';
import '../../widgets/welcome/welcome_actions.dart';

/// Welcome step that introduces users to SelfOS and the onboarding concept.
///
/// This is the first step in the "Start Your Story" narrative onboarding.
/// Composed of reusable, animated components for better maintainability.
class WelcomeStep extends StatefulWidget {
  final VoidCallback onNext;
  final VoidCallback onSkip;

  const WelcomeStep({
    super.key,
    required this.onNext,
    required this.onSkip,
  });

  @override
  State<WelcomeStep> createState() => _WelcomeStepState();
}

class _WelcomeStepState extends State<WelcomeStep> {

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
          // Main content
          Expanded(
            child: _buildMainContent(isWideScreen),
          ),

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

  Widget _buildMainContent(bool isWideScreen) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
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

        // Add space at bottom
        const SizedBox(height: 20),
      ],
    );
  }

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

  Widget _buildWelcomeText() {
    return WelcomeText(
      rotationInterval: const Duration(seconds: 3),
      entranceDelay: const Duration(milliseconds: 200),
      enableRotation: true,
      onMessageChange: _handleMessageChange,
    );
  }

  Widget _buildFeatureCards(bool isWideScreen) {
    return FeatureCards.defaultFeatures(
      sectionTitle: "What makes SelfOS special?",
      isResponsive: true,
      enableHoverEffects: true,
    );
  }

  Widget _buildStoryIntroduction() {
    return StoryIntroduction(
      entranceDelay: const Duration(milliseconds: 600),
      onTap: _handleStoryTap,
    );
  }

  Widget _buildBottomActions() {
    return WelcomeActions.onboarding(
      onNext: widget.onNext,
      onSkip: widget.onSkip,
      enableHoverEffects: true,
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
    debugPrint('Welcome message changed');
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