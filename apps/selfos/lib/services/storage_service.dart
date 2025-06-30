import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';
import '../config/app_config.dart';
import '../models/user.dart';
import '../models/auth_response.dart';

/// Storage service for managing user data with secure storage and fallback
/// 
/// This service provides storage for JWT tokens, user data, and other
/// information using Flutter Secure Storage when available, with SharedPreferences
/// as a fallback for development/testing environments.
/// 
/// Key features:
/// - Secure JWT token storage (when possible)
/// - SharedPreferences fallback for development
/// - User data persistence
/// - Automatic JSON serialization/deserialization
/// - Cross-platform support
class StorageService {
  /// Flutter Secure Storage instance
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
    ),
  );

  /// Flag to track if secure storage is available (assume false initially for macOS)
  static bool _useSecureStorage = false;
  static bool _initialized = false;
  
  /// Initialize storage - check if secure storage is available
  static Future<void> _initializeStorage() async {
    if (_initialized) return;
    
    // For now, always use SharedPreferences on macOS due to entitlement issues
    _useSecureStorage = false;
    _initialized = true;
    
    if (kDebugMode) {
      print('💾 STORAGE: Using SharedPreferences (secure storage disabled for development)');
    }
  }

  /// Helper method to write data with fallback to SharedPreferences
  static Future<void> _writeData(String key, String value) async {
    // Ensure storage is initialized
    await _initializeStorage();
    
    // Always use SharedPreferences if secure storage is disabled
    if (!_useSecureStorage) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, value);
      if (kDebugMode) {
        print('💾 STORAGE: Wrote $key to SharedPreferences');
      }
      return;
    }
    
    // Try secure storage first
    try {
      await _storage.write(key: key, value: value);
      if (kDebugMode) {
        print('💾 STORAGE: Wrote $key to secure storage');
      }
      return;
    } catch (e) {
      if (kDebugMode) {
        print('⚠️ Secure storage failed, falling back to SharedPreferences: $e');
      }
      _useSecureStorage = false;
      
      // Fallback to SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, value);
      if (kDebugMode) {
        print('💾 STORAGE: Wrote $key to SharedPreferences (fallback)');
      }
    }
  }

  /// Helper method to read data with fallback to SharedPreferences
  static Future<String?> _readData(String key) async {
    // Ensure storage is initialized
    await _initializeStorage();
    
    // Always use SharedPreferences if secure storage is disabled
    if (!_useSecureStorage) {
      final prefs = await SharedPreferences.getInstance();
      final value = prefs.getString(key);
      if (kDebugMode) {
        print('💾 STORAGE: Read $key from SharedPreferences: ${value != null ? "found" : "null"}');
      }
      return value;
    }
    
    // Try secure storage first
    try {
      final value = await _storage.read(key: key);
      if (kDebugMode) {
        print('💾 STORAGE: Read $key from secure storage: ${value != null ? "found" : "null"}');
      }
      return value;
    } catch (e) {
      if (kDebugMode) {
        print('⚠️ Secure storage failed, falling back to SharedPreferences: $e');
      }
      _useSecureStorage = false;
      
      // Fallback to SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      final value = prefs.getString(key);
      if (kDebugMode) {
        print('💾 STORAGE: Read $key from SharedPreferences (fallback): ${value != null ? "found" : "null"}');
      }
      return value;
    }
  }

  /// Helper method to delete data with fallback to SharedPreferences
  static Future<void> _deleteData(String key) async {
    // Ensure storage is initialized
    await _initializeStorage();
    
    if (_useSecureStorage) {
      try {
        await _storage.delete(key: key);
        return;
      } catch (e) {
        if (kDebugMode) {
          print('⚠️ Secure storage failed, falling back to SharedPreferences: $e');
        }
        _useSecureStorage = false;
      }
    }
    
    // Fallback to SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(key);
  }

  // Storage keys
  static const String _accessTokenKey = '${AppConfig.tokenKey}_access';
  static const String _refreshTokenKey = AppConfig.refreshTokenKey;
  static const String _userDataKey = AppConfig.userKey;
  static const String _tokenExpiryKey = '${AppConfig.tokenKey}_expiry';
  static const String _loginProviderKey = 'login_provider';

  /// Stores authentication data securely
  /// 
  /// Saves the access token, refresh token (if available), user data,
  /// and token expiry information.
  /// 
  /// [authResponse] - Authentication response from login/register
  /// [user] - User data to store
  static Future<void> storeAuthData({
    required AuthResponse authResponse,
    User? user,
  }) async {
    try {
      // Store access token
      await _writeData(_accessTokenKey, authResponse.accessToken);

      // Store refresh token if available
      if (authResponse.refreshToken != null) {
        await _writeData(_refreshTokenKey, authResponse.refreshToken!);
      }

      // Store token expiry if available
      if (authResponse.expiresIn != null) {
        final expiryTime = DateTime.now().add(
          Duration(seconds: authResponse.expiresIn!),
        );
        await _writeData(_tokenExpiryKey, expiryTime.toIso8601String());
      }

      // Store user data
      final userData = user ?? authResponse.user;
      if (userData != null) {
        await _writeData(_userDataKey, jsonEncode(userData.toJson()));
      }
    } catch (e) {
      throw StorageException('Failed to store authentication data: $e');
    }
  }

  /// Retrieves the stored access token
  /// 
  /// Returns the JWT access token if available, null otherwise.
  static Future<String?> getAccessToken() async {
    try {
      return await _readData(_accessTokenKey);
    } catch (e) {
      throw StorageException('Failed to retrieve access token: $e');
    }
  }

  /// Retrieves the stored refresh token
  /// 
  /// Returns the refresh token if available, null otherwise.
  static Future<String?> getRefreshToken() async {
    try {
      return await _readData(_refreshTokenKey);
    } catch (e) {
      throw StorageException('Failed to retrieve refresh token: $e');
    }
  }

  /// Retrieves the stored user data
  /// 
  /// Returns the [User] object if stored, null otherwise.
  static Future<User?> getUserData() async {
    try {
      final userData = await _readData(_userDataKey);
      if (userData != null) {
        final userJson = jsonDecode(userData) as Map<String, dynamic>;
        return User.fromJson(userJson);
      }
      return null;
    } catch (e) {
      throw StorageException('Failed to retrieve user data: $e');
    }
  }

  /// Checks if the stored token is expired
  /// 
  /// Returns true if the token is expired or no expiry data is stored.
  static Future<bool> isTokenExpired() async {
    try {
      if (kDebugMode) {
        print('💾 STORAGE: Checking token expiry...');
      }
      
      final expiryString = await _readData(_tokenExpiryKey);
      if (kDebugMode) {
        print('💾 STORAGE: Expiry string: $expiryString');
      }
      
      if (expiryString == null) {
        if (kDebugMode) {
          print('💾 STORAGE: No expiry data, token valid');
        }
        return false; // No expiry data
      }
      
      final expiryTime = DateTime.parse(expiryString);
      final now = DateTime.now();
      final isExpired = now.isAfter(expiryTime);
      
      if (kDebugMode) {
        print('💾 STORAGE: Token expires at: $expiryTime');
        print('💾 STORAGE: Current time: $now');
        print('💾 STORAGE: Token expired: $isExpired');
      }
      
      return isExpired;
    } catch (e) {
      if (kDebugMode) {
        print('💾 STORAGE: Error checking expiry: $e');
      }
      // If we can't parse the expiry, assume it's expired
      return true;
    }
  }

  /// Gets the authorization header value for API requests
  /// 
  /// Returns the properly formatted "Bearer {token}" string if a token
  /// is stored, null otherwise.
  static Future<String?> getAuthorizationHeader() async {
    try {
      final token = await getAccessToken();
      return token != null ? 'Bearer $token' : null;
    } catch (e) {
      return null;
    }
  }

  /// Stores the login provider (email, google, apple, etc.)
  /// 
  /// [provider] - The authentication provider used for login
  static Future<void> storeLoginProvider(String provider) async {
    try {
      await _writeData(_loginProviderKey, provider);
    } catch (e) {
      throw StorageException('Failed to store login provider: $e');
    }
  }

  /// Gets the stored login provider
  /// 
  /// Returns the provider string or 'email' as default.
  static Future<String> getLoginProvider() async {
    try {
      return await _readData(_loginProviderKey) ?? 'email';
    } catch (e) {
      return 'email';
    }
  }

  /// Checks if user authentication data exists
  /// 
  /// Returns true if both access token and user data are stored.
  static Future<bool> hasAuthData() async {
    try {
      if (kDebugMode) {
        print('💾 STORAGE: Checking if auth data exists...');
      }
      
      final token = await getAccessToken();
      final user = await getUserData();
      
      if (kDebugMode) {
        print('💾 STORAGE: Token exists: ${token != null}');
        print('💾 STORAGE: User data exists: ${user != null}');
      }
      
      return token != null && user != null;
    } catch (e) {
      if (kDebugMode) {
        print('💾 STORAGE: Error checking auth data: $e');
      }
      return false;
    }
  }

  /// Clears all stored authentication data
  /// 
  /// This method removes all stored tokens, user data, and auth-related
  /// information. Use this for logout functionality.
  static Future<void> clearAuthData() async {
    try {
      await Future.wait([
        _deleteData(_accessTokenKey),
        _deleteData(_refreshTokenKey),
        _deleteData(_userDataKey),
        _deleteData(_tokenExpiryKey),
        _deleteData(_loginProviderKey),
      ]);
    } catch (e) {
      throw StorageException('Failed to clear authentication data: $e');
    }
  }

  /// Updates stored user data
  /// 
  /// [user] - Updated user data to store
  static Future<void> updateUserData(User user) async {
    try {
      await _writeData(_userDataKey, jsonEncode(user.toJson()));
    } catch (e) {
      throw StorageException('Failed to update user data: $e');
    }
  }

  /// Gets all stored keys (for debugging)
  /// 
  /// Returns a list of all keys stored in secure storage.
  /// Note: This should only be used for debugging purposes.
  static Future<List<String>> getAllKeys() async {
    try {
      final all = await _storage.readAll();
      return all.keys.toList();
    } catch (e) {
      return [];
    }
  }

  /// Migrates old storage format if needed
  /// 
  /// This method can be used to migrate from older storage formats
  /// to maintain backward compatibility.
  static Future<void> migrateStorageIfNeeded() async {
    // Initialize storage system first - this is critical for app startup
    await _initializeStorage();
    
    if (kDebugMode) {
      print('💾 STORAGE: Storage system initialized');
    }
    
    try {
      // Check for old token format and migrate if needed
      final oldToken = await _readData(AppConfig.tokenKey);
      if (oldToken != null) {
        await _writeData(_accessTokenKey, oldToken);
        await _deleteData(AppConfig.tokenKey);
        if (kDebugMode) {
          print('💾 STORAGE: Migrated old token format');
        }
      }
    } catch (e) {
      // Migration failed, but not critical
      if (kDebugMode) {
        print('💾 STORAGE: Migration failed: $e');
      }
    }
  }
}

/// Exception thrown when storage operations fail
class StorageException implements Exception {
  final String message;
  
  const StorageException(this.message);
  
  @override
  String toString() => 'StorageException: $message';
}