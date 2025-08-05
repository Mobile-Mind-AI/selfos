/// Assistant Profile Manager for offline-first operations
/// 
/// This manager handles all operations for assistant profiles including:
/// - Creating and updating AI assistant configurations
/// - Managing assistant personality styles and instructions
/// - Temperature settings and model selection
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../config/api_config.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';

/// Assistant Profile Manager for all assistant operations
class AssistantProfileManager {
  static AssistantProfileManager? _instance;
  AssistantProfileManager._();

  static AssistantProfileManager get instance {
    _instance ??= AssistantProfileManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  static const String _tableName = AssistantProfileSchema.tableName;

  /// Create new assistant profile with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    required String name,
    String? description,
    String? avatarUrl,
    String aiModel = 'gpt-3.5-turbo',
    String language = 'en',
    bool requiresConfirmation = true,
    bool isDefault = false,
    bool isPublic = false,
    required Map<String, dynamic> style,
    double dialogueTemperature = 0.8,
    double intentTemperature = 0.3,
    String? customInstructions,
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final profile = {
      'id': id,
      'user_id': userId,
      'name': name,
      'description': description,
      'avatar_url': avatarUrl,
      'ai_model': aiModel,
      'language': language,
      'requires_confirmation': requiresConfirmation ? 1 : 0,
      'is_default': isDefault ? 1 : 0,
      'is_public': isPublic ? 1 : 0,
      'style': json.encode(style),
      'dialogue_temperature': dialogueTemperature,
      'intent_temperature': intentTemperature,
      'custom_instructions': customInstructions,
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first (optimistic update)
    try {
      await _db.insert(_tableName, profile);
      print('✅ Assistant profile saved to local database');
    } catch (e) {
      print('❌ Failed to insert assistant profile: $e');
      print('❌ Table name: $_tableName');
      print('❌ Profile data: $profile');
      rethrow;
    }

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createAssistantOperation(
        objectId: id,
        operation: SyncOperationType.create,
        data: {
          'name': name,
          'description': description,
          'avatar_url': avatarUrl,
          'ai_model': aiModel,
          'language': language,
          'requires_confirmation': requiresConfirmation,
          'is_default': isDefault,
          'is_public': isPublic,
          'style': style,
          'dialogue_temperature': dialogueTemperature,
          'intent_temperature': intentTemperature,
          'custom_instructions': customInstructions,
        },
        version: 1,
        priority: SyncPriority.high,
      ),
    );

    print('✅ Created assistant profile: $name ($id)');
    return profile;
  }

  /// Update assistant profile with optimistic update
  Future<Map<String, dynamic>> update(
    String profileId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(profileId);
    if (existing == null) {
      throw Exception('Assistant profile not found: $profileId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Encode style map for SQLite storage
    if (updateData['style'] is Map) {
      updateData['style'] = json.encode(updateData['style']);
    }

    // Convert boolean values to integers for SQLite
    if (updateData.containsKey('requires_confirmation')) {
      updateData['requires_confirmation'] = updateData['requires_confirmation'] ? 1 : 0;
    }
    if (updateData.containsKey('is_default')) {
      updateData['is_default'] = updateData['is_default'] ? 1 : 0;
    }
    if (updateData.containsKey('is_public')) {
      updateData['is_public'] = updateData['is_public'] ? 1 : 0;
    }

    // Save locally first
    await _db.update(_tableName, updateData, profileId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createAssistantOperation(
        objectId: profileId,
        operation: SyncOperationType.update,
        data: updates, // Send original updates (not encoded) to API
        version: updateData['local_version'],
        priority: SyncPriority.normal,
      ),
    );

    final updated = await getById(profileId);
    print('✅ Updated assistant profile: $profileId');
    return updated!;
  }

  /// Update assistant style
  Future<Map<String, dynamic>> updateStyle(
    String profileId,
    Map<String, dynamic> style,
  ) async {
    return await update(profileId, {'style': style});
  }

  /// Update temperature settings
  Future<Map<String, dynamic>> updateTemperatures(
    String profileId, {
    double? dialogueTemperature,
    double? intentTemperature,
  }) async {
    final updates = <String, dynamic>{};
    if (dialogueTemperature != null) {
      updates['dialogue_temperature'] = dialogueTemperature;
    }
    if (intentTemperature != null) {
      updates['intent_temperature'] = intentTemperature;
    }
    return await update(profileId, updates);
  }

  /// Set default assistant
  Future<Map<String, dynamic>> setDefault(String profileId, String userId) async {
    // First, unset any existing default for this user
    final existingDefaults = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_default = 1',
      whereArgs: [userId],
    );

    for (final existing in existingDefaults) {
      if (existing['id'] != profileId) {
        await update(existing['id'] as String, {'is_default': false});
      }
    }

    // Set new default
    return await update(profileId, {'is_default': true});
  }

  /// Get profile by ID
  Future<Map<String, dynamic>?> getById(String profileId) async {
    final record = await _db.getById(_tableName, profileId);
    if (record == null) return null;

    // Decode JSON fields and convert integers to booleans
    final decoded = Map<String, dynamic>.from(record);
    decoded['style'] = json.decode(record['style'] ?? '{}');
    decoded['requires_confirmation'] = record['requires_confirmation'] == 1;
    decoded['is_default'] = record['is_default'] == 1;
    decoded['is_public'] = record['is_public'] == 1;

    return decoded;
  }

  /// Get all profiles for a user
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'created_at DESC',
    );

    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['style'] = json.decode(record['style'] ?? '{}');
      decoded['requires_confirmation'] = record['requires_confirmation'] == 1;
      decoded['is_default'] = record['is_default'] == 1;
      decoded['is_public'] = record['is_public'] == 1;
      return decoded;
    }).toList();
  }

  /// Get default assistant for user
  Future<Map<String, dynamic>?> getDefaultForUser(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_default = 1',
      whereArgs: [userId],
      limit: 1,
    );

    if (records.isEmpty) return null;

    final record = records.first;
    final decoded = Map<String, dynamic>.from(record);
    decoded['style'] = json.decode(record['style'] ?? '{}');
    decoded['requires_confirmation'] = record['requires_confirmation'] == 1;
    decoded['is_default'] = record['is_default'] == 1;
    decoded['is_public'] = record['is_public'] == 1;

    return decoded;
  }

  /// Get public assistants
  Future<List<Map<String, dynamic>>> getPublicAssistants() async {
    final records = await _db.query(
      _tableName,
      where: 'is_public = 1',
      orderBy: 'created_at DESC',
    );

    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['style'] = json.decode(record['style'] ?? '{}');
      decoded['requires_confirmation'] = record['requires_confirmation'] == 1;
      decoded['is_default'] = record['is_default'] == 1;
      decoded['is_public'] = record['is_public'] == 1;
      return decoded;
    }).toList();
  }

  /// Delete assistant profile (soft delete)
  Future<void> delete(String profileId) async {
    await _db.softDelete(_tableName, profileId);

    await _syncQueue.enqueue(
      SyncOperationHelper.createAssistantOperation(
        objectId: profileId,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('🗑️ Deleted assistant profile: $profileId');
  }

  /// Mark profile as synced
  Future<void> markSynced(String profileId, int serverVersion) async {
    await _db.markClean(_tableName, profileId, serverVersion);
    print('✅ Marked assistant profile as synced: $profileId (v$serverVersion)');
  }

  /// Mark profile as having conflicts
  Future<void> markConflicted(String profileId) async {
    await _db.markConflict(_tableName, profileId);
    print('⚠️ Marked assistant profile as conflicted: $profileId');
  }
  
  /// Fetch assistant profiles from backend
  Future<List<Map<String, dynamic>>> fetchFromBackend(String userId) async {
    try {
      print('📥 Fetching assistant profiles from backend...');
      
      // Get auth token
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token_access');
      if (token == null) {
        print('⚠️ No auth token available');
        return [];
      }
      
      // Fetch from backend
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/assistant_profiles'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body) as List<dynamic>;
        
        // Save profiles locally
        for (final profile in data) {
          await _createProfileFromBackend(profile);
        }
        
        print('✅ Fetched ${data.length} assistant profiles from backend');
        
        // Return the local profiles
        return await getByUserId(userId);
      } else {
        print('⚠️ Failed to fetch assistant profiles: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      print('❌ Error fetching assistant profiles: $e');
      return [];
    }
  }
  
  /// Create profile from backend data
  Future<void> _createProfileFromBackend(Map<String, dynamic> backendData) async {
    final now = DateTime.now();
    
    final profile = {
      'id': backendData['id'].toString(),
      'user_id': backendData['user_id'],
      'name': backendData['name'],
      'description': backendData['description'],
      'avatar_url': backendData['avatar_url'],
      'ai_model': backendData['ai_model'] ?? 'gpt-3.5-turbo',
      'language': backendData['language'] ?? 'en',
      'requires_confirmation': backendData['requires_confirmation'] == true ? 1 : 0,
      'is_default': backendData['is_default'] == true ? 1 : 0,
      'is_public': backendData['is_public'] == true ? 1 : 0,
      'style': json.encode(backendData['style'] ?? {}),
      'dialogue_temperature': backendData['dialogue_temperature'] ?? 0.8,
      'intent_temperature': backendData['intent_temperature'] ?? 0.3,
      'custom_instructions': backendData['custom_instructions'],
      'version': backendData['version'] ?? 1,
      'local_version': backendData['version'] ?? 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'clean', // Already synced from backend
      'created_at': backendData['created_at'] ?? now.toIso8601String(),
      'updated_at': backendData['updated_at'] ?? now.toIso8601String(),
    };
    
    try {
      await _db.insert(_tableName, profile);
    } catch (e) {
      // Ignore duplicate key errors
      if (!e.toString().contains('UNIQUE constraint failed')) {
        rethrow;
      }
    }
  }
}