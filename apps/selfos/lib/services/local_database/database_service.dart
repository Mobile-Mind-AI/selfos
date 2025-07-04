/// Local database service for offline-first architecture
/// 
/// This service manages SQLite database operations, including:
/// - Database initialization and migrations
/// - CRUD operations for all syncable objects
/// - Transaction management
/// - Conflict detection and resolution

import 'dart:io';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:uuid/uuid.dart';
import 'schemas.dart';

/// Main database service for local storage
class LocalDatabaseService {
  static LocalDatabaseService? _instance;
  static Database? _database;
  
  LocalDatabaseService._();
  
  static LocalDatabaseService get instance {
    _instance ??= LocalDatabaseService._();
    return _instance!;
  }
  
  /// Get database instance (lazy initialization)
  Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }
  
  /// Initialize database with all tables
  Future<Database> _initDatabase() async {
    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, DatabaseInfo.databaseName);
    
    return await openDatabase(
      path,
      version: DatabaseInfo.currentVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
      onOpen: _onOpen,
    );
  }
  
  /// Create all tables on first run
  Future<void> _onCreate(Database db, int version) async {
    print('📦 Creating local database v$version');
    
    // Create all tables
    for (final sql in DatabaseInfo.getAllCreateTableStatements()) {
      await db.execute(sql);
    }
    
    // Initialize sync metadata
    await db.insert(SyncMetadataSchema.tableName, {
      'key': 'last_sync_timestamp',
      'value': '0',
      'updated_at': DateTime.now().toIso8601String(),
    });
    
    await db.insert(SyncMetadataSchema.tableName, {
      'key': 'database_version',
      'value': version.toString(),
      'updated_at': DateTime.now().toIso8601String(),
    });
    
    print('✅ Database created successfully');
  }
  
  /// Handle database upgrades
  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    print('🔄 Upgrading database from v$oldVersion to v$newVersion');
    
    // Add migration logic here as needed
    if (oldVersion < 2) {
      // Example: Add new columns, tables, etc.
    }
  }
  
  /// Called when database is opened
  Future<void> _onOpen(Database db) async {
    print('🔓 Database opened: ${DatabaseInfo.databaseName}');
    
    // Enable foreign key constraints
    await db.execute('PRAGMA foreign_keys = ON');
    
    // Optimize SQLite performance
    await db.execute('PRAGMA journal_mode = WAL');
    await db.execute('PRAGMA synchronous = NORMAL');
    await db.execute('PRAGMA temp_store = MEMORY');
    await db.execute('PRAGMA mmap_size = 67108864'); // 64MB
  }
  
  /// Generic insert operation
  Future<int> insert(String table, Map<String, dynamic> data) async {
    final db = await database;
    
    // Add common fields
    data['created_at'] ??= DateTime.now().toIso8601String();
    data['updated_at'] = DateTime.now().toIso8601String();
    data['last_modified'] = DateTime.now().toIso8601String();
    
    try {
      final result = await db.insert(table, data);
      print('➕ Inserted into $table: ${data['id']}');
      return result;
    } catch (e) {
      print('❌ Failed to insert into $table: $e');
      rethrow;
    }
  }
  
  /// Generic update operation
  Future<int> update(String table, Map<String, dynamic> data, String id) async {
    final db = await database;
    
    // Update common fields
    data['updated_at'] = DateTime.now().toIso8601String();
    data['last_modified'] = DateTime.now().toIso8601String();
    
    try {
      final result = await db.update(
        table,
        data,
        where: 'id = ?',
        whereArgs: [id],
      );
      print('📝 Updated $table: $id');
      return result;
    } catch (e) {
      print('❌ Failed to update $table: $e');
      rethrow;
    }
  }
  
  /// Generic delete operation
  Future<int> delete(String table, String id) async {
    final db = await database;
    
    try {
      final result = await db.delete(
        table,
        where: 'id = ?',
        whereArgs: [id],
      );
      print('🗑️  Deleted from $table: $id');
      return result;
    } catch (e) {
      print('❌ Failed to delete from $table: $e');
      rethrow;
    }
  }
  
  /// Insert or update operation (upsert)
  Future<int> insertOrUpdate(
    String table, 
    Map<String, dynamic> data, 
    String whereColumn, 
    dynamic whereValue
  ) async {
    final db = await database;
    
    try {
      // Check if record exists
      final existing = await db.query(
        table,
        where: '$whereColumn = ?',
        whereArgs: [whereValue],
        limit: 1,
      );
      
      if (existing.isNotEmpty) {
        // Update existing record
        final result = await db.update(
          table,
          data,
          where: '$whereColumn = ?',
          whereArgs: [whereValue],
        );
        print('📝 Updated (upsert) $table where $whereColumn = $whereValue');
        return result;
      } else {
        // Insert new record
        final result = await db.insert(table, data);
        print('➕ Inserted (upsert) $table where $whereColumn = $whereValue');
        return result;
      }
    } catch (e) {
      print('❌ Failed to upsert $table: $e');
      rethrow;
    }
  }
  
  /// Generic query operation
  Future<List<Map<String, dynamic>>> query(
    String table, {
    String? where,
    List<dynamic>? whereArgs,
    String? orderBy,
    int? limit,
    int? offset,
  }) async {
    final db = await database;
    
    try {
      return await db.query(
        table,
        where: where,
        whereArgs: whereArgs,
        orderBy: orderBy,
        limit: limit,
        offset: offset,
      );
    } catch (e) {
      print('❌ Failed to query $table: $e');
      rethrow;
    }
  }
  
  /// Get single record by ID
  Future<Map<String, dynamic>?> getById(String table, String id) async {
    final results = await query(
      table,
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    
    return results.isNotEmpty ? results.first : null;
  }
  
  /// Get all records for a user
  Future<List<Map<String, dynamic>>> getByUserId(String table, String userId) async {
    return await query(
      table,
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'created_at DESC',
    );
  }
  
  /// Get all dirty (unsynced) records
  Future<List<Map<String, dynamic>>> getDirtyRecords(String table) async {
    return await query(
      table,
      where: 'sync_status = ?',
      whereArgs: ['dirty'],
      orderBy: 'last_modified ASC',
    );
  }
  
  /// Mark record as dirty (needs sync)
  Future<void> markDirty(String table, String id) async {
    await update(table, {
      'sync_status': 'dirty',
      'local_version': await _incrementLocalVersion(table, id),
    }, id);
  }
  
  /// Mark record as clean (synced)
  Future<void> markClean(String table, String id, int serverVersion) async {
    await update(table, {
      'sync_status': 'clean',
      'version': serverVersion,
    }, id);
  }
  
  /// Mark record as having conflicts
  Future<void> markConflict(String table, String id) async {
    await update(table, {
      'sync_status': 'conflict',
    }, id);
  }
  
  /// Increment local version counter
  Future<int> _incrementLocalVersion(String table, String id) async {
    final record = await getById(table, id);
    if (record == null) return 1;
    
    return (record['local_version'] as int? ?? 0) + 1;
  }
  
  /// Execute multiple operations in a transaction
  Future<T> transaction<T>(Future<T> Function(Transaction txn) action) async {
    final db = await database;
    return await db.transaction(action);
  }
  
  /// Batch operations for better performance
  Future<List<dynamic>> batch(List<Map<String, dynamic>> operations) async {
    final db = await database;
    final batch = db.batch();
    
    for (final op in operations) {
      switch (op['type']) {
        case 'insert':
          batch.insert(op['table'], op['data']);
          break;
        case 'update':
          batch.update(
            op['table'],
            op['data'],
            where: 'id = ?',
            whereArgs: [op['id']],
          );
          break;
        case 'delete':
          batch.delete(
            op['table'],
            where: 'id = ?',
            whereArgs: [op['id']],
          );
          break;
      }
    }
    
    return await batch.commit();
  }
  
  /// Get sync statistics
  Future<Map<String, int>> getSyncStats() async {
    final stats = <String, int>{};
    
    for (final objectType in DatabaseInfo.getAllObjectTypes()) {
      final tableName = '${objectType}s'; // Simple pluralization
      
      final total = await _getCount(tableName);
      final dirty = await _getCount(tableName, where: 'sync_status = ?', whereArgs: ['dirty']);
      final conflicts = await _getCount(tableName, where: 'sync_status = ?', whereArgs: ['conflict']);
      
      stats['${objectType}_total'] = total;
      stats['${objectType}_dirty'] = dirty;
      stats['${objectType}_conflicts'] = conflicts;
    }
    
    return stats;
  }
  
  /// Get record count with optional filter
  Future<int> _getCount(String table, {String? where, List<dynamic>? whereArgs}) async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM $table${where != null ? ' WHERE $where' : ''}',
      whereArgs,
    );
    return result.first['count'] as int;
  }
  
  /// Get last sync timestamp
  Future<int> getLastSyncTimestamp() async {
    final result = await query(
      SyncMetadataSchema.tableName,
      where: 'key = ?',
      whereArgs: ['last_sync_timestamp'],
      limit: 1,
    );
    
    if (result.isNotEmpty) {
      return int.parse(result.first['value']);
    }
    return 0;
  }
  
  /// Update last sync timestamp
  Future<void> updateLastSyncTimestamp(int timestamp) async {
    final db = await database;
    await db.update(
      SyncMetadataSchema.tableName,
      {
        'value': timestamp.toString(),
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'key = ?',
      whereArgs: ['last_sync_timestamp'],
    );
  }
  
  /// Clear all data (for debugging/reset)
  Future<void> clearAllData() async {
    final db = await database;
    
    for (final objectType in DatabaseInfo.getAllObjectTypes()) {
      final tableName = '${objectType}s';
      await db.delete(tableName);
    }
    
    // Clear auxiliary tables
    await db.delete(SyncQueueSchema.tableName);
    await db.delete(ChangeLogSchema.tableName);
    await db.delete(ConflictSchema.tableName);
    
    print('🧹 All local data cleared');
  }
  
  /// Close database connection
  Future<void> close() async {
    if (_database != null) {
      await _database!.close();
      _database = null;
      print('🔒 Database connection closed');
    }
  }
  
  /// Database health check
  Future<bool> healthCheck() async {
    try {
      final db = await database;
      await db.rawQuery('SELECT 1');
      return true;
    } catch (e) {
      print('❌ Database health check failed: $e');
      return false;
    }
  }
  
  /// Get database file size
  Future<int> getDatabaseSize() async {
    try {
      final databasesPath = await getDatabasesPath();
      final path = join(databasesPath, DatabaseInfo.databaseName);
      final file = File(path);
      
      if (await file.exists()) {
        return await file.length();
      }
      return 0;
    } catch (e) {
      print('❌ Failed to get database size: $e');
      return 0;
    }
  }
  
  /// Vacuum database to reclaim space
  Future<void> vacuum() async {
    try {
      final db = await database;
      await db.execute('VACUUM');
      print('🧽 Database vacuumed');
    } catch (e) {
      print('❌ Failed to vacuum database: $e');
    }
  }
}

/// Extension for easier database operations
extension DatabaseOperations on LocalDatabaseService {
  /// Quick insert with auto-generated ID
  Future<String> insertWithId(String table, Map<String, dynamic> data) async {
    final id = data['id'] ?? const Uuid().v4();
    data['id'] = id;
    await insert(table, data);
    return id;
  }
  
  /// Upsert operation (insert or update)
  Future<void> upsert(String table, Map<String, dynamic> data) async {
    final id = data['id'];
    if (id == null) {
      throw ArgumentError('ID is required for upsert operation');
    }
    
    final existing = await getById(table, id);
    if (existing != null) {
      await update(table, data, id);
    } else {
      await insert(table, data);
    }
  }
  
  /// Soft delete (mark as deleted instead of removing)
  Future<void> softDelete(String table, String id) async {
    await update(table, {
      'deleted_at': DateTime.now().toIso8601String(),
      'sync_status': 'dirty',
    }, id);
  }
}