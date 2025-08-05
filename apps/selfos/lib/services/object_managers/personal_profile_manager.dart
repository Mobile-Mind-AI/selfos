/// Personal Profile Manager for offline-first operations
/// 
/// This manager handles all operations for personal profiles including:
/// - Creating and updating user personal information
/// - Managing interests, challenges, and aspirations
/// - Preference management with smart batching
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../config/api_config.dart';
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

  /// Create personal profile with specific ID (for syncing from backend)
  Future<Map<String, dynamic>> createWithId({
    required String profileId,
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
    final now = DateTime.now();
    
    final profile = {
      'id': profileId,
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
      'version': 1,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first
    await _db.insert(_tableName, profile);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createPersonalProfileOperation(
        objectId: profileId,
        operation: SyncOperationType.update, // Use update since it exists on backend
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

    print('✅ Created personal profile with specific ID: $profileId for user: $userId');
    return profile;
  }

  /// Create new personal profile with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    String? preferredName,
    String? avatarId,
    String? currentSituation,
    String? lifeStory,
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
    Map<String, double> lifeAreaImportance = const {},
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
      'preferences': json.encode({
        ...preferences,
        'life_area_importance': lifeAreaImportance, // Store importance within preferences
      }),
      'custom_answers': json.encode({
        ...customAnswers,
        'life_story': lifeStory, // Store life story within custom answers
      }),
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
    print('🔍 PROFILE MANAGER: Updating profile $profileId with data: $updates');
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
    
    // Handle preferences specially - ensure we don't include the dedicated column fields
    if (updateData['preferences'] is Map) {
      // Remove any preference fields that have dedicated columns
      final prefsToEncode = Map<String, dynamic>.from(updateData['preferences']);
      prefsToEncode.remove('work_style');
      prefsToEncode.remove('communication_frequency');
      prefsToEncode.remove('goal_approach');
      prefsToEncode.remove('motivation_style');
      updateData['preferences'] = json.encode(prefsToEncode);
    }
    
    if (updateData['custom_answers'] is Map) {
      updateData['custom_answers'] = json.encode(updateData['custom_answers']);
    }
    if (updateData['selected_life_areas'] is List) {
      updateData['selected_life_areas'] = json.encode(updateData['selected_life_areas']);
    }

    // Save locally first
    await _db.update(_tableName, updateData, profileId);

    // Queue for sync - ensure we send the correct data structure
    final syncData = Map<String, dynamic>.from(updates);
    print('🔍 PROFILE MANAGER: Preparing sync data: $syncData');
    
    // If preferences exist and contain dedicated column fields, extract them
    if (syncData['preferences'] is Map) {
      final prefs = Map<String, dynamic>.from(syncData['preferences']);
      
      // Extract fields that have dedicated columns
      if (prefs.containsKey('work_style')) {
        syncData['work_style'] = prefs['work_style'];
        prefs.remove('work_style');
      }
      if (prefs.containsKey('communication_frequency')) {
        syncData['communication_frequency'] = prefs['communication_frequency'];
        prefs.remove('communication_frequency');
      }
      if (prefs.containsKey('goal_approach')) {
        syncData['goal_approach'] = prefs['goal_approach'];
        prefs.remove('goal_approach');
      }
      if (prefs.containsKey('motivation_style')) {
        syncData['motivation_style'] = prefs['motivation_style'];
        prefs.remove('motivation_style');
      }
      
      // Update preferences with remaining fields only
      syncData['preferences'] = prefs;
    }
    
    print('🔍 PROFILE MANAGER: Final sync data being enqueued: $syncData');
    await _syncQueue.enqueue(
      SyncOperationHelper.createPersonalProfileOperation(
        objectId: profileId,
        operation: SyncOperationType.update,
        data: syncData,
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
  
  /// Fetch personal profile from backend
  Future<Map<String, dynamic>?> fetchFromBackend(String userId) async {
    try {
      print('📥 Fetching personal profile from backend...');
      
      // Get auth token
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token_access');
      if (token == null) {
        print('⚠️ No auth token available');
        return null;
      }
      
      // Fetch from backend
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/personal-config/profile'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Create profile locally with backend ID
        await _createProfileFromBackend(data);
        
        print('✅ Fetched personal profile from backend');
        
        // Return the local profile
        return await getByUserId(userId);
      } else if (response.statusCode == 404) {
        print('📝 No personal profile found on backend');
        return null;
      } else {
        print('⚠️ Failed to fetch personal profile: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('❌ Error fetching personal profile: $e');
      return null;
    }
  }
  
  /// Create profile from backend data
  Future<void> _createProfileFromBackend(Map<String, dynamic> backendData) async {
    final now = DateTime.now();
    
    await createWithId(
      profileId: backendData['id'].toString(),
      userId: backendData['user_id'],
      preferredName: backendData['preferred_name'],
      avatarId: backendData['avatar_id'],
      currentSituation: backendData['current_situation'],
      interests: List<String>.from(backendData['interests'] ?? []),
      challenges: List<String>.from(backendData['challenges'] ?? []),
      aspirations: List<String>.from(backendData['aspirations'] ?? []),
      motivation: backendData['motivation'],
      workStyle: backendData['work_style'],
      communicationFrequency: backendData['communication_frequency'],
      goalApproach: backendData['goal_approach'],
      motivationStyle: backendData['motivation_style'],
      preferences: backendData['preferences'] ?? {},
      customAnswers: backendData['custom_answers'] ?? {},
      selectedLifeAreas: List<String>.from(backendData['selected_life_areas'] ?? []),
    );
  }
}