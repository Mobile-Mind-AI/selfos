/// Goal Manager for offline-first operations
/// 
/// This manager handles all operations for goals including:
/// - Creating and updating goals with progress tracking
/// - Managing goal status and lifecycle
/// - Linking goals to life areas and projects
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';

/// Goal Manager for all goal operations
class GoalManager {
  static GoalManager? _instance;
  GoalManager._();

  static GoalManager get instance {
    _instance ??= GoalManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  static const String _tableName = GoalSchema.tableName;

  /// Create new goal with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    required String title,
    String? description,
    String status = 'active',
    double progress = 0.0,
    String? lifeAreaId,
    String? projectId,
    String? targetDate,
    List<String> mediaAttachments = const [],
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final goal = {
      'id': id,
      'user_id': userId,
      'title': title,
      'description': description,
      'status': status,
      'progress': progress,
      'life_area_id': lifeAreaId,
      'project_id': projectId,
      'target_date': targetDate,
      'media_attachments': json.encode(mediaAttachments),
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first (optimistic update)
    await _db.insert(_tableName, goal);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: id,
        objectType: GoalSchema.objectType,
        operation: SyncOperationType.create,
        data: {
          'title': title,
          'description': description,
          'status': status,
          'progress': progress,
          'life_area_id': lifeAreaId,
          'project_id': projectId,
          'target_date': targetDate,
          'media_attachments': mediaAttachments,
        },
        version: 1,
        priority: SyncPriority.high, // Goal creation is high priority
      ),
    );

    print('✅ Created goal: $title ($id)');
    return goal;
  }

  /// Update goal with optimistic update
  Future<Map<String, dynamic>> update(
    String goalId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(goalId);
    if (existing == null) {
      throw Exception('Goal not found: $goalId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Encode media attachments if provided
    if (updateData['media_attachments'] is List) {
      updateData['media_attachments'] = json.encode(updateData['media_attachments']);
    }

    // Save locally first
    await _db.update(_tableName, updateData, goalId);

    // Queue for sync - progress updates are normal priority, status changes are high
    final priority = updates.containsKey('status') ? SyncPriority.high : SyncPriority.normal;

    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: goalId,
        objectType: GoalSchema.objectType,
        operation: SyncOperationType.update,
        data: updates, // Send original updates to API
        version: updateData['local_version'],
        priority: priority,
      ),
    );

    final updated = await getById(goalId);
    print('✅ Updated goal: $goalId');
    return updated!;
  }

  /// Update goal progress
  Future<Map<String, dynamic>> updateProgress(String goalId, double progress) async {
    return await update(goalId, {'progress': progress.clamp(0.0, 100.0)});
  }

  /// Update goal status
  Future<Map<String, dynamic>> updateStatus(String goalId, String status) async {
    return await update(goalId, {'status': status});
  }

  /// Complete goal
  Future<Map<String, dynamic>> completeGoal(String goalId) async {
    return await update(goalId, {
      'status': 'completed',
      'progress': 100.0,
    });
  }

  /// Get goal by ID
  Future<Map<String, dynamic>?> getById(String goalId) async {
    final record = await _db.getById(_tableName, goalId);
    if (record == null) return null;

    // Decode JSON fields
    final decoded = Map<String, dynamic>.from(record);
    decoded['media_attachments'] = json.decode(record['media_attachments'] ?? '[]');

    return decoded;
  }

  /// Get all goals for user
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'created_at DESC',
    );

    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['media_attachments'] = json.decode(record['media_attachments'] ?? '[]');
      return decoded;
    }).toList();
  }

  /// Get goals by life area
  Future<List<Map<String, dynamic>>> getByLifeArea(String lifeAreaId) async {
    final records = await _db.query(
      _tableName,
      where: 'life_area_id = ?',
      whereArgs: [lifeAreaId],
      orderBy: 'created_at DESC',
    );

    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['media_attachments'] = json.decode(record['media_attachments'] ?? '[]');
      return decoded;
    }).toList();
  }

  /// Get goals by status
  Future<List<Map<String, dynamic>>> getByStatus(String userId, String status) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND status = ?',
      whereArgs: [userId, status],
      orderBy: 'created_at DESC',
    );

    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['media_attachments'] = json.decode(record['media_attachments'] ?? '[]');
      return decoded;
    }).toList();
  }

  /// Delete goal (soft delete)
  Future<void> delete(String goalId) async {
    await _db.softDelete(_tableName, goalId);

    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: goalId,
        objectType: GoalSchema.objectType,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('🗑️ Deleted goal: $goalId');
  }

  /// Mark goal as synced
  Future<void> markSynced(String goalId, int serverVersion) async {
    await _db.markClean(_tableName, goalId, serverVersion);
    print('✅ Marked goal as synced: $goalId (v$serverVersion)');
  }

  /// Mark goal as having conflicts
  Future<void> markConflicted(String goalId) async {
    await _db.markConflict(_tableName, goalId);
    print('⚠️ Marked goal as conflicted: $goalId');
  }
}