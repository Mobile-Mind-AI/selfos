import 'package:dio/dio.dart';
import '../config/api_endpoints.dart';
import '../models/chat_message.dart';

/// Service for AI chat functionality
class ChatService {
  final Dio _dio;

  ChatService({required Dio dio}) : _dio = dio;

  /// Send a message to the AI chat endpoint
  Future<ChatMessage> sendMessage(String message) async {
    try {
      // Check if this looks like a goal to decompose, otherwise use chat
      final bool isGoalRequest = _isGoalDecompositionRequest(message);
      
      return isGoalRequest 
        ? await _sendGoalDecomposition(message)
        : await _sendChatMessage(message);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw ChatException('Authentication required. Please log in again.');
      } else if (e.response?.statusCode == 422) {
        throw ChatException('Invalid request format. Please try again.');
      } else if (e.response?.statusCode == 429) {
        throw ChatException('Too many requests. Please try again later.');
      } else if (e.response?.statusCode == 500) {
        throw ChatException('AI service temporarily unavailable. Please try again.');
      } else if (e.type == DioExceptionType.connectionTimeout) {
        throw ChatException('Connection timeout. Please check your internet connection.');
      } else if (e.type == DioExceptionType.receiveTimeout) {
        throw ChatException('Response timeout. Please try again.');
      } else {
        throw ChatException('Failed to send message: ${e.response?.data?['detail'] ?? e.message ?? 'Unknown error'}');
      }
    } catch (e) {
      throw ChatException('Unexpected error: $e');
    }
  }

  /// Check if the message looks like a goal decomposition request
  bool _isGoalDecompositionRequest(String message) {
    final goalKeywords = [
      'i want to', 'i need to', 'help me', 'create a plan',
      'break down', 'decompose', 'achieve', 'goal', 'learn to'
    ];
    
    final lowercaseMessage = message.toLowerCase();
    return goalKeywords.any((keyword) => lowercaseMessage.contains(keyword));
  }

  /// Send a regular chat message
  Future<ChatMessage> _sendChatMessage(String message) async {
    final response = await _dio.post(
      ApiEndpoints.aiChat,
      data: {
        'message': message,
        'conversation_history': [],
        'user_context': {},
      },
    );

    if (response.statusCode == 200) {
      final responseData = response.data;
      return ChatMessage.ai(
        text: responseData['content'] ?? 'No response received',
        id: responseData['request_id']?.toString(),
      );
    } else {
      throw ChatException('Failed to get response from AI service (${response.statusCode})');
    }
  }

  /// Send a goal decomposition request
  Future<ChatMessage> _sendGoalDecomposition(String message) async {
    final response = await _dio.post(
      ApiEndpoints.aiDecomposeGoal,
      data: {
        'goal_description': message,
        'life_areas': [],
        'existing_goals': [],
        'user_preferences': null,
        'additional_context': null,
      },
    );

    if (response.statusCode == 200) {
      final responseData = response.data;
      
      // Parse the response according to GoalDecompositionResponse format
      String responseText = responseData['content'] ?? 'No response received';
      
      // Add suggested tasks if available
      if (responseData['suggested_tasks'] != null && 
          responseData['suggested_tasks'] is List &&
          (responseData['suggested_tasks'] as List).isNotEmpty) {
        responseText += '\n\n📋 **Suggested Tasks:**\n';
        for (var task in responseData['suggested_tasks']) {
          responseText += '\n• **${task['title'] ?? 'Task'}**';
          if (task['description'] != null) {
            responseText += ': ${task['description']}';
          }
          if (task['estimated_duration'] != null) {
            responseText += ' (Est. ${task['estimated_duration']} mins)';
          }
        }
      }
      
      // Add overall timeline if available
      if (responseData['overall_timeline'] != null) {
        responseText += '\n\n⏰ **Timeline:** ${responseData['overall_timeline']}';
      }
      
      // Add next steps if available
      if (responseData['next_steps'] != null && 
          responseData['next_steps'] is List &&
          (responseData['next_steps'] as List).isNotEmpty) {
        responseText += '\n\n🎯 **Next Steps:**\n';
        for (var step in responseData['next_steps']) {
          responseText += '\n• $step';
        }
      }
      
      return ChatMessage.ai(
        text: responseText,
        id: responseData['request_id']?.toString(),
      );
    } else {
      throw ChatException('Failed to get response from AI service (${response.statusCode})');
    }
  }

  /// Get chat history (if implemented on backend)
  Future<List<ChatMessage>> getChatHistory() async {
    try {
      final response = await _dio.get(ApiEndpoints.aiChat);
      
      if (response.statusCode == 200) {
        final List<dynamic> messages = response.data['messages'] ?? [];
        return messages.map((msg) => ChatMessage(
          text: msg['text'] ?? '',
          isUser: msg['isUser'] ?? false,
          timestamp: DateTime.tryParse(msg['timestamp'] ?? '') ?? DateTime.now(),
          id: msg['id']?.toString(),
        )).toList();
      } else {
        return [];
      }
    } catch (e) {
      // Return empty list if history fetch fails
      return [];
    }
  }
}

/// Custom exception for chat operations
class ChatException implements Exception {
  final String message;
  
  const ChatException(this.message);
  
  @override
  String toString() => 'ChatException: $message';
}