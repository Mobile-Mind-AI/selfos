import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:typed_data';
import '../../services/object_managers/media_attachment_manager.dart';
import '../../providers/auth_provider.dart' as simple_auth;
import '../../services/auth_provider.dart';
import '../common/image_cropper_dialog.dart';

/// Dialog for custom avatar upload
class CustomAvatarUploadDialog extends ConsumerStatefulWidget {
  final Function(String avatarId, Uint8List imageData) onAvatarUploaded;

  const CustomAvatarUploadDialog({
    super.key,
    required this.onAvatarUploaded,
  });

  @override
  ConsumerState<CustomAvatarUploadDialog> createState() => _CustomAvatarUploadDialogState();
}

class _CustomAvatarUploadDialogState extends ConsumerState<CustomAvatarUploadDialog> {
  final MediaAttachmentManager _mediaManager = MediaAttachmentManager.instance;
  bool _isUploading = false;
  String? _errorMessage;
  Uint8List? _selectedImageData;
  String? _selectedImageName;

  Future<void> _pickImage() async {
    try {
      setState(() {
        _errorMessage = null;
      });

      // Use ImageCropperDialog for better cropping experience
      final result = await showDialog<Map<String, dynamic>>(
        context: context,
        builder: (context) => const ImageCropperDialog(
          title: 'Select Avatar Image',
        ),
      );

      if (result != null && result['imageData'] != null) {
        setState(() {
          _selectedImageData = result['imageData'] as Uint8List;
          _selectedImageName = result['filename'] as String;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    }
  }

  Future<void> _uploadAvatar() async {
    if (_selectedImageData == null) return;

    setState(() {
      _isUploading = true;
      _errorMessage = null;
    });

    try {
      // Get current user
      final authState = ref.read(authProvider);
      String? userId;
      
      if (authState is AuthStateAuthenticated) {
        userId = authState.user.uid;
      } else {
        final user = ref.read(simple_auth.currentUserProvider);
        userId = user?.uid;
      }
      
      if (userId == null) {
        throw Exception('User not authenticated');
      }

      // Create avatar using media attachment manager (offline-first)
      final attachment = await _mediaManager.createAvatarFromImageData(
        userId: userId,
        imageData: _selectedImageData!,
        filename: _selectedImageName ?? 'avatar.jpg',
      );

      final avatarId = attachment['id'] as String;

      // Call the callback with the new avatar data
      widget.onAvatarUploaded(avatarId, _selectedImageData!);

      // Close the dialog
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isUploading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Text('Upload Custom Avatar'),
      content: SizedBox(
        width: 300,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Choose an image for your AI assistant avatar',
              style: theme.textTheme.bodyMedium,
            ),

            const SizedBox(height: 16),

            // Image preview or upload button
            if (_selectedImageData != null)
              _buildImagePreview(theme)
            else
              _buildUploadButton(theme),

            const SizedBox(height: 12),

            // Upload requirements
            _buildRequirements(theme),

            // Error message
            if (_errorMessage != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  _errorMessage!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.error,
                  ),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isUploading ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isUploading || _selectedImageData == null ? null : _uploadAvatar,
          child: _isUploading
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Upload'),
        ),
      ],
    );
  }

  Widget _buildImagePreview(ThemeData theme) {
    return Column(
      children: [
        Container(
          width: 100,
          height: 100,
          decoration: BoxDecoration(
            border: Border.all(color: theme.colorScheme.outline),
            borderRadius: BorderRadius.circular(8),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.memory(
              _selectedImageData!,
              width: 100,
              height: 100,
              fit: BoxFit.cover,
            ),
          ),
        ),

        const SizedBox(height: 8),

        Text(
          _selectedImageName ?? 'Selected image',
          style: theme.textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 8),

        TextButton(
          onPressed: _pickImage,
          child: const Text('Choose Different Image'),
        ),
      ],
    );
  }

  Widget _buildUploadButton(ThemeData theme) {
    return GestureDetector(
      onTap: _pickImage,
      child: Container(
        width: double.infinity,
        height: 120,
        decoration: BoxDecoration(
          border: Border.all(
            color: theme.colorScheme.primary,
            style: BorderStyle.solid,
            width: 2,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.cloud_upload_outlined,
              size: 32,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 8),
            Text(
              'Click to select image',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.primary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRequirements(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Requirements:',
          style: theme.textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          '• JPG, PNG, or WebP format\n• Maximum 5MB file size\n• Square images work best',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
      ],
    );
  }
}