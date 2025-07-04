/// Sync Queue Service for intelligent operation batching and merging
/// 
/// This service implements the core sync logic with:
/// - Smart operation merging (newer replaces older)
/// - Priority-based queuing
/// - Exponential backoff for retries
/// - Leaky bucket rate limiting
/// - Network-aware processing

import 'dart:async';
import 'dart:convert';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:uuid/uuid.dart';
import '../local_database/database_service.dart';
import '../local_database/schemas.dart';

/// Sync operation model
class SyncOperation {
  final String id;
  final String objectId;
  final String objectType;
  final SyncOperationType operation;
  final SyncPriority priority;
  final Map<String, dynamic> data;
  final int version;
  final int retryCount;
  final int maxRetries;
  final DateTime scheduledAt;
  final DateTime createdAt;
  
  SyncOperation({
    required this.id,
    required this.objectId,
    required this.objectType,
    required this.operation,
    required this.priority,
    required this.data,
    required this.version,
    this.retryCount = 0,
    this.maxRetries = 3,
    required this.scheduledAt,
    required this.createdAt,
  });
  
  /// Create from database record
  factory SyncOperation.fromMap(Map<String, dynamic> map) {
    return SyncOperation(
      id: map['id'],
      objectId: map['object_id'],
      objectType: map['object_type'],
      operation: SyncOperationType.values.byName(map['operation']),
      priority: SyncPriority.values.byName(map['priority']),
      data: json.decode(map['data']),
      version: map['version'],
      retryCount: map['retry_count'],
      maxRetries: map['max_retries'],
      scheduledAt: DateTime.parse(map['scheduled_at']),
      createdAt: DateTime.parse(map['created_at']),
    );
  }
  
  /// Convert to database record
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'object_id': objectId,
      'object_type': objectType,
      'operation': operation.name,
      'priority': priority.name,
      'data': json.encode(data),
      'version': version,
      'retry_count': retryCount,
      'max_retries': maxRetries,
      'scheduled_at': scheduledAt.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
    };
  }
  
  /// Create copy with updated retry count
  SyncOperation withRetry() {
    return SyncOperation(
      id: id,
      objectId: objectId,
      objectType: objectType,
      operation: operation,
      priority: priority,
      data: data,
      version: version,
      retryCount: retryCount + 1,
      maxRetries: maxRetries,
      scheduledAt: _calculateBackoffDelay(),
      createdAt: createdAt,
    );
  }
  
  /// Calculate exponential backoff delay
  DateTime _calculateBackoffDelay() {
    const baseDelay = Duration(seconds: 2);
    final backoffMultiplier = [1, 2, 4, 8, 16][retryCount.clamp(0, 4)];
    return DateTime.now().add(baseDelay * backoffMultiplier);
  }
  
  /// Check if operation should be retried
  bool get canRetry => retryCount < maxRetries;
  
  /// Get unique key for operation merging
  String get mergeKey => '$objectType:$objectId';
}

/// Sync operation types
enum SyncOperationType {
  create,
  update,
  delete,
}

/// Sync priority levels
enum SyncPriority {
  low,      // Background updates (e.g., personality tweaks)
  normal,   // Standard operations (e.g., goal updates)
  high,     // Important changes (e.g., assistant creation)
  critical, // User-blocking operations (e.g., onboarding completion)
}

/// Sync queue statistics
class SyncQueueStats {
  final int totalOperations;
  final int pendingOperations;
  final int processingOperations;
  final int failedOperations;
  final Map<String, int> operationsByType;
  final Map<String, int> operationsByPriority;
  final DateTime lastProcessedAt;
  final bool isOnline;
  final bool isProcessing;
  
  SyncQueueStats({
    required this.totalOperations,
    required this.pendingOperations,
    required this.processingOperations,
    required this.failedOperations,
    required this.operationsByType,
    required this.operationsByPriority,
    required this.lastProcessedAt,
    required this.isOnline,
    required this.isProcessing,
  });
}

/// Main sync queue service
class SyncQueueService {
  static SyncQueueService? _instance;
  SyncQueueService._();
  
  static SyncQueueService get instance {
    _instance ??= SyncQueueService._();
    return _instance!;
  }
  
  final LocalDatabaseService _db = LocalDatabaseService.instance;
  final Connectivity _connectivity = Connectivity();
  
  // Processing state
  bool _isProcessing = false;
  Timer? _processingTimer;
  DateTime? _lastProcessedAt;
  
  // Leaky bucket rate limiting
  static const int _bucketCapacity = 20;  // Max operations per batch
  static const int _refillRate = 5;       // Operations per second
  int _currentTokens = _bucketCapacity;
  Timer? _refillTimer;
  
  // Network state
  bool _isOnline = true;
  StreamSubscription<ConnectivityResult>? _connectivitySubscription;
  
  /// Initialize sync queue service
  Future<void> initialize() async {
    print('🔄 Initializing sync queue service...');
    
    // Setup connectivity monitoring
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      _onConnectivityChanged,
    );
    
    // Check initial connectivity
    final connectivityResult = await _connectivity.checkConnectivity();
    _isOnline = connectivityResult != ConnectivityResult.none;
    
    // Setup leaky bucket refill
    _refillTimer = Timer.periodic(
      const Duration(milliseconds: 200), // 5 operations per second
      (_) => _refillTokens(),
    );
    
    // Setup periodic processing
    _startPeriodicProcessing();
    
    print('✅ Sync queue service initialized');
  }
  
  /// Enqueue sync operation with smart merging
  Future<void> enqueue(SyncOperation operation) async {
    print('📤 Enqueueing ${operation.operation.name} for ${operation.objectType}:${operation.objectId}');
    
    try {
      // Check if operation already exists
      final existing = await _getExistingOperation(operation.mergeKey);
      
      if (existing != null) {
        // Merge operations
        final merged = _mergeOperations(existing, operation);
        await _updateOperation(merged);
        print('🔀 Merged operation for ${operation.objectType}:${operation.objectId}');
      } else {
        // Add new operation
        await _addOperation(operation);
        print('➕ Added new operation for ${operation.objectType}:${operation.objectId}');
      }
      
      // Trigger immediate processing for critical operations
      if (operation.priority == SyncPriority.critical) {
        _scheduleImmediateProcessing();
      }
      
    } catch (e) {
      print('❌ Failed to enqueue operation: $e');
      rethrow;
    }
  }
  
  /// Get existing operation by merge key
  Future<SyncOperation?> _getExistingOperation(String mergeKey) async {
    final parts = mergeKey.split(':');
    final objectType = parts[0];
    final objectId = parts[1];
    
    final results = await _db.query(
      SyncQueueSchema.tableName,
      where: 'object_type = ? AND object_id = ?',
      whereArgs: [objectType, objectId],
      limit: 1,
    );
    
    return results.isNotEmpty ? SyncOperation.fromMap(results.first) : null;
  }
  
  /// Add new operation to queue
  Future<void> _addOperation(SyncOperation operation) async {
    await _db.insert(SyncQueueSchema.tableName, operation.toMap());
  }
  
  /// Update existing operation
  Future<void> _updateOperation(SyncOperation operation) async {
    await _db.update(SyncQueueSchema.tableName, operation.toMap(), operation.id);
  }
  
  /// Remove operation from queue
  Future<void> _removeOperation(String operationId) async {
    await _db.delete(SyncQueueSchema.tableName, operationId);
  }
  
  /// Merge two operations for the same object
  SyncOperation _mergeOperations(SyncOperation existing, SyncOperation newOp) {
    // Determine final operation type
    SyncOperationType finalOperation;
    Map<String, dynamic> finalData;
    
    if (existing.operation == SyncOperationType.create && 
        newOp.operation == SyncOperationType.update) {
      // create + update = enhanced create
      finalOperation = SyncOperationType.create;
      finalData = {...existing.data, ...newOp.data};
    } else if (existing.operation == SyncOperationType.update && 
               newOp.operation == SyncOperationType.update) {
      // update + update = merged update
      finalOperation = SyncOperationType.update;
      finalData = {...existing.data, ...newOp.data};
    } else if (newOp.operation == SyncOperationType.delete) {
      // Any operation + delete = delete
      finalOperation = SyncOperationType.delete;
      finalData = newOp.data;
    } else {
      // Default: newer operation takes precedence
      finalOperation = newOp.operation;
      finalData = newOp.data;
    }
    
    // Use higher priority and newer version
    return SyncOperation(
      id: existing.id, // Keep original ID
      objectId: existing.objectId,
      objectType: existing.objectType,
      operation: finalOperation,
      priority: SyncPriority.values[
        existing.priority.index > newOp.priority.index 
          ? existing.priority.index 
          : newOp.priority.index
      ],
      data: finalData,
      version: newOp.version > existing.version ? newOp.version : existing.version,
      retryCount: existing.retryCount, // Keep retry count from existing
      maxRetries: existing.maxRetries,
      scheduledAt: newOp.scheduledAt,
      createdAt: existing.createdAt, // Keep original creation time
    );
  }
  
  /// Start periodic processing
  void _startPeriodicProcessing() {
    _processingTimer = Timer.periodic(
      const Duration(seconds: 3), // Process every 3 seconds
      (_) => _processQueueIfReady(),
    );
  }
  
  /// Schedule immediate processing for critical operations
  void _scheduleImmediateProcessing() {
    if (!_isProcessing && _isOnline) {
      Timer(const Duration(milliseconds: 100), () => _processQueueIfReady());
    }
  }
  
  /// Process queue if conditions are met
  Future<void> _processQueueIfReady() async {
    if (!_isOnline || _isProcessing || _currentTokens <= 0) {
      return;
    }
    
    await processQueue();
  }
  
  /// Process sync queue with intelligent batching
  Future<void> processQueue() async {
    if (_isProcessing || !_isOnline) return;
    
    _isProcessing = true;
    print('🔄 Processing sync queue...');
    
    try {
      // Get next batch of operations
      final operations = await _getNextBatch();
      
      if (operations.isEmpty) {
        print('📭 No operations to process');
        return;
      }
      
      print('📦 Processing batch of ${operations.length} operations');
      
      // Group operations by type for efficient API calls
      final groupedOps = _groupOperationsByType(operations);
      
      // Process each group
      for (final entry in groupedOps.entries) {
        final objectType = entry.key;
        final typeOps = entry.value;
        
        await _processBatch(objectType, typeOps);
      }
      
      _lastProcessedAt = DateTime.now();
      
    } catch (e) {
      print('❌ Error processing sync queue: $e');
    } finally {
      _isProcessing = false;
    }
  }
  
  /// Get next batch of operations to process
  Future<List<SyncOperation>> _getNextBatch() async {
    final availableTokens = _currentTokens.clamp(0, _bucketCapacity);
    
    if (availableTokens <= 0) return [];
    
    // Get operations ordered by priority and scheduled time
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
      limit: availableTokens,
    );
    
    return results.map((r) => SyncOperation.fromMap(r)).toList();
  }
  
  /// Group operations by object type for batching
  Map<String, List<SyncOperation>> _groupOperationsByType(List<SyncOperation> operations) {
    final grouped = <String, List<SyncOperation>>{};
    
    for (final op in operations) {
      grouped.putIfAbsent(op.objectType, () => []).add(op);
    }
    
    return grouped;
  }
  
  /// Process a batch of operations for a specific object type
  Future<void> _processBatch(String objectType, List<SyncOperation> operations) async {
    try {
      print('🔄 Processing ${operations.length} $objectType operations');
      
      // Consume tokens
      _currentTokens -= operations.length;
      
      // Delegate to SyncManager for actual processing
      // The SyncManager will handle the API calls and update operations
      // This method is now just for token management and logging
      print('📤 Batch prepared for SyncManager: $objectType (${operations.length} ops)');
      
    } catch (e) {
      print('❌ Batch processing failed for $objectType: $e');
      
      // Handle failed operations
      for (final op in operations) {
        await _handleFailedOperation(op, e.toString());
      }
    }
  }
  
  /// Handle failed operation with retry logic
  Future<void> _handleFailedOperation(SyncOperation operation, String error) async {
    if (operation.canRetry) {
      // Retry with exponential backoff
      final retryOp = operation.withRetry();
      await _updateOperation(retryOp);
      print('🔄 Scheduled retry for ${operation.objectType}:${operation.objectId} (attempt ${retryOp.retryCount})');
    } else {
      // Max retries reached - remove from queue and log error
      await _removeOperation(operation.id);
      print('❌ Max retries reached for ${operation.objectType}:${operation.objectId}: $error');
    }
  }
  
  /// Refill leaky bucket tokens
  void _refillTokens() {
    if (_currentTokens < _bucketCapacity) {
      _currentTokens = (_currentTokens + 1).clamp(0, _bucketCapacity);
    }
  }
  
  /// Handle connectivity changes
  void _onConnectivityChanged(ConnectivityResult result) {
    final wasOnline = _isOnline;
    _isOnline = result != ConnectivityResult.none;
    
    if (_isOnline && !wasOnline) {
      print('🌐 Network restored - scheduling immediate sync');
      _scheduleImmediateProcessing();
    } else if (!_isOnline && wasOnline) {
      print('📶 Network lost - sync paused');
    }
  }
  
  /// Get sync queue statistics
  Future<SyncQueueStats> getStats() async {
    final total = await _db.query(SyncQueueSchema.tableName);
    final pending = await _db.query(
      SyncQueueSchema.tableName,
      where: 'scheduled_at <= ?',
      whereArgs: [DateTime.now().toIso8601String()],
    );
    
    // Count by type and priority
    final typeCount = <String, int>{};
    final priorityCount = <String, int>{};
    
    for (final op in total) {
      final objectType = op['object_type'] as String;
      final priority = op['priority'] as String;
      
      typeCount[objectType] = (typeCount[objectType] ?? 0) + 1;
      priorityCount[priority] = (priorityCount[priority] ?? 0) + 1;
    }
    
    return SyncQueueStats(
      totalOperations: total.length,
      pendingOperations: pending.length,
      processingOperations: _isProcessing ? _currentTokens : 0,
      failedOperations: 0, // TODO: Track failed operations
      operationsByType: typeCount,
      operationsByPriority: priorityCount,
      lastProcessedAt: _lastProcessedAt ?? DateTime.now(),
      isOnline: _isOnline,
      isProcessing: _isProcessing,
    );
  }
  
  /// Dispose resources
  void dispose() {
    _processingTimer?.cancel();
    _refillTimer?.cancel();
    _connectivitySubscription?.cancel();
    print('🔒 Sync queue service disposed');
  }
}

/// Helper extension for creating sync operations
extension SyncOperationHelper on Object {
  /// Create sync operation for assistant profile
  static SyncOperation createAssistantOperation({
    required String objectId,
    required SyncOperationType operation,
    required Map<String, dynamic> data,
    required int version,
    SyncPriority priority = SyncPriority.normal,
  }) {
    return SyncOperation(
      id: const Uuid().v4(),
      objectId: objectId,
      objectType: AssistantProfileSchema.objectType,
      operation: operation,
      priority: priority,
      data: data,
      version: version,
      scheduledAt: DateTime.now(),
      createdAt: DateTime.now(),
    );
  }
  
  /// Create sync operation for personal profile
  static SyncOperation createPersonalProfileOperation({
    required String objectId,
    required SyncOperationType operation,
    required Map<String, dynamic> data,
    required int version,
    SyncPriority priority = SyncPriority.normal,
  }) {
    return SyncOperation(
      id: const Uuid().v4(),
      objectId: objectId,
      objectType: PersonalProfileSchema.objectType,
      operation: operation,
      priority: priority,
      data: data,
      version: version,
      scheduledAt: DateTime.now(),
      createdAt: DateTime.now(),
    );
  }
  
  /// Create sync operation for any object type
  static SyncOperation createGenericOperation({
    required String objectId,
    required String objectType,
    required SyncOperationType operation,
    required Map<String, dynamic> data,
    required int version,
    SyncPriority priority = SyncPriority.normal,
  }) {
    return SyncOperation(
      id: const Uuid().v4(),
      objectId: objectId,
      objectType: objectType,
      operation: operation,
      priority: priority,
      data: data,
      version: version,
      scheduledAt: DateTime.now(),
      createdAt: DateTime.now(),
    );
  }
}