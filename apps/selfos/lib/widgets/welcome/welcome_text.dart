import 'package:flutter/material.dart';

/// Welcome text section with time-based greetings and rotating messages
class WelcomeText extends StatefulWidget {
  final String? customTitle;
  final String? customSubtitle;
  final List<String>? customMessages;
  final Duration rotationInterval;
  final Duration entranceDelay;
  final TextStyle? titleStyle;
  final TextStyle? subtitleStyle;
  final TextStyle? messageStyle;
  final bool enableRotation;
  final VoidCallback? onMessageChange;

  const WelcomeText({
    super.key,
    this.customTitle,
    this.customSubtitle,
    this.customMessages,
    this.rotationInterval = const Duration(seconds: 3),
    this.entranceDelay = const Duration(milliseconds: 200),
    this.titleStyle,
    this.subtitleStyle,
    this.messageStyle,
    this.enableRotation = true,
    this.onMessageChange,
  });

  @override
  State<WelcomeText> createState() => _WelcomeTextState();
}

class _WelcomeTextState extends State<WelcomeText>
    with TickerProviderStateMixin {

  late AnimationController _slideController;
  late AnimationController _fadeController;

  late Animation<Offset> _slideAnimation;
  late Animation<double> _fadeAnimation;

  int _currentMessageIndex = 0;
  List<String> _messages = [];
  String _title = '';
  String _subtitle = '';

  @override
  void initState() {
    super.initState();
    _initializeContent();
    _setupAnimations();
    _startAnimations();
    if (widget.enableRotation) {
      _startMessageRotation();
    }
  }

  @override
  void dispose() {
    _slideController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  void _initializeContent() {
    // Set title
    _title = widget.customTitle ?? 'Welcome to SelfOS';

    // Set subtitle
    _subtitle = widget.customSubtitle ?? 'Your Personal Growth Operating System';

    // Set rotating messages
    if (widget.customMessages != null && widget.customMessages!.isNotEmpty) {
      _messages = widget.customMessages!;
    } else {
      _messages = _generateTimeBasedMessages();
    }
  }

  List<String> _generateTimeBasedMessages() {
    final hour = DateTime.now().hour;
    final isWeekend = DateTime.now().weekday >= 6;

    String timeGreeting;
    if (hour < 12) {
      timeGreeting = 'Good morning! Ready to start your story?';
    } else if (hour < 17) {
      timeGreeting = 'Good afternoon! Perfect timing to begin.';
    } else if (hour < 22) {
      timeGreeting = 'Good evening! Ready to design your journey?';
    } else {
      timeGreeting = 'Working late? Let\'s make it productive!';
    }

    final messages = [timeGreeting];

    // Add context-based messages
    if (isWeekend) {
      messages.addAll([
        'Weekend vibes! Perfect for planning ahead.',
        'Relaxed weekend, focused growth.',
        'Your future self will thank you for starting today.',
      ]);
    } else {
      messages.addAll([
        'Turn your dreams into actionable plans.',
        'Every expert was once a beginner.',
        'Progress, not perfection, is the goal.',
        'What you focus on grows.',
      ]);
    }

    return messages;
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
      begin: const Offset(0, 0.5),
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

  void _startMessageRotation() {
    if (_messages.length <= 1) return;

    Future.delayed(widget.rotationInterval, () {
      if (mounted && widget.enableRotation) {
        setState(() {
          _currentMessageIndex = (_currentMessageIndex + 1) % _messages.length;
        });
        widget.onMessageChange?.call();
        _startMessageRotation();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: Column(
          children: [
            // Main title
            _buildTitle(theme),

            const SizedBox(height: 16),

            // Subtitle
            _buildSubtitle(theme),

            const SizedBox(height: 24),

            // Rotating message
            if (_messages.isNotEmpty)
              _buildRotatingMessage(theme),
          ],
        ),
      ),
    );
  }

  Widget _buildTitle(ThemeData theme) {
    final defaultStyle = theme.textTheme.headlineLarge?.copyWith(
      fontWeight: FontWeight.bold,
      color: theme.colorScheme.onSurface,
    );

    return Text(
      _title,
      style: widget.titleStyle ?? defaultStyle,
      textAlign: TextAlign.center,
    );
  }

  Widget _buildSubtitle(ThemeData theme) {
    final defaultStyle = theme.textTheme.titleMedium?.copyWith(
      color: theme.colorScheme.onSurface.withOpacity(0.8),
    );

    return Text(
      _subtitle,
      style: widget.subtitleStyle ?? defaultStyle,
      textAlign: TextAlign.center,
    );
  }

  Widget _buildRotatingMessage(ThemeData theme) {
    final defaultStyle = theme.textTheme.bodyLarge?.copyWith(
      color: theme.colorScheme.primary,
      fontWeight: FontWeight.w500,
    );

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 500),
      transitionBuilder: (Widget child, Animation<double> animation) {
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.3),
              end: Offset.zero,
            ).animate(animation),
            child: child,
          ),
        );
      },
      child: Container(
        key: ValueKey(_currentMessageIndex),
        constraints: const BoxConstraints(maxWidth: 400),
        child: Text(
          _messages[_currentMessageIndex],
          style: widget.messageStyle ?? defaultStyle,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// Manually trigger next message
  void nextMessage() {
    if (_messages.length > 1) {
      setState(() {
        _currentMessageIndex = (_currentMessageIndex + 1) % _messages.length;
      });
      widget.onMessageChange?.call();
    }
  }

  /// Manually trigger previous message
  void previousMessage() {
    if (_messages.length > 1) {
      setState(() {
        _currentMessageIndex = (_currentMessageIndex - 1 + _messages.length) % _messages.length;
      });
      widget.onMessageChange?.call();
    }
  }

  /// Jump to specific message index
  void jumpToMessage(int index) {
    if (index >= 0 && index < _messages.length) {
      setState(() {
        _currentMessageIndex = index;
      });
      widget.onMessageChange?.call();
    }
  }

  /// Update messages dynamically
  void updateMessages(List<String> newMessages) {
    setState(() {
      _messages = newMessages;
      _currentMessageIndex = 0;
    });
  }

  /// Update title and subtitle
  void updateText({String? title, String? subtitle}) {
    setState(() {
      if (title != null) _title = title;
      if (subtitle != null) _subtitle = subtitle;
    });
  }

  /// Play entrance animation
  void playEntrance() {
    _fadeController.forward(from: 0);
    Future.delayed(widget.entranceDelay, () {
      if (mounted) {
        _slideController.forward(from: 0);
      }
    });
  }

  /// Get current state
  Map<String, dynamic> get currentState => {
    'title': _title,
    'subtitle': _subtitle,
    'currentMessage': _messages.isNotEmpty ? _messages[_currentMessageIndex] : '',
    'messageIndex': _currentMessageIndex,
    'totalMessages': _messages.length,
    'isAnimating': _slideController.isAnimating || _fadeController.isAnimating,
  };
}