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
  OnboardingNotifier() : super(const AsyncValue.data(OnboardingStatus.unknown)) {
    _startLeakyBucket();
  }

  final Dio _dio = Dio();
  OnboardingState? _onboardingState;
  
  
  // Leaky bucket rate limiting
  static const int _bucketCapacity = 3; // Max 3 requests
  static const Duration _refillInterval = Duration(seconds: 2); // Refill 1 token every 2 seconds
  int _bucketTokens = 3;
  Timer? _refillTimer;
  
  // Queue for pending saves
  final List<_PendingSave> _saveQueue = [];
  Timer? _processQueueTimer;

  /// Get the current onboarding state data
  OnboardingState? get onboardingState => _onboardingState;

  /// Check if user has completed onboarding
  Future<bool> checkOnboardingStatus() async {
    try {
      // Don't show loading state - we have offline-first data
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

  /// Start the leaky bucket timer
  void _startLeakyBucket() {
    _refillTimer = Timer.periodic(_refillInterval, (timer) {
      if (_bucketTokens < _bucketCapacity) {
        _bucketTokens++;
        print('🪣 LEAKY_BUCKET: Refilled token, now have $_bucketTokens tokens');
        
        // Process queue if we have tokens and pending saves
        if (_saveQueue.isNotEmpty) {
          _processQueue();
        }
      }
    });
  }

  /// Add save to queue and process if possible
  Future<bool> updateOnboardingStep(String step, Map<String, dynamic> data) async {
    // Remove any existing save for the same step (latest request replaces old one)
    final removedCount = _saveQueue.length;
    _saveQueue.removeWhere((save) => save.step == step);
    final actualRemovedCount = removedCount - _saveQueue.length;
    
    if (actualRemovedCount > 0) {
      print('🔄 REPLACE_QUEUE: Removed $actualRemovedCount existing pending save(s) for $step');
    }
    
    // Add new save to queue
    _saveQueue.add(_PendingSave(step, data, DateTime.now()));
    
    print('🪣 LEAKY_BUCKET: Added $step to queue (${_saveQueue.length} items)');
    
    // Try to process immediately
    _processQueue();
    
    return true;
  }

  /// Process the save queue using leaky bucket
  void _processQueue() {
    if (_saveQueue.isEmpty || _bucketTokens <= 0) {
      return;
    }
    
    final save = _saveQueue.removeAt(0);
    _bucketTokens--;
    
    print('🪣 LEAKY_BUCKET: Processing ${save.step}, tokens remaining: $_bucketTokens');
    
    // Perform the actual save
    _performSave(save.step, save.data);
    
    // Schedule next processing if more items in queue
    if (_saveQueue.isNotEmpty && _bucketTokens > 0) {
      Future.delayed(const Duration(milliseconds: 100), () => _processQueue());
    }
  }

  /// Perform the actual API call
  Future<void> _performSave(String step, Map<String, dynamic> data) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) {
        print('🚦 ONBOARDING: No access token for $step');
        return;
      }

      print('🚦 ONBOARDING: Making API request for $step');
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
      } else {
        print('🚦 ONBOARDING: Step update failed with status ${response.statusCode} for $step');
      }
    } catch (e) {
      print('🚦 ONBOARDING: Step update error for $step: $e');
      if (e is DioException && e.response?.statusCode == 429) {
        print('🚦 ONBOARDING: Rate limited by server (429), re-queuing data');
        
        print('🔄 RETRY: Re-queuing $step');
        
        // Add data back to queue for retry (replace any duplicates)
        _saveQueue.removeWhere((save) => save.step == step); // Remove any existing
        _saveQueue.insert(0, _PendingSave(step, data, DateTime.now()));
      }
    }
  }

  /// Complete onboarding
  Future<bool> completeOnboarding() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      // First, ensure backend onboarding state exists by calling /state endpoint
      try {
        print('🎯 ONBOARDING: Ensuring backend state exists before completion');
        final stateResponse = await _dio.get(
          '${ApiConfig.baseUrl}/api/onboarding/state',
          options: Options(
            headers: {
              'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
          ),
        );
        
        if (stateResponse.statusCode == 200) {
          print('🎯 ONBOARDING: Backend state exists, proceeding with completion');
        }
      } catch (stateError) {
        print('⚠️ ONBOARDING: Could not verify backend state: $stateError');
        // Continue anyway - the /complete endpoint might handle it
      }

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
        
        // If it's a 404 because onboarding state hasn't synced yet, 
        // we should NOT just mark as completed locally - this is a real error
        if (e.response?.statusCode == 404) {
          print('❌ ONBOARDING: Backend state not found - this indicates sync failure');
          // Return false so the UI can show an error
          return false;
        }
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

  /// Get assistant profile data from the backend
  Future<Map<String, dynamic>?> getAssistantData() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) {
        print('🔄 GET_ASSISTANT_DATA: No access token found');
        return null;
      }

      print('🔄 GET_ASSISTANT_DATA: Making request to ${ApiConfig.baseUrl}/api/assistant_profiles');
      
      final response = await _dio.get(
        '${ApiConfig.baseUrl}/api/assistant_profiles',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      print('🔄 GET_ASSISTANT_DATA: Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final assistantsList = response.data as List<dynamic>;
        print('🔄 GET_ASSISTANT_DATA: Found ${assistantsList.length} assistants');
        
        if (assistantsList.isEmpty) {
          print('🔄 GET_ASSISTANT_DATA: No assistants found - this is normal for new users');
          return null;
        }
        
        // Find the default assistant, or use the first one if no default
        Map<String, dynamic>? assistantData;
        
        // First try to find one marked as default
        for (final assistant in assistantsList) {
          if (assistant['is_default'] == true) {
            assistantData = assistant as Map<String, dynamic>;
            print('🔄 GET_ASSISTANT_DATA: Found default assistant: ${assistantData['name']}');
            break;
          }
        }
        
        // If no default found, use the first one
        if (assistantData == null && assistantsList.isNotEmpty) {
          assistantData = assistantsList.first as Map<String, dynamic>;
          print('🔄 GET_ASSISTANT_DATA: No default assistant, using first: ${assistantData['name']}');
        }
        
        if (assistantData == null) {
          return null;
        }
        
        // Convert to format expected by the frontend
        final result = {
          'assistant_name': assistantData['name'],
          'avatar_url': assistantData['avatar_url'],
          'language': assistantData['language'],
          'requires_confirmation': assistantData['requires_confirmation'],
          'style': assistantData['style'],
        };
        
        print('🔄 GET_ASSISTANT_DATA: Converted result: $result');
        return result;
      }
      return null;
    } catch (e) {
      print('Failed to get assistant data: $e');
      return null;
    }
  }

  /// Get personal config data from the backend
  Future<Map<String, dynamic>?> getPersonalConfigData() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) {
        print('🔄 GET_PERSONAL_CONFIG: No access token found');
        return null;
      }

      print('🔄 GET_PERSONAL_CONFIG: Making requests to personal config endpoints');
      
      final Map<String, dynamic> result = {};
      
      // Get personal profile
      try {
        final profileResponse = await _dio.get(
          '${ApiConfig.baseUrl}/api/personal-config/profile',
          options: Options(
            headers: {
              'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
          ),
        );
        
        if (profileResponse.statusCode == 200 && profileResponse.data != null) {
          final profileData = profileResponse.data as Map<String, dynamic>;
          result['profile_id'] = profileData['id'] ?? ''; // IMPORTANT: Extract the profile ID!
          result['preferred_name'] = profileData['preferred_name'] ?? '';
          result['current_situation'] = profileData['current_situation'] ?? '';
          result['aspirations'] = profileData['aspirations'] ?? '';
          result['interests'] = profileData['interests'] ?? [];
          result['challenges'] = profileData['challenges'] ?? [];
          result['preferences'] = profileData['preferences'] ?? {};
          result['custom_answers'] = profileData['custom_answers'] ?? {};
          result['avatar_id'] = profileData['avatar_id'] ?? '';
          result['life_area_ids'] = profileData['selected_life_areas'] ?? [];
        }
      } catch (e) {
        if (e is DioException) {
          if (e.response?.statusCode == 429) {
            print('🔄 GET_PERSONAL_CONFIG: Profile request rate limited (429), skipping');
          } else if (e.response?.statusCode == 500) {
            print('🔄 GET_PERSONAL_CONFIG: Profile request server error (500) - endpoint may not exist yet');
          } else {
            print('🔄 GET_PERSONAL_CONFIG: Profile request failed: ${e.response?.statusCode} - ${e.message}');
          }
        } else {
          print('🔄 GET_PERSONAL_CONFIG: Profile request failed: $e');
        }
        // If profile endpoint fails, just continue with empty profile data
        result['profile_id'] = '';  // No profile ID if endpoint fails
        result['preferred_name'] = '';
        result['current_situation'] = '';
        result['aspirations'] = '';
        result['interests'] = [];
        result['challenges'] = [];
        result['preferences'] = {};
        result['custom_answers'] = {};
        result['avatar_id'] = '';
        result['life_area_ids'] = [];
      }
      
      // Get custom life areas from sync/delta endpoint instead of personal-config
      try {
        await Future.delayed(const Duration(milliseconds: 200)); // Small delay to avoid rate limiting
        
        // Use the sync/delta endpoint to get life areas
        // Use current timestamp to only get non-deleted items
        final currentTimestamp = DateTime.now().millisecondsSinceEpoch;
        final deltaResponse = await _dio.get(
          '${ApiConfig.baseUrl}/api/sync/delta/0?object_types=life_area',
          options: Options(
            headers: {
              'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
          ),
        );
        
        if (deltaResponse.statusCode == 200) {
          final changes = deltaResponse.data['changes'] as List;
          final customAreas = changes
              .where((change) => 
                  change['object_type'] == 'life_area' && 
                  change['data']['is_custom'] == true)
              .map((change) => change['data'])
              .toList();
          result['custom_life_areas'] = customAreas;
          print('🔄 GET_PERSONAL_CONFIG: Loaded ${customAreas.length} custom life areas from sync');
        }
      } catch (e) {
        if (e is DioException && e.response?.statusCode == 429) {
          print('🔄 GET_PERSONAL_CONFIG: Life areas request rate limited (429), using empty list');
          result['custom_life_areas'] = [];
        } else {
          print('🔄 GET_PERSONAL_CONFIG: Life areas request failed: $e');
          result['custom_life_areas'] = [];
        }
      }
      


      print('🔄 GET_PERSONAL_CONFIG: Combined result: $result');
      return result.isNotEmpty ? result : null;
    } catch (e) {
      print('Failed to get personal config data: $e');
      return null;
    }
  }


  /// Reset onboarding status (for development/testing)
  void reset() {
    state = const AsyncValue.data(OnboardingStatus.unknown);
    _onboardingState = null;
    _saveQueue.clear();
    _bucketTokens = _bucketCapacity;
  }
  
  @override
  void dispose() {
    _refillTimer?.cancel();
    _processQueueTimer?.cancel();
    super.dispose();
  }
}

/// Provider for onboarding status
final onboardingProvider = StateNotifierProvider<OnboardingNotifier, AsyncValue<OnboardingStatus>>((ref) {
  return OnboardingNotifier();
});

/// Helper class for queued save operations
class _PendingSave {
  final String step;
  final Map<String, dynamic> data;
  final DateTime timestamp;

  _PendingSave(this.step, this.data, this.timestamp);
}

/// Provider to get onboarding completion status as a boolean
final isOnboardingCompletedProvider = Provider<bool>((ref) {
  final onboardingStatus = ref.watch(onboardingProvider);
  return onboardingStatus.when(
    data: (status) => status == OnboardingStatus.completed,
    loading: () => false,
    error: (_, __) => false,
  );
});