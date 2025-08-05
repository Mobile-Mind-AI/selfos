import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../providers/auth_provider.dart';
import '../../services/object_managers/personal_profile_manager.dart';
import '../../services/object_managers/life_area_manager.dart';
import '../../services/object_managers/media_attachment_manager.dart';
import '../../services/sync/sync_manager.dart';
import '../../widgets/onboarding/life_area_compact.dart';
import '../../widgets/common/avatar.dart';

/// Personal configuration step for onboarding
/// Simplified version with offline-first approach
class PersonalConfigurationStep extends ConsumerStatefulWidget {
  final Function(Map<String, dynamic>) onNext;
  final VoidCallback onPrevious;

  const PersonalConfigurationStep({
    super.key,
    required this.onNext,
    required this.onPrevious,
  });

  @override
  ConsumerState<PersonalConfigurationStep> createState() => _PersonalConfigurationStepState();
}

/// State class for the `PersonalConfigurationStep` widget.
/// This class manages the state and logic for the personal configuration step
/// in the onboarding process. It includes functionality for handling user input,
/// managing life areas, interests, challenges, preferences, and avatar selection.
class _PersonalConfigurationStepState extends ConsumerState<PersonalConfigurationStep> {
  // Managers
  final PersonalProfileManager _profileManager = PersonalProfileManager.instance;
  final LifeAreaManager _lifeAreaManager = LifeAreaManager.instance;
  final MediaAttachmentManager _mediaManager = MediaAttachmentManager.instance;
  
  // Controllers
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _lifeStoryController = TextEditingController();
  
  // State
  String? _avatarId; // Avatar ID (either media attachment ID or predefined like 'avatar_1')
  File? _avatarFile; // Temporary file for display
  final Map<String, double> _lifeAreaImportance = {};
  final Map<String, String> _lifeAreaColors = {}; // Store color for each life area
  final Set<String> _selectedInterests = {};
  final Set<String> _customInterests = {};
  final Set<String> _selectedChallenges = {};
  final Set<String> _customChallenges = {};
  final Map<String, String> _preferences = {};
  
  // Default options
  final List<String> _defaultInterests = [
    'Reading', 'Travel', 'Fitness', 'Cooking', 'Music', 
    'Technology', 'Art', 'Nature', 'Gaming', 'Photography'
  ];
  
  final List<String> _defaultChallenges = [
    'Time Management', 'Procrastination', 'Work-Life Balance', 
    'Stress', 'Motivation', 'Focus', 'Health', 'Relationships'
  ];
  
  final List<Map<String, dynamic>> _preferenceQuestions = [
    {
      'id': 'work_style',
      'question': 'How do you prefer to work?',
      'options': ['Deep focused work', 'Collaborative', 'Flexible mix', 'Structured routine'],
    },
    {
      'id': 'communication_frequency',
      'question': 'How often do you want check-ins?',
      'options': ['Daily', 'Weekly', 'Bi-weekly', 'Monthly', 'As needed'],
    },
    {
      'id': 'goal_approach',
      'question': 'How do you approach goals?',
      'options': ['Structured planning', 'Flexible adaptation', 'Experimental', 'Milestone-based'],
    },
    {
      'id': 'motivation_style',
      'question': 'What motivates you most?',
      'options': ['Achievement', 'Personal growth', 'Balance', 'Recognition'],
    },
  ];

  @override
  void initState() {
    super.initState();
    _loadExistingData();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _lifeStoryController.dispose();
    super.dispose();
  }
  /// Loads the list of life areas for the user.
  ///
  /// This method retrieves all life areas from the database.
  /// It includes both system default life areas and user-specific custom life areas.
  ///
  /// Returns:
  ///   A `Future` that resolves to a list of maps, where each map represents a life area
  ///   with properties like `id`, `name`, `icon`, `color`, and `is_custom`.
  Future<List<Map<String, dynamic>>> _loadLifeAreas() async {
    final authState = ref.read(authStateProvider);
    if (!authState.isLoggedIn || authState.user == null) return [];
    
    final userId = authState.user!.uid;
    
    // Get all life areas (system defaults + user custom)
    final allAreas = await _lifeAreaManager.getAllLifeAreas(userId);
    
    return allAreas;
  }
  /// Displays a dialog for adding a custom life area.
  ///
  /// This dialog allows the user to specify a name, select an icon, and choose a color
  /// for the custom life area. The selected values are then saved using the `LifeAreaManager`.
  /// The dialog includes:
  /// - A text field for entering the name of the life area.
  /// - A grid of icons for selecting an icon.
  /// - A palette of colors for choosing a color.
  /// - Buttons for canceling or adding the custom life area.
  ///
  /// The dialog updates the state of the widget when a new life area is added.
  void _showAddCustomLifeAreaDialog() {
    final nameController = TextEditingController();
    final icons = [
      {'name': 'fitness_center', 'icon': Icons.fitness_center},
      {'name': 'restaurant', 'icon': Icons.restaurant},
      {'name': 'public', 'icon': Icons.public},
      {'name': 'local_hospital', 'icon': Icons.local_hospital},
      {'name': 'music_note', 'icon': Icons.music_note},
      {'name': 'category', 'icon': Icons.category},
      {'name': 'favorite', 'icon': Icons.favorite},
      {'name': 'work', 'icon': Icons.work},
      {'name': 'home', 'icon': Icons.home},
      {'name': 'school', 'icon': Icons.school},
      {'name': 'attach_money', 'icon': Icons.attach_money},
      {'name': 'self_improvement', 'icon': Icons.self_improvement},
      {'name': 'family_restroom', 'icon': Icons.family_restroom},
      {'name': 'sports_soccer', 'icon': Icons.sports_soccer},
      {'name': 'sports_basketball', 'icon': Icons.sports_basketball},
      {'name': 'sports_tennis', 'icon': Icons.sports_tennis},
      {'name': 'pool', 'icon': Icons.pool},
      {'name': 'directions_run', 'icon': Icons.directions_run},
      {'name': 'directions_bike', 'icon': Icons.directions_bike},
      {'name': 'directions_car', 'icon': Icons.directions_car},
      {'name': 'flight', 'icon': Icons.flight},
      {'name': 'hotel', 'icon': Icons.hotel},
      {'name': 'beach_access', 'icon': Icons.beach_access},
      {'name': 'terrain', 'icon': Icons.terrain},
      {'name': 'park', 'icon': Icons.park},
      {'name': 'pets', 'icon': Icons.pets},
      {'name': 'child_care', 'icon': Icons.child_care},
      {'name': 'brush', 'icon': Icons.brush},
      {'name': 'palette', 'icon': Icons.palette},
      {'name': 'camera_alt', 'icon': Icons.camera_alt},
      {'name': 'movie', 'icon': Icons.movie},
      {'name': 'book', 'icon': Icons.book},
      {'name': 'computer', 'icon': Icons.computer},
      {'name': 'code', 'icon': Icons.code},
      {'name': 'science', 'icon': Icons.science},
      {'name': 'psychology', 'icon': Icons.psychology},
      {'name': 'volunteer_activism', 'icon': Icons.volunteer_activism},
      {'name': 'groups', 'icon': Icons.groups},
      {'name': 'celebration', 'icon': Icons.celebration},
      {'name': 'spa', 'icon': Icons.spa},
      {'name': 'meditation', 'icon': Icons.self_improvement},
      {'name': 'nightlife', 'icon': Icons.nightlife},
      {'name': 'shopping_cart', 'icon': Icons.shopping_cart},
      {'name': 'videogame_asset', 'icon': Icons.videogame_asset},
    ];
    
    final colors = [
      Colors.red,
      Colors.pink,
      Colors.purple,
      Colors.deepPurple,
      Colors.indigo,
      Colors.blue,
      Colors.lightBlue,
      Colors.cyan,
      Colors.teal,
      Colors.green,
      Colors.lightGreen,
      Colors.lime,
      Colors.yellow,
      Colors.amber,
      Colors.orange,
      Colors.deepOrange,
      Colors.brown,
      Colors.grey,
      Colors.blueGrey,
    ];
    
    String selectedIcon = 'category';
    Color selectedColor = colors[0];
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Add Custom Life Area'),
          content: SizedBox(
            width: 400, // Fixed width for the dialog content
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: nameController,
                    decoration: const InputDecoration(
                      labelText: 'Name',
                      hintText: 'e.g., Hobbies, Travel',
                    ),
                    autofocus: true,
                  ),
                  const SizedBox(height: 16),
                  const Text('Choose an icon:'),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 200,
                    child: GridView.count(
                      shrinkWrap: true,
                      physics: const AlwaysScrollableScrollPhysics(),
                      crossAxisCount: 6,
                      mainAxisSpacing: 8,
                      crossAxisSpacing: 8,
                      children: icons.map((item) => InkWell(
                  onTap: () {
                    setDialogState(() {
                      selectedIcon = item['name'].toString();
                    });
                  },
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: selectedIcon == item['name'].toString()
                          ? Theme.of(context).colorScheme.primary
                          : Colors.grey.shade300,
                        width: 2,
                      ),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(item['icon'] as IconData),
                  ),
                )).toList(),
                  ),
                ),
                const SizedBox(height: 16),
                const Text('Choose a color:'),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: colors.map((color) => InkWell(
                  onTap: () {
                    setDialogState(() {
                      selectedColor = color;
                    });
                  },
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: color,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: selectedColor == color
                          ? Colors.black
                          : Colors.transparent,
                        width: 2,
                      ),
                    ),
                  ),
                )).toList(),
                ),
              ],
            ),
          ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                final name = nameController.text.trim();
                if (name.isNotEmpty) {
                  final authState = ref.read(authStateProvider);
                  if (authState.isLoggedIn && authState.user != null) {
                    await _lifeAreaManager.create(
                      userId: authState.user!.uid,
                      name: name,
                      icon: selectedIcon,
                      color: '#${selectedColor.value.toRadixString(16).substring(2)}',
                    );
                    setState(() {});
                  }
                }
                Navigator.pop(context);
              },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
  }
  /// Loads existing user data and updates the state of the widget.
  ///
  /// This method retrieves the user's profile data, including their preferred name,
  /// avatar, life story, interests, challenges, and preferences. It uses the `PersonalProfileManager`
  /// to fetch the data and updates the widget's state accordingly.
  ///
  /// The method checks if the user is logged in and has a valid user ID before attempting
  /// to load the data. If the profile exists, it populates the state variables such as
  /// `_nameController`, `_avatarId`, `_lifeStoryController`, `_selectedInterests`, `_selectedChallenges`,
  /// `_lifeAreaImportance`, `_lifeAreaColors`, and `_preferences`.
  ///
  /// This method ensures that the widget reflects the user's existing data for a personalized experience.
  Future<void> _loadExistingData() async {
    final authState = ref.read(authStateProvider);
    if (authState.isLoggedIn && authState.user != null) {
      final userId = authState.user!.uid;
      
      // Load personal profile if exists
      final profile = await _profileManager.getByUserId(userId);
      if (profile != null) {
        setState(() {
          _nameController.text = profile['preferred_name'] ?? '';
          
          // Load avatar ID
          _avatarId = profile['avatar_id'];
          
          // Load life story from current_situation
          _lifeStoryController.text = profile['current_situation'] ?? '';
          
          // Load interests and separate custom from default
          final interests = profile['interests'] as List<dynamic>? ?? [];
          for (var interest in interests) {
            final interestStr = interest.toString();
            _selectedInterests.add(interestStr);
            // If not in default list, it's custom
            if (!_defaultInterests.contains(interestStr)) {
              _customInterests.add(interestStr);
            }
          }
          
          // Load challenges and separate custom from default
          final challenges = profile['challenges'] as List<dynamic>? ?? [];
          for (var challenge in challenges) {
            final challengeStr = challenge.toString();
            _selectedChallenges.add(challengeStr);
            // If not in default list, it's custom
            if (!_defaultChallenges.contains(challengeStr)) {
              _customChallenges.add(challengeStr);
            }
          }
          
          // Load preferences including life area importance and colors
          final prefs = profile['preferences'] as Map<String, dynamic>? ?? {};
          final lifeAreaImportance = prefs['life_area_importance'] as Map<String, dynamic>?;
          if (lifeAreaImportance != null) {
            lifeAreaImportance.forEach((key, value) {
              _lifeAreaImportance[key] = (value as num).toDouble();
            });
          }
          
          final lifeAreaColors = prefs['life_area_colors'] as Map<String, dynamic>?;
          if (lifeAreaColors != null) {
            lifeAreaColors.forEach((key, value) {
              _lifeAreaColors[key] = value.toString();
            });
          }
          
          // Load other preferences
          prefs.forEach((key, value) {
            if (key != 'life_area_importance' && key != 'life_area_colors' && value is String) {
              _preferences[key] = value;
            }
          });
        });
      }
    }
  }
  /// Allows the user to pick an avatar for their profile.
  ///
  /// This method presents a modal bottom sheet with three options:
  /// - Take a photo using the camera.
  /// - Choose an image from the gallery.
  /// - Select a predefined avatar icon.
  ///
  /// Depending on the user's choice, the avatar file or ID is updated in the widget's state.
  /// If a photo or gallery image is selected, the file is stored temporarily for display.
  /// If a predefined avatar is chosen, its identifier is stored.
  Future<void> _pickAvatar() async {
    final ImagePicker picker = ImagePicker();
    
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Only show camera option on mobile platforms
            if (Platform.isIOS || Platform.isAndroid)
              ListTile(
                leading: const Icon(Icons.camera_alt),
                title: const Text('Take Photo'),
                onTap: () async {
                  Navigator.pop(context);
                  final XFile? photo = await picker.pickImage(source: ImageSource.camera);
                  if (photo != null) {
                    setState(() {
                      _avatarFile = File(photo.path);
                      _avatarId = null; // Clear any previous ID, will create new one on save
                    });
                  }
                },
              ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Choose from Gallery'),
              onTap: () async {
                Navigator.pop(context);
                final XFile? image = await picker.pickImage(source: ImageSource.gallery);
                if (image != null) {
                  setState(() {
                    _avatarFile = File(image.path);
                    _avatarId = null; // Clear any previous ID, will create new one on save
                  });
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.emoji_emotions),
              title: const Text('Choose an Icon'),
              onTap: () {
                Navigator.pop(context);
                _showIconPicker();
              },
            ),
          ],
        ),
      ),
    );
  }
  /// Displays a dialog for selecting a predefined avatar icon.
  ///
  /// This method shows a grid of predefined avatar options in a dialog.
  /// Each avatar is represented by an icon and associated colors.
  /// When the user selects an avatar, its identifier is stored in the widget's state.
  /// The dialog closes after the selection is made.
  void _showIconPicker() {
    final avatarOptions = [
      'avatar_1', 'avatar_2', 'avatar_3', 'avatar_4',
      'avatar_5', 'avatar_6', 'avatar_7', 'avatar_8',
    ];
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Choose an Avatar'),
        content: SizedBox(
          width: 300,
          height: 300,
          child: GridView.builder(
            shrinkWrap: true,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
            ),
            itemCount: avatarOptions.length,
            itemBuilder: (context, index) {
              final avatar = avatarOptions[index];
              return GestureDetector(
                onTap: () {
                  setState(() {
                    // Store predefined avatar identifier
                    _avatarId = avatar; // This will be a string like 'avatar_1'
                    _avatarFile = null;
                  });
                  Navigator.pop(context);
                },
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: _avatarId == avatar 
                        ? Theme.of(context).colorScheme.primary 
                        : Colors.grey.shade300,
                      width: 2,
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: Avatar(
                      avatarId: avatar,
                      icon: _getPredefinedAvatarData(avatar)['icon'],
                      gradientColors: _getPredefinedAvatarData(avatar)['colors'],
                      size: 60,
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  /// Saves the user's profile data and proceeds to the next onboarding step.
  ///
  /// This method collects the user's input, including their name, avatar, life story,
  /// interests, challenges, and preferences, and saves it using the `PersonalProfileManager`.
  /// If an avatar file is selected, it uploads the file and retrieves its ID.
  /// The method ensures offline-first functionality by checking for an existing profile
  /// and updating it if necessary, or creating a new profile otherwise.
  ///
  /// After saving the data, it triggers a background sync and calls the `onNext` callback
  /// to proceed to the next step in the onboarding process.
  ///
  /// Preconditions:
  /// - The user must be logged in and have a valid user ID.
  ///
  /// Side Effects:
  /// - Updates the user's profile data in the local database.
  /// - Uploads the avatar file if selected.
  /// - Triggers a background sync process.
  ///
  /// Returns:
  ///   A `Future` that completes when the profile data is saved and the next step is triggered.
  Future<void> _saveAndContinue() async {
    print('🔵 PERSONAL CONFIG: Starting save process...');
    
    final authState = ref.read(authStateProvider);
    if (!authState.isLoggedIn || authState.user == null) {
      print('🔴 PERSONAL CONFIG: User not logged in, cannot save');
      return;
    }
    
    final userId = authState.user!.uid;
    print('🔵 PERSONAL CONFIG: User ID: $userId');
    
    // Handle avatar file upload if selected
    String? finalAvatarId = _avatarId;
    if (_avatarFile != null) {
      try {
        print('🔵 PERSONAL CONFIG: Uploading avatar file...');
        // Create media attachment for the avatar
        final fileInfo = await _avatarFile!.stat();
        final attachment = await _mediaManager.create(
          userId: userId,
          filename: 'avatar_${DateTime.now().millisecondsSinceEpoch}.jpg',
          originalFilename: _avatarFile!.path.split('/').last,
          contentType: 'image/jpeg',
          fileSize: fileInfo.size,
          isDefault: true,
          localPath: _avatarFile!.path,
        );
        finalAvatarId = attachment['id'];
        print('🔵 PERSONAL CONFIG: Avatar uploaded with ID: $finalAvatarId');
      } catch (e) {
        print('🔴 PERSONAL CONFIG: Failed to create avatar attachment: $e');
      }
    }
    
    // Prepare data using proper database columns
    final allInterests = [..._selectedInterests].toSet().toList(); // Use Set to remove duplicates
    final allChallenges = [..._selectedChallenges].toSet().toList(); // Use Set to remove duplicates
    
    print('🔵 PERSONAL CONFIG: Preparing profile data...');
    print('🔵 Selected interests: $_selectedInterests');
    print('🔵 Custom interests: $_customInterests');
    print('🔵 All interests: $allInterests');
    print('🔵 Selected challenges: $_selectedChallenges');
    print('🔵 Custom challenges: $_customChallenges');
    print('🔵 All challenges: $allChallenges');
    print('🔵 Preferences: $_preferences');
    print('🔵 Life area importance: $_lifeAreaImportance');
    
    final profileData = {
      'preferred_name': _nameController.text.trim(),
      'avatar_id': finalAvatarId, // Either media attachment ID or predefined avatar
      'current_situation': _lifeStoryController.text.trim(), // Use current_situation for life story
      'interests': allInterests,
      'challenges': allChallenges,
      'preferences': {
        ..._preferences,
        'life_area_importance': _lifeAreaImportance,
        'life_area_colors': _lifeAreaColors,
      },
    };
    
    try {
      // Save profile using offline-first approach
      print('🔵 PERSONAL CONFIG: Checking for existing profile...');
      final existingProfile = await _profileManager.getByUserId(userId);
      
      if (existingProfile != null) {
        print('🔵 PERSONAL CONFIG: Found existing profile ${existingProfile['id']}, updating...');
        
        // Debug: Check what's in _preferences before saving
        print('🔍 PERSONAL CONFIG: Current _preferences map: $_preferences');
        print('🔍 PERSONAL CONFIG: work_style: ${_preferences['work_style']}');
        print('🔍 PERSONAL CONFIG: communication_frequency: ${_preferences['communication_frequency']}');
        print('🔍 PERSONAL CONFIG: goal_approach: ${_preferences['goal_approach']}');
        print('🔍 PERSONAL CONFIG: motivation_style: ${_preferences['motivation_style']}');
        
        // Extract preference fields that should go in dedicated columns
        final updateData = {
          'preferred_name': profileData['preferred_name'],
          'avatar_id': profileData['avatar_id'],
          'current_situation': profileData['current_situation'],
          'interests': profileData['interests'],
          'challenges': profileData['challenges'],
          // Extract the four preference fields from _preferences
          'work_style': _preferences['work_style'],
          'communication_frequency': _preferences['communication_frequency'],
          'goal_approach': _preferences['goal_approach'],
          'motivation_style': _preferences['motivation_style'],
          // Only store extra data in preferences JSON
          'preferences': {
            'life_area_importance': _lifeAreaImportance,
            'life_area_colors': _lifeAreaColors,
          },
        };
        
        await _profileManager.update(existingProfile['id'], updateData);
        print('✅ PERSONAL CONFIG: Profile updated successfully');
        
        // Debug: Read back the saved profile to verify preferences were stored
        final savedProfile = await _profileManager.getById(existingProfile['id']);
        if (savedProfile != null) {
          print('🔍 VERIFICATION: Saved profile work_style: ${savedProfile['work_style']}');
          print('🔍 VERIFICATION: Saved profile communication_frequency: ${savedProfile['communication_frequency']}');
          print('🔍 VERIFICATION: Saved profile goal_approach: ${savedProfile['goal_approach']}');
          print('🔍 VERIFICATION: Saved profile motivation_style: ${savedProfile['motivation_style']}');
        }
      } else {
        print('🔵 PERSONAL CONFIG: No existing profile, creating new...');
        // Debug: Check what's in _preferences before creating
        print('🔍 PERSONAL CONFIG: Creating with _preferences: $_preferences');
        final newProfile = await _profileManager.create(
          userId: userId,
          preferredName: profileData['preferred_name'] as String?,
          avatarId: profileData['avatar_id'] as String?,
          currentSituation: profileData['current_situation'] as String?,
          interests: profileData['interests'] as List<String>,
          challenges: profileData['challenges'] as List<String>,
          preferences: profileData['preferences'] as Map<String, dynamic>,
          // Pass all preference fields that match database columns
          workStyle: _preferences['work_style'] as String?,
          communicationFrequency: _preferences['communication_frequency'] as String?,
          goalApproach: _preferences['goal_approach'] as String?,
          motivationStyle: _preferences['motivation_style'] as String?,
        );
        print('✅ PERSONAL CONFIG: Profile created with ID: ${newProfile['id']}');
        
        // Debug: Read back the saved profile to verify preferences were stored
        final savedProfile = await _profileManager.getById(newProfile['id']);
        if (savedProfile != null) {
          print('🔍 VERIFICATION: Created profile work_style: ${savedProfile['work_style']}');
          print('🔍 VERIFICATION: Created profile communication_frequency: ${savedProfile['communication_frequency']}');
          print('🔍 VERIFICATION: Created profile goal_approach: ${savedProfile['goal_approach']}');
          print('🔍 VERIFICATION: Created profile motivation_style: ${savedProfile['motivation_style']}');
        }
      }
      
      // Trigger sync in background
      print('🔵 PERSONAL CONFIG: Triggering background sync...');
      await SyncManager.instance.processSyncQueue();
      print('✅ PERSONAL CONFIG: Sync triggered successfully');
      
    } catch (e) {
      print('🔴 PERSONAL CONFIG: Error saving profile: $e');
      print('🔴 PERSONAL CONFIG: Stack trace: ${StackTrace.current}');
    }
    
    // Continue to next step
    print('🔵 PERSONAL CONFIG: Proceeding to next step...');
    print('🔍 FINAL CHECK: _preferences = $_preferences');
    widget.onNext({
      'profile_data': profileData,
      'life_area_importance': _lifeAreaImportance,
      'personal_profile_saved': true, // Flag to indicate profile was saved
    });
  }

  /// Builds the widget tree for the `PersonalConfigurationStep` screen.
  ///
  /// This method constructs the UI for the personal configuration step in the onboarding process.
  /// It includes:
  /// - A progress indicator to show the current step.
  /// - Sections for avatar selection, name input, life areas, life story, interests, challenges, and preferences.
  /// - Navigation buttons to move to the previous or next step.
  ///
  /// Parameters:
  /// - `context`: The `BuildContext` object that provides access to the widget tree and theme.
  ///
  /// Returns:
  ///   A `Widget` representing the complete screen layout.
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Progress indicator
            LinearProgressIndicator(
              value: 0.66,
              backgroundColor: theme.colorScheme.surfaceVariant,
              valueColor: AlwaysStoppedAnimation<Color>(theme.colorScheme.primary),
            ),
            
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Personal Configuration',
                      style: theme.textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Tell us about yourself to personalize your experience',
                      style: theme.textTheme.bodyLarge?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 32),
                    
                    // Avatar selection
                    Center(
                      child: GestureDetector(
                        onTap: _pickAvatar,
                        child: Stack(
                          children: [
                            Container(
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: theme.colorScheme.outline.withOpacity(0.2),
                                  width: 2,
                                ),
                              ),
                              child: ClipOval(
                                child: _buildAvatarWidget(),
                              ),
                            ),
                            Positioned(
                              bottom: 0,
                              right: 0,
                              child: Container(
                                padding: const EdgeInsets.all(4),
                                decoration: BoxDecoration(
                                  color: theme.colorScheme.primary,
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(
                                  Icons.camera_alt,
                                  size: 20,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    
                    // Name input
                    TextField(
                      controller: _nameController,
                      decoration: InputDecoration(
                        labelText: 'Your Name',
                        hintText: 'How would you like to be called?',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    
                    // Life areas with importance
                    _buildLifeAreasSection(theme),
                    const SizedBox(height: 32),
                    
                    // Life story
                    TextField(
                      controller: _lifeStoryController,
                      maxLines: 4,
                      decoration: InputDecoration(
                        labelText: 'Your Life Story',
                        hintText: 'Share anything you\'d like us to know about you...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    
                    // Interests
                    _buildInterestsSection(theme),
                    const SizedBox(height: 32),
                    
                    // Challenges
                    _buildChallengesSection(theme),
                    const SizedBox(height: 32),
                    
                    // Preferences
                    _buildPreferencesSection(theme),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
            
            // Navigation buttons
            Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                children: [
                  TextButton(
                    onPressed: widget.onPrevious,
                    child: const Text('Previous'),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: FilledButton(
                      onPressed: _nameController.text.isNotEmpty ? _saveAndContinue : null,
                      child: const Text('Continue'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  /// Builds the Life Areas section of the onboarding screen.
  ///
  /// This section allows users to select predefined or custom life areas
  /// and set their importance (1-100). It includes:
  /// - A list of life areas with sliders to adjust importance.
  /// - Options to add custom life areas.
  /// - Functionality to delete custom life areas.
  ///
  /// The method uses a `FutureBuilder` to load life areas asynchronously
  /// and updates the widget state based on user interactions.
  ///
  /// Parameters:
  /// - `theme`: The `ThemeData` object used for styling the section.
  ///
  /// Returns:
  ///   A `Widget` representing the Life Areas section.
  Widget _buildLifeAreasSection(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Life Areas',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            TextButton.icon(
              onPressed: _showAddCustomLifeAreaDialog,
              icon: const Icon(Icons.add),
              label: const Text('Add Custom'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          'Choose and prioritize areas of your life',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 16),
        FutureBuilder<List<Map<String, dynamic>>>(
          future: _loadLifeAreas(),
          builder: (context, snapshot) {
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            
            final lifeAreas = snapshot.data!;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // All areas in a wrap layout
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: lifeAreas.map((area) {
                    final areaId = area['id']?.toString() ?? area['name'];
                    final isSelected = _lifeAreaImportance.containsKey(areaId);
                    final importance = _lifeAreaImportance[areaId] ?? 50.0;
                    
                    return LifeAreaCompact(
                      area: area,
                      isSelected: isSelected,
                      importance: importance,
                      selectedColor: _lifeAreaColors[areaId],
                    onSelectedChanged: (selected) {
                      setState(() {
                        if (selected) {
                          _lifeAreaImportance[areaId] = 50.0;
                          // Set default color if not already set
                          if (!_lifeAreaColors.containsKey(areaId)) {
                            _lifeAreaColors[areaId] = area['color'] ?? '#6366f1';
                          }
                        } else {
                          _lifeAreaImportance.remove(areaId);
                          _lifeAreaColors.remove(areaId);
                        }
                      });
                    },
                    onImportanceChanged: isSelected ? (value) {
                      setState(() {
                        _lifeAreaImportance[areaId] = value;
                      });
                    } : null,
                    onColorChanged: isSelected ? (newColor) {
                      setState(() {
                        _lifeAreaColors[areaId] = newColor;
                      });
                    } : null,
                    onDelete: area['is_custom'] == true ? () async {
                      // Delete custom life area
                      await _lifeAreaManager.delete(area['id']);
                      setState(() {
                        _lifeAreaImportance.remove(areaId);
                        _lifeAreaColors.remove(areaId);
                      });
                    } : null,
                    );
                  }).toList(),
                ),
              ],
            );
          },
        ),
      ],
    );
  }
  /// Builds the Interests section of the onboarding screen.
  ///
  /// This section allows users to select predefined interests or add custom ones.
  /// It includes:
  /// - A list of predefined interests displayed as filter chips.
  /// - Custom interests displayed as chips with delete functionality.
  /// - An action chip for adding custom interests.
  ///
  /// The method updates the widget state based on user interactions, such as
  /// selecting or deselecting interests, adding custom interests, or deleting them.
  ///
  /// Parameters:
  /// - `theme`: The `ThemeData` object used for styling the section.
  ///
  /// Returns:
  ///   A `Widget` representing the Interests section.
  Widget _buildInterestsSection(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Interests',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ..._defaultInterests.map((interest) => FilterChip(
              label: Text(interest),
              selected: _selectedInterests.contains(interest),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _selectedInterests.add(interest);
                  } else {
                    _selectedInterests.remove(interest);
                  }
                });
              },
            )),
            ..._customInterests.map((interest) => FilterChip(
              label: Text(interest),
              selected: _selectedInterests.contains(interest),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _selectedInterests.add(interest);
                  } else {
                    _selectedInterests.remove(interest);
                  }
                });
              },
              deleteIcon: const Icon(Icons.close, size: 18),
              onDeleted: () {
                setState(() {
                  _customInterests.remove(interest);
                  _selectedInterests.remove(interest);
                });
              },
            )),
            ActionChip(
              label: const Text('Add Custom'),
              avatar: const Icon(Icons.add, size: 18),
              onPressed: () => _showAddCustomDialog('interest'),
            ),
          ],
        ),
      ],
    );
  }
  /// Builds the Challenges section of the onboarding screen.
  ///
  /// This section allows users to select predefined challenges or add custom ones.
  /// It includes:
  /// - A list of predefined challenges displayed as filter chips.
  /// - Custom challenges displayed as chips with delete functionality.
  /// - An action chip for adding custom challenges.
  ///
  /// The method updates the widget state based on user interactions, such as
  /// selecting or deselecting challenges, adding custom challenges, or deleting them.
  ///
  /// Parameters:
  /// - `theme`: The `ThemeData` object used for styling the section.
  ///
  /// Returns:
  ///   A `Widget` representing the Challenges section.
  Widget _buildChallengesSection(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Challenges',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ..._defaultChallenges.map((challenge) => FilterChip(
              label: Text(challenge),
              selected: _selectedChallenges.contains(challenge),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _selectedChallenges.add(challenge);
                  } else {
                    _selectedChallenges.remove(challenge);
                  }
                });
              },
            )),
            ..._customChallenges.map((challenge) => FilterChip(
              label: Text(challenge),
              selected: _selectedChallenges.contains(challenge),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _selectedChallenges.add(challenge);
                  } else {
                    _selectedChallenges.remove(challenge);
                  }
                });
              },
              deleteIcon: const Icon(Icons.close, size: 18),
              onDeleted: () {
                setState(() {
                  _customChallenges.remove(challenge);
                  _selectedChallenges.remove(challenge);
                });
              },
            )),
            ActionChip(
              label: const Text('Add Custom'),
              avatar: const Icon(Icons.add, size: 18),
              onPressed: () => _showAddCustomDialog('challenge'),
            ),
          ],
        ),
      ],
    );
  }
  /// Builds the Preferences section of the onboarding screen.
  ///
  /// This section allows users to answer predefined questions about their preferences
  /// or provide custom answers. It includes:
  /// - A list of questions with predefined options displayed as choice chips.
  /// - Functionality to add custom answers for each question.
  /// - Ability to delete custom answers.
  ///
  /// The method updates the widget state based on user interactions, such as
  /// selecting predefined options, adding custom answers, or deleting them.
  ///
  /// Parameters:
  /// - `theme`: The `ThemeData` object used for styling the section.
  ///
  /// Returns:
  ///   A `Widget` representing the Preferences section.
  Widget _buildPreferencesSection(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Quick Preferences',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        ..._preferenceQuestions.map((question) {
          final id = question['id'] as String;
          final options = question['options'] as List<String>;
          final selectedOption = _preferences[id];
          
          return Padding(
            padding: const EdgeInsets.only(bottom: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  question['question'] as String,
                  style: theme.textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    ...options.map((option) => ChoiceChip(
                      label: Text(option),
                      selected: selectedOption == option,
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _preferences[id] = option;
                            print('🔍 PREFERENCE SELECTED: $id = $option');
                          } else {
                            _preferences.remove(id);
                            print('🔍 PREFERENCE REMOVED: $id');
                          }
                        });
                      },
                    )),
                    if (selectedOption != null && !options.contains(selectedOption))
                      ChoiceChip(
                        label: Text(selectedOption),
                        selected: true,
                        onSelected: (selected) {
                          if (!selected) {
                            setState(() {
                              _preferences.remove(id);
                            });
                          }
                        },
                      ),
                    ActionChip(
                      label: const Text('Custom'),
                      avatar: const Icon(Icons.edit, size: 18),
                      onPressed: () => _showCustomAnswerDialog(id),
                    ),
                  ],
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
  /// Displays a dialog for adding a custom interest or challenge.
  ///
  /// This method creates a dialog with a text field where the user can input
  /// a custom interest or challenge. The dialog includes:
  /// - A text field for entering the custom value.
  /// - Buttons for canceling or adding the custom value.
  ///
  /// Parameters:
  /// - `type`: A `String` indicating the type of custom value to add.
  ///   It can be either 'interest' or 'challenge'.
  ///
  /// Side Effects:
  /// - Updates the state of the widget by adding the custom value to the
  ///   corresponding set (`_customInterests` or `_customChallenges`).
  void _showAddCustomDialog(String type) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Add Custom ${type.capitalize()}'),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(
            hintText: 'Enter your $type',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              final value = controller.text.trim();
              if (value.isNotEmpty) {
                setState(() {
                  if (type == 'interest') {
                    _customInterests.add(value);
                    _selectedInterests.add(value); // Auto-select custom interest
                  } else if (type == 'challenge') {
                    _customChallenges.add(value);
                    _selectedChallenges.add(value); // Auto-select custom challenge
                  }
                });
              }
              Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }
  /// Displays a dialog for adding a custom answer to a preference question.
  ///
  /// This method creates a dialog with a text field where the user can input
  /// a custom answer for a specific question. The dialog includes:
  /// - A text field pre-filled with the current answer (if any).
  /// - Buttons for canceling or saving the custom answer.
  ///
  /// Parameters:
  /// - `questionId`: A `String` representing the unique identifier of the question
  ///   for which the custom answer is being added.
  ///
  /// Side Effects:
  /// - Updates the `_preferences` map with the custom answer for the given question ID.
  void _showCustomAnswerDialog(String questionId) {
    final controller = TextEditingController(text: _preferences[questionId]);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Custom Answer'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'Enter your answer',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              final value = controller.text.trim();
              if (value.isNotEmpty) {
                setState(() {
                  _preferences[questionId] = value;
                });
              }
              Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
  /// Builds the avatar widget for the user's profile.
  ///
  /// This method determines the appropriate avatar to display based on the current state:
  /// - If a temporary file is selected, it displays the image from the file.
  /// - If a predefined avatar is selected, it displays the avatar with its associated icon and gradient colors.
  /// - If a media attachment ID is provided, it displays the avatar stored in the backend.
  /// - If no avatar is selected, it displays a default placeholder.
  ///
  /// Returns:
  ///   A `Widget` representing the avatar.
  Widget _buildAvatarWidget() {
    // If we have a temporary file, show it
    if (_avatarFile != null) {
      return Image.file(
        _avatarFile!,
        width: 120,
        height: 120,
        fit: BoxFit.cover,
      );
    }
    
    // If we have a predefined avatar
    if (_avatarId != null && _avatarId!.startsWith('avatar_')) {
      // Get the predefined avatar data
      final avatarData = _getPredefinedAvatarData(_avatarId!);
      return Avatar(
        avatarId: _avatarId!,
        icon: avatarData['icon'],
        gradientColors: avatarData['colors'],
        size: 120,
      );
    }
    
    // If we have a media attachment ID
    if (_avatarId != null && !_avatarId!.startsWith('avatar_')) {
      // Use Avatar with backend storage flag
      return Avatar(
        avatarId: _avatarId!,
        size: 120,
        isBackendStored: true,
      );
    }
    
    // Default empty state
    return Container(
      width: 120,
      height: 120,
      color: Theme.of(context).colorScheme.surfaceVariant,
      child: Icon(
        Icons.person,
        size: 60,
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
  }
  
  Map<String, dynamic> _getPredefinedAvatarData(String avatarId) {
    // Define predefined avatar options with their icons and gradients
    final predefinedAvatars = {
      'avatar_1': {
        'icon': Icons.smart_toy,
        'colors': [Colors.blue.shade400, Colors.purple.shade400],
      },
      'avatar_2': {
        'icon': Icons.psychology,
        'colors': [Colors.green.shade400, Colors.teal.shade400],
      },
      'avatar_3': {
        'icon': Icons.auto_awesome,
        'colors': [Colors.orange.shade400, Colors.red.shade400],
      },
      'avatar_4': {
        'icon': Icons.rocket_launch,
        'colors': [Colors.purple.shade400, Colors.pink.shade400],
      },
      'avatar_5': {
        'icon': Icons.spa,
        'colors': [Colors.cyan.shade400, Colors.blue.shade400],
      },
      'avatar_6': {
        'icon': Icons.lightbulb,
        'colors': [Colors.amber.shade400, Colors.orange.shade400],
      },
      'avatar_7': {
        'icon': Icons.favorite,
        'colors': [Colors.pink.shade400, Colors.red.shade400],
      },
      'avatar_8': {
        'icon': Icons.star,
        'colors': [Colors.indigo.shade400, Colors.purple.shade400],
      },
    };
    
    return predefinedAvatars[avatarId] ?? predefinedAvatars['avatar_1']!;
  }
}

extension StringExtension on String {
  String capitalize() {
    return "${this[0].toUpperCase()}${substring(1)}";
  }
}