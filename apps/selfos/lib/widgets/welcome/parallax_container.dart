import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../utils/animation_controller_wrapper.dart';
import '../services/animation_service.dart';
import '../config/animation_config.dart';
import 'particle_widget.dart';

/// Multi-layer parallax container with depth-based movement
class ParallaxContainer extends StatefulWidget {
  final ParallaxPreset preset;
  final Widget child;
  final double width;
  final double height;
  final bool isEnabled;
  final bool followCursor;
  final bool followScroll;
  final ParallaxTrigger trigger;

  const ParallaxContainer({
    super.key,
    required this.preset,
    required this.child,
    required this.width,
    required this.height,
    this.isEnabled = true,
    this.followCursor = true,
    this.followScroll = false,
    this.trigger = ParallaxTrigger.hover,
  });

  @override
  State<ParallaxContainer> createState() => _ParallaxContainerState();
}

class _ParallaxContainerState extends State<ParallaxContainer>
    with TickerProviderStateMixin {

  late CustomAnimationController _parallaxController;
  final AnimationService _animationService = AnimationService.instance;

  // Mouse/touch tracking
  Offset _currentOffset = Offset.zero;
  Offset _targetOffset = Offset.zero;

  // Scroll tracking
  double _scrollOffset = 0.0;

  // Animation state
  bool _shouldAnimate = true;
  bool _isHovered = false;

  // Animations for each layer
  late List<Animation<Offset>> _layerAnimations;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
  }

  @override
  void dispose() {
    _parallaxController.dispose();
    super.dispose();
  }

  void _initializeAnimations() {
    _shouldAnimate = widget.isEnabled && _animationService.shouldUseParallaxEffects;

    _parallaxController = CustomAnimationController(
      id: 'parallax_${widget.hashCode}',
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    if (_shouldAnimate) {
      _setupLayerAnimations();
    } else {
      _setupStaticAnimations();
    }
  }

  void _setupLayerAnimations() {
    _layerAnimations = widget.preset.layers.map((layer) {
      return _parallaxController.createOptimizedAnimation(
        Tween<Offset>(begin: Offset.zero, end: Offset.zero),
        curve: Curves.easeOut,
      );
    }).toList();
  }

  void _setupStaticAnimations() {
    _layerAnimations = widget.preset.layers.map((layer) {
      return AlwaysStoppedAnimation<Offset>(Offset.zero);
    }).toList();
  }

  void _updateParallax(Offset localPosition) {
    if (!_shouldAnimate) return;

    final center = Offset(widget.width / 2, widget.height / 2);
    final deltaX = (localPosition.dx - center.dx) / center.dx;
    final deltaY = (localPosition.dy - center.dy) / center.dy;

    _targetOffset = Offset(
      deltaX * widget.preset.maxOffset * widget.preset.sensitivity,
      deltaY * widget.preset.maxOffset * widget.preset.sensitivity,
    );

    _animateToTarget();
  }

  void _animateToTarget() {
    // Update tween targets for each layer
    for (int i = 0; i < widget.preset.layers.length && i < _layerAnimations.length; i++) {
      final layer = widget.preset.layers[i];
      final layerOffset = Offset(
        _targetOffset.dx * layer.depth,
        _targetOffset.dy * layer.depth,
      );

      // Create new animation with updated target
      _layerAnimations[i] = _parallaxController.createOptimizedAnimation(
        Tween<Offset>(begin: _currentOffset, end: layerOffset),
        curve: Curves.easeOut,
      );
    }

    _parallaxController.forward(from: 0.0);
    _currentOffset = _targetOffset;
  }

  void _resetParallax() {
    if (!_shouldAnimate) return;

    _targetOffset = Offset.zero;

    // Animate back to center
    for (int i = 0; i < _layerAnimations.length; i++) {
      _layerAnimations[i] = _parallaxController.createOptimizedAnimation(
        Tween<Offset>(begin: _currentOffset, end: Offset.zero),
        curve: Curves.easeOut,
      );
    }

    _parallaxController.forward(from: 0.0);
    _currentOffset = Offset.zero;
  }

  @override
  Widget build(BuildContext context) {
    if (!_shouldAnimate) {
      return _buildStaticContent();
    }

    Widget content = _buildParallaxContent();

    // Wrap with appropriate input detector based on trigger type
    switch (widget.trigger) {
      case ParallaxTrigger.hover:
        content = MouseRegion(
          onEnter: (_) => _onHoverEnter(),
          onExit: (_) => _onHoverExit(),
          onHover: widget.followCursor ? (event) => _onHover(event) : null,
          child: content,
        );
        break;

      case ParallaxTrigger.pan:
        content = GestureDetector(
          onPanUpdate: (details) => _onPan(details),
          onPanEnd: (_) => _onPanEnd(),
          child: content,
        );
        break;

      case ParallaxTrigger.tap:
        content = GestureDetector(
          onTapDown: (details) => _onTapDown(details),
          onTapUp: (_) => _onTapUp(),
          onTapCancel: () => _onTapCancel(),
          child: content,
        );
        break;

      case ParallaxTrigger.scroll:
        content = NotificationListener<ScrollNotification>(
          onNotification: _onScroll,
          child: content,
        );
        break;

      case ParallaxTrigger.continuous:
        // Continuous automatic parallax
        _startContinuousParallax();
        break;
    }

    return SizedBox(
      width: widget.width,
      height: widget.height,
      child: content,
    );
  }

  Widget _buildParallaxContent() {
    return AnimatedBuilder(
      animation: _parallaxController,
      builder: (context, child) {
        return Stack(
          clipBehavior: Clip.none,
          children: [
            // Background layers (furthest depth)
            ...widget.preset.layers.asMap().entries.map((entry) {
              final index = entry.key;
              final layer = entry.value;

              if (index >= _layerAnimations.length) return const SizedBox.shrink();

              final layerOffset = _layerAnimations[index].value;

              return Transform.translate(
                offset: layerOffset,
                child: _buildLayer(layer, index),
              );
            }),

            // Main content (foreground)
            widget.child,
          ],
        );
      },
    );
  }

  Widget _buildLayer(ParallaxLayer layer, int index) {
    // Build different types of layer content based on configuration
    if (layer.asset != null) {
      return _buildAssetLayer(layer);
    } else {
      return _buildGeneratedLayer(layer, index);
    }
  }

  Widget _buildAssetLayer(ParallaxLayer layer) {
    // For future implementation with actual asset files
    return Container(
      width: widget.width,
      height: widget.height,
      decoration: const BoxDecoration(
        color: Colors.transparent,
      ),
      child: const Center(
        child: Text('Asset Layer', style: TextStyle(color: Colors.grey)),
      ),
    );
  }

  Widget _buildGeneratedLayer(ParallaxLayer layer, int index) {
    // Generate procedural content based on layer depth
    final opacity = (1.0 - layer.depth).clamp(0.1, 0.6);
    final particleCount = math.max(2, (8 * (1.0 - layer.depth)).round());

    // Create particles with different properties based on depth
    final colors = _getLayerColors(layer.depth);
    final animationType = _getLayerAnimationType(layer.depth);

    final preset = ParticlePreset(
      count: particleCount,
      duration: Duration(seconds: 3 + index),
      radius: widget.width * 0.3 * (1.0 + layer.depth),
      size: 6.0 * (1.0 - layer.depth * 0.5),
      colors: colors.map((c) => c.withOpacity(opacity)).toList(),
      animationType: animationType,
    );

    return ParticleWidget(
      preset: preset,
      containerWidth: widget.width * 1.2, // Slightly larger for parallax movement
      containerHeight: widget.height * 1.2,
    );
  }

  List<Color> _getLayerColors(double depth) {
    if (depth < 0.3) {
      // Foreground: vibrant colors
      return [
        const Color(0xFF6366F1),
        const Color(0xFF8B5CF6),
        const Color(0xFF06B6D4),
      ];
    } else if (depth < 0.6) {
      // Midground: medium saturation
      return [
        const Color(0xFF94A3B8),
        const Color(0xFF64748B),
        const Color(0xFF475569),
      ];
    } else {
      // Background: muted colors
      return [
        const Color(0xFFE2E8F0),
        const Color(0xFFCBD5E1),
        const Color(0xFFB1BEC8),
      ];
    }
  }

  ParticleAnimationType _getLayerAnimationType(double depth) {
    if (depth < 0.3) {
      return ParticleAnimationType.swirling;
    } else if (depth < 0.6) {
      return ParticleAnimationType.floating;
    } else {
      return ParticleAnimationType.orbiting;
    }
  }

  Widget _buildStaticContent() {
    return SizedBox(
      width: widget.width,
      height: widget.height,
      child: Stack(
        children: [
          // Simplified static background
          Container(
            width: widget.width,
            height: widget.height,
            decoration: BoxDecoration(
              gradient: RadialGradient(
                colors: [
                  Colors.blue.withOpacity(0.1),
                  Colors.purple.withOpacity(0.05),
                  Colors.transparent,
                ],
              ),
            ),
          ),
          widget.child,
        ],
      ),
    );
  }

  // Event handlers
  void _onHoverEnter() {
    _isHovered = true;
    _animationService.triggerHapticFeedback();
  }

  void _onHoverExit() {
    _isHovered = false;
    _resetParallax();
  }

  void _onHover(PointerHoverEvent event) {
    if (_isHovered && widget.followCursor) {
      _updateParallax(event.localPosition);
    }
  }

  void _onPan(DragUpdateDetails details) {
    _updateParallax(details.localPosition);
  }

  void _onPanEnd() {
    _resetParallax();
  }

  void _onTapDown(TapDownDetails details) {
    _updateParallax(details.localPosition);
  }

  void _onTapUp() {
    _resetParallax();
  }

  void _onTapCancel() {
    _resetParallax();
  }

  bool _onScroll(ScrollNotification notification) {
    if (widget.followScroll) {
      _scrollOffset = notification.metrics.pixels;
      final normalizedScroll = (_scrollOffset / 100).clamp(-1.0, 1.0);
      _targetOffset = Offset(0, normalizedScroll * widget.preset.maxOffset);
      _animateToTarget();
    }
    return false;
  }

  void _startContinuousParallax() {
    if (!_shouldAnimate) return;

    // Create a repeating animation that moves the parallax continuously
    final continuousController = CustomAnimationController(
      id: 'parallax_continuous_${widget.hashCode}',
      duration: const Duration(seconds: 10),
      vsync: this,
    );

    final continuousAnimation = continuousController.createOptimizedAnimation(
      Tween<double>(begin: 0.0, end: 2 * math.pi),
      curve: Curves.linear,
    );

    continuousAnimation.addListener(() {
      final angle = continuousAnimation.value;
      final radius = widget.preset.maxOffset * 0.3;

      _targetOffset = Offset(
        math.cos(angle) * radius,
        math.sin(angle) * radius * 0.5,
      );

      _animateToTarget();
    });

    continuousController.repeat();
  }
}

/// Parallax trigger types
enum ParallaxTrigger {
  hover,      // Mouse hover (desktop)
  pan,        // Touch/drag gesture
  tap,        // Tap and hold
  scroll,     // Scroll-based parallax
  continuous, // Automatic continuous movement
}

/// Preset parallax containers
class ParallaxContainers {
  /// Welcome screen hero parallax
  static ParallaxContainer welcomeHero({
    required Widget child,
    double width = 200,
    double height = 200,
  }) {
    return ParallaxContainer(
      preset: WelcomeAnimationPresets.parallaxLayers,
      child: child,
      width: width,
      height: height,
      trigger: ParallaxTrigger.hover,
      followCursor: true,
    );
  }

  /// Subtle background parallax
  static ParallaxContainer backgroundParallax({
    required Widget child,
    required double width,
    required double height,
  }) {
    const preset = ParallaxPreset(
      layers: [
        ParallaxLayer(depth: 0.1),
        ParallaxLayer(depth: 0.3),
      ],
      sensitivity: 0.3,
      maxOffset: 15.0,
    );

    return ParallaxContainer(
      preset: preset,
      child: child,
      width: width,
      height: height,
      trigger: ParallaxTrigger.continuous,
    );
  }

  /// Interactive card parallax
  static ParallaxContainer interactiveCard({
    required Widget child,
    required double width,
    required double height,
  }) {
    const preset = ParallaxPreset(
      layers: [
        ParallaxLayer(depth: 0.2),
        ParallaxLayer(depth: 0.5),
      ],
      sensitivity: 0.8,
      maxOffset: 25.0,
    );

    return ParallaxContainer(
      preset: preset,
      child: child,
      width: width,
      height: height,
      trigger: ParallaxTrigger.hover,
      followCursor: true,
    );
  }

  /// Mobile-friendly parallax (touch-based)
  static ParallaxContainer mobileParallax({
    required Widget child,
    required double width,
    required double height,
  }) {
    const preset = ParallaxPreset(
      layers: [
        ParallaxLayer(depth: 0.15),
        ParallaxLayer(depth: 0.4),
      ],
      sensitivity: 0.6,
      maxOffset: 20.0,
    );

    return ParallaxContainer(
      preset: preset,
      child: child,
      width: width,
      height: height,
      trigger: ParallaxTrigger.pan,
    );
  }
}

/// Parallax effect controller for managing multiple containers
class ParallaxController {
  final List<_ParallaxContainerState> _containers = [];
  bool _globalEnabled = true;

  /// Register a parallax container
  void register(_ParallaxContainerState container) {
    _containers.add(container);
  }

  /// Unregister a parallax container
  void unregister(_ParallaxContainerState container) {
    _containers.remove(container);
  }

  /// Enable/disable all parallax effects
  void setGlobalEnabled(bool enabled) {
    _globalEnabled = enabled;
    // Individual containers will check AnimationService
  }

  /// Reset all parallax effects to center
  void resetAll() {
    for (final container in _containers) {
      container._resetParallax();
    }
  }

  /// Get performance metrics
  Map<String, dynamic> getMetrics() {
    return {
      'containerCount': _containers.length,
      'globalEnabled': _globalEnabled,
      'totalLayers': _containers.fold(0, (sum, container) =>
          sum + container.widget.preset.layers.length),
    };
  }

  /// Dispose all containers
  void dispose() {
    _containers.clear();
  }
}