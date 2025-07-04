import 'package:flutter/material.dart';

/// Widget for selecting life areas in the personal configuration step
class LifeAreasSection extends StatelessWidget {
  final List<Map<String, dynamic>> lifeAreas;
  final Set<int> selectedAreas;
  final List<Map<String, dynamic>> customAreas;
  final Function(int) onAreaToggle;
  final VoidCallback onAddCustomArea;
  final Function(Map<String, dynamic>) onRemoveCustomArea;

  const LifeAreasSection({
    super.key,
    required this.lifeAreas,
    required this.selectedAreas,
    required this.customAreas,
    required this.onAreaToggle,
    required this.onAddCustomArea,
    required this.onRemoveCustomArea,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '🎯 Life Areas',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Choose areas that matter most to you',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
        const SizedBox(height: 16),
        
        // Colorful, compact life areas
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ...lifeAreas.map((area) => _LifeAreaChip(
              area: area,
              isSelected: selectedAreas.contains(area['id']),
              onTap: () => onAreaToggle(area['id']),
            )),
            _AddCustomAreaChip(onTap: onAddCustomArea),
          ],
        ),
        
        // Custom areas
        if (customAreas.isNotEmpty) ...[
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: customAreas.map((area) => _CustomAreaChip(
              area: area,
              onRemove: () => onRemoveCustomArea(area),
            )).toList(),
          ),
        ],
        
        // Selection summary
        if (selectedAreas.isNotEmpty || customAreas.isNotEmpty) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withOpacity(0.5),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.check_circle,
                  color: theme.colorScheme.onPrimaryContainer,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Text(
                  '${selectedAreas.length + customAreas.length} areas selected',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _LifeAreaChip extends StatelessWidget {
  final Map<String, dynamic> area;
  final bool isSelected;
  final VoidCallback onTap;

  const _LifeAreaChip({
    required this.area,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = area['color'] as Color;
    
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? color.withOpacity(0.1) : Colors.transparent,
          border: Border.all(
            color: isSelected ? color : theme.colorScheme.outline.withOpacity(0.3),
            width: isSelected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(20),
          boxShadow: isSelected ? [
            BoxShadow(
              color: color.withOpacity(0.2),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ] : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              area['icon'],
              color: isSelected ? color : theme.colorScheme.onSurface.withOpacity(0.6),
              size: 16,
            ),
            const SizedBox(width: 6),
            Text(
              area['name'],
              style: theme.textTheme.bodySmall?.copyWith(
                color: isSelected ? color : theme.colorScheme.onSurface,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AddCustomAreaChip extends StatelessWidget {
  final VoidCallback onTap;

  const _AddCustomAreaChip({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: theme.colorScheme.primary.withOpacity(0.1),
          border: Border.all(
            color: theme.colorScheme.primary.withOpacity(0.3),
            width: 1,
          ),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.add,
              color: theme.colorScheme.primary,
              size: 16,
            ),
            const SizedBox(width: 6),
            Text(
              'Add Custom',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.primary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CustomAreaChip extends StatelessWidget {
  final Map<String, dynamic> area;
  final VoidCallback onRemove;

  const _CustomAreaChip({
    required this.area,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = area['color'] as Color;
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        border: Border.all(
          color: color,
          width: 2,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            area['icon'],
            color: color,
            size: 16,
          ),
          const SizedBox(width: 6),
          Text(
            area['name'],
            style: theme.textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 6),
          GestureDetector(
            onTap: onRemove,
            child: Icon(
              Icons.close,
              color: color,
              size: 14,
            ),
          ),
        ],
      ),
    );
  }
}