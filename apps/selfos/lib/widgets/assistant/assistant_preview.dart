// widgets/assistant_preview.dart
import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../common/assistant_avatar.dart';

class AssistantPreview extends StatelessWidget {
  final String assistantName;
  final Map<String, dynamic> selectedAvatarData;
  final Map<String, Uint8List> globalCustomAvatars;
  final String previewMessage;

  const AssistantPreview({
    super.key,
    required this.assistantName,
    required this.selectedAvatarData,
    required this.globalCustomAvatars,
    required this.previewMessage,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            theme.colorScheme.primary.withOpacity(0.1),
            theme.colorScheme.secondary.withOpacity(0.1),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
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
                size: 16,
              ),
              const SizedBox(width: 6),
              Text(
                'Preview',
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: theme.colorScheme.primary,
                ),
              ),
            ],
          ),

          const SizedBox(height: 8),

          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Use actual avatar widget
                Container(
                  width: 28,
                  height: 28,
                  child: AssistantAvatar(
                    avatarId: selectedAvatarData['id'],
                    imagePath: selectedAvatarData['isCustom'] == true
                        ? null
                        : selectedAvatarData['imagePath'],
                    imageData: selectedAvatarData['isCustom'] == true
                        ? selectedAvatarData['imageData']
                        : globalCustomAvatars[selectedAvatarData['id']],
                    icon: selectedAvatarData['icon'],
                    gradientColors: selectedAvatarData['colors'] != null
                        ? List<Color>.from(selectedAvatarData['colors'])
                        : null,
                    size: 28.0,
                    isSelected: false,
                    isBackendStored: selectedAvatarData['isBackendStored'] == true,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        assistantName,
                        style: theme.textTheme.bodySmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: theme.colorScheme.primary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        previewMessage,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface,
                        ),
                      ),
                    ],
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