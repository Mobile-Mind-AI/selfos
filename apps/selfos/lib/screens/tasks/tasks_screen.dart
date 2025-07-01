import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Tasks management screen
class TasksScreen extends ConsumerStatefulWidget {
  const TasksScreen({super.key});

  @override
  ConsumerState<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends ConsumerState<TasksScreen> with TickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) {
          return [
            SliverAppBar(
              floating: true,
              title: const Text('Tasks'),
              automaticallyImplyLeading: false,
              actions: [
                IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: () {
                    // TODO: Implement search
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.filter_list),
                  onPressed: () {
                    // TODO: Show filter options
                  },
                ),
              ],
              bottom: TabBar(
                controller: _tabController,
                tabs: const [
                  Tab(text: 'Today'),
                  Tab(text: 'Pending'),
                  Tab(text: 'Completed'),
                ],
              ),
            ),
          ];
        },
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildTodayTasks(),
            _buildPendingTasks(),
            _buildCompletedTasks(),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddTaskDialog(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildTodayTasks() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildTaskCard(
          'Review project proposal',
          'Go through the new client proposal and provide feedback',
          'High',
          'Work',
          false,
          DateTime.now(),
        ),
        const SizedBox(height: 12),
        _buildTaskCard(
          'Morning workout',
          '30-minute cardio session',
          'Medium',
          'Health',
          true,
          DateTime.now(),
        ),
        const SizedBox(height: 12),
        _buildTaskCard(
          'Call client about meeting',
          'Schedule follow-up meeting for next week',
          'High',
          'Work',
          false,
          DateTime.now(),
        ),
        const SizedBox(height: 12),
        _buildTaskCard(
          'Buy groceries',
          'Weekly grocery shopping for meal prep',
          'Low',
          'Personal',
          false,
          DateTime.now(),
        ),
      ],
    );
  }

  Widget _buildPendingTasks() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildTaskCard(
          'Finish Flutter tutorial',
          'Complete the advanced Flutter course sections',
          'Medium',
          'Learning',
          false,
          DateTime.now().add(const Duration(days: 1)),
        ),
        const SizedBox(height: 12),
        _buildTaskCard(
          'Plan weekend trip',
          'Research and book accommodation for weekend getaway',
          'Low',
          'Personal',
          false,
          DateTime.now().add(const Duration(days: 3)),
        ),
        const SizedBox(height: 12),
        _buildTaskCard(
          'Update resume',
          'Add recent projects and skills to resume',
          'Medium',
          'Career',
          false,
          DateTime.now().add(const Duration(days: 7)),
        ),
      ],
    );
  }

  Widget _buildCompletedTasks() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildTaskCard(
          'Setup development environment',
          'Install and configure all necessary development tools',
          'High',
          'Work',
          true,
          DateTime.now().subtract(const Duration(days: 1)),
        ),
        const SizedBox(height: 12),
        _buildTaskCard(
          'Read daily news',
          'Stay updated with current events',
          'Low',
          'Personal',
          true,
          DateTime.now().subtract(const Duration(hours: 2)),
        ),
        const SizedBox(height: 12),
        _buildTaskCard(
          'Water plants',
          'Daily plant care routine',
          'Low',
          'Home',
          true,
          DateTime.now().subtract(const Duration(hours: 1)),
        ),
      ],
    );
  }

  Widget _buildTaskCard(
    String title,
    String description,
    String priority,
    String category,
    bool isCompleted,
    DateTime dueDate,
  ) {
    final theme = Theme.of(context);
    final priorityColor = _getPriorityColor(priority);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Checkbox(
                  value: isCompleted,
                  onChanged: (value) {
                    // TODO: Toggle task completion
                  },
                ),
                Expanded(
                  child: Text(
                    title,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      decoration: isCompleted ? TextDecoration.lineThrough : null,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: priorityColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    priority,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: priorityColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.only(left: 48),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    description,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.7),
                      decoration: isCompleted ? TextDecoration.lineThrough : null,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.secondaryContainer,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          category,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSecondaryContainer,
                          ),
                        ),
                      ),
                      const Spacer(),
                      Icon(
                        Icons.schedule,
                        size: 16,
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _formatDueDate(dueDate),
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface.withOpacity(0.6),
                        ),
                      ),
                      if (!isCompleted) ...[
                        const SizedBox(width: 8),
                        IconButton(
                          icon: const Icon(Icons.edit, size: 20),
                          onPressed: () {
                            // TODO: Edit task
                          },
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  String _formatDueDate(DateTime date) {
    final now = DateTime.now();
    final difference = date.difference(now).inDays;

    if (difference == 0) {
      return 'Today';
    } else if (difference == 1) {
      return 'Tomorrow';
    } else if (difference == -1) {
      return 'Yesterday';
    } else if (difference > 0) {
      return 'In $difference days';
    } else {
      return '${difference.abs()} days ago';
    }
  }

  void _showAddTaskDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add New Task'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              decoration: InputDecoration(
                labelText: 'Task Title',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 16),
            TextField(
              decoration: InputDecoration(
                labelText: 'Description',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              // TODO: Create task
              Navigator.pop(context);
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }
}