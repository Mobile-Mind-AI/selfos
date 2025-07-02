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
      // On error, assume onboarding not completed
      state = AsyncValue.error(e, StackTrace.current);
      return false;
    }
  }

  /// Update onboarding step
  Future<bool> updateOnboardingStep(String step, Map<String, dynamic> data) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

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
        // Don't refresh status immediately to avoid router conflicts
        // The status will be checked when completing onboarding
        return true;
      }
      return false;
    } catch (e) {
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
      state = AsyncValue.error(e, StackTrace.current);
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

  /// Reset onboarding status (for development/testing)
  void reset() {
    state = const AsyncValue.data(OnboardingStatus.unknown);
    _onboardingState = null;
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