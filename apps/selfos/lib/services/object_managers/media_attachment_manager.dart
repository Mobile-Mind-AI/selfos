/// Media Attachment Manager for offline-first operations
/// 
/// This manager handles all operations for media attachments including:
/// - Creating and managing avatar uploads
/// - File upload status tracking
/// - Local file storage management
/// - Local-first operations with background sync
/// 
/// Note: Avatars are treated as MediaAttachment type as requested

import 'dart:convert';
import 'dart:io';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import '../sync/sync_queue.dart';
import '../sync/sync_manager.dart';

/// Media Attachment Manager for all media operations
class MediaAttachmentManager {
  static MediaAttachmentManager? _instance;
  MediaAttachmentManager._();

  static MediaAttachmentManager get instance {
    _instance ??= MediaAttachmentManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  final SyncManager _syncManager = SyncManager.instance;
  static const String _tableName = AvatarSchema.tableName;

  /// Create new media attachment (avatar) with optimistic update
  Future<Map<String, dynamic>> create({
    required String userId,
    required String filename,
    String? originalFilename,
    required String contentType,
    required int fileSize,
    int? width,
    int? height,
    bool isDefault = false,
    String? localPath,
  }) async {
    final id = const Uuid().v4();
    final now = DateTime.now();

    final attachment = {
      'id': id,
      'user_id': userId,
      'filename': filename,
      'original_filename': originalFilename ?? filename,
      'content_type': contentType,
      'file_size': fileSize,
      'width': width,
      'height': height,
      'is_default': isDefault ? 1 : 0,
      'upload_status': 'pending',
      'local_path': localPath,
      'server_url': null,
      'version': 0,
      'local_version': 1,
      'last_modified': now.toIso8601String(),
      'sync_status': 'dirty',
      'created_at': now.toIso8601String(),
      'updated_at': now.toIso8601String(),
    };

    // Save locally first (optimistic update)
    await _db.insert(_tableName, attachment);

    // Queue for sync with high priority for media uploads
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: id,
        objectType: AvatarSchema.objectType,
        operation: SyncOperationType.create,
        data: {
          'filename': filename,
          'original_filename': originalFilename ?? filename,
          'content_type': contentType,
          'file_size': fileSize,
          'width': width,
          'height': height,
          'is_default': isDefault,
          'local_path': localPath,
        },
        version: 1,
        priority: SyncPriority.high, // High priority for media uploads
      ),
    );

    print(' Created media attachment: $filename ($id)');
    return attachment;
  }

  /// Update media attachment with optimistic update
  Future<Map<String, dynamic>> update(
    String attachmentId,
    Map<String, dynamic> updates,
  ) async {
    final existing = await getById(attachmentId);
    if (existing == null) {
      throw Exception('Media attachment not found: $attachmentId');
    }

    // Prepare update data
    final updateData = Map<String, dynamic>.from(updates);
    updateData['local_version'] = (existing['local_version'] as int) + 1;
    updateData['last_modified'] = DateTime.now().toIso8601String();
    updateData['sync_status'] = 'dirty';
    updateData['updated_at'] = DateTime.now().toIso8601String();

    // Handle boolean conversion
    if (updateData['is_default'] is bool) {
      updateData['is_default'] = updateData['is_default'] ? 1 : 0;
    }

    // Save locally first
    await _db.update(_tableName, updateData, attachmentId);

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: attachmentId,
        objectType: AvatarSchema.objectType,
        operation: SyncOperationType.update,
        data: updates,
        version: updateData['local_version'],
        priority: SyncPriority.high, // High priority for media updates
      ),
    );

    final updated = await getById(attachmentId);
    print(' Updated media attachment: $attachmentId');
    return updated!;
  }

  /// Update upload status
  Future<Map<String, dynamic>> updateUploadStatus(
    String attachmentId,
    String status, {
    String? serverUrl,
    String? errorMessage,
  }) async {
    final updates = <String, dynamic>{
      'upload_status': status,
    };

    if (serverUrl != null) {
      updates['server_url'] = serverUrl;
    }

    // Store error in a meta field if needed (could extend schema)
    return await update(attachmentId, updates);
  }

  /// Mark as default avatar (and unmark others)
  Future<Map<String, dynamic>> setAsDefault(String attachmentId, String userId) async {
    // First, unmark any existing default avatars
    final existingDefaults = await getDefaultAvatars(userId);
    for (final avatar in existingDefaults) {
      if (avatar['id'] != attachmentId) {
        await update(avatar['id'], {'is_default': false});
      }
    }

    // Mark this one as default
    return await update(attachmentId, {'is_default': true});
  }

  /// Delete media attachment (soft delete)
  Future<void> delete(String attachmentId) async {
    // Get the attachment to check for local file cleanup
    final attachment = await getById(attachmentId);
    
    await _db.softDelete(_tableName, attachmentId);

    // Clean up local file if it exists
    if (attachment?['local_path'] != null) {
      try {
        final file = File(attachment!['local_path']);
        if (await file.exists()) {
          await file.delete();
          print('=Ñ Deleted local file: ${attachment['local_path']}');
        }
      } catch (e) {
        print('  Failed to delete local file: $e');
      }
    }

    // Queue for sync
    await _syncQueue.enqueue(
      SyncOperationHelper.createGenericOperation(
        objectId: attachmentId,
        objectType: AvatarSchema.objectType,
        operation: SyncOperationType.delete,
        data: {'deleted_at': DateTime.now().toIso8601String()},
        version: 0,
        priority: SyncPriority.normal,
      ),
    );

    print('=Ñ Deleted media attachment: $attachmentId');
  }

  /// Get media attachment by ID
  Future<Map<String, dynamic>?> getById(String attachmentId) async {
    final record = await _db.getById(_tableName, attachmentId);
    if (record == null) return null;

    // Parse boolean fields
    final decoded = Map<String, dynamic>.from(record);
    decoded['is_default'] = record['is_default'] == 1;

    return decoded;
  }

  /// Get all media attachments for user
  Future<List<Map<String, dynamic>>> getByUserId(String userId) async {
    final records = await _db.getByUserId(_tableName, userId);
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['is_default'] = record['is_default'] == 1;
      return decoded;
    }).toList();
  }

  /// Get default avatar for user
  Future<Map<String, dynamic>?> getDefaultAvatar(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_default = ?',
      whereArgs: [userId, 1],
      limit: 1,
    );
    
    if (records.isEmpty) return null;
    
    final record = records.first;
    final decoded = Map<String, dynamic>.from(record);
    decoded['is_default'] = record['is_default'] == 1;
    return decoded;
  }

  /// Get all default avatars (should be only one, but included for cleanup)
  Future<List<Map<String, dynamic>>> getDefaultAvatars(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND is_default = ?',
      whereArgs: [userId, 1],
    );
    return _parseAttachmentRecords(records);
  }

  /// Get attachments by upload status
  Future<List<Map<String, dynamic>>> getByUploadStatus(String status, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND upload_status = ?',
      whereArgs: [userId, status],
      orderBy: 'created_at DESC',
    );
    return _parseAttachmentRecords(records);
  }

  /// Get pending uploads
  Future<List<Map<String, dynamic>>> getPendingUploads(String userId) async {
    return await getByUploadStatus('pending', userId);
  }

  /// Get failed uploads
  Future<List<Map<String, dynamic>>> getFailedUploads(String userId) async {
    return await getByUploadStatus('failed', userId);
  }

  /// Get completed uploads
  Future<List<Map<String, dynamic>>> getCompletedUploads(String userId) async {
    return await getByUploadStatus('completed', userId);
  }

  /// Get attachments by content type
  Future<List<Map<String, dynamic>>> getByContentType(String contentType, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND content_type LIKE ?',
      whereArgs: [userId, '%$contentType%'],
      orderBy: 'created_at DESC',
    );
    return _parseAttachmentRecords(records);
  }

  /// Get image attachments (avatars)
  Future<List<Map<String, dynamic>>> getImageAttachments(String userId) async {
    return await getByContentType('image/', userId);
  }

  /// Get large attachments (above size threshold)
  Future<List<Map<String, dynamic>>> getLargeAttachments(String userId, {int minSizeBytes = 1048576}) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND file_size >= ?',
      whereArgs: [userId, minSizeBytes],
      orderBy: 'file_size DESC',
    );
    return _parseAttachmentRecords(records);
  }

  /// Get total storage used by user
  Future<int> getTotalStorageUsed(String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ?',
      whereArgs: [userId],
    );
    
    int totalSize = 0;
    for (final record in records) {
      totalSize += (record['file_size'] as int?) ?? 0;
    }
    
    return totalSize;
  }

  /// Search attachments by filename
  Future<List<Map<String, dynamic>>> searchByFilename(String query, String userId) async {
    final records = await _db.query(
      _tableName,
      where: 'user_id = ? AND (filename LIKE ? OR original_filename LIKE ?)',
      whereArgs: [userId, '%$query%', '%$query%'],
      orderBy: 'filename ASC',
    );
    return _parseAttachmentRecords(records);
  }

  /// Mark media attachment as synced
  Future<void> markSynced(String attachmentId, int serverVersion) async {
    await _db.markClean(_tableName, attachmentId, serverVersion);
    print(' Marked media attachment as synced: $attachmentId (v$serverVersion)');
  }

  /// Mark media attachment as having conflicts
  Future<void> markConflicted(String attachmentId) async {
    await _db.markConflict(_tableName, attachmentId);
    print('  Marked media attachment as conflicted: $attachmentId');
  }

  /// Get media attachments by sync status
  Future<List<Map<String, dynamic>>> getBySyncStatus(SyncStatus status) async {
    final records = await _db.query(
      _tableName,
      where: 'sync_status = ?',
      whereArgs: [status.name],
    );
    return _parseAttachmentRecords(records);
  }

  /// Cleanup orphaned local files
  Future<void> cleanupOrphanedFiles(String localStorageDir) async {
    try {
      final dir = Directory(localStorageDir);
      if (!await dir.exists()) return;

      // Get all attachment records with local paths
      final allRecords = await _db.query(_tableName);
      final knownPaths = allRecords
          .where((record) => record['local_path'] != null)
          .map((record) => record['local_path'] as String)
          .toSet();

      // Check directory for orphaned files
      await for (final entity in dir.list()) {
        if (entity is File && !knownPaths.contains(entity.path)) {
          await entity.delete();
          print('=Ñ Cleaned up orphaned file: ${entity.path}');
        }
      }
    } catch (e) {
      print('  Failed to cleanup orphaned files: $e');
    }
  }

  /// Parse attachment records with boolean conversion
  List<Map<String, dynamic>> _parseAttachmentRecords(List<Map<String, dynamic>> records) {
    return records.map((record) {
      final decoded = Map<String, dynamic>.from(record);
      decoded['is_default'] = record['is_default'] == 1;
      return decoded;
    }).toList();
  }
}