import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../services/storage_service.dart';
import '../services/object_managers/assistant_profile_manager.dart';
import '../providers/auth_provider.dart' as simple_auth;
import '../services/auth_provider.dart';
import '../models/user.dart';

/// Assistant profile data model
class AssistantProfile {
  final String id;
  final String name;
  final String avatarUrl;
  final Map<String, dynamic> style;
  final String language;
  final bool requiresConfirmation;

  AssistantProfile({
    required this.id,
    required this.name,
    required this.avatarUrl,
    required this.style,
    required this.language,
    required this.requiresConfirmation,
  });

  factory AssistantProfile.fromJson(Map<String, dynamic> json) {
    return AssistantProfile(
      id: json['id'] ?? '',
      name: json['name'] ?? 'Assistant',
      avatarUrl: json['avatar_url'] ?? 'ai_robot_blue',
      style: json['style'] ?? {},
      language: json['language'] ?? 'en',
      requiresConfirmation: json['requires_confirmation'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'avatar_url': avatarUrl,
      'style': style,
      'language': language,
      'requires_confirmation': requiresConfirmation,
    };
  }
}

/// Notifier for managing assistant profile state
class AssistantNotifier extends StateNotifier<AsyncValue<AssistantProfile?>> {
  final Dio _dio = Dio();
  final Ref ref;

  AssistantNotifier(this.ref) : super(const AsyncValue.data(null));

  /// Get the current assistant profile
  Future<Map<String, dynamic>?> getCurrentAssistant() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return null;

      final response = await _dio.get(
        '${ApiConfig.baseUrl}/api/assistant/profile',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        final profile = AssistantProfile.fromJson(response.data);
        state = AsyncValue.data(profile);
        return profile.toJson();
      }
      return null;
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
      return null;
    }
  }

  /// Update the assistant profile
  Future<bool> updateAssistant(Map<String, dynamic> updateData) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      final response = await _dio.put(
        '${ApiConfig.baseUrl}/api/assistant/profile',
        data: updateData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        final profile = AssistantProfile.fromJson(response.data);
        state = AsyncValue.data(profile);
        return true;
      }
      return false;
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
      return false;
    }
  }

  /// Create a new assistant profile
  Future<bool> createAssistant(Map<String, dynamic> assistantData) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      final response = await _dio.post(
        '${ApiConfig.baseUrl}/api/assistant/profile',
        data: assistantData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 201) {
        final profile = AssistantProfile.fromJson(response.data);
        state = AsyncValue.data(profile);
        return true;
      }
      return false;
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
      return false;
    }
  }

  /// Get all assistant profiles for the user (offline-first)
  Future<List<Map<String, dynamic>>?> getAssistantProfiles() async {
    try {
      // Get current user from auth state
      final authState = ref.read(authProvider);
      User? user;
      if (authState is AuthStateAuthenticated) {
        user = authState.user;
      } else {
        user = ref.read(simple_auth.currentUserProvider);
      }
      if (user == null || user.uid == null) return null;
      
      // Use AssistantProfileManager for offline-first operation
      final profiles = await AssistantProfileManager.instance.getByUserId(user.uid!);
      return profiles;
    } catch (e) {
      // Failed to get assistant profiles: $e
      return null;
    }
  }

  /// Create assistant profile (offline-first)
  Future<bool> createAssistantProfile(Map<String, dynamic> data) async {
    try {
      // Creating assistant profile...
      
      // Get current user from auth state
      final authState = ref.read(authProvider);
      // Auth state type: ${authState.runtimeType}
      
      User? user;
      if (authState is AuthStateAuthenticated) {
        user = authState.user;
        // User from AuthStateAuthenticated: ${user.uid}
      } else {
        // Fallback to current user provider
        final currentUser = ref.read(simple_auth.currentUserProvider);
        user = currentUser;
        // User from currentUserProvider: ${user?.uid}
      }
      
      if (user == null || user.uid == null) {
        // No current user found in any provider!
        return false;
      }
      
      // Use AssistantProfileManager for offline-first operation
      final profile = await AssistantProfileManager.instance.create(
        userId: user.uid!,
        name: data['name'] as String,
        description: data['description'] as String?,
        avatarUrl: data['avatar_url'] as String?,
        aiModel: data['ai_model'] as String? ?? 'gpt-3.5-turbo',
        language: data['language'] as String? ?? 'en',
        style: data['style'] as Map<String, dynamic>? ?? {},
        isDefault: data['is_default'] as bool? ?? true,
        isPublic: data['is_public'] as bool? ?? false,
        requiresConfirmation: data['requires_confirmation'] as bool? ?? true,
        dialogueTemperature: data['dialogue_temperature'] as double? ?? 0.8,
        intentTemperature: data['intent_temperature'] as double? ?? 0.3,
        customInstructions: data['custom_instructions'] as String?,
      );
      
      // Profile created: ${profile != null}
      
      return profile != null;
    } catch (e, stackTrace) {
      // Failed to create assistant profile: $e
      return false;
    }
  }

  /// Update assistant profile (offline-first)
  Future<bool> updateAssistantProfile(String profileId, Map<String, dynamic> data) async {
    try {
      // Get current user from auth state
      final authState = ref.read(authProvider);
      User? user;
      if (authState is AuthStateAuthenticated) {
        user = authState.user;
      } else {
        user = ref.read(simple_auth.currentUserProvider);
      }
      
      if (user == null || user.uid == null) return false;
      
      // Use AssistantProfileManager for offline-first operation
      final profile = await AssistantProfileManager.instance.update(
        profileId,
        data,
      );
      
      return profile != null;
    } catch (e) {
      // Failed to update assistant profile: $e
      return false;
    }
  }

  /// Create assistant profile and return the ID (offline-first)
  Future<String?> createAssistantProfileAndGetId(Map<String, dynamic> data) async {
    try {
      // Get current user from auth state
      final authState = ref.read(authProvider);
      User? user;
      if (authState is AuthStateAuthenticated) {
        user = authState.user;
      } else {
        user = ref.read(simple_auth.currentUserProvider);
      }
      
      if (user == null || user.uid == null) return null;
      
      // Use AssistantProfileManager for offline-first operation
      final profile = await AssistantProfileManager.instance.create(
        userId: user.uid!,
        name: data['name'] as String,
        description: data['description'] as String?,
        avatarUrl: data['avatar_url'] as String?,
        aiModel: data['ai_model'] as String? ?? 'gpt-3.5-turbo',
        language: data['language'] as String? ?? 'en',
        style: data['style'] as Map<String, dynamic>? ?? {},
        isDefault: data['is_default'] as bool? ?? true,
        isPublic: data['is_public'] as bool? ?? false,
        requiresConfirmation: data['requires_confirmation'] as bool? ?? true,
        dialogueTemperature: data['dialogue_temperature'] as double? ?? 0.8,
        intentTemperature: data['intent_temperature'] as double? ?? 0.3,
        customInstructions: data['custom_instructions'] as String?,
      );
      
      // Return the profile ID if created successfully
      return profile?['id'] as String?;
    } catch (e) {
      print('Failed to create assistant profile and get ID: $e');
      return null;
    }
  }
}

/// Provider for assistant profile management
final assistantProvider = StateNotifierProvider<AssistantNotifier, AsyncValue<AssistantProfile?>>((ref) {
  return AssistantNotifier(ref);
});

/// Provider to get current assistant name
final assistantNameProvider = Provider<String>((ref) {
  final assistant = ref.watch(assistantProvider);
  return assistant.when(
    data: (profile) => profile?.name ?? 'Assistant',
    loading: () => 'Assistant',
    error: (_, __) => 'Assistant',
  );
});

/// Provider to get current assistant avatar ID
final assistantAvatarProvider = Provider<String>((ref) {
  final assistant = ref.watch(assistantProvider);
  return assistant.when(
    data: (profile) => profile?.avatarUrl ?? 'ai_robot_blue',
    loading: () => 'ai_robot_blue',
    error: (_, __) => 'ai_robot_blue',
  );
});