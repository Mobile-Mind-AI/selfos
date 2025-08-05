/// Life Area Manager for offline-first operations
/// 
/// This manager handles all operations for life areas including:
/// - Creating and updating life areas with optimistic updates
/// - Custom life area management
/// - Priority and weighting system
/// - Local-first operations with background sync

import 'dart:convert';
import 'package:uuid/uuid.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';
import '../sync/sync_manager.dart' as sync;

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
  final sync.SyncManager _syncManager = sync.SyncManager.instance;
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

  /// Get all life areas for user (excluding soft-deleted)
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND deleted_at IS NULL',
      whereArgs: [userId],
      orderBy: 'created_at DESC',
    );
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
      where: 'user_id = ? AND deleted_at IS NULL',
      whereArgs: [userId],
      orderBy: 'priority_order ASC, name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Get all life areas (system defaults + user custom)
  Future<List<Map<String, dynamic>>> getAllLifeAreas(String userId) async {
    // First check if we have any life areas locally
    final records = await _db.query(
      _tableName,
      where: '(user_id = ? OR user_id = ?) AND deleted_at IS NULL',
      whereArgs: [userId, 'system'],
      orderBy: 'is_custom ASC, priority_order ASC, name ASC',
    );
    
    // If no system life areas found locally, fetch from backend
    final systemAreas = records.where((r) => r['user_id'] == 'system').toList();
    if (systemAreas.isEmpty) {
      print('📥 No system life areas found locally, fetching from backend...');
      await _fetchAndCacheSystemLifeAreas();
      
      // Re-query after fetching
      final updatedRecords = await _db.query(
        _tableName,
        where: '(user_id = ? OR user_id = ?) AND deleted_at IS NULL',
        whereArgs: [userId, 'system'],
        orderBy: 'is_custom ASC, priority_order ASC, name ASC',
      );
      return _parseLifeAreaRecords(updatedRecords);
    }
    
    return _parseLifeAreaRecords(records);
  }
  
  /// Get custom life areas only
  Future<List<Map<String, dynamic>>> getCustomLifeAreas(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_custom = ? AND deleted_at IS NULL',
      whereArgs: [userId, 1],
      orderBy: 'priority_order ASC, name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Get default life areas only
  Future<List<Map<String, dynamic>>> getDefaultLifeAreas(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_custom = ? AND deleted_at IS NULL',
      whereArgs: [userId, 0],
      orderBy: 'priority_order ASC, name ASC',
    );
    return _parseLifeAreaRecords(records);
  }

  /// Search life areas by name
  Future<List<Map<String, dynamic>>> searchByName(String query, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND name LIKE ? AND deleted_at IS NULL',
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
  
  /// Fetch and cache system life areas from backend
  Future<void> _fetchAndCacheSystemLifeAreas() async {
    print('🔄 LIFE_AREAS: Starting fetch and cache of system life areas');
    try {
      // Get auth token
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token_access');
      if (token == null) {
        print('⚠️ LIFE_AREAS: No auth token available, using hardcoded defaults');
        await _createHardcodedDefaults();
        return;
      }
      
      print('🔄 LIFE_AREAS: Auth token found, attempting backend fetch');
      
      // Fetch from backend
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/life_areas'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      
      print('🔄 LIFE_AREAS: Backend response status: ${response.statusCode}');
      if (response.statusCode == 200) {
        final data = json.decode(response.body) as List<dynamic>;
        print('🔄 LIFE_AREAS: Received ${data.length} life areas from backend');
        
        // Save system life areas locally
        int systemAreaCount = 0;
        for (final area in data) {
          if (area['user_id'] == 'system') {
            systemAreaCount++;
            print('🔄 LIFE_AREAS: Creating system life area: ${area['name']}');
            await _createLifeAreaFromBackend(area);
          }
        }
        print('✅ LIFE_AREAS: Cached $systemAreaCount system life areas');
        
        if (systemAreaCount == 0) {
          print('⚠️ LIFE_AREAS: No system life areas found in backend response, using hardcoded defaults');
          await _createHardcodedDefaults();
        }
      } else {
        print('⚠️ LIFE_AREAS: Failed to fetch life areas: ${response.statusCode} - ${response.body}');
        await _createHardcodedDefaults();
      }
    } catch (e) {
      print('❌ Error fetching system life areas: $e');
      await _createHardcodedDefaults();
    }
  }
  
  /// Create life area from backend data
  Future<void> _createLifeAreaFromBackend(Map<String, dynamic> backendData) async {
    final now = DateTime.now();
    
    final lifeArea = {
      'id': backendData['id'].toString(),
      'user_id': backendData['user_id'],
      'name': backendData['name'],
      'icon': backendData['icon'] ?? 'category',
      'color': backendData['color'] ?? '#6366f1',
      'description': backendData['description'],
      'keywords': backendData['keywords'] != null ? json.encode(backendData['keywords']) : null,
      'weight': backendData['weight'] ?? 1.0,
      'priority_order': backendData['priority_order'] ?? 0,
      'is_custom': backendData['is_custom'] == true ? 1 : 0,
      'version': backendData['version'] ?? 1,
      'local_version': backendData['version'] ?? 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'clean', // Already synced from backend
      'created_at': backendData['created_at'] ?? now.toIso8601String(),
      'updated_at': backendData['updated_at'] ?? now.toIso8601String(),
    };
    
    try {
      await _db.insert(_tableName, lifeArea);
    } catch (e) {
      // Ignore duplicate key errors
      if (!e.toString().contains('UNIQUE constraint failed')) {
        rethrow;
      }
    }
  }
  
  /// Create hardcoded default life areas
  Future<void> _createHardcodedDefaults() async {
    final defaults = [
      {'name': 'Health & Fitness', 'icon': 'favorite', 'color': '#FF6B6B', 'priority_order': 1},
      {'name': 'Career & Work', 'icon': 'work', 'color': '#4ECDC4', 'priority_order': 2},
      {'name': 'Relationships', 'icon': 'family_restroom', 'color': '#FFE66D', 'priority_order': 3},
      {'name': 'Personal Growth', 'icon': 'school', 'color': '#A8E6CF', 'priority_order': 4},
      {'name': 'Finance', 'icon': 'attach_money', 'color': '#C7CEEA', 'priority_order': 5},
      {'name': 'Spirituality', 'icon': 'self_improvement', 'color': '#FFDAB9', 'priority_order': 6},
      {'name': 'Fun & Recreation', 'icon': 'music_note', 'color': '#B4A7D6', 'priority_order': 7},
      {'name': 'Environment', 'icon': 'home', 'color': '#D4A5A5', 'priority_order': 8},
    ];
    
    final now = DateTime.now();
    for (int i = 0; i < defaults.length; i++) {
      final area = defaults[i];
      final lifeArea = {
        'id': 'default_${i + 1}',
        'user_id': 'system',
        'name': area['name'],
        'icon': area['icon'],
        'color': area['color'],
        'description': null,
        'keywords': null,
        'weight': 1.0,
        'priority_order': area['priority_order'],
        'is_custom': 0,
        'version': 1,
        'local_version': 1,
        'last_modified': now.toIso8601String(),
        'sync_status': 'clean',
        'created_at': now.toIso8601String(),
        'updated_at': now.toIso8601String(),
      };
      
      try {
        await _db.insert(_tableName, lifeArea);
      } catch (e) {
        // Ignore duplicate key errors
        if (!e.toString().contains('UNIQUE constraint failed')) {
          rethrow;
        }
      }
    }
    print('✅ Created ${defaults.length} hardcoded default life areas');
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