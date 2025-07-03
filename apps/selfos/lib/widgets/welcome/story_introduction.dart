import 'package:flutter/material.dart';

/// Story introduction widget with customizable narrative content
class StoryIntroduction extends StatefulWidget {
  final String title;
  final String description;
  final IconData icon;
  final Color? iconColor;
  final Color? backgroundColor;
  final Color? borderColor;
  final EdgeInsets padding;
  final BorderRadius? borderRadius;
  final Duration entranceDelay;
  final TextStyle? titleStyle;
  final TextStyle? descriptionStyle;
  final bool enableAnimation;
  final VoidCallback? onTap;

  const StoryIntroduction({
    super.key,
    this.title = 'Start Your Story',
    this.description = 'You\'re the main character. We\'ll create an AI assistant who will journey with you. Let\'s start with the basics...',
    this.icon = Icons.auto_stories,
    this.iconColor,
    this.backgroundColor,
    this.borderColor,
    this.padding = const EdgeInsets.all(20),
    this.borderRadius,
    this.entranceDelay = const Duration(milliseconds: 600),
    this.titleStyle,
    this.descriptionStyle,
    this.enableAnimation = true,
    this.onTap,
  });

  /// Factory for motivational variant
  factory StoryIntroduction.motivational({
    Duration? entranceDelay,
    VoidCallback? onTap,
  }) {
    return StoryIntroduction(
      title: 'Begin Your Transformation',
      description: 'Every journey starts with a single step. Today is your day to take that step towards the life you envision.',
      icon: Icons.rocket_launch,
      entranceDelay: entranceDelay ?? const Duration(milliseconds: 600),
      onTap: onTap,
    );
  }

  /// Factory for goal-focused variant
  factory StoryIntroduction.goalFocused({
    Duration? entranceDelay,
    VoidCallback? onTap,
  }) {
    return StoryIntroduction(
      title: 'Design Your Future',
      description: 'Turn your dreams into achievable goals. Let\'s build a roadmap that takes you from where you are to where you want to be.',
      icon: Icons.flag,
      entranceDelay: entranceDelay ?? const Duration(milliseconds: 600),
      onTap: onTap,
    );
  }

  /// Factory for AI-focused variant
  factory StoryIntroduction.aiFocused({
    Duration? entranceDelay,
    VoidCallback? onTap,
  }) {
    return StoryIntroduction(
      title: 'Meet Your AI Companion',
      description: 'Your personal AI assistant will learn your preferences, celebrate your wins, and help you stay motivated every step of the way.',
      icon: Icons.psychology,
      entranceDelay: entranceDelay ?? const Duration(milliseconds: 600),
      onTap: onTap,
    );
  }

  /// Factory for minimal variant
  factory StoryIntroduction.minimal({
    required String title,
    required String description,
    IconData? icon,
    Duration? entranceDelay,
    VoidCallback? onTap,
  }) {
    return StoryIntroduction(
      title: title,
      description: description,
      icon: icon ?? Icons.auto_stories,
      padding: const EdgeInsets.all(16),
      entranceDelay: entranceDelay ?? const Duration(milliseconds: 600),
      onTap: onTap,
    );
  }

  @override
  State<StoryIntroduction> createState() => _StoryIntroductionState();
}

class _StoryIntroductionState extends State<StoryIntroduction>
    with TickerProviderStateMixin {

  late AnimationController _slideController;
  late AnimationController _fadeController;
  late AnimationController _scaleController;

  late Animation<Offset> _slideAnimation;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    if (widget.enableAnimation) {
      _setupAnimations();
      _startAnimations();
    }
  }

  @override
  void dispose() {
    if (widget.enableAnimation) {
      _slideController.dispose();
      _fadeController.dispose();
      _scaleController.dispose();
    }
    super.dispose();
  }

  void _setupAnimations() {
    _slideController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );

    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeOut,
    ));

    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.02,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.easeInOut,
    ));
  }

  void _startAnimations() {
    _fadeController.forward();

    Future.delayed(widget.entranceDelay, () {
      if (mounted) {
        _slideController.forward();
      }
    });
  }

  void _handleHover(bool isHovered) {
    setState(() {
      _isHovered = isHovered;
    });

    if (widget.enableAnimation) {
      if (isHovered) {
        _scaleController.forward();
      } else {
        _scaleController.reverse();
      }
    }
  }

  void _handleTap() {
    if (widget.onTap != null) {
      // Add a little haptic feedback simulation through scale animation
      if (widget.enableAnimation) {
        _scaleController.forward().then((_) {
          _scaleController.reverse();
        });
      }
      widget.onTap!();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (!widget.enableAnimation) {
      return _buildContent(theme);
    }

    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: AnimatedBuilder(
          animation: _scaleAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _scaleAnimation.value,
              child: _buildContent(theme),
            );
          },
        ),
      ),
    );
  }

  Widget _buildContent(ThemeData theme) {
    return MouseRegion(
      onEnter: (_) => _handleHover(true),
      onExit: (_) => _handleHover(false),
      child: GestureDetector(
        onTap: widget.onTap != null ? _handleTap : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: widget.padding,
          decoration: BoxDecoration(
            color: widget.backgroundColor ??
                   theme.colorScheme.surfaceVariant.withOpacity(_isHovered ? 0.4 : 0.3),
            borderRadius: widget.borderRadius ?? BorderRadius.circular(16),
            border: Border.all(
              color: widget.borderColor ??
                     theme.colorScheme.primary.withOpacity(_isHovered ? 0.3 : 0.1),
              width: _isHovered ? 2 : 1,
            ),
            boxShadow: _isHovered ? [
              BoxShadow(
                color: theme.colorScheme.primary.withOpacity(0.1),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ] : null,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Icon
              _buildIcon(theme),

              const SizedBox(height: 12),

              // Title
              _buildTitle(theme),

              const SizedBox(height: 8),

              // Description
              _buildDescription(theme),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIcon(ThemeData theme) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      child: Icon(
        widget.icon,
        color: widget.iconColor ?? theme.colorScheme.primary,
        size: _isHovered ? 36 : 32,
      ),
    );
  }

  Widget _buildTitle(ThemeData theme) {
    final defaultStyle = theme.textTheme.titleMedium?.copyWith(
      fontWeight: FontWeight.w600,
      color: theme.colorScheme.onSurface,
    );

    return AnimatedDefaultTextStyle(
      duration: const Duration(milliseconds: 200),
      style: widget.titleStyle ?? defaultStyle!,
      child: Text(
        widget.title,
        textAlign: TextAlign.center,
      ),
    );
  }

  Widget _buildDescription(ThemeData theme) {
    final defaultStyle = theme.textTheme.bodyMedium?.copyWith(
      color: theme.colorScheme.onSurface.withOpacity(0.7),
    );

    return AnimatedDefaultTextStyle(
      duration: const Duration(milliseconds: 200),
      style: widget.descriptionStyle ?? defaultStyle!,
      child: Text(
        widget.description,
        textAlign: TextAlign.center,
      ),
    );
  }

  /// Manually trigger entrance animation
  void playEntrance() {
    if (widget.enableAnimation) {
      _fadeController.forward(from: 0);
      Future.delayed(widget.entranceDelay, () {
        if (mounted) {
          _slideController.forward(from: 0);
        }
      });
    }
  }

  /// Update content dynamically
  void updateContent({
    String? title,
    String? description,
    IconData? icon,
  }) {
    setState(() {
      // Content is passed via constructor, so this would need widget rebuilding
      // This could be enhanced with proper state management
    });
  }

  /// Trigger hover effect programmatically
  void simulateHover({required bool isHovered}) {
    _handleHover(isHovered);
  }

  /// Trigger tap effect programmatically
  void simulateTap() {
    _handleTap();
  }

  /// Get current state
  Map<String, dynamic> get currentState => {
    'isHovered': _isHovered,
    'title': widget.title,
    'description': widget.description,
    'isAnimating': widget.enableAnimation ?
        (_slideController.isAnimating || _fadeController.isAnimating || _scaleController.isAnimating) : false,
  };
}