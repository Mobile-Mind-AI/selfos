// assistant_creation_step.dart
import 'package:flutter/material.dart';
import 'dart:typed_data';
import 'dart:math' as math;
import 'dart:convert';
import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../widgets/dialogs/custom_avatar_upload_dialog.dart';
import '../../providers/onboarding_provider.dart';
import '../../providers/assistant_provider.dart';
import '../../providers/auth_provider.dart' as simple_auth;
import '../../services/auth_provider.dart';
import '../../services/sync/sync_manager.dart';
import '../../services/network_service.dart';
import '../../services/object_managers/media_attachment_manager.dart';
import '../../config/environment.dart';
import '../../widgets/assistant/assistant_hero_section.dart';
import '../../widgets/assistant/assistant_name_input.dart';
import '../../widgets/assistant/avatar_selection_grid.dart';
import '../../widgets/assistant/language_preferences.dart';
import '../../widgets/assistant/personality_setup.dart';
import '../../widgets/assistant/assistant_preview.dart';

/// Global storage for custom avatars during the onboarding session.
/// This map stores avatar ID as key and the image data as value.
/// It persists across screen transitions within the onboarding flow.
final Map<String, Uint8List> _globalCustomAvatars = {};

/// Global storage for custom avatar metadata and options.
/// Stores avatar ID as key and avatar configuration (icon, colors, etc.) as value.
final Map<String, Map<String, dynamic>> _globalCustomAvatarOptions = {};

/// Clears all custom avatars from global storage.
/// 
/// This should be called when:
/// - The onboarding process is completed
/// - The onboarding process is reset
/// - The user logs out
/// 
/// This ensures that avatar data doesn't persist between different onboarding sessions.
void clearAllCustomAvatars() {
  _globalCustomAvatars.clear();
  _globalCustomAvatarOptions.clear();
}

/// Returns the global custom avatars map.
/// 
/// This getter provides read-only access to the custom avatar image data
/// stored during the current onboarding session.
/// 
/// Returns:
///   A map where keys are avatar IDs and values are the avatar image data as Uint8List.
Map<String, Uint8List> getGlobalCustomAvatars() => _globalCustomAvatars;

/// Returns the global custom avatar options map.
/// 
/// This getter provides read-only access to the custom avatar metadata
/// stored during the current onboarding session.
/// 
/// Returns:
///   A map where keys are avatar IDs and values are avatar configuration maps
///   containing properties like icon, colors, and other display options.
Map<String, Map<String, dynamic>> getGlobalCustomAvatarOptions() => _globalCustomAvatarOptions;

/// Represents a step in the onboarding process for creating an assistant.
///
/// This widget is a stateful component that manages the assistant creation flow.
/// It includes functionality for selecting an avatar, setting preferences, and
/// configuring personality traits. The widget uses Riverpod for state management.
///
/// Parameters:
/// - [onNext]: A callback function that is triggered when the user proceeds to the next step.
/// - [onPrevious]: A callback function that is triggered when the user navigates back to the previous step.
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
/// Represents the state for the `AssistantCreationStep` widget.
///
/// This class manages the internal state and behavior of the assistant creation flow.
/// It includes animations, user input handling, and data synchronization with the backend.
/// The state is tied to the Riverpod framework for state management.
///
/// Key responsibilities:
/// - Handles assistant name validation and auto-saving changes.
/// - Manages avatar selection, including custom avatar uploads and deletions.
/// - Tracks language preferences and personality traits.
/// - Synchronizes assistant profile data with the backend.
/// - Provides a preview of the assistant based on user inputs.
///
/// Mixins:
/// - `TickerProviderStateMixin`: Used for managing animations within the widget.
class _AssistantCreationStepState extends ConsumerState<AssistantCreationStep>
    with TickerProviderStateMixin {

  /// Animation controller for entrance animations
  late AnimationController _animationController;
  
  /// Fade animation for smooth appearance
  late Animation<double> _fadeAnimation;
  
  /// Slide animation for content entry
  late Animation<Offset> _slideAnimation;

  /// Text controller for the assistant name input field
  final TextEditingController _nameController = TextEditingController();
  
  /// Focus node for managing keyboard focus on name input
  final FocusNode _nameFocus = FocusNode();

  /// Currently selected avatar ID, defaults to blue robot
  String _selectedAvatar = 'ai_robot_blue';
  
  /// Whether the current name meets validation requirements
  bool _isNameValid = false;

  /// Selected language code for the assistant
  String _selectedLanguage = 'en';
  
  /// Whether the assistant should ask for confirmation before actions
  bool _requiresConfirmation = true;

  /// Personality trait: Communication formality (0=formal, 100=casual)
  double _formality = 50.0;
  
  /// Personality trait: Humor level (0=serious, 100=playful)
  double _humor = 30.0;
  
  /// Personality trait: Motivational intensity (0=gentle, 100=high-energy)
  double _motivation = 60.0;

  /// Current preview message showing assistant personality
  String _currentPreview = '';
  
  /// Timer for debounced saving
  Timer? _saveTimer;
  /// Predefined list of assistant names for random generation.
  /// These names are gender-neutral and suitable for AI assistants.
  final List<String> _assistantNames = [
    'Alex', 'Sage', 'Nova', 'Zara', 'Kai', 'Luna', 'Echo', 'Orion',
    'Maya', 'Leo', 'Iris', 'Atlas', 'Vera', 'Felix', 'Cora', 'Max',
    'Ava', 'Neo', 'Zoe', 'Rex', 'Sky', 'Eve', 'Jax', 'Mia'
  ];
  
  /// Flag to prevent auto-save during initial data loading.
  /// Set to false after `_loadExistingData` completes.
  bool _isLoadingData = true;
  
  /// Flag to prevent multiple simultaneous navigation attempts.
  /// Set to true when "Continue" is pressed, false when navigation completes or fails.
  bool _isNavigating = false;
  
  /// Stores the assistant profile ID after creation/update.
  /// This ID is passed to the next onboarding step for backend completion.
  String? _assistantProfileId;

  /// Supported languages for the assistant.
  /// 
  /// Each language entry contains:
  /// - code: ISO 639-1 language code used internally
  /// - name: Localized display name of the language
  /// - flag: Emoji flag for visual representation
  /// 
  /// The assistant will respond in the selected language and adapt
  /// its communication style accordingly.
  final List<Map<String, String>> _languages = [
    {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
    {'code': 'ru', 'name': 'Русский', 'flag': '🇷🇺'},
    {'code': 'es', 'name': 'Español', 'flag': '🇪🇸'}
  ];

    /// Available avatar options for the assistant.
  /// 
  /// Each avatar includes:
  /// - id: Unique identifier used for selection and storage
  /// - imagePath: Path to the avatar image asset
  /// - icon: Fallback icon if image fails to load
  /// - colors: Gradient colors for avatar background effects
  /// 
  /// These are the default avatars provided by the app. Users can also
  /// upload custom avatars which are added to this list dynamically.
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
  /// Initializes the component for the assistant creation step.
  ///
  /// This method sets up animations, listeners, and loads initial data required
  /// for the assistant creation flow. It also ensures that the UI is updated
  /// with default values if no existing data is found.
  ///
  /// Key actions:
  /// - Configures animation controllers and transitions.
  /// - Adds listeners for name validation.
  /// - Loads custom avatars and existing onboarding data.
  /// - Generates a random assistant name if none is provided.
  /// - Starts animations and updates the assistant preview.
  ///
  /// Returns:
  ///   A `Future<void>` indicating the completion of the initialization process.
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
    
    // Check for existing assistant profiles from local DB
    await _checkExistingProfiles();

    // Generate random name as default only if no name was loaded
    if (_nameController.text.trim().isEmpty) {
      _refreshAssistantName();
    }

    // Start animations
    _animationController.forward();

    // Update preview
    _updatePreview();
    
    // Enable auto-save after initial data loading is complete
    _isLoadingData = false;
  }

  @override
  void dispose() {
    _saveTimer?.cancel();
    _animationController.dispose();
    _nameController.dispose();
    _nameFocus.dispose();
    super.dispose();
  }
  /// Validates the assistant name entered by the user.
  ///
  /// This method checks if the name meets the required length constraints
  /// (minimum 2 characters and maximum 50 characters). It updates the state
  /// to reflect whether the name is valid and triggers an auto-save if the
  /// name is valid and initial data loading is complete.
  void _validateName() {
    final name = _nameController.text.trim();
    setState(() {
      _isNameValid = name.length >= 2 && name.length <= 50;
    });
    // Only trigger auto-save if not loading initial data
    if (_isNameValid && !_isLoadingData) {
      _debouncedSave();
    }
  }

  /// Generates and sets a random assistant name from the predefined list.
  /// 
  /// This method:
  /// 1. Selects a random name from `_assistantNames`
  /// 2. Updates the name controller with the selected name
  /// 3. Validates the new name
  /// 4. Updates the preview to reflect the new name
  /// 
  /// Used when the user clicks the refresh button next to the name input field.
  void _refreshAssistantName() {
    final randomName = _assistantNames[math.Random().nextInt(_assistantNames.length)];
    _nameController.text = randomName;
    _validateName();
    _updatePreview();
  }

  /// Retrieves the complete data for the currently selected avatar.
  /// 
  /// This method searches through `_avatarOptions` to find the avatar
  /// matching the `_selectedAvatar` ID. If no match is found, it returns
  /// the first avatar in the list as a fallback.
  /// 
  /// Returns:
  ///   A map containing avatar properties including:
  ///   - id: Avatar identifier
  ///   - imagePath: Path to avatar image (for built-in avatars)
  ///   - icon: Icon widget for display
  ///   - colors: List of gradient colors
  ///   - isCustom: Whether this is a user-uploaded avatar
  Map<String, dynamic> _getSelectedAvatarData() {
    return _avatarOptions.firstWhere(
      (avatar) => avatar['id'] == _selectedAvatar,
      orElse: () => _avatarOptions.first,
    );
  }

  /// Handles avatar selection from the avatar grid.
  /// 
  /// Updates the selected avatar ID and triggers a debounced save
  /// to persist the selection. This method is called when the user
  /// taps on an avatar in the selection grid.
  /// 
  /// Parameters:
  ///   - avatarId: The unique identifier of the selected avatar
  void _onAvatarSelected(String avatarId) {
    setState(() {
      _selectedAvatar = avatarId;
    });
    // Use debounced save to prevent rate limiting
    _debouncedSave();
  }
  /// Handles the upload of a custom avatar.
  ///
  /// This method stores the uploaded avatar data globally and updates the local
  /// avatar options. If the uploaded avatar is new, it adds it to the list of
  /// available avatars. The selected avatar is updated to the newly uploaded one.
  ///
  /// Parameters:
  /// - [avatarId]: A unique identifier for the uploaded avatar.
  /// - [imageData]: The binary data of the uploaded avatar image.
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
  /// Deletes a custom avatar from the available options.
  ///
  /// This method removes the specified avatar from both global and local storage.
  /// If the avatar is stored in the backend, it attempts to delete it using the
  /// `MediaAttachmentManager`. If the deletion fails, an error message is displayed.
  /// If the deleted avatar is currently selected, the selection is reset to the default avatar.
  ///
  /// Parameters:
  /// - [avatarId]: A unique identifier for the avatar to be deleted.
  ///
  /// Throws:
  /// - Displays a `SnackBar` with an error message if the deletion fails.
  Future<void> _onAvatarDeleted(String avatarId) async {
    try {
      // Find the avatar to check if it's backend stored
      final avatarOption = _avatarOptions.firstWhere(
        (option) => option['id'] == avatarId,
        orElse: () => {},
      );

      // If it's backend stored, delete using media manager
      if (avatarOption['isBackendStored'] == true) {
        try {
          final mediaManager = MediaAttachmentManager.instance;
          await mediaManager.deleteAvatarWithRateLimit(avatarId);
        } catch (e) {
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
  /// Handles language selection changes.
  void _onLanguageChanged(String language) {
    setState(() {
      _selectedLanguage = language;
    });
    _updatePreview();
    // Use debounced save to prevent rate limiting
    _debouncedSave();
  }

  /// Handles confirmation requirement changes.
  void _onConfirmationChanged(bool value) {
    setState(() {
      _requiresConfirmation = value;
    });
    // Use debounced save to prevent rate limiting
    _debouncedSave();
  }
  /// Updates the personality trait value based on user input.
  ///
  /// This method modifies the specified personality trait (e.g., formality, humor, or motivation)
  /// and updates the assistant preview accordingly. It also triggers an auto-save to persist
  /// the changes to the backend.
  ///
  /// Parameters:
  /// - [trait]: The name of the personality trait to update (e.g., 'formality', 'humor', 'motivation').
  /// - [value]: The new value for the specified personality trait, ranging from 0 to 100.
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
  /// Loads existing assistant profile data from the backend.
  ///
  /// This method retrieves the user's assistant profiles and loads the first profile
  /// (default profile) if available. It updates the state with the profile's data,
  /// including name, avatar, language, confirmation requirement, and personality traits.
  /// If no profiles are found, it logs a message indicating the absence of profiles.
  ///
  /// Key actions:
  /// - Fetches assistant profiles using the `assistantProvider`.
  /// - Updates the state with the first profile's data.
  /// - Validates the assistant name and updates the preview.
  ///
  /// Throws:
  /// - Logs an error message if the data loading fails.
  
  /// Check for existing assistant profiles from local database
  Future<void> _checkExistingProfiles() async {
    try {
      print('🔍 Checking for existing assistant profiles from local DB...');
      
      // This check is separate from _loadExistingData to ensure we always
      // check the local database even if onboarding data is not available
      final profiles = await ref.read(assistantProvider.notifier).getAssistantProfiles();
      
      if (profiles != null && profiles.isNotEmpty) {
        print('✅ Found ${profiles.length} existing assistant profiles in local DB');
        // The profiles will be loaded in _loadExistingData
      } else {
        print('📝 No existing assistant profiles found in local DB');
      }
    } catch (e) {
      print('❌ Error checking existing profiles: $e');
    }
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
          
          // Store the profile ID
          _assistantProfileId = profile['id'];
          print('🔄 LOADING: Loaded profile ID: $_assistantProfileId');
          
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



  /// Loads custom avatars from both global storage and backend.
  /// 
  /// This method performs two main operations:
  /// 
  /// 1. **Restores avatars from global storage**: Adds any custom avatars
  ///    that were uploaded during the current onboarding session.
  /// 
  /// 2. **Loads avatars from backend**: If the user is authenticated,
  ///    fetches any previously uploaded avatars from the backend using
  ///    the MediaAttachmentManager.
  /// 
  /// The method ensures no duplicate avatars are added by checking
  /// existing IDs before adding new ones. It also stores backend avatars
  /// in global storage for access by other screens.
  /// 
  /// Throws:
  ///   Logs errors if avatar loading fails but doesn't interrupt the flow.
  Future<void> _loadCustomAvatars() async {
    try {
      // Restore custom avatars from global storage first
      _globalCustomAvatarOptions.forEach((avatarId, avatarData) {
        if (!_avatarOptions.any((option) => option['id'] == avatarId)) {
          _avatarOptions.add(avatarData);
        }
      });

      // Load custom avatars using media manager if user is authenticated
      final authState = ref.read(authProvider);
      if (authState is AuthStateAuthenticated) {
        final mediaManager = MediaAttachmentManager.instance;
        final avatars = await mediaManager.loadUserAvatars(authState.user.uid!);
        
        for (final avatarData in avatars) {
          final avatarId = avatarData['id'] as String;
          
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

  /// Updates the assistant preview message based on current personality settings.
  /// 
  /// This method generates a list of possible preview messages using the
  /// current personality traits (formality, humor, motivation) and randomly
  /// selects one to display. The preview gives users immediate feedback on
  /// how their assistant will communicate.
  /// 
  /// Called whenever:
  /// - The assistant name changes
  /// - Personality traits are adjusted
  /// - Language preferences are modified
  void _updatePreview() {
    // Generate comprehensive preview message based on current settings
    final List<String> previewMessages = _generatePreviewMessages();
    final randomIndex = math.Random().nextInt(previewMessages.length);
    
    setState(() {
      _currentPreview = previewMessages[randomIndex];
    });
  }

  /// Generates a list of preview messages based on the assistant's personality configuration.
  /// 
  /// This method creates contextually appropriate messages by combining:
  /// - Greeting styles (based on formality level)
  /// - Motivational content (based on motivation level)
  /// - Humor elements (emojis based on humor level)
  /// 
  /// The algorithm:
  /// 1. Selects greetings based on formality (< 30 = formal, > 70 = casual)
  /// 2. Chooses motivational messages based on motivation level
  /// 3. Adds humor elements (emojis) based on humor level
  /// 4. Combines these elements into natural-sounding messages
  /// 
  /// Returns:
  ///   A list of 4-8 preview messages that reflect the assistant's personality.
  ///   Falls back to a simple greeting if generation fails.
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

  /// Implements debounced saving to prevent excessive API calls.
  /// 
  /// This method cancels any pending save operation and schedules a new one
  /// after a 3-second delay. This prevents rate limiting when users are
  /// actively making changes to the assistant configuration.
  /// 
  /// The debounce pattern ensures that:
  /// - Rapid changes don't trigger multiple API calls
  /// - The final state is saved after the user stops making changes
  /// - Backend resources are used efficiently
  void _debouncedSave() {
    // Cancel previous timer
    _saveTimer?.cancel();
    
    // Start new timer with longer delay to prevent rate limiting
    _saveTimer = Timer(const Duration(seconds: 3), () {
      _saveDataToBackend();
    });
  }

  /// Saves the assistant profile data to the backend.
  /// 
  /// This method:
  /// 1. Validates that the assistant name is valid
  /// 2. Prepares the assistant data object with all configuration
  /// 3. Calls `_saveAssistantProfile` to persist the data
  /// 4. Stores the profile ID for later reference
  /// 
  /// The method is called automatically via debounced save when users
  /// make changes, and explicitly when proceeding to the next step.
  /// 
  /// Throws:
  ///   Exception if the save operation fails, which is re-thrown
  ///   to allow the caller to handle the error appropriately.
  Future<void> _saveDataToBackend() async {
    if (!_isNameValid) return;

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
      final profileId = await _saveAssistantProfile(assistantData);
      
      print('💾 SAVING: Save result - profile ID: $profileId');
      
      if (profileId == null) {
        throw Exception('Failed to save assistant profile');
      }
      
      // Store the profile ID for later use
      _assistantProfileId = profileId;
    } catch (e) {
      print('Auto-save failed: $e');
      rethrow; // Re-throw to allow caller to handle
    }
  }

  /// Saves or updates the assistant profile in the local database and queues for sync.
  /// 
  /// This method implements an "upsert" pattern:
  /// - If an assistant profile exists, it updates the existing profile
  /// - If no profile exists, it creates a new one
  /// 
  /// After saving locally, it triggers a sync operation to send the data
  /// to the backend. The sync is fault-tolerant and will retry if it fails.
  /// 
  /// Parameters:
  ///   - data: Map containing assistant configuration (name, avatar, language, style, etc.)
  /// 
  /// Returns:
  ///   The profile ID if successful, null if the operation fails.
  ///   
  /// Side effects:
  ///   - Updates local database
  ///   - Queues sync operation
  ///   - Checks network status
  ///   - Triggers immediate sync attempt
  Future<String?> _saveAssistantProfile(Map<String, dynamic> data) async {
    try {
      // First check if user already has an assistant profile
      final profiles = await ref.read(assistantProvider.notifier).getAssistantProfiles();
      
      if (profiles != null && profiles.isNotEmpty) {
        print('🔄 Found existing profile, updating...');
        // Update existing profile
        final profileId = profiles.first['id'];
        final result = await ref.read(assistantProvider.notifier).updateAssistantProfile(profileId, data);
        print('🔄 Update result: $result');
        return result ? profileId : null;
      } else {
        print('🆕 No existing profile, creating new...');
        // Create new profile and get the ID
        final profileId = await ref.read(assistantProvider.notifier).createAssistantProfileAndGetId(data);
        print('🆕 Created profile with ID: $profileId');
        return profileId;
      }
    } catch (e) {
      print('Failed to save assistant profile: $e');
      return null;
    } finally {
      // Trigger sync to send data to backend
      try {
        print('🔄 Triggering assistant profile sync...');
        
        // Force network check before sync
        final networkService = NetworkService.instance;
        print('📡 Checking network status...');
        final networkState = await networkService.checkNetwork();
        print('📡 Network status: ${networkState.status.name}');
        print('📡 Can reach backend: ${networkState.canReachBackend}');
        print('📡 Backend URL: ${Environment.backendUrl}');
        
        await SyncManager.instance.processSyncQueue();
        print('✅ Assistant profile sync completed');
      } catch (syncError) {
        print('⚠️ Assistant sync failed (will retry later): $syncError');
        // Don't throw - sync will retry automatically later
      }
    }
  }

  /// Handles the "Continue" button press to proceed to the next onboarding step.
  /// 
  /// This method:
  /// 1. Validates that the assistant name is valid
  /// 2. Prevents multiple simultaneous navigation attempts
  /// 3. Cancels any pending auto-save operations
  /// 4. Saves the current assistant configuration
  /// 5. Passes the assistant data (including profile ID) to the next step
  /// 
  /// If saving fails, it re-enables the button and shows an error message.
  /// The navigation is blocked until the save operation completes to ensure
  /// data consistency.
  /// 
  /// Error handling:
  ///   Shows a SnackBar with error message if save fails.
  void _handleNext() async {
    if (_isNameValid && !_isNavigating) {
      // Prevent multiple clicks
      setState(() {
        _isNavigating = true;
      });
      
      // Cancel any pending debounced save to prevent duplicate calls
      _saveTimer?.cancel();
      
      try {
        // Save the data before proceeding (ensures data is saved even if user goes back)
        await _saveDataToBackend();
        
        // Now _assistantProfileId should be set
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
          'assistant_profile_id': _assistantProfileId, // Include the profile ID
        };
        
        print('🎯 ASSISTANT: Proceeding to next step with profile ID: $_assistantProfileId');
        
        // Proceed to next step with the data
        widget.onNext(data);
      } catch (error) {
        print('Error in _handleNext: $error');
        // If save fails, re-enable the button
        if (mounted) {
          setState(() {
            _isNavigating = false;
          });
          
          // Show error message
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Failed to save. Please try again.'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  /// Builds the main UI for the assistant creation step.
  /// 
  /// This method constructs a comprehensive interface that includes:
  /// - Animated transitions for smooth entry
  /// - Assistant hero section with avatar display
  /// - Name input field with validation
  /// - Avatar selection grid with custom upload support
  /// - Language and confirmation preferences
  /// - Personality trait sliders (formality, humor, motivation)
  /// - Live preview of assistant personality
  /// - Navigation buttons (Continue/Back)
  /// 
  /// The layout is responsive and scrollable to accommodate different
  /// screen sizes. All user interactions trigger auto-save through
  /// the debounced save mechanism.
  /// 
  /// Parameters:
  ///   - context: The build context for accessing theme and navigation
  /// 
  /// Returns:
  ///   A Padding widget containing the complete assistant creation interface
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
                  padding: const EdgeInsets.only(bottom: 20),
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

              // Add space before bottom actions
              const SizedBox(height: 24),

              // Bottom actions
              _buildBottomActions(theme),
            ],
          ),
        ),
      ),
    );
  }

  /// Builds the bottom action buttons for the assistant creation step.
  /// 
  /// Creates two buttons:
  /// 1. **Continue button**: Proceeds to the next step if the assistant name is valid.
  ///    Shows a loading spinner while saving/navigating.
  /// 2. **Back button**: Returns to the previous onboarding step.
  /// 
  /// The Continue button is disabled when:
  /// - The assistant name is invalid
  /// - A navigation/save operation is in progress
  /// 
  /// Parameters:
  ///   - theme: The current theme data for styling the buttons
  /// 
  /// Returns:
  ///   A Column widget containing the action buttons with appropriate spacing.
  Widget _buildBottomActions(ThemeData theme) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _isNameValid && !_isNavigating ? _handleNext : null,
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: _isNavigating
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Text(
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