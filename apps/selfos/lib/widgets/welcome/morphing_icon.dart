import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../utils/animation_controller_wrapper.dart';
import '../services/animation_service.dart';
import '../config/animation_config.dart';

/// Morphing icon widget that transitions between different shapes and colors
class MorphingIcon extends StatefulWidget {
  final MorphingPreset preset;
  final double size;
  final bool isEnabled;
  final bool autoPlay;
  final Duration pauseBetweenMorphs;
  final VoidCallback? onMorphComplete;

  const MorphingIcon({
    super.key,
    required this.preset,
    this.size = 80.0,
    this.isEnabled = true,
    this.autoPlay = true,
    this.pauseBetweenMorphs = const Duration(milliseconds: 500),
    this.onMorphComplete,
  });

  @override
  State<MorphingIcon> createState() => _MorphingIconState();
}

class _MorphingIconState extends State<MorphingIcon>
    with TickerProviderStateMixin {

  late CustomAnimationController _morphController;
  late CustomAnimationController _pulseController;
  late CustomAnimationController _rotationController;

  final AnimationService _animationService = AnimationService.instance;

  int _currentShapeIndex = 0;
  bool _shouldAnimate = true;

  // Animations
  late Animation<double> _morphProgress;
  late Animation<double> _pulseScale;
  late Animation<double> _rotation;
  late Animation<Color?> _colorTransition;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    if (widget.autoPlay) {
      _startMorphing();
    }
  }

  @override
  void dispose() {
    _morphController.dispose();
    _pulseController.dispose();
    _rotationController.dispose();
    super.dispose();
  }

  void _initializeAnimations() {
    _shouldAnimate = widget.isEnabled && _animationService.shouldUseMorphingAnimations;

    // Main morphing animation
    _morphController = CustomAnimationController(
      id: 'morph_main_${widget.hashCode}',
      duration: widget.preset.duration,
      vsync: this,
    );

    // Pulse animation for breathing effect
    _pulseController = CustomAnimationController(
      id: 'morph_pulse_${widget.hashCode}',
      duration: Duration(seconds: 2),
      vsync: this,
    );

    // Rotation animation for dynamic effect
    _rotationController = CustomAnimationController(
      id: 'morph_rotation_${widget.hashCode}',
      duration: Duration(seconds: 8),
      vsync: this,
    );

    if (_shouldAnimate) {
      _setupAnimations();
      _setupListeners();
    } else {
      _setupStaticAnimations();
    }
  }

  void _setupAnimations() {
    // Morphing progress (0 to 1 for each shape transition)
    _morphProgress = _morphController.createOptimizedAnimation(
      Tween<double>(begin: 0.0, end: 1.0),
      curve: widget.preset.curve,
    );

    // Pulse scale for breathing effect
    _pulseScale = _pulseController.createOptimizedAnimation(
      Tween<double>(begin: 0.95, end: 1.05),
      curve: Curves.easeInOut,
    );

    // Rotation for dynamic movement
    _rotation = _rotationController.createOptimizedAnimation(
      Tween<double>(begin: 0.0, end: 2 * math.pi),
      curve: Curves.linear,
    );

    // Color transition between current and next shape
    _colorTransition = ColorTween(
      begin: widget.preset.colors[_currentShapeIndex],
      end: widget.preset.colors[(_currentShapeIndex + 1) % widget.preset.colors.length],
    ).animate(_morphProgress);

    // Start continuous animations
    _pulseController.repeat(reverse: true);
    _rotationController.repeat();
  }

  void _setupStaticAnimations() {
    // Static versions for performance mode
    _morphProgress = AlwaysStoppedAnimation(0.0);
    _pulseScale = AlwaysStoppedAnimation(1.0);
    _rotation = AlwaysStoppedAnimation(0.0);
    _colorTransition = AlwaysStoppedAnimation(widget.preset.colors[0]);
  }

  void _setupListeners() {
    _morphController.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _onMorphComplete();
      }
    });
  }

  void _startMorphing() {
    if (!_shouldAnimate) return;

    _morphToNextShape();
  }

  void _morphToNextShape() async {
    if (!mounted || !_shouldAnimate) return;

    // Update color transition for next morph
    final nextIndex = (_currentShapeIndex + 1) % widget.preset.shapes.length;
    _colorTransition = ColorTween(
      begin: widget.preset.colors[_currentShapeIndex],
      end: widget.preset.colors[nextIndex],
    ).animate(_morphProgress);

    // Trigger haptic feedback
    _animationService.triggerHapticFeedback();

    // Start morph animation
    await _morphController.forward();
  }

  void _onMorphComplete() async {
    // Update to next shape
    setState(() {
      _currentShapeIndex = (_currentShapeIndex + 1) % widget.preset.shapes.length;
    });

    // Reset morph controller
    _morphController.reset();

    // Callback
    widget.onMorphComplete?.call();

    // Continue morphing if auto-play is enabled
    if (widget.autoPlay && _shouldAnimate) {
      await Future.delayed(widget.pauseBetweenMorphs);
      if (mounted) {
        _morphToNextShape();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_shouldAnimate) {
      return _buildStaticIcon();
    }

    return AnimatedBuilder(
      animation: Listenable.merge([_morphProgress, _pulseScale, _rotation]),
      builder: (context, child) {
        return Transform.scale(
          scale: _pulseScale.value,
          child: Transform.rotate(
            angle: _rotation.value * 0.1, // Subtle rotation
            child: SizedBox(
              width: widget.size,
              height: widget.size,
              child: CustomPaint(
                painter: MorphingIconPainter(
                  currentShape: widget.preset.shapes[_currentShapeIndex],
                  nextShape: widget.preset.shapes[
                    (_currentShapeIndex + 1) % widget.preset.shapes.length
                  ],
                  morphProgress: _morphProgress.value,
                  color: _colorTransition.value ?? widget.preset.colors[_currentShapeIndex],
                  size: widget.size,
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildStaticIcon() {
    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: Icon(
        widget.preset.shapes[0],
        size: widget.size * 0.8,
        color: widget.preset.colors[0],
      ),
    );
  }

  /// Manually trigger morph to next shape
  void morphToNext() {
    if (_shouldAnimate && !_morphController.isAnimating) {
      _morphToNextShape();
    }
  }

  /// Morph to specific shape index
  void morphToShape(int index) {
    if (!_shouldAnimate || index < 0 || index >= widget.preset.shapes.length) {
      return;
    }

    setState(() {
      _currentShapeIndex = index;
    });

    _morphController.reset();
  }

  /// Pause morphing animations
  void pause() {
    _morphController.stop();
    _pulseController.stop();
    _rotationController.stop();
  }

  /// Resume morphing animations
  void resume() {
    if (_shouldAnimate) {
      if (widget.autoPlay && !_morphController.isAnimating) {
        _morphToNextShape();
      }
      _pulseController.repeat(reverse: true);
      _rotationController.repeat();
    }
  }
}

/// Custom painter for morphing between icon shapes
class MorphingIconPainter extends CustomPainter {
  final IconData currentShape;
  final IconData nextShape;
  final double morphProgress;
  final Color color;
  final double size;

  const MorphingIconPainter({
    required this.currentShape,
    required this.nextShape,
    required this.morphProgress,
    required this.color,
    required this.size,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final center = Offset(size.width / 2, size.height / 2);
    final iconSize = this.size * 0.8;

    // Create morphing effect by blending opacity and scale
    if (morphProgress < 0.5) {
      // First half: fade out current shape while scaling down
      final progress = morphProgress * 2; // 0 to 1
      final opacity = (1.0 - progress).clamp(0.0, 1.0);
      final scale = (1.0 - progress * 0.3).clamp(0.7, 1.0);

      _drawIcon(canvas, center, currentShape, iconSize * scale, color.withOpacity(opacity));
    } else {
      // Second half: fade in next shape while scaling up
      final progress = (morphProgress - 0.5) * 2; // 0 to 1
      final opacity = progress.clamp(0.0, 1.0);
      final scale = (0.7 + progress * 0.3).clamp(0.7, 1.0);

      _drawIcon(canvas, center, nextShape, iconSize * scale, color.withOpacity(opacity));
    }

    // Add morphing particle effect
    if (morphProgress > 0.3 && morphProgress < 0.7) {
      _drawMorphingParticles(canvas, center, iconSize);
    }
  }

  void _drawIcon(Canvas canvas, Offset center, IconData iconData, double size, Color color) {
    final textPainter = TextPainter(
      text: TextSpan(
        text: String.fromCharCode(iconData.codePoint),
        style: TextStyle(
          fontSize: size,
          fontFamily: iconData.fontFamily,
          color: color,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();

    final offset = Offset(
      center.dx - textPainter.width / 2,
      center.dy - textPainter.height / 2,
    );

    textPainter.paint(canvas, offset);
  }

  void _drawMorphingParticles(Canvas canvas, Offset center, double iconSize) {
    final particlePaint = Paint()
      ..color = color.withOpacity(0.6)
      ..style = PaintingStyle.fill;

    final particleCount = 8;
    final radius = iconSize * 0.6;

    for (int i = 0; i < particleCount; i++) {
      final angle = (i / particleCount) * 2 * math.pi;
      final distance = radius * (0.5 + 0.5 * math.sin(morphProgress * math.pi * 4));

      final particleX = center.dx + math.cos(angle) * distance;
      final particleY = center.dy + math.sin(angle) * distance;

      final particleSize = 3.0 * (1.0 - (morphProgress - 0.3) / 0.4);

      canvas.drawCircle(
        Offset(particleX, particleY),
        particleSize,
        particlePaint,
      );
    }
  }

  @override
  bool shouldRepaint(MorphingIconPainter oldDelegate) {
    return oldDelegate.morphProgress != morphProgress ||
           oldDelegate.color != color ||
           oldDelegate.currentShape != currentShape ||
           oldDelegate.nextShape != nextShape;
  }
}

/// Preset morphing icon widgets
class MorphingIcons {
  /// Welcome screen hero morphing icon
  static MorphingIcon welcomeHero({
    double size = 80.0,
    bool autoPlay = true,
    VoidCallback? onMorphComplete,
  }) {
    return MorphingIcon(
      preset: WelcomeAnimationPresets.morphingIcon,
      size: size,
      autoPlay: autoPlay,
      onMorphComplete: onMorphComplete,
    );
  }

  /// Create AI-themed morphing icon
  static MorphingIcon aiThemed({
    double size = 60.0,
    bool autoPlay = true,
    Color? primaryColor,
  }) {
    final colors = primaryColor != null
        ? [
            primaryColor,
            primaryColor.withOpacity(0.8),
            primaryColor.withOpacity(0.6),
            primaryColor.withOpacity(0.9),
          ]
        : [
            const Color(0xFF6366F1),
            const Color(0xFF8B5CF6),
            const Color(0xFF06B6D4),
            const Color(0xFF10B981),
          ];

    final preset = MorphingPreset(
      duration: const Duration(seconds: 2),
      curve: Curves.easeInOut,
      shapes: const [
        Icons.psychology,
        Icons.auto_awesome,
        Icons.lightbulb_outline,
        Icons.memory,
      ],
      colors: colors,
    );

    return MorphingIcon(
      preset: preset,
      size: size,
      autoPlay: autoPlay,
    );
  }

  /// Create goal-themed morphing icon
  static MorphingIcon goalThemed({
    double size = 50.0,
    bool autoPlay = true,
  }) {
    const preset = MorphingPreset(
      duration: Duration(milliseconds: 1500),
      curve: Curves.easeInOut,
      shapes: [
        Icons.flag_outlined,
        Icons.trending_up,
        Icons.emoji_events,
        Icons.star_outline,
      ],
      colors: [
        Color(0xFFFF6B35),
        Color(0xFF4ECDC4),
        Color(0xFFFEEAE6),
        Color(0xFF96CEB4),
      ],
    );

    return MorphingIcon(
      preset: preset,
      size: size,
      autoPlay: autoPlay,
    );
  }

  /// Create progress-themed morphing icon
  static MorphingIcon progressThemed({
    double size = 40.0,
    bool autoPlay = true,
  }) {
    const preset = MorphingPreset(
      duration: Duration(milliseconds: 2500),
      curve: Curves.easeInOut,
      shapes: [
        Icons.radio_button_unchecked,
        Icons.more_horiz,
        Icons.check_circle_outline,
        Icons.celebration,
      ],
      colors: [
        Color(0xFF9CA3AF),
        Color(0xFF6366F1),
        Color(0xFF10B981),
        Color(0xFFF59E0B),
      ],
    );

    return MorphingIcon(
      preset: preset,
      size: size,
      autoPlay: autoPlay,
      pauseBetweenMorphs: const Duration(milliseconds: 800),
    );
  }
}

/// Controller for managing multiple morphing icons
class MorphingIconController {
  final List<_MorphingIconState> _icons = [];

  /// Register a morphing icon for management
  void register(_MorphingIconState icon) {
    _icons.add(icon);
  }

  /// Unregister a morphing icon
  void unregister(_MorphingIconState icon) {
    _icons.remove(icon);
  }

  /// Pause all morphing icons
  void pauseAll() {
    for (final icon in _icons) {
      icon.pause();
    }
  }

  /// Resume all morphing icons
  void resumeAll() {
    for (final icon in _icons) {
      icon.resume();
    }
  }

  /// Trigger manual morph on all icons
  void morphAll() {
    for (final icon in _icons) {
      icon.morphToNext();
    }
  }

  /// Dispose all icons
  void dispose() {
    _icons.clear();
  }
}