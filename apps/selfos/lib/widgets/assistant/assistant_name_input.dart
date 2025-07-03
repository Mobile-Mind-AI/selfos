// widgets/assistant_name_input.dart
import 'package:flutter/material.dart';

class AssistantNameInput extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final bool isValid;
  final VoidCallback onRefresh;

  const AssistantNameInput({
    super.key,
    required this.controller,
    required this.focusNode,
    required this.isValid,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(
          color: theme.colorScheme.outline.withOpacity(0.2),
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Assistant Name',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w600,
              color: theme.colorScheme.onSurface,
            ),
          ),

          const SizedBox(height: 12),

          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  focusNode: focusNode,
                  decoration: InputDecoration(
                    hintText: 'e.g., Alex, Sage, Helper...',
                    prefixIcon: Icon(
                      Icons.badge,
                      color: theme.colorScheme.primary,
                    ),
                    suffixIcon: isValid
                        ? Icon(
                            Icons.check_circle,
                            color: theme.colorScheme.primary,
                          )
                        : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    errorText: controller.text.isNotEmpty && !isValid
                        ? 'Name must be 2-50 characters'
                        : null,
                  ),
                  textCapitalization: TextCapitalization.words,
                  maxLength: 50,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                height: 56,
                width: 56,
                decoration: BoxDecoration(
                  border: Border.all(
                    color: theme.colorScheme.outline.withOpacity(0.3),
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: IconButton(
                  onPressed: onRefresh,
                  icon: Icon(
                    Icons.refresh,
                    color: theme.colorScheme.primary,
                  ),
                  tooltip: 'Generate new name',
                ),
              ),
            ],
          ),

          const SizedBox(height: 8),

          Text(
            'Choose a name that feels right to you. This is how you\'ll think of your assistant.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
        ],
      ),
    );
  }
}