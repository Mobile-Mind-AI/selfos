import 'package:flutter/material.dart';

/// Animation configuration and presets for consistent animations across the app
class AnimationConfig {
  // Base durations for different types of animations
  static const Duration ultraFast = Duration(milliseconds: 150);
  static const Duration fast = Duration(milliseconds: 250);
  static const Duration medium = Duration(milliseconds: 400);
  static const Duration slow = Duration(milliseconds: 600);
  static const Duration ultraSlow = Duration(milliseconds: 1000);

  // Welcome screen specific durations
  static const Duration welcomeHeroEntry = Duration(milliseconds: 800);
  static const Duration welcomeTextStagger = Duration(milliseconds: 200);
  static const Duration welcomeFeatureStagger = Duration(milliseconds: 150);
  static const Duration welcomeParticleLoop = Duration(seconds: 3);
  static const Duration welcomeMorphCycle = Duration(seconds: 2);

  // Onboarding flow durations
  static const Duration stepTransition = Duration(milliseconds: 350);
  static const Duration progressBarUpdate = Duration(milliseconds: 400);
  static const Duration formFieldEntry = Duration(milliseconds: 200);
  static const Duration buttonPress = Duration(milliseconds: 100);

  // Common animation curves
  static const Curve easeInOutCubic = Curves.easeInOutCubic;
  static const Curve elasticOut = Curves.elasticOut;
  static const Curve bounceOut = Curves.bounceOut;
  static const Curve anticipate = Curves.anticipate;
  static const Curve overshoot = Curves.elasticOut;

  // Custom curves for specific effects
  static final Curve smoothEntry = Cubic(0.25, 0.1, 0.25, 1.0);
  static final Curve dramaticEntry = Cubic(0.68, -0.55, 0.265, 1.55);
  static final Curve gentleExit = Cubic(0.4, 0.0, 1.0, 1.0);
  static final Curve springy = Cubic(0.175, 0.885, 0.32, 1.275);

  // Performance-based curve alternatives
  static final Map<Curve, Curve> performanceFallbacks = {
    Curves.elasticOut: Curves.easeOut,
    Curves.bounceOut: Curves.easeOut,
    dramaticEntry: easeInOutCubic,
    springy: Curves.easeInOut,
  };
}

/// Welcome screen animation presets
class WelcomeAnimationPresets {
  // Hero animation configuration
  static const heroEntry = AnimationPreset(
    duration: AnimationConfig.welcomeHeroEntry,
    curve: AnimationConfig.smoothEntry,
    delay: Duration.zero,
    tags: ['hero', 'entry'],
  );

  // Text stagger animation
  static const textStagger = AnimationPreset(
    duration: AnimationConfig.medium,
    curve: AnimationConfig.easeInOutCubic,
    delay: Duration(milliseconds: 400),
    tags: ['text', 'stagger'],
  );

  // Feature highlight animations
  static const featureStagger = AnimationPreset(
    duration: AnimationConfig.fast,
    curve: AnimationConfig.springy,
    delay: Duration(milliseconds: 800),
    tags: ['features', 'stagger'],
  );

  // Particle system configuration
  static const particleSystem = ParticlePreset(
    count: 6,
    duration: AnimationConfig.welcomeParticleLoop,
    radius: 60.0,
    size: 8.0,
    colors: [
      Color(0xFFFF6B35), // Orange
      Color(0xFF4ECDC4), // Teal
      Color(0xFF45B7D1), // Blue
      Color(0xFF96CEB4), // Green
      Color(0xFFFEEAE6), // Light pink
      Color(0xFFDDA0DD), // Plum
    ],
    animationType: ParticleAnimationType.floating,
  );

  // Morphing icon configuration
  static const morphingIcon = MorphingPreset(
    duration: AnimationConfig.welcomeMorphCycle,
    curve: AnimationConfig.easeInOutCubic,
    shapes: [
      IconData(0xe0b7, fontFamily: 'MaterialIcons'), // psychology
      IconData(0xe1a3, fontFamily: 'MaterialIcons'), // auto_awesome
      IconData(0xe3f4, fontFamily: 'MaterialIcons'), // lightbulb_outline
      IconData(0xe80d, fontFamily: 'MaterialIcons'), // favorite
    ],
    colors: [
      Color(0xFF6366F1), // Primary
      Color(0xFF8B5CF6), // Purple
      Color(0xFF06B6D4), // Cyan
      Color(0xFF10B981), // Emerald
    ],
  );

  // Parallax layers configuration
  static const parallaxLayers = ParallaxPreset(
    layers: [
      ParallaxLayer(depth: 0.1, asset: null), // Background particles
      ParallaxLayer(depth: 0.3, asset: null), // Mid particles
      ParallaxLayer(depth: 0.6, asset: null), // Foreground elements
    ],
    sensitivity: 0.5,
    maxOffset: 20.0,
  );

  // Interactive card animations
  static const interactiveCard = InteractionPreset(
    hoverScale: 1.05,
    pressScale: 0.95,
    hoverDuration: Duration(milliseconds: 200),
    pressDuration: Duration(milliseconds: 100),
    shadowElevation: 8.0,
    borderRadius: 12.0,
  );
}

/// Onboarding step animation presets
class OnboardingAnimationPresets {
  // Step transition animations
  static const stepEntry = AnimationPreset(
    duration: AnimationConfig.stepTransition,
    curve: AnimationConfig.smoothEntry,
    delay: Duration.zero,
    tags: ['step', 'entry'],
  );

  static const stepExit = AnimationPreset(
    duration: AnimationConfig.fast,
    curve: AnimationConfig.gentleExit,
    delay: Duration.zero,
    tags: ['step', 'exit'],
  );

  // Progress bar animation
  static const progressUpdate = AnimationPreset(
    duration: AnimationConfig.progressBarUpdate,
    curve: AnimationConfig.easeInOutCubic,
    delay: Duration(milliseconds: 100),
    tags: ['progress'],
  );

  // Form field animations
  static const fieldEntry = AnimationPreset(
    duration: AnimationConfig.formFieldEntry,
    curve: Curves.easeOut,
    delay: Duration.zero,
    tags: ['form', 'field'],
  );

  // Button interaction animations
  static const buttonPress = AnimationPreset(
    duration: AnimationConfig.buttonPress,
    curve: Curves.easeInOut,
    delay: Duration.zero,
    tags: ['button', 'interaction'],
  );

  // Personality slider animations
  static const sliderUpdate = AnimationPreset(
    duration: Duration(milliseconds: 150),
    curve: Curves.easeOut,
    delay: Duration.zero,
    tags: ['slider', 'personality'],
  );

  // Preview card animations
  static const previewEntry = AnimationPreset(
    duration: AnimationConfig.medium,
    curve: AnimationConfig.springy,
    delay: Duration(milliseconds: 200),
    tags: ['preview', 'card'],
  );
}

/// Base animation preset class
class AnimationPreset {
  final Duration duration;
  final Curve curve;
  final Duration delay;
  final List<String> tags;

  const AnimationPreset({
    required this.duration,
    required this.curve,
    required this.delay,
    required this.tags,
  });

  /// Create a modified preset with different values
  AnimationPreset copyWith({
    Duration? duration,
    Curve? curve,
    Duration? delay,
    List<String>? tags,
  }) {
    return AnimationPreset(
      duration: duration ?? this.duration,
      curve: curve ?? this.curve,
      delay: delay ?? this.delay,
      tags: tags ?? this.tags,
    );
  }

  /// Get performance-optimized version of this preset
  AnimationPreset optimized({required bool reducedMotion, required bool highPerformance}) {
    if (reducedMotion) {
      return copyWith(
        duration: Duration(milliseconds: (duration.inMilliseconds * 0.3).round()),
        curve: Curves.linear,
      );
    }

    if (!highPerformance) {
      final fallbackCurve = AnimationConfig.performanceFallbacks[curve] ?? curve;
      return copyWith(
        curve: fallbackCurve,
        duration: Duration(milliseconds: (duration.inMilliseconds * 0.8).round()),
      );
    }

    return this;
  }
}

/// Particle animation preset
class ParticlePreset {
  final int count;
  final Duration duration;
  final double radius;
  final double size;
  final List<Color> colors;
  final ParticleAnimationType animationType;

  const ParticlePreset({
    required this.count,
    required this.duration,
    required this.radius,
    required this.size,
    required this.colors,
    required this.animationType,
  });
}

/// Morphing animation preset
class MorphingPreset {
  final Duration duration;
  final Curve curve;
  final List<IconData> shapes;
  final List<Color> colors;

  const MorphingPreset({
    required this.duration,
    required this.curve,
    required this.shapes,
    required this.colors,
  });
}

/// Parallax animation preset
class ParallaxPreset {
  final List<ParallaxLayer> layers;
  final double sensitivity;
  final double maxOffset;

  const ParallaxPreset({
    required this.layers,
    required this.sensitivity,
    required this.maxOffset,
  });
}

/// Parallax layer definition
class ParallaxLayer {
  final double depth;
  final String? asset;

  const ParallaxLayer({
    required this.depth,
    this.asset,
  });
}

/// Interactive element preset
class InteractionPreset {
  final double hoverScale;
  final double pressScale;
  final Duration hoverDuration;
  final Duration pressDuration;
  final double shadowElevation;
  final double borderRadius;

  const InteractionPreset({
    required this.hoverScale,
    required this.pressScale,
    required this.hoverDuration,
    required this.pressDuration,
    required this.shadowElevation,
    required this.borderRadius,
  });
}

/// Particle animation types
enum ParticleAnimationType {
  floating,
  orbiting,
  pulsing,
  shooting,
  swirling,
}

/// Animation preset finder utility
class AnimationPresetFinder {
  static final Map<String, List<AnimationPreset>> _presetsByTag = {
    'hero': [WelcomeAnimationPresets.heroEntry],
    'text': [WelcomeAnimationPresets.textStagger],
    'stagger': [
      WelcomeAnimationPresets.textStagger,
      WelcomeAnimationPresets.featureStagger,
    ],
    'entry': [
      WelcomeAnimationPresets.heroEntry,
      OnboardingAnimationPresets.stepEntry,
      OnboardingAnimationPresets.fieldEntry,
      OnboardingAnimationPresets.previewEntry,
    ],
    'step': [
      OnboardingAnimationPresets.stepEntry,
      OnboardingAnimationPresets.stepExit,
    ],
    'form': [OnboardingAnimationPresets.fieldEntry],
    'button': [OnboardingAnimationPresets.buttonPress],
    'progress': [OnboardingAnimationPresets.progressUpdate],
  };

  /// Find presets by tag
  static List<AnimationPreset> findByTag(String tag) {
    return _presetsByTag[tag] ?? [];
  }

  /// Find preset by multiple tags (intersection)
  static List<AnimationPreset> findByTags(List<String> tags) {
    if (tags.isEmpty) return [];

    List<AnimationPreset> result = findByTag(tags.first);

    for (int i = 1; i < tags.length; i++) {
      final tagPresets = findByTag(tags[i]);
      result = result.where((preset) => tagPresets.contains(preset)).toList();
    }

    return result;
  }

  /// Get all available tags
  static List<String> getAllTags() {
    return _presetsByTag.keys.toList();
  }
}

/// Stagger animation utility
class StaggerConfig {
  final Duration baseDelay;
  final Duration increment;
  final int maxItems;
  final Curve curve;

  const StaggerConfig({
    required this.baseDelay,
    required this.increment,
    required this.maxItems,
    this.curve = Curves.easeOut,
  });

  /// Calculate delay for item at index
  Duration delayForIndex(int index) {
    final clampedIndex = index.clamp(0, maxItems - 1);
    return baseDelay + (increment * clampedIndex);
  }

  /// Get all delays for the stagger
  List<Duration> getAllDelays() {
    return List.generate(
      maxItems,
      (index) => delayForIndex(index),
    );
  }

  // Common stagger configurations
  static const welcomeFeatures = StaggerConfig(
    baseDelay: Duration(milliseconds: 800),
    increment: Duration(milliseconds: 150),
    maxItems: 3,
  );

  static const onboardingSteps = StaggerConfig(
    baseDelay: Duration(milliseconds: 200),
    increment: Duration(milliseconds: 100),
    maxItems: 5,
  );

  static const formFields = StaggerConfig(
    baseDelay: Duration(milliseconds: 100),
    increment: Duration(milliseconds: 50),
    maxItems: 10,
  );
}