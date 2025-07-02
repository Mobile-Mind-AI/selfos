import 'package:flutter/material.dart';
import 'dart:math' as math;

/// Personality setup step with interactive sliders for assistant personality traits.
/// 
/// This is step 3 in the onboarding flow: "Personality Setup"
class PersonalitySetupStep extends StatefulWidget {
  final Function(Map<String, dynamic>) onNext;
  final VoidCallback onPrevious;

  const PersonalitySetupStep({
    super.key,
    required this.onNext,
    required this.onPrevious,
  });

  @override
  State<PersonalitySetupStep> createState() => _PersonalitySetupStepState();
}

class _PersonalitySetupStepState extends State<PersonalitySetupStep>
    with TickerProviderStateMixin {
  
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  
  // Personality trait values (0-100)
  double _formality = 50.0;
  double _humor = 30.0;
  double _motivation = 60.0;
  
  String _currentPreview = '';
  bool _isPreviewVisible = false;

  final List<Map<String, dynamic>> _personalityTraits = [
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
  void initState() {
    super.initState();
    
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    ));
    
    _animationController.forward();
    _updatePreview();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  double _getTraitValue(String traitName) {
    switch (traitName) {
      case 'formality':
        return _formality;
      case 'humor':
        return _humor;
      case 'motivation':
        return _motivation;
      default:
        return 50.0;
    }
  }

  void _setTraitValue(String traitName, double value) {
    setState(() {
      switch (traitName) {
        case 'formality':
          _formality = value;
          break;
        case 'humor':
          _humor = value;
          break;
        case 'motivation':
          _motivation = value;
          break;
      }
    });
    _updatePreview();
  }

  void _updatePreview() {
    // Generate preview message based on current settings
    String greeting = '';
    
    if (_formality < 30) {
      greeting = 'Good day! ';
    } else if (_formality > 70) {
      greeting = 'Hey there! ';
    } else {
      greeting = 'Hello! ';
    }
    
    String motivation = '';
    if (_motivation > 70) {
      motivation = 'Ready to crush some goals together? Let\'s do this! 🚀';
    } else if (_motivation < 30) {
      motivation = 'I\'m here to support you at your own pace.';
    } else {
      motivation = 'I\'m excited to help you achieve your goals!';
    }
    
    if (_humor > 70) {
      motivation += ' ✨';
    }
    
    setState(() {
      _currentPreview = greeting + motivation;
      _isPreviewVisible = true;
    });
  }

  void _handleNext() {
    final data = {
      'style': {
        'formality': _formality.round(),
        'directness': 50, // Default for now
        'humor': _humor.round(),
        'empathy': 70, // Default for now
        'motivation': _motivation.round(),
      },
    };
    widget.onNext(data);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Introduction
                    _buildIntroduction(theme),
                    
                    const SizedBox(height: 32),
                    
                    // Personality sliders
                    ..._personalityTraits.map((trait) => 
                      _buildPersonalitySlider(theme, trait)
                    ).toList(),
                    
                    const SizedBox(height: 24),
                    
                    // Preview
                    _buildPreview(theme),
                  ],
                ),
              ),
            ),
            
            // Bottom actions
            _buildBottomActions(theme),
          ],
        ),
      ),
    );
  }

  Widget _buildIntroduction(ThemeData theme) {
    return Column(
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
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(60),
          ),
          child: Icon(
            Icons.tune,
            size: 60,
            color: theme.colorScheme.primary,
          ),
        ),
        
        const SizedBox(height: 24),
        
        Text(
          'Personality Setup',
          style: theme.textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.onSurface,
          ),
          textAlign: TextAlign.center,
        ),
        
        const SizedBox(height: 12),
        
        Text(
          'How would you like your assistant to communicate with you? '
          'Adjust these settings to match your preferred style.',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildPersonalitySlider(ThemeData theme, Map<String, dynamic> trait) {
    final value = _getTraitValue(trait['name']);
    final color = trait['color'] as Color;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Trait header
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Icon(
                  trait['icon'],
                  color: color,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  trait['label'],
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          // Slider
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: color,
              inactiveTrackColor: color.withOpacity(0.3),
              thumbColor: color,
              overlayColor: color.withOpacity(0.2),
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 12),
              trackHeight: 6,
            ),
            child: Slider(
              value: value,
              min: 0,
              max: 100,
              divisions: 20,
              onChanged: (newValue) {
                _setTraitValue(trait['name'], newValue);
              },
            ),
          ),
          
          // Labels
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    trait['leftLabel'],
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: value < 50 
                          ? color 
                          : theme.colorScheme.onSurface.withOpacity(0.6),
                      fontWeight: value < 50 ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                ),
                Expanded(
                  child: Text(
                    trait['rightLabel'],
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: value >= 50 
                          ? color 
                          : theme.colorScheme.onSurface.withOpacity(0.6),
                      fontWeight: value >= 50 ? FontWeight.w600 : FontWeight.normal,
                    ),
                    textAlign: TextAlign.end,
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Example
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.05),
              border: Border.all(
                color: color.withOpacity(0.2),
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.format_quote,
                  color: color,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    value < 50 ? trait['leftExample'] : trait['rightExample'],
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.8),
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPreview(ThemeData theme) {
    return AnimatedOpacity(
      opacity: _isPreviewVisible ? 1.0 : 0.0,
      duration: const Duration(milliseconds: 300),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              theme.colorScheme.primary.withOpacity(0.1),
              theme.colorScheme.secondary.withOpacity(0.1),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: theme.colorScheme.primary.withOpacity(0.2),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.preview,
                  color: theme.colorScheme.primary,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  'Preview',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.primary,
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 12),
            
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Icon(
                      Icons.smart_toy,
                      color: theme.colorScheme.primary,
                      size: 16,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _currentPreview,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 8),
            
            Text(
              'This is how your assistant will communicate with you based on your preferences.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomActions(ThemeData theme) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _handleNext,
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
    );
  }
}