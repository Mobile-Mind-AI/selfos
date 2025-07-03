import 'package:flutter/material.dart';

/// Model for feature card data
class FeatureData {
  final IconData icon;
  final String title;
  final String description;
  final String? detail;
  final Color? color;

  const FeatureData({
    required this.icon,
    required this.title,
    required this.description,
    this.detail,
    this.color,
  });
}

/// Interactive feature cards widget with hover effects and responsive layout
class FeatureCards extends StatefulWidget {
  final List<FeatureData> features;
  final String? sectionTitle;
  final bool isResponsive;
  final bool enableHoverEffects;
  final Duration animationDuration;
  final Duration entranceDelay;
  final EdgeInsets cardPadding;
  final double cardSpacing;
  final int maxColumns;
  final VoidCallback? onFeatureHover;
  final VoidCallback? onFeatureHoverExit;

  const FeatureCards({
    super.key,
    required this.features,
    this.sectionTitle,
    this.isResponsive = true,
    this.enableHoverEffects = true,
    this.animationDuration = const Duration(milliseconds: 300),
    this.entranceDelay = const Duration(milliseconds: 400),
    this.cardPadding = const EdgeInsets.all(16),
    this.cardSpacing = 16.0,
    this.maxColumns = 3,
    this.onFeatureHover,
    this.onFeatureHoverExit,
  });

  /// Default SelfOS features
  factory FeatureCards.defaultFeatures({
    String? sectionTitle,
    bool isResponsive = true,
    bool enableHoverEffects = true,
  }) {
    return FeatureCards(
      features: const [
        FeatureData(
          icon: Icons.smart_toy,
          title: 'AI Assistant',
          description: 'Personalized help',
          detail: 'Your AI companion learns your preferences and helps you stay motivated.',
        ),
        FeatureData(
          icon: Icons.track_changes,
          title: 'Goal Tracking',
          description: 'Measure progress',
          detail: 'Visualize your journey with intelligent progress tracking and insights.',
        ),
        FeatureData(
          icon: Icons.psychology,
          title: 'Smart Insights',
          description: 'Learn & grow',
          detail: 'Get personalized recommendations based on your patterns and achievements.',
        ),
      ],
      sectionTitle: sectionTitle ?? 'What makes SelfOS special?',
      isResponsive: isResponsive,
      enableHoverEffects: enableHoverEffects,
    );
  }

  @override
  State<FeatureCards> createState() => _FeatureCardsState();
}

class _FeatureCardsState extends State<FeatureCards>
    with TickerProviderStateMixin {

  late AnimationController _slideController;
  late AnimationController _fadeController;

  late Animation<Offset> _slideAnimation;
  late Animation<double> _fadeAnimation;

  int? _hoveredIndex;
  bool _featuresExpanded = false;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _startAnimations();
  }

  @override
  void dispose() {
    _slideController.dispose();
    _fadeController.dispose();
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
  }

  void _startAnimations() {
    _fadeController.forward();

    Future.delayed(widget.entranceDelay, () {
      if (mounted) {
        _slideController.forward();
      }
    });
  }

  void _handleFeatureHover(int index, bool isHovered) {
    if (!widget.enableHoverEffects) return;

    setState(() {
      _hoveredIndex = isHovered ? index : null;
      _featuresExpanded = isHovered;
    });

    if (isHovered) {
      widget.onFeatureHover?.call();
    } else {
      widget.onFeatureHoverExit?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isWideScreen = screenWidth > 768;

    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: Column(
          children: [
            // Section title
            if (widget.sectionTitle != null)
              _buildSectionTitle(context),

            if (widget.sectionTitle != null)
              const SizedBox(height: 16),

            // Feature cards layout
            if (widget.isResponsive && isWideScreen)
              _buildRowLayout(context)
            else
              _buildColumnLayout(context),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context) {
    final theme = Theme.of(context);

    return Text(
      widget.sectionTitle!,
      style: theme.textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.w600,
        color: theme.colorScheme.onSurface,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget _buildRowLayout(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: widget.features.asMap().entries.map((entry) {
        final index = entry.key;
        final feature = entry.value;

        return Expanded(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: widget.cardSpacing / 2),
            child: _buildFeatureCard(context, feature, index),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildColumnLayout(BuildContext context) {
    return Column(
      children: widget.features.asMap().entries.map((entry) {
        final index = entry.key;
        final feature = entry.value;

        return Padding(
          padding: EdgeInsets.only(
            bottom: index < widget.features.length - 1 ? widget.cardSpacing : 0,
          ),
          child: _buildFeatureCard(context, feature, index, isFullWidth: true),
        );
      }).toList(),
    );
  }

  Widget _buildFeatureCard(
    BuildContext context,
    FeatureData feature,
    int index, {
    bool isFullWidth = false,
  }) {
    final theme = Theme.of(context);
    final isHovered = _hoveredIndex == index;
    final isExpanded = _featuresExpanded && isHovered;

    return MouseRegion(
      onEnter: (_) => _handleFeatureHover(index, true),
      onExit: (_) => _handleFeatureHover(index, false),
      child: AnimatedContainer(
        duration: widget.animationDuration,
        width: isFullWidth ? double.infinity : null,
        padding: widget.cardPadding,
        decoration: BoxDecoration(
          color: isExpanded
              ? theme.colorScheme.primary.withOpacity(0.1)
              : theme.colorScheme.surfaceVariant.withOpacity(0.5),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isExpanded
                ? theme.colorScheme.primary
                : theme.colorScheme.primary.withOpacity(0.1),
            width: isExpanded ? 2 : 1,
          ),
          boxShadow: isExpanded ? [
            BoxShadow(
              color: theme.colorScheme.primary.withOpacity(0.2),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ] : null,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icon
            _buildFeatureIcon(theme, feature, isExpanded),

            const SizedBox(height: 12),

            // Title
            _buildFeatureTitle(theme, feature, isExpanded),

            const SizedBox(height: 4),

            // Description
            _buildFeatureDescription(theme, feature, isExpanded),

            // Expandable detail
            if (feature.detail != null)
              _buildExpandableDetail(theme, feature, isExpanded),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureIcon(ThemeData theme, FeatureData feature, bool isExpanded) {
    final iconColor = feature.color ?? theme.colorScheme.primary;

    return AnimatedContainer(
      duration: widget.animationDuration,
      width: isExpanded ? 56 : 48,
      height: isExpanded ? 56 : 48,
      decoration: BoxDecoration(
        color: iconColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(isExpanded ? 28 : 24),
      ),
      child: Icon(
        feature.icon,
        color: iconColor,
        size: isExpanded ? 28 : 24,
      ),
    );
  }

  Widget _buildFeatureTitle(ThemeData theme, FeatureData feature, bool isExpanded) {
    return Text(
      feature.title,
      style: theme.textTheme.labelLarge?.copyWith(
        fontWeight: FontWeight.w600,
        color: isExpanded
            ? theme.colorScheme.primary
            : theme.colorScheme.onSurface,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget _buildFeatureDescription(ThemeData theme, FeatureData feature, bool isExpanded) {
    return Text(
      feature.description,
      style: theme.textTheme.labelSmall?.copyWith(
        color: theme.colorScheme.onSurface.withOpacity(0.6),
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget _buildExpandableDetail(ThemeData theme, FeatureData feature, bool isExpanded) {
    return AnimatedContainer(
      duration: widget.animationDuration,
      height: isExpanded ? null : 0,
      child: isExpanded
          ? Column(
              children: [
                const SizedBox(height: 8),
                Text(
                  feature.detail!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.7),
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            )
          : const SizedBox.shrink(),
    );
  }

  /// Manually trigger entrance animation
  void playEntrance() {
    _fadeController.forward(from: 0);
    Future.delayed(widget.entranceDelay, () {
      if (mounted) {
        _slideController.forward(from: 0);
      }
    });
  }

  /// Update features dynamically
  void updateFeatures(List<FeatureData> newFeatures) {
    setState(() {
      // Features are passed via constructor, so we'd need to rebuild the widget
      // This could be enhanced with a proper state management solution
    });
  }

  /// Simulate hover on specific feature
  void hoverFeature(int index) {
    _handleFeatureHover(index, true);
  }

  /// Clear all hover states
  void clearHover() {
    _handleFeatureHover(-1, false);
  }

  /// Get current state
  Map<String, dynamic> get currentState => {
    'hoveredIndex': _hoveredIndex,
    'featuresExpanded': _featuresExpanded,
    'featureCount': widget.features.length,
    'isAnimating': _slideController.isAnimating || _fadeController.isAnimating,
  };
}