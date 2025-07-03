import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../../config/app_config.dart';
import '../../services/storage_service.dart';
import 'package:http/http.dart' as http;

/// A reusable avatar widget for AI assistants
///
/// Displays portrait-style avatars with gradient backgrounds or images
/// and hover effects. Can be used in selection grids or profiles.
class AssistantAvatar extends StatelessWidget {
  final String avatarId;
  final IconData? icon;
  final List<Color>? gradientColors;
  final String? imagePath;
  final Uint8List? imageData;
  final bool isSelected;
  final VoidCallback? onTap;
  final double size;
  final bool showDescription;
  final String description;
  final bool isBackendStored;

  const AssistantAvatar({
    super.key,
    required this.avatarId,
    this.icon,
    this.gradientColors,
    this.imagePath,
    this.imageData,
    this.isSelected = false,
    this.onTap,
    this.size = 36.0, // Much smaller default size
    this.showDescription = false,
    this.description = '',
    this.isBackendStored = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: size,
        height: size,
        decoration: BoxDecoration(
          gradient: _shouldUseGradient()
              ? LinearGradient(
                  colors: gradientColors!,
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : null,
          borderRadius: BorderRadius.circular(8), // Smaller border radius for squares
          border: isSelected ? Border.all(
            color: theme.colorScheme.primary,
            width: 2.5,
          ) : null,
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: theme.colorScheme.primary.withOpacity(0.3),
                    blurRadius: 4,
                    spreadRadius: 1,
                  ),
                ]
              : null,
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: _buildAvatarContent(theme),
        ),
      ),
    );
  }

  bool _shouldUseGradient() {
    return gradientColors != null && imagePath == null && imageData == null;
  }

  Widget _buildAvatarContent(ThemeData theme) {
    // Priority: imageData > backend stored > imagePath > icon
    if (imageData != null) {
      return Image.memory(
        imageData!,
        width: size,
        height: size,
        fit: BoxFit.cover, // Fill the entire square
      );
    } else if (isBackendStored) {
      // Load image from backend API with authentication
      return _AuthenticatedImage(
        avatarId: avatarId,
        size: size,
        fallback: _buildFallbackIcon(theme),
      );
    } else if (imagePath != null) {
      return Image.asset(
        imagePath!,
        width: size,
        height: size,
        fit: BoxFit.cover, // Fill the entire square
        errorBuilder: (context, error, stackTrace) {
          return _buildFallbackIcon(theme);
        },
      );
    } else if (icon != null && _shouldUseGradient()) {
      return Icon(
        icon!,
        size: size * 0.5, // Slightly bigger icon
        color: Colors.white,
      );
    } else {
      return _buildFallbackIcon(theme);
    }
  }

  Widget _buildFallbackIcon(ThemeData theme) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: theme.colorScheme.primary.withOpacity(0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Icon(
        icon ?? Icons.smart_toy,
        size: size * 0.5,
        color: theme.colorScheme.primary,
      ),
    );
  }
}

/// Widget for loading authenticated images from backend
class _AuthenticatedImage extends StatefulWidget {
  final String avatarId;
  final double size;
  final Widget fallback;

  const _AuthenticatedImage({
    required this.avatarId,
    required this.size,
    required this.fallback,
  });

  @override
  State<_AuthenticatedImage> createState() => _AuthenticatedImageState();
}

class _AuthenticatedImageState extends State<_AuthenticatedImage> {
  Uint8List? _imageData;
  bool _loading = true;
  bool _error = false;

  @override
  void initState() {
    super.initState();
    _loadImage();
  }

  Future<void> _loadImage() async {
    try {
      final authHeader = await StorageService.getAuthorizationHeader();
      if (authHeader == null) {
        setState(() {
          _error = true;
          _loading = false;
        });
        return;
      }

      final response = await http.get(
        Uri.parse('${AppConfig.baseUrl}/api/avatars/${widget.avatarId}/image'),
        headers: {
          'Authorization': authHeader,
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          _imageData = response.bodyBytes;
          _loading = false;
        });
      } else {
        setState(() {
          _error = true;
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = true;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return SizedBox(
        width: widget.size,
        height: widget.size,
        child: Center(
          child: SizedBox(
            width: widget.size * 0.5,
            height: widget.size * 0.5,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      );
    }

    if (_error || _imageData == null) {
      return widget.fallback;
    }

    return Image.memory(
      _imageData!,
      width: widget.size,
      height: widget.size,
      fit: BoxFit.cover,
    );
  }
}

/// Compact grid widget for selecting assistant avatars with upload option
class AvatarSelectionGrid extends StatelessWidget {
  final List<Map<String, dynamic>> avatarOptions;
  final String selectedAvatarId;
  final Function(String) onAvatarSelected;
  final double avatarSize;
  final VoidCallback? onAddCustomAvatar;
  final Map<String, Uint8List>? customAvatars; // Store custom uploaded avatars

  const AvatarSelectionGrid({
    super.key,
    required this.avatarOptions,
    required this.selectedAvatarId,
    required this.onAvatarSelected,
    this.avatarSize = 36.0,
    this.onAddCustomAvatar,
    this.customAvatars,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(
          color: theme.colorScheme.outline.withOpacity(0.2),
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar selection grid
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              // Built-in avatars
              ...avatarOptions.map((avatar) {
                final isSelected = selectedAvatarId == avatar['id'];
                return AssistantAvatar(
                  avatarId: avatar['id'],
                  icon: avatar['icon'],
                  gradientColors: avatar['colors'] != null
                      ? List<Color>.from(avatar['colors'])
                      : null,
                  imagePath: avatar['imagePath'],
                  isSelected: isSelected,
                  size: avatarSize,
                  onTap: () => onAvatarSelected(avatar['id']),
                );
              }).toList(),

              // Custom uploaded avatars
              if (customAvatars != null)
                ...customAvatars!.entries.map((entry) {
                  final isSelected = selectedAvatarId == entry.key;
                  return AssistantAvatar(
                    avatarId: entry.key,
                    imageData: entry.value,
                    isSelected: isSelected,
                    size: avatarSize,
                    onTap: () => onAvatarSelected(entry.key),
                  );
                }).toList(),

              // Add custom avatar button
              if (onAddCustomAvatar != null)
                _buildAddAvatarButton(theme),
            ],
          ),

          const SizedBox(height: 8),

          // Helper text
          Text(
            'Choose an avatar or upload your own',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAddAvatarButton(ThemeData theme) {
    return GestureDetector(
      onTap: onAddCustomAvatar,
      child: Container(
        width: avatarSize,
        height: avatarSize,
        decoration: BoxDecoration(
          border: Border.all(
            color: theme.colorScheme.primary,
            width: 1.5,
            style: BorderStyle.solid,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(
          Icons.add,
          size: avatarSize * 0.5,
          color: theme.colorScheme.primary,
        ),
      ),
    );
  }
}

/// Preview widget that shows the selected avatar with assistant name
class AssistantPreview extends StatelessWidget {
  final String assistantName;
  final String selectedAvatarId;
  final List<Map<String, dynamic>> avatarOptions;
  final String previewMessage;
  final Map<String, Uint8List>? customAvatars;

  const AssistantPreview({
    super.key,
    required this.assistantName,
    required this.selectedAvatarId,
    required this.avatarOptions,
    required this.previewMessage,
    this.customAvatars,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final selectedAvatar = _findSelectedAvatar();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.colorScheme.primary.withOpacity(0.2),
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              _buildPreviewAvatar(selectedAvatar),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      assistantName,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                    Text(
                      'Your AI Assistant',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.chat_bubble_outline,
                  color: theme.colorScheme.primary,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    previewMessage,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.8),
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

  Map<String, dynamic> _findSelectedAvatar() {
    // First check custom avatars
    if (customAvatars?.containsKey(selectedAvatarId) == true) {
      return {
        'id': selectedAvatarId,
        'imageData': customAvatars![selectedAvatarId],
      };
    }

    // Then check built-in avatars
    return avatarOptions.firstWhere(
      (avatar) => avatar['id'] == selectedAvatarId,
      orElse: () => avatarOptions.first,
    );
  }

  Widget _buildPreviewAvatar(Map<String, dynamic> avatar) {
    if (avatar.containsKey('imageData')) {
      return AssistantAvatar(
        avatarId: avatar['id'],
        imageData: avatar['imageData'],
        size: 50,
      );
    } else {
      return AssistantAvatar(
        avatarId: avatar['id'],
        icon: avatar['icon'],
        gradientColors: avatar['colors'] != null
            ? List<Color>.from(avatar['colors'])
            : null,
        imagePath: avatar['imagePath'],
        size: 50,
      );
    }
  }
}