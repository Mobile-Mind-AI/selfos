// assistant_creation_step.dart
import 'package:flutter/material.dart';
import 'dart:typed_data';
import 'dart:math' as math;
import 'dart:convert';
import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/avatar_upload_service.dart';
import '../../providers/onboarding_provider.dart';
import '../../providers/assistant_provider.dart';
import '../../widgets/assistant/assistant_hero_section.dart';
import '../../widgets/assistant/assistant_name_input.dart';
import '../../widgets/assistant/avatar_selection_grid.dart';
import '../../widgets/assistant/language_preferences.dart';
import '../../widgets/assistant/personality_setup.dart';
import '../../widgets/assistant/assistant_preview.dart';

// Global storage for custom avatars during onboarding session
final Map<String, Uint8List> _globalCustomAvatars = {};
final Map<String, Map<String, dynamic>> _globalCustomAvatarOptions = {};

// Clear all custom avatars (call when onboarding is reset or completed)
void clearAllCustomAvatars() {
  _globalCustomAvatars.clear();
  _globalCustomAvatarOptions.clear();
}

// Getters for accessing custom avatars from other screens
Map<String, Uint8List> getGlobalCustomAvatars() => _globalCustomAvatars;
Map<String, Map<String, dynamic>> getGlobalCustomAvatarOptions() => _globalCustomAvatarOptions;

/// Assistant creation step where users name their assistant and choose an avatar.
///
/// This is step 2 in the onboarding flow: "Meet Your Assistant"
class AssistantCreationStep extends ConsumerStatefulWidget {
  final Function(Map<String, dynamic>) onNext;
  final VoidCallback onPrevious;

  const AssistantCreationStep({
    super.key,
    required this.onNext,
    required this.onPrevious,
  });

  @override
  ConsumerState<AssistantCreationStep> createState() => _AssistantCreationStepState();
}

class _AssistantCreationStepState extends ConsumerState<AssistantCreationStep>
    with TickerProviderStateMixin {

  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  final TextEditingController _nameController = TextEditingController();
  final FocusNode _nameFocus = FocusNode();

  String _selectedAvatar = 'ai_robot_blue';
  bool _isNameValid = false;

  // Language and preferences
  String _selectedLanguage = 'en';
  bool _requiresConfirmation = true;

  // Personality traits (0-100)
  double _formality = 50.0;
  double _humor = 30.0;
  double _motivation = 60.0;

  String _currentPreview = '';
  Timer? _saveTimer;
  bool _isSaving = false;
  DateTime? _lastSaveAttempt;
  bool _showSaveSuccess = false;

  // Random assistant names
  final List<String> _assistantNames = [
    'Alex', 'Sage', 'Nova', 'Zara', 'Kai', 'Luna', 'Echo', 'Orion',
    'Maya', 'Leo', 'Iris', 'Atlas', 'Vera', 'Felix', 'Cora', 'Max',
    'Ava', 'Neo', 'Zoe', 'Rex', 'Sky', 'Eve', 'Jax', 'Mia'
  ];

  final List<Map<String, String>> _languages = [
    {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
    {'code': 'ru', 'name': 'Русский', 'flag': '🇷🇺'},
    {'code': 'es', 'name': 'Español', 'flag': '🇪🇸'},
    {'code': 'fr', 'name': 'Français', 'flag': '🇫🇷'},
    {'code': 'de', 'name': 'Deutsch', 'flag': '🇩🇪'},
    {'code': 'it', 'name': 'Italiano', 'flag': '🇮🇹'},
    {'code': 'pt', 'name': 'Português', 'flag': '🇵🇹'},
  ];

  // Avatar options with actual image paths
  final List<Map<String, dynamic>> _avatarOptions = [
    {
      'id': 'ai_robot_blue',
      'imagePath': 'assets/images/avatars/ai_robot_blue.png',
      'icon': Icons.smart_toy,
      'colors': [Color(0xFF2196F3), Color(0xFF64B5F6)],
    },
    {
      'id': 'ai_brain_purple',
      'imagePath': 'assets/images/avatars/ai_brain_purple.png',
      'icon': Icons.psychology,
      'colors': [Color(0xFF9C27B0), Color(0xFFBA68C8)],
    },
    {
      'id': 'ai_spark_orange',
      'imagePath': 'assets/images/avatars/ai_spark_orange.png',
      'icon': Icons.auto_awesome,
      'colors': [Color(0xFFFF9800), Color(0xFFFFB74D)],
    },
    {
      'id': 'ai_owl_yellow',
      'imagePath': 'assets/images/avatars/ai_owl_yellow.png',
      'icon': Icons.lightbulb_outline,
      'colors': [Color(0xFFFFC107), Color(0xFFFFD54F)],
    },
    {
      'id': 'ai_crystal_green',
      'imagePath': 'assets/images/avatars/ai_crystal_green.png',
      'icon': Icons.auto_fix_high,
      'colors': [Color(0xFF4CAF50), Color(0xFF81C784)],
    },
    {
      'id': 'ai_agent_gray',
      'imagePath': 'assets/images/avatars/ai_agent_gray.png',
      'icon': Icons.support_agent,
      'colors': [Color(0xFF607D8B), Color(0xFF90A4AE)],
    },
    {
      'id': 'ai_cat_teal',
      'imagePath': 'assets/images/avatars/ai_cat_teal.png',
      'icon': Icons.pets,
      'colors': [Color(0xFF009688), Color(0xFF4DB6AC)],
    },
    {
      'id': 'ai_heart_pink',
      'imagePath': 'assets/images/avatars/ai_heart_pink.png',
      'icon': Icons.favorite_outline,
      'colors': [Color(0xFFE91E63), Color(0xFFF48FB1)],
    },
    {
      'id': 'ai_lightning_indigo',
      'imagePath': 'assets/images/avatars/ai_lightning_indigo.png',
      'icon': Icons.flash_on,
      'colors': [Color(0xFF3F51B5), Color(0xFF7986CB)],
    },
    {
      'id': 'ai_leaf_lime',
      'imagePath': 'assets/images/avatars/ai_leaf_lime.png',
      'icon': Icons.eco,
      'colors': [Color(0xFF8BC34A), Color(0xFFAED581)],
    },
  ];

  @override
  void initState() {
    super.initState();
    _initializeComponent();
  }

  Future<void> _initializeComponent() async {

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

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    ));

    _nameController.addListener(_validateName);

    // Load custom avatars from backend and global storage
    _loadCustomAvatars();
    
    // Load any existing onboarding data (this may set a name)
    await _loadExistingData();

    // Generate random name as default only if no name was loaded
    if (_nameController.text.trim().isEmpty) {
      _refreshAssistantName();
    }

    // Start animations
    _animationController.forward();

    // Update preview
    _updatePreview();
  }

  @override
  void dispose() {
    _saveTimer?.cancel();
    _animationController.dispose();
    _nameController.dispose();
    _nameFocus.dispose();
    super.dispose();
  }

  void _validateName() {
    final name = _nameController.text.trim();
    setState(() {
      _isNameValid = name.length >= 2 && name.length <= 50;
    });
    if (_isNameValid) {
      _debouncedSave();
    }
  }

  void _refreshAssistantName() {
    final randomName = _assistantNames[math.Random().nextInt(_assistantNames.length)];
    _nameController.text = randomName;
    _validateName();
    _updatePreview();
  }

  Map<String, dynamic> _getSelectedAvatarData() {
    return _avatarOptions.firstWhere(
      (avatar) => avatar['id'] == _selectedAvatar,
      orElse: () => _avatarOptions.first,
    );
  }

  void _onAvatarSelected(String avatarId) {
    setState(() {
      _selectedAvatar = avatarId;
    });
    // Use debounced save to prevent rate limiting
    _debouncedSave();
  }

  void _onAvatarUploaded(String avatarId, Uint8List imageData) {
    setState(() {
      // Store custom avatar data globally
      _globalCustomAvatars[avatarId] = imageData;

      // Create avatar option
      final avatarOption = {
        'id': avatarId,
        'imageData': imageData,
        'isCustom': true,
        'icon': Icons.person,
      };

      // Store in global options
      _globalCustomAvatarOptions[avatarId] = avatarOption;

      // Add to local options if not already present
      if (!_avatarOptions.any((option) => option['id'] == avatarId)) {
        _avatarOptions.add(avatarOption);
      }

      _selectedAvatar = avatarId;
    });
    // Use debounced save to prevent rate limiting
    _debouncedSave();
  }

  Future<void> _onAvatarDeleted(String avatarId) async {
    try {
      // Find the avatar to check if it's backend stored
      final avatarOption = _avatarOptions.firstWhere(
        (option) => option['id'] == avatarId,
        orElse: () => {},
      );

      // If it's backend stored, delete from backend first
      if (avatarOption['isBackendStored'] == true) {
        final success = await AvatarUploadService.deleteAvatar(avatarId);
        if (!success) {
          // Show error message if deletion failed
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Failed to delete avatar'),
                backgroundColor: Colors.red,
              ),
            );
          }
          return;
        }
      }

      setState(() {
        // Remove from global storage
        _globalCustomAvatars.remove(avatarId);
        _globalCustomAvatarOptions.remove(avatarId);

        // Remove from local options
        _avatarOptions.removeWhere((option) => option['id'] == avatarId);

        // If the deleted avatar was selected, switch to default
        if (_selectedAvatar == avatarId) {
          _selectedAvatar = 'ai_robot_blue';
        }
      });
      
      // Use debounced save to prevent rate limiting
      _debouncedSave();
    } catch (e) {
      print('Error deleting avatar: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to delete avatar'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _onLanguageChanged(String language) {
    setState(() {
      _selectedLanguage = language;
    });
    _updatePreview();
    // Use debounced save to prevent rate limiting
    _debouncedSave();
  }

  void _onConfirmationChanged(bool value) {
    setState(() {
      _requiresConfirmation = value;
    });
    // Use debounced save to prevent rate limiting
    _debouncedSave();
  }

  void _onPersonalityChanged(String trait, double value) {
    setState(() {
      switch (trait) {
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
    _debouncedSave();
  }

  Future<void> _loadExistingData() async {
    try {
      print('🔄 LOADING: Checking for existing assistant profile...');
      
      // Load user's assistant profiles directly
      final profiles = await ref.read(assistantProvider.notifier).getAssistantProfiles();
      
      if (profiles != null && profiles.isNotEmpty) {
        print('🔄 LOADING: Found ${profiles.length} assistant profiles');
        
        // Load the first (default) profile
        final profile = profiles.first;
        print('🔄 LOADING: Loading profile: $profile');
        
        setState(() {
          _nameController.text = profile['name'] ?? '';
          _selectedAvatar = profile['avatar_url'] ?? 'ai_robot_blue';
          _selectedLanguage = profile['language'] ?? 'en';
          _requiresConfirmation = profile['requires_confirmation'] ?? true;
          
          final style = profile['style'] as Map<String, dynamic>? ?? {};
          _formality = (style['formality'] ?? 50).toDouble();
          _humor = (style['humor'] ?? 30).toDouble();
          _motivation = (style['motivation'] ?? 60).toDouble();
        });
        
        _validateName();
        _updatePreview();
        print('🔄 LOADING: Profile loaded successfully');
      } else {
        print('🔄 LOADING: No assistant profiles found');
      }
    } catch (e) {
      print('Failed to load existing data: $e');
    }
  }

  Future<void> _loadFromAssistantProfile(String profileId) async {
    try {
      // Load assistant profile from backend
      final response = await ref.read(onboardingProvider.notifier).getAssistantProfile(profileId);
      if (response != null) {
        setState(() {
          _nameController.text = response['name'] ?? '';
          _selectedAvatar = response['avatar_url'] ?? 'ai_robot_blue';
          _selectedLanguage = response['language'] ?? 'en';
          _requiresConfirmation = response['requires_confirmation'] ?? true;
          
          final style = response['style'] as Map<String, dynamic>? ?? {};
          _formality = (style['formality'] ?? 50).toDouble();
          _humor = (style['humor'] ?? 30).toDouble();
          _motivation = (style['motivation'] ?? 60).toDouble();
        });
        
        _validateName();
        _updatePreview();
      }
    } catch (e) {
      print('Failed to load assistant profile: $e');
    }
  }


  Future<void> _loadCustomAvatars() async {
    try {
      // Restore custom avatars from global storage first
      _globalCustomAvatarOptions.forEach((avatarId, avatarData) {
        if (!_avatarOptions.any((option) => option['id'] == avatarId)) {
          _avatarOptions.add(avatarData);
        }
      });

      // Load custom avatars from backend
      final response = await AvatarUploadService.loadUserAvatars();
      if (response != null && response.isNotEmpty) {
        for (final avatarData in response) {
          final avatarId = avatarData['avatar_id'] as String;
          
          // Skip if already loaded
          if (_avatarOptions.any((option) => option['id'] == avatarId)) {
            continue;
          }

          // Create avatar option for backend stored avatar
          final avatarOption = {
            'id': avatarId,
            'isCustom': true,
            'isBackendStored': true,
            'icon': Icons.person,
            'filename': avatarData['filename'],
          };

          // Add to local options
          _avatarOptions.add(avatarOption);
          
          // Store in global options for other screens
          _globalCustomAvatarOptions[avatarId] = avatarOption;
        }
        
        // Trigger rebuild to show loaded avatars
        if (mounted) {
          setState(() {});
        }
      }
    } catch (e) {
      print('Failed to load custom avatars: $e');
    }
  }

  void _updatePreview() {
    // Generate comprehensive preview message based on current settings
    final List<String> previewMessages = _generatePreviewMessages();
    final randomIndex = math.Random().nextInt(previewMessages.length);
    
    setState(() {
      _currentPreview = previewMessages[randomIndex];
    });
  }

  List<String> _generatePreviewMessages() {
    final String name = _nameController.text.trim().isNotEmpty ? _nameController.text.trim() : 'Assistant';
    final List<String> messages = [];

    // Greeting variations based on formality
    List<String> greetings;
    if (_formality < 30) {
      greetings = ['Good day', 'Greetings', 'Good morning'];
    } else if (_formality > 70) {
      greetings = ['Hey', 'Hi there', 'What\'s up'];
    } else {
      greetings = ['Hello', 'Hi', 'Hey there'];
    }

    // Message content variations based on motivation
    List<String> motivations;
    if (_motivation > 70) {
      motivations = [
        'Ready to crush some goals today? Let\'s make it happen! 🚀',
        'Time to level up! What amazing thing are we working on?',
        'I\'m pumped to help you achieve something incredible today!',
        'Let\'s turn your dreams into reality! What\'s first on the agenda?'
      ];
    } else if (_motivation < 30) {
      motivations = [
        'I\'m here to support you at your own pace.',
        'Take your time - I\'ll be here whenever you need me.',
        'Let\'s work together gently on whatever feels right.',
        'No pressure - we\'ll figure this out step by step.'
      ];
    } else {
      motivations = [
        'I\'m excited to help you achieve your goals!',
        'Ready to work together on something meaningful?',
        'How can I assist you in making progress today?',
        'Let\'s tackle whatever you have in mind!'
      ];
    }

    // Humor additions
    List<String> humorElements = [];
    if (_humor > 70) {
      humorElements = [' ✨', ' 😊', ' 🎯', ' 💫', ' 🌟'];
    } else if (_humor > 40) {
      humorElements = [' 😊', ' 🙂', ''];
    } else {
      humorElements = ['', '', ''];
    }

    // Generate combinations
    for (String greeting in greetings.take(2)) {
      for (String motivation in motivations.take(2)) {
        for (String humor in humorElements.take(2)) {
          if (_formality < 30) {
            messages.add('$greeting! I\'m $name. $motivation$humor');
          } else {
            messages.add('$greeting! $motivation$humor');
          }
        }
      }
    }

    // Add some task-specific examples
    if (_motivation > 60) {
      messages.addAll([
        'I\'m $name and I\'m fired up to help you conquer your goals! What\'s our mission?${_humor > 60 ? ' 🎯' : ''}',
        'Hey! I\'m $name, your AI companion. Let\'s make some serious progress today!${_humor > 60 ? ' 🚀' : ''}',
      ]);
    }

    if (_formality < 40 && _humor > 50) {
      messages.addAll([
        'Greetings! I\'m $name, here to assist with your endeavors.${_humor > 70 ? ' ✨' : ''}',
        'Good day! I\'m $name and I\'m delighted to be working with you.${_humor > 70 ? ' 😊' : ''}',
      ]);
    }

    return messages.isNotEmpty ? messages : ['Hi! I\'m $name. How can I help you today?'];
  }

  void _debouncedSave() {
    // Cancel previous timer
    _saveTimer?.cancel();
    
    // Start new timer with longer delay to prevent rate limiting
    _saveTimer = Timer(const Duration(seconds: 3), () {
      _saveDataToBackend();
    });
  }

  Future<void> _saveDataToBackend() async {
    if (!_isNameValid || _isSaving) return;

    // Prevent rapid API calls (minimum 2 seconds between saves)
    if (_lastSaveAttempt != null && 
        DateTime.now().difference(_lastSaveAttempt!) < const Duration(seconds: 2)) {
      print('💾 SAVING: Skipping save due to rate limiting');
      return;
    }

    setState(() {
      _isSaving = true;
    });
    _lastSaveAttempt = DateTime.now();

    try {
      // Create or update assistant profile directly
      final assistantData = {
        'name': _nameController.text.trim(),
        'avatar_url': _selectedAvatar,
        'language': _selectedLanguage,
        'requires_confirmation': _requiresConfirmation,
        'style': {
          'formality': _formality.round(),
          'directness': 50,
          'humor': _humor.round(),
          'empathy': 70,
          'motivation': _motivation.round(),
        },
      };

      print('💾 SAVING: Assistant data: $assistantData');
      
      // Save directly to assistant profile (create or update)
      final success = await _saveAssistantProfile(assistantData);
      
      print('💾 SAVING: Save result: $success');
      
      // Show brief success indicator
      if (success && mounted) {
        setState(() {
          _showSaveSuccess = true;
        });
        Timer(const Duration(seconds: 2), () {
          if (mounted) {
            setState(() {
              _showSaveSuccess = false;
            });
          }
        });
      }
    } catch (e) {
      print('Auto-save failed: $e');
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  Future<bool> _saveAssistantProfile(Map<String, dynamic> data) async {
    try {
      // First check if user already has an assistant profile
      final profiles = await ref.read(assistantProvider.notifier).getAssistantProfiles();
      
      if (profiles != null && profiles.isNotEmpty) {
        // Update existing profile
        final profileId = profiles.first['id'];
        return await ref.read(assistantProvider.notifier).updateAssistantProfile(profileId, data);
      } else {
        // Create new profile
        return await ref.read(assistantProvider.notifier).createAssistantProfile(data);
      }
    } catch (e) {
      print('Failed to save assistant profile: $e');
      return false;
    }
  }

  void _handleNext() {
    if (_isNameValid) {
      // Cancel any pending debounced save and save immediately before proceeding
      _saveTimer?.cancel();
      
      final data = {
        'name': _nameController.text.trim(),
        'avatar_url': _selectedAvatar,
        'language': _selectedLanguage,
        'requires_confirmation': _requiresConfirmation,
        'style': {
          'formality': _formality.round(),
          'directness': 50,
          'humor': _humor.round(),
          'empathy': 70,
          'motivation': _motivation.round(),
        },
      };
      
      // Save immediately before proceeding
      _saveDataToBackend();
      widget.onNext(data);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: SlideTransition(
          position: _slideAnimation,
          child: Column(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Hero section
                      AssistantHeroSection(
                        selectedAvatarData: _getSelectedAvatarData(),
                        globalCustomAvatars: _globalCustomAvatars,
                        assistantName: _nameController.text.trim().isNotEmpty 
                            ? _nameController.text.trim() 
                            : 'Your Assistant',
                      ),

                      const SizedBox(height: 32),

                      // Name input
                      AssistantNameInput(
                        controller: _nameController,
                        focusNode: _nameFocus,
                        isValid: _isNameValid,
                        onRefresh: _refreshAssistantName,
                      ),

                      const SizedBox(height: 32),

                      // Avatar selection
                      AvatarSelectionGrid(
                        avatarOptions: _avatarOptions,
                        selectedAvatar: _selectedAvatar,
                        onAvatarSelected: _onAvatarSelected,
                        onAvatarUploaded: _onAvatarUploaded,
                        onAvatarDeleted: _onAvatarDeleted,
                      ),

                      const SizedBox(height: 32),

                      // Language selection
                      LanguagePreferences(
                        languages: _languages,
                        selectedLanguage: _selectedLanguage,
                        requiresConfirmation: _requiresConfirmation,
                        onLanguageChanged: _onLanguageChanged,
                        onConfirmationChanged: _onConfirmationChanged,
                      ),

                      const SizedBox(height: 32),

                      // Personality setup
                      PersonalitySetup(
                        formality: _formality,
                        humor: _humor,
                        motivation: _motivation,
                        onPersonalityChanged: _onPersonalityChanged,
                      ),

                      const SizedBox(height: 32),

                      // Preview
                      if (_isNameValid)
                        AssistantPreview(
                          assistantName: _nameController.text.trim(),
                          selectedAvatarData: _getSelectedAvatarData(),
                          globalCustomAvatars: _globalCustomAvatars,
                          previewMessage: _currentPreview,
                        ),
                    ],
                  ),
                ),
              ),

              // Bottom actions
              _buildBottomActions(theme),
            ],
          ),
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
            onPressed: _isNameValid ? _handleNext : null,
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
        
        // Auto-save indicator
        if (_isSaving || _saveTimer?.isActive == true || _showSaveSuccess)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (_showSaveSuccess)
                  Icon(
                    Icons.check_circle,
                    size: 16,
                    color: theme.colorScheme.primary,
                  )
                else
                  SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        theme.colorScheme.primary.withOpacity(0.6),
                      ),
                    ),
                  ),
                const SizedBox(width: 8),
                Text(
                  _showSaveSuccess 
                      ? 'Saved!' 
                      : (_isSaving ? 'Saving...' : 'Auto-saving...'),
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: _showSaveSuccess 
                        ? theme.colorScheme.primary
                        : theme.colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
              ],
            ),
          ),
        
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