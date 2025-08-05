import 'package:flutter/material.dart';

/// Widget for displaying life areas with importance sliders
class LifeAreaWithImportance extends StatelessWidget {
  final Map<String, dynamic> area;
  final bool isSelected;
  final double importance;
  final String? selectedColor;
  final ValueChanged<bool>? onSelectedChanged;
  final ValueChanged<double>? onImportanceChanged;
  final ValueChanged<String>? onColorChanged;
  final VoidCallback? onDelete;

  const LifeAreaWithImportance({
    super.key,
    required this.area,
    required this.isSelected,
    required this.importance,
    this.selectedColor,
    this.onSelectedChanged,
    this.onImportanceChanged,
    this.onColorChanged,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isCustom = area['is_custom'] == true;
    
    // Handle color - use selected color if available, otherwise default
    Color color;
    if (selectedColor != null) {
      final hexCode = selectedColor!.replaceAll('#', '');
      color = Color(int.parse('FF$hexCode', radix: 16));
    } else if (area['color'] is Color) {
      color = area['color'] as Color;
    } else if (area['color'] is String) {
      final hexColor = area['color'] as String;
      final hexCode = hexColor.replaceAll('#', '');
      color = Color(int.parse('FF$hexCode', radix: 16));
    } else {
      color = theme.colorScheme.primary;
    }

    return Card(
      elevation: isSelected ? 2 : 0,
      color: isSelected ? color.withOpacity(0.1) : theme.colorScheme.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isSelected ? color : theme.colorScheme.outline.withOpacity(0.3),
          width: isSelected ? 2 : 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Checkbox
                Checkbox(
                  value: isSelected,
                  onChanged: onSelectedChanged != null 
                    ? (bool? value) => onSelectedChanged!(value ?? false)
                    : null,
                  activeColor: color,
                ),
                
                // Icon
                Icon(
                  _getIcon(area['icon'] ?? 'category'),
                  color: isSelected ? color : theme.colorScheme.onSurface.withOpacity(0.6),
                  size: 24,
                ),
                const SizedBox(width: 8),
                
                // Name
                Expanded(
                  child: Text(
                    area['name'] ?? 'Unknown',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: isSelected ? color : theme.colorScheme.onSurface,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                  ),
                ),
                
                // Delete button for custom areas
                if (isCustom && onDelete != null)
                  IconButton(
                    icon: Icon(
                      Icons.delete_outline,
                      color: theme.colorScheme.error,
                      size: 20,
                    ),
                    onPressed: onDelete,
                    tooltip: 'Remove custom area',
                  ),
              ],
            ),
            
            // Importance slider and color picker (only show if selected)
            if (isSelected) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Text(
                    'Importance:',
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Slider(
                      value: importance,
                      min: 1,
                      max: 100,
                      divisions: 99,
                      activeColor: color,
                      label: importance.round().toString(),
                      onChanged: onImportanceChanged,
                    ),
                  ),
                  SizedBox(
                    width: 40,
                    child: Text(
                      importance.round().toString(),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: color,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(
                    'Color:',
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(width: 8),
                  InkWell(
                    onTap: () => _showColorPicker(context, color),
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: color,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: theme.colorScheme.outline,
                          width: 2,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Tap to change',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  IconData _getIcon(String iconName) {
    switch (iconName) {
      case 'favorite':
        return Icons.favorite;
      case 'work':
        return Icons.work;
      case 'family_restroom':
        return Icons.family_restroom;
      case 'school':
        return Icons.school;
      case 'attach_money':
        return Icons.attach_money;
      case 'self_improvement':
        return Icons.self_improvement;
      case 'public':
        return Icons.public;
      case 'music_note':
        return Icons.music_note;
      case 'fitness_center':
        return Icons.fitness_center;
      case 'restaurant':
        return Icons.restaurant;
      case 'home':
        return Icons.home;
      case 'local_hospital':
        return Icons.local_hospital;
      case 'category':
        return Icons.category;
      case 'sports_soccer':
        return Icons.sports_soccer;
      case 'sports_basketball':
        return Icons.sports_basketball;
      case 'sports_tennis':
        return Icons.sports_tennis;
      case 'pool':
        return Icons.pool;
      case 'directions_run':
        return Icons.directions_run;
      case 'directions_bike':
        return Icons.directions_bike;
      case 'directions_car':
        return Icons.directions_car;
      case 'flight':
        return Icons.flight;
      case 'hotel':
        return Icons.hotel;
      case 'beach_access':
        return Icons.beach_access;
      case 'terrain':
        return Icons.terrain;
      case 'park':
        return Icons.park;
      case 'pets':
        return Icons.pets;
      case 'child_care':
        return Icons.child_care;
      case 'brush':
        return Icons.brush;
      case 'palette':
        return Icons.palette;
      case 'camera_alt':
        return Icons.camera_alt;
      case 'movie':
        return Icons.movie;
      case 'book':
        return Icons.book;
      case 'computer':
        return Icons.computer;
      case 'code':
        return Icons.code;
      case 'science':
        return Icons.science;
      case 'psychology':
        return Icons.psychology;
      case 'volunteer_activism':
        return Icons.volunteer_activism;
      case 'groups':
        return Icons.groups;
      case 'celebration':
        return Icons.celebration;
      case 'spa':
        return Icons.spa;
      case 'meditation':
        return Icons.self_improvement;
      case 'nightlife':
        return Icons.nightlife;
      case 'shopping_cart':
        return Icons.shopping_cart;
      case 'videogame_asset':
        return Icons.videogame_asset;
      default:
        return Icons.category;
    }
  }

  void _showColorPicker(BuildContext context, Color currentColor) {
    final colors = [
      Colors.red,
      Colors.pink,
      Colors.purple,
      Colors.deepPurple,
      Colors.indigo,
      Colors.blue,
      Colors.lightBlue,
      Colors.cyan,
      Colors.teal,
      Colors.green,
      Colors.lightGreen,
      Colors.lime,
      Colors.yellow,
      Colors.amber,
      Colors.orange,
      Colors.deepOrange,
      Colors.brown,
      Colors.grey,
      Colors.blueGrey,
    ];

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Choose Color for ${area['name']}'),
        content: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: colors.map((color) => InkWell(
            onTap: () {
              if (onColorChanged != null) {
                // Convert color to hex string
                final hexColor = '#${color.value.toRadixString(16).substring(2)}';
                onColorChanged!(hexColor);
              }
              Navigator.pop(context);
            },
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
                border: Border.all(
                  color: color == currentColor ? Colors.black : Colors.transparent,
                  width: 3,
                ),
              ),
            ),
          )).toList(),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }
}