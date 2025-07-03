// widgets/avatar_selection_grid.dart
import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../common/assistant_avatar.dart';
import '../../services/avatar_upload_service.dart';

class AvatarSelectionGrid extends StatelessWidget {
  final List<Map<String, dynamic>> avatarOptions;
  final String selectedAvatar;
  final Function(String) onAvatarSelected;
  final Function(String, Uint8List) onAvatarUploaded;
  final Function(String) onAvatarDeleted;

  const AvatarSelectionGrid({
    super.key,
    required this.avatarOptions,
    required this.selectedAvatar,
    required this.onAvatarSelected,
    required this.onAvatarUploaded,
    required this.onAvatarDeleted,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Choose an Avatar',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.onSurface,
          ),
        ),

        const SizedBox(height: 12),

        // Responsive avatar grid with upload
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
            children: [
              // Responsive grid
              LayoutBuilder(
                builder: (context, constraints) {
                  // Calculate optimal columns (3-7 for desktop)
                  final screenWidth = constraints.maxWidth;
                  int columns;

                  if (screenWidth < 400) {
                    columns = 3; // Mobile: minimum 3
                  } else if (screenWidth < 600) {
                    columns = 4; // Small tablet
                  } else if (screenWidth < 800) {
                    columns = 5; // Large tablet
                  } else if (screenWidth < 1000) {
                    columns = 6; // Small desktop
                  } else {
                    columns = 7; // Large desktop: maximum 7
                  }

                  // Total items = avatars + upload button
                  final totalItems = avatarOptions.length + 1;

                  return GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: columns,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 1,
                    ),
                    itemCount: totalItems,
                    itemBuilder: (context, index) {
                      // Upload button as last item
                      if (index == avatarOptions.length) {
                        return _UploadButton(
                          onUpload: () => _handleUploadAvatar(context),
                        );
                      }

                      // Regular avatar options
                      final avatar = avatarOptions[index];
                      final isSelected = selectedAvatar == avatar['id'];
                      final isCustom = avatar['isCustom'] == true;

                      return LayoutBuilder(
                        builder: (context, constraints) {
                          // Grid item stretches to fill available space
                          final containerSize = constraints.maxWidth;
                          final padding = 8.0;
                          final availableContentSize = containerSize - (padding * 2);

                          // Ensure minimum 64x64 avatar size
                          final avatarSize = availableContentSize < 64 ? 64.0 : availableContentSize;

                          return Stack(
                            children: [
                              // Avatar container stretches to fill grid cell
                              GestureDetector(
                                onTap: () => onAvatarSelected(avatar['id']),
                                child: Container(
                                  width: double.infinity, // Stretch to fill grid cell
                                  height: double.infinity, // Stretch to fill grid cell
                                  decoration: BoxDecoration(
                                    border: Border.all(
                                      color: isSelected
                                          ? theme.colorScheme.primary
                                          : theme.colorScheme.outline.withOpacity(0.2),
                                      width: isSelected ? 2 : 1,
                                    ),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Padding(
                                    padding: EdgeInsets.all(padding),
                                    child: Center(
                                      child: SizedBox(
                                        width: avatarSize,
                                        height: avatarSize,
                                        child: ClipRRect(
                                          borderRadius: BorderRadius.circular(4),
                                          child: AssistantAvatar(
                                            avatarId: avatar['id'],
                                            imagePath: isCustom ? null : avatar['imagePath'],
                                            imageData: isCustom ? avatar['imageData'] : null,
                                            icon: avatar['icon'],
                                            gradientColors: avatar['colors'] != null
                                                ? List<Color>.from(avatar['colors'])
                                                : null,
                                            isSelected: false,
                                            size: avatarSize,
                                            isBackendStored: avatar['isBackendStored'] == true,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              // Delete button for custom avatars
                              if (isCustom)
                                Positioned(
                                  top: -8,
                                  right: -8,
                                  child: GestureDetector(
                                    onTap: () => onAvatarDeleted(avatar['id']),
                                    child: Container(
                                      width: 24,
                                      height: 24,
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
                                        size: 14,
                                        color: theme.colorScheme.onError,
                                      ),
                                    ),
                                  ),
                                ),
                            ],
                          );
                        },
                      );
                    },
                  );
                },
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
        ),
      ],
    );
  }

  void _handleUploadAvatar(BuildContext context) {
    // Show upload dialog
    showDialog(
      context: context,
      builder: (context) => CustomAvatarUploadDialog(
        onAvatarUploaded: onAvatarUploaded,
      ),
    );
  }
}

class _UploadButton extends StatelessWidget {
  final VoidCallback onUpload;

  const _UploadButton({
    required this.onUpload,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return LayoutBuilder(
      builder: (context, constraints) {
        // Upload button stretches to fill grid cell
        final containerSize = constraints.maxWidth;

        // Scale icon and text based on container size
        final iconSize = (containerSize * 0.25).clamp(16.0, 40.0);
        final fontSize = (containerSize * 0.12).clamp(10.0, 16.0);
        final spacing = (containerSize * 0.05).clamp(4.0, 12.0);

        return GestureDetector(
          onTap: onUpload,
          child: Container(
            width: double.infinity, // Stretch to fill grid cell
            height: double.infinity, // Stretch to fill grid cell
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
                  size: iconSize,
                  color: theme.colorScheme.primary,
                ),
                SizedBox(height: spacing),
                Text(
                  'Upload',
                  style: TextStyle(
                    fontSize: fontSize,
                    color: theme.colorScheme.primary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}