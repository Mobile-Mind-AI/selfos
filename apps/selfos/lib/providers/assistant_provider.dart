import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../services/storage_service.dart';

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

  AssistantNotifier() : super(const AsyncValue.loading());

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

  /// Get all assistant profiles for the user
  Future<List<Map<String, dynamic>>?> getAssistantProfiles() async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return null;

      final response = await _dio.get(
        '${ApiConfig.baseUrl}/api/assistant_profiles/',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(response.data);
      }
      return null;
    } catch (e) {
      print('Failed to get assistant profiles: $e');
      return null;
    }
  }

  /// Create assistant profile using the profiles API
  Future<bool> createAssistantProfile(Map<String, dynamic> data) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      final response = await _dio.post(
        '${ApiConfig.baseUrl}/api/assistant_profiles/',
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      return response.statusCode == 201;
    } catch (e) {
      print('Failed to create assistant profile: $e');
      return false;
    }
  }

  /// Update assistant profile using the profiles API
  Future<bool> updateAssistantProfile(String profileId, Map<String, dynamic> data) async {
    try {
      final token = await StorageService.getAccessToken();
      if (token == null) return false;

      final response = await _dio.patch(
        '${ApiConfig.baseUrl}/api/assistant_profiles/$profileId',
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        ),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Failed to update assistant profile: $e');
      return false;
    }
  }
}

/// Provider for assistant profile management
final assistantProvider = StateNotifierProvider<AssistantNotifier, AsyncValue<AssistantProfile?>>((ref) {
  return AssistantNotifier();
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

/// Provider to get current assistant avatar
final assistantAvatarProvider = Provider<String>((ref) {
  final assistant = ref.watch(assistantProvider);
  return assistant.when(
    data: (profile) => profile?.avatarUrl ?? 'ai_robot_blue',
    loading: () => 'ai_robot_blue',
    error: (_, __) => 'ai_robot_blue',
  );
});