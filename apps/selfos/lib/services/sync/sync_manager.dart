/// Sync Manager for batch synchronization with backend API
/// 
/// This manager coordinates between the local sync queue and the backend
/// batch sync endpoints, implementing the offline-first sync architecture:
/// - Processes queued operations via batch API calls
/// - Handles conflict detection and resolution
/// - Manages delta sync for incremental updates
/// - Provides real-time sync status monitoring

import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:connectivity_plus/connectivity_plus.dart';
import '../auth_service.dart';
import '../network_service.dart';
import '../../config/app_config.dart';
import '../../config/api_endpoints.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import 'sync_queue.dart';
import 'conflict_resolver.dart';

/// Sync result from batch API call
class SyncResult {
  final String objectId;
  final SyncResultStatus status;
  final int? newVersion;
  final Map<String, dynamic>? serverData;
  final String? errorMessage;

  SyncResult({
    required this.objectId,
    required this.status,
    this.newVersion,
    this.serverData,
    this.errorMessage,
  });

  factory SyncResult.fromJson(Map<String, dynamic> json) {
    return SyncResult(
      objectId: json['object_id'],
      status: SyncResultStatus.values.byName(json['status']),
      newVersion: json['new_version'],
      serverData: json['server_data'],
      errorMessage: json['error_message'],
    );
  }

  bool get isSuccess => status == SyncResultStatus.success;
  bool get isConflict => status == SyncResultStatus.conflict;
  bool get isError => status == SyncResultStatus.error;
}

enum SyncResultStatus { success, conflict, error }

/// Delta sync response from API
class DeltaSyncResponse {
  final List<DeltaChange> changes;
  final int currentTimestamp;
  final bool hasMore;

  DeltaSyncResponse({
    required this.changes,
    required this.currentTimestamp,
    required this.hasMore,
  });

  factory DeltaSyncResponse.fromJson(Map<String, dynamic> json) {
    return DeltaSyncResponse(
      changes: (json['changes'] as List)
          .map((c) => DeltaChange.fromJson(c))
          .toList(),
      currentTimestamp: json['current_timestamp'],
      hasMore: json['has_more'],
    );
  }
}

/// Individual change from delta sync
class DeltaChange {
  final String objectId;
  final String objectType;
  final String operation;
  final Map<String, dynamic> data;
  final int version;
  final int timestamp;

  DeltaChange({
    required this.objectId,
    required this.objectType,
    required this.operation,
    required this.data,
    required this.version,
    required this.timestamp,
  });

  factory DeltaChange.fromJson(Map<String, dynamic> json) {
    return DeltaChange(
      objectId: json['object_id'].toString(),
      objectType: json['object_type'],
      operation: json['operation'],
      data: json['data'],
      version: json['version'],
      timestamp: json['timestamp'],
    );
  }
}

/// Sync status information
class SyncStatus {
  final bool isOnline;
  final bool isSyncing;
  final int pendingOperations;
  final int totalOperations;
  final DateTime? lastSyncAt;
  final String? lastError;
  final Map<String, int> operationsByType;

  SyncStatus({
    required this.isOnline,
    required this.isSyncing,
    required this.pendingOperations,
    required this.totalOperations,
    this.lastSyncAt,
    this.lastError,
    required this.operationsByType,
  });

  double get syncProgress {
    if (totalOperations == 0) return 1.0;
    final completed = totalOperations - pendingOperations;
    return completed / totalOperations;
  }

  bool get isComplete => pendingOperations == 0;
}

/// Main sync manager class
class SyncManager {
  static SyncManager? _instance;
  SyncManager._();

  static SyncManager get instance {
    _instance ??= SyncManager._();
    return _instance!;
  }

  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final SyncQueueService _syncQueue = SyncQueueService.instance;
  final AuthService _auth = AuthService.instance;
  final NetworkService _network = NetworkService.instance;
  final ConflictResolver _conflictResolver = ConflictResolver.instance;

  // HTTP client for API calls
  late http.Client _httpClient;

  // Sync state
  bool _isInitialized = false;
  bool _isSyncing = false;
  DateTime? _lastSyncAt;
  String? _lastError;
  Timer? _deltaTimer;
  
  // Status stream controller
  final StreamController<SyncStatus> _statusController = 
      StreamController<SyncStatus>.broadcast();

  /// Stream of sync status updates
  Stream<SyncStatus> get statusStream => _statusController.stream;

  /// Get current sync status (async method)
  Future<SyncStatus> get currentStatus async {
    final networkState = _network.currentState;
    final stats = await _syncQueue.getStats();
    
    return SyncStatus(
      isOnline: networkState.isOnline,
      isSyncing: _isSyncing,
      pendingOperations: stats.pendingOperations,
      totalOperations: stats.totalOperations,
      lastSyncAt: _lastSyncAt,
      lastError: _lastError,
      operationsByType: stats.operationsByType,
    );
  }

  /// Initialize sync manager
  Future<void> initialize() async {
    if (_isInitialized) return;

    print('🔄 Initializing sync manager...');

    _httpClient = http.Client();

    // Initialize network service first
    await _network.initialize();

    // Replace the mock API call in sync queue with real implementation
    await _syncQueue.initialize();

    // Start periodic delta sync (every 30 seconds)
    _deltaTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _performDeltaSync(),
    );

    _isInitialized = true;
    await _updateStatus();

    print('✅ Sync manager initialized');
  }

  /// Process sync queue with batch API calls
  Future<void> processSyncQueue() async {
    if (_isSyncing) return;

    // Check network availability
    if (!_network.currentState.isOnline) {
      print('📶 Skipping sync - network unavailable');
      return;
    }

    _isSyncing = true;
    _lastError = null;

    try {
      print('🔄 Processing sync queue...');

      // Get pending operations from queue
      final stats = await _syncQueue.getStats();
      if (stats.pendingOperations == 0) {
        print('📭 No pending operations to sync');
        return;
      }

      // Get operations by batch
      final operations = await _getPendingOperations();
      if (operations.isEmpty) return;

      print('📦 Syncing ${operations.length} operations');

      // Group operations by type for efficient API calls
      final groupedOps = _groupOperationsByType(operations);

      // Process each group via batch API
      for (final entry in groupedOps.entries) {
        final objectType = entry.key;
        final typeOps = entry.value;

        await _processBatchForType(objectType, typeOps);
      }

      _lastSyncAt = DateTime.now();
      print('✅ Sync queue processed successfully');

    } catch (e) {
      _lastError = e.toString();
      print('❌ Error processing sync queue: $e');
    } finally {
      _isSyncing = false;
      await _updateStatus();
    }
  }

  /// Get pending operations from sync queue
  Future<List<SyncOperation>> _getPendingOperations() async {
    final results = await _db.query(
      SyncQueueSchema.tableName,
      where: 'scheduled_at <= ?',
      whereArgs: [DateTime.now().toIso8601String()],
      orderBy: '''
        CASE priority 
          WHEN 'critical' THEN 1
          WHEN 'high' THEN 2
          WHEN 'normal' THEN 3
          WHEN 'low' THEN 4
        END,
        scheduled_at ASC
      ''',
      limit: 50, // Process in batches of 50
    );

    return results.map((r) => SyncOperation.fromMap(r)).toList();
  }

  /// Group operations by object type
  Map<String, List<SyncOperation>> _groupOperationsByType(
      List<SyncOperation> operations) {
    final grouped = <String, List<SyncOperation>>{};

    for (final op in operations) {
      grouped.putIfAbsent(op.objectType, () => []).add(op);
    }

    return grouped;
  }

  /// Process batch of operations for specific type via API
  Future<void> _processBatchForType(
      String objectType, List<SyncOperation> operations) async {
    try {
      print('🌐 Syncing ${operations.length} $objectType operations');

      // Prepare batch request
      final batchRequest = {
        'operations': operations.map((op) => {
          'object_id': op.objectId,
          'object_type': op.objectType,
          'operation': op.operation.name,
          'data': op.data,
          'version': op.version,
          if (op.operation == SyncOperationType.update)
            'if_match_version': op.version - 1,
        }).toList(),
        'client_id': 'flutter_client',
      };

      // Make API call
      final results = await _callBatchSyncAPI(batchRequest);

      // Process results
      for (int i = 0; i < operations.length; i++) {
        final operation = operations[i];
        final result = results[i];

        await _handleSyncResult(operation, result);
      }

    } catch (e) {
      print('❌ Batch sync failed for $objectType: $e');

      // Handle failed operations
      for (final op in operations) {
        await _handleFailedOperation(op, e.toString());
      }
    }
  }

  /// Make batch sync API call with retry logic
  Future<List<SyncResult>> _callBatchSyncAPI(
      Map<String, dynamic> batchRequest) async {
    return await _network.withRetry(() async {
      final token = await _auth.getToken();
      if (token == null) {
        throw Exception('No authentication token available');
      }

      final response = await _httpClient.post(
        Uri.parse(ApiEndpoints.syncBatch),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(batchRequest),
      );

      if (response.statusCode != 200) {
        throw Exception('API call failed: ${response.statusCode} ${response.body}');
      }

      final List<dynamic> resultsJson = json.decode(response.body);
      return resultsJson.map((r) => SyncResult.fromJson(r)).toList();
    }, maxRetries: 3);
  }

  /// Handle individual sync result
  Future<void> _handleSyncResult(SyncOperation operation, SyncResult result) async {
    if (result.isSuccess) {
      // Remove from queue and mark as synced
      await _syncQueue._removeOperation(operation.id);
      
      if (result.newVersion != null) {
        await _markObjectSynced(operation, result.newVersion!);
      }
      
      print('✅ Synced ${operation.operation.name} for ${operation.objectType}:${operation.objectId}');

    } else if (result.isConflict) {
      // Handle conflict
      await _handleSyncConflict(operation, result);
      
    } else if (result.isError) {
      // Handle error
      await _handleFailedOperation(operation, result.errorMessage ?? 'Unknown error');
    }
  }

  /// Mark object as synced in local database
  Future<void> _markObjectSynced(SyncOperation operation, int newVersion) async {
    final tableName = _getTableNameForObjectType(operation.objectType);
    if (tableName != null) {
      await _db.markClean(tableName, operation.objectId, newVersion);
    }
  }

  /// Handle sync conflict with automated resolution
  Future<void> _handleSyncConflict(SyncOperation operation, SyncResult result) async {
    print('⚠️ Conflict detected for ${operation.objectType}:${operation.objectId}');
    
    try {
      // Attempt automated conflict resolution
      final resolution = await _conflictResolver.resolveConflict(
        objectType: operation.objectType,
        localData: operation.data,
        serverData: result.serverData ?? {},
        localVersion: operation.version,
        serverVersion: result.newVersion ?? 0,
      );

      if (!resolution.requiresManualReview) {
        // Apply automated resolution
        await _applyResolvedConflict(operation, resolution);
        print('✅ Automatically resolved conflict for ${operation.objectType}:${operation.objectId}');
        
        // Remove from queue as resolved
        await _syncQueue._removeOperation(operation.id);
      } else {
        // Store for manual review
        await _storeConflictForManualReview(operation, result, resolution);
        await _syncQueue._removeOperation(operation.id);
      }
      
    } catch (e) {
      print('❌ Failed to resolve conflict for ${operation.objectType}:${operation.objectId}: $e');
      
      // Fallback to storing conflict data
      await _storeConflictData(operation, result);
      await _syncQueue._removeOperation(operation.id);
    }
  }

  /// Apply resolved conflict to local database
  Future<void> _applyResolvedConflict(
    SyncOperation operation, 
    ConflictResolutionResult resolution
  ) async {
    final tableName = _getTableNameForObjectType(operation.objectType);
    if (tableName == null) return;

    // Apply resolved data
    final resolvedData = Map<String, dynamic>.from(resolution.resolvedData);
    resolvedData['sync_status'] = 'clean';
    resolvedData['version'] = operation.version + 1; // Increment version
    
    await _db.update(tableName, resolvedData, operation.objectId);
    
    // Log resolution details
    for (final logEntry in resolution.resolutionLog) {
      print('🔧 Resolution: $logEntry');
    }
  }

  /// Store conflict for manual review with resolution context
  Future<void> _storeConflictForManualReview(
    SyncOperation operation,
    SyncResult result,
    ConflictResolutionResult resolution
  ) async {
    final conflictData = {
      'id': operation.id,
      'object_id': operation.objectId,
      'object_type': operation.objectType,
      'local_data': json.encode(operation.data),
      'server_data': json.encode(result.serverData),
      'local_version': operation.version,
      'server_version': result.newVersion,
      'resolution_strategy': 'auto_with_manual_review',
      'resolved_data': json.encode(resolution.resolvedData),
      'resolution_log': json.encode(resolution.resolutionLog),
      'resolved': 0,
      'created_at': DateTime.now().toIso8601String(),
    };

    await _db.insert(ConflictSchema.tableName, conflictData);
    print('📝 Conflict stored for manual review: ${operation.objectType}:${operation.objectId}');
  }

  /// Store conflict data for later resolution (fallback)
  Future<void> _storeConflictData(SyncOperation operation, SyncResult result) async {
    final conflictData = {
      'id': operation.id,
      'object_id': operation.objectId,
      'object_type': operation.objectType,
      'local_data': json.encode(operation.data),
      'server_data': json.encode(result.serverData),
      'local_version': operation.version,
      'server_version': result.newVersion,
      'resolution_strategy': 'manual',
      'resolved': 0,
      'created_at': DateTime.now().toIso8601String(),
    };

    await _db.insert(ConflictSchema.tableName, conflictData);
    print('📝 Conflict stored for manual resolution: ${operation.objectType}:${operation.objectId}');
  }

  /// Handle failed operation
  Future<void> _handleFailedOperation(SyncOperation operation, String error) async {
    if (operation.canRetry) {
      // Update operation with retry
      final retryOp = operation.withRetry();
      await _syncQueue._updateOperation(retryOp);
      print('🔄 Scheduled retry for ${operation.objectType}:${operation.objectId} (attempt ${retryOp.retryCount})');
    } else {
      // Max retries reached - remove from queue
      await _syncQueue._removeOperation(operation.id);
      print('❌ Max retries reached for ${operation.objectType}:${operation.objectId}: $error');
    }
  }

  /// Perform delta sync to get server changes
  Future<void> _performDeltaSync() async {
    if (_isSyncing) return;

    try {
      final lastSyncTimestamp = await _getLastDeltaSyncTimestamp();
      final delta = await _callDeltaSyncAPI(lastSyncTimestamp);

      if (delta.changes.isNotEmpty) {
        print('📥 Received ${delta.changes.length} changes from server');
        await _applyDeltaChanges(delta.changes);
      }

      // Update last sync timestamp
      await _setLastDeltaSyncTimestamp(delta.currentTimestamp);

    } catch (e) {
      print('❌ Delta sync failed: $e');
    }
  }

  /// Call delta sync API with retry logic
  Future<DeltaSyncResponse> _callDeltaSyncAPI(int sinceTimestamp) async {
    return await _network.withRetry(() async {
      final token = await _auth.getToken();
      if (token == null) {
        throw Exception('No authentication token available');
      }

      final response = await _httpClient.get(
        Uri.parse(ApiEndpoints.syncDelta(sinceTimestamp)),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode != 200) {
        throw Exception('Delta sync failed: ${response.statusCode} ${response.body}');
      }

      return DeltaSyncResponse.fromJson(json.decode(response.body));
    }, maxRetries: 2); // Fewer retries for delta sync
  }

  /// Apply delta changes to local database
  Future<void> _applyDeltaChanges(List<DeltaChange> changes) async {
    for (final change in changes) {
      await _applyDeltaChange(change);
    }
  }

  /// Apply individual delta change
  Future<void> _applyDeltaChange(DeltaChange change) async {
    final tableName = _getTableNameForObjectType(change.objectType);
    if (tableName == null) return;

    try {
      if (change.operation == 'create' || change.operation == 'update') {
        // Merge server data with local data
        final localData = await _db.getById(tableName, change.objectId);
        
        if (localData != null && localData['sync_status'] == 'dirty') {
          // Local changes exist - attempt automated conflict resolution
          try {
            final resolution = await _conflictResolver.resolveConflict(
              objectType: change.objectType,
              localData: localData,
              serverData: change.data,
              localVersion: localData['version'] ?? 0,
              serverVersion: change.version,
            );

            if (!resolution.requiresManualReview) {
              // Apply automated resolution
              final resolvedData = Map<String, dynamic>.from(resolution.resolvedData);
              resolvedData['version'] = change.version;
              resolvedData['sync_status'] = 'clean';
              
              await _db.update(tableName, resolvedData, change.objectId);
              print('✅ Auto-resolved delta conflict for ${change.objectType}:${change.objectId}');
            } else {
              // Mark as conflict for manual review
              await _db.markConflict(tableName, change.objectId);
              print('⚠️ Delta conflict needs manual review for ${change.objectType}:${change.objectId}');
            }
          } catch (e) {
            // Fallback to marking as conflict
            await _db.markConflict(tableName, change.objectId);
            print('⚠️ Conflict detected for ${change.objectType}:${change.objectId} during delta sync (resolution failed: $e)');
          }
        } else {
          // Safe to update with server data
          final updateData = Map<String, dynamic>.from(change.data);
          updateData['version'] = change.version;
          updateData['sync_status'] = 'clean';
          updateData['last_modified'] = DateTime.fromMillisecondsSinceEpoch(change.timestamp).toIso8601String();

          if (localData == null) {
            await _db.insert(tableName, updateData);
          } else {
            await _db.update(tableName, updateData, change.objectId);
          }
          
          print('📥 Applied ${change.operation} for ${change.objectType}:${change.objectId}');
        }
      } else if (change.operation == 'delete') {
        await _db.delete(tableName, change.objectId);
        print('🗑️ Applied delete for ${change.objectType}:${change.objectId}');
      }
    } catch (e) {
      print('❌ Failed to apply delta change for ${change.objectType}:${change.objectId}: $e');
    }
  }

  /// Get table name for object type
  String? _getTableNameForObjectType(String objectType) {
    switch (objectType) {
      case 'assistant_profile':
        return AssistantProfileSchema.tableName;
      case 'personal_profile':
        return PersonalProfileSchema.tableName;
      case 'goal':
        return GoalSchema.tableName;
      case 'project':
        return ProjectSchema.tableName;
      case 'task':
        return TaskSchema.tableName;
      case 'life_area':
        return LifeAreaSchema.tableName;
      case 'avatar':
      case 'media_attachment':
        return AvatarSchema.tableName;
      case 'onboarding_state':
        return OnboardingStateSchema.tableName;
      default:
        return null;
    }
  }

  /// Get last delta sync timestamp
  Future<int> _getLastDeltaSyncTimestamp() async {
    final results = await _db.query(
      'sync_metadata',
      where: 'key = ?',
      whereArgs: ['last_delta_sync'],
      limit: 1,
    );

    if (results.isNotEmpty) {
      return int.parse(results.first['value']);
    }

    // Return timestamp from 1 hour ago for first sync
    return DateTime.now().subtract(const Duration(hours: 1)).millisecondsSinceEpoch;
  }

  /// Set last delta sync timestamp
  Future<void> _setLastDeltaSyncTimestamp(int timestamp) async {
    await _db.insertOrUpdate(
      'sync_metadata',
      {
        'key': 'last_delta_sync',
        'value': timestamp.toString(),
        'updated_at': DateTime.now().toIso8601String(),
      },
      'key',
      'last_delta_sync',
    );
  }

  /// Update status and notify listeners
  Future<void> _updateStatus() async {
    final stats = await _syncQueue.getStats();
    final status = SyncStatus(
      isOnline: stats.isOnline,
      isSyncing: _isSyncing,
      pendingOperations: stats.pendingOperations,
      totalOperations: stats.totalOperations,
      lastSyncAt: _lastSyncAt,
      lastError: _lastError,
      operationsByType: stats.operationsByType,
    );

    _statusController.add(status);
  }

  /// Force immediate sync
  Future<void> forcSync() async {
    print('🚀 Force sync requested');
    await processSyncQueue();
    await _performDeltaSync();
  }

  /// Get sync statistics
  Future<SyncStatus> getStatus() async {
    await _updateStatus();
    return await currentStatus;
  }

  /// Dispose resources
  void dispose() {
    _deltaTimer?.cancel();
    _statusController.close();
    _httpClient.close();
    print('🔒 Sync manager disposed');
  }
}