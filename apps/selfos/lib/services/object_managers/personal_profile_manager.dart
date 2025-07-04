/// Personal Profile Manager for offline-first operations
/// 
/// This manager handles all operations for personal profiles including:
/// - Creating and updating user personal information
/// - Managing interests, challenges, and aspirations
/// - Preference management with smart batching
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';

/// Personal Profile Manager for all profile operations
class PersonalProfileManager {
  static PersonalProfileManager? _instance;
  PersonalProfileManager._();

  static PersonalProfileManager get instance {
    _instance ??= PersonalProfileManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  static const String _tableName = PersonalProfileSchema.tableName;

  /// Create new personal profile with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    String? preferredName,
    String? avatarId,
    String? currentSituation,
    List<String> interests = const [],
    List<String> challenges = const [],
    List<String> aspirations = const [],
    String? motivation,
    String? workStyle,
    String? communicationFrequency,
    String? goalApproach,
    String? motivationStyle,
    Map<String, dynamic> preferences = const {},
    Map<String, dynamic> customAnswers = const {},
    List<String> selectedLifeAreas = const [],
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final profile = {
      'id': id,
      'user_id': userId,
      'preferred_name': preferredName,
      'avatar_id': avatarId,
      'current_situation': currentSituation,
      'interests': json.encode(interests),
      'challenges': json.encode(challenges),
      'aspirations': json.encode(aspirations),
      'motivation': motivation,
      'work_style': workStyle,
      'communication_frequency': communicationFrequency,
      'goal_approach': goalApproach,
      'motivation_style': motivationStyle,
      'preferences': json.encode(preferences),
      'custom_answers': json.encode(customAnswers),
      'selected_life_areas': json.encode(selectedLifeAreas),
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first (optimistic update)
    await _db.insert(_tableName, profile);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createPersonalProfileOperation(
        objectId: id,
        operation: SyncOperationType.create,
        data: {
          'preferred_name': preferredName,
          'avatar_id': avatarId,
          'current_situation': currentSituation,
          'interests': interests,
          'challenges': challenges,
          'aspirations': aspirations,
          'motivation': motivation,
          'work_style': workStyle,
          'communication_frequency': communicationFrequency,
          'goal_approach': goalApproach,
          'motivation_style': motivationStyle,
          'preferences': preferences,
          'custom_answers': customAnswers,
          'selected_life_areas': selectedLifeAreas,
        },
        version: 1,
        priority: SyncPriority.high,
      ),
    );

    print('✅ Created personal profile for user: $userId ($id)');
    return profile;
  }

  /// Update personal profile with optimistic update
  Future<Map<String, dynamic>> update(
    String profileId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(profileId);
    if (existing == null) {
      throw Exception('Personal profile not found: $profileId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Encode lists and maps for SQLite storage
    if (updateData['interests'] is List) {
      updateData['interests'] = json.encode(updateData['interests']);
    }
    if (updateData['challenges'] is List) {
      updateData['challenges'] = json.encode(updateData['challenges']);
    }
    if (updateData['aspirations'] is List) {
      updateData['aspirations'] = json.encode(updateData['aspirations']);
    }
    if (updateData['preferences'] is Map) {
      updateData['preferences'] = json.encode(updateData['preferences']);
    }
    if (updateData['custom_answers'] is Map) {
      updateData['custom_answers'] = json.encode(updateData['custom_answers']);
    }
    if (updateData['selected_life_areas'] is List) {
      updateData['selected_life_areas'] = json.encode(updateData['selected_life_areas']);
    }

    // Save locally first
    await _db.update(_tableName, updateData, profileId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createPersonalProfileOperation(
        objectId: profileId,
        operation: SyncOperationType.update,
        data: updates, // Send original updates (not encoded) to API
        version: updateData['local_version'],
        priority: SyncPriority.normal,
      ),
    );

    final updated = await getById(profileId);
    print('✅ Updated personal profile: $profileId');
    return updated!;
  }

  /// Update interests
  Future<Map<String, dynamic>> updateInterests(
    String profileId,
    List<String> interests,
  ) async {
    return await update(profileId, {'interests': interests});
  }

  /// Update preferences with merging
  Future<Map<String, dynamic>> updatePreferences(
    String profileId,
    Map<String, dynamic> newPreferences,
  ) async {
    final existing = await getById(profileId);
    if (existing == null) {
      throw Exception('Personal profile not found: $profileId');
    }

    // Merge preferences
    final currentPrefs = existing['preferences'] as Map<String, dynamic>;
    final mergedPreferences = Map<String, dynamic>.from(currentPrefs);
    mergedPreferences.addAll(newPreferences);

    return await update(profileId, {'preferences': mergedPreferences});
  }

  /// Get profile by ID
  Future<Map<String, dynamic>?> getById(String profileId) async {
    final record = await _db.getById(_tableName, profileId);
    if (record == null) return null;

    // Decode JSON fields
    final decoded = Map<String, dynamic>.from(record);
    decoded['interests'] = json.decode(record['interests'] ?? '[]');
    decoded['challenges'] = json.decode(record['challenges'] ?? '[]');
    decoded['aspirations'] = json.decode(record['aspirations'] ?? '[]');
    decoded['preferences'] = json.decode(record['preferences'] ?? '{}');
    decoded['custom_answers'] = json.decode(record['custom_answers'] ?? '{}');
    decoded['selected_life_areas'] = json.decode(record['selected_life_areas'] ?? '[]');

    return decoded;
  }

  /// Get profile by user ID
  Future<Map<String, dynamic>?> getByUserId(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ?',
      whereArgs: [userId],
      limit: 1,
    );

    if (records.isEmpty) return null;

    final record = records.first;
    final decoded = Map<String, dynamic>.from(record);
    decoded['interests'] = json.decode(record['interests'] ?? '[]');
    decoded['challenges'] = json.decode(record['challenges'] ?? '[]');
    decoded['aspirations'] = json.decode(record['aspirations'] ?? '[]');
    decoded['preferences'] = json.decode(record['preferences'] ?? '{}');
    decoded['custom_answers'] = json.decode(record['custom_answers'] ?? '{}');
    decoded['selected_life_areas'] = json.decode(record['selected_life_areas'] ?? '[]');

    return decoded;
  }

  /// Delete personal profile (soft delete)
  Future<void> delete(String profileId) async {
    await _db.softDelete(_tableName, profileId);

    await _syncQueue.enqueue(
      SyncOperationHelper.createPersonalProfileOperation(
        objectId: profileId,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('🗑️ Deleted personal profile: $profileId');
  }

  /// Mark profile as synced
  Future<void> markSynced(String profileId, int serverVersion) async {
    await _db.markClean(_tableName, profileId, serverVersion);
    print('✅ Marked personal profile as synced: $profileId (v$serverVersion)');
  }

  /// Mark profile as having conflicts
  Future<void> markConflicted(String profileId) async {
    await _db.markConflict(_tableName, profileId);
    print('⚠️ Marked personal profile as conflicted: $profileId');
  }
}