import 'package:flutter/material.dart';
import 'dart:math' as math;

/// Hero section widget with animated brain icon and orbiting colored dots
class HeroSection extends StatefulWidget {
  final double size;
  final Duration orbitDuration;
  final Duration pulseDuration;
  final bool enableHoverEffect;
  final VoidCallback? onHover;
  final VoidCallback? onHoverExit;

  const HeroSection({
    super.key,
    this.size = 280.0,
    this.orbitDuration = const Duration(seconds: 8),
    this.pulseDuration = const Duration(seconds: 2),
    this.enableHoverEffect = true,
    this.onHover,
    this.onHoverExit,
  });

  @override
  State<HeroSection> createState() => _HeroSectionState();
}

class _HeroSectionState extends State<HeroSection>
    with TickerProviderStateMixin {

  late AnimationController _entranceController;
  late AnimationController _pulseController;
  late AnimationController _orbitController;

  late Animation<double> _entranceAnimation;
  late Animation<double> _pulseAnimation;
  late Animation<double> _orbitAnimation;

  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _startAnimations();
  }

  @override
  void dispose() {
    _entranceController.dispose();
    _pulseController.dispose();
    _orbitController.dispose();
    super.dispose();
  }

  void _setupAnimations() {
    // Entrance animation
    _entranceController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    // Pulse animation for breathing effect
    _pulseController = AnimationController(
      duration: widget.pulseDuration,
      vsync: this,
    );

    // Orbit animation for dots
    _orbitController = AnimationController(
      duration: widget.orbitDuration,
      vsync: this,
    );

    _entranceAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _entranceController,
      curve: Curves.easeOut,
    ));

    _pulseAnimation = Tween<double>(
      begin: 0.95,
      end: 1.05,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));

    _orbitAnimation = Tween<double>(
      begin: 0.0,
      end: 2 * math.pi,
    ).animate(CurvedAnimation(
      parent: _orbitController,
      curve: Curves.linear,
    ));
  }

  void _startAnimations() {
    _entranceController.forward();
    _pulseController.repeat(reverse: true);
    _orbitController.repeat();
  }

  void _handleHover(bool isHovered) {
    setState(() {
      _isHovered = isHovered;
    });

    if (isHovered) {
      widget.onHover?.call();
    } else {
      widget.onHoverExit?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AnimatedBuilder(
      animation: Listenable.merge([_entranceAnimation, _pulseAnimation, _orbitAnimation]),
      builder: (context, child) {
        return Transform.scale(
          scale: 0.5 + 0.5 * _entranceAnimation.value,
          child: Opacity(
            opacity: _entranceAnimation.value,
            child: widget.enableHoverEffect
                ? MouseRegion(
                    onEnter: (_) => _handleHover(true),
                    onExit: (_) => _handleHover(false),
                    child: _buildHeroContent(theme),
                  )
                : _buildHeroContent(theme),
          ),
        );
      },
    );
  }

  Widget _buildHeroContent(ThemeData theme) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      transform: Matrix4.identity()
        ..scale(_isHovered ? 1.05 : 1.0),
      child: Container(
        width: widget.size,
        height: widget.size,
        decoration: BoxDecoration(
          gradient: RadialGradient(
            colors: [
              theme.colorScheme.primary.withOpacity(0.2),
              theme.colorScheme.secondary.withOpacity(0.1),
              Colors.transparent,
            ],
          ),
          borderRadius: BorderRadius.circular(widget.size / 2),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            // Main brain icon
            _buildMainIcon(theme),

            // Orbiting colored dots
            ..._buildOrbitingDots(theme),
          ],
        ),
      ),
    );
  }

  Widget _buildMainIcon(ThemeData theme) {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _pulseAnimation.value,
          child: Container(
            width: widget.size * 0.5, // 50% of hero size
            height: widget.size * 0.5,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  theme.colorScheme.primary.withOpacity(0.15),
                  theme.colorScheme.secondary.withOpacity(0.15),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(widget.size * 0.25),
            ),
            child: Icon(
              Icons.psychology,
              size: widget.size * 0.285, // Proportional to hero size
              color: theme.colorScheme.primary,
            ),
          ),
        );
      },
    );
  }

  List<Widget> _buildOrbitingDots(ThemeData theme) {
    const dotColors = [
      Colors.orange,
      Colors.blue,
      Colors.green,
      Colors.purple,
      Colors.red,
      Colors.teal,
    ];

    return List.generate(6, (index) {
      final baseAngle = (index * 60) * (math.pi / 180);
      final currentAngle = baseAngle + _orbitAnimation.value;
      final orbitRadius = widget.size * 0.357; // Proportional orbit radius

      return Transform.translate(
        offset: Offset(
          orbitRadius * math.cos(currentAngle),
          orbitRadius * math.sin(currentAngle),
        ),
        child: _buildOrbitingDot(
          dotColors[index],
          widget.size * 0.043, // Proportional dot size
        ),
      );
    });
  }

  Widget _buildOrbitingDot(Color color, double size) {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: 0.8 + 0.2 * _pulseAnimation.value,
          child: Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              color: color.withOpacity(0.8),
              borderRadius: BorderRadius.circular(size / 2),
              boxShadow: [
                BoxShadow(
                  color: color.withOpacity(0.3),
                  blurRadius: 4,
                  spreadRadius: 1,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  /// Manually trigger entrance animation
  void playEntrance() {
    _entranceController.forward(from: 0);
  }

  /// Pause all animations
  void pauseAnimations() {
    _pulseController.stop();
    _orbitController.stop();
  }

  /// Resume all animations
  void resumeAnimations() {
    if (!_pulseController.isAnimating) {
      _pulseController.repeat(reverse: true);
    }
    if (!_orbitController.isAnimating) {
      _orbitController.repeat();
    }
  }

  /// Get current hover state
  bool get isHovered => _isHovered;

  /// Get animation progress values
  Map<String, double> get animationProgress => {
    'entrance': _entranceAnimation.value,
    'pulse': _pulseAnimation.value,
    'orbit': _orbitAnimation.value,
  };
}