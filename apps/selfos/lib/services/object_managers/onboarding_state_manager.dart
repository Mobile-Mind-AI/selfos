/// Onboarding State Manager for offline-first operations
/// 
/// This manager handles all operations for onboarding state including:
/// - Tracking onboarding progress and completion
/// - Managing temporary form data during onboarding
/// - Storing references to created entities (assistant, goal, task)
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../config/api_config.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';

/// Onboarding State Manager for all onboarding operations
class OnboardingStateManager {
  static OnboardingStateManager? _instance;
  OnboardingStateManager._();

  static OnboardingStateManager get instance {
    _instance ??= OnboardingStateManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  static const String _tableName = OnboardingStateSchema.tableName;

  /// Create or update onboarding state
  Future<Map<String, dynamic>> createOrUpdate({
    required String userId,
    required int currentStep,
    required List<int> completedSteps,
    bool onboardingCompleted = false,
    String? assistantProfileId,
    String? firstGoalId,
    String? firstTaskId,
    Map<String, dynamic>? tempData,
    bool skipIntro = false,
    String? themePreference,
    String flowVersion = 'v2',
  }) async {
    // Check if state already exists
    final existing = await getByUserId(userId);
    
    if (existing != null) {
      // Update existing state
      return await update(existing['id'], {
        'current_step': currentStep,
        'completed_steps': json.encode(completedSteps),
        'onboarding_completed': onboardingCompleted ? 1 : 0,
        'assistant_profile_id': assistantProfileId,
        'first_goal_id': firstGoalId,
        'first_task_id': firstTaskId,
        'temp_data': tempData != null ? json.encode(tempData) : null,
        'skip_intro': skipIntro ? 1 : 0,
        'theme_preference': themePreference,
        'flow_version': flowVersion,
        'last_activity': DateTime.now().toIso8601String(),
        if (onboardingCompleted) 'completed_at': DateTime.now().toIso8601String(),
      });
    } else {
      // Create new state
      return await create(
        userId: userId,
        currentStep: currentStep,
        completedSteps: completedSteps,
        onboardingCompleted: onboardingCompleted,
        assistantProfileId: assistantProfileId,
        firstGoalId: firstGoalId,
        firstTaskId: firstTaskId,
        tempData: tempData,
        skipIntro: skipIntro,
        themePreference: themePreference,
        flowVersion: flowVersion,
      );
    }
  }

  /// Create new onboarding state
  Future<Map<String, dynamic>> create({
    required String userId,
    required int currentStep,
    required List<int> completedSteps,
    bool onboardingCompleted = false,
    String? assistantProfileId,
    String? firstGoalId,
    String? firstTaskId,
    Map<String, dynamic>? tempData,
    bool skipIntro = false,
    String? themePreference,
    String flowVersion = 'v2',
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final state = {
      'id': id,
      'user_id': userId,
      'current_step': currentStep,
      'completed_steps': json.encode(completedSteps),
      'onboarding_completed': onboardingCompleted ? 1 : 0,
      'assistant_profile_id': assistantProfileId,
      'first_goal_id': firstGoalId,
      'first_task_id': firstTaskId,
      'temp_data': tempData != null ? json.encode(tempData) : null,
      'skip_intro': skipIntro ? 1 : 0,
      'theme_preference': themePreference,
      'flow_version': flowVersion,
      'started_at': now.toIso8601String(),
      'completed_at': onboardingCompleted ? now.toIso8601String() : null,
      'last_activity': now.toIso8601String(),
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    await _db.insert(_tableName, state);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: id,
        objectType: OnboardingStateSchema.objectType,
        operation: SyncOperationType.create,
        data: {
          'current_step': currentStep,
          'completed_steps': completedSteps,
          'onboarding_completed': onboardingCompleted,
          'assistant_profile_id': assistantProfileId,
          'first_goal_id': firstGoalId,
          'first_task_id': firstTaskId,
          'temp_data': tempData,
          'skip_intro': skipIntro,
          'theme_preference': themePreference,
          'flow_version': flowVersion,
        },
        version: 1,
        priority: SyncPriority.normal,
      ),
    );

    print('✅ Created onboarding state for user: $userId');
    return state;
  }

  /// Update onboarding state
  Future<Map<String, dynamic>> update(String stateId, Map<String, dynamic> updates) async {
    final existing = await getById(stateId);
    if (existing == null) {
      throw Exception('Onboarding state not found: $stateId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Handle JSON encoding for complex fields
    if (updateData['completed_steps'] is List) {
      updateData['completed_steps'] = json.encode(updateData['completed_steps']);
    }
    if (updateData['temp_data'] is Map) {
      updateData['temp_data'] = json.encode(updateData['temp_data']);
    }

    // Handle boolean conversion
    if (updateData['onboarding_completed'] is bool) {
      updateData['onboarding_completed'] = updateData['onboarding_completed'] ? 1 : 0;
    }
    if (updateData['skip_intro'] is bool) {
      updateData['skip_intro'] = updateData['skip_intro'] ? 1 : 0;
    }

    await _db.update(_tableName, updateData, stateId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: stateId,
        objectType: OnboardingStateSchema.objectType,
        operation: SyncOperationType.update,
        data: updates,
        version: updateData['local_version'],
        priority: SyncPriority.normal,
      ),
    );

    final updated = await getById(stateId);
    print('✅ Updated onboarding state: $stateId');
    return updated!;
  }

  /// Get onboarding state by ID
  Future<Map<String, dynamic>?> getById(String stateId) async {
    final record = await _db.getById(_tableName, stateId);
    if (record == null) return null;

    return _parseOnboardingState(record);
  }

  /// Get onboarding state by user ID
  Future<Map<String, dynamic>?> getByUserId(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ?',
      whereArgs: [userId],
      limit: 1,
    );

    if (records.isEmpty) return null;
    return _parseOnboardingState(records.first);
  }

  /// Parse onboarding state record
  Map<String, dynamic> _parseOnboardingState(Map<String, dynamic> record) {
    final decoded = Map<String, dynamic>.from(record);
    
    // Parse JSON fields
    if (record['completed_steps'] != null) {
      try {
        decoded['completed_steps'] = json.decode(record['completed_steps']) as List<dynamic>;
      } catch (e) {
        decoded['completed_steps'] = [];
      }
    } else {
      decoded['completed_steps'] = [];
    }

    if (record['temp_data'] != null) {
      try {
        decoded['temp_data'] = json.decode(record['temp_data']) as Map<String, dynamic>;
      } catch (e) {
        decoded['temp_data'] = {};
      }
    }

    // Convert integers to booleans
    decoded['onboarding_completed'] = record['onboarding_completed'] == 1;
    decoded['skip_intro'] = record['skip_intro'] == 1;

    return decoded;
  }

  /// Mark state as synced
  Future<void> markSynced(String stateId, int serverVersion) async {
    await _db.markClean(_tableName, stateId, serverVersion);
    print('✅ Marked onboarding state as synced: $stateId (v$serverVersion)');
  }

  /// Mark state as having conflicts
  Future<void> markConflicted(String stateId) async {
    await _db.markConflict(_tableName, stateId);
    print('⚠️ Marked onboarding state as conflicted: $stateId');
  }
  
  /// Fetch onboarding state from backend
  Future<Map<String, dynamic>?> fetchFromBackend(String userId) async {
    try {
      print('📥 Fetching onboarding state from backend...');
      
      // Get auth token
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token_access');
      if (token == null) {
        print('⚠️ No auth token available');
        return null;
      }
      
      // Fetch from backend
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/onboarding/state'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Create state locally with backend data
        await _createStateFromBackend(data);
        
        print('✅ Fetched onboarding state from backend');
        
        // Return the local state
        return await getByUserId(userId);
      } else if (response.statusCode == 404) {
        print('📝 No onboarding state found on backend');
        return null;
      } else {
        print('⚠️ Failed to fetch onboarding state: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('❌ Error fetching onboarding state: $e');
      return null;
    }
  }
  
  /// Create state from backend data
  Future<void> _createStateFromBackend(Map<String, dynamic> backendData) async {
    final now = DateTime.now();
    
    final state = {
      'id': backendData['id'].toString(),
      'user_id': backendData['user_id'],
      'current_step': backendData['current_step'] ?? 1,
      'completed_steps': json.encode(backendData['completed_steps'] ?? []),
      'onboarding_completed': backendData['onboarding_completed'] == true ? 1 : 0,
      'assistant_profile_id': backendData['assistant_profile_id'],
      'first_goal_id': backendData['first_goal_id'],
      'first_task_id': backendData['first_task_id'],
      'temp_data': backendData['temp_data'] != null ? json.encode(backendData['temp_data']) : null,
      'skip_intro': backendData['skip_intro'] == true ? 1 : 0,
      'theme_preference': backendData['theme_preference'],
      'flow_version': backendData['flow_version'] ?? 'v2',
      'started_at': backendData['started_at'] ?? now.toIso8601String(),
      'completed_at': backendData['completed_at'],
      'last_activity': backendData['last_activity'] ?? now.toIso8601String(),
      'version': backendData['version'] ?? 1,
      'local_version': backendData['version'] ?? 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'clean', // Already synced from backend
      'created_at': backendData['created_at'] ?? now.toIso8601String(),
      'updated_at': backendData['updated_at'] ?? now.toIso8601String(),
    };
    
    try {
      await _db.insert(_tableName, state);
    } catch (e) {
      // Ignore duplicate key errors
      if (!e.toString().contains('UNIQUE constraint failed')) {
        rethrow;
      }
    }
  }
}