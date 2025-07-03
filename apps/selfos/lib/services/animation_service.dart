import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Central service for managing animations across the app
class AnimationService {
  static AnimationService? _instance;
  static AnimationService get instance => _instance ??= AnimationService._();

  AnimationService._();

  // Animation performance settings
  bool _reducedMotion = false;
  bool _highPerformanceMode = false;
  double _animationSpeed = 1.0;

  // Performance monitoring
  final List<double> _frameTimes = [];
  bool _performanceMonitoringEnabled = true;

  // Animation state tracking
  final Map<String, AnimationController> _activeControllers = {};
  final Map<String, bool> _animationStates = {};

  /// Initialize the animation service
  Future<void> initialize() async {
    await _loadUserPreferences();
    await _detectDeviceCapabilities();
    _startPerformanceMonitoring();
  }

  /// Load user animation preferences
  Future<void> _loadUserPreferences() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _reducedMotion = prefs.getBool('reduced_motion') ?? false;
      _animationSpeed = prefs.getDouble('animation_speed') ?? 1.0;

      // Also check system accessibility settings
      final accessibilityFeatures = MediaQueryData.fromView(
        WidgetsBinding.instance.platformDispatcher.views.first
      ).accessibleNavigation;

      if (accessibilityFeatures) {
        _reducedMotion = true;
      }
    } catch (e) {
      debugPrint('Failed to load animation preferences: $e');
    }
  }

  /// Detect device animation capabilities
  Future<void> _detectDeviceCapabilities() async {
    // Simple heuristic based on platform and available memory
    try {
      // Enable high performance mode for newer devices
      _highPerformanceMode = !_reducedMotion;
    } catch (e) {
      debugPrint('Failed to detect device capabilities: $e');
      _highPerformanceMode = false;
    }
  }

  /// Start monitoring animation performance
  void _startPerformanceMonitoring() {
    if (!_performanceMonitoringEnabled) return;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _monitorFrameRate();
    });
  }

  /// Monitor frame rate and adjust performance accordingly
  void _monitorFrameRate() {
    if (!_performanceMonitoringEnabled) return;

    final now = DateTime.now().millisecondsSinceEpoch.toDouble();
    _frameTimes.add(now);

    // Keep only recent frame times (last 60 frames)
    if (_frameTimes.length > 60) {
      _frameTimes.removeAt(0);
    }

    // Calculate average FPS over recent frames
    if (_frameTimes.length >= 10) {
      final avgFrameTime = _calculateAverageFrameTime();
      final fps = 1000 / avgFrameTime;

      // Auto-adjust performance if FPS drops below 45
      if (fps < 45 && _highPerformanceMode) {
        _degradePerformance();
      } else if (fps > 55 && !_highPerformanceMode && !_reducedMotion) {
        _improvePerformance();
      }
    }

    // Schedule next monitoring
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _monitorFrameRate();
    });
  }

  /// Calculate average frame time
  double _calculateAverageFrameTime() {
    if (_frameTimes.length < 2) return 16.67; // Default to 60fps

    double totalTime = 0;
    for (int i = 1; i < _frameTimes.length; i++) {
      totalTime += _frameTimes[i] - _frameTimes[i - 1];
    }

    return totalTime / (_frameTimes.length - 1);
  }

  /// Reduce animation quality for better performance
  void _degradePerformance() {
    debugPrint('AnimationService: Degrading performance for better FPS');
    _highPerformanceMode = false;
    _animationSpeed = 0.7; // Slightly faster animations
  }

  /// Improve animation quality when performance allows
  void _improvePerformance() {
    debugPrint('AnimationService: Improving animation quality');
    _highPerformanceMode = true;
    _animationSpeed = 1.0;
  }

  /// Register an animation controller for management
  void registerController(String id, AnimationController controller) {
    _activeControllers[id] = controller;
    _animationStates[id] = false;

    // Add listener to track animation state
    controller.addStatusListener((status) {
      _animationStates[id] = status == AnimationStatus.forward ||
                           status == AnimationStatus.reverse;
    });
  }

  /// Unregister an animation controller
  void unregisterController(String id) {
    _activeControllers.remove(id);
    _animationStates.remove(id);
  }

  /// Get recommended animation duration based on current settings
  Duration getAnimationDuration(Duration baseDuration) {
    if (_reducedMotion) {
      return Duration(milliseconds: (baseDuration.inMilliseconds * 0.3).round());
    }

    final adjustedMs = (baseDuration.inMilliseconds / _animationSpeed).round();
    return Duration(milliseconds: adjustedMs);
  }

  /// Get animation curve based on performance settings
  Curve getAnimationCurve(Curve baseCurve) {
    if (_reducedMotion) {
      return Curves.linear;
    }

    if (!_highPerformanceMode) {
      // Use simpler curves for better performance
      if (baseCurve == Curves.elasticOut) return Curves.easeOut;
      if (baseCurve == Curves.bounceOut) return Curves.easeOut;
    }

    return baseCurve;
  }

  /// Check if advanced animations should be enabled
  bool get shouldUseAdvancedAnimations =>
      !_reducedMotion && _highPerformanceMode;

  /// Check if particle animations should be enabled
  bool get shouldUseParticleAnimations =>
      !_reducedMotion && _highPerformanceMode;

  /// Check if morphing animations should be enabled
  bool get shouldUseMorphingAnimations =>
      !_reducedMotion && _highPerformanceMode;

  /// Check if parallax effects should be enabled
  bool get shouldUseParallaxEffects =>
      !_reducedMotion && _highPerformanceMode;

  /// Get animation scale factor for consistent scaling
  double get animationScale {
    if (_reducedMotion) return 0.5;
    return _highPerformanceMode ? 1.0 : 0.8;
  }

  /// Pause all animations (useful for app lifecycle changes)
  void pauseAllAnimations() {
    for (final controller in _activeControllers.values) {
      if (controller.isAnimating) {
        controller.stop();
      }
    }
  }

  /// Resume all paused animations
  void resumeAllAnimations() {
    for (final entry in _animationStates.entries) {
      if (entry.value) { // Was animating before pause
        final controller = _activeControllers[entry.key];
        controller?.forward();
      }
    }
  }

  /// Dispose all managed controllers
  void dispose() {
    for (final controller in _activeControllers.values) {
      controller.dispose();
    }
    _activeControllers.clear();
    _animationStates.clear();
    _performanceMonitoringEnabled = false;
  }

  /// Create haptic feedback for animations (if enabled)
  void triggerHapticFeedback({HapticFeedbackType type = HapticFeedbackType.lightImpact}) {
    if (!_reducedMotion) {
      HapticFeedback.lightImpact();
    }
  }

  /// Update user preferences
  Future<void> updatePreferences({
    bool? reducedMotion,
    double? animationSpeed,
  }) async {
    if (reducedMotion != null) _reducedMotion = reducedMotion;
    if (animationSpeed != null) _animationSpeed = animationSpeed;

    // Save to preferences
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('reduced_motion', _reducedMotion);
    await prefs.setDouble('animation_speed', _animationSpeed);
  }

  /// Get current performance metrics
  Map<String, dynamic> getPerformanceMetrics() {
    return {
      'reducedMotion': _reducedMotion,
      'highPerformanceMode': _highPerformanceMode,
      'animationSpeed': _animationSpeed,
      'activeAnimations': _animationStates.values.where((v) => v).length,
      'totalControllers': _activeControllers.length,
      'averageFPS': _frameTimes.length >= 10 ? 1000 / _calculateAverageFrameTime() : null,
    };
  }
}

/// Provider for the animation service
final animationServiceProvider = Provider<AnimationService>((ref) {
  return AnimationService.instance;
});

/// Provider for animation preferences
final animationPreferencesProvider = StateNotifierProvider<AnimationPreferencesNotifier, AnimationPreferences>((ref) {
  return AnimationPreferencesNotifier();
});

/// Animation preferences state
class AnimationPreferences {
  final bool reducedMotion;
  final double animationSpeed;
  final bool highPerformanceMode;

  const AnimationPreferences({
    this.reducedMotion = false,
    this.animationSpeed = 1.0,
    this.highPerformanceMode = true,
  });

  AnimationPreferences copyWith({
    bool? reducedMotion,
    double? animationSpeed,
    bool? highPerformanceMode,
  }) {
    return AnimationPreferences(
      reducedMotion: reducedMotion ?? this.reducedMotion,
      animationSpeed: animationSpeed ?? this.animationSpeed,
      highPerformanceMode: highPerformanceMode ?? this.highPerformanceMode,
    );
  }
}

/// Notifier for animation preferences
class AnimationPreferencesNotifier extends StateNotifier<AnimationPreferences> {
  AnimationPreferencesNotifier() : super(const AnimationPreferences());

  void updateReducedMotion(bool value) {
    state = state.copyWith(reducedMotion: value);
    AnimationService.instance.updatePreferences(reducedMotion: value);
  }

  void updateAnimationSpeed(double value) {
    state = state.copyWith(animationSpeed: value);
    AnimationService.instance.updatePreferences(animationSpeed: value);
  }

  void updateHighPerformanceMode(bool value) {
    state = state.copyWith(highPerformanceMode: value);
  }
}