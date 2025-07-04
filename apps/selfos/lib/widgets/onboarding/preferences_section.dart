import 'package:flutter/material.dart';

/// Widget for quick preferences selection in the personal configuration step
class PreferencesSection extends StatelessWidget {
  final List<Map<String, dynamic>> scenarios;
  final Map<String, String> preferences;
  final Map<String, TextEditingController> customAnswerControllers;
  final Function(String, String) onPreferenceSelected;
  final VoidCallback onSave;

  const PreferencesSection({
    super.key,
    required this.scenarios,
    required this.preferences,
    required this.customAnswerControllers,
    required this.onPreferenceSelected,
    required this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '⚙️ Quick Preferences',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Help us understand how you like to work',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
        const SizedBox(height: 16),
        
        // Scenarios with horizontal layout
        ...scenarios.map((scenario) => PreferenceScenarioCard(
          scenario: scenario,
          selectedPreference: preferences[scenario['key']],
          customController: customAnswerControllers[scenario['key']]!,
          onPreferenceSelected: onPreferenceSelected,
          onSave: onSave,
        )),
      ],
    );
  }
}

/// Individual scenario card for preference selection
class PreferenceScenarioCard extends StatefulWidget {
  final Map<String, dynamic> scenario;
  final String? selectedPreference;
  final TextEditingController customController;
  final Function(String, String) onPreferenceSelected;
  final VoidCallback onSave;

  const PreferenceScenarioCard({
    super.key,
    required this.scenario,
    this.selectedPreference,
    required this.customController,
    required this.onPreferenceSelected,
    required this.onSave,
  });

  @override
  State<PreferenceScenarioCard> createState() => _PreferenceScenarioCardState();
}

class _PreferenceScenarioCardState extends State<PreferenceScenarioCard> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isCustomSelected = widget.selectedPreference == 'custom';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            widget.scenario['question'],
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          
          // Horizontal layout options
          SizedBox(
            width: double.infinity,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: IntrinsicWidth(
                child: Row(
                  children: [
                    // Default options
                    ...widget.scenario['options'].map<Widget>((option) {
                      final isSelected = widget.selectedPreference == option['value'];
                      return Expanded(
                        child: Container(
                          margin: const EdgeInsets.only(right: 8),
                          child: GestureDetector(
                            onTap: () => widget.onPreferenceSelected(widget.scenario['key'], option['value']),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                              decoration: BoxDecoration(
                                color: isSelected 
                                    ? theme.colorScheme.primary.withOpacity(0.1)
                                    : Colors.transparent,
                                border: Border.all(
                                  color: isSelected 
                                      ? theme.colorScheme.primary
                                      : theme.colorScheme.outline.withOpacity(0.3),
                                  width: isSelected ? 2 : 1,
                                ),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                option['label'],
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: isSelected 
                                      ? theme.colorScheme.primary
                                      : theme.colorScheme.onSurface,
                                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                    
                    // Custom option button
                    if (isCustomSelected && widget.customController.text.trim().isNotEmpty)
                      Expanded(
                        child: Container(
                          margin: const EdgeInsets.only(right: 8),
                          child: GestureDetector(
                            onTap: () {
                              // Allow editing by focusing on the text field
                              WidgetsBinding.instance.addPostFrameCallback((_) {
                                FocusScope.of(context).requestFocus(FocusNode());
                                // Scroll to make the text field visible
                                Scrollable.ensureVisible(context);
                              });
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.secondary.withOpacity(0.1),
                                border: Border.all(
                                  color: theme.colorScheme.secondary,
                                  width: 2,
                                ),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.edit,
                                    size: 14,
                                    color: theme.colorScheme.secondary,
                                  ),
                                  const SizedBox(width: 4),
                                  Flexible(
                                    child: Text(
                                      widget.customController.text.trim(),
                                      style: theme.textTheme.bodySmall?.copyWith(
                                        color: theme.colorScheme.secondary,
                                        fontWeight: FontWeight.w600,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                      maxLines: 1,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      )
                    else
                      Expanded(
                        child: Container(
                          margin: const EdgeInsets.only(right: 8),
                          child: GestureDetector(
                            onTap: () => widget.onPreferenceSelected(widget.scenario['key'], 'custom'),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                              decoration: BoxDecoration(
                                color: Colors.transparent,
                                border: Border.all(
                                  color: theme.colorScheme.outline.withOpacity(0.3),
                                  width: 1,
                                ),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.edit,
                                    size: 14,
                                    color: theme.colorScheme.onSurface.withOpacity(0.7),
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    'Custom',
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      color: theme.colorScheme.onSurface,
                                      fontWeight: FontWeight.normal,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
          
          // Custom answer input (only show if custom is selected)
          if (isCustomSelected) ...[
            const SizedBox(height: 12),
            Focus(
              onFocusChange: (hasFocus) {
                if (!hasFocus) {
                  // Save when the field loses focus
                  print('📝 Custom answer field lost focus, saving to backend...');
                  widget.onSave();
                  // Update the UI to show the new text in the pill
                  setState(() {});
                }
              },
              child: TextField(
                controller: widget.customController,
                decoration: InputDecoration(
                  hintText: 'Enter your custom answer...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  filled: true,
                  fillColor: theme.colorScheme.secondaryContainer.withOpacity(0.3),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  isDense: true,
                ),
                textCapitalization: TextCapitalization.sentences,
                maxLines: 2,
                onSubmitted: (value) {
                  widget.onSave();
                  setState(() {}); // Update the pill display
                },
                onChanged: (value) {
                  // Update pill in real time as user types
                  setState(() {});
                },
              ),
            ),
          ],
        ],
      ),
    );
  }
}