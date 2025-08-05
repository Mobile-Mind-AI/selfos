import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/object_managers/goal_manager.dart';
import '../services/auth_provider.dart';

/// Goal state management using offline-first GoalManager
class GoalState {
  final List<Map<String, dynamic>> goals;
  final bool isLoading;
  final String? error;

  const GoalState({
    this.goals = const [],
    this.isLoading = false,
    this.error,
  });

  GoalState copyWith({
    List<Map<String, dynamic>>? goals,
    bool? isLoading,
    String? error,
  }) {
    return GoalState(
      goals: goals ?? this.goals,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

/// Goal provider using offline-first GoalManager
class GoalNotifier extends StateNotifier<GoalState> {
  GoalNotifier(this._ref) : super(const GoalState());

  final Ref _ref;
  final GoalManager _goalManager = GoalManager.instance;

  /// Load goals for current user
  Future<void> loadGoals() async {
    if (state.isLoading) return;

    state = state.copyWith(isLoading: true, error: null);

    try {
      final user = _ref.read(currentUserProvider);
      if (user?.uid == null) {
        throw Exception('No authenticated user');
      }

      final goals = await _goalManager.getByUserId(user!.uid);
      state = state.copyWith(
        goals: goals,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Create a new goal
  Future<bool> createGoal({
    required String title,
    String? description,
    DateTime? targetDate,
    String? lifeAreaId,
    String priority = 'medium',
  }) async {
    try {
      final user = _ref.read(currentUserProvider);
      if (user?.uid == null) return false;

      final goal = await _goalManager.create(
        userId: user!.uid,
        title: title,
        description: description,
        targetDate: targetDate?.toIso8601String(),
        lifeAreaId: lifeAreaId,
      );

      // Add to local state optimistically
      state = state.copyWith(
        goals: [...state.goals, goal],
      );

      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// Update an existing goal
  Future<bool> updateGoal(String goalId, Map<String, dynamic> updates) async {
    try {
      final updatedGoal = await _goalManager.update(goalId, updates);
      
      // Update local state
      final updatedGoals = state.goals.map((goal) {
        if (goal['id'] == goalId) {
          return updatedGoal;
        }
        return goal;
      }).toList();

      state = state.copyWith(goals: updatedGoals);
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// Delete a goal
  Future<bool> deleteGoal(String goalId) async {
    try {
      await _goalManager.delete(goalId);
      
      // Remove from local state
      final updatedGoals = state.goals.where((goal) => goal['id'] != goalId).toList();
      state = state.copyWith(goals: updatedGoals);
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  /// Mark goal as completed
  Future<bool> completeGoal(String goalId) async {
    return updateGoal(goalId, {
      'status': 'completed',
      'completed_at': DateTime.now().toIso8601String(),
    });
  }

  /// Get goals by status
  List<Map<String, dynamic>> getGoalsByStatus(String status) {
    return state.goals.where((goal) => goal['status'] == status).toList();
  }

  /// Get active goals
  List<Map<String, dynamic>> get activeGoals {
    return getGoalsByStatus('active');
  }

  /// Get completed goals
  List<Map<String, dynamic>> get completedGoals {
    return getGoalsByStatus('completed');
  }

  /// Clear error state
  void clearError() {
    state = state.copyWith(error: null);
  }
}

/// Goal provider instance
final goalProvider = StateNotifierProvider<GoalNotifier, GoalState>((ref) {
  return GoalNotifier(ref);
});

/// Convenience providers for specific goal lists
final activeGoalsProvider = Provider<List<Map<String, dynamic>>>((ref) {
  return ref.watch(goalProvider.select((state) => state.goals.where((goal) => goal['status'] == 'active').toList()));
});

final completedGoalsProvider = Provider<List<Map<String, dynamic>>>((ref) {
  return ref.watch(goalProvider.select((state) => state.goals.where((goal) => goal['status'] == 'completed').toList()));
});