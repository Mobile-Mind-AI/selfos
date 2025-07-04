import 'package:flutter/material.dart';
import 'dart:math' as math;
import 'dart:io';
import 'dart:async';
import 'dart:typed_data';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../providers/onboarding_provider.dart';
import '../../widgets/common/image_cropper_dialog.dart';
import '../../config/api_config.dart';
import '../../services/storage_service.dart';
import '../../services/avatar_upload_service.dart';
import '../../widgets/onboarding/personal_config_header.dart';
import '../../widgets/onboarding/name_section.dart';
import '../../widgets/onboarding/life_areas_section.dart';
import '../../widgets/onboarding/story_section.dart';
import '../../widgets/onboarding/preferences_section.dart';
import '../../widgets/onboarding/navigation_buttons.dart';

/// Enhanced Personal Configuration Step - Single Scrollable Screen
/// 
/// Features:
/// - Colorful, compact life areas with custom area creation
/// - Story Builder with progressive prompts
/// - Preference Learning with interactive scenario cards
/// - Single scrollable screen (no tabs)
/// - Most data will be collected during AI conversation via MCP
class EnhancedPersonalConfigurationStep extends ConsumerStatefulWidget {
  final Map<String, dynamic> onboardingData;
  final Function(Map<String, dynamic>) onNext;
  final VoidCallback onPrevious;
  final bool shouldReloadData;

  const EnhancedPersonalConfigurationStep({
    super.key,
    required this.onboardingData,
    required this.onNext,
    required this.onPrevious,
    this.shouldReloadData = false,
  });

  @override
  ConsumerState<EnhancedPersonalConfigurationStep> createState() => _EnhancedPersonalConfigurationStepState();
}

class _EnhancedPersonalConfigurationStepState extends ConsumerState<EnhancedPersonalConfigurationStep>
    with TickerProviderStateMixin {
  
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  
  // Life Areas state - colorful and compact
  final Set<int> _selectedAreas = {};
  final List<Map<String, dynamic>> _customAreas = [];
  final List<Map<String, dynamic>> _lifeAreas = [
    {'id': 1, 'name': 'Health & Fitness', 'icon': 'favorite', 'color': '#E91E63'},
    {'id': 2, 'name': 'Career & Work', 'icon': 'trending_up', 'color': '#2196F3'},
    {'id': 3, 'name': 'Relationships', 'icon': 'people', 'color': '#4CAF50'},
    {'id': 4, 'name': 'Learning & Growth', 'icon': 'psychology', 'color': '#9C27B0'},
    {'id': 5, 'name': 'Lifestyle & Fun', 'icon': 'celebration', 'color': '#FF9800'},
    {'id': 6, 'name': 'Finance & Money', 'icon': 'account_balance_wallet', 'color': '#00BCD4'},
    {'id': 7, 'name': 'Family & Home', 'icon': 'home', 'color': '#795548'},
    {'id': 8, 'name': 'Creativity & Arts', 'icon': 'palette', 'color': '#E91E63'},
  ];
  
  // Name input state
  final TextEditingController _nameController = TextEditingController();
  
  // Avatar state
  String? _avatarId;
  final ImagePicker _imagePicker = ImagePicker();
  
  // Simple debouncing for auto-save (rate limiting is now in provider)
  Timer? _saveDebounceTimer;
  bool _isSaving = false;
  bool _isInitialLoading = true; // Prevent auto-save during initial load
  
  // AI Avatar options
  final List<String> _aiAvatars = [
    '👨‍💼', '👩‍💼', '👨‍💻', '👩‍💻', '👨‍🎓', '👩‍🎓', 
    '👨‍🔬', '👩‍🔬', '👨‍🎨', '👩‍🎨', '👨‍🏫', '👩‍🏫',
    '👨‍⚕️', '👩‍⚕️', '👨‍🚀', '👩‍🚀', '🧑‍💼', '🧑‍💻',
    '🧑‍🎓', '🧑‍🔬', '🧑‍🎨', '🧑‍🏫', '🧑‍⚕️', '🧑‍🚀'
  ];
  
  // Story Builder state
  final TextEditingController _currentSituationController = TextEditingController();
  final TextEditingController _aspirationsController = TextEditingController();
  final Set<String> _interests = {};
  final Set<String> _challenges = {};
  final TextEditingController _customInterestController = TextEditingController();
  final TextEditingController _customChallengeController = TextEditingController();
  
  final List<String> _interestSuggestions = [
    'Technology', 'Health & Fitness', 'Creativity', 'Learning', 'Travel',
    'Music', 'Reading', 'Cooking', 'Sports', 'Nature', 'Art', 'Business',
    'Photography', 'Gaming', 'Writing', 'Meditation', 'Gardening', 'Dancing'
  ];
  
  final List<String> _challengeSuggestions = [
    'Time Management', 'Work-Life Balance', 'Motivation', 'Focus',
    'Procrastination', 'Stress', 'Goal Setting', 'Consistency', 'Confidence',
    'Public Speaking', 'Organization', 'Sleep Quality', 'Social Anxiety'
  ];
  
  // Preference Learning state
  final Map<String, String> _preferences = {};
  final Map<String, TextEditingController> _customAnswerControllers = {};
  
  final List<Map<String, dynamic>> _scenarios = [
    {
      'question': 'When working on projects, do you prefer...',
      'key': 'work_style',
      'options': [
        {'label': 'Detailed planning', 'value': 'structured'},
        {'label': 'Flexible approach', 'value': 'flexible'},
        {'label': 'Balanced mix', 'value': 'balanced'},
        {'label': 'Collaborative style', 'value': 'collaborative'},
        {'label': 'Independent work', 'value': 'independent'},
      ]
    },
    {
      'question': 'How do you like to receive feedback?',
      'key': 'communication_style',
      'options': [
        {'label': 'Direct & clear', 'value': 'direct'},
        {'label': 'Gentle & encouraging', 'value': 'gentle'},
        {'label': 'Detailed examples', 'value': 'detailed'},
        {'label': 'Regular check-ins', 'value': 'regular'},
        {'label': 'Written summaries', 'value': 'written'},
      ]
    },
    {
      'question': 'What motivates you most?',
      'key': 'motivation_style',
      'options': [
        {'label': 'Big achievements', 'value': 'achievement'},
        {'label': 'Daily progress', 'value': 'progress'},
        {'label': 'Learning new things', 'value': 'learning'},
        {'label': 'Helping others', 'value': 'helping'},
        {'label': 'Creative expression', 'value': 'creative'},
      ]
    },
    {
      'question': 'How do you prefer to learn?',
      'key': 'learning_style',
      'options': [
        {'label': 'Visual examples', 'value': 'visual'},
        {'label': 'Hands-on practice', 'value': 'practical'},
        {'label': 'Step-by-step guides', 'value': 'structured'},
        {'label': 'Discussion & debate', 'value': 'interactive'},
        {'label': 'Self-paced study', 'value': 'independent'},
      ]
    },
    {
      'question': 'When facing challenges, you tend to...',
      'key': 'problem_solving',
      'options': [
        {'label': 'Break it into steps', 'value': 'systematic'},
        {'label': 'Try different approaches', 'value': 'experimental'},
        {'label': 'Seek advice first', 'value': 'collaborative'},
        {'label': 'Research thoroughly', 'value': 'analytical'},
        {'label': 'Trust your instincts', 'value': 'intuitive'},
      ]
    },
  ];

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
    _animationController.forward();
    
    // Initialize custom answer controllers for each scenario
    for (final scenario in _scenarios) {
      _customAnswerControllers[scenario['key']] = TextEditingController();
    }
    
    // Load existing data from backend
    _loadFromBackend();
  }

  @override
  void didUpdateWidget(covariant EnhancedPersonalConfigurationStep oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    // Do NOT reload data when navigating back - preserve user's current form state
    // Data should only be loaded on initial mount, not when returning from other steps
  }
  
  @override
  void dispose() {
    _animationController.dispose();
    _nameController.dispose();
    _currentSituationController.dispose();
    _aspirationsController.dispose();
    _customInterestController.dispose();
    _customChallengeController.dispose();
    
    // Dispose custom answer controllers
    for (final controller in _customAnswerControllers.values) {
      controller.dispose();
    }
    
    // Cancel save timer
    _saveDebounceTimer?.cancel();
    
    super.dispose();
  }

  Future<void> _handleComplete() async {
    // Ensure any pending changes are saved immediately before completing
    await _saveImmediately();
    
    // Collect custom answers
    final Map<String, String> customAnswers = {};
    for (final entry in _customAnswerControllers.entries) {
      if (entry.value.text.trim().isNotEmpty) {
        customAnswers[entry.key] = entry.value.text.trim();
      }
    }
    
    // Convert custom life areas to serializable format for completion
    final serializableCustomAreas = _customAreas.map((area) => {
      'name': area['name'],
      'icon_codepoint': (area['icon'] as IconData).codePoint,
      'icon_font_family': (area['icon'] as IconData).fontFamily,
      'color_value': (area['color'] as Color).value,
    }).toList();

    final configData = {
      // Avatar and name
      'avatar_id': _avatarId,
      'preferred_name': _nameController.text.trim(),
      
      // Life Areas
      'life_area_ids': _selectedAreas.toList(),
      'custom_life_areas': serializableCustomAreas,
      
      // Story data (basic - most will be collected by AI via MCP)
      'current_situation': _currentSituationController.text.trim(),
      'aspirations': _aspirationsController.text.trim(),
      'interests': _interests.toList(),
      'challenges': _challenges.toList(),
      
      // Preferences
      'preferences': _preferences,
      'custom_answers': customAnswers,
      
      // Skip goal creation - goals will be created during AI conversation
      'skip_goal_creation': true,
      'use_ai_collection': true,
    };
    
    widget.onNext(configData);
  }

  bool get _canComplete => _selectedAreas.isNotEmpty;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: Stack(
            children: [
              Column(
                children: [
                  // Header
                  PersonalConfigHeader(
                    avatarId: _avatarId,
                    aiAvatars: _aiAvatars,
                    onAvatarTap: () => _showAvatarOptions(theme),
                  ),
                  
                  // Scrollable content
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Name Input Section
                          NameSection(
                            nameController: _nameController,
                            onSave: _saveToBackend,
                            onChanged: () => setState(() {}),
                          ),
                          
                          const SizedBox(height: 40),
                          
                          // Life Areas Section
                          LifeAreasSection(
                            lifeAreas: _getDisplayLifeAreas(),
                            selectedAreas: _selectedAreas,
                            customAreas: _getDisplayCustomAreas(),
                            onAreaToggle: (areaId) {
                              setState(() {
                                if (_selectedAreas.contains(areaId)) {
                                  _selectedAreas.remove(areaId);
                                  print('📤 Removed life area $areaId');
                                } else {
                                  _selectedAreas.add(areaId);
                                  print('📤 Added life area $areaId');
                                }
                                print('📤 Selected areas now: $_selectedAreas');
                              });
                              _saveToBackend();
                            },
                            onAddCustomArea: () => _showCustomAreaDialog(theme),
                            onRemoveCustomArea: (area) async {
                              setState(() {
                                _customAreas.remove(area);
                              });
                              
                              // Delete from backend if it has an ID
                              if (area['id'] != null) {
                                await _deleteCustomLifeArea(area['id']);
                              }
                              
                              _saveToBackend();
                            },
                          ),
                          
                          const SizedBox(height: 40),
                          
                          // Story Builder Section
                          StorySection(
                            currentSituationController: _currentSituationController,
                            aspirationsController: _aspirationsController,
                            interests: _interests,
                            challenges: _challenges,
                            interestSuggestions: _interestSuggestions,
                            challengeSuggestions: _challengeSuggestions,
                            onSave: _saveToBackend,
                          ),
                          
                          const SizedBox(height: 40),
                          
                          // Preferences Section
                          PreferencesSection(
                            scenarios: _scenarios,
                            preferences: _preferences,
                            customAnswerControllers: _customAnswerControllers,
                            onPreferenceSelected: _selectPreference,
                            onSave: _saveToBackend,
                          ),
                          
                          const SizedBox(height: 40),
                          
                          // AI Collection Note
                          _buildAINote(theme),
                          
                          const SizedBox(height: 80), // Extra space for navigation
                        ],
                      ),
                    ),
                  ),
                  
                  // Navigation buttons
                  Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: NavigationButtons(
                      isSaving: _isSaving,
                      onNext: () {
                        _saveImmediately().then((_) {
                          widget.onNext({
                            'preferred_name': _nameController.text.trim(),
                            'life_area_ids': _selectedAreas.toList(),
                            'custom_life_areas': _customAreas,
                            'current_situation': _currentSituationController.text.trim(),
                            'aspirations': _aspirationsController.text.trim(),
                            'interests': _interests.toList(),
                            'challenges': _challenges.toList(),
                            'preferences': _preferences,
                          });
                        });
                      },
                      onPrevious: widget.onPrevious,
                      nextEnabled: _nameController.text.trim().isNotEmpty,
                    ),
                  ),
                ],
              ),
              
              // Floating save indicator
              if (_isSaving)
                Positioned(
                  top: 20,
                  right: 20,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withOpacity(0.9),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: theme.colorScheme.shadow.withOpacity(0.2),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 12,
                          height: 12,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: theme.colorScheme.onPrimary,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Saving...',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onPrimary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          // Avatar upload section
          GestureDetector(
            onTap: () => _showAvatarOptions(theme),
            child: Stack(
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    gradient: _avatarId == null ? LinearGradient(
                      colors: [
                        theme.colorScheme.primary.withOpacity(0.1),
                        theme.colorScheme.secondary.withOpacity(0.1),
                      ],
                    ) : null,
                    borderRadius: BorderRadius.circular(40),
                    border: Border.all(
                      color: theme.colorScheme.primary.withOpacity(0.3),
                      width: 2,
                    ),
                  ),
                  child: Center(
                    child: _avatarId == null || _avatarId!.isEmpty
                      ? Icon(
                          Icons.person,
                          size: 50,
                          color: theme.colorScheme.primary,
                        )
                      : _isEmojiAvatar(_avatarId!)
                          ? Text(
                              _avatarId!,
                              style: const TextStyle(fontSize: 50),
                            )
                          : ClipRRect(
                              borderRadius: BorderRadius.circular(38),
                              child: Image.network(
                                AvatarUploadService.getAvatarImageUrl(_avatarId!),
                                fit: BoxFit.cover,
                                width: 80,
                                height: 80,
                                errorBuilder: (context, error, stackTrace) => Icon(
                                  Icons.person,
                                  size: 50,
                                  color: theme.colorScheme.primary,
                                ),
                              ),
                            ),
                  ),
                ),
                Positioned(
                  bottom: 0,
                  right: 0,
                  child: Container(
                    width: 24,
                    height: 24,
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: theme.colorScheme.surface,
                        width: 2,
                      ),
                    ),
                    child: Icon(
                      Icons.camera_alt,
                      size: 12,
                      color: theme.colorScheme.onPrimary,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Tell Us About Yourself',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 6),
          Text(
            'Quick setup to personalize your AI assistant',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.7),
            ),
            textAlign: TextAlign.center,
          ),
          
        ],
      ),
    );
  }

  Widget _buildNameSection(ThemeData theme) {
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
              _saveToBackend();
            }
          },
          child: TextField(
            controller: _nameController,
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
            onChanged: (value) => setState(() {}),
            onSubmitted: (value) => _saveToBackend(),
          ),
        ),
      ],
    );
  }

  Widget _buildLifeAreasSection(ThemeData theme) {
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
            ..._lifeAreas.map((area) => _buildCompactLifeArea(theme, area)),
            _buildAddCustomAreaChip(theme),
          ],
        ),
        
        // Custom areas
        if (_customAreas.isNotEmpty) ...[
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _customAreas.map((area) => _buildCustomAreaChip(theme, area)).toList(),
          ),
        ],
        
        // Selection summary
        if (_selectedAreas.isNotEmpty || _customAreas.isNotEmpty) ...[
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
                  '${_selectedAreas.length + _customAreas.length} areas selected',
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

  Widget _buildCompactLifeArea(ThemeData theme, Map<String, dynamic> area) {
    final isSelected = _selectedAreas.contains(area['id']);
    final color = area['color'] as Color;
    
    return GestureDetector(
      onTap: () {
        setState(() {
          if (isSelected) {
            _selectedAreas.remove(area['id']);
            print('📤 Removed life area ${area['id']} (${area['name']})');
          } else {
            _selectedAreas.add(area['id']);
            print('📤 Added life area ${area['id']} (${area['name']})');
          }
          print('📤 Selected areas now: $_selectedAreas');
        });
        _saveToBackend();
      },
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

  Widget _buildAddCustomAreaChip(ThemeData theme) {
    return GestureDetector(
      onTap: () => _showCustomAreaDialog(theme),
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
              'Add custom',
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

  Widget _buildCustomAreaChip(ThemeData theme, Map<String, dynamic> area) {
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
            onTap: () {
              setState(() {
                _customAreas.remove(area);
              });
            },
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

  Widget _buildStorySection(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📖 Your Story',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Help your AI understand your journey',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
        const SizedBox(height: 16),
        
        // Current situation
        _buildStoryField(
          theme,
          'Current Situation',
          'Where are you in life right now?',
          _currentSituationController,
          maxLength: 150,
        ),
        
        const SizedBox(height: 16),
        
        // Interests
        _buildTagSection(
          theme,
          'Interests',
          'What are you passionate about?',
          _interests,
          _interestSuggestions,
        ),
        
        const SizedBox(height: 16),
        
        // Challenges
        _buildTagSection(
          theme,
          'Challenges',
          'What would you like to improve?',
          _challenges,
          _challengeSuggestions,
        ),
        
        const SizedBox(height: 16),
        
        // Aspirations
        _buildStoryField(
          theme,
          'Aspirations',
          'What do you hope to achieve?',
          _aspirationsController,
          maxLength: 150,
        ),
      ],
    );
  }

  Widget _buildStoryField(
    ThemeData theme,
    String title,
    String hint,
    TextEditingController controller, {
    int maxLength = 100,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Focus(
          onFocusChange: (hasFocus) {
            if (!hasFocus) {
              // Save when the field loses focus
              print('📝 Story field "$title" lost focus, saving to backend...');
              _saveToBackend();
            }
          },
          child: TextField(
            controller: controller,
            decoration: InputDecoration(
              hintText: hint,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: theme.colorScheme.surfaceVariant.withOpacity(0.3),
              contentPadding: const EdgeInsets.all(12),
              counterText: '${controller.text.length}/$maxLength',
            ),
            maxLines: 3,
            maxLength: maxLength,
            onChanged: (value) => setState(() {}),
            onSubmitted: (value) => _saveToBackend(),
          ),
        ),
      ],
    );
  }

  Widget _buildTagSection(
    ThemeData theme,
    String title,
    String hint,
    Set<String> selectedTags,
    List<String> suggestions,
  ) {
    final isInterests = title == 'Interests';
    final customController = isInterests ? _customInterestController : _customChallengeController;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          hint,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.6),
          ),
        ),
        const SizedBox(height: 8),
        
        // All available chips (suggestions + custom added items)
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            // Suggestion chips
            ...suggestions.map((tag) {
              final isSelected = selectedTags.contains(tag);
              return FilterChip(
                label: Text(tag),
                selected: isSelected,
                onSelected: (selected) {
                  setState(() {
                    if (selected) {
                      selectedTags.add(tag);
                    } else {
                      selectedTags.remove(tag);
                    }
                  });
                  _saveToBackend();
                },
                labelStyle: theme.textTheme.bodySmall,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              );
            }),
            // Custom added chips that aren't in suggestions
            ...selectedTags.where((tag) => !suggestions.contains(tag)).map((tag) {
              return FilterChip(
                label: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(tag),
                    const SizedBox(width: 4),
                    Icon(Icons.star, size: 12, color: theme.colorScheme.primary),
                  ],
                ),
                selected: true,
                onSelected: (selected) {
                  setState(() {
                    selectedTags.remove(tag);
                  });
                  _saveToBackend();
                },
                labelStyle: theme.textTheme.bodySmall,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                backgroundColor: theme.colorScheme.primaryContainer.withOpacity(0.3),
              );
            }),
          ],
        ),
        
        const SizedBox(height: 12),
        
        // Custom input
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: customController,
                decoration: InputDecoration(
                  hintText: 'Add custom ${title.toLowerCase()}...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  filled: true,
                  fillColor: theme.colorScheme.surfaceVariant.withOpacity(0.2),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  isDense: true,
                ),
                textCapitalization: TextCapitalization.words,
                onSubmitted: (value) => _addCustomTag(selectedTags, customController),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: () => _addCustomTag(selectedTags, customController),
              icon: const Icon(Icons.add),
              style: IconButton.styleFrom(
                backgroundColor: theme.colorScheme.primary.withOpacity(0.1),
                foregroundColor: theme.colorScheme.primary,
              ),
            ),
          ],
        ),
      ],
    );
  }
  
  void _addCustomTag(Set<String> selectedTags, TextEditingController controller) {
    final value = controller.text.trim();
    if (value.isNotEmpty && !selectedTags.contains(value)) {
      setState(() {
        selectedTags.add(value);
        controller.clear();
      });
    }
  }

  Widget _buildPreferencesSection(ThemeData theme) {
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
        ..._scenarios.map((scenario) => _buildHorizontalScenarioCard(theme, scenario)),
      ],
    );
  }

  Widget _buildHorizontalScenarioCard(ThemeData theme, Map<String, dynamic> scenario) {
    final isCustomSelected = _preferences[scenario['key']] == 'custom';
    final customController = _customAnswerControllers[scenario['key']]!;
    
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
            scenario['question'],
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
                    ...scenario['options'].map<Widget>((option) {
                      final isSelected = _preferences[scenario['key']] == option['value'];
                      return Expanded(
                        child: Container(
                          margin: const EdgeInsets.only(right: 8),
                          child: GestureDetector(
                            onTap: () => _selectPreference(scenario['key'], option['value']),
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
                    if (isCustomSelected && customController.text.trim().isNotEmpty)
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
                                      customController.text.trim(),
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
                            onTap: () => _selectPreference(scenario['key'], 'custom'),
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
                  _saveToBackend();
                  // Update the UI to show the new text in the pill
                  setState(() {});
                }
              },
              child: TextField(
                controller: customController,
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
                  _saveToBackend();
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

  Widget _buildAINote(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer.withOpacity(0.5),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(
            Icons.chat,
            color: theme.colorScheme.onSecondaryContainer,
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Your AI assistant will learn more about you through our conversations',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSecondaryContainer,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavigationButtons(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: theme.colorScheme.shadow.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: OutlinedButton(
              onPressed: widget.onPrevious,
              child: const Text('Previous'),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            flex: 2,
            child: ElevatedButton(
              onPressed: _canComplete ? _handleComplete : null,
              child: const Text('Complete Setup'),
            ),
          ),
        ],
      ),
    );
  }

  void _selectPreference(String key, String value) {
    setState(() {
      // If the same option is selected, deselect it (toggle behavior)
      if (_preferences[key] == value) {
        _preferences.remove(key);
        // If deselecting custom, clear the custom answer
        if (value == 'custom' && _customAnswerControllers.containsKey(key)) {
          _customAnswerControllers[key]!.clear();
        }
      } else {
        _preferences[key] = value;
      }
    });
    _saveToBackend();
  }

  void _showCustomAreaDialog(ThemeData theme) {
    final nameController = TextEditingController();
    IconData selectedIcon = Icons.category;
    Color selectedColor = Colors.blue;
    
    final availableIcons = [
      // Work & Career
      Icons.work, Icons.business_center, Icons.laptop_mac, Icons.engineering,
      Icons.code, Icons.design_services, Icons.analytics, Icons.campaign,
      
      // Health & Fitness
      Icons.fitness_center, Icons.sports_soccer, Icons.directions_run, Icons.pool,
      Icons.self_improvement, Icons.spa, Icons.medical_services, Icons.psychology,
      
      // Home & Family
      Icons.home, Icons.family_restroom, Icons.child_care, Icons.pets,
      Icons.home_repair_service, Icons.cleaning_services, Icons.kitchen, Icons.bed,
      
      // Learning & Education
      Icons.school, Icons.menu_book, Icons.science, Icons.language,
      Icons.computer, Icons.library_books, Icons.quiz, Icons.lightbulb,
      
      // Creative & Arts
      Icons.palette, Icons.camera_alt, Icons.music_note, Icons.theater_comedy,
      Icons.draw, Icons.video_camera_front, Icons.mic, Icons.piano,
      
      // Social & Entertainment
      Icons.people, Icons.celebration, Icons.local_bar, Icons.restaurant,
      Icons.movie, Icons.games, Icons.beach_access, Icons.park,
      
      // Travel & Adventure
      Icons.travel_explore, Icons.flight, Icons.directions_car, Icons.hiking,
      Icons.sailing, Icons.terrain, Icons.explore, Icons.map,
      
      // Finance & Business
      Icons.account_balance_wallet, Icons.savings, Icons.trending_up, Icons.store,
      Icons.receipt_long, Icons.credit_card, Icons.paid, Icons.monetization_on,
      
      // Hobbies & Interests
      Icons.sports_esports, Icons.extension, Icons.auto_fix_high, Icons.forest,
      Icons.yard, Icons.volunteer_activism, Icons.favorite, Icons.star,
    ];
    
    final availableColors = [
      Colors.red, Colors.blue, Colors.green, Colors.purple,
      Colors.orange, Colors.teal, Colors.pink, Colors.indigo,
      Colors.amber, Colors.cyan, Colors.lime, Colors.deepOrange,
    ];
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Add Custom Life Area'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(
                    labelText: 'Area Name',
                    hintText: 'e.g., Side Projects',
                  ),
                ),
                const SizedBox(height: 16),
                
                Text(
                  'Choose Icon',
                  style: theme.textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                Container(
                  height: 120,
                  decoration: BoxDecoration(
                    border: Border.all(color: theme.colorScheme.outline.withOpacity(0.2)),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(8),
                    child: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: availableIcons.map((icon) {
                        return GestureDetector(
                          onTap: () => setDialogState(() => selectedIcon = icon),
                          child: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: selectedIcon == icon 
                                  ? selectedColor.withOpacity(0.2)
                                  : null,
                              borderRadius: BorderRadius.circular(8),
                              border: selectedIcon == icon 
                                  ? Border.all(color: selectedColor, width: 2)
                                  : Border.all(color: theme.colorScheme.outline.withOpacity(0.1)),
                            ),
                            child: Icon(icon, color: selectedColor, size: 20),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
                
                const SizedBox(height: 16),
                
                Text(
                  'Choose Color',
                  style: theme.textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: availableColors.map((color) {
                    return GestureDetector(
                      onTap: () => setDialogState(() => selectedColor = color),
                      child: Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(16),
                          border: selectedColor == color 
                              ? Border.all(color: Colors.white, width: 3)
                              : null,
                          boxShadow: selectedColor == color ? [
                            BoxShadow(
                              color: color.withOpacity(0.5),
                              blurRadius: 4,
                              offset: const Offset(0, 2),
                            ),
                          ] : null,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                if (nameController.text.trim().isNotEmpty) {
                  try {
                    setState(() {
                      _customAreas.add({
                        'name': nameController.text.trim(),
                        'icon': _getStringFromIcon(selectedIcon),
                        'color': _getStringFromColor(selectedColor),
                      });
                    });
                    Navigator.of(context).pop();
                    
                    // Delay the save slightly to ensure UI is stable
                    Future.delayed(const Duration(milliseconds: 100), () {
                      _saveToBackend();
                    });
                  } catch (e) {
                    print('🔴 Error adding custom area: $e');
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Failed to add custom area: $e'),
                          backgroundColor: Colors.red,
                        ),
                      );
                    }
                  }
                }
              },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
  }
  
  void _showAvatarOptions(ThemeData theme) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: BoxDecoration(
          color: theme.colorScheme.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: theme.colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'Choose Profile Photo',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildAvatarOption(
                  theme,
                  icon: Icons.camera_alt,
                  label: 'Camera',
                  onTap: () {
                    Navigator.pop(context);
                    _takePhoto();
                  },
                ),
                _buildAvatarOption(
                  theme,
                  icon: Icons.photo_library,
                  label: 'Gallery',
                  onTap: () {
                    Navigator.pop(context);
                    _pickFromGallery();
                  },
                ),
                _buildAvatarOption(
                  theme,
                  icon: Icons.auto_awesome,
                  label: 'AI Avatar',
                  onTap: () {
                    Navigator.pop(context);
                    _generateAIAvatar();
                  },
                ),
                if (_avatarId != null)
                  _buildAvatarOption(
                    theme,
                    icon: Icons.delete,
                    label: 'Remove',
                    onTap: () {
                      Navigator.pop(context);
                      _removeAvatar();
                    },
                  ),
              ],
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
  
  Widget _buildAvatarOption(
    ThemeData theme, {
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withOpacity(0.3),
              borderRadius: BorderRadius.circular(30),
            ),
            child: Icon(
              icon,
              color: theme.colorScheme.primary,
              size: 30,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: theme.textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
  
  Future<void> _takePhoto() async {
    try {
      final result = await showDialog<Map<String, dynamic>>(
        context: context,
        builder: (context) => const ImageCropperDialog(
          title: 'Take Photo for Profile',
        ),
      );
      
      if (result != null) {
        final imageData = result['imageData'] as Uint8List;
        final filename = result['filename'] as String;
        final avatarResponse = await AvatarUploadService.uploadAvatarToBackend(imageData, filename);
        setState(() {
          _avatarId = avatarResponse['avatar_id'] as String;
        });
        _saveToBackend();
      }
    } catch (e) {
      print('Error taking photo: $e');
      _showErrorSnackBar('Failed to take photo. Please try again.');
    }
  }
  
  Future<void> _pickFromGallery() async {
    try {
      final result = await showDialog<Map<String, dynamic>>(
        context: context,
        builder: (context) => const ImageCropperDialog(
          title: 'Select Photo for Profile',
        ),
      );
      
      if (result != null) {
        final imageData = result['imageData'] as Uint8List;
        final filename = result['filename'] as String;
        final avatarResponse = await AvatarUploadService.uploadAvatarToBackend(imageData, filename);
        setState(() {
          _avatarId = avatarResponse['avatar_id'] as String;
        });
        _saveToBackend();
      }
    } catch (e) {
      print('Error picking from gallery: $e');
      _showErrorSnackBar('Failed to pick image. Please try again.');
    }
  }
  
  void _generateAIAvatar() {
    _showAIAvatarPicker();
  }
  
  
  bool _isEmojiAvatar(String path) {
    return _aiAvatars.contains(path);
  }
  
  /// Map string icon names to IconData objects
  IconData _getIconFromString(String iconName) {
    switch (iconName) {
      case 'favorite':
        return Icons.favorite;
      case 'trending_up':
        return Icons.trending_up;
      case 'people':
        return Icons.people;
      case 'psychology':
        return Icons.psychology;
      case 'celebration':
        return Icons.celebration;
      case 'account_balance_wallet':
        return Icons.account_balance_wallet;
      case 'home':
        return Icons.home;
      case 'palette':
        return Icons.palette;
      case 'work':
      case 'business_center':
        return Icons.work;
      case 'fitness_center':
      case 'sports':
        return Icons.fitness_center;
      case 'school':
        return Icons.school;
      case 'category':
      default:
        return Icons.category;
    }
  }
  
  /// Convert hex color string to Color object
  Color _getColorFromString(String colorHex) {
    try {
      // Remove # if present and add FF for full opacity
      final hex = colorHex.replaceAll('#', '');
      return Color(int.parse('FF$hex', radix: 16));
    } catch (e) {
      return const Color(0xFF6366f1); // Default color
    }
  }
  
  /// Convert string-based life areas to display format with IconData and Color objects
  List<Map<String, dynamic>> _getDisplayLifeAreas() {
    return _lifeAreas.map((area) {
      return {
        'id': area['id'],
        'name': area['name'],
        'icon': _getIconFromString(area['icon'] as String),
        'color': _getColorFromString(area['color'] as String),
      };
    }).toList();
  }
  
  /// Convert string-based custom areas to display format with IconData and Color objects
  List<Map<String, dynamic>> _getDisplayCustomAreas() {
    return _customAreas.map((area) {
      return {
        'name': area['name'],
        'icon': area['icon'] is String 
            ? _getIconFromString(area['icon'] as String)
            : area['icon'], // Already converted
        'color': area['color'] is String 
            ? _getColorFromString(area['color'] as String)
            : area['color'], // Already converted
      };
    }).toList();
  }
  
  /// Convert IconData to string identifier
  String _getStringFromIcon(IconData icon) {
    if (icon == Icons.favorite) return 'favorite';
    if (icon == Icons.trending_up) return 'trending_up';
    if (icon == Icons.people) return 'people';
    if (icon == Icons.psychology) return 'psychology';
    if (icon == Icons.celebration) return 'celebration';
    if (icon == Icons.account_balance_wallet) return 'account_balance_wallet';
    if (icon == Icons.home) return 'home';
    if (icon == Icons.palette) return 'palette';
    if (icon == Icons.work) return 'work';
    if (icon == Icons.fitness_center) return 'fitness_center';
    if (icon == Icons.school) return 'school';
    return 'category'; // default
  }
  
  /// Convert Color to hex string
  String _getStringFromColor(Color color) {
    return '#${color.value.toRadixString(16).substring(2).toUpperCase()}';
  }
  
  void _showErrorSnackBar(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
  
  void _removeAvatar() {
    setState(() {
      _avatarId = null;
    });
    _saveToBackend();
  }
  
  void _showAIAvatarPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.7,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          children: [
            // Handle bar
            Container(
              margin: const EdgeInsets.symmetric(vertical: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            
            // Title
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Text(
                'Choose AI Avatar',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Avatar grid
            Expanded(
              child: GridView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 4,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  childAspectRatio: 1,
                ),
                itemCount: _aiAvatars.length,
                itemBuilder: (context, index) {
                  final avatar = _aiAvatars[index];
                  final isSelected = _avatarId == avatar;
                  
                  return GestureDetector(
                    onTap: () {
                      setState(() {
                        _avatarId = avatar;
                      });
                      Navigator.of(context).pop();
                      _saveToBackend();
                    },
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      decoration: BoxDecoration(
                        color: isSelected 
                            ? Theme.of(context).colorScheme.primaryContainer
                            : Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(16),
                        border: isSelected ? Border.all(
                          color: Theme.of(context).colorScheme.primary,
                          width: 3,
                        ) : null,
                        boxShadow: isSelected ? [
                          BoxShadow(
                            color: Theme.of(context).colorScheme.primary.withOpacity(0.2),
                            blurRadius: 8,
                            offset: const Offset(0, 4),
                          ),
                        ] : null,
                      ),
                      child: Center(
                        child: Text(
                          avatar,
                          style: const TextStyle(fontSize: 48),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            
            // Close button
            Padding(
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  // Debounced auto-save functionality
  void _saveToBackend() {
    // Don't save during initial loading
    if (_isInitialLoading) {
      print('🚫 Skipping save during initial loading');
      return;
    }
    
    // Cancel any existing timer
    _saveDebounceTimer?.cancel();
    
    // Set up new timer with longer delay to reduce API calls
    _saveDebounceTimer = Timer(const Duration(seconds: 3), () {
      _performSave();
    });
  }
  
  Future<void> _performSave() async {
    if (_isSaving) {
      print('🔄 Save already in progress, skipping...');
      return;
    }
    
    setState(() {
      _isSaving = true;
    });
    
    try {
      print('🔄 Auto-saving to backend...');
      print('🔄 Custom areas count: ${_customAreas.length}');
      
      // Convert custom life areas to serializable format (already strings!)
      List<Map<String, dynamic>> serializableCustomAreas = [];
      for (final area in _customAreas) {
        try {
          final serializedArea = {
            'name': area['name'],
            'icon': area['icon'], // Already a string
            'color': area['color'], // Already a hex string
            'is_custom': true,
          };
          serializableCustomAreas.add(serializedArea);
          print('✅ Serialized custom area: ${area['name']}');
        } catch (e) {
          print('🔴 Error serializing custom area ${area['name']}: $e');
          print('🔴 Area data: $area');
          rethrow;
        }
      }

      final currentData = {
        'avatar_id': _avatarId,
        'preferred_name': _nameController.text.trim(),
        'life_area_ids': _selectedAreas.toList(),
        'custom_life_areas': serializableCustomAreas,
        'current_situation': _currentSituationController.text.trim(),
        'aspirations': _aspirationsController.text.trim().isNotEmpty 
            ? [_aspirationsController.text.trim()] 
            : [], // Convert string to list for backend
        'interests': _interests.toList(),
        'challenges': _challenges.toList(),
        'preferences': _preferences,
        'custom_answers': Map.fromEntries(
          _customAnswerControllers.entries
              .where((entry) => entry.value.text.trim().isNotEmpty)
              .map((entry) => MapEntry(entry.key, entry.value.text.trim())),
        ),
      };
      
      print('📦 Saving personal config data: $currentData');
      
      // Save directly to personal-config endpoints (NO temp_data!)
      try {
        await _saveToPersonalConfigEndpoints(currentData);
        print('✅ Personal config data saved successfully');
        
        // Save custom life areas to CustomLifeArea table
        await _saveCustomLifeAreas(currentData);
        print('✅ Custom life areas saved successfully');
      } catch (saveError) {
        print('🔴 Error saving to backend: $saveError');
        throw saveError;
      }
    } catch (e) {
      print('🔴 Error saving to backend: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }
  
  // Immediate save for critical actions (like completing step)
  Future<void> _saveImmediately() async {
    _saveDebounceTimer?.cancel(); // Cancel any pending debounced save
    await _performSave(); // Save immediately
  }
  
  Future<void> _saveToPersonalConfigEndpoints(Map<String, dynamic> data) async {
    final token = await StorageService.getAccessToken();
    if (token == null) throw Exception('No access token');

    // Save to personal-config/profile endpoint - only profile fields
    final profileData = <String, dynamic>{};
    
    // Only include non-null and relevant fields for PersonalProfile
    if (data['preferred_name'] != null) {
      profileData['preferred_name'] = data['preferred_name'];
    }
    if (data['avatar_id'] != null) {
      profileData['avatar_id'] = data['avatar_id'];
    }
    if (data['current_situation'] != null && data['current_situation'].toString().isNotEmpty) {
      profileData['current_situation'] = data['current_situation'];
    }
    if (data['aspirations'] != null) {
      profileData['aspirations'] = data['aspirations'];
    }
    if (data['interests'] != null) {
      profileData['interests'] = data['interests'];
    }
    if (data['challenges'] != null) {
      profileData['challenges'] = data['challenges'];
    }
    if (data['preferences'] != null) {
      profileData['preferences'] = data['preferences'];
    }
    if (data['custom_answers'] != null) {
      profileData['custom_answers'] = data['custom_answers'];
    }
    if (data['life_area_ids'] != null) {
      profileData['selected_life_areas'] = data['life_area_ids'];
    }
    
    print('🔍 SAVE: Sending profile data: $profileData');

    final response = await Dio().post(
      '${ApiConfig.baseUrl}/api/personal-config/profile',
      data: profileData,
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to save profile: ${response.statusCode}');
    }

    print('✅ Saved to personal-config/profile endpoint');
  }
  
  Future<void> _saveCustomLifeAreas(Map<String, dynamic> data) async {
    final token = await StorageService.getAccessToken();
    if (token == null) throw Exception('No access token');

    // Save custom life areas to the CustomLifeArea table
    if (data['custom_life_areas'] != null) {
      final customAreas = data['custom_life_areas'] as List;
      
      // Batch save: only save new areas that don't exist yet
      int savedCount = 0;
      for (final areaData in customAreas) {
        try {
          final response = await Dio().post(
            '${ApiConfig.baseUrl}/api/personal-config/life-areas',
            data: areaData,
            options: Options(
              headers: {
                'Authorization': 'Bearer $token',
                'Content-Type': 'application/json',
              },
              validateStatus: (status) => status! < 500, // Accept 409 duplicates
            ),
          );

          if (response.statusCode == 200 || response.statusCode == 201) {
            savedCount++;
          } else if (response.statusCode == 409) {
            print('ℹ️ Custom area "${areaData['name']}" already exists, skipping');
          } else {
            print('⚠️ Failed to save custom life area: ${response.statusCode}');
          }
        } catch (e) {
          print('⚠️ Error saving custom life area "${areaData['name']}": $e');
          // Continue with other areas instead of failing completely
        }
      }
      
      print('✅ Saved $savedCount custom life areas');
    }
  }

  Future<void> _deleteCustomLifeArea(int areaId) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) {
        print('⚠️ No access token for deleting life area');
        return;
      }

      print('🗑️ Deleting custom life area ID: $areaId');
      final response = await Dio().delete(
        '${ApiConfig.baseUrl}/api/personal-config/life-areas/$areaId',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        print('✅ Successfully deleted custom life area ID: $areaId');
      } else {
        print('⚠️ Failed to delete custom life area: ${response.statusCode}');
      }
    } catch (e) {
      print('🔴 Error deleting custom life area: $e');
    }
  }

  Future<void> _loadFromBackend() async {
    try {
      print('📥 Loading personal config from backend...');
      
      // Load data directly from backend endpoints
      final loadedData = await ref.read(onboardingProvider.notifier).getPersonalConfigData();
      
      if (loadedData != null) {
        print('📦 Loaded personal config data: $loadedData');
        
        if (mounted) {
          setState(() {
            // Load avatar (check for both null and empty string)
            if (loadedData['avatar_id'] != null && loadedData['avatar_id'].toString().isNotEmpty) {
              _avatarId = loadedData['avatar_id'] as String;
            } else {
              _avatarId = null; // Ensure empty strings are treated as null
            }
            
            // Load name
            if (loadedData['preferred_name'] != null) {
              _nameController.text = loadedData['preferred_name'] as String;
            }
          
          // Load life areas
          if (loadedData['life_area_ids'] != null) {
            _selectedAreas.clear();
            final loadedAreaIds = (loadedData['life_area_ids'] as List).cast<int>();
            _selectedAreas.addAll(loadedAreaIds);
            print('📥 Loaded life area IDs: $loadedAreaIds');
            print('📥 Selected areas after loading: $_selectedAreas');
          }
          
          // Load custom life areas from the personal config API
          if (loadedData['custom_life_areas'] != null) {
            _customAreas.clear();
            final customAreasData = loadedData['custom_life_areas'] as List;
            print('📥 Loading ${customAreasData.length} custom life areas from backend');
            
            for (final areaData in customAreasData) {
              final area = Map<String, dynamic>.from(areaData as Map);
              print('📥 Processing area: ${area['name']}, is_custom: ${area['is_custom']}, icon: ${area['icon']}');
              
              // Only process areas that are marked as custom
              final isCustom = area['is_custom'] == true;
              if (!isCustom) {
                print('📥 Skipping built-in area: ${area['name']} (is_custom: ${area['is_custom']})');
                continue;
              }
              
              // Store the area data as-is with string values for consistency
              _customAreas.add({
                'id': area['id'], // Include ID for deletion
                'name': area['name'],
                'icon': area['icon'] ?? 'category',
                'color': area['color'] ?? '#6366f1',
              });
              
              print('📥 Loaded custom area: ${area['name']} with color: ${area['color']} and icon: ${area['icon']}');
            }
          }
          
          // Load story fields
          if (loadedData['current_situation'] != null) {
            _currentSituationController.text = loadedData['current_situation'] as String;
          }
          if (loadedData['aspirations'] != null) {
            // Handle aspirations as either string or list
            final aspirationsData = loadedData['aspirations'];
            if (aspirationsData is String) {
              _aspirationsController.text = aspirationsData;
            } else if (aspirationsData is List && aspirationsData.isNotEmpty) {
              _aspirationsController.text = aspirationsData.first.toString();
            }
          }
          
          // Load interests and challenges
          if (loadedData['interests'] != null) {
            _interests.clear();
            _interests.addAll((loadedData['interests'] as List).cast<String>());
          }
          if (loadedData['challenges'] != null) {
            _challenges.clear();
            _challenges.addAll((loadedData['challenges'] as List).cast<String>());
          }
          
          // Load preferences
          if (loadedData['preferences'] != null) {
            _preferences.clear();
            final preferencesData = Map<String, dynamic>.from(loadedData['preferences'] as Map);
            _preferences.addAll(preferencesData.cast<String, String>());
          }
          
          // Load custom answers
          if (loadedData['custom_answers'] != null) {
            final customAnswers = Map<String, dynamic>.from(loadedData['custom_answers'] as Map);
            for (final entry in customAnswers.entries) {
              if (_customAnswerControllers.containsKey(entry.key)) {
                _customAnswerControllers[entry.key]!.text = entry.value.toString();
              }
            }
          }
          });
        }
        
        print('✅ Personal config data loaded successfully');
        
        // Enable auto-save after initial loading is complete
        _isInitialLoading = false;
      } else {
        print('📭 No existing personal config data found');
      }
    } catch (e) {
      print('🔴 Error loading from backend: $e');
    }
  }
}