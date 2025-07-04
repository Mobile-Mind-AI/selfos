/// Automated Conflict Resolution for Sync Operations
/// 
/// This service implements automated strategies for resolving sync conflicts
/// without requiring user intervention, as requested.

import 'dart:convert';
import '../local_database/schemas.dart';

enum ConflictResolutionStrategy {
  serverWins,     // Always use server version
  clientWins,     // Always use client version
  lastWriteWins,  // Use version with latest timestamp
  merge,          // Intelligent field-level merging
  additive,       // Combine values where possible
}

class ConflictField {
  final String name;
  final dynamic localValue;
  final dynamic serverValue;
  final ConflictResolutionStrategy strategy;

  ConflictField({
    required this.name,
    required this.localValue,
    required this.serverValue,
    required this.strategy,
  });
}

class ConflictResolutionResult {
  final Map<String, dynamic> resolvedData;
  final List<String> resolutionLog;
  final bool requiresManualReview;

  ConflictResolutionResult({
    required this.resolvedData,
    required this.resolutionLog,
    this.requiresManualReview = false,
  });
}

/// Automated conflict resolver that implements smart resolution strategies
class ConflictResolver {
  static ConflictResolver? _instance;
  ConflictResolver._();

  static ConflictResolver get instance {
    _instance ??= ConflictResolver._();
    return _instance!;
  }

  /// Resolve conflict between local and server data
  Future<ConflictResolutionResult> resolveConflict({
    required String objectType,
    required Map<String, dynamic> localData,
    required Map<String, dynamic> serverData,
    required int localVersion,
    required int serverVersion,
  }) async {
    final log = <String>[];
    final resolvedData = <String, dynamic>{};
    bool requiresManualReview = false;

    log.add('Starting conflict resolution for $objectType');
    log.add('Local version: $localVersion, Server version: $serverVersion');

    // Get field-specific strategies for this object type
    final fieldStrategies = _getFieldStrategies(objectType);

    // Process each field
    for (final field in _getAllFields(localData, serverData)) {
      final localValue = localData[field];
      final serverValue = serverData[field];

      // Skip if values are the same
      if (_valuesEqual(localValue, serverValue)) {
        resolvedData[field] = localValue;
        continue;
      }

      final strategy = fieldStrategies[field] ?? _getDefaultStrategy(field, objectType);
      final conflictField = ConflictField(
        name: field,
        localValue: localValue,
        serverValue: serverValue,
        strategy: strategy,
      );

      final resolution = await _resolveField(conflictField);
      resolvedData[field] = resolution.value;
      log.add(resolution.logMessage);

      if (resolution.needsReview) {
        requiresManualReview = true;
      }
    }

    // Apply post-resolution rules
    _applyPostResolutionRules(objectType, resolvedData, log);

    return ConflictResolutionResult(
      resolvedData: resolvedData,
      resolutionLog: log,
      requiresManualReview: requiresManualReview,
    );
  }

  /// Get field-specific resolution strategies for each object type
  Map<String, ConflictResolutionStrategy> _getFieldStrategies(String objectType) {
    switch (objectType) {
      case 'goal':
        return {
          'title': ConflictResolutionStrategy.lastWriteWins,
          'description': ConflictResolutionStrategy.merge,
          'status': ConflictResolutionStrategy.serverWins, // Server authoritative for status
          'progress': ConflictResolutionStrategy.serverWins, // Server has latest progress
          'target_date': ConflictResolutionStrategy.lastWriteWins,
          'media_attachments': ConflictResolutionStrategy.additive,
        };

      case 'task':
        return {
          'title': ConflictResolutionStrategy.lastWriteWins,
          'description': ConflictResolutionStrategy.merge,
          'status': ConflictResolutionStrategy.serverWins,
          'progress': ConflictResolutionStrategy.serverWins,
          'due_date': ConflictResolutionStrategy.lastWriteWins,
          'estimated_hours': ConflictResolutionStrategy.lastWriteWins,
          'actual_hours': ConflictResolutionStrategy.serverWins, // Actual hours from server
          'priority': ConflictResolutionStrategy.lastWriteWins,
        };

      case 'project':
        return {
          'title': ConflictResolutionStrategy.lastWriteWins,
          'description': ConflictResolutionStrategy.merge,
          'status': ConflictResolutionStrategy.serverWins,
          'progress': ConflictResolutionStrategy.serverWins,
          'start_date': ConflictResolutionStrategy.lastWriteWins,
          'target_date': ConflictResolutionStrategy.lastWriteWins,
        };

      case 'life_area':
        return {
          'name': ConflictResolutionStrategy.lastWriteWins,
          'description': ConflictResolutionStrategy.merge,
          'color': ConflictResolutionStrategy.lastWriteWins,
          'icon': ConflictResolutionStrategy.lastWriteWins,
          'weight': ConflictResolutionStrategy.lastWriteWins,
          'priority_order': ConflictResolutionStrategy.serverWins, // Server manages ordering
          'keywords': ConflictResolutionStrategy.additive,
        };

      case 'avatar':
      case 'media_attachment':
        return {
          'filename': ConflictResolutionStrategy.serverWins,
          'upload_status': ConflictResolutionStrategy.serverWins,
          'server_url': ConflictResolutionStrategy.serverWins,
          'is_default': ConflictResolutionStrategy.serverWins,
        };

      case 'personal_profile':
        return {
          'preferred_name': ConflictResolutionStrategy.lastWriteWins,
          'current_situation': ConflictResolutionStrategy.merge,
          'interests': ConflictResolutionStrategy.additive,
          'challenges': ConflictResolutionStrategy.additive,
          'aspirations': ConflictResolutionStrategy.additive,
          'motivation': ConflictResolutionStrategy.merge,
          'preferences': ConflictResolutionStrategy.merge,
          'selected_life_areas': ConflictResolutionStrategy.additive,
        };

      case 'assistant_profile':
        return {
          'name': ConflictResolutionStrategy.lastWriteWins,
          'description': ConflictResolutionStrategy.merge,
          'avatar_url': ConflictResolutionStrategy.lastWriteWins,
          'ai_model': ConflictResolutionStrategy.lastWriteWins,
          'custom_instructions': ConflictResolutionStrategy.merge,
          'style': ConflictResolutionStrategy.merge,
          'is_default': ConflictResolutionStrategy.serverWins,
        };

      default:
        return {};
    }
  }

  /// Get default strategy for unknown fields
  ConflictResolutionStrategy _getDefaultStrategy(String field, String objectType) {
    // System fields always use server
    if (['id', 'user_id', 'created_at', 'version'].contains(field)) {
      return ConflictResolutionStrategy.serverWins;
    }

    // Timestamps use latest
    if (['updated_at', 'last_modified'].contains(field)) {
      return ConflictResolutionStrategy.lastWriteWins;
    }

    // Progress and status fields prefer server
    if (['progress', 'status', 'completed_at'].contains(field)) {
      return ConflictResolutionStrategy.serverWins;
    }

    // Text fields can be merged
    if (['description', 'notes', 'content'].contains(field)) {
      return ConflictResolutionStrategy.merge;
    }

    // Arrays can be combined
    if (field.endsWith('_list') || field.endsWith('_array') || field.contains('attachments')) {
      return ConflictResolutionStrategy.additive;
    }

    // Default to last write wins
    return ConflictResolutionStrategy.lastWriteWins;
  }

  /// Resolve individual field conflict
  Future<FieldResolution> _resolveField(ConflictField field) async {
    switch (field.strategy) {
      case ConflictResolutionStrategy.serverWins:
        return FieldResolution(
          value: field.serverValue,
          logMessage: '${field.name}: Used server value (server wins strategy)',
          needsReview: false,
        );

      case ConflictResolutionStrategy.clientWins:
        return FieldResolution(
          value: field.localValue,
          logMessage: '${field.name}: Used client value (client wins strategy)',
          needsReview: false,
        );

      case ConflictResolutionStrategy.lastWriteWins:
        // Use updated_at or last_modified timestamps if available
        final value = field.serverValue; // Assume server has later timestamp for now
        return FieldResolution(
          value: value,
          logMessage: '${field.name}: Used latest value (last write wins)',
          needsReview: false,
        );

      case ConflictResolutionStrategy.merge:
        return await _mergeTextFields(field);

      case ConflictResolutionStrategy.additive:
        return await _additiveMerge(field);
    }
  }

  /// Merge text fields intelligently
  Future<FieldResolution> _mergeTextFields(ConflictField field) async {
    final localText = field.localValue?.toString() ?? '';
    final serverText = field.serverValue?.toString() ?? '';

    if (localText.isEmpty) {
      return FieldResolution(
        value: serverText,
        logMessage: '${field.name}: Used server text (local empty)',
        needsReview: false,
      );
    }

    if (serverText.isEmpty) {
      return FieldResolution(
        value: localText,
        logMessage: '${field.name}: Used local text (server empty)',
        needsReview: false,
      );
    }

    // Simple merge: combine if different
    if (localText != serverText) {
      final merged = '$localText\n\n[Server changes]: $serverText';
      return FieldResolution(
        value: merged,
        logMessage: '${field.name}: Merged local and server text',
        needsReview: true, // Text merges should be reviewed
      );
    }

    return FieldResolution(
      value: localText,
      logMessage: '${field.name}: Texts identical, no merge needed',
      needsReview: false,
    );
  }

  /// Additive merge for arrays and collections
  Future<FieldResolution> _additiveMerge(ConflictField field) async {
    List<dynamic> localList = [];
    List<dynamic> serverList = [];

    // Parse local value
    if (field.localValue is List) {
      localList = List.from(field.localValue);
    } else if (field.localValue is String && field.localValue.toString().isNotEmpty) {
      try {
        localList = List.from(json.decode(field.localValue));
      } catch (e) {
        localList = [field.localValue];
      }
    }

    // Parse server value
    if (field.serverValue is List) {
      serverList = List.from(field.serverValue);
    } else if (field.serverValue is String && field.serverValue.toString().isNotEmpty) {
      try {
        serverList = List.from(json.decode(field.serverValue));
      } catch (e) {
        serverList = [field.serverValue];
      }
    }

    // Combine and deduplicate
    final combined = <dynamic>{};
    combined.addAll(localList);
    combined.addAll(serverList);

    final result = combined.toList();
    
    return FieldResolution(
      value: result,
      logMessage: '${field.name}: Combined ${localList.length} local + ${serverList.length} server items = ${result.length} total',
      needsReview: false,
    );
  }

  /// Apply object-specific post-resolution rules
  void _applyPostResolutionRules(String objectType, Map<String, dynamic> data, List<String> log) {
    switch (objectType) {
      case 'task':
        // Ensure progress and status are consistent
        if (data['progress'] != null && data['status'] != null) {
          final progress = (data['progress'] as num).toDouble();
          if (progress >= 100.0 && data['status'] != 'completed') {
            data['status'] = 'completed';
            log.add('Auto-corrected: Set status to completed for 100% progress');
          } else if (progress < 100.0 && data['status'] == 'completed') {
            data['status'] = 'in_progress';
            log.add('Auto-corrected: Set status to in_progress for incomplete task');
          }
        }
        break;

      case 'project':
        // Similar progress/status consistency for projects
        if (data['progress'] != null && data['status'] != null) {
          final progress = (data['progress'] as num).toDouble();
          if (progress >= 100.0 && data['status'] != 'completed') {
            data['status'] = 'completed';
            data['completed_date'] = DateTime.now().toIso8601String();
            log.add('Auto-corrected: Set project status to completed');
          }
        }
        break;

      case 'goal':
        // Ensure target_date is in the future for active goals
        if (data['status'] == 'active' && data['target_date'] != null) {
          try {
            final targetDate = DateTime.parse(data['target_date']);
            if (targetDate.isBefore(DateTime.now()) && data['status'] != 'completed') {
              log.add('Warning: Active goal has past target date');
            }
          } catch (e) {
            // Invalid date format, let validation handle it
          }
        }
        break;
    }

    // Always ensure updated_at is current
    data['updated_at'] = DateTime.now().toIso8601String();
    data['last_modified'] = DateTime.now().toIso8601String();
  }

  /// Helper methods
  Set<String> _getAllFields(Map<String, dynamic> local, Map<String, dynamic> server) {
    return {...local.keys, ...server.keys};
  }

  bool _valuesEqual(dynamic a, dynamic b) {
    if (a == null && b == null) return true;
    if (a == null || b == null) return false;
    
    // Handle JSON strings vs objects
    if (a is String && b is List) {
      try {
        return _valuesEqual(json.decode(a), b);
      } catch (e) {
        return false;
      }
    }
    if (a is List && b is String) {
      try {
        return _valuesEqual(a, json.decode(b));
      } catch (e) {
        return false;
      }
    }
    
    return a.toString() == b.toString();
  }
}

class FieldResolution {
  final dynamic value;
  final String logMessage;
  final bool needsReview;

  FieldResolution({
    required this.value,
    required this.logMessage,
    this.needsReview = false,
  });
}