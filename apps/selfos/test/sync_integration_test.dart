/// Comprehensive multi-entity sync integration tests
/// 
/// Tests the complete offline-first sync architecture across all CRUD entities:
/// - Project, Task, Life Area, and Media Attachment managers
/// - Automated conflict resolution
/// - Cross-entity relationships and dependencies
/// - Real-world sync scenarios

import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import '../lib/services/local_database/database_service.dart';
import '../lib/services/object_managers/project_manager.dart';
import '../lib/services/object_managers/task_manager.dart';
import '../lib/services/object_managers/life_area_manager.dart';
import '../lib/services/object_managers/media_attachment_manager.dart';
import '../lib/services/sync/sync_queue.dart';
import '../lib/services/sync/sync_manager.dart';
import '../lib/services/sync/conflict_resolver.dart';

void main() {
  group('Multi-Entity Sync Integration Tests', () {
    late DatabaseService dbService;
    late ProjectManager projectManager;
    late TaskManager taskManager;
    late LifeAreaManager lifeAreaManager;
    late MediaAttachmentManager mediaManager;
    late SyncQueueService syncQueue;
    late ConflictResolver conflictResolver;

    const testUserId = 'test-user-123';

    setUpAll(() {
      // Initialize FFI for testing
      sqfliteFfiInit();
      databaseFactory = databaseFactoryFfi;
    });

    setUp(() async {
      // Initialize services
      dbService = LocalDatabaseService.instance;
      await dbService.initialize(':memory:'); // In-memory database for tests

      projectManager = ProjectManager.instance;
      taskManager = TaskManager.instance;
      lifeAreaManager = LifeAreaManager.instance;
      mediaManager = MediaAttachmentManager.instance;
      syncQueue = SyncQueueService.instance;
      conflictResolver = ConflictResolver.instance;

      await syncQueue.initialize();
    });

    tearDown(() async {
      await dbService.close();
    });

    test('Create complete project hierarchy with sync', () async {
      // Create life area
      final lifeArea = await lifeAreaManager.create(
        userId: testUserId,
        name: 'Career Development',
        description: 'Professional growth and skill building',
        color: '#4F46E5',
        icon: 'work',
        weight: 8.0,
      );

      // Create project in life area
      final project = await projectManager.create(
        userId: testUserId,
        title: 'Flutter Mastery',
        description: 'Learn advanced Flutter development',
        lifeAreaId: lifeArea['id'],
        targetDate: DateTime.now().add(const Duration(days: 90)),
      );

      // Create tasks for project
      final task1 = await taskManager.create(
        userId: testUserId,
        title: 'Complete Flutter course',
        description: 'Finish the advanced Flutter course on platform X',
        projectId: project['id'],
        lifeAreaId: lifeArea['id'],
        priority: 'high',
        estimatedHours: 40.0,
        dueDate: DateTime.now().add(const Duration(days: 30)),
      );

      final task2 = await taskManager.create(
        userId: testUserId,
        title: 'Build portfolio app',
        description: 'Create a showcase app using learned concepts',
        projectId: project['id'],
        lifeAreaId: lifeArea['id'],
        priority: 'medium',
        estimatedHours: 60.0,
        dependsOnTaskId: task1['id'],
        dueDate: DateTime.now().add(const Duration(days: 60)),
      );

      // Verify sync queue has operations
      final stats = await syncQueue.getStats();
      expect(stats.pendingOperations, greaterThan(0));
      expect(stats.operationsByType['life_area'], equals(1));
      expect(stats.operationsByType['project'], equals(1));
      expect(stats.operationsByType['task'], equals(2));

      print('✅ Created complete project hierarchy with ${stats.pendingOperations} sync operations');
    });

    test('Cross-entity relationship integrity during sync', () async {
      // Create entities with relationships
      final lifeArea = await lifeAreaManager.create(
        userId: testUserId,
        name: 'Health & Fitness',
        color: '#10B981',
      );

      final project = await projectManager.create(
        userId: testUserId,
        title: 'Marathon Training',
        lifeAreaId: lifeArea['id'],
      );

      final task = await taskManager.create(
        userId: testUserId,
        title: 'Weekly long run',
        projectId: project['id'],
        lifeAreaId: lifeArea['id'],
      );

      // Update project progress - should cascade properly
      await projectManager.updateProgress(project['id'], 25.0);
      await taskManager.updateProgress(task['id'], 50.0);

      // Verify relationships are maintained
      final updatedProject = await projectManager.getById(project['id']);
      final updatedTask = await taskManager.getById(task['id']);

      expect(updatedProject?['life_area_id'], equals(lifeArea['id']));
      expect(updatedTask?['project_id'], equals(project['id']));
      expect(updatedTask?['life_area_id'], equals(lifeArea['id']));

      // Verify sync operations maintain relationships
      final projectOps = await syncQueue.getOperationsForObject(project['id']);
      final taskOps = await syncQueue.getOperationsForObject(task['id']);

      expect(projectOps.isNotEmpty, isTrue);
      expect(taskOps.isNotEmpty, isTrue);

      print('✅ Cross-entity relationships maintained during sync');
    });

    test('Media attachment (avatar) sync workflow', () async {
      // Create avatar attachment
      final avatar = await mediaManager.create(
        userId: testUserId,
        filename: 'profile_pic.jpg',
        contentType: 'image/jpeg',
        fileSize: 2048576, // 2MB
        width: 800,
        height: 800,
        isDefault: true,
        localPath: '/tmp/profile_pic.jpg',
      );

      // Update upload status
      await mediaManager.updateUploadStatus(
        avatar['id'],
        'completed',
        serverUrl: 'https://cdn.example.com/avatars/profile_pic.jpg',
      );

      // Create another avatar and test default switching
      final avatar2 = await mediaManager.create(
        userId: testUserId,
        filename: 'new_avatar.png',
        contentType: 'image/png',
        fileSize: 1024768,
        localPath: '/tmp/new_avatar.png',
      );

      await mediaManager.setAsDefault(avatar2['id'], testUserId);

      // Verify only one default avatar
      final defaultAvatars = await mediaManager.getDefaultAvatars(testUserId);
      expect(defaultAvatars.length, equals(1));
      expect(defaultAvatars.first['id'], equals(avatar2['id']));

      // Check sync queue for avatar operations
      final stats = await syncQueue.getStats();
      expect(stats.operationsByType['avatar'], greaterThan(0));

      print('✅ Avatar/media attachment sync workflow complete');
    });

    test('Automated conflict resolution scenarios', () async {
      // Create a task locally
      final task = await taskManager.create(
        userId: testUserId,
        title: 'Learn Dart fundamentals',
        description: 'Study Dart language basics',
        progress: 30.0,
        status: 'in_progress',
      );

      // Simulate server data with conflicts
      final localData = {
        'title': 'Learn Dart fundamentals',
        'description': 'Study Dart language basics and advanced features', // Local change
        'progress': 45.0, // Local progress
        'status': 'in_progress',
        'updated_at': DateTime.now().subtract(const Duration(minutes: 5)).toIso8601String(),
      };

      final serverData = {
        'title': 'Learn Dart fundamentals',
        'description': 'Study Dart language syntax', // Server change
        'progress': 60.0, // Server progress (higher)
        'status': 'completed', // Server completed
        'updated_at': DateTime.now().toIso8601String(),
      };

      // Test conflict resolution
      final resolution = await conflictResolver.resolveConflict(
        objectType: 'task',
        localData: localData,
        serverData: serverData,
        localVersion: 1,
        serverVersion: 2,
      );

      // Verify resolution strategies applied
      expect(resolution.resolvedData['progress'], equals(60.0)); // Server wins for progress
      expect(resolution.resolvedData['status'], equals('completed')); // Server wins for status
      expect(resolution.resolvedData['description'], contains('advanced features')); // Merged description
      expect(resolution.requiresManualReview, isFalse); // Should auto-resolve

      print('✅ Automated conflict resolution: ${resolution.resolutionLog.length} operations');
      for (final log in resolution.resolutionLog) {
        print('   - $log');
      }
    });

    test('Complex conflict with manual review required', () async {
      // Create conflicting data that requires manual review
      final localData = {
        'title': 'Important Project Meeting',
        'description': 'Discuss quarterly goals and budget allocation',
        'status': 'active',
        'progress': 0.0,
      };

      final serverData = {
        'title': 'Critical Project Meeting', // Significant title change
        'description': 'Review project timeline and resource requirements',
        'status': 'paused', // Different status
        'progress': 0.0,
      };

      final resolution = await conflictResolver.resolveConflict(
        objectType: 'project',
        localData: localData,
        serverData: serverData,
        localVersion: 2,
        serverVersion: 3,
      );

      // This should require manual review due to significant differences
      expect(resolution.requiresManualReview, isTrue);
      expect(resolution.resolvedData['description'], contains('quarterly goals'));
      expect(resolution.resolvedData['description'], contains('timeline'));

      print('⚠️ Complex conflict requires manual review');
      print('   Resolved description: ${resolution.resolvedData['description']}');
    });

    test('Batch sync performance with multiple entity types', () async {
      final stopwatch = Stopwatch()..start();

      // Create multiple entities quickly
      for (int i = 0; i < 5; i++) {
        final lifeArea = await lifeAreaManager.create(
          userId: testUserId,
          name: 'Life Area $i',
          color: '#${(i * 111111).toRadixString(16).padLeft(6, '0')}',
        );

        final project = await projectManager.create(
          userId: testUserId,
          title: 'Project $i',
          lifeAreaId: lifeArea['id'],
        );

        for (int j = 0; j < 3; j++) {
          await taskManager.create(
            userId: testUserId,
            title: 'Task $i.$j',
            projectId: project['id'],
            lifeAreaId: lifeArea['id'],
          );
        }

        if (i % 2 == 0) {
          await mediaManager.create(
            userId: testUserId,
            filename: 'image_$i.jpg',
            contentType: 'image/jpeg',
            fileSize: 1024 * 1024,
          );
        }
      }

      stopwatch.stop();

      // Verify sync queue efficiency
      final stats = await syncQueue.getStats();
      expect(stats.pendingOperations, equals(5 + 5 + 15 + 3)); // life_areas + projects + tasks + avatars
      expect(stats.operationsByType.keys.length, greaterThan(3)); // Multiple entity types

      print('✅ Created ${stats.pendingOperations} entities in ${stopwatch.elapsedMilliseconds}ms');
      print('   Operations by type: ${stats.operationsByType}');
    });

    test('Sync queue operation merging and optimization', () async {
      // Create and update same entity multiple times
      final project = await projectManager.create(
        userId: testUserId,
        title: 'Test Project',
        description: 'Initial description',
      );

      // Make multiple updates
      await projectManager.update(project['id'], {'description': 'Updated description 1'});
      await projectManager.update(project['id'], {'description': 'Updated description 2'});
      await projectManager.update(project['id'], {'progress': 25.0});
      await projectManager.update(project['id'], {'description': 'Final description', 'progress': 50.0});

      // Check if operations were merged efficiently
      final projectOps = await syncQueue.getOperationsForObject(project['id']);
      
      // Should have create + merged updates, not 5 separate operations
      expect(projectOps.length, lessThan(5));
      
      // Final operation should have latest data
      final latestOp = projectOps.last;
      expect(latestOp.data['description'], equals('Final description'));
      expect(latestOp.data['progress'], equals(50.0));

      print('✅ Operation merging: ${projectOps.length} operations for 5 updates');
    });

    test('Data consistency during concurrent operations', () async {
      // Test concurrent modifications
      final lifeArea = await lifeAreaManager.create(
        userId: testUserId,
        name: 'Concurrent Test Area',
      );

      // Simulate concurrent updates
      final futures = <Future>[];
      
      for (int i = 0; i < 10; i++) {
        futures.add(
          lifeAreaManager.update(lifeArea['id'], {
            'weight': (i + 1).toDouble(),
            'priority_order': i,
          })
        );
      }

      await Future.wait(futures);

      // Verify final state is consistent
      final finalLifeArea = await lifeAreaManager.getById(lifeArea['id']);
      expect(finalLifeArea?['weight'], isA<double>());
      expect(finalLifeArea?['priority_order'], isA<int>());

      // Check sync status
      expect(finalLifeArea?['sync_status'], equals('dirty'));
      expect(finalLifeArea?['local_version'], greaterThan(1));

      print('✅ Data consistency maintained during concurrent operations');
      print('   Final weight: ${finalLifeArea?['weight']}, priority: ${finalLifeArea?['priority_order']}');
    });
  });
}