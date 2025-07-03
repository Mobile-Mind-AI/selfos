import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import '../services/animation_service.dart';

/// Enhanced animation controller wrapper with automatic performance optimization
/// and lifecycle management integrated with AnimationService
class CustomAnimationController extends AnimationController {
  final String id;
  final AnimationService _animationService;
  bool _isRegistered = false;
  bool _autoOptimize = true;

  // Performance tracking
  DateTime? _lastFrameTime;
  final List<double> _frameTimes = [];

  // Sequence management
  final List<AnimationSequenceStep> _sequence = [];
  int _currentSequenceIndex = 0;
  bool _isPlayingSequence = false;

  CustomAnimationController({
    required this.id,
    required Duration duration,
    required TickerProvider vsync,
    AnimationService? animationService,
    double? value,
    Duration? reverseDuration,
    String? debugLabel,
    AnimationBehavior animationBehavior = AnimationBehavior.normal,
    bool autoOptimize = true,
  }) : _animationService = animationService ?? AnimationService.instance,
       _autoOptimize = autoOptimize,
       super(
         duration: duration,
         reverseDuration: reverseDuration,
         value: value,
         debugLabel: debugLabel ?? 'CustomController_$id',
         vsync: vsync,
         animationBehavior: animationBehavior,
       ) {
    _initialize();
  }

  /// Initialize the controller and register with AnimationService
  void _initialize() {
    _register();
    _setupPerformanceMonitoring();
    _applyPerformanceOptimizations();
  }

  /// Register with AnimationService for centralized management
  void _register() {
    if (!_isRegistered) {
      _animationService.registerController(id, this);
      _isRegistered = true;
    }
  }

  /// Setup performance monitoring for this controller
  void _setupPerformanceMonitoring() {
    if (!_autoOptimize) return;

    addListener(_trackPerformance);
    addStatusListener(_handleStatusChange);
  }

  /// Track animation performance
  void _trackPerformance() {
    final now = DateTime.now();
    if (_lastFrameTime != null) {
      final frameTime = now.difference(_lastFrameTime!).inMicroseconds / 1000.0;
      _frameTimes.add(frameTime);

      // Keep only recent frames for analysis
      if (_frameTimes.length > 30) {
        _frameTimes.removeAt(0);
      }

      // Auto-optimize if performance degrades
      if (_frameTimes.length >= 10) {
        final avgFrameTime = _frameTimes.reduce((a, b) => a + b) / _frameTimes.length;
        if (avgFrameTime > 20 && _autoOptimize) { // > 50 FPS threshold
          _optimizeForPerformance();
        }
      }
    }
    _lastFrameTime = now;
  }

  /// Handle animation status changes
  void _handleStatusChange(AnimationStatus status) {
    if (status == AnimationStatus.completed && _isPlayingSequence) {
      _playNextSequenceStep();
    }
  }

  /// Apply performance optimizations based on AnimationService settings
  void _applyPerformanceOptimizations() {
    // Adjust duration based on service recommendations
    final optimizedDuration = _animationService.getAnimationDuration(duration);
    if (optimizedDuration != duration) {
      duration = optimizedDuration;
    }
  }

  /// Optimize animation for better performance
  void _optimizeForPerformance() {
    // Reduce animation complexity when performance drops
    final currentDuration = duration;
    duration = Duration(
      milliseconds: (currentDuration.inMilliseconds * 0.8).round(),
    );
    debugPrint('CustomAnimationController($id): Optimized duration to ${duration.inMilliseconds}ms');
  }

  /// Create an optimized animation with automatic curve adjustment
  Animation<T> createOptimizedAnimation<T>(
    Tween<T> tween, {
    Curve? curve,
    Duration? delay,
  }) {
    final optimizedCurve = curve != null
        ? _animationService.getAnimationCurve(curve)
        : Curves.easeInOut;

    late Animation<T> animation;

    if (delay != null && delay > Duration.zero) {
      // Create delayed animation
      final delayedController = AnimationController(
        duration: delay,
        vsync: vsync!,
      );

      final mainAnimation = tween.animate(
        CurvedAnimation(parent: this, curve: optimizedCurve),
      );

      animation = TweenSequence<T>([
        TweenSequenceItem(
          tween: ConstantTween<T>(tween.begin!),
          weight: delay.inMilliseconds.toDouble(),
        ),
        TweenSequenceItem(
          tween: tween,
          weight: duration.inMilliseconds.toDouble(),
        ),
      ]).animate(this);
    } else {
      animation = tween.animate(
        CurvedAnimation(parent: this, curve: optimizedCurve),
      );
    }

    return animation;
  }

  /// Create a spring-based animation with physics
  Animation<double> createSpringAnimation({
    required double target,
    double tension = 400,
    double friction = 30,
    double? initialVelocity,
  }) {
    if (!_animationService.shouldUseAdvancedAnimations) {
      // Fallback to simple animation for performance
      return Tween<double>(begin: value, end: target)
          .animate(CurvedAnimation(parent: this, curve: Curves.easeOut));
    }

    // Create spring simulation
    final simulation = SpringSimulation(
      SpringDescription(
        mass: 1.0,
        stiffness: tension,
        damping: friction,
      ),
      value,
      target,
      initialVelocity ?? velocity,
    );

    return _SpringAnimation(this, simulation);
  }

  /// Add step to animation sequence
  void addSequenceStep(AnimationSequenceStep step) {
    _sequence.add(step);
  }

  /// Play animation sequence
  Future<void> playSequence() async {
    if (_sequence.isEmpty) return;

    _isPlayingSequence = true;
    _currentSequenceIndex = 0;

    await _playCurrentSequenceStep();
  }

  /// Play current step in sequence
  Future<void> _playCurrentSequenceStep() async {
    if (_currentSequenceIndex >= _sequence.length) {
      _isPlayingSequence = false;
      return;
    }

    final step = _sequence[_currentSequenceIndex];

    // Apply step-specific settings
    duration = _animationService.getAnimationDuration(step.duration);

    // Execute step action
    if (step.action != null) {
      step.action!();
    }

    // Play animation
    switch (step.direction) {
      case AnimationDirection.forward:
        await forward();
        break;
      case AnimationDirection.reverse:
        await reverse();
        break;
      case AnimationDirection.reset:
        reset();
        break;
    }

    // Wait for delay if specified
    if (step.delay > Duration.zero) {
      await Future.delayed(step.delay);
    }
  }

  /// Play next step in sequence
  void _playNextSequenceStep() {
    _currentSequenceIndex++;
    if (_currentSequenceIndex < _sequence.length) {
      _playCurrentSequenceStep();
    } else {
      _isPlayingSequence = false;
    }
  }

  /// Clear animation sequence
  void clearSequence() {
    _sequence.clear();
    _currentSequenceIndex = 0;
    _isPlayingSequence = false;
  }

  /// Enhanced forward with performance optimization
  @override
  TickerFuture forward({double? from}) {
    _animationService.triggerHapticFeedback();
    return super.forward(from: from);
  }

  /// Enhanced reverse with performance optimization
  @override
  TickerFuture reverse({double? from}) {
    _animationService.triggerHapticFeedback();
    return super.reverse(from: from);
  }

  /// Create a staggered animation controller for multiple elements
  static List<CustomAnimationController> createStaggered({
    required String baseId,
    required int count,
    required Duration baseDuration,
    required Duration staggerDelay,
    required TickerProvider vsync,
    AnimationService? animationService,
  }) {
    final controllers = <CustomAnimationController>[];

    for (int i = 0; i < count; i++) {
      final controller = CustomAnimationController(
        id: '${baseId}_$i',
        duration: baseDuration,
        vsync: vsync,
        animationService: animationService,
      );

      // Add delay for staggered effect
      if (i > 0) {
        controller.addSequenceStep(
          AnimationSequenceStep(
            duration: staggerDelay * i,
            direction: AnimationDirection.reset,
            delay: Duration.zero,
          ),
        );
      }

      controllers.add(controller);
    }

    return controllers;
  }

  /// Get performance metrics for this controller
  Map<String, dynamic> getPerformanceMetrics() {
    return {
      'id': id,
      'averageFrameTime': _frameTimes.isNotEmpty
          ? _frameTimes.reduce((a, b) => a + b) / _frameTimes.length
          : null,
      'frameCount': _frameTimes.length,
      'currentValue': value,
      'isAnimating': isAnimating,
      'status': status.toString(),
      'duration': duration.inMilliseconds,
    };
  }

  @override
  void dispose() {
    if (_isRegistered) {
      _animationService.unregisterController(id);
      _isRegistered = false;
    }
    super.dispose();
  }
}

/// Animation sequence step definition
class AnimationSequenceStep {
  final Duration duration;
  final AnimationDirection direction;
  final Duration delay;
  final VoidCallback? action;

  const AnimationSequenceStep({
    required this.duration,
    required this.direction,
    this.delay = Duration.zero,
    this.action,
  });
}

/// Animation direction for sequences
enum AnimationDirection {
  forward,
  reverse,
  reset,
}

/// Spring animation implementation
class _SpringAnimation extends Animation<double> {
  final AnimationController _controller;
  final Simulation _simulation;
  late final Animation<double> _animation;

  _SpringAnimation(this._controller, this._simulation) {
    _animation = _controller.drive(
      Tween<double>(begin: _simulation.x(0), end: _simulation.x(double.infinity)),
    );
  }

  @override
  double get value {
    if (_controller.isAnimating) {
      final time = _controller.value * _controller.duration!.inMilliseconds / 1000;
      return _simulation.x(time);
    }
    return _animation.value;
  }

  @override
  AnimationStatus get status => _controller.status;

  @override
  void addListener(VoidCallback listener) => _animation.addListener(listener);

  @override
  void removeListener(VoidCallback listener) => _animation.removeListener(listener);

  @override
  void addStatusListener(AnimationStatusListener listener) =>
      _animation.addStatusListener(listener);

  @override
  void removeStatusListener(AnimationStatusListener listener) =>
      _animation.removeStatusListener(listener);
}

/// Utility extension for easier animation creation
extension AnimationControllerExtensions on TickerProvider {
  /// Create a custom animation controller with automatic service integration
  CustomAnimationController createCustomController({
    required String id,
    required Duration duration,
    Duration? reverseDuration,
    double? value,
    String? debugLabel,
    bool autoOptimize = true,
  }) {
    return CustomAnimationController(
      id: id,
      duration: duration,
      vsync: this,
      reverseDuration: reverseDuration,
      value: value,
      debugLabel: debugLabel,
      autoOptimize: autoOptimize,
    );
  }
}