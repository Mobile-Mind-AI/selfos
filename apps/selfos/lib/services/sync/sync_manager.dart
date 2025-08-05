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
import '../storage_service.dart';
import '../network_service.dart';
import '../../config/api_endpoints.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';
import 'sync_queue.dart';
import 'conflict_resolver.dart';
import '../object_managers/assistant_profile_manager.dart';
import '../object_managers/life_area_manager.dart';
import '../object_managers/personal_profile_manager.dart';
import '../object_managers/onboarding_state_manager.dart';

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

    // Temporarily disable periodic delta sync to prevent infinite loops
    // TODO: Re-enable once sync architecture is stabilized
    // _deltaTimer = Timer.periodic(
    //   const Duration(seconds: 30),
    //   (_) => _performDeltaSync(),
    // );

    _isInitialized = true;
    await _updateStatus();

    print('✅ Sync manager initialized');
  }

  /// Perform initial sync for a newly authenticated user
  /// This fetches essential data from backend to populate local database
  Future<void> performInitialSync(String userId) async {
    try {
      print('🔄 INITIAL_SYNC: Starting initial sync for user: $userId');
      
      // Ensure sync manager is initialized
      if (!_isInitialized) {
        await initialize();
      }
      
      // Always fetch from backend first to establish baseline
      print('🔄 INITIAL_SYNC: Fetching latest data from backend');
      
      // Get manager instances
      final assistantManager = AssistantProfileManager.instance;
      final lifeAreaManager = LifeAreaManager.instance;
      final personalProfileManager = PersonalProfileManager.instance;
      final onboardingManager = OnboardingStateManager.instance;
      
      // Always fetch from backend to get the authoritative state
      await Future.wait([
        _syncAssistantProfilesFromBackend(userId, assistantManager),
        _syncLifeAreas(userId, lifeAreaManager),
        _syncPersonalProfile(userId, personalProfileManager),
        _syncOnboardingState(userId, onboardingManager),
      ]);
      
      print('✅ INITIAL_SYNC: Backend fetch completed');
      
      // Then sync any local changes to backend
      print('🔄 INITIAL_SYNC: Syncing local changes to backend');
      processSyncQueue();
    } catch (e) {
      print('❌ INITIAL_SYNC: Error during initial sync: $e');
      // Don't throw - app should work offline
    }
  }
  
  /// Check if we have any local data for this user
  Future<bool> _checkLocalData(String userId) async {
    try {
      final records = await _db.query(
        AssistantProfileSchema.tableName,
        where: 'user_id = ?',
        whereArgs: [userId],
        limit: 1,
      );
      return records.isNotEmpty;
    } catch (e) {
      return false;
    }
  }
  
  
  /// Always fetch assistant profiles from backend (authoritative)
  Future<void> _syncAssistantProfilesFromBackend(String userId, dynamic manager) async {
    try {
      print('🔄 INITIAL_SYNC: Fetching assistant profiles from backend...');
      
      // Always fetch from backend to get authoritative state
      final assistants = await manager.fetchFromBackend(userId);
      print('✅ INITIAL_SYNC: Fetched ${assistants.length} assistant profiles from backend');
    } catch (e) {
      print('⚠️ INITIAL_SYNC: Failed to fetch assistant profiles from backend: $e');
    }
  }
  
  /// Sync life areas from backend
  Future<void> _syncLifeAreas(String userId, dynamic manager) async {
    try {
      print('🔄 INITIAL_SYNC: Syncing life areas...');
      
      // This will fetch system life areas if not present
      final lifeAreas = await manager.getAllLifeAreas(userId);
      print('✅ INITIAL_SYNC: Found ${lifeAreas.length} life areas');
    } catch (e) {
      print('⚠️ INITIAL_SYNC: Failed to sync life areas: $e');
    }
  }
  
  /// Sync personal profile from backend
  Future<void> _syncPersonalProfile(String userId, dynamic manager) async {
    try {
      print('🔄 INITIAL_SYNC: Syncing personal profile...');
      
      // Check if we already have a profile locally
      final localProfile = await manager.getByUserId(userId);
      if (localProfile != null) {
        print('🔄 INITIAL_SYNC: Personal profile already exists locally');
        return;
      }
      
      // Fetch from backend
      final profile = await manager.fetchFromBackend(userId);
      if (profile != null) {
        print('✅ INITIAL_SYNC: Synced personal profile');
      } else {
        print('📝 INITIAL_SYNC: No personal profile on backend');
      }
    } catch (e) {
      print('⚠️ INITIAL_SYNC: Failed to sync personal profile: $e');
    }
  }
  
  /// Sync onboarding state from backend
  Future<void> _syncOnboardingState(String userId, dynamic manager) async {
    try {
      print('🔄 INITIAL_SYNC: Syncing onboarding state...');
      
      // Check if we already have onboarding state locally
      final localState = await manager.getByUserId(userId);
      if (localState != null) {
        print('🔄 INITIAL_SYNC: Onboarding state already exists locally');
        return;
      }
      
      // Fetch from backend
      final state = await manager.fetchFromBackend(userId);
      if (state != null) {
        print('✅ INITIAL_SYNC: Synced onboarding state');
      } else {
        print('📝 INITIAL_SYNC: No onboarding state on backend');
      }
    } catch (e) {
      print('⚠️ INITIAL_SYNC: Failed to sync onboarding state: $e');
    }
  }

  /// Process sync queue with batch API calls
  Future<void> processSyncQueue() async {
    // Ensure sync manager is initialized
    if (!_isInitialized) {
      await initialize();
    }
    
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
      
      // Add a small delay to prevent rapid-fire requests
      await Future.delayed(const Duration(milliseconds: 500));

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
      print('📊 Grouped operations by type: ${groupedOps.keys.toList()}');
      
      for (final entry in groupedOps.entries) {
        final objectType = entry.key;
        final typeOps = entry.value;

        // Process critical types one at a time to avoid transaction conflicts
        if (objectType == 'onboarding_state' || objectType == 'assistant_profile') {
          print('🔐 Processing $objectType operations sequentially (${typeOps.length} ops)');
          for (final op in typeOps) {
            await _processBatchForType(objectType, [op]);
            await Future.delayed(const Duration(milliseconds: 500));
          }
        } else {
          print('📦 Processing $objectType operations in batch (${typeOps.length} ops)');
          await _processBatchForType(objectType, typeOps);
        }
        
        // Add delay between batches to avoid rate limiting
        if (groupedOps.entries.toList().indexOf(entry) < groupedOps.entries.length - 1) {
          await Future.delayed(const Duration(milliseconds: 500));
        }
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
      limit: 5, // Process in smaller batches to avoid rate limiting and transaction conflicts
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
      
      // Check if it's a transaction error - if so, retry with delay
      if (e.toString().contains('Transaction failed') || 
          e.toString().contains('transaction is already begun')) {
        print('⚠️ Backend transaction conflict detected, will retry with delay');
        
        // Add longer delay before retry for transaction conflicts
        await Future.delayed(const Duration(seconds: 2));
      }

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
      final token = await StorageService.getAuthorizationHeader();
      if (token == null) {
        throw Exception('No authentication token available');
      }

      final response = await _httpClient.post(
        Uri.parse(ApiEndpoints.syncBatch),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token,
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
      await _syncQueue.removeOperation(operation.id);
      
      // For create operations, check if backend returned a different ID
      if (operation.operation == SyncOperationType.create && result.serverData != null) {
        final serverId = result.serverData!['id'] as String?;
        if (serverId != null && serverId != operation.objectId) {
          print('🔄 Backend returned different ID: local=${operation.objectId}, server=$serverId');
          // Update local record with server ID
          await _updateLocalIdWithServerId(operation, serverId);
        }
      }
      
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

  /// Update local record ID with server-generated ID
  Future<void> _updateLocalIdWithServerId(SyncOperation operation, String serverId) async {
    final tableName = _getTableNameForObjectType(operation.objectType);
    if (tableName == null) return;

    try {
      // Get the existing record
      final existingRecord = await _db.getById(tableName, operation.objectId);
      if (existingRecord == null) {
        print('⚠️ Could not find local record to update ID: ${operation.objectId}');
        return;
      }

      // Create new record with server ID
      final newRecord = Map<String, dynamic>.from(existingRecord);
      newRecord['id'] = serverId;
      
      // Delete old record and insert new one with server ID
      await _db.delete(tableName, operation.objectId);
      await _db.insert(tableName, newRecord);
      
      print('✅ Updated local record ID from ${operation.objectId} to $serverId');
    } catch (e) {
      print('❌ Failed to update local ID: $e');
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
        await _syncQueue.removeOperation(operation.id);
      } else {
        // Store for manual review
        await _storeConflictForManualReview(operation, result, resolution);
        await _syncQueue.removeOperation(operation.id);
      }
      
    } catch (e) {
      print('❌ Failed to resolve conflict for ${operation.objectType}:${operation.objectId}: $e');
      
      // Fallback to storing conflict data
      await _storeConflictData(operation, result);
      await _syncQueue.removeOperation(operation.id);
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
    
    // Encode JSON fields for SQLite storage
    _encodeJsonFieldsForObjectType(operation.objectType, resolvedData);
    
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
    // Find conflicting fields
    final conflictFields = _findConflictingFields(operation.data, result.serverData ?? {});
    
    final conflictData = {
      'id': operation.id,
      'object_id': operation.objectId,
      'object_type': operation.objectType,
      'local_data': json.encode(operation.data),
      'server_data': json.encode(result.serverData),
      'local_version': operation.version,
      'server_version': result.newVersion,
      'conflict_fields': json.encode(conflictFields),
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
    // Find conflicting fields
    final conflictFields = _findConflictingFields(operation.data, result.serverData ?? {});
    
    final conflictData = {
      'id': operation.id,
      'object_id': operation.objectId,
      'object_type': operation.objectType,
      'local_data': json.encode(operation.data),
      'server_data': json.encode(result.serverData),
      'local_version': operation.version,
      'server_version': result.newVersion,
      'conflict_fields': json.encode(conflictFields),
      'resolution_strategy': 'manual',
      'resolved': 0,
      'created_at': DateTime.now().toIso8601String(),
    };

    await _db.insert(ConflictSchema.tableName, conflictData);
    print('📝 Conflict stored for manual resolution: ${operation.objectType}:${operation.objectId}');
  }
  
  /// Find fields that differ between local and server data
  List<String> _findConflictingFields(Map<String, dynamic> localData, Map<String, dynamic> serverData) {
    final conflictingFields = <String>[];
    
    // Check all fields in local data
    for (final key in localData.keys) {
      if (serverData.containsKey(key)) {
        final localValue = localData[key];
        final serverValue = serverData[key];
        
        // Compare values (handle different types)
        if (localValue != serverValue) {
          if (localValue is List && serverValue is List) {
            // Deep compare lists
            if (localValue.length != serverValue.length ||
                !localValue.every((item) => serverValue.contains(item))) {
              conflictingFields.add(key);
            }
          } else if (localValue is Map && serverValue is Map) {
            // For maps, just mark as conflicting if they're different
            if (json.encode(localValue) != json.encode(serverValue)) {
              conflictingFields.add(key);
            }
          } else {
            conflictingFields.add(key);
          }
        }
      }
    }
    
    // Check fields that exist in server but not in local
    for (final key in serverData.keys) {
      if (!localData.containsKey(key) && serverData[key] != null) {
        conflictingFields.add(key);
      }
    }
    
    return conflictingFields;
  }

  /// Handle failed operation
  Future<void> _handleFailedOperation(SyncOperation operation, String error) async {
    // Let the sync queue handle the retry logic to avoid duplicate operations
    // The sync queue already has retry handling in its _handleFailedOperation method
    print('⚠️ Operation failed for ${operation.objectType}:${operation.objectId}: $error');
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
      final token = await StorageService.getAuthorizationHeader();
      if (token == null) {
        throw Exception('No authentication token available');
      }

      final response = await _httpClient.get(
        Uri.parse(ApiEndpoints.syncDelta(sinceTimestamp)),
        headers: {
          'Authorization': token,
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
            // For delta sync, ignore objects we don't have locally
            // They should be created through normal sync flow with temp IDs first
            print('⚠️ Delta sync: Ignoring unknown object ${change.objectType}:${change.objectId} - should be created with temp ID first');
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
      case 'media_attachment':
        return AvatarSchema.tableName;
      case 'avatar':
        // Disable avatar syncing for now
        return null;
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

  /// Encode JSON fields for SQLite storage based on object type
  void _encodeJsonFieldsForObjectType(String objectType, Map<String, dynamic> data) {
    switch (objectType) {
      case 'personal_profile':
        // Encode list fields
        if (data['interests'] is List) data['interests'] = json.encode(data['interests']);
        if (data['challenges'] is List) data['challenges'] = json.encode(data['challenges']);
        if (data['aspirations'] is List) data['aspirations'] = json.encode(data['aspirations']);
        if (data['selected_life_areas'] is List) data['selected_life_areas'] = json.encode(data['selected_life_areas']);
        // Encode map fields
        if (data['preferences'] is Map) data['preferences'] = json.encode(data['preferences']);
        if (data['custom_answers'] is Map) data['custom_answers'] = json.encode(data['custom_answers']);
        if (data['story_analysis'] is Map) data['story_analysis'] = json.encode(data['story_analysis']);
        break;
        
      case 'assistant_profile':
        if (data['style'] is Map) data['style'] = json.encode(data['style']);
        break;
        
      case 'life_area':
        if (data['keywords'] is List) data['keywords'] = json.encode(data['keywords']);
        break;
        
      case 'goal':
      case 'project':
        if (data['media_attachments'] is List) data['media_attachments'] = json.encode(data['media_attachments']);
        break;
        
      case 'task':
        if (data['dependencies'] is List) data['dependencies'] = json.encode(data['dependencies']);
        break;
        
      case 'onboarding_state':
        if (data['completed_steps'] is List) data['completed_steps'] = json.encode(data['completed_steps']);
        if (data['temp_data'] is Map) data['temp_data'] = json.encode(data['temp_data']);
        break;
    }
  }

  /// Dispose resources
  void dispose() {
    _deltaTimer?.cancel();
    _statusController.close();
    _httpClient.close();
    print('🔒 Sync manager disposed');
  }
}