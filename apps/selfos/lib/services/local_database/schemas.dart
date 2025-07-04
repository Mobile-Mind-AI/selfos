/// Database schemas for offline-first sync architecture
/// 
/// This file contains all table schemas and metadata for local SQLite storage.
/// Each entity includes sync metadata for conflict detection and resolution.

import 'dart:convert';

/// Database configuration and metadata
class DatabaseInfo {
  static const String databaseName = 'selfos_local.db';
  static const int currentVersion = 1;
  
  /// Get all object types that support sync
  static List<String> getAllObjectTypes() {
    return [
      'assistant_profile',
      'personal_profile', 
      'avatar',
      'life_area',
      'goal',
      'project',
      'task',
      'onboarding_state',
    ];
  }
  
  /// Get all CREATE TABLE statements
  static List<String> getAllCreateTableStatements() {
    return [
      AssistantProfileSchema.createTableSql,
      PersonalProfileSchema.createTableSql,
      AvatarSchema.createTableSql,
      LifeAreaSchema.createTableSql,
      GoalSchema.createTableSql,
      ProjectSchema.createTableSql,
      TaskSchema.createTableSql,
      OnboardingStateSchema.createTableSql,
      SyncQueueSchema.createTableSql,
      SyncMetadataSchema.createTableSql,
      ChangeLogSchema.createTableSql,
      ConflictSchema.createTableSql,
    ];
  }
}

/// Common sync status enumeration
enum SyncStatus {
  clean,     // Synchronized with server
  dirty,     // Has local changes needing sync
  syncing,   // Currently being synchronized
  conflict,  // Has conflicts needing resolution
}

/// Base sync metadata fields for all entities
abstract class BaseSyncSchema {
  static const String syncMetadataFields = '''
    version INTEGER NOT NULL DEFAULT 0,
    local_version INTEGER NOT NULL DEFAULT 1,
    last_modified TEXT NOT NULL,
    sync_status TEXT NOT NULL DEFAULT 'dirty',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
  ''';
}

/// Assistant Profile Schema
class AssistantProfileSchema extends BaseSyncSchema {
  static const String tableName = 'assistant_profiles';
  static const String objectType = 'assistant_profile';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      name TEXT NOT NULL,
      description TEXT,
      avatar_url TEXT,
      ai_model TEXT NOT NULL DEFAULT 'gpt-3.5-turbo',
      language TEXT NOT NULL DEFAULT 'en',
      requires_confirmation INTEGER NOT NULL DEFAULT 1,
      is_default INTEGER NOT NULL DEFAULT 0,
      is_public INTEGER NOT NULL DEFAULT 0,
      style TEXT NOT NULL, -- JSON: personality configuration
      dialogue_temperature REAL NOT NULL DEFAULT 0.8,
      intent_temperature REAL NOT NULL DEFAULT 0.3,
      custom_instructions TEXT,
      ${BaseSyncSchema.syncMetadataFields}
    )
  ''';
}

/// Personal Profile Schema (optimized without life area duplication)
class PersonalProfileSchema extends BaseSyncSchema {
  static const String tableName = 'personal_profiles';
  static const String objectType = 'personal_profile';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      preferred_name TEXT,
      avatar_id TEXT,
      current_situation TEXT,
      interests TEXT, -- JSON array
      challenges TEXT, -- JSON array
      aspirations TEXT, -- JSON array
      motivation TEXT,
      work_style TEXT,
      communication_frequency TEXT,
      goal_approach TEXT,
      motivation_style TEXT,
      preferences TEXT, -- JSON object
      custom_answers TEXT, -- JSON object
      selected_life_areas TEXT, -- JSON array of life area IDs (authoritative)
      ${BaseSyncSchema.syncMetadataFields}
    )
  ''';
}

/// Avatar Schema
class AvatarSchema extends BaseSyncSchema {
  static const String tableName = 'avatars';
  static const String objectType = 'avatar';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      filename TEXT NOT NULL,
      original_filename TEXT,
      content_type TEXT NOT NULL,
      file_size INTEGER NOT NULL,
      width INTEGER,
      height INTEGER,
      is_default INTEGER NOT NULL DEFAULT 0,
      upload_status TEXT NOT NULL DEFAULT 'pending', -- pending, uploading, completed, failed
      local_path TEXT, -- Local file path for offline access
      server_url TEXT, -- Server URL after upload
      ${BaseSyncSchema.syncMetadataFields}
    )
  ''';
}

/// Life Area Schema
class LifeAreaSchema extends BaseSyncSchema {
  static const String tableName = 'life_areas';
  static const String objectType = 'life_area';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      name TEXT NOT NULL,
      icon TEXT NOT NULL DEFAULT 'category',
      color TEXT NOT NULL DEFAULT '#6366f1',
      description TEXT,
      keywords TEXT, -- JSON array
      weight REAL NOT NULL DEFAULT 1.0,
      priority_order INTEGER NOT NULL DEFAULT 0,
      is_custom INTEGER NOT NULL DEFAULT 1,
      ${BaseSyncSchema.syncMetadataFields}
    )
  ''';
}

/// Goal Schema
class GoalSchema extends BaseSyncSchema {
  static const String tableName = 'goals';
  static const String objectType = 'goal';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT,
      status TEXT NOT NULL DEFAULT 'active', -- active, completed, paused, archived
      progress REAL NOT NULL DEFAULT 0.0,
      life_area_id TEXT,
      project_id TEXT,
      target_date TEXT, -- ISO date string
      media_attachments TEXT, -- JSON array of media URLs
      ${BaseSyncSchema.syncMetadataFields},
      FOREIGN KEY (life_area_id) REFERENCES life_areas(id),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    )
  ''';
}

/// Project Schema
class ProjectSchema extends BaseSyncSchema {
  static const String tableName = 'projects';
  static const String objectType = 'project';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT,
      status TEXT NOT NULL DEFAULT 'active', -- active, completed, paused, archived
      progress REAL NOT NULL DEFAULT 0.0,
      life_area_id TEXT,
      start_date TEXT, -- ISO date string
      target_date TEXT, -- ISO date string
      completed_date TEXT, -- ISO date string
      ${BaseSyncSchema.syncMetadataFields},
      FOREIGN KEY (life_area_id) REFERENCES life_areas(id)
    )
  ''';
}

/// Task Schema
class TaskSchema extends BaseSyncSchema {
  static const String tableName = 'tasks';
  static const String objectType = 'task';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT,
      status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, cancelled
      progress REAL NOT NULL DEFAULT 0.0,
      goal_id TEXT,
      project_id TEXT,
      life_area_id TEXT,
      due_date TEXT, -- ISO date string
      completed_date TEXT, -- ISO date string
      duration INTEGER, -- Estimated duration in minutes
      dependencies TEXT, -- JSON array of task IDs
      ${BaseSyncSchema.syncMetadataFields},
      FOREIGN KEY (goal_id) REFERENCES goals(id),
      FOREIGN KEY (project_id) REFERENCES projects(id),
      FOREIGN KEY (life_area_id) REFERENCES life_areas(id)
    )
  ''';
}

/// Onboarding State Schema (optimized without duplication)
class OnboardingStateSchema extends BaseSyncSchema {
  static const String tableName = 'onboarding_states';
  static const String objectType = 'onboarding_state';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      current_step INTEGER NOT NULL DEFAULT 1,
      completed_steps TEXT NOT NULL, -- JSON array of completed step numbers
      onboarding_completed INTEGER NOT NULL DEFAULT 0,
      assistant_profile_id TEXT,
      first_goal_id TEXT,
      first_task_id TEXT,
      temp_data TEXT, -- JSON object for temporary form data
      skip_intro INTEGER NOT NULL DEFAULT 0,
      theme_preference TEXT,
      flow_version TEXT NOT NULL DEFAULT 'v2',
      started_at TEXT NOT NULL,
      completed_at TEXT,
      last_activity TEXT NOT NULL,
      ${BaseSyncSchema.syncMetadataFields},
      FOREIGN KEY (assistant_profile_id) REFERENCES assistant_profiles(id),
      FOREIGN KEY (first_goal_id) REFERENCES goals(id),
      FOREIGN KEY (first_task_id) REFERENCES tasks(id)
    )
  ''';
}

/// Sync Queue Schema - for managing pending sync operations
class SyncQueueSchema {
  static const String tableName = 'sync_queue';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      object_id TEXT NOT NULL,
      object_type TEXT NOT NULL,
      operation TEXT NOT NULL, -- create, update, delete
      priority TEXT NOT NULL, -- low, normal, high, critical
      data TEXT NOT NULL, -- JSON object with the data to sync
      version INTEGER NOT NULL,
      retry_count INTEGER NOT NULL DEFAULT 0,
      max_retries INTEGER NOT NULL DEFAULT 3,
      scheduled_at TEXT NOT NULL, -- When to attempt sync
      created_at TEXT NOT NULL
    )
  ''';
}

/// Sync Metadata Schema - for storing sync timestamps and state
class SyncMetadataSchema {
  static const String tableName = 'sync_metadata';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  ''';
}

/// Change Log Schema - for tracking all local changes
class ChangeLogSchema {
  static const String tableName = 'change_log';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      object_id TEXT NOT NULL,
      object_type TEXT NOT NULL,
      operation TEXT NOT NULL, -- create, update, delete
      old_data TEXT, -- JSON object with old data (for updates/deletes)
      new_data TEXT, -- JSON object with new data (for creates/updates)
      timestamp TEXT NOT NULL,
      synced INTEGER NOT NULL DEFAULT 0
    )
  ''';
}

/// Conflict Schema - for storing sync conflicts that need resolution
class ConflictSchema {
  static const String tableName = 'conflicts';
  
  static const String createTableSql = '''
    CREATE TABLE IF NOT EXISTS $tableName (
      id TEXT PRIMARY KEY,
      object_id TEXT NOT NULL,
      object_type TEXT NOT NULL,
      local_data TEXT NOT NULL, -- JSON object with local version
      server_data TEXT NOT NULL, -- JSON object with server version
      local_version INTEGER NOT NULL,
      server_version INTEGER NOT NULL,
      conflict_fields TEXT NOT NULL, -- JSON array of conflicting field names
      resolution_strategy TEXT, -- auto, manual, etc.
      resolved INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL,
      resolved_at TEXT
    )
  ''';
}

/// Helper extension for JSON operations
extension JsonHelpers on Map<String, dynamic> {
  /// Safely encode a field as JSON if it's a complex type
  void encodeField(String key) {
    final value = this[key];
    if (value is List || value is Map) {
      this[key] = json.encode(value);
    }
  }
  
  /// Safely decode a JSON field
  T? decodeField<T>(String key) {
    final value = this[key];
    if (value is String && value.isNotEmpty) {
      try {
        return json.decode(value) as T;
      } catch (e) {
        print('Warning: Failed to decode JSON field $key: $e');
        return null;
      }
    }
    return null;
  }
}

/// Validation helpers
class SchemaValidation {
  /// Validate sync status
  static bool isValidSyncStatus(String status) {
    return SyncStatus.values.any((s) => s.name == status);
  }
  
  /// Validate required fields for an object type
  static List<String> validateRequiredFields(
    String objectType, 
    Map<String, dynamic> data
  ) {
    final errors = <String>[];
    
    // Common required fields
    if (data['id'] == null || (data['id'] as String).isEmpty) {
      errors.add('ID is required');
    }
    
    if (data['user_id'] == null || (data['user_id'] as String).isEmpty) {
      errors.add('User ID is required');
    }
    
    // Object-specific validation
    switch (objectType) {
      case 'assistant_profile':
        if (data['name'] == null || (data['name'] as String).trim().isEmpty) {
          errors.add('Assistant name is required');
        }
        break;
        
      case 'goal':
        if (data['title'] == null || (data['title'] as String).trim().isEmpty) {
          errors.add('Goal title is required');
        }
        break;
        
      case 'task':
        if (data['title'] == null || (data['title'] as String).trim().isEmpty) {
          errors.add('Task title is required');
        }
        break;
        
      case 'project':
        if (data['title'] == null || (data['title'] as String).trim().isEmpty) {
          errors.add('Project title is required');
        }
        break;
        
      case 'life_area':
        if (data['name'] == null || (data['name'] as String).trim().isEmpty) {
          errors.add('Life area name is required');
        }
        break;
    }
    
    return errors;
  }
}