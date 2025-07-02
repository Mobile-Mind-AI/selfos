import 'package:flutter/material.dart';

/// First goal creation step.
/// 
/// This is step 6 in the onboarding flow: "Your First Goal"
class FirstGoalStep extends StatefulWidget {
  final Function(Map<String, dynamic>) onNext;
  final VoidCallback onPrevious;

  const FirstGoalStep({
    super.key,
    required this.onNext,
    required this.onPrevious,
  });

  @override
  State<FirstGoalStep> createState() => _FirstGoalStepState();
}

class _FirstGoalStepState extends State<FirstGoalStep> {
  final TextEditingController _goalController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  bool _generateTasks = true;
  bool _isGoalValid = false;

  final List<String> _goalSuggestions = [
    'Learn to play guitar',
    'Run a 5K race',
    'Read 12 books this year',
    'Learn a new language',
    'Start a side business',
    'Meditate daily for 30 days',
    'Cook more meals at home',
    'Take a photography course',
  ];

  @override
  void initState() {
    super.initState();
    _goalController.addListener(_validateGoal);
  }

  @override
  void dispose() {
    _goalController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _validateGoal() {
    setState(() {
      _isGoalValid = _goalController.text.trim().length >= 3;
    });
  }

  void _handleCreateGoal() {
    if (_isGoalValid) {
      final data = {
        'skip_goal_creation': false,
        'title': _goalController.text.trim(),
        'description': _descriptionController.text.trim(),
        'generate_tasks': _generateTasks,
      };
      widget.onNext(data);
    }
  }

  void _handleSkipGoal() {
    final data = {
      'skip_goal_creation': true,
    };
    widget.onNext(data);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Introduction
                  Center(
                    child: Column(
                      children: [
                        Container(
                          width: 120,
                          height: 120,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                theme.colorScheme.primary.withOpacity(0.1),
                                theme.colorScheme.secondary.withOpacity(0.1),
                              ],
                            ),
                            borderRadius: BorderRadius.circular(60),
                          ),
                          child: Icon(
                            Icons.flag,
                            size: 60,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                        const SizedBox(height: 24),
                        Text(
                          'Your First Goal',
                          style: theme.textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'What would you like to achieve? You can create your first goal now, or skip this step and create goals, tasks, and projects later from the main dashboard.',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurface.withOpacity(0.7),
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Goal input
                  Text(
                    'What do you want to achieve?',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _goalController,
                    decoration: InputDecoration(
                      hintText: 'I want to...',
                      prefixIcon: Icon(
                        Icons.emoji_events,
                        color: theme.colorScheme.primary,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    maxLines: 2,
                    textCapitalization: TextCapitalization.sentences,
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Description input
                  Text(
                    'Tell us more (optional)',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _descriptionController,
                    decoration: InputDecoration(
                      hintText: 'Why is this important to you?',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    maxLines: 3,
                    textCapitalization: TextCapitalization.sentences,
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Suggestions
                  Text(
                    'Need inspiration?',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _goalSuggestions.map((suggestion) {
                      return ActionChip(
                        label: Text(suggestion),
                        onPressed: () {
                          _goalController.text = suggestion;
                        },
                        backgroundColor: theme.colorScheme.surfaceVariant.withOpacity(0.5),
                        side: BorderSide(
                          color: theme.colorScheme.outline.withOpacity(0.2),
                        ),
                      );
                    }).toList(),
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Generate tasks option
                  Card(
                    child: SwitchListTile(
                      title: const Text('Generate action steps'),
                      subtitle: const Text(
                        'Let AI create initial tasks to help you get started'
                      ),
                      value: _generateTasks,
                      onChanged: (value) {
                        setState(() {
                          _generateTasks = value;
                        });
                      },
                      secondary: Icon(
                        Icons.auto_awesome,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          // Bottom actions
          Column(
            children: [
              // Create Goal button (only enabled if goal is valid)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isGoalValid ? _handleCreateGoal : null,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text(
                        'Create Goal',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (_generateTasks) ...[
                        const SizedBox(width: 8),
                        Icon(
                          Icons.auto_awesome,
                          size: 20,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 12),
              
              // Skip Goal button
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: _handleSkipGoal,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text(
                    'Skip for Now',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              
              // Info text about skipping
              const SizedBox(height: 8),
              Text(
                'You can create goals, tasks, and projects later from the dashboard',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: 16),
              
              TextButton(
                onPressed: widget.onPrevious,
                child: Text(
                  'Back',
                  style: TextStyle(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}