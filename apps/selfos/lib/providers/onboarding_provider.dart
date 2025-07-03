import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../services/storage_service.dart';

/// Onboarding state for tracking user progress
enum OnboardingStatus {
  unknown,
  notStarted,
  inProgress,
  completed,
}

/// Onboarding data model
class OnboardingState {
  final String id;
  final String userId;
  final int currentStep;
  final List<int> completedSteps;
  final bool onboardingCompleted;
  final String? assistantProfileId;
  final List<int> selectedLifeAreas;
  final int? firstGoalId;
  final int? firstTaskId;
  final Map<String, dynamic> tempData;
  final DateTime startedAt;
  final DateTime? completedAt;
  final DateTime lastActivity;

  const OnboardingState({
    required this.id,
    required this.userId,
    required this.currentStep,
    required this.completedSteps,
    required this.onboardingCompleted,
    this.assistantProfileId,
    required this.selectedLifeAreas,
    this.firstGoalId,
    this.firstTaskId,
    required this.tempData,
    required this.startedAt,
    this.completedAt,
    required this.lastActivity,
  });

  factory OnboardingState.fromJson(Map<String, dynamic> json) {
    return OnboardingState(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      currentStep: json['current_step'] as int,
      completedSteps: List<int>.from(json['completed_steps'] as List),
      onboardingCompleted: json['onboarding_completed'] as bool,
      assistantProfileId: json['assistant_profile_id'] as String?,
      selectedLifeAreas: List<int>.from(json['selected_life_areas'] as List),
      firstGoalId: json['first_goal_id'] as int?,
      firstTaskId: json['first_task_id'] as int?,
      tempData: Map<String, dynamic>.from(json['temp_data'] as Map? ?? {}),
      startedAt: DateTime.parse(json['started_at'] as String),
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
      lastActivity: DateTime.parse(json['last_activity'] as String),
    );
  }
}

/// Onboarding notifier for managing onboarding state
class OnboardingNotifier extends StateNotifier<AsyncValue<OnboardingStatus>> {
  OnboardingNotifier() : super(const AsyncValue.data(OnboardingStatus.unknown));

  final Dio _dio = Dio();
  OnboardingState? _onboardingState;
  
  // Rate limiting for step updates
  DateTime? _lastStepUpdate;
  Timer? _stepUpdateTimer;

  /// Get the current onboarding state data
  OnboardingState? get onboardingState => _onboardingState;

  /// Check if user has completed onboarding
  Future<bool> checkOnboardingStatus() async {
    try {
      state = const AsyncValue.loading();

      final token = await StorageService.getAccessToken();
      if (token == null) {
        state = const AsyncValue.data(OnboardingStatus.notStarted);
        return false;
      }

      print('🔍 ONBOARDING: Checking onboarding status...');
      final response = await _dio.get(
        '${ApiConfig.baseUrl}/api/onboarding/state',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        print('🔍 ONBOARDING: Status response: $data');
        _onboardingState = OnboardingState.fromJson(data);

        if (_onboardingState!.onboardingCompleted) {
          state = const AsyncValue.data(OnboardingStatus.completed);
          return true;
        } else if (_onboardingState!.completedSteps.isNotEmpty) {
          state = const AsyncValue.data(OnboardingStatus.inProgress);
          return false;
        } else {
          state = const AsyncValue.data(OnboardingStatus.notStarted);
          return false;
        }
      } else {
        // No onboarding state found, user hasn't started
        state = const AsyncValue.data(OnboardingStatus.notStarted);
        return false;
      }
    } catch (e) {
      print('🔴 ONBOARDING: Check status error: $e');
      // On error, assume onboarding not completed
      state = AsyncValue.error(e, StackTrace.current);
      return false;
    }
  }

  /// Update onboarding step
  Future<bool> updateOnboardingStep(String step, Map<String, dynamic> data) async {
    try {
      // Rate limiting: minimum 2 seconds between step updates
      if (_lastStepUpdate != null && 
          DateTime.now().difference(_lastStepUpdate!) < const Duration(seconds: 2)) {
        print('🚦 ONBOARDING: Rate limiting step update for $step');
        return false;
      }
      
      _lastStepUpdate = DateTime.now();
      
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      print('🚦 ONBOARDING: Making step update request for $step');
      final response = await _dio.post(
        '${ApiConfig.baseUrl}/api/onboarding/step',
        data: {
          'step': step,
          'data': data,
        },
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        print('🚦 ONBOARDING: Step update successful for $step');
        // Don't refresh status immediately to avoid router conflicts
        // The status will be checked when completing onboarding
        return true;
      }
      print('🚦 ONBOARDING: Step update failed with status ${response.statusCode}');
      return false;
    } catch (e) {
      print('🚦 ONBOARDING: Step update error for $step: $e');
      if (e is DioException && e.response?.statusCode == 429) {
        print('🚦 ONBOARDING: Rate limited by server (429), will retry in 3 seconds');
        // Schedule a retry for rate limited requests
        _stepUpdateTimer?.cancel();
        _stepUpdateTimer = Timer(const Duration(seconds: 3), () {
          // Retry the step update after the rate limit period
          print('🚦 ONBOARDING: Retrying step update for $step after rate limit');
          updateOnboardingStep(step, data);
        });
        // Don't set error state for rate limiting, just return false
        return false;
      }
      state = AsyncValue.error(e, StackTrace.current);
      return false;
    }
  }

  /// Complete onboarding
  Future<bool> completeOnboarding() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      final response = await _dio.post(
        '${ApiConfig.baseUrl}/api/onboarding/complete',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        state = const AsyncValue.data(OnboardingStatus.completed);
        return true;
      }
      return false;
    } catch (e) {
      print('🔴 ONBOARDING: Complete onboarding failed: $e');
      if (e is DioException && e.response != null) {
        print('🔴 ONBOARDING: Error response: ${e.response?.data}');
        print('🔴 ONBOARDING: Status code: ${e.response?.statusCode}');
      }
      // Don't set error state if we're completing onboarding
      // Just log the error and return false
      return false;
    }
  }

  /// Skip onboarding
  Future<bool> skipOnboarding() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      final response = await _dio.post(
        '${ApiConfig.baseUrl}/api/onboarding/skip',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        state = const AsyncValue.data(OnboardingStatus.completed);
        return true;
      }
      return false;
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
      return false;
    }
  }

  /// Reset onboarding to allow user to go through it again
  Future<bool> resetOnboarding() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) {
        print('🔄 ONBOARDING: No access token found for reset');
        return false;
      }

      print('🔄 ONBOARDING: Calling reset endpoint...');
      final response = await _dio.post(
        '${ApiConfig.baseUrl}/api/onboarding/reset',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      print('🔄 ONBOARDING: Reset response: ${response.statusCode}');
      if (response.statusCode == 200) {
        print('🔄 ONBOARDING: Reset successful, updating state to notStarted');
        state = const AsyncValue.data(OnboardingStatus.notStarted);
        return true;
      }
      print('🔄 ONBOARDING: Reset failed with status: ${response.statusCode}');
      return false;
    } catch (e) {
      print('🔄 ONBOARDING: Reset error: $e');
      // Don't set error state immediately - try to recover
      print('🔄 ONBOARDING: Attempting to recover by checking current status');
      await checkOnboardingStatus();
      return false;
    }
  }

  /// Get assistant profile data
  Future<Map<String, dynamic>?> getAssistantProfile(String profileId) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return null;

      final response = await _dio.get(
        '${ApiConfig.baseUrl}/api/assistant_profiles/$profileId',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Failed to get assistant profile: $e');
      return null;
    }
  }

  /// Get temp data from onboarding state
  Future<Map<String, dynamic>?> getTempData() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) {
        print('🔄 GET_TEMP_DATA: No access token found');
        return null;
      }

      print('🔄 GET_TEMP_DATA: Making request to ${ApiConfig.baseUrl}/api/onboarding/state');
      
      final response = await _dio.get(
        '${ApiConfig.baseUrl}/api/onboarding/state',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      print('🔄 GET_TEMP_DATA: Response status: ${response.statusCode}');
      print('🔄 GET_TEMP_DATA: Response data: ${response.data}');

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final tempData = data['temp_data'] as Map<String, dynamic>?;
        print('🔄 GET_TEMP_DATA: Extracted temp_data: $tempData');
        return tempData;
      }
      return null;
    } catch (e) {
      print('Failed to get temp data: $e');
      return null;
    }
  }

  /// Reset onboarding status (for development/testing)
  void reset() {
    state = const AsyncValue.data(OnboardingStatus.unknown);
    _onboardingState = null;
    _lastStepUpdate = null;
    _stepUpdateTimer?.cancel();
    _stepUpdateTimer = null;
  }
  
  @override
  void dispose() {
    _stepUpdateTimer?.cancel();
    super.dispose();
  }
}

/// Provider for onboarding status
final onboardingProvider = StateNotifierProvider<OnboardingNotifier, AsyncValue<OnboardingStatus>>((ref) {
  return OnboardingNotifier();
});

/// Provider to get onboarding completion status as a boolean
final isOnboardingCompletedProvider = Provider<bool>((ref) {
  final onboardingStatus = ref.watch(onboardingProvider);
  return onboardingStatus.when(
    data: (status) => status == OnboardingStatus.completed,
    loading: () => false,
    error: (_, __) => false,
  );
});