/// Project Manager for offline-first operations
/// 
/// This manager handles all operations for projects including:
/// - Creating and updating projects with optimistic updates
/// - Progress tracking and status management
/// - Life area associations
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';
import '../sync/sync_manager.dart';

/// Project Manager for all project operations
class ProjectManager {
  static ProjectManager? _instance;
  ProjectManager._();

  static ProjectManager get instance {
    _instance ??= ProjectManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  final SyncManager _syncManager = SyncManager.instance;
  static const String _tableName = ProjectSchema.tableName;

  /// Create new project with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    required String title,
    String? description,
    String status = 'active',
    double progress = 0.0,
    String? lifeAreaId,
    DateTime? startDate,
    DateTime? targetDate,
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final project = {
      'id': id,
      'user_id': userId,
      'title': title,
      'description': description,
      'status': status,
      'progress': progress,
      'life_area_id': lifeAreaId,
      'start_date': startDate?.toIso8601String(),
      'target_date': targetDate?.toIso8601String(),
      'completed_date': null,
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first (optimistic update)
    await _db.insert(_tableName, project);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: id,
        objectType: ProjectSchema.objectType,
        operation: SyncOperationType.create,
        data: {
          'title': title,
          'description': description,
          'status': status,
          'progress': progress,
          'life_area_id': lifeAreaId,
          'start_date': startDate?.toIso8601String(),
          'target_date': targetDate?.toIso8601String(),
        },
        version: 1,
        priority: SyncPriority.normal,
      ),
    );

    print('✅ Created project: $title ($id)');
    return project;
  }

  /// Update project with optimistic update
  Future<Map<String, dynamic>> update(
    String projectId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(projectId);
    if (existing == null) {
      throw Exception('Project not found: $projectId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Handle date conversions
    if (updateData['start_date'] is DateTime) {
      updateData['start_date'] = (updateData['start_date'] as DateTime).toIso8601String();
    }
    if (updateData['target_date'] is DateTime) {
      updateData['target_date'] = (updateData['target_date'] as DateTime).toIso8601String();
    }
    if (updateData['completed_date'] is DateTime) {
      updateData['completed_date'] = (updateData['completed_date'] as DateTime).toIso8601String();
    }

    // Save locally first
    await _db.update(_tableName, updateData, projectId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: projectId,
        objectType: ProjectSchema.objectType,
        operation: SyncOperationType.update,
        data: updates,
        version: updateData['local_version'],
        priority: SyncPriority.normal,
      ),
    );

    final updated = await getById(projectId);
    print('✅ Updated project: $projectId');
    return updated!;
  }

  /// Update project progress
  Future<Map<String, dynamic>> updateProgress(
    String projectId,
    double progress,
  ) async {
    // Automatically update status based on progress
    final updates = <String, dynamic>{
      'progress': progress.clamp(0.0, 100.0),
    };

    if (progress >= 100.0) {
      updates['status'] = 'completed';
      updates['completed_date'] = DateTime.now().toIso8601String();
    } else if (progress > 0 && await getStatus(projectId) == 'completed') {
      // Reopen if progress reduced from 100%
      updates['status'] = 'active';
      updates['completed_date'] = null;
    }

    return await update(projectId, updates);
  }

  /// Get project status
  Future<String?> getStatus(String projectId) async {
    final project = await getById(projectId);
    return project?['status'];
  }

  /// Delete project (soft delete)
  Future<void> delete(String projectId) async {
    await _db.softDelete(_tableName, projectId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: projectId,
        objectType: ProjectSchema.objectType,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('🗑️ Deleted project: $projectId');
  }

  /// Get project by ID
  Future<Map<String, dynamic>?> getById(String projectId) async {
    final record = await _db.getById(_tableName, projectId);
    if (record == null) return null;

    // Parse dates
    final decoded = Map<String, dynamic>.from(record);
    if (record['start_date'] != null) {
      decoded['start_date'] = DateTime.parse(record['start_date']);
    }
    if (record['target_date'] != null) {
      decoded['target_date'] = DateTime.parse(record['target_date']);
    }
    if (record['completed_date'] != null) {
      decoded['completed_date'] = DateTime.parse(record['completed_date']);
    }

    return decoded;
  }

  /// Get all projects for user
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.getByUserId(_tableName, userId);
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      if (record['start_date'] != null) {
        decoded['start_date'] = DateTime.parse(record['start_date']);
      }
      if (record['target_date'] != null) {
        decoded['target_date'] = DateTime.parse(record['target_date']);
      }
      if (record['completed_date'] != null) {
        decoded['completed_date'] = DateTime.parse(record['completed_date']);
      }
      return decoded;
    }).toList();
  }

  /// Get projects by life area
  Future<List<Map<String, dynamic>>> getByLifeArea(String lifeAreaId) async {
    final records = await _db.query(
      _tableName,
      where: 'life_area_id = ?',
      whereArgs: [lifeAreaId],
      orderBy: 'created_at DESC',
    );
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      if (record['start_date'] != null) {
        decoded['start_date'] = DateTime.parse(record['start_date']);
      }
      if (record['target_date'] != null) {
        decoded['target_date'] = DateTime.parse(record['target_date']);
      }
      if (record['completed_date'] != null) {
        decoded['completed_date'] = DateTime.parse(record['completed_date']);
      }
      return decoded;
    }).toList();
  }

  /// Get active projects
  Future<List<Map<String, dynamic>>> getActiveProjects(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND status = ?',
      whereArgs: [userId, 'active'],
      orderBy: 'updated_at DESC',
    );
    return records;
  }

  /// Get completed projects
  Future<List<Map<String, dynamic>>> getCompletedProjects(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND status = ?',
      whereArgs: [userId, 'completed'],
      orderBy: 'completed_date DESC',
    );
    return records;
  }

  /// Mark project as synced
  Future<void> markSynced(String projectId, int serverVersion) async {
    await _db.markClean(_tableName, projectId, serverVersion);
    print('✅ Marked project as synced: $projectId (v$serverVersion)');
  }

  /// Mark project as having conflicts
  Future<void> markConflicted(String projectId) async {
    await _db.markConflict(_tableName, projectId);
    print('⚠️ Marked project as conflicted: $projectId');
  }

  /// Get projects by sync status
  Future<List<Map<String, dynamic>>> getBySyncStatus(SyncStatus status) async {
    final records = await _db.query(
      _tableName,
      where: 'sync_status = ?',
      whereArgs: [status.name],
    );
    return records;
  }

  /// Search projects by title
  Future<List<Map<String, dynamic>>> searchByTitle(String query, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND title LIKE ?',
      whereArgs: [userId, '%$query%'],
      orderBy: 'title ASC',
    );
    return records;
  }
}