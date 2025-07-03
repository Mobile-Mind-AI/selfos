import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:math' as math;

/// Service for generating personalized, time-based greetings
class GreetingService {
  static GreetingService? _instance;
  static GreetingService get instance => _instance ??= GreetingService._();

  GreetingService._();

  // User preference tracking
  String? _userName;
  bool _isReturningUser = false;
  DateTime? _lastVisit;
  int _visitCount = 0;
  String _preferredLanguage = 'en';

  // Greeting templates by time and context
  final Map<String, Map<String, List<String>>> _greetingTemplates = {
    'en': {
      'morning_new': [
        'Good morning! Ready to start your story?',
        'Rise and shine! Your journey begins now.',
        'Good morning! Let\'s create something amazing today.',
        'Morning! Time to turn your dreams into plans.',
        'Good morning! Your future self is waiting.',
      ],
      'morning_returning': [
        'Good morning! Welcome back to your journey.',
        'Morning! Ready to continue where you left off?',
        'Good morning! Let\'s build on yesterday\'s progress.',
        'Rise and shine! Your goals are calling.',
        'Morning! Another day, another step forward.',
      ],
      'afternoon_new': [
        'Good afternoon! Perfect timing to start fresh.',
        'Afternoon! Ready to design your path forward?',
        'Good afternoon! Let\'s make this moment count.',
        'Perfect timing! Your transformation starts now.',
        'Good afternoon! Time to unlock your potential.',
      ],
      'afternoon_returning': [
        'Good afternoon! How\'s your progress today?',
        'Afternoon! Ready for your next breakthrough?',
        'Good afternoon! Let\'s keep the momentum going.',
        'Perfect timing for a productivity boost!',
        'Afternoon! Your future self will thank you.',
      ],
      'evening_new': [
        'Good evening! A perfect time for new beginnings.',
        'Evening! Ready to plan tomorrow\'s success?',
        'Good evening! Let\'s set up your path to greatness.',
        'Perfect evening to design your journey.',
        'Good evening! Your story starts whenever you\'re ready.',
      ],
      'evening_returning': [
        'Good evening! How did today treat your goals?',
        'Evening! Time to reflect and plan ahead.',
        'Good evening! Ready to wind down and prepare?',
        'Perfect time to review today\'s wins!',
        'Evening! Let\'s set tomorrow up for success.',
      ],
      'late_night': [
        'Working late? Let\'s make it productive!',
        'Late night planning session? Perfect!',
        'Night owl mode activated! Let\'s create.',
        'Late night energy for early morning wins!',
        'Burning the midnight oil? Let\'s make it count!',
      ],
      'weekend': [
        'Happy weekend! Time for personal growth.',
        'Weekend vibes! Perfect for planning ahead.',
        'Weekend energy! Let\'s invest in your future.',
        'Relaxed weekend perfect for goal setting.',
        'Weekend time! Let\'s work on your dreams.',
      ],
      'monday': [
        'Monday motivation! Let\'s start the week strong.',
        'Fresh Monday, fresh possibilities!',
        'Monday magic! Your week of wins begins now.',
        'New week, new opportunities to grow!',
        'Monday momentum! Let\'s build something great.',
      ],
      'friday': [
        'Friday feeling! Let\'s finish the week strong.',
        'TGIF! Perfect time to plan the weekend.',
        'Friday energy! Let\'s prep for next week.',
        'End-of-week reflection time!',
        'Friday momentum! Keep the progress going.',
      ],
    },
    'es': {
      'morning_new': [
        '¡Buenos días! ¿Listo para comenzar tu historia?',
        '¡Despierta y brilla! Tu viaje comienza ahora.',
        '¡Buenos días! Creemos algo increíble hoy.',
        '¡Mañana! Es hora de convertir tus sueños en planes.',
        '¡Buenos días! Tu yo futuro te está esperando.',
      ],
      'morning_returning': [
        '¡Buenos días! Bienvenido de vuelta a tu viaje.',
        '¡Mañana! ¿Listo para continuar donde lo dejaste?',
        '¡Buenos días! Construyamos sobre el progreso de ayer.',
        '¡Despierta y brilla! Tus metas te están llamando.',
        '¡Mañana! Otro día, otro paso adelante.',
      ],
      // Add more Spanish templates...
    },
    // Add more languages as needed
  };

  // Contextual modifiers based on user behavior
  final Map<String, List<String>> _contextualModifiers = {
    'first_time': [
      'Welcome to your transformation journey!',
      'This is where your story begins.',
      'Every expert was once a beginner.',
      'Your future self starts here.',
      'Ready to become who you\'re meant to be?',
    ],
    'streak_building': [
      'Your consistency is paying off!',
      'Momentum is building beautifully.',
      'Each day compounds your progress.',
      'You\'re creating powerful habits.',
      'This streak is your superpower!',
    ],
    'goal_achiever': [
      'Look at you crushing goals!',
      'Your determination is inspiring.',
      'Success looks good on you.',
      'You\'re proving what\'s possible.',
      'Goals achieved, dreams realized!',
    ],
    'need_motivation': [
      'Every small step counts.',
      'Progress, not perfection.',
      'You\'re stronger than you think.',
      'Tomorrow starts with today.',
      'Your breakthrough is coming.',
    ],
  };

  /// Initialize the greeting service with user data
  Future<void> initialize() async {
    await _loadUserData();
    await _updateVisitTracking();
  }

  /// Load user data from preferences
  Future<void> _loadUserData() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      _userName = prefs.getString('user_name');
      _lastVisit = prefs.getString('last_visit') != null
          ? DateTime.parse(prefs.getString('last_visit')!)
          : null;
      _visitCount = prefs.getInt('visit_count') ?? 0;
      _preferredLanguage = prefs.getString('preferred_language') ?? 'en';
      _isReturningUser = _visitCount > 0;

      debugPrint('GreetingService: Loaded user data - visits: $_visitCount, returning: $_isReturningUser');
    } catch (e) {
      debugPrint('GreetingService: Error loading user data: $e');
    }
  }

  /// Update visit tracking
  Future<void> _updateVisitTracking() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final now = DateTime.now();

      // Check if this is a new day
      bool isNewDay = _lastVisit == null ||
          !_isSameDay(_lastVisit!, now);

      if (isNewDay) {
        _visitCount++;
        _isReturningUser = _visitCount > 1;

        await prefs.setInt('visit_count', _visitCount);
        await prefs.setString('last_visit', now.toIso8601String());

        _lastVisit = now;

        debugPrint('GreetingService: Updated visit tracking - count: $_visitCount');
      }
    } catch (e) {
      debugPrint('GreetingService: Error updating visit tracking: $e');
    }
  }

  /// Generate main greeting based on current time and user context
  String generateGreeting({
    String? customName,
    bool forceRefresh = false,
  }) {
    final now = DateTime.now();
    final timeContext = _getTimeContext(now);
    final userContext = _isReturningUser ? 'returning' : 'new';
    final key = '${timeContext}_$userContext';

    final templates = _greetingTemplates[_preferredLanguage]?[key] ??
                     _greetingTemplates['en']![key]!;

    // Select greeting based on time and some randomness
    final index = _getGreetingIndex(templates.length, now);
    String greeting = templates[index];

    // Personalize with name if available
    final name = customName ?? _userName;
    if (name != null && name.isNotEmpty) {
      greeting = _personalizeWithName(greeting, name);
    }

    return greeting;
  }

  /// Generate contextual subtitle based on user behavior
  String generateSubtitle({UserContext? context}) {
    final userContext = context ?? _determineUserContext();
    final modifiers = _contextualModifiers[userContext.toString().split('.').last] ??
                     _contextualModifiers['first_time']!;

    final index = math.Random().nextInt(modifiers.length);
    return modifiers[index];
  }

  /// Generate dynamic rotating messages for the welcome screen
  List<String> generateRotatingMessages() {
    final messages = <String>[];

    // Add time-based message
    messages.add(_getTimeBasedMessage());

    // Add motivational message
    messages.add(_getMotivationalMessage());

    // Add goal-focused message
    messages.add(_getGoalFocusedMessage());

    // Add progress message (if returning user)
    if (_isReturningUser) {
      messages.add(_getProgressMessage());
    }

    return messages;
  }

  /// Get greeting for specific time of day
  String getTimeBasedGreeting(TimeOfDay timeOfDay) {
    final now = DateTime.now();
    final adjustedTime = DateTime(
      now.year, now.month, now.day,
      timeOfDay.hour, timeOfDay.minute,
    );

    final timeContext = _getTimeContext(adjustedTime);
    final userContext = _isReturningUser ? 'returning' : 'new';
    final key = '${timeContext}_$userContext';

    final templates = _greetingTemplates[_preferredLanguage]?[key] ??
                     _greetingTemplates['en']![key]!;

    return templates.first;
  }

  /// Get encouragement message based on user progress
  String getEncouragementMessage({
    int? completedGoals,
    int? currentStreak,
    bool? hasRecentActivity,
  }) {
    if (completedGoals != null && completedGoals > 0) {
      return _contextualModifiers['goal_achiever']![
        math.Random().nextInt(_contextualModifiers['goal_achiever']!.length)
      ];
    }

    if (currentStreak != null && currentStreak > 3) {
      return _contextualModifiers['streak_building']![
        math.Random().nextInt(_contextualModifiers['streak_building']!.length)
      ];
    }

    if (hasRecentActivity == false) {
      return _contextualModifiers['need_motivation']![
        math.Random().nextInt(_contextualModifiers['need_motivation']!.length)
      ];
    }

    return _contextualModifiers['first_time']![
      math.Random().nextInt(_contextualModifiers['first_time']!.length)
    ];
  }

  /// Update user preferences
  Future<void> updateUserPreferences({
    String? name,
    String? language,
  }) async {
    final prefs = await SharedPreferences.getInstance();

    if (name != null) {
      _userName = name;
      await prefs.setString('user_name', name);
    }

    if (language != null) {
      _preferredLanguage = language;
      await prefs.setString('preferred_language', language);
    }
  }

  // Private helper methods

  String _getTimeContext(DateTime time) {
    final hour = time.hour;
    final weekday = time.weekday;

    // Special day handling
    if (weekday == DateTime.monday) return 'monday';
    if (weekday == DateTime.friday) return 'friday';
    if (weekday == DateTime.saturday || weekday == DateTime.sunday) return 'weekend';

    // Time of day
    if (hour >= 5 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 17) return 'afternoon';
    if (hour >= 17 && hour < 22) return 'evening';
    return 'late_night';
  }

  int _getGreetingIndex(int templateCount, DateTime time) {
    // Use time-based seed for some consistency within the same hour
    final seed = time.hour + time.day;
    final random = math.Random(seed);
    return random.nextInt(templateCount);
  }

  String _personalizeWithName(String greeting, String name) {
    // Simple personalization - could be enhanced with more sophisticated NLP
    if (greeting.startsWith('Good morning!')) {
      return greeting.replaceFirst('Good morning!', 'Good morning, $name!');
    }
    if (greeting.startsWith('Good afternoon!')) {
      return greeting.replaceFirst('Good afternoon!', 'Good afternoon, $name!');
    }
    if (greeting.startsWith('Good evening!')) {
      return greeting.replaceFirst('Good evening!', 'Good evening, $name!');
    }

    // Fallback: add name at the end
    return '$greeting Welcome, $name!';
  }

  UserContext _determineUserContext() {
    if (_visitCount == 0) return UserContext.firstTime;
    if (_visitCount > 7) return UserContext.streakBuilding;
    // This would be enhanced with actual goal completion data
    return UserContext.needMotivation;
  }

  String _getTimeBasedMessage() {
    final hour = DateTime.now().hour;
    if (hour < 12) {
      return 'Start your day with purpose and intention.';
    } else if (hour < 17) {
      return 'Perfect time to focus on what matters most.';
    } else {
      return 'Evening reflection leads to morning clarity.';
    }
  }

  String _getMotivationalMessage() {
    final motivational = [
      'Every expert was once a beginner.',
      'Progress, not perfection, is the goal.',
      'Your future self will thank you for starting today.',
      'Small steps lead to big transformations.',
      'The best time to plant a tree was 20 years ago. The second best time is now.',
    ];
    return motivational[math.Random().nextInt(motivational.length)];
  }

  String _getGoalFocusedMessage() {
    final goalFocused = [
      'Turn your dreams into actionable plans.',
      'Goals without a plan are just wishes.',
      'What you focus on grows.',
      'Clarity leads to achievement.',
      'Your goals are the roadmap to your future.',
    ];
    return goalFocused[math.Random().nextInt(goalFocused.length)];
  }

  String _getProgressMessage() {
    return 'Welcome back! Let\'s build on your momentum.';
  }

  bool _isSameDay(DateTime date1, DateTime date2) {
    return date1.year == date2.year &&
           date1.month == date2.month &&
           date1.day == date2.day;
  }

  // Getters for current state
  bool get isReturningUser => _isReturningUser;
  int get visitCount => _visitCount;
  String? get userName => _userName;
  DateTime? get lastVisit => _lastVisit;
  String get preferredLanguage => _preferredLanguage;
}

/// User context for personalized messaging
enum UserContext {
  firstTime,
  streakBuilding,
  goalAchiever,
  needMotivation,
}

/// Greeting configuration for different scenarios
class GreetingConfig {
  final bool showTimeBasedGreeting;
  final bool showPersonalization;
  final bool showRotatingMessages;
  final Duration rotationInterval;
  final bool enableEncouragement;

  const GreetingConfig({
    this.showTimeBasedGreeting = true,
    this.showPersonalization = true,
    this.showRotatingMessages = true,
    this.rotationInterval = const Duration(seconds: 3),
    this.enableEncouragement = true,
  });
}

/// Greeting data model
class GreetingData {
  final String mainGreeting;
  final String subtitle;
  final List<String> rotatingMessages;
  final UserContext userContext;
  final bool isPersonalized;

  const GreetingData({
    required this.mainGreeting,
    required this.subtitle,
    required this.rotatingMessages,
    required this.userContext,
    required this.isPersonalized,
  });
}

/// Provider-like interface for using in widgets
class GreetingProvider {
  static GreetingData generateWelcomeData({GreetingConfig? config}) {
    final service = GreetingService.instance;
    config ??= const GreetingConfig();

    return GreetingData(
      mainGreeting: service.generateGreeting(),
      subtitle: service.generateSubtitle(),
      rotatingMessages: config.showRotatingMessages
          ? service.generateRotatingMessages()
          : [],
      userContext: service._determineUserContext(),
      isPersonalized: service.userName != null,
    );
  }
}