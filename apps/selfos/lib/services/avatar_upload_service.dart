import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../widgets/common/image_cropper_dialog.dart';
import '../services/auth_service.dart';
import '../services/storage_service.dart';
import '../config/app_config.dart';

/// Service for handling custom avatar uploads
class AvatarUploadService {
  static const List<String> allowedExtensions = ['jpg', 'jpeg', 'png', 'webp'];
  static const int maxFileSizeBytes = 5 * 1024 * 1024; // 5MB

  /// Pick an image file for avatar upload
  static Future<Map<String, dynamic>?> pickAvatarImage() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: allowedExtensions,
        allowMultiple: false,
        withData: true,
      );

      if (result != null && result.files.isNotEmpty) {
        final file = result.files.first;

        // Validate file size
        if (file.size > maxFileSizeBytes) {
          throw Exception('File size must be less than 5MB');
        }

        // Validate file extension
        final extension = file.extension?.toLowerCase();
        if (extension == null || !allowedExtensions.contains(extension)) {
          throw Exception('Please select a valid image file (${allowedExtensions.join(', ')})');
        }

        return {
          'name': file.name,
          'bytes': file.bytes,
          'extension': extension,
          'size': file.size,
        };
      }
      return null;
    } catch (e) {
      rethrow;
    }
  }

  /// Upload avatar image to backend API
  static Future<Map<String, dynamic>> uploadAvatarToBackend(Uint8List imageData, String filename) async {
    try {
      // Get the authorization header
      final authHeader = await StorageService.getAuthorizationHeader();
      if (authHeader == null) {
        throw Exception('User not authenticated');
      }

      // Create multipart request
      final uri = Uri.parse('${AppConfig.baseUrl}/api/avatars/upload');
      final request = http.MultipartRequest('POST', uri);
      
      // Add authorization header
      request.headers['Authorization'] = authHeader;
      
      // Determine content type from filename extension
      String contentType;
      final lowerFilename = filename.toLowerCase();
      
      if (lowerFilename.endsWith('.png')) {
        contentType = 'image/png';
      } else if (lowerFilename.endsWith('.webp')) {
        contentType = 'image/webp';
      } else if (lowerFilename.endsWith('.jpg') || lowerFilename.endsWith('.jpeg')) {
        contentType = 'image/jpeg';
      } else {
        // Default to JPEG for unknown extensions
        contentType = 'image/jpeg';
      }
      
      // Debug logging
      print('🔍 FLUTTER DEBUG: Uploading file - filename: $filename, contentType: $contentType, size: ${imageData.length}');
      
      // Add the image file with proper content type
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          imageData,
          filename: filename,
          contentType: MediaType.parse(contentType),
        ),
      );

      // Send the request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data;
      } else {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'Upload failed');
      }
    } catch (e) {
      throw Exception('Failed to upload avatar: $e');
    }
  }

  /// Get avatar image URL for backend-stored avatars
  static String getAvatarImageUrl(String avatarId, {bool thumbnail = false}) {
    final query = thumbnail ? '?thumbnail=true' : '';
    return '${AppConfig.baseUrl}/api/avatars/$avatarId/image$query';
  }

  /// Load user's custom avatars from backend
  static Future<List<Map<String, dynamic>>?> loadUserAvatars() async {
    try {
      // Get the authorization header
      final authHeader = await StorageService.getAuthorizationHeader();
      if (authHeader == null) {
        throw Exception('User not authenticated');
      }

      // Create request to list avatars
      final uri = Uri.parse('${AppConfig.baseUrl}/api/avatars/list');
      final response = await http.get(
        uri,
        headers: {
          'Authorization': authHeader,
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((item) => item as Map<String, dynamic>).toList();
      } else {
        print('Failed to load avatars: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Error loading avatars: $e');
      return null;
    }
  }

  /// Delete avatar from backend
  static Future<bool> deleteAvatar(String avatarId) async {
    try {
      // Get the authorization header
      final authHeader = await StorageService.getAuthorizationHeader();
      if (authHeader == null) {
        throw Exception('User not authenticated');
      }

      // Create request to delete avatar
      final uri = Uri.parse('${AppConfig.baseUrl}/api/avatars/$avatarId');
      final response = await http.delete(
        uri,
        headers: {
          'Authorization': authHeader,
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        print('Failed to delete avatar: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      print('Error deleting avatar: $e');
      return false;
    }
  }

  /// Generate a unique avatar ID for custom uploads (fallback)
  static String generateCustomAvatarId() {
    return 'custom_${DateTime.now().millisecondsSinceEpoch}';
  }
}

/// Dialog for custom avatar upload
class CustomAvatarUploadDialog extends StatefulWidget {
  final Function(String avatarId, Uint8List imageData) onAvatarUploaded;

  const CustomAvatarUploadDialog({
    super.key,
    required this.onAvatarUploaded,
  });

  @override
  State<CustomAvatarUploadDialog> createState() => _CustomAvatarUploadDialogState();
}

class _CustomAvatarUploadDialogState extends State<CustomAvatarUploadDialog> {
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
      // Upload to backend
      final response = await AvatarUploadService.uploadAvatarToBackend(
        _selectedImageData!,
        _selectedImageName ?? 'avatar.jpg',
      );

      final avatarId = response['avatar_id'] as String;

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