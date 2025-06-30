import 'app_config.dart';

/// API endpoint definitions for the SelfOS backend
class ApiEndpoints {
  // Base URL
  static String get baseUrl => AppConfig.baseUrl;
  
  // Authentication
  static String get register => '${AppConfig.authEndpoint}/register';
  static String get login => '${AppConfig.authEndpoint}/login';
  static String get me => '${AppConfig.authEndpoint}/me';
  
  // Goals
  static String get goals => AppConfig.goalsEndpoint;
  static String goalById(int id) => '${AppConfig.goalsEndpoint}/$id';
  
  // Tasks
  static String get tasks => AppConfig.tasksEndpoint;
  static String taskById(int id) => '${AppConfig.tasksEndpoint}/$id';
  static String tasksByGoal(int goalId) => '${AppConfig.tasksEndpoint}/goal/$goalId';
  
  // Life Areas
  static String get lifeAreas => AppConfig.lifeAreasEndpoint;
  static String lifeAreaById(int id) => '${AppConfig.lifeAreasEndpoint}/$id';
  
  // AI Services
  static String get aiChat => '${AppConfig.aiEndpoint}/chat';
  static String get aiDecomposeGoal => '${AppConfig.aiEndpoint}/decompose-goal';
  static String get aiMemorySearch => '${AppConfig.aiEndpoint}/memory/search';
  static String get aiHealth => '${AppConfig.aiEndpoint}/health';
}