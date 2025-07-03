// widgets/personality_setup.dart
import 'package:flutter/material.dart';

class PersonalitySetup extends StatelessWidget {
  final double formality;
  final double humor;
  final double motivation;
  final Function(String, double) onPersonalityChanged;

  const PersonalitySetup({
    super.key,
    required this.formality,
    required this.humor,
    required this.motivation,
    required this.onPersonalityChanged,
  });

  static final List<Map<String, dynamic>> _personalityTraits = [
    {
      'name': 'formality',
      'label': 'Communication Style',
      'leftLabel': 'Formal & Professional',
      'rightLabel': 'Casual & Friendly',
      'leftExample': '"Good day! How may I assist you?"',
      'rightExample': '"Hey! What\'s up? Ready to crush some goals?"',
      'icon': Icons.chat_bubble_outline,
      'color': Colors.blue,
    },
    {
      'name': 'humor',
      'label': 'Humor Level',
      'leftLabel': 'Serious & Focused',
      'rightLabel': 'Playful & Fun',
      'leftExample': '"Let\'s focus on your objectives."',
      'rightExample': '"Time to make some magic happen! ✨"',
      'icon': Icons.sentiment_satisfied,
      'color': Colors.orange,
    },
    {
      'name': 'motivation',
      'label': 'Motivation Style',
      'leftLabel': 'Gentle & Supportive',
      'rightLabel': 'High-Energy Coach',
      'leftExample': '"Take your time. Every step counts."',
      'rightExample': '"You\'ve got this! Let\'s smash those goals! 💪"',
      'icon': Icons.trending_up,
      'color': Colors.green,
    },
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Personality',
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
            children: _personalityTraits.map((trait) =>
              _PersonalitySlider(
                trait: trait,
                value: _getTraitValue(trait['name']),
                onChanged: (value) => onPersonalityChanged(trait['name'], value),
              )
            ).toList(),
          ),
        ),
      ],
    );
  }

  double _getTraitValue(String traitName) {
    switch (traitName) {
      case 'formality':
        return formality;
      case 'humor':
        return humor;
      case 'motivation':
        return motivation;
      default:
        return 50.0;
    }
  }
}

class _PersonalitySlider extends StatelessWidget {
  final Map<String, dynamic> trait;
  final double value;
  final Function(double) onChanged;

  const _PersonalitySlider({
    required this.trait,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = trait['color'] as Color;

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Compact header
          Row(
            children: [
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  trait['icon'],
                  color: color,
                  size: 14,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                trait['label'],
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),

          const SizedBox(height: 8),

          // Compact slider
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: color,
              inactiveTrackColor: color.withOpacity(0.3),
              thumbColor: color,
              overlayColor: color.withOpacity(0.2),
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 8),
              trackHeight: 4,
            ),
            child: Slider(
              value: value,
              min: 0,
              max: 100,
              divisions: 20,
              onChanged: onChanged,
            ),
          ),

          // Compact labels
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  trait['leftLabel'],
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: value < 50
                        ? color
                        : theme.colorScheme.onSurface.withOpacity(0.5),
                    fontSize: 11,
                  ),
                ),
                Text(
                  trait['rightLabel'],
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: value >= 50
                        ? color
                        : theme.colorScheme.onSurface.withOpacity(0.5),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}