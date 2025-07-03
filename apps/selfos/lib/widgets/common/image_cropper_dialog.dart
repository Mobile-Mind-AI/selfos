import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image_cropper/image_cropper.dart';
import 'dart:typed_data';
import 'dart:io';

/// Dialog for selecting and cropping images to square format
class ImageCropperDialog extends StatefulWidget {
  final String title;
  final double cropSize;

  const ImageCropperDialog({
    super.key,
    this.title = 'Select and Crop Image',
    this.cropSize = 256.0,
  });

  @override
  State<ImageCropperDialog> createState() => _ImageCropperDialogState();
}

class _ImageCropperDialogState extends State<ImageCropperDialog> {
  final ImagePicker _picker = ImagePicker();
  bool _isProcessing = false;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        width: 400,
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header
            Row(
              children: [
                Icon(
                  Icons.crop_free,
                  color: theme.colorScheme.primary,
                  size: 24,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    widget.title,
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close),
                  tooltip: 'Close',
                ),
              ],
            ),
            
            const SizedBox(height: 24),
            
            // Description
            Text(
              defaultTargetPlatform == TargetPlatform.macOS
                  ? 'Choose an image source for your avatar. Square images work best.'
                  : 'Choose an image source and crop it to a square format for your avatar.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.7),
              ),
              textAlign: TextAlign.center,
            ),
            
            const SizedBox(height: 32),
            
            // Error message
            if (_errorMessage != null) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.error_outline,
                      color: theme.colorScheme.onErrorContainer,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onErrorContainer,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],
            
            // Action buttons
            if (_isProcessing)
              const Padding(
                padding: EdgeInsets.all(24),
                child: CircularProgressIndicator(),
              )
            else
              Row(
                children: [
                  Expanded(
                    child: _SourceButton(
                      icon: Icons.photo_library,
                      label: 'Gallery',
                      onTap: () => _pickImage(ImageSource.gallery),
                      theme: theme,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _SourceButton(
                      icon: Icons.camera_alt,
                      label: 'Camera',
                      onTap: () => _pickImage(ImageSource.camera),
                      theme: theme,
                    ),
                  ),
                ],
              ),
            
            const SizedBox(height: 16),
            
            // Technical requirements
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Requirements:',
                    style: theme.textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    defaultTargetPlatform == TargetPlatform.macOS
                        ? '• Maximum file size: 5MB\n• Supported formats: JPEG, PNG\n• Square images work best for avatars'
                        : '• Maximum file size: 5MB\n• Supported formats: JPEG, PNG\n• Image will be cropped to square format',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.8),
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

  Future<void> _pickImage(ImageSource source) async {
    setState(() {
      _isProcessing = true;
      _errorMessage = null;
    });

    try {
      final XFile? pickedFile = await _picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (pickedFile == null) {
        setState(() {
          _isProcessing = false;
        });
        return;
      }

      // Validate file size (5MB limit)
      final fileSize = await pickedFile.length();
      if (fileSize > 5 * 1024 * 1024) {
        setState(() {
          _isProcessing = false;
          _errorMessage = 'Image file is too large. Please select an image under 5MB.';
        });
        return;
      }

      await _cropImage(pickedFile.path, pickedFile);
    } catch (e) {
      setState(() {
        _isProcessing = false;
        _errorMessage = 'Failed to pick image: ${e.toString()}';
      });
    }
  }

  Future<void> _cropImage(String imagePath, XFile pickedFile) async {
    try {
      // Check if we're on macOS and handle differently
      if (defaultTargetPlatform == TargetPlatform.macOS) {
        // For macOS, just use the image without cropping due to plugin limitations
        final file = File(imagePath);
        final imageBytes = await file.readAsBytes();
        
        // Validate final image size
        if (imageBytes.length > 5 * 1024 * 1024) {
          setState(() {
            _isProcessing = false;
            _errorMessage = 'Image is too large. Please select an image under 5MB.';
          });
          return;
        }

        setState(() {
          _isProcessing = false;
        });

        // Detect file type from the original picked file
        String extension = 'jpg'; // Default fallback
        if (pickedFile.name.toLowerCase().endsWith('.png')) {
          extension = 'png';
        } else if (pickedFile.name.toLowerCase().endsWith('.jpeg') || pickedFile.name.toLowerCase().endsWith('.jpg')) {
          extension = 'jpg';
        } else if (pickedFile.name.toLowerCase().endsWith('.webp')) {
          extension = 'webp';
        }
        
        // Return the image data with metadata and close with the result
        if (mounted) {
          Navigator.of(context).pop({
            'imageData': imageBytes,
            'filename': 'custom_avatar_${DateTime.now().millisecondsSinceEpoch}.$extension',
            'extension': extension,
          });
        }
        return;
      }

      // For other platforms, use the cropper
      final croppedFile = await ImageCropper().cropImage(
        sourcePath: imagePath,
        aspectRatio: const CropAspectRatio(ratioX: 1, ratioY: 1),
        uiSettings: [
          AndroidUiSettings(
            toolbarTitle: 'Crop Avatar',
            toolbarColor: Theme.of(context).colorScheme.primary,
            toolbarWidgetColor: Theme.of(context).colorScheme.onPrimary,
            initAspectRatio: CropAspectRatioPreset.square,
            lockAspectRatio: true,
            hideBottomControls: false,
            showCropGrid: true,
          ),
          IOSUiSettings(
            title: 'Crop Avatar',
            aspectRatioLockEnabled: true,
            resetAspectRatioEnabled: false,
            aspectRatioPickerButtonHidden: true,
            showCancelConfirmationDialog: true,
          ),
          WebUiSettings(
            context: context,
            presentStyle: WebPresentStyle.dialog,
            size: const CropperSize(
              width: 320,
              height: 320,
            ),
          ),
        ],
      );

      if (croppedFile != null) {
        final imageBytes = await croppedFile.readAsBytes();
        
        // Validate final image size
        if (imageBytes.length > 5 * 1024 * 1024) {
          setState(() {
            _isProcessing = false;
            _errorMessage = 'Cropped image is still too large. Please try a smaller image.';
          });
          return;
        }

        setState(() {
          _isProcessing = false;
        });

        // Detect file type from the cropped file
        String extension = 'jpg'; // Default fallback
        if (croppedFile.path.toLowerCase().endsWith('.png')) {
          extension = 'png';
        } else if (croppedFile.path.toLowerCase().endsWith('.jpeg') || croppedFile.path.toLowerCase().endsWith('.jpg')) {
          extension = 'jpg';
        } else if (croppedFile.path.toLowerCase().endsWith('.webp')) {
          extension = 'webp';
        }
        
        // Return the cropped image data with metadata and close with the result
        if (mounted) {
          Navigator.of(context).pop({
            'imageData': imageBytes,
            'filename': 'custom_avatar_${DateTime.now().millisecondsSinceEpoch}.$extension',
            'extension': extension,
          });
        }
      } else {
        setState(() {
          _isProcessing = false;
        });
      }
    } catch (e) {
      setState(() {
        _isProcessing = false;
        _errorMessage = 'Failed to process image: ${e.toString()}';
      });
    }
  }
}

class _SourceButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final ThemeData theme;

  const _SourceButton({
    required this.icon,
    required this.label,
    required this.onTap,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
        decoration: BoxDecoration(
          border: Border.all(
            color: theme.colorScheme.outline.withOpacity(0.5),
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              size: 32,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: theme.textTheme.labelMedium?.copyWith(
                fontWeight: FontWeight.w500,
                color: theme.colorScheme.onSurface,
              ),
            ),
          ],
        ),
      ),
    );
  }
}