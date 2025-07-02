import 'package:flutter/material.dart';

/// Life areas selection step.
/// 
/// This is step 5 in the onboarding flow: "Life Areas"
class LifeAreasStep extends StatefulWidget {
  final Function(Map<String, dynamic>) onNext;
  final VoidCallback onPrevious;

  const LifeAreasStep({
    super.key,
    required this.onNext,
    required this.onPrevious,
  });

  @override
  State<LifeAreasStep> createState() => _LifeAreasStepState();
}

class _LifeAreasStepState extends State<LifeAreasStep> {
  final Set<String> _selectedAreas = {};
  final TextEditingController _customAreaController = TextEditingController();

  final List<Map<String, dynamic>> _lifeAreas = [
    {'id': 'health', 'name': 'Health & Fitness', 'icon': Icons.favorite, 'color': Colors.red},
    {'id': 'career', 'name': 'Career & Work', 'icon': Icons.work, 'color': Colors.blue},
    {'id': 'relationships', 'name': 'Relationships', 'icon': Icons.people, 'color': Colors.green},
    {'id': 'finance', 'name': 'Finance', 'icon': Icons.attach_money, 'color': Colors.orange},
    {'id': 'creativity', 'name': 'Creativity & Arts', 'icon': Icons.palette, 'color': Colors.purple},
    {'id': 'learning', 'name': 'Learning & Growth', 'icon': Icons.school, 'color': Colors.teal},
    {'id': 'spirituality', 'name': 'Spirituality', 'icon': Icons.self_improvement, 'color': Colors.indigo},
    {'id': 'fun', 'name': 'Fun & Recreation', 'icon': Icons.sports_esports, 'color': Colors.pink},
  ];

  void _handleNext() {
    final data = {
      'selected_life_areas': _selectedAreas.toList(),
      'custom_life_areas': [], // TODO: Implement custom areas
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
                children: [
                  // Introduction
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
                      Icons.dashboard_customize,
                      size: 60,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Choose Your Life Areas',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Select the areas of life that are important to you. '
                    'You can always add or modify these later.',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.7),
                    ),
                    textAlign: TextAlign.center,
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Life areas grid
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 1.2,
                    ),
                    itemCount: _lifeAreas.length,
                    itemBuilder: (context, index) {
                      final area = _lifeAreas[index];
                      final isSelected = _selectedAreas.contains(area['id']);
                      
                      return GestureDetector(
                        onTap: () {
                          setState(() {
                            if (isSelected) {
                              _selectedAreas.remove(area['id']);
                            } else {
                              _selectedAreas.add(area['id']);
                            }
                          });
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? (area['color'] as Color).withOpacity(0.1)
                                : theme.colorScheme.surfaceVariant.withOpacity(0.5),
                            border: Border.all(
                              color: isSelected
                                  ? area['color'] as Color
                                  : Colors.transparent,
                              width: 2,
                            ),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                area['icon'],
                                size: 32,
                                color: isSelected
                                    ? area['color'] as Color
                                    : theme.colorScheme.onSurface.withOpacity(0.7),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                area['name'],
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  color: isSelected
                                      ? area['color'] as Color
                                      : theme.colorScheme.onSurface.withOpacity(0.8),
                                  fontWeight: isSelected 
                                      ? FontWeight.w600 
                                      : FontWeight.normal,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                  
                  const SizedBox(height: 24),
                  
                  if (_selectedAreas.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        children: [
                          Icon(
                            Icons.check_circle,
                            color: theme.colorScheme.primary,
                            size: 24,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '${_selectedAreas.length} areas selected',
                            style: theme.textTheme.titleSmall?.copyWith(
                              color: theme.colorScheme.primary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Great! Your assistant will help you focus on these areas.',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurface.withOpacity(0.7),
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
          
          // Bottom actions
          Column(
            children: [
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _selectedAreas.isNotEmpty ? _handleNext : null,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text(
                    'Continue',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
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