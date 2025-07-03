// widgets/language_preferences.dart
import 'package:flutter/material.dart';

class LanguagePreferences extends StatelessWidget {
  final List<Map<String, String>> languages;
  final String selectedLanguage;
  final bool requiresConfirmation;
  final Function(String) onLanguageChanged;
  final Function(bool) onConfirmationChanged;

  const LanguagePreferences({
    super.key,
    required this.languages,
    required this.selectedLanguage,
    required this.requiresConfirmation,
    required this.onLanguageChanged,
    required this.onConfirmationChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Language & Preferences',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.onSurface,
          ),
        ),

        const SizedBox(height: 12),

        Container(
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
              // Language dropdown
              Row(
                children: [
                  Icon(
                    Icons.language,
                    color: theme.colorScheme.primary,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Language',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 8),

              DropdownButtonFormField<String>(
                value: selectedLanguage,
                decoration: InputDecoration(
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                ),
                items: languages.map((language) {
                  return DropdownMenuItem<String>(
                    value: language['code'],
                    child: Row(
                      children: [
                        Text(
                          language['flag']!,
                          style: const TextStyle(fontSize: 18),
                        ),
                        const SizedBox(width: 8),
                        Text(language['name']!),
                      ],
                    ),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    onLanguageChanged(value);
                  }
                },
              ),

              const SizedBox(height: 16),

              // Confirmation preference
              SwitchListTile(
                title: Text(
                  'Ask before taking actions',
                  style: theme.textTheme.bodyMedium,
                ),
                subtitle: Text(
                  'Assistant will ask for confirmation',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
                value: requiresConfirmation,
                onChanged: onConfirmationChanged,
                contentPadding: EdgeInsets.zero,
              ),
            ],
          ),
        ),
      ],
    );
  }
}