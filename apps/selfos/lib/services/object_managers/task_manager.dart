/// Task Manager for offline-first operations
/// 
/// This manager handles all operations for tasks including:
/// - Creating and updating tasks with optimistic updates
/// - Priority and dependency management
/// - Goal/Project/LifeArea associations
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';
import '../sync/sync_manager.dart';

/// Task Manager for all task operations
class TaskManager {
  static TaskManager? _instance;
  TaskManager._();

  static TaskManager get instance {
    _instance ??= TaskManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  final SyncManager _syncManager = SyncManager.instance;
  static const String _tableName = TaskSchema.tableName;

  /// Create new task with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    required String title,
    String? description,
    String status = 'pending',
    double progress = 0.0,
    String? goalId,
    String? projectId,
    String? lifeAreaId,
    String priority = 'medium',
    DateTime? dueDate,
    double? estimatedHours,
    String? dependsOnTaskId,
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final task = {
      'id': id,
      'user_id': userId,
      'title': title,
      'description': description,
      'status': status,
      'progress': progress,
      'goal_id': goalId,
      'project_id': projectId,
      'life_area_id': lifeAreaId,
      'priority': priority,
      'due_date': dueDate?.toIso8601String(),
      'estimated_hours': estimatedHours,
      'actual_hours': 0.0,
      'depends_on_task_id': dependsOnTaskId,
      'completed_at': null,
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first (optimistic update)
    await _db.insert(_tableName, task);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: id,
        objectType: TaskSchema.objectType,
        operation: SyncOperationType.create,
        data: {
          'title': title,
          'description': description,
          'status': status,
          'progress': progress,
          'goal_id': goalId,
          'project_id': projectId,
          'life_area_id': lifeAreaId,
          'priority': priority,
          'due_date': dueDate?.toIso8601String(),
          'estimated_hours': estimatedHours,
          'depends_on_task_id': dependsOnTaskId,
        },
        version: 1,
        priority: SyncPriority.normal,
      ),
    );

    print('✅ Created task: $title ($id)');
    return task;
  }

  /// Update task with optimistic update
  Future<Map<String, dynamic>> update(
    String taskId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(taskId);
    if (existing == null) {
      throw Exception('Task not found: $taskId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Handle date conversions
    if (updateData['due_date'] is DateTime) {
      updateData['due_date'] = (updateData['due_date'] as DateTime).toIso8601String();
    }
    if (updateData['completed_at'] is DateTime) {
      updateData['completed_at'] = (updateData['completed_at'] as DateTime).toIso8601String();
    }

    // Save locally first
    await _db.update(_tableName, updateData, taskId);

    // Queue for sync with appropriate priority
    final syncPriority = updates.containsKey('status') && updates['status'] == 'completed'
        ? SyncPriority.high  // Completed tasks sync with higher priority
        : SyncPriority.normal;

    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: taskId,
        objectType: TaskSchema.objectType,
        operation: SyncOperationType.update,
        data: updates,
        version: updateData['local_version'],
        priority: syncPriority,
      ),
    );

    final updated = await getById(taskId);
    print('✅ Updated task: $taskId');
    return updated!;
  }

  /// Update task progress
  Future<Map<String, dynamic>> updateProgress(
    String taskId,
    double progress, {
    double? actualHours,
  }) async {
    final updates = <String, dynamic>{
      'progress': progress.clamp(0.0, 100.0),
    };

    if (actualHours != null) {
      updates['actual_hours'] = actualHours;
    }

    // Auto-update status based on progress
    if (progress >= 100.0) {
      updates['status'] = 'completed';
      updates['completed_at'] = DateTime.now().toIso8601String();
    } else if (progress > 0 && await getStatus(taskId) == 'pending') {
      updates['status'] = 'in_progress';
    }

    return await update(taskId, updates);
  }

  /// Complete a task
  Future<Map<String, dynamic>> complete(String taskId, {double? actualHours}) async {
    final updates = <String, dynamic>{
      'status': 'completed',
      'progress': 100.0,
      'completed_at': DateTime.now().toIso8601String(),
    };

    if (actualHours != null) {
      updates['actual_hours'] = actualHours;
    }

    return await update(taskId, updates);
  }

  /// Get task status
  Future<String?> getStatus(String taskId) async {
    final task = await getById(taskId);
    return task?['status'];
  }

  /// Delete task (soft delete)
  Future<void> delete(String taskId) async {
    await _db.softDelete(_tableName, taskId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: taskId,
        objectType: TaskSchema.objectType,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('🗑️ Deleted task: $taskId');
  }

  /// Get task by ID
  Future<Map<String, dynamic>?> getById(String taskId) async {
    final record = await _db.getById(_tableName, taskId);
    if (record == null) return null;

    // Parse dates
    final decoded = Map<String, dynamic>.from(record);
    if (record['due_date'] != null) {
      decoded['due_date'] = DateTime.parse(record['due_date']);
    }
    if (record['completed_at'] != null) {
      decoded['completed_at'] = DateTime.parse(record['completed_at']);
    }

    return decoded;
  }

  /// Get all tasks for user
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.getByUserId(_tableName, userId);
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      if (record['due_date'] != null) {
        decoded['due_date'] = DateTime.parse(record['due_date']);
      }
      if (record['completed_at'] != null) {
        decoded['completed_at'] = DateTime.parse(record['completed_at']);
      }
      return decoded;
    }).toList();
  }

  /// Get tasks by goal
  Future<List<Map<String, dynamic>>> getByGoal(String goalId) async {
    final records = await _db.query(
      _tableName,
      where: 'goal_id = ?',
      whereArgs: [goalId],
      orderBy: 'priority DESC, created_at DESC',
    );
    return _parseTaskRecords(records);
  }

  /// Get tasks by project
  Future<List<Map<String, dynamic>>> getByProject(String projectId) async {
    final records = await _db.query(
      _tableName,
      where: 'project_id = ?',
      whereArgs: [projectId],
      orderBy: 'priority DESC, created_at DESC',
    );
    return _parseTaskRecords(records);
  }

  /// Get tasks by life area
  Future<List<Map<String, dynamic>>> getByLifeArea(String lifeAreaId) async {
    final records = await _db.query(
      _tableName,
      where: 'life_area_id = ?',
      whereArgs: [lifeAreaId],
      orderBy: 'priority DESC, created_at DESC',
    );
    return _parseTaskRecords(records);
  }

  /// Get pending tasks
  Future<List<Map<String, dynamic>>> getPendingTasks(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND status = ?',
      whereArgs: [userId, 'pending'],
      orderBy: 'priority DESC, due_date ASC',
    );
    return _parseTaskRecords(records);
  }

  /// Get tasks due soon
  Future<List<Map<String, dynamic>>> getTasksDueSoon(String userId, {int days = 7}) async {
    final future = DateTime.now().add(Duration(days: days));
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND status != ? AND due_date <= ?',
      whereArgs: [userId, 'completed', future.toIso8601String()],
      orderBy: 'due_date ASC, priority DESC',
    );
    return _parseTaskRecords(records);
  }

  /// Get overdue tasks
  Future<List<Map<String, dynamic>>> getOverdueTasks(String userId) async {
    final now = DateTime.now();
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND status != ? AND due_date < ?',
      whereArgs: [userId, 'completed', now.toIso8601String()],
      orderBy: 'due_date ASC, priority DESC',
    );
    return _parseTaskRecords(records);
  }

  /// Get dependent tasks
  Future<List<Map<String, dynamic>>> getDependentTasks(String taskId) async {
    final records = await _db.query(
      _tableName,
      where: 'depends_on_task_id = ?',
      whereArgs: [taskId],
      orderBy: 'created_at ASC',
    );
    return _parseTaskRecords(records);
  }

  /// Check if task can be started (no blocking dependencies)
  Future<bool> canStart(String taskId) async {
    final task = await getById(taskId);
    if (task == null) return false;

    final dependsOnId = task['depends_on_task_id'];
    if (dependsOnId == null) return true;

    final blockingTask = await getById(dependsOnId);
    return blockingTask == null || blockingTask['status'] == 'completed';
  }

  /// Mark task as synced
  Future<void> markSynced(String taskId, int serverVersion) async {
    await _db.markClean(_tableName, taskId, serverVersion);
    print('✅ Marked task as synced: $taskId (v$serverVersion)');
  }

  /// Mark task as having conflicts
  Future<void> markConflicted(String taskId) async {
    await _db.markConflict(_tableName, taskId);
    print('⚠️ Marked task as conflicted: $taskId');
  }

  /// Get tasks by sync status
  Future<List<Map<String, dynamic>>> getBySyncStatus(SyncStatus status) async {
    final records = await _db.query(
      _tableName,
      where: 'sync_status = ?',
      whereArgs: [status.name],
    );
    return _parseTaskRecords(records);
  }

  /// Search tasks by title
  Future<List<Map<String, dynamic>>> searchByTitle(String query, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND title LIKE ?',
      whereArgs: [userId, '%$query%'],
      orderBy: 'title ASC',
    );
    return _parseTaskRecords(records);
  }

  /// Parse task records with date conversion
  List<Map<String, dynamic>> _parseTaskRecords(List<Map<String, dynamic>> records) {
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      if (record['due_date'] != null) {
        decoded['due_date'] = DateTime.parse(record['due_date']);
      }
      if (record['completed_at'] != null) {
        decoded['completed_at'] = DateTime.parse(record['completed_at']);
      }
      return decoded;
    }).toList();
  }
}