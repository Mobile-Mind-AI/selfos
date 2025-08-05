import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// Environment configuration for different platforms and build modes
class Environment {
  /// Get the appropriate backend URL based on the platform
  static String get backendUrl {
    // For web, localhost works fine
    if (kIsWeb) {
      return 'http://localhost:8000';
    }
    
    // For mobile/desktop platforms
    try {
      if (Platform.isAndroid) {
        // Android emulator uses 10.0.2.2 to access host machine
        return 'http://10.0.2.2:8000';
      } else if (Platform.isIOS || Platform.isMacOS) {
        // iOS simulator and macOS can use localhost
        // But for real devices, you'd need the actual IP
        return 'http://localhost:8000';
      } else {
        // Default for other platforms
        return 'http://localhost:8000';
      }
    } catch (e) {
      // Fallback if Platform is not available
      return 'http://localhost:8000';
    }
  }
  
  /// Get the base URL for API calls
  static String get apiBaseUrl => backendUrl;
  
  /// Get the health check endpoint
  static String get healthEndpoint => '$backendUrl/';
  
  /// Check if we're in development mode
  static bool get isDevelopment => !const bool.fromEnvironment('dart.vm.product');
  
  /// Get backend URL for specific host (useful for real devices)
  static String backendUrlForHost(String hostIp) {
    return 'http://$hostIp:8000';
  }
}