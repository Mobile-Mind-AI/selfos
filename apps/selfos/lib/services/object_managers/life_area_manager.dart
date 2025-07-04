/// Life Area Manager for offline-first operations
/// 
/// This manager handles all operations for life areas including:
/// - Creating and updating life areas with optimistic updates
/// - Custom life area management
/// - Priority and weighting system
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';
import '../sync/sync_manager.dart';

/// Life Area Manager for all life area operations
class LifeAreaManager {
  static LifeAreaManager? _instance;
  LifeAreaManager._();

  static LifeAreaManager get instance {
    _instance ??= LifeAreaManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  final SyncManager _syncManager = SyncManager.instance;
  static const String _tableName = LifeAreaSchema.tableName;

  /// Create new life area with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    required String name,
    String icon = 'category',
    String color = '#6366f1',
    String? description,
    List<String>? keywords,
    double weight = 1.0,
    int priorityOrder = 0,
    bool isCustom = true,
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final lifeArea = {
      'id': id,
      'user_id': userId,
      'name': name,
      'icon': icon,
      'color': color,
      'description': description,
      'keywords': keywords != null ? json.encode(keywords) : null,
      'weight': weight,
      'priority_order': priorityOrder,
      'is_custom': isCustom ? 1 : 0,
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first (optimistic update)
    await _db.insert(_tableName, lifeArea);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: id,
        objectType: LifeAreaSchema.objectType,
        operation: SyncOperationType.create,
        data: {
          'name': name,
          'icon': icon,
          'color': color,
          'description': description,
          'keywords': keywords,
          'weight': weight,
          'priority_order': priorityOrder,
          'is_custom': isCustom,
        },
        version: 1,
        priority: SyncPriority.normal,
      ),
    );

    print('✅ Created life area: $name ($id)');
    return lifeArea;
  }

  /// Update life area with optimistic update
  Future<Map<String, dynamic>> update(
    String lifeAreaId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(lifeAreaId);
    if (existing == null) {
      throw Exception('Life area not found: $lifeAreaId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Handle keywords encoding
    if (updateData['keywords'] is List) {
      updateData['keywords'] = json.encode(updateData['keywords']);
    }

    // Handle boolean conversion
    if (updateData['is_custom'] is bool) {
      updateData['is_custom'] = updateData['is_custom'] ? 1 : 0;
    }

    // Save locally first
    await _db.update(_tableName, updateData, lifeAreaId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: lifeAreaId,
        objectType: LifeAreaSchema.objectType,
        operation: SyncOperationType.update,
        data: updates,
        version: updateData['local_version'],
        priority: SyncPriority.normal,
      ),
    );

    final updated = await getById(lifeAreaId);
    print('✅ Updated life area: $lifeAreaId');
    return updated!;
  }

  /// Update life area priority order
  Future<Map<String, dynamic>> updatePriority(
    String lifeAreaId,
    int newPriorityOrder,
  ) async {
    return await update(lifeAreaId, {'priority_order': newPriorityOrder});
  }

  /// Update life area weight
  Future<Map<String, dynamic>> updateWeight(
    String lifeAreaId,
    double newWeight,
  ) async {
    return await update(lifeAreaId, {'weight': newWeight.clamp(0.0, 10.0)});
  }

  /// Delete life area (soft delete)
  Future<void> delete(String lifeAreaId) async {
    await _db.softDelete(_tableName, lifeAreaId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: lifeAreaId,
        objectType: LifeAreaSchema.objectType,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('🗑️ Deleted life area: $lifeAreaId');
  }

  /// Get life area by ID
  Future<Map<String, dynamic>?> getById(String lifeAreaId) async {
    final record = await _db.getById(_tableName, lifeAreaId);
    if (record == null) return null;

    // Parse keywords and boolean fields
    final decoded = Map<String, dynamic>.from(record);
    if (record['keywords'] != null && record['keywords'].toString().isNotEmpty) {
      try {
        decoded['keywords'] = json.decode(record['keywords']) as List<String>;
      } catch (e) {
        decoded['keywords'] = <String>[];
      }
    } else {
      decoded['keywords'] = <String>[];
    }
    
    decoded['is_custom'] = record['is_custom'] == 1;

    return decoded;
  }

  /// Get all life areas for user
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.getByUserId(_tableName, userId);
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      if (record['keywords'] != null && record['keywords'].toString().isNotEmpty) {
        try {
          decoded['keywords'] = json.decode(record['keywords']) as List<String>;
        } catch (e) {
          decoded['keywords'] = <String>[];
        }
      } else {
        decoded['keywords'] = <String>[];
      }
      decoded['is_custom'] = record['is_custom'] == 1;
      return decoded;
    }).toList();
  }

  /// Get life areas ordered by priority
  Future<List<Map<String, dynamic>>> getOrderedByPriority(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'priority_order ASC, name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Get custom life areas only
  Future<List<Map<String, dynamic>>> getCustomLifeAreas(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_custom = ?',
      whereArgs: [userId, 1],
      orderBy: 'priority_order ASC, name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Get default life areas only
  Future<List<Map<String, dynamic>>> getDefaultLifeAreas(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_custom = ?',
      whereArgs: [userId, 0],
      orderBy: 'priority_order ASC, name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Search life areas by name
  Future<List<Map<String, dynamic>>> searchByName(String query, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND name LIKE ?',
      whereArgs: [userId, '%$query%'],
      orderBy: 'name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Get life areas by color
  Future<List<Map<String, dynamic>>> getByColor(String color, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND color = ?',
      whereArgs: [userId, color],
      orderBy: 'name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Get life areas with high weight
  Future<List<Map<String, dynamic>>> getHighPriorityAreas(String userId, {double minWeight = 5.0}) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND weight >= ?',
      whereArgs: [userId, minWeight],
      orderBy: 'weight DESC, priority_order ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Reorder life areas by updating priority order
  Future<void> reorderLifeAreas(List<String> lifeAreaIds) async {
    for (int i = 0; i < lifeAreaIds.length; i++) {
      await updatePriority(lifeAreaIds[i], i);
    }
    print('✅ Reordered ${lifeAreaIds.length} life areas');
  }

  /// Mark life area as synced
  Future<void> markSynced(String lifeAreaId, int serverVersion) async {
    await _db.markClean(_tableName, lifeAreaId, serverVersion);
    print('✅ Marked life area as synced: $lifeAreaId (v$serverVersion)');
  }

  /// Mark life area as having conflicts
  Future<void> markConflicted(String lifeAreaId) async {
    await _db.markConflict(_tableName, lifeAreaId);
    print('⚠️ Marked life area as conflicted: $lifeAreaId');
  }

  /// Get life areas by sync status
  Future<List<Map<String, dynamic>>> getBySyncStatus(SyncStatus status) async {
    final records = await _db.query(
      _tableName,
      where: 'sync_status = ?',
      whereArgs: [status.name],
    );
    return _parseLifeAreaRecords(records);
  }

  /// Parse life area records with JSON and boolean conversion
  List<Map<String, dynamic>> _parseLifeAreaRecords(List<Map<String, dynamic>> records) {
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      if (record['keywords'] != null && record['keywords'].toString().isNotEmpty) {
        try {
          decoded['keywords'] = json.decode(record['keywords']) as List<String>;
        } catch (e) {
          decoded['keywords'] = <String>[];
        }
      } else {
        decoded['keywords'] = <String>[];
      }
      decoded['is_custom'] = record['is_custom'] == 1;
      return decoded;
    }).toList();
  }
}