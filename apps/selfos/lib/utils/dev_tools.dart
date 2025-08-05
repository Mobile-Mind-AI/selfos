/// Development tools for debugging and testing
/// 
/// This file contains utility functions for development purposes,
/// such as clearing local data, resetting state, etc.

import '../services/local_database/database_service.dart';
import '../services/sync/sync_queue.dart';
import '../services/storage_service.dart';

class DevTools {
  /// Clear all local data (database, sync queue, and stored tokens)
  static Future<void> clearAllLocalData() async {
    try {
      print('🧹 Starting complete local data cleanup...');
      
      // 1. Clear sync queue
      await SyncQueueService.instance.clearQueue();
      print('✅ Sync queue cleared');
      
      // 2. Delete local database
      await LocalDatabaseService.instance.deleteDatabase();
      print('✅ Local database deleted');
      
      // 3. Clear stored tokens
      await StorageService.clearAccessToken();
      await StorageService.clearRefreshToken();
      print('✅ Authentication tokens cleared');
      
      // 4. Clear any other stored preferences
      await StorageService.clearAll();
      print('✅ All stored preferences cleared');
      
      print('🎉 All local data cleared successfully!');
    } catch (e) {
      print('❌ Error clearing local data: $e');
      rethrow;
    }
  }
  
  /// Clear only the local database (keeps auth tokens)
  static Future<void> clearLocalDatabase() async {
    try {
      print('🗄️ Clearing local database...');
      
      // Clear sync queue first
      await SyncQueueService.instance.clearQueue();
      
      // Delete database
      await LocalDatabaseService.instance.deleteDatabase();
      
      print('✅ Local database cleared successfully!');
    } catch (e) {
      print('❌ Error clearing database: $e');
      rethrow;
    }
  }
  
  /// Get database info for debugging
  static Future<Map<String, dynamic>> getDatabaseInfo() async {
    try {
      final db = await LocalDatabaseService.instance.database;
      final tables = await db.rawQuery(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
      );
      
      final info = <String, dynamic>{
        'path': db.path,
        'isOpen': db.isOpen,
        'tables': [],
      };
      
      for (final table in tables) {
        final tableName = table['name'] as String;
        final count = await db.rawQuery('SELECT COUNT(*) as count FROM $tableName');
        info['tables'].add({
          'name': tableName,
          'rowCount': count.first['count'],
        });
      }
      
      return info;
    } catch (e) {
      return {'error': e.toString()};
    }
  }
}