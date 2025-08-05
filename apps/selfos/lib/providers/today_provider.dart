import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'goal_provider.dart';
import 'task_provider.dart';
import 'auth_provider.dart';

/// Today dashboard data aggregated from multiple sources
class TodayData {
  final int totalGoals;
  final int activeGoals;
  final int completedGoals;
  final double goalProgress;
  
  final int totalTasks;
  final int todayTasks;
  final int pendingTasks;
  final int completedTasks;
  final int overdueTasks;
  
  final List<Map<String, dynamic>> upcomingTasks;
  final List<Map<String, dynamic>> recentlyCompletedTasks;
  final Map<String, dynamic> weeklyStats;
  
  final bool isLoading;
  final String? error;

  const TodayData({
    this.totalGoals = 0,
    this.activeGoals = 0,
    this.completedGoals = 0,
    this.goalProgress = 0.0,
    this.totalTasks = 0,
    this.todayTasks = 0,
    this.pendingTasks = 0,
    this.completedTasks = 0,
    this.overdueTasks = 0,
    this.upcomingTasks = const [],
    this.recentlyCompletedTasks = const [],
    this.weeklyStats = const {},
    this.isLoading = false,
    this.error,
  });

  TodayData copyWith({
    int? totalGoals,
    int? activeGoals,
    int? completedGoals,
    double? goalProgress,
    int? totalTasks,
    int? todayTasks,
    int? pendingTasks,
    int? completedTasks,
    int? overdueTasks,
    List<Map<String, dynamic>>? upcomingTasks,
    List<Map<String, dynamic>>? recentlyCompletedTasks,
    Map<String, dynamic>? weeklyStats,
    bool? isLoading,
    String? error,
  }) {
    return TodayData(
      totalGoals: totalGoals ?? this.totalGoals,
      activeGoals: activeGoals ?? this.activeGoals,
      completedGoals: completedGoals ?? this.completedGoals,
      goalProgress: goalProgress ?? this.goalProgress,
      totalTasks: totalTasks ?? this.totalTasks,
      todayTasks: todayTasks ?? this.todayTasks,
      pendingTasks: pendingTasks ?? this.pendingTasks,
      completedTasks: completedTasks ?? this.completedTasks,
      overdueTasks: overdueTasks ?? this.overdueTasks,
      upcomingTasks: upcomingTasks ?? this.upcomingTasks,
      recentlyCompletedTasks: recentlyCompletedTasks ?? this.recentlyCompletedTasks,
      weeklyStats: weeklyStats ?? this.weeklyStats,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

/// Today provider that aggregates data from goals and tasks
class TodayNotifier extends StateNotifier<TodayData> {
  TodayNotifier(this._ref) : super(const TodayData());

  final Ref _ref;

  /// Load all today's data
  Future<void> loadTodayData() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      // Load goals and tasks data
      await Future.wait([
        _ref.read(goalProvider.notifier).loadGoals(),
        _ref.read(taskProvider.notifier).loadTasks(),
      ]);

      _calculateTodayStats();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Calculate today's statistics from goals and tasks
  void _calculateTodayStats() {
    final goalState = _ref.read(goalProvider);
    final taskState = _ref.read(taskProvider);

    // Calculate goal statistics
    final goals = goalState.goals;
    final activeGoals = goals.where((g) => g['status'] == 'active').length;
    final completedGoals = goals.where((g) => g['status'] == 'completed').length;
    final goalProgress = goals.isEmpty ? 0.0 : completedGoals / goals.length;

    // Calculate task statistics
    final tasks = taskState.tasks;
    final todayTasks = _ref.read(todayTasksProvider);
    final pendingTasks = _ref.read(pendingTasksProvider);
    final completedTasks = _ref.read(completedTasksProvider);
    final overdueTasks = _ref.read(overdueTasksProvider);

    // Get upcoming tasks (next 3 days, limited to 5 tasks)
    final upcomingTasks = _getUpcomingTasks(tasks);

    // Get recently completed tasks (last 7 days, limited to 3 tasks)
    final recentlyCompleted = _getRecentlyCompletedTasks(tasks);

    // Calculate weekly stats
    final weeklyStats = _calculateWeeklyStats(tasks);

    state = state.copyWith(
      totalGoals: goals.length,
      activeGoals: activeGoals,
      completedGoals: completedGoals,
      goalProgress: goalProgress,
      totalTasks: tasks.length,
      todayTasks: todayTasks.length,
      pendingTasks: pendingTasks.length,
      completedTasks: completedTasks.length,
      overdueTasks: overdueTasks.length,
      upcomingTasks: upcomingTasks,
      recentlyCompletedTasks: recentlyCompleted,
      weeklyStats: weeklyStats,
      isLoading: false,
    );
  }

  /// Get upcoming tasks for the next few days
  List<Map<String, dynamic>> _getUpcomingTasks(List<Map<String, dynamic>> tasks) {
    final now = DateTime.now();
    final threeDaysFromNow = now.add(const Duration(days: 3));

    return tasks
        .where((task) {
          if (task['due_date'] == null || task['status'] == 'completed') return false;
          final dueDate = DateTime.parse(task['due_date']);
          return dueDate.isAfter(now) && dueDate.isBefore(threeDaysFromNow);
        })
        .take(5)
        .toList();
  }

  /// Get recently completed tasks
  List<Map<String, dynamic>> _getRecentlyCompletedTasks(List<Map<String, dynamic>> tasks) {
    final weekAgo = DateTime.now().subtract(const Duration(days: 7));

    return tasks
        .where((task) {
          if (task['completed_at'] == null) return false;
          final completedAt = DateTime.parse(task['completed_at']);
          return completedAt.isAfter(weekAgo);
        })
        .take(3)
        .toList();
  }

  /// Calculate weekly statistics
  Map<String, dynamic> _calculateWeeklyStats(List<Map<String, dynamic>> tasks) {
    final weekAgo = DateTime.now().subtract(const Duration(days: 7));
    
    final thisWeekTasks = tasks.where((task) {
      final createdAt = DateTime.parse(task['created_at']);
      return createdAt.isAfter(weekAgo);
    }).toList();

    final thisWeekCompleted = tasks.where((task) {
      if (task['completed_at'] == null) return false;
      final completedAt = DateTime.parse(task['completed_at']);
      return completedAt.isAfter(weekAgo);
    }).toList();

    return {
      'tasks_created': thisWeekTasks.length,
      'tasks_completed': thisWeekCompleted.length,
      'completion_rate': thisWeekTasks.isEmpty ? 0.0 : thisWeekCompleted.length / thisWeekTasks.length,
      'productivity_trend': _calculateProductivityTrend(tasks),
    };
  }

  /// Calculate productivity trend (simple implementation)
  String _calculateProductivityTrend(List<Map<String, dynamic>> tasks) {
    final thisWeek = DateTime.now().subtract(const Duration(days: 7));
    final lastWeek = DateTime.now().subtract(const Duration(days: 14));

    final thisWeekCompleted = tasks.where((task) {
      if (task['completed_at'] == null) return false;
      final completedAt = DateTime.parse(task['completed_at']);
      return completedAt.isAfter(thisWeek);
    }).length;

    final lastWeekCompleted = tasks.where((task) {
      if (task['completed_at'] == null) return false;
      final completedAt = DateTime.parse(task['completed_at']);
      return completedAt.isAfter(lastWeek) && completedAt.isBefore(thisWeek);
    }).length;

    if (thisWeekCompleted > lastWeekCompleted) return 'up';
    if (thisWeekCompleted < lastWeekCompleted) return 'down';
    return 'stable';
  }

  /// Refresh all data
  Future<void> refresh() async {
    await loadTodayData();
  }

  /// Clear error state
  void clearError() {
    state = state.copyWith(error: null);
  }
}

/// Today provider instance
final todayProvider = StateNotifierProvider<TodayNotifier, TodayData>((ref) {
  return TodayNotifier(ref);
});

/// Auto-refresh today data when goals or tasks change
final todayAutoRefreshProvider = Provider((ref) {
  // Watch for changes in goals and tasks
  ref.listen(goalProvider, (previous, next) {
    if (previous?.goals != next.goals) {
      ref.read(todayProvider.notifier)._calculateTodayStats();
    }
  });

  ref.listen(taskProvider, (previous, next) {
    if (previous?.tasks != next.tasks) {
      ref.read(todayProvider.notifier)._calculateTodayStats();
    }
  });

  return ref.watch(todayProvider);
});