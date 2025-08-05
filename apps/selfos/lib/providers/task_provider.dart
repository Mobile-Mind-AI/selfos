import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/object_managers/task_manager.dart';
import '../services/auth_provider.dart';

/// Task state management using offline-first TaskManager
class TaskState {
  final List<Map<String, dynamic>> tasks;
  final bool isLoading;
  final String? error;

  const TaskState({
    this.tasks = const [],
    this.isLoading = false,
    this.error,
  });

  TaskState copyWith({
    List<Map<String, dynamic>>? tasks,
    bool? isLoading,
    String? error,
  }) {
    return TaskState(
      tasks: tasks ?? this.tasks,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

/// Task provider using offline-first TaskManager
class TaskNotifier extends StateNotifier<TaskState> {
  TaskNotifier(this._ref) : super(const TaskState());

  final Ref _ref;
  final TaskManager _taskManager = TaskManager.instance;

  /// Load tasks for current user
  Future<void> loadTasks() async {
    if (state.isLoading) return;

    state = state.copyWith(isLoading: true, error: null);

    try {
      final user = _ref.read(currentUserProvider);
      if (user?.uid == null) {
        throw Exception('No authenticated user');
      }

      final tasks = await _taskManager.getByUserId(user!.uid);
      state = state.copyWith(
        tasks: tasks,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Create a new task
  Future<bool> createTask({
    required String title,
    String? description,
    String? goalId,
    String? projectId,
    DateTime? dueDate,
    String priority = 'medium',
    String status = 'pending',
  }) async {
    try {
      final user = _ref.read(currentUserProvider);
      if (user?.uid == null) return false;

      final task = await _taskManager.create(
        userId: user!.uid,
        title: title,
        description: description,
        goalId: goalId,
        projectId: projectId,
        dueDate: dueDate,
        priority: priority,
        status: status,
      );

      // Add to local state optimistically
      state = state.copyWith(
        tasks: [...state.tasks, task],
      );

      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// Update an existing task
  Future<bool> updateTask(String taskId, Map<String, dynamic> updates) async {
    try {
      final updatedTask = await _taskManager.update(taskId, updates);
      
      // Update local state
      final updatedTasks = state.tasks.map((task) {
        if (task['id'] == taskId) {
          return updatedTask;
        }
        return task;
      }).toList();

      state = state.copyWith(tasks: updatedTasks);
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// Delete a task
  Future<bool> deleteTask(String taskId) async {
    try {
      await _taskManager.delete(taskId);
      
      // Remove from local state
      final updatedTasks = state.tasks.where((task) => task['id'] != taskId).toList();
      state = state.copyWith(tasks: updatedTasks);
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// Mark task as completed
  Future<bool> completeTask(String taskId) async {
    return updateTask(taskId, {
      'status': 'completed',
      'completed_at': DateTime.now().toIso8601String(),
    });
  }

  /// Mark task as in progress
  Future<bool> startTask(String taskId) async {
    return updateTask(taskId, {
      'status': 'in_progress',
      'started_at': DateTime.now().toIso8601String(),
    });
  }

  /// Get tasks by status
  List<Map<String, dynamic>> getTasksByStatus(String status) {
    return state.tasks.where((task) => task['status'] == status).toList();
  }

  /// Get tasks due today
  List<Map<String, dynamic>> get todayTasks {
    final today = DateTime.now();
    final todayStart = DateTime(today.year, today.month, today.day);
    final todayEnd = todayStart.add(const Duration(days: 1));

    return state.tasks.where((task) {
      if (task['due_date'] == null) return false;
      final dueDate = DateTime.parse(task['due_date']);
      return dueDate.isAfter(todayStart) && dueDate.isBefore(todayEnd);
    }).toList();
  }

  /// Get overdue tasks
  List<Map<String, dynamic>> get overdueTasks {
    final now = DateTime.now();
    return state.tasks.where((task) {
      if (task['due_date'] == null || task['status'] == 'completed') return false;
      final dueDate = DateTime.parse(task['due_date']);
      return dueDate.isBefore(now);
    }).toList();
  }

  /// Get pending tasks
  List<Map<String, dynamic>> get pendingTasks {
    return getTasksByStatus('pending');
  }

  /// Get in progress tasks
  List<Map<String, dynamic>> get inProgressTasks {
    return getTasksByStatus('in_progress');
  }

  /// Get completed tasks
  List<Map<String, dynamic>> get completedTasks {
    return getTasksByStatus('completed');
  }

  /// Get tasks for a specific goal
  List<Map<String, dynamic>> getTasksForGoal(String goalId) {
    return state.tasks.where((task) => task['goal_id'] == goalId).toList();
  }

  /// Clear error state
  void clearError() {
    state = state.copyWith(error: null);
  }
}

/// Task provider instance
final taskProvider = StateNotifierProvider<TaskNotifier, TaskState>((ref) {
  return TaskNotifier(ref);
});

/// Convenience providers for specific task lists
final todayTasksProvider = Provider<List<Map<String, dynamic>>>((ref) {
  final tasks = ref.watch(taskProvider.select((state) => state.tasks));
  final today = DateTime.now();
  final todayStart = DateTime(today.year, today.month, today.day);
  final todayEnd = todayStart.add(const Duration(days: 1));

  return tasks.where((task) {
    if (task['due_date'] == null) return false;
    final dueDate = DateTime.parse(task['due_date']);
    return dueDate.isAfter(todayStart) && dueDate.isBefore(todayEnd);
  }).toList();
});

final pendingTasksProvider = Provider<List<Map<String, dynamic>>>((ref) {
  return ref.watch(taskProvider.select((state) => state.tasks.where((task) => task['status'] == 'pending').toList()));
});

final completedTasksProvider = Provider<List<Map<String, dynamic>>>((ref) {
  return ref.watch(taskProvider.select((state) => state.tasks.where((task) => task['status'] == 'completed').toList()));
});

final overdueTasksProvider = Provider<List<Map<String, dynamic>>>((ref) {
  final tasks = ref.watch(taskProvider.select((state) => state.tasks));
  final now = DateTime.now();
  
  return tasks.where((task) {
    if (task['due_date'] == null || task['status'] == 'completed') return false;
    final dueDate = DateTime.parse(task['due_date']);
    return dueDate.isBefore(now);
  }).toList();
});