import 'package:flutter/material.dart';

/// Welcome actions widget with primary and secondary action buttons
class WelcomeActions extends StatefulWidget {
  final String primaryText;
  final String secondaryText;
  final VoidCallback? onPrimaryPressed;
  final VoidCallback? onSecondaryPressed;
  final IconData? primaryIcon;
  final IconData? secondaryIcon;
  final bool primaryEnabled;
  final bool secondaryEnabled;
  final bool primaryLoading;
  final bool secondaryLoading;
  final Duration entranceDelay;
  final Duration animationDuration;
  final bool enableHoverEffects;
  final bool enableIconAnimation;
  final EdgeInsets buttonPadding;
  final double spacing;
  final ButtonStyle? primaryButtonStyle;
  final ButtonStyle? secondaryButtonStyle;
  final TextStyle? primaryTextStyle;
  final TextStyle? secondaryTextStyle;

  const WelcomeActions({
    super.key,
    this.primaryText = 'Begin Your Journey',
    this.secondaryText = 'Skip setup (use defaults)',
    this.onPrimaryPressed,
    this.onSecondaryPressed,
    this.primaryIcon = Icons.arrow_forward,
    this.secondaryIcon,
    this.primaryEnabled = true,
    this.secondaryEnabled = true,
    this.primaryLoading = false,
    this.secondaryLoading = false,
    this.entranceDelay = const Duration(milliseconds: 800),
    this.animationDuration = const Duration(milliseconds: 300),
    this.enableHoverEffects = true,
    this.enableIconAnimation = true,
    this.buttonPadding = const EdgeInsets.symmetric(vertical: 18),
    this.spacing = 12.0,
    this.primaryButtonStyle,
    this.secondaryButtonStyle,
    this.primaryTextStyle,
    this.secondaryTextStyle,
  });

  /// Factory for onboarding actions
  factory WelcomeActions.onboarding({
    required VoidCallback onNext,
    required VoidCallback onSkip,
    bool enableHoverEffects = true,
  }) {
    return WelcomeActions(
      primaryText: 'Begin Your Journey',
      secondaryText: 'Skip setup (use defaults)',
      primaryIcon: Icons.arrow_forward,
      onPrimaryPressed: onNext,
      onSecondaryPressed: onSkip,
      enableHoverEffects: enableHoverEffects,
    );
  }

  /// Factory for authentication actions
  factory WelcomeActions.auth({
    required VoidCallback onSignIn,
    required VoidCallback onSignUp,
    bool isLoading = false,
  }) {
    return WelcomeActions(
      primaryText: 'Sign In',
      secondaryText: 'Create Account',
      primaryIcon: Icons.login,
      secondaryIcon: Icons.person_add,
      onPrimaryPressed: onSignIn,
      onSecondaryPressed: onSignUp,
      primaryLoading: isLoading,
      secondaryEnabled: !isLoading,
    );
  }

  /// Factory for single action
  factory WelcomeActions.single({
    required String text,
    required VoidCallback onPressed,
    IconData? icon,
    bool isLoading = false,
    bool enabled = true,
  }) {
    return WelcomeActions(
      primaryText: text,
      secondaryText: '',
      primaryIcon: icon,
      onPrimaryPressed: onPressed,
      primaryLoading: isLoading,
      primaryEnabled: enabled,
      secondaryEnabled: false,
    );
  }

  /// Factory for custom actions
  factory WelcomeActions.custom({
    required String primaryText,
    required String secondaryText,
    required VoidCallback onPrimary,
    required VoidCallback onSecondary,
    IconData? primaryIcon,
    IconData? secondaryIcon,
    Duration? entranceDelay,
  }) {
    return WelcomeActions(
      primaryText: primaryText,
      secondaryText: secondaryText,
      primaryIcon: primaryIcon,
      secondaryIcon: secondaryIcon,
      onPrimaryPressed: onPrimary,
      onSecondaryPressed: onSecondary,
      entranceDelay: entranceDelay ?? const Duration(milliseconds: 800),
    );
  }

  @override
  State<WelcomeActions> createState() => _WelcomeActionsState();
}

class _WelcomeActionsState extends State<WelcomeActions>
    with TickerProviderStateMixin {

  late AnimationController _slideController;
  late AnimationController _fadeController;
  late AnimationController _iconRotationController;

  late Animation<Offset> _slideAnimation;
  late Animation<double> _fadeAnimation;
  late Animation<double> _iconRotationAnimation;

  bool _isPrimaryHovered = false;
  bool _isSecondaryHovered = false;

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
    _iconRotationController.dispose();
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

    _iconRotationController = AnimationController(
      duration: widget.animationDuration,
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

    _iconRotationAnimation = Tween<double>(
      begin: 0.0,
      end: 0.1,
    ).animate(CurvedAnimation(
      parent: _iconRotationController,
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

  void _handlePrimaryHover(bool isHovered) {
    if (!widget.enableHoverEffects) return;

    setState(() {
      _isPrimaryHovered = isHovered;
    });

    if (widget.enableIconAnimation && widget.primaryIcon != null) {
      if (isHovered) {
        _iconRotationController.forward();
      } else {
        _iconRotationController.reverse();
      }
    }
  }

  void _handleSecondaryHover(bool isHovered) {
    if (!widget.enableHoverEffects) return;

    setState(() {
      _isSecondaryHovered = isHovered;
    });
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Primary action button
            _buildPrimaryButton(context),

            // Spacing between buttons
            if (widget.secondaryText.isNotEmpty && widget.secondaryEnabled)
              SizedBox(height: widget.spacing),

            // Secondary action button
            if (widget.secondaryText.isNotEmpty && widget.secondaryEnabled)
              _buildSecondaryButton(context),
          ],
        ),
      ),
    );
  }

  Widget _buildPrimaryButton(BuildContext context) {
    final theme = Theme.of(context);

    return MouseRegion(
      onEnter: (_) => _handlePrimaryHover(true),
      onExit: (_) => _handlePrimaryHover(false),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          onPressed: widget.primaryEnabled && !widget.primaryLoading
              ? widget.onPrimaryPressed
              : null,
          style: widget.primaryButtonStyle ?? ElevatedButton.styleFrom(
            padding: widget.buttonPadding,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            elevation: _isPrimaryHovered ? 6 : 4,
          ),
          child: widget.primaryLoading
              ? _buildLoadingIndicator(theme)
              : _buildPrimaryButtonContent(theme),
        ),
      ),
    );
  }

  Widget _buildPrimaryButtonContent(ThemeData theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          widget.primaryText,
          style: widget.primaryTextStyle ?? const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),

        if (widget.primaryIcon != null) ...[
          const SizedBox(width: 8),
          AnimatedBuilder(
            animation: _iconRotationAnimation,
            builder: (context, child) {
              return Transform.rotate(
                angle: _iconRotationAnimation.value,
                child: Icon(
                  widget.primaryIcon,
                  size: 24,
                ),
              );
            },
          ),
        ],
      ],
    );
  }

  Widget _buildSecondaryButton(BuildContext context) {
    final theme = Theme.of(context);

    return MouseRegion(
      onEnter: (_) => _handleSecondaryHover(true),
      onExit: (_) => _handleSecondaryHover(false),
      child: AnimatedContainer(
        duration: widget.animationDuration,
        child: widget.secondaryLoading
            ? _buildLoadingIndicator(theme, isSecondary: true)
            : TextButton(
                onPressed: widget.secondaryEnabled && !widget.secondaryLoading
                    ? widget.onSecondaryPressed
                    : null,
                style: widget.secondaryButtonStyle ?? TextButton.styleFrom(
                  padding: widget.buttonPadding,
                  foregroundColor: _isSecondaryHovered
                      ? theme.colorScheme.primary
                      : theme.colorScheme.onSurface.withOpacity(0.6),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (widget.secondaryIcon != null) ...[
                      Icon(
                        widget.secondaryIcon,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                    ],
                    Text(
                      widget.secondaryText,
                      style: widget.secondaryTextStyle ?? TextStyle(
                        fontSize: 16,
                        fontWeight: _isSecondaryHovered
                            ? FontWeight.w600
                            : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildLoadingIndicator(ThemeData theme, {bool isSecondary = false}) {
    return SizedBox(
      height: 24,
      width: 24,
      child: CircularProgressIndicator(
        strokeWidth: 2,
        valueColor: AlwaysStoppedAnimation<Color>(
          isSecondary
              ? theme.colorScheme.primary
              : theme.colorScheme.onPrimary,
        ),
      ),
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

  /// Simulate button hover effects
  void simulateHover({bool primary = true, bool isHovered = true}) {
    if (primary) {
      _handlePrimaryHover(isHovered);
    } else {
      _handleSecondaryHover(isHovered);
    }
  }

  /// Trigger button press programmatically
  void triggerPress({bool primary = true}) {
    if (primary && widget.onPrimaryPressed != null) {
      widget.onPrimaryPressed!();
    } else if (!primary && widget.onSecondaryPressed != null) {
      widget.onSecondaryPressed!();
    }
  }

  /// Get current state
  Map<String, dynamic> get currentState => {
    'isPrimaryHovered': _isPrimaryHovered,
    'isSecondaryHovered': _isSecondaryHovered,
    'primaryEnabled': widget.primaryEnabled,
    'secondaryEnabled': widget.secondaryEnabled,
    'primaryLoading': widget.primaryLoading,
    'secondaryLoading': widget.secondaryLoading,
    'isAnimating': _slideController.isAnimating || _fadeController.isAnimating,
  };
}