/// Application configuration and constants
class AppConfig {
  // API Configuration
  static const String baseUrl = 'http://127.0.0.1:8000';
  static const String apiVersion = 'v1';
  
  // API Endpoints
  static const String authEndpoint = '/auth';
  static const String goalsEndpoint = '/api/goals';
  static const String tasksEndpoint = '/api/tasks';
  static const String lifeAreasEndpoint = '/api/life-areas';
  static const String aiEndpoint = '/api/ai';
  
  // Storage Keys
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String refreshTokenKey = 'refresh_token';
  
  // App Information
  static const String appName = 'SelfOS';
  static const String appVersion = '1.0.0';
  
  // Timeouts
  static const Duration apiTimeout = Duration(seconds: 60);
  static const Duration connectTimeout = Duration(seconds: 15);
}