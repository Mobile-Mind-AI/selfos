/// API configuration for SelfOS Flutter app
class ApiConfig {
  /// Base URL for the SelfOS backend API
  static const String baseUrl = 'http://localhost:8000';
  
  /// API endpoints
  static const String authEndpoint = '/api/auth';
  static const String goalsEndpoint = '/api/goals';
  static const String tasksEndpoint = '/api/tasks';
  static const String onboardingEndpoint = '/api/onboarding';
  static const String assistantEndpoint = '/api/assistant';
  
  /// Request timeout duration
  static const Duration requestTimeout = Duration(seconds: 30);
  
  /// Connect timeout duration
  static const Duration connectTimeout = Duration(seconds: 15);
  
  /// Receive timeout duration
  static const Duration receiveTimeout = Duration(seconds: 30);
}