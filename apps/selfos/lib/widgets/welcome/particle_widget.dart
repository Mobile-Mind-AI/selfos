import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../utils/animation_controller_wrapper.dart';
import '../services/animation_service.dart';
import '../config/animation_config.dart';

/// Floating particle animation widget with physics-based movement
class ParticleWidget extends StatefulWidget {
  final ParticlePreset preset;
  final bool isEnabled;
  final double containerWidth;
  final double containerHeight;
  final Widget? child;

  const ParticleWidget({
    super.key,
    required this.preset,
    this.isEnabled = true,
    this.containerWidth = 200,
    this.containerHeight = 200,
    this.child,
  });

  @override
  State<ParticleWidget> createState() => _ParticleWidgetState();
}

class _ParticleWidgetState extends State<ParticleWidget>
    with TickerProviderStateMixin {

  late CustomAnimationController _masterController;
  final List<Particle> _particles = [];
  final AnimationService _animationService = AnimationService.instance;

  bool _shouldAnimate = true;

  @override
  void initState() {
    super.initState();
    _initializeAnimation();
    _createParticles();
  }

  @override
  void dispose() {
    _masterController.dispose();
    super.dispose();
  }

  void _initializeAnimation() {
    _shouldAnimate = widget.isEnabled && _animationService.shouldUseParticleAnimations;

    if (_shouldAnimate) {
      _masterController = CustomAnimationController(
        id: 'particle_master_${widget.hashCode}',
        duration: widget.preset.duration,
        vsync: this,
      );

      _masterController.repeat();
    } else {
      // Create a dummy controller for performance mode
      _masterController = CustomAnimationController(
        id: 'particle_dummy_${widget.hashCode}',
        duration: Duration(milliseconds: 1),
        vsync: this,
      );
    }
  }

  void _createParticles() {
    if (!_shouldAnimate) return;

    final random = math.Random();
    final centerX = widget.containerWidth / 2;
    final centerY = widget.containerHeight / 2;

    for (int i = 0; i < widget.preset.count; i++) {
      final angle = (i * 2 * math.pi) / widget.preset.count;
      final radius = widget.preset.radius + (random.nextDouble() - 0.5) * 20;

      final particle = Particle(
        id: 'particle_$i',
        initialAngle: angle,
        radius: radius,
        centerX: centerX,
        centerY: centerY,
        size: widget.preset.size + (random.nextDouble() - 0.5) * 4,
        color: widget.preset.colors[i % widget.preset.colors.length],
        animationType: widget.preset.animationType,
        controller: _masterController,
        phaseOffset: random.nextDouble(),
        speed: 0.5 + random.nextDouble() * 0.5,
      );

      _particles.add(particle);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_shouldAnimate) {
      // Return simplified version for performance mode
      return _buildSimplifiedVersion();
    }

    return SizedBox(
      width: widget.containerWidth,
      height: widget.containerHeight,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // Child content (if any)
          if (widget.child != null)
            Center(child: widget.child!),

          // Animated particles
          ..._particles.map((particle) => _buildParticle(particle)),
        ],
      ),
    );
  }

  Widget _buildParticle(Particle particle) {
    return AnimatedBuilder(
      animation: _masterController,
      builder: (context, child) {
        final position = particle.getPosition(_masterController.value);
        final opacity = particle.getOpacity(_masterController.value);
        final scale = particle.getScale(_masterController.value);

        return Positioned(
          left: position.dx - particle.size / 2,
          top: position.dy - particle.size / 2,
          child: Transform.scale(
            scale: scale,
            child: Opacity(
              opacity: opacity,
              child: Container(
                width: particle.size,
                height: particle.size,
                decoration: BoxDecoration(
                  color: particle.color,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: particle.color.withOpacity(0.3),
                      blurRadius: 4,
                      spreadRadius: 1,
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildSimplifiedVersion() {
    // Static particles for reduced motion/performance mode
    return SizedBox(
      width: widget.containerWidth,
      height: widget.containerHeight,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          if (widget.child != null)
            Center(child: widget.child!),

          // Static decorative elements
          ...List.generate(3, (index) {
            final angle = (index * 2 * math.pi) / 3;
            final x = widget.containerWidth / 2 +
                     math.cos(angle) * (widget.preset.radius * 0.6);
            final y = widget.containerHeight / 2 +
                     math.sin(angle) * (widget.preset.radius * 0.6);

            return Positioned(
              left: x - 4,
              top: y - 4,
              child: Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: widget.preset.colors[index % widget.preset.colors.length]
                      .withOpacity(0.6),
                  shape: BoxShape.circle,
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}

/// Individual particle with physics-based animation
class Particle {
  final String id;
  final double initialAngle;
  final double radius;
  final double centerX;
  final double centerY;
  final double size;
  final Color color;
  final ParticleAnimationType animationType;
  final CustomAnimationController controller;
  final double phaseOffset;
  final double speed;

  // Animation parameters
  late final double _floatAmplitude;
  late final double _pulseAmplitude;
  late final double _orbitSpeed;

  Particle({
    required this.id,
    required this.initialAngle,
    required this.radius,
    required this.centerX,
    required this.centerY,
    required this.size,
    required this.color,
    required this.animationType,
    required this.controller,
    required this.phaseOffset,
    required this.speed,
  }) {
    _floatAmplitude = 10 + (size - 8) * 2; // Larger particles float more
    _pulseAmplitude = 0.3;
    _orbitSpeed = speed;
  }

  /// Get current particle position based on animation progress
  Offset getPosition(double animationValue) {
    final time = animationValue + phaseOffset;

    switch (animationType) {
      case ParticleAnimationType.floating:
        return _getFloatingPosition(time);
      case ParticleAnimationType.orbiting:
        return _getOrbitingPosition(time);
      case ParticleAnimationType.pulsing:
        return _getPulsingPosition(time);
      case ParticleAnimationType.shooting:
        return _getShootingPosition(time);
      case ParticleAnimationType.swirling:
        return _getSwirlingPosition(time);
    }
  }

  /// Get current particle opacity
  double getOpacity(double animationValue) {
    final time = animationValue + phaseOffset;

    switch (animationType) {
      case ParticleAnimationType.floating:
        return 0.6 + 0.4 * math.sin(time * 2 * math.pi * 0.7);
      case ParticleAnimationType.orbiting:
        return 0.8;
      case ParticleAnimationType.pulsing:
        return 0.3 + 0.7 * (math.sin(time * 2 * math.pi * 1.5) * 0.5 + 0.5);
      case ParticleAnimationType.shooting:
        final progress = (time * speed) % 1.0;
        return progress < 0.7 ? 0.9 : 0.9 * (1.0 - (progress - 0.7) / 0.3);
      case ParticleAnimationType.swirling:
        return 0.7 + 0.3 * math.sin(time * 2 * math.pi);
    }
  }

  /// Get current particle scale
  double getScale(double animationValue) {
    final time = animationValue + phaseOffset;

    switch (animationType) {
      case ParticleAnimationType.floating:
        return 1.0 + _pulseAmplitude * 0.3 * math.sin(time * 2 * math.pi * 0.8);
      case ParticleAnimationType.orbiting:
        return 1.0;
      case ParticleAnimationType.pulsing:
        return 0.7 + 0.6 * (math.sin(time * 2 * math.pi * 1.5) * 0.5 + 0.5);
      case ParticleAnimationType.shooting:
        final progress = (time * speed) % 1.0;
        return progress < 0.1 ? progress * 10 : 1.0;
      case ParticleAnimationType.swirling:
        return 1.0 + 0.2 * math.sin(time * 2 * math.pi * 2);
    }
  }

  Offset _getFloatingPosition(double time) {
    // Gentle floating motion with figure-8 pattern
    final baseX = centerX + math.cos(initialAngle) * radius;
    final baseY = centerY + math.sin(initialAngle) * radius;

    final floatX = _floatAmplitude * math.sin(time * 2 * math.pi * 0.3) * 0.7;
    final floatY = _floatAmplitude * math.sin(time * 2 * math.pi * 0.5) * 0.5;

    return Offset(baseX + floatX, baseY + floatY);
  }

  Offset _getOrbitingPosition(double time) {
    // Circular orbit around center
    final angle = initialAngle + time * 2 * math.pi * _orbitSpeed * 0.2;
    final x = centerX + math.cos(angle) * radius;
    final y = centerY + math.sin(angle) * radius;

    return Offset(x, y);
  }

  Offset _getPulsingPosition(double time) {
    // Static position with pulsing effect
    final x = centerX + math.cos(initialAngle) * radius;
    final y = centerY + math.sin(initialAngle) * radius;

    return Offset(x, y);
  }

  Offset _getShootingPosition(double time) {
    // Shooting star effect
    final progress = (time * speed) % 1.0;
    final startAngle = initialAngle;
    final endAngle = initialAngle + math.pi * 0.3;

    final currentAngle = startAngle + (endAngle - startAngle) * progress;
    final currentRadius = radius * (0.5 + progress * 1.5);

    final x = centerX + math.cos(currentAngle) * currentRadius;
    final y = centerY + math.sin(currentAngle) * currentRadius;

    return Offset(x, y);
  }

  Offset _getSwirlingPosition(double time) {
    // Spiral motion
    final spiralRadius = radius * (1.0 + 0.3 * math.sin(time * 2 * math.pi * 0.4));
    final angle = initialAngle + time * 2 * math.pi * _orbitSpeed * 0.7;

    final x = centerX + math.cos(angle) * spiralRadius;
    final y = centerY + math.sin(angle) * spiralRadius;

    return Offset(x, y);
  }
}

/// Particle controller for managing multiple particle systems
class ParticleController {
  final List<ParticleWidget> _systems = [];
  bool _isGloballyEnabled = true;

  /// Add a particle system to be managed
  void addSystem(ParticleWidget system) {
    _systems.add(system);
  }

  /// Remove a particle system
  void removeSystem(ParticleWidget system) {
    _systems.remove(system);
  }

  /// Enable/disable all particle systems
  void setGlobalEnabled(bool enabled) {
    _isGloballyEnabled = enabled;
    // Note: Individual systems will check this via AnimationService
  }

  /// Get performance metrics for all systems
  Map<String, dynamic> getMetrics() {
    return {
      'systemCount': _systems.length,
      'globallyEnabled': _isGloballyEnabled,
      'totalParticles': _systems.fold(0, (sum, system) => sum + system.preset.count),
    };
  }

  /// Dispose all systems
  void dispose() {
    _systems.clear();
  }
}

/// Utility for creating preset particle widgets
class ParticleWidgets {
  /// Create welcome screen hero particles
  static ParticleWidget welcomeHero({
    required double width,
    required double height,
    Widget? child,
  }) {
    return ParticleWidget(
      preset: WelcomeAnimationPresets.particleSystem,
      containerWidth: width,
      containerHeight: height,
      child: child,
    );
  }

  /// Create subtle background particles
  static ParticleWidget backgroundParticles({
    required double width,
    required double height,
    int count = 8,
    List<Color>? colors,
  }) {
    final preset = ParticlePreset(
      count: count,
      duration: Duration(seconds: 5),
      radius: math.min(width, height) * 0.4,
      size: 4.0,
      colors: colors ?? [
        Colors.white.withOpacity(0.1),
        Colors.white.withOpacity(0.05),
        Colors.white.withOpacity(0.15),
      ],
      animationType: ParticleAnimationType.floating,
    );

    return ParticleWidget(
      preset: preset,
      containerWidth: width,
      containerHeight: height,
    );
  }

  /// Create energetic particles for active states
  static ParticleWidget energeticParticles({
    required double width,
    required double height,
    required Color primaryColor,
  }) {
    final preset = ParticlePreset(
      count: 12,
      duration: Duration(seconds: 2),
      radius: math.min(width, height) * 0.3,
      size: 6.0,
      colors: [
        primaryColor,
        primaryColor.withOpacity(0.7),
        primaryColor.withOpacity(0.5),
        Colors.white.withOpacity(0.8),
      ],
      animationType: ParticleAnimationType.swirling,
    );

    return ParticleWidget(
      preset: preset,
      containerWidth: width,
      containerHeight: height,
    );
  }
}