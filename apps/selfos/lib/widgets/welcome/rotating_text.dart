import 'package:flutter/material.dart';
import 'dart:async';
import '../utils/animation_controller_wrapper.dart';
import '../services/animation_service.dart';
import '../services/greeting_service.dart';
import '../config/animation_config.dart';

/// Dynamic rotating text widget with typewriter effects and smooth transitions
class RotatingText extends StatefulWidget {
  final List<String> messages;
  final Duration rotationInterval;
  final Duration typewriterSpeed;
  final TextStyle? textStyle;
  final TextAlign textAlign;
  final bool enableTypewriter;
  final bool autoStart;
  final RotatingTextEffect effect;
  final bool pauseOnHover;
  final VoidCallback? onMessageChange;
  final VoidCallback? onCycleComplete;

  const RotatingText({
    super.key,
    required this.messages,
    this.rotationInterval = const Duration(seconds: 3),
    this.typewriterSpeed = const Duration(milliseconds: 50),
    this.textStyle,
    this.textAlign = TextAlign.center,
    this.enableTypewriter = true,
    this.autoStart = true,
    this.effect = RotatingTextEffect.fadeSlide,
    this.pauseOnHover = true,
    this.onMessageChange,
    this.onCycleComplete,
  });

  @override
  State<RotatingText> createState() => _RotatingTextState();
}

class _RotatingTextState extends State<RotatingText>
    with TickerProviderStateMixin {

  late CustomAnimationController _transitionController;
  late CustomAnimationController _typewriterController;
  final AnimationService _animationService = AnimationService.instance;

  int _currentIndex = 0;
  String _displayText = '';
  String _targetText = '';
  bool _isTyping = false;
  bool _isPaused = false;
  bool _shouldAnimate = true;

  Timer? _rotationTimer;
  Timer? _typewriterTimer;

  // Animations
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _scaleAnimation;
  late Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _initializeText();
    if (widget.autoStart) {
      _startRotation();
    }
  }

  @override
  void dispose() {
    _rotationTimer?.cancel();
    _typewriterTimer?.cancel();
    _transitionController.dispose();
    _typewriterController.dispose();
    super.dispose();
  }

  void _initializeAnimations() {
    _shouldAnimate = _animationService.shouldUseAdvancedAnimations;

    // Main transition controller
    _transitionController = CustomAnimationController(
      id: 'rotating_text_transition_${widget.hashCode}',
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );

    // Typewriter effect controller
    _typewriterController = CustomAnimationController(
      id: 'rotating_text_typewriter_${widget.hashCode}',
      duration: const Duration(milliseconds: 100),
      vsync: this,
    );

    if (_shouldAnimate) {
      _setupAnimations();
    } else {
      _setupStaticAnimations();
    }
  }

  void _setupAnimations() {
    // Fade animation for smooth transitions
    _fadeAnimation = _transitionController.createOptimizedAnimation(
      Tween<double>(begin: 1.0, end: 0.0),
      curve: Curves.easeInOut,
    );

    // Slide animation based on effect type
    _slideAnimation = _transitionController.createOptimizedAnimation(
      Tween<Offset>(begin: Offset.zero, end: const Offset(0, -0.5)),
      curve: Curves.easeInOut,
    );

    // Scale animation for zoom effects
    _scaleAnimation = _transitionController.createOptimizedAnimation(
      Tween<double>(begin: 1.0, end: 0.8),
      curve: Curves.easeInOut,
    );

    // Rotation animation for spin effects
    _rotationAnimation = _transitionController.createOptimizedAnimation(
      Tween<double>(begin: 0.0, end: 0.25),
      curve: Curves.easeInOut,
    );

    _transitionController.addStatusListener(_onTransitionComplete);
  }

  void _setupStaticAnimations() {
    _fadeAnimation = AlwaysStoppedAnimation(1.0);
    _slideAnimation = AlwaysStoppedAnimation(Offset.zero);
    _scaleAnimation = AlwaysStoppedAnimation(1.0);
    _rotationAnimation = AlwaysStoppedAnimation(0.0);
  }

  void _initializeText() {
    if (widget.messages.isNotEmpty) {
      _targetText = widget.messages[0];
      if (widget.enableTypewriter && _shouldAnimate) {
        _startTypewriter();
      } else {
        _displayText = _targetText;
      }
    }
  }

  void _startRotation() {
    if (widget.messages.length <= 1) return;

    _rotationTimer?.cancel();
    _rotationTimer = Timer.periodic(widget.rotationInterval, (_) {
      if (!_isPaused && mounted) {
        _rotateToNext();
      }
    });
  }

  void _stopRotation() {
    _rotationTimer?.cancel();
  }

  void _rotateToNext() {
    if (!_shouldAnimate) {
      _jumpToNext();
      return;
    }

    // Start transition out
    _transitionController.forward();
  }

  void _jumpToNext() {
    _currentIndex = (_currentIndex + 1) % widget.messages.length;
    _targetText = widget.messages[_currentIndex];

    if (widget.enableTypewriter) {
      _displayText = '';
      _startTypewriter();
    } else {
      _displayText = _targetText;
    }

    widget.onMessageChange?.call();

    if (_currentIndex == 0) {
      widget.onCycleComplete?.call();
    }
  }

  void _onTransitionComplete(AnimationStatus status) {
    if (status == AnimationStatus.completed) {
      // Update to next message
      _currentIndex = (_currentIndex + 1) % widget.messages.length;
      _targetText = widget.messages[_currentIndex];

      // Clear display text for typewriter effect
      if (widget.enableTypewriter) {
        _displayText = '';
        _startTypewriter();
      } else {
        _displayText = _targetText;
      }

      // Transition back in
      _transitionController.reverse();

      widget.onMessageChange?.call();

      if (_currentIndex == 0) {
        widget.onCycleComplete?.call();
      }
    }
  }

  void _startTypewriter() {
    if (!widget.enableTypewriter || !_shouldAnimate) {
      _displayText = _targetText;
      return;
    }

    _typewriterTimer?.cancel();
    _isTyping = true;

    int charIndex = 0;
    _typewriterTimer = Timer.periodic(widget.typewriterSpeed, (timer) {
      if (!mounted || _isPaused) return;

      if (charIndex < _targetText.length) {
        setState(() {
          _displayText = _targetText.substring(0, charIndex + 1);
        });
        charIndex++;

        // Add subtle typing haptic feedback
        if (charIndex % 3 == 0) {
          _animationService.triggerHapticFeedback();
        }
      } else {
        _isTyping = false;
        timer.cancel();
      }
    });
  }

  void _pauseRotation() {
    if (widget.pauseOnHover) {
      _isPaused = true;
    }
  }

  void _resumeRotation() {
    if (widget.pauseOnHover) {
      _isPaused = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_shouldAnimate) {
      return _buildStaticText();
    }

    Widget textWidget = _buildAnimatedText();

    if (widget.pauseOnHover) {
      textWidget = MouseRegion(
        onEnter: (_) => _pauseRotation(),
        onExit: (_) => _resumeRotation(),
        child: textWidget,
      );
    }

    return textWidget;
  }

  Widget _buildAnimatedText() {
    return AnimatedBuilder(
      animation: Listenable.merge([_fadeAnimation, _slideAnimation, _scaleAnimation, _rotationAnimation]),
      builder: (context, child) {
        Widget textWidget = Text(
          _displayText,
          style: widget.textStyle,
          textAlign: widget.textAlign,
        );

        // Apply animation effects based on selected effect
        switch (widget.effect) {
          case RotatingTextEffect.fade:
            textWidget = Opacity(
              opacity: _fadeAnimation.value,
              child: textWidget,
            );
            break;

          case RotatingTextEffect.slide:
            textWidget = SlideTransition(
              position: _slideAnimation,
              child: textWidget,
            );
            break;

          case RotatingTextEffect.fadeSlide:
            textWidget = SlideTransition(
              position: _slideAnimation,
              child: Opacity(
                opacity: _fadeAnimation.value,
                child: textWidget,
              ),
            );
            break;

          case RotatingTextEffect.scale:
            textWidget = Transform.scale(
              scale: _scaleAnimation.value,
              child: Opacity(
                opacity: _fadeAnimation.value,
                child: textWidget,
              ),
            );
            break;

          case RotatingTextEffect.rotation:
            textWidget = Transform.rotate(
              angle: _rotationAnimation.value * 2 * 3.14159,
              child: Opacity(
                opacity: _fadeAnimation.value,
                child: textWidget,
              ),
            );
            break;

          case RotatingTextEffect.typewriter:
            // Typewriter effect is handled in text content, just fade
            textWidget = Opacity(
              opacity: _fadeAnimation.value,
              child: textWidget,
            );
            break;
        }

        return textWidget;
      },
    );
  }

  Widget _buildStaticText() {
    return Text(
      _displayText,
      style: widget.textStyle,
      textAlign: widget.textAlign,
    );
  }

  /// Manually trigger next message
  void next() {
    if (_isTyping) {
      // Complete current typewriter immediately
      _typewriterTimer?.cancel();
      setState(() {
        _displayText = _targetText;
        _isTyping = false;
      });
    } else {
      _rotateToNext();
    }
  }

  /// Manually trigger previous message
  void previous() {
    _currentIndex = (_currentIndex - 1 + widget.messages.length) % widget.messages.length;
    _targetText = widget.messages[_currentIndex];

    if (widget.enableTypewriter && _shouldAnimate) {
      _displayText = '';
      _startTypewriter();
    } else {
      setState(() {
        _displayText = _targetText;
      });
    }

    widget.onMessageChange?.call();
  }

  /// Jump to specific message index
  void jumpTo(int index) {
    if (index >= 0 && index < widget.messages.length) {
      _currentIndex = index;
      _targetText = widget.messages[_currentIndex];

      if (widget.enableTypewriter && _shouldAnimate) {
        _displayText = '';
        _startTypewriter();
      } else {
        setState(() {
          _displayText = _targetText;
        });
      }

      widget.onMessageChange?.call();
    }
  }

  /// Pause/resume rotation
  void toggle() {
    _isPaused = !_isPaused;
  }

  /// Get current message index
  int get currentIndex => _currentIndex;

  /// Get current display text
  String get currentText => _displayText;

  /// Check if currently typing
  bool get isTyping => _isTyping;

  /// Check if paused
  bool get isPaused => _isPaused;
}

/// Animation effect types for rotating text
enum RotatingTextEffect {
  fade,
  slide,
  fadeSlide,
  scale,
  rotation,
  typewriter,
}

/// Preset rotating text widgets
class RotatingTextWidgets {
  /// Welcome screen rotating messages
  static RotatingText welcomeMessages({
    TextStyle? style,
    List<String>? customMessages,
  }) {
    final messages = customMessages ?? GreetingService.instance.generateRotatingMessages();

    return RotatingText(
      messages: messages,
      rotationInterval: const Duration(seconds: 4),
      typewriterSpeed: const Duration(milliseconds: 80),
      effect: RotatingTextEffect.fadeSlide,
      textStyle: style,
      enableTypewriter: true,
      pauseOnHover: true,
    );
  }

  /// Feature highlight rotating text
  static RotatingText featureHighlights({
    TextStyle? style,
  }) {
    const features = [
      'AI-powered goal planning',
      'Smart task generation',
      'Progress tracking & insights',
      'Personalized motivation',
      'Achievement celebrations',
    ];

    return RotatingText(
      messages: features,
      rotationInterval: const Duration(seconds: 2, milliseconds: 500),
      typewriterSpeed: const Duration(milliseconds: 60),
      effect: RotatingTextEffect.scale,
      textStyle: style,
      enableTypewriter: false,
      pauseOnHover: false,
    );
  }

  /// Motivational quotes rotating text
  static RotatingText motivationalQuotes({
    TextStyle? style,
  }) {
    const quotes = [
      '"The best time to plant a tree was 20 years ago. The second best time is now."',
      '"Your future self will thank you for starting today."',
      '"Progress, not perfection, is the goal."',
      '"Every expert was once a beginner."',
      '"What you focus on grows."',
    ];

    return RotatingText(
      messages: quotes,
      rotationInterval: const Duration(seconds: 5),
      typewriterSpeed: const Duration(milliseconds: 40),
      effect: RotatingTextEffect.typewriter,
      textStyle: style,
      enableTypewriter: true,
      pauseOnHover: true,
    );
  }

  /// Quick status updates
  static RotatingText statusUpdates({
    required List<String> statuses,
    TextStyle? style,
  }) {
    return RotatingText(
      messages: statuses,
      rotationInterval: const Duration(seconds: 2),
      typewriterSpeed: const Duration(milliseconds: 30),
      effect: RotatingTextEffect.fade,
      textStyle: style,
      enableTypewriter: false,
      pauseOnHover: false,
    );
  }
}

/// Controller for managing multiple rotating text widgets
class RotatingTextController {
  final List<_RotatingTextState> _widgets = [];

  /// Register a rotating text widget
  void register(_RotatingTextState widget) {
    _widgets.add(widget);
  }

  /// Unregister a rotating text widget
  void unregister(_RotatingTextState widget) {
    _widgets.remove(widget);
  }

  /// Pause all rotating text widgets
  void pauseAll() {
    for (final widget in _widgets) {
      widget._isPaused = true;
    }
  }

  /// Resume all rotating text widgets
  void resumeAll() {
    for (final widget in _widgets) {
      widget._isPaused = false;
    }
  }

  /// Trigger next message on all widgets
  void nextAll() {
    for (final widget in _widgets) {
      widget.next();
    }
  }

  /// Get performance metrics
  Map<String, dynamic> getMetrics() {
    return {
      'widgetCount': _widgets.length,
      'activeAnimations': _widgets.where((w) => w._isTyping).length,
      'pausedWidgets': _widgets.where((w) => w._isPaused).length,
    };
  }

  /// Dispose all widgets
  void dispose() {
    _widgets.clear();
  }
}

/// Utility for creating synchronized rotating text groups
class RotatingTextGroup {
  final List<_RotatingTextState> _group = [];
  Timer? _syncTimer;

  /// Add widget to synchronized group
  void add(_RotatingTextState widget) {
    _group.add(widget);
  }

  /// Remove widget from group
  void remove(_RotatingTextState widget) {
    _group.remove(widget);
  }

  /// Start synchronized rotation
  void startSync(Duration interval) {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(interval, (_) {
      for (final widget in _group) {
        widget.next();
      }
    });
  }

  /// Stop synchronized rotation
  void stopSync() {
    _syncTimer?.cancel();
  }

  /// Dispose group
  void dispose() {
    _syncTimer?.cancel();
    _group.clear();
  }
}