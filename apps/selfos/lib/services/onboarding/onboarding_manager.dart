/// Onboarding Manager for simplified offline-first onboarding
/// 
/// This manager handles the complete onboarding flow with:
/// - Single transaction for all onboarding data
/// - Optimistic local storage first
/// - Background sync with intelligent batching
/// - Elimination of redundant API calls

import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';
import '../sync/sync_manager.dart';
import '../object_managers/assistant_manager.dart';
import '../object_managers/personal_profile_manager.dart';
import '../object_managers/life_area_manager.dart';
import '../object_managers/goal_manager.dart';
import '../object_managers/task_manager.dart';

/// Onboarding data collection model
class OnboardingData {
  final String assistantName;
  final String? assistantDescription;
  final String? avatarUrl;
  final Map<String, dynamic> personalityStyle;
  final String language;
  final String aiModel;
  final bool requiresConfirmation;
  
  // Personal story data
  final String? currentSituation;
  final List<String> interests;
  final List<String> challenges;
  final List<String> aspirations;
  final String? motivation;
  
  // Preferences
  final String? workStyle;
  final String? communicationFrequency;
  final String? goalApproach;
  final String? motivationStyle;
  final Map<String, dynamic> customPreferences;
  
  // Life areas
  final List<String> selectedLifeAreaIds;
  final List<Map<String, dynamic>> customLifeAreas;
  
  // Optional first goal
  final String? firstGoalTitle;
  final String? firstGoalDescription;
  final String? firstGoalLifeAreaId;
  
  // UI preferences
  final String? themePreference;
  final bool skipIntro;

  OnboardingData({
    required this.assistantName,
    this.assistantDescription,
    this.avatarUrl,
    required this.personalityStyle,
    this.language = 'en',
    this.aiModel = 'gpt-3.5-turbo',
    this.requiresConfirmation = true,
    this.currentSituation,
    this.interests = const [],
    this.challenges = const [],
    this.aspirations = const [],
    this.motivation,
    this.workStyle,
    this.communicationFrequency,
    this.goalApproach,
    this.motivationStyle,
    this.customPreferences = const {},
    this.selectedLifeAreaIds = const [],
    this.customLifeAreas = const [],
    this.firstGoalTitle,
    this.firstGoalDescription,
    this.firstGoalLifeAreaId,
    this.themePreference,
    this.skipIntro = false,
  });
}

/// Onboarding result model
class OnboardingResult {
  final bool success;
  final String assistantId;
  final String personalProfileId;
  final String onboardingStateId;
  final List<String> lifeAreaIds;
  final String? firstGoalId;
  final String? firstTaskId;
  final String message;
  final List<String> warnings;

  OnboardingResult({
    required this.success,
    required this.assistantId,
    required this.personalProfileId,
    required this.onboardingStateId,
    this.lifeAreaIds = const [],
    this.firstGoalId,
    this.firstTaskId,
    this.message = 'Onboarding completed successfully',
    this.warnings = const [],
  });
}

/// Main onboarding manager
class OnboardingManager {
  static OnboardingManager? _instance;
  OnboardingManager._();

  static OnboardingManager get instance {
    _instance ??= OnboardingManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  final SyncManager _syncManager = SyncManager.instance;
  final AssistantManager _assistantManager = AssistantManager.instance;
  final PersonalProfileManager _profileManager = PersonalProfileManager.instance;
  final LifeAreaManager _lifeAreaManager = LifeAreaManager.instance;
  final GoalManager _goalManager = GoalManager.instance;
  final TaskManager _taskManager = TaskManager.instance;

  /// Complete entire onboarding in single transaction
  Future<OnboardingResult> completeOnboarding({
    required String userId,
    required OnboardingData data,
  }) async {
    print('🚀 Starting complete onboarding for user: $userId');

    try {
      // Execute all operations in a single transaction
      final result = await _db.transaction<OnboardingResult>((txn) async {
        final now = DateTime.now();
        final assistantId = const Uuid().v4();
        final personalProfileId = const Uuid().v4();
        final onboardingStateId = const Uuid().v4();

        // 1. Create Assistant Profile
        final assistant = {
          'id': assistantId,
          'user_id': userId,
          'name': data.assistantName,
          'description': data.assistantDescription,
          'avatar_url': data.avatarUrl,
          'ai_model': data.aiModel,
          'language': data.language,
          'requires_confirmation': data.requiresConfirmation ? 1 : 0,
          'is_default': 1, // First assistant is default
          'is_public': 0,
          'style': json.encode(data.personalityStyle),
          'dialogue_temperature': 0.8,
          'intent_temperature': 0.3,
          'custom_instructions': null,
          'version': 0,
          'local_version': 1,
          'last_modified': now.toIso8601String(),
          'sync_status': 'dirty',
          'created_at': now.toIso8601String(),
          'updated_at': now.toIso8601String(),
        };

        await txn.insert(AssistantProfileSchema.tableName, assistant);

        // 2. Create Personal Profile (authoritative for life areas)
        final personalProfile = {
          'id': personalProfileId,
          'user_id': userId,
          'preferred_name': null,
          'avatar_id': null,
          'current_situation': data.currentSituation,
          'interests': json.encode(data.interests),
          'challenges': json.encode(data.challenges),
          'aspirations': json.encode(data.aspirations),
          'motivation': data.motivation,
          'work_style': data.workStyle,
          'communication_frequency': data.communicationFrequency,
          'goal_approach': data.goalApproach,
          'motivation_style': data.motivationStyle,
          'preferences': json.encode(data.customPreferences),
          'custom_answers': json.encode({}),
          'selected_life_areas': json.encode(data.selectedLifeAreaIds),
          'version': 0,
          'local_version': 1,
          'last_modified': now.toIso8601String(),
          'sync_status': 'dirty',
          'created_at': now.toIso8601String(),
          'updated_at': now.toIso8601String(),
        };

        await txn.insert(PersonalProfileSchema.tableName, personalProfile);

        // 3. Create Custom Life Areas if any
        final createdLifeAreaIds = <String>[];
        for (final lifeAreaData in data.customLifeAreas) {
          final lifeAreaId = const Uuid().v4();
          createdLifeAreaIds.add(lifeAreaId);

          await txn.insert(LifeAreaSchema.tableName, {
            'id': lifeAreaId,
            'user_id': userId,
            'name': lifeAreaData['name'],
            'icon': lifeAreaData['icon'] ?? 'category',
            'color': lifeAreaData['color'] ?? '#6366f1',
            'description': lifeAreaData['description'],
            'keywords': json.encode(lifeAreaData['keywords'] ?? []),
            'weight': 1.0,
            'priority_order': 0,
            'is_custom': 1,
            'version': 0,
            'local_version': 1,
            'last_modified': now.toIso8601String(),
            'sync_status': 'dirty',
            'created_at': now.toIso8601String(),
            'updated_at': now.toIso8601String(),
          });
        }

        // 4. Create First Goal if provided
        String? firstGoalId;
        String? firstTaskId;
        
        if (data.firstGoalTitle?.isNotEmpty == true) {
          firstGoalId = const Uuid().v4();
          
          await txn.insert(GoalSchema.tableName, {
            'id': firstGoalId,
            'user_id': userId,
            'title': data.firstGoalTitle!,
            'description': data.firstGoalDescription,
            'status': 'active',
            'progress': 0.0,
            'life_area_id': data.firstGoalLifeAreaId ?? 
                (data.selectedLifeAreaIds.isNotEmpty ? data.selectedLifeAreaIds.first : null),
            'project_id': null,
            'target_date': null,
            'media_attachments': json.encode([]),
            'version': 0,
            'local_version': 1,
            'last_modified': now.toIso8601String(),
            'sync_status': 'dirty',
            'created_at': now.toIso8601String(),
            'updated_at': now.toIso8601String(),
          });

          // Create a starter task for the goal
          firstTaskId = const Uuid().v4();
          await txn.insert(TaskSchema.tableName, {
            'id': firstTaskId,
            'user_id': userId,
            'title': 'Plan approach for ${data.firstGoalTitle}',
            'description': 'Think about the first steps needed to achieve this goal',
            'status': 'pending',
            'progress': 0.0,
            'goal_id': firstGoalId,
            'project_id': null,
            'life_area_id': data.firstGoalLifeAreaId,
            'due_date': null,
            'completed_date': null,
            'duration': 30, // 30 minutes
            'dependencies': json.encode([]),
            'version': 0,
            'local_version': 1,
            'last_modified': now.toIso8601String(),
            'sync_status': 'dirty',
            'created_at': now.toIso8601String(),
            'updated_at': now.toIso8601String(),
          });
        }

        // 5. Create Onboarding State (simplified, no duplication)
        final onboardingState = {
          'id': onboardingStateId,
          'user_id': userId,
          'current_step': 6, // Completed
          'completed_steps': json.encode([1, 2, 3, 4, 5, 6]),
          'onboarding_completed': 1,
          'assistant_profile_id': assistantId,
          'first_goal_id': firstGoalId,
          'first_task_id': firstTaskId,
          'temp_data': json.encode({}), // Clear temp data since onboarding is complete
          'skip_intro': data.skipIntro ? 1 : 0,
          'theme_preference': data.themePreference,
          'flow_version': 'v2',
          'started_at': now.toIso8601String(),
          'completed_at': now.toIso8601String(),
          'last_activity': now.toIso8601String(),
          'version': 0,
          'local_version': 1,
          'sync_status': 'dirty',
          'created_at': now.toIso8601String(),
          'updated_at': now.toIso8601String(),
        };

        await txn.insert(OnboardingStateSchema.tableName, onboardingState);

        return OnboardingResult(
          success: true,
          assistantId: assistantId,
          personalProfileId: personalProfileId,
          onboardingStateId: onboardingStateId,
          lifeAreaIds: [...data.selectedLifeAreaIds, ...createdLifeAreaIds],
          firstGoalId: firstGoalId,
          firstTaskId: firstTaskId,
          message: 'Onboarding completed successfully! Welcome to SelfOS.',
        );
      });

      // Queue all objects for background sync (single batch operation)
      await _queueOnboardingSyncOperations(result, data);

      print('✅ Onboarding completed successfully!');
      print('   Assistant: ${result.assistantId}');
      print('   Profile: ${result.personalProfileId}');
      print('   Life Areas: ${result.lifeAreaIds.length}');
      print('   Goal: ${result.firstGoalId ?? 'None'}');

      return result;

    } catch (e) {
      print('❌ Onboarding failed: $e');
      rethrow;
    }
  }

  /// Queue all onboarding objects for sync in a single batch
  Future<void> _queueOnboardingSyncOperations(
    OnboardingResult result,
    OnboardingData data,
  ) async {
    // Create batch sync operations
    final operations = <SyncOperation>[];

    // Assistant profile
    operations.add(SyncOperationHelper.createGenericOperation(
      objectId: result.assistantId,
      objectType: AssistantProfileSchema.objectType,
      operation: SyncOperationType.create,
      data: {
        'name': data.assistantName,
        'description': data.assistantDescription,
        'avatar_url': data.avatarUrl,
        'ai_model': data.aiModel,
        'language': data.language,
        'requires_confirmation': data.requiresConfirmation,
        'is_default': true,
        'style': data.personalityStyle,
      },
      version: 1,
      priority: SyncPriority.critical, // Onboarding is critical
    ));

    // Personal profile
    operations.add(SyncOperationHelper.createGenericOperation(
      objectId: result.personalProfileId,
      objectType: PersonalProfileSchema.objectType,
      operation: SyncOperationType.create,
      data: {
        'current_situation': data.currentSituation,
        'interests': data.interests,
        'challenges': data.challenges,
        'aspirations': data.aspirations,
        'motivation': data.motivation,
        'work_style': data.workStyle,
        'communication_frequency': data.communicationFrequency,
        'goal_approach': data.goalApproach,
        'motivation_style': data.motivationStyle,
        'preferences': data.customPreferences,
        'selected_life_areas': data.selectedLifeAreaIds,
      },
      version: 1,
      priority: SyncPriority.critical,
    ));

    // Onboarding state
    operations.add(SyncOperationHelper.createGenericOperation(
      objectId: result.onboardingStateId,
      objectType: OnboardingStateSchema.objectType,
      operation: SyncOperationType.create,
      data: {
        'current_step': 6,
        'completed_steps': [1, 2, 3, 4, 5, 6],
        'onboarding_completed': true,
        'assistant_profile_id': result.assistantId,
        'first_goal_id': result.firstGoalId,
        'first_task_id': result.firstTaskId,
        'skip_intro': data.skipIntro,
        'theme_preference': data.themePreference,
      },
      version: 1,
      priority: SyncPriority.critical,
    ));

    // Queue all operations
    for (final operation in operations) {
      await _syncQueue.enqueue(operation);
    }

    print('📤 Queued ${operations.length} onboarding sync operations');

    // Trigger immediate sync for critical onboarding operations
    _syncManager.processSyncQueue().catchError((e) {
      print('⚠️ Background onboarding sync failed: $e');
      // Continue - user experience isn't blocked by sync failures
    });
  }

  /// Get onboarding state for user
  Future<Map<String, dynamic>?> getOnboardingState(String userId) async {
    final records = await _db.query(
      OnboardingStateSchema.tableName,
      where: 'user_id = ?',
      whereArgs: [userId],
      limit: 1,
    );

    if (records.isEmpty) return null;

    final record = records.first;
    final decoded = Map<String, dynamic>.from(record);
    decoded['completed_steps'] = json.decode(record['completed_steps'] ?? '[]');
    decoded['temp_data'] = json.decode(record['temp_data'] ?? '{}');
    decoded['onboarding_completed'] = (record['onboarding_completed'] as int) == 1;
    decoded['skip_intro'] = (record['skip_intro'] as int) == 1;

    return decoded;
  }

  /// Check if user has completed onboarding
  Future<bool> isOnboardingCompleted(String userId) async {
    final state = await getOnboardingState(userId);
    return state?['onboarding_completed'] ?? false;
  }

  /// Get onboarding progress summary
  Future<Map<String, dynamic>> getOnboardingProgress(String userId) async {
    final state = await getOnboardingState(userId);
    final syncStats = await _syncQueue.getStats();

    return {
      'completed': state?['onboarding_completed'] ?? false,
      'currentStep': state?['current_step'] ?? 1,
      'completedSteps': state?['completed_steps'] ?? [],
      'assistantCreated': state?['assistant_profile_id'] != null,
      'profileCreated': state != null,
      'syncProgress': {
        'totalOperations': syncStats.totalOperations,
        'pendingOperations': syncStats.pendingOperations,
        'isOnline': syncStats.isOnline,
        'isProcessing': syncStats.isProcessing,
      },
      'lastActivity': state?['last_activity'],
    };
  }
}