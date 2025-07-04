import 'package:flutter/material.dart';
import 'dart:io';
import '../../services/avatar_upload_service.dart';

/// Header widget for personal configuration with avatar upload
class PersonalConfigHeader extends StatelessWidget {
  final String? avatarId;
  final List<String> aiAvatars;
  final VoidCallback onAvatarTap;

  const PersonalConfigHeader({
    super.key,
    this.avatarId,
    required this.aiAvatars,
    required this.onAvatarTap,
  });

  bool _isEmojiAvatar(String path) {
    return aiAvatars.contains(path);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          // Avatar upload section
          GestureDetector(
            onTap: onAvatarTap,
            child: Stack(
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    gradient: avatarId == null ? LinearGradient(
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
                    child: avatarId == null 
                      ? Icon(
                          Icons.person,
                          size: 50,
                          color: theme.colorScheme.primary,
                        )
                      : _isEmojiAvatar(avatarId!)
                          ? Text(
                              avatarId!,
                              style: const TextStyle(fontSize: 50),
                            )
                          : ClipRRect(
                              borderRadius: BorderRadius.circular(38),
                              child: Image.network(
                                AvatarUploadService.getAvatarImageUrl(avatarId!),
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
          
          const SizedBox(height: 16),
          
          Text(
            'Personal Information',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          
          const SizedBox(height: 8),
          
          Text(
            'Tell us a bit about yourself to personalize your experience',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}