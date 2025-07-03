import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:typed_data';
import '../onboarding/assistant_creation_step.dart' show getGlobalCustomAvatars, getGlobalCustomAvatarOptions;
import '../../widgets/common/assistant_avatar.dart';
import '../../providers/assistant_provider.dart';
import '../../services/avatar_upload_service.dart';

/// Screen for configuring the AI assistant (similar to onboarding but for existing users)
class AssistantConfigurationScreen extends ConsumerStatefulWidget {
  const AssistantConfigurationScreen({super.key});

  @override
  ConsumerState<AssistantConfigurationScreen> createState() => _AssistantConfigurationScreenState();
}

class _AssistantConfigurationScreenState extends ConsumerState<AssistantConfigurationScreen> 
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  // Form state
  final _nameController = TextEditingController();
  String _selectedAvatar = 'ai_robot_blue';
  Map<String, dynamic> _personalityData = {};
  Map<String, dynamic> _languageData = {
    'language': 'en',
    'requires_confirmation': true,
  };
  
  bool _isLoading = false;
  bool _hasChanges = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadCurrentAssistantData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _loadCurrentAssistantData() async {
    setState(() => _isLoading = true);
    
    try {
      // TODO: Load current assistant data from API/provider
      final assistantData = await ref.read(assistantProvider.notifier).getCurrentAssistant();
      
      if (assistantData != null) {
        setState(() {
          _nameController.text = assistantData['name'] ?? 'Assistant';
          _selectedAvatar = assistantData['avatar_url'] ?? 'ai_robot_blue';
          _personalityData = assistantData['style'] ?? {};
          _languageData = {
            'language': assistantData['language'] ?? 'en',
            'requires_confirmation': assistantData['requires_confirmation'] ?? true,
          };
        });
      }
    } catch (e) {
      print('Error loading assistant data: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _markAsChanged() {
    if (!_hasChanges) {
      setState(() => _hasChanges = true);
    }
  }

  Future<void> _saveChanges() async {
    if (!_hasChanges) return;
    
    setState(() => _isLoading = true);
    
    try {
      // Prepare update data
      final updateData = {
        'name': _nameController.text.trim(),
        'avatar_url': _selectedAvatar,
        'style': _personalityData,
        'language': _languageData['language'],
        'requires_confirmation': _languageData['requires_confirmation'],
      };
      
      // TODO: Call API to update assistant
      await ref.read(assistantProvider.notifier).updateAssistant(updateData);
      
      // Show success message
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Assistant preferences updated successfully'),
            backgroundColor: Colors.green,
          ),
        );
        setState(() => _hasChanges = false);
      }
    } catch (e) {
      // Show error message
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to update preferences: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Assistant Configuration'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Profile', icon: Icon(Icons.person)),
            Tab(text: 'Personality', icon: Icon(Icons.psychology)),
            Tab(text: 'Language', icon: Icon(Icons.language)),
          ],
        ),
        actions: [
          if (_hasChanges)
            TextButton(
              onPressed: _isLoading ? null : _saveChanges,
              child: const Text('SAVE'),
            ),
        ],
      ),
      body: _isLoading && _nameController.text.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // Profile Tab
                _buildProfileTab(theme),
                
                // Personality Tab
                _buildPersonalityTab(theme),
                
                // Language Tab
                _buildLanguageTab(theme),
              ],
            ),
    );
  }

  Widget _buildProfileTab(ThemeData theme) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Name input
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Assistant Name',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _nameController,
                    decoration: InputDecoration(
                      hintText: 'e.g., Alex, Sage, Helper...',
                      prefixIcon: const Icon(Icons.badge),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onChanged: (_) => _markAsChanged(),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'This is how you\'ll address your assistant',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Avatar selection
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Avatar',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildAvatarSelection(theme),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Preview
          if (_nameController.text.isNotEmpty)
            AssistantPreview(
              assistantName: _nameController.text.trim(),
              selectedAvatarId: _selectedAvatar,
              avatarOptions: _getAvatarOptions(),
              customAvatars: getGlobalCustomAvatars(),
              previewMessage: 'Hi! I\'m ${_nameController.text.trim()}. How can I help you today?',
            ),
        ],
      ),
    );
  }

  Widget _buildPersonalityTab(ThemeData theme) {
    final personalityTraits = [
      {
        'name': 'formality',
        'label': 'Communication Style',
        'leftLabel': 'Formal',
        'rightLabel': 'Casual',
        'icon': Icons.chat_bubble_outline,
        'color': Colors.blue,
      },
      {
        'name': 'humor',
        'label': 'Humor Level',
        'leftLabel': 'Serious',
        'rightLabel': 'Playful',
        'icon': Icons.sentiment_satisfied,
        'color': Colors.orange,
      },
      {
        'name': 'motivation',
        'label': 'Motivation Style',
        'leftLabel': 'Gentle',
        'rightLabel': 'High-Energy',
        'icon': Icons.trending_up,
        'color': Colors.green,
      },
    ];
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Personality Settings',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Adjust how your assistant communicates with you.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 32),
          
          // Personality controls
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
              children: personalityTraits.map((trait) => 
                _buildPersonalitySlider(theme, trait)
              ).toList(),
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildPersonalitySlider(ThemeData theme, Map<String, dynamic> trait) {
    final value = (_personalityData[trait['name']] ?? 50).toDouble();
    final color = trait['color'] as Color;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(
                  trait['icon'],
                  color: color,
                  size: 18,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                trait['label'],
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
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
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 10),
              trackHeight: 5,
            ),
            child: Slider(
              value: value,
              min: 0,
              max: 100,
              divisions: 20,
              onChanged: (newValue) {
                setState(() {
                  _personalityData[trait['name']] = newValue.round();
                  _hasChanges = true;
                });
              },
              onChangeEnd: (newValue) {
                // Show saved notification when user stops sliding
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('${trait['label']} updated'),
                    duration: const Duration(seconds: 1),
                  ),
                );
              },
            ),
          ),
          
          // Labels
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
                    fontWeight: value < 50 ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
                Text(
                  '${value.round()}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: color,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  trait['rightLabel'],
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: value >= 50 
                        ? color 
                        : theme.colorScheme.onSurface.withOpacity(0.5),
                    fontWeight: value >= 50 ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageTab(ThemeData theme) {
    final languages = [
      {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
      {'code': 'ru', 'name': 'Русский', 'flag': '🇷🇺'},
      {'code': 'es', 'name': 'Español', 'flag': '🇪🇸'},
      {'code': 'fr', 'name': 'Français', 'flag': '🇫🇷'},
      {'code': 'de', 'name': 'Deutsch', 'flag': '🇩🇪'},
      {'code': 'it', 'name': 'Italiano', 'flag': '🇮🇹'},
      {'code': 'pt', 'name': 'Português', 'flag': '🇵🇹'},
    ];
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Language & Preferences',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Configure language and interaction preferences.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 32),
          
          // Language selection
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
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 16),
                
                DropdownButtonFormField<String>(
                  value: _languageData['language'] ?? 'en',
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
                      setState(() {
                        _languageData['language'] = value;
                        _hasChanges = true;
                      });
                      
                      // Show saved notification
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Language updated'),
                          duration: Duration(seconds: 2),
                        ),
                      );
                    }
                  },
                ),
                
                const SizedBox(height: 24),
                
                // Confirmation preference
                SwitchListTile(
                  title: Text(
                    'Ask before taking actions',
                    style: theme.textTheme.bodyMedium,
                  ),
                  subtitle: Text(
                    'Assistant will ask for confirmation before performing actions',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                  value: _languageData['requires_confirmation'] ?? true,
                  onChanged: (value) {
                    setState(() {
                      _languageData['requires_confirmation'] = value;
                      _hasChanges = true;
                    });
                    
                    // Show saved notification
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(value 
                          ? 'Confirmation enabled' 
                          : 'Confirmation disabled'),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                  contentPadding: EdgeInsets.zero,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAvatarSelection(ThemeData theme) {
    final avatarOptions = _getAvatarOptions();
    
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
        children: [
          // Avatar grid
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              // Built-in avatars
              ...avatarOptions.map((avatar) {
                final isSelected = _selectedAvatar == avatar['id'];
                final isCustom = avatar['isCustom'] == true;
                
                return Stack(
                  children: [
                    AssistantAvatar(
                      avatarId: avatar['id'],
                      imagePath: isCustom ? null : avatar['imagePath'],
                      imageData: isCustom ? avatar['imageData'] : null,
                      icon: avatar['icon'],
                      gradientColors: avatar['colors'] != null
                          ? List<Color>.from(avatar['colors'])
                          : null,
                      isSelected: isSelected,
                      size: 56.0,
                      onTap: () {
                        setState(() {
                          _selectedAvatar = avatar['id'];
                          _markAsChanged();
                        });
                      },
                    ),
                    // Delete button for custom avatars
                    if (isCustom)
                      Positioned(
                        top: -4,
                        right: -4,
                        child: GestureDetector(
                          onTap: () => _deleteCustomAvatar(avatar['id']),
                          child: Container(
                            width: 18,
                            height: 18,
                            decoration: BoxDecoration(
                              color: theme.colorScheme.error,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: theme.colorScheme.surface,
                                width: 2,
                              ),
                            ),
                            child: Icon(
                              Icons.close,
                              size: 10,
                              color: theme.colorScheme.onError,
                            ),
                          ),
                        ),
                      ),
                  ],
                );
              }).toList(),
              
              // Upload button
              _buildUploadButton(theme),
            ],
          ),
          
          const SizedBox(height: 12),
          
          Text(
            'Choose an avatar or upload your own image',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildUploadButton(ThemeData theme) {
    return GestureDetector(
      onTap: _handleUploadAvatar,
      child: Container(
        width: 56.0,
        height: 56.0,
        decoration: BoxDecoration(
          border: Border.all(
            color: theme.colorScheme.primary,
            width: 2,
            style: BorderStyle.solid,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.add_photo_alternate_outlined,
              size: 20,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 2),
            Text(
              'Upload',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.primary,
                fontSize: 10,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handleUploadAvatar() {
    // Reuse the upload dialog from onboarding
    showDialog(
      context: context,
      builder: (context) => CustomAvatarUploadDialog(
        onAvatarUploaded: (avatarId, imageData) {
          setState(() {
            // Store custom avatar data globally
            getGlobalCustomAvatars()[avatarId] = imageData;
            
            // Create avatar option
            final avatarOption = {
              'id': avatarId,
              'imageData': imageData,
              'isCustom': true,
              'icon': Icons.person,
            };
            
            // Store in global options
            getGlobalCustomAvatarOptions()[avatarId] = avatarOption;
            
            _selectedAvatar = avatarId;
            _markAsChanged();
          });
        },
      ),
    );
  }

  void _deleteCustomAvatar(String avatarId) {
    setState(() {
      // Remove from global storage
      getGlobalCustomAvatars().remove(avatarId);
      getGlobalCustomAvatarOptions().remove(avatarId);
      
      // If the deleted avatar was selected, switch to default
      if (_selectedAvatar == avatarId) {
        _selectedAvatar = 'ai_robot_blue';
      }
      _markAsChanged();
    });
  }

  List<Map<String, dynamic>> _getAvatarOptions() {
    // Base avatar options (same as in onboarding)
    final List<Map<String, dynamic>> baseOptions = [
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
    ];
    
    // Add custom avatars
    final List<Map<String, dynamic>> allOptions = [...baseOptions];
    getGlobalCustomAvatarOptions().forEach((avatarId, avatarData) {
      // Create a new map with proper typing
      final Map<String, dynamic> typedAvatar = {};
      avatarData.forEach((key, value) {
        typedAvatar[key] = value;
      });
      allOptions.add(typedAvatar);
    });
    
    return allOptions;
  }
}

