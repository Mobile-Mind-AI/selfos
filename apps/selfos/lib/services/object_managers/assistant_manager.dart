/// Assistant Profile Manager for offline-first operations
/// 
/// This manager handles all operations for assistant profiles including:
/// - Creating and updating assistants with optimistic updates
/// - Personality configuration changes with smart batching
/// - Permission management and sharing
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';
import '../sync/sync_manager.dart';

/// Assistant Manager for all assistant profile operations
class AssistantManager {
  static AssistantManager? _instance;
  AssistantManager._();

  static AssistantManager get instance {
    _instance ??= AssistantManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  final SyncManager _syncManager = SyncManager.instance;
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
    Map<String, dynamic>? style,
    double dialogueTemperature = 0.8,
    double intentTemperature = 0.3,
    String? customInstructions,
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final assistant = {
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
      'style': json.encode(style ?? _getDefaultPersonalityStyle()),
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
    await _db.insert(_tableName, assistant);

    // Queue for sync with high priority
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
          'style': style ?? _getDefaultPersonalityStyle(),
          'dialogue_temperature': dialogueTemperature,
          'intent_temperature': intentTemperature,
          'custom_instructions': customInstructions,
        },
        version: 1,
        priority: SyncPriority.high, // Assistant creation is high priority
      ),
    );

    // Trigger immediate sync for high priority operations
    _syncManager.processSyncQueue().catchError((e) {
      print('⚠️ Background sync failed: $e');
    });

    print('✅ Created assistant: $name ($id)');
    return assistant;
  }

  /// Update assistant profile with optimistic update
  Future<Map<String, dynamic>> update(
    String assistantId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(assistantId);
    if (existing == null) {
      throw Exception('Assistant not found: $assistantId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Convert boolean fields to integers for SQLite
    if (updateData['requires_confirmation'] is bool) {
      updateData['requires_confirmation'] = updateData['requires_confirmation'] ? 1 : 0;
    }
    if (updateData['is_default'] is bool) {
      updateData['is_default'] = updateData['is_default'] ? 1 : 0;
    }
    if (updateData['is_public'] is bool) {
      updateData['is_public'] = updateData['is_public'] ? 1 : 0;
    }

    // Encode style if it's a Map
    if (updateData['style'] is Map) {
      updateData['style'] = json.encode(updateData['style']);
    }

    // Save locally first
    await _db.update(_tableName, updateData, assistantId);

    // Queue for sync (lower priority for most updates)
    final priority = updates.containsKey('name') || updates.containsKey('is_default')
        ? SyncPriority.normal
        : SyncPriority.low;

    await _syncQueue.enqueue(
      SyncOperationHelper.createAssistantOperation(
        objectId: assistantId,
        operation: SyncOperationType.update,
        data: updates, // Send original updates to API
        version: updateData['local_version'],
        priority: priority,
      ),
    );

    final updated = await getById(assistantId);
    print('✅ Updated assistant: $assistantId');
    return updated!;
  }

  /// Update personality style with smart batching
  Future<Map<String, dynamic>> updatePersonality(
    String assistantId,
    Map<String, dynamic> personalityChanges,
  ) async {
    final existing = await getById(assistantId);
    if (existing == null) {
      throw Exception('Assistant not found: $assistantId');
    }

    // Merge personality changes
    final currentStyle = json.decode(existing['style'] ?? '{}');
    final newStyle = Map<String, dynamic>.from(currentStyle);
    newStyle.addAll(personalityChanges);

    return await update(assistantId, {'style': newStyle});
  }

  /// Delete assistant (soft delete)
  Future<void> delete(String assistantId) async {
    await _db.softDelete(_tableName, assistantId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createAssistantOperation(
        objectId: assistantId,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('🗑️ Deleted assistant: $assistantId');
  }

  /// Get assistant by ID
  Future<Map<String, dynamic>?> getById(String assistantId) async {
    final record = await _db.getById(_tableName, assistantId);
    if (record == null) return null;

    // Decode JSON fields and convert SQLite integers to booleans
    final decoded = Map<String, dynamic>.from(record);
    decoded['style'] = json.decode(record['style'] ?? '{}');
    decoded['requires_confirmation'] = (record['requires_confirmation'] as int) == 1;
    decoded['is_default'] = (record['is_default'] as int) == 1;
    decoded['is_public'] = (record['is_public'] as int) == 1;

    return decoded;
  }

  /// Get all assistants for user
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.getByUserId(_tableName, userId);
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['style'] = json.decode(record['style'] ?? '{}');
      decoded['requires_confirmation'] = (record['requires_confirmation'] as int) == 1;
      decoded['is_default'] = (record['is_default'] as int) == 1;
      decoded['is_public'] = (record['is_public'] as int) == 1;
      return decoded;
    }).toList();
  }

  /// Get default assistant for user
  Future<Map<String, dynamic>?> getDefaultAssistant(String userId) async {
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
    decoded['requires_confirmation'] = (record['requires_confirmation'] as int) == 1;
    decoded['is_default'] = true;
    decoded['is_public'] = (record['is_public'] as int) == 1;

    return decoded;
  }

  /// Set assistant as default (only one can be default)
  Future<void> setAsDefault(String assistantId) async {
    final assistant = await getById(assistantId);
    if (assistant == null) {
      throw Exception('Assistant not found: $assistantId');
    }

    await _db.transaction((txn) async {
      // Remove default from all other assistants
      await txn.update(
        _tableName,
        {'is_default': 0, 'sync_status': 'dirty'},
        where: 'user_id = ? AND id != ?',
        whereArgs: [assistant['user_id'], assistantId],
      );

      // Set this assistant as default
      await txn.update(
        _tableName,
        {'is_default': 1, 'sync_status': 'dirty'},
        where: 'id = ?',
        whereArgs: [assistantId],
      );
    });

    // Queue sync for the change
    await _syncQueue.enqueue(
      SyncOperationHelper.createAssistantOperation(
        objectId: assistantId,
        operation: SyncOperationType.update,
        data: {'is_default': true},
        version: (assistant['local_version'] as int) + 1,
        priority: SyncPriority.normal,
      ),
    );

    print('⭐ Set assistant as default: $assistantId');
  }

  /// Mark assistant as synced
  Future<void> markSynced(String assistantId, int serverVersion) async {
    await _db.markClean(_tableName, assistantId, serverVersion);
    print('✅ Marked assistant as synced: $assistantId (v$serverVersion)');
  }

  /// Mark assistant as having conflicts
  Future<void> markConflicted(String assistantId) async {
    await _db.markConflict(_tableName, assistantId);
    print('⚠️ Marked assistant as conflicted: $assistantId');
  }

  /// Get assistants by sync status
  Future<List<Map<String, dynamic>>> getBySyncStatus(SyncStatus status) async {
    final records = await _db.query(
      _tableName,
      where: 'sync_status = ?',
      whereArgs: [status.name],
    );
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['style'] = json.decode(record['style'] ?? '{}');
      decoded['requires_confirmation'] = (record['requires_confirmation'] as int) == 1;
      decoded['is_default'] = (record['is_default'] as int) == 1;
      decoded['is_public'] = (record['is_public'] as int) == 1;
      return decoded;
    }).toList();
  }

  /// Search assistants by name
  Future<List<Map<String, dynamic>>> searchByName(String query, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND name LIKE ?',
      whereArgs: [userId, '%$query%'],
      orderBy: 'name ASC',
    );
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['style'] = json.decode(record['style'] ?? '{}');
      decoded['requires_confirmation'] = (record['requires_confirmation'] as int) == 1;
      decoded['is_default'] = (record['is_default'] as int) == 1;
      decoded['is_public'] = (record['is_public'] as int) == 1;
      return decoded;
    }).toList();
  }

  /// Get default personality style
  Map<String, dynamic> _getDefaultPersonalityStyle() {
    return {
      'formality': 50,      // 0 = very formal, 100 = extremely casual
      'directness': 50,     // 0 = very indirect, 100 = extremely direct
      'humor': 30,          // 0 = serious, 100 = humorous
      'empathy': 70,        // 0 = cold, 100 = warm and emotional
      'motivation': 60,     // 0 = passive, 100 = high-energy motivator
    };
  }

  /// Validate personality style values
  bool isValidPersonalityStyle(Map<String, dynamic> style) {
    final requiredKeys = ['formality', 'directness', 'humor', 'empathy', 'motivation'];
    
    for (final key in requiredKeys) {
      if (!style.containsKey(key)) return false;
      
      final value = style[key];
      if (value is! num || value < 0 || value > 100) return false;
    }
    
    return true;
  }
}