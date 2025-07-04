import 'package:flutter/material.dart';

/// Widget for name input in the personal configuration step
class NameSection extends StatelessWidget {
  final TextEditingController nameController;
  final VoidCallback onSave;
  final VoidCallback? onChanged;

  const NameSection({
    super.key,
    required this.nameController,
    required this.onSave,
    this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '👋 What should I call you?',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'How would you like your AI assistant to address you?',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
        const SizedBox(height: 16),
        Focus(
          onFocusChange: (hasFocus) {
            if (!hasFocus) {
              // Save when the field loses focus
              print('📝 Name field lost focus, saving to backend...');
              onSave();
            }
          },
          child: TextField(
            controller: nameController,
            decoration: InputDecoration(
              hintText: 'Enter your preferred name...',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: theme.colorScheme.surfaceVariant.withOpacity(0.3),
              contentPadding: const EdgeInsets.all(16),
              prefixIcon: const Icon(Icons.person_outline),
            ),
            textCapitalization: TextCapitalization.words,
            onChanged: (value) => onChanged?.call(),
            onSubmitted: (value) => onSave(),
          ),
        ),
      ],
    );
  }
}