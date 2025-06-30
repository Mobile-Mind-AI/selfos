import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../config/app_config.dart';
import '../config/api_endpoints.dart';
import '../models/auth_request.dart';
import '../models/auth_response.dart';
import '../models/user.dart';
import 'storage_service.dart';

/// Authentication service for managing user login, registration, and auth state
/// 
/// This service handles all authentication-related API calls to the SelfOS backend.
/// It provides methods for email/password authentication, social login, token management,
/// and user session handling.
/// 
/// Key features:
/// - Email/password authentication
/// - Social login support (Google, Apple, etc.)
/// - Automatic token management
/// - Session persistence
/// - Error handling with detailed error messages
class AuthService {
  /// HTTP client for API requests
  late final Dio _dio;

  /// Creates an AuthService instance
  /// 
  /// Initializes the Dio client with base configuration for authentication endpoints.
  AuthService() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.baseUrl,
      connectTimeout: AppConfig.connectTimeout,
      receiveTimeout: AppConfig.apiTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // Add request interceptor for automatic token attachment
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          if (kDebugMode) {
            print('🚀 AUTH REQUEST: ${options.method} ${options.uri}');
            print('📦 REQUEST DATA: ${options.data}');
          }
          
          // Add authorization header if token exists
          final authHeader = await StorageService.getAuthorizationHeader();
          if (authHeader != null) {
            options.headers['Authorization'] = authHeader;
          }
          handler.next(options);
        },
        onResponse: (response, handler) async {
          if (kDebugMode) {
            print('✅ AUTH RESPONSE: ${response.statusCode} ${response.requestOptions.uri}');
          }
          handler.next(response);
        },
        onError: (error, handler) async {
          if (kDebugMode) {
            print('❌ AUTH ERROR: ${error.type} - ${error.message}');
            print('🔗 URL: ${error.requestOptions.uri}');
            print('📄 Response: ${error.response?.data}');
          }
          
          // Handle 401 errors (token expired)
          if (error.response?.statusCode == 401) {
            await _handleTokenExpired();
          }
          handler.next(error);
        },
      ),
    );
  }

  /// Authenticates user with email and password
  /// 
  /// [request] - Login request containing email/password
  /// 
  /// Returns [AuthResponse] on success
  /// Throws [AuthException] on failure
  Future<AuthResponse> login(LoginRequest request) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.login,
        data: request.toJson(),
      );

      final authResponse = AuthResponse.fromJson(response.data);
      
      // Store authentication data securely
      await StorageService.storeAuthData(authResponse: authResponse);
      await StorageService.storeLoginProvider(request.provider ?? 'email');

      return authResponse;
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw AuthException('Login failed: $e');
    }
  }

  /// Registers a new user account
  /// 
  /// [request] - Registration request containing user details
  /// 
  /// Returns [RegisterResponse] on success
  /// Throws [AuthException] on failure
  Future<RegisterResponse> register(RegisterRequest request) async {
    try {
      // Validate request before sending
      final validationErrors = request.validate();
      if (validationErrors.isNotEmpty) {
        throw AuthException(validationErrors.join(', '));
      }

      final response = await _dio.post(
        ApiEndpoints.register,
        data: request.toJson(),
      );

      final registerResponse = RegisterResponse.fromJson(response.data);
      
      // Store provider info for future reference
      await StorageService.storeLoginProvider(request.provider ?? 'email');

      return registerResponse;
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw AuthException('Registration failed: $e');
    }
  }

  /// Gets current user information from the server
  /// 
  /// Fetches fresh user data from the /auth/me endpoint.
  /// Requires valid authentication token.
  /// 
  /// Returns [User] on success
  /// Throws [AuthException] on failure
  Future<User> getCurrentUser() async {
    try {
      final response = await _dio.get(ApiEndpoints.me);
      final user = User.fromJson(response.data);
      
      // Update stored user data
      await StorageService.updateUserData(user);
      
      return user;
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw AuthException('Failed to get current user: $e');
    }
  }

  /// Refreshes the authentication token
  /// 
  /// Uses the stored refresh token to get a new access token.
  /// 
  /// Returns [AuthResponse] with new token on success
  /// Throws [AuthException] on failure
  Future<AuthResponse> refreshToken() async {
    try {
      final refreshToken = await StorageService.getRefreshToken();
      if (refreshToken == null) {
        throw AuthException('No refresh token available');
      }

      final response = await _dio.post(
        '${ApiEndpoints.baseUrl}/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      final authResponse = AuthResponse.fromJson(response.data);
      
      // Store new authentication data
      await StorageService.storeAuthData(authResponse: authResponse);
      
      return authResponse;
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw AuthException('Token refresh failed: $e');
    }
  }

  /// Logs out the current user
  /// 
  /// Clears all stored authentication data and optionally notifies the server.
  /// 
  /// [notifyServer] - Whether to call the server logout endpoint
  Future<void> logout({bool notifyServer = true}) async {
    try {
      if (notifyServer) {
        // Attempt to notify server, but don't fail if it doesn't work
        try {
          await _dio.post('${ApiEndpoints.baseUrl}/auth/logout');
        } catch (e) {
          // Server logout failed, but continue with local logout
          print('Server logout failed: $e');
        }
      }
    } finally {
      // Always clear local storage
      await StorageService.clearAuthData();
    }
  }

  /// Checks if user is currently authenticated
  /// 
  /// Returns true if valid authentication data exists and token is not expired.
  Future<bool> isAuthenticated() async {
    try {
      if (kDebugMode) {
        print('🔐 AUTH_SERVICE: Checking authentication...');
      }
      
      final hasAuth = await StorageService.hasAuthData();
      if (kDebugMode) {
        print('🔐 AUTH_SERVICE: Has auth data: $hasAuth');
      }
      if (!hasAuth) return false;

      final isExpired = await StorageService.isTokenExpired();
      if (kDebugMode) {
        print('🔐 AUTH_SERVICE: Token expired: $isExpired');
      }
      
      if (isExpired) {
        // Try to refresh token
        try {
          if (kDebugMode) {
            print('🔐 AUTH_SERVICE: Attempting token refresh...');
          }
          await refreshToken();
          return true;
        } catch (e) {
          if (kDebugMode) {
            print('🔐 AUTH_SERVICE: Token refresh failed: $e');
          }
          // Refresh failed, user needs to login again
          await StorageService.clearAuthData();
          return false;
        }
      }

      if (kDebugMode) {
        print('🔐 AUTH_SERVICE: Authentication valid');
      }
      return true;
    } catch (e) {
      if (kDebugMode) {
        print('🔐 AUTH_SERVICE: Authentication check failed: $e');
      }
      return false;
    }
  }

  /// Gets the stored user data
  /// 
  /// Returns cached [User] data from secure storage.
  Future<User?> getStoredUser() async {
    try {
      return await StorageService.getUserData();
    } catch (e) {
      return null;
    }
  }

  /// Social login with provider (Google, Apple, etc.)
  /// 
  /// [provider] - Social login provider (google, apple, facebook, etc.)
  /// [socialToken] - Token/credential from the social provider
  /// [email] - Optional email from social provider
  /// 
  /// Returns [AuthResponse] on success
  /// Throws [AuthException] on failure
  Future<AuthResponse> socialLogin({
    required String provider,
    required String socialToken,
    String? email,
  }) async {
    try {
      final request = LoginRequest.social(
        provider: provider,
        socialToken: socialToken,
        email: email,
      );

      return await login(request);
    } catch (e) {
      throw AuthException('Social login failed: $e');
    }
  }

  /// Social registration with provider
  /// 
  /// [provider] - Social registration provider
  /// [socialToken] - Token/credential from the social provider
  /// [email] - Optional email from social provider
  /// [displayName] - Optional display name from social provider
  /// 
  /// Returns [RegisterResponse] on success
  /// Throws [AuthException] on failure
  Future<RegisterResponse> socialRegister({
    required String provider,
    required String socialToken,
    String? email,
    String? displayName,
  }) async {
    try {
      final request = RegisterRequest.social(
        provider: provider,
        socialToken: socialToken,
        email: email,
        displayName: displayName,
      );

      return await register(request);
    } catch (e) {
      throw AuthException('Social registration failed: $e');
    }
  }

  /// Changes user password
  /// 
  /// [currentPassword] - Current password for verification
  /// [newPassword] - New password to set
  /// 
  /// Throws [AuthException] on failure
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      await _dio.post(
        '${ApiEndpoints.baseUrl}/auth/change-password',
        data: {
          'current_password': currentPassword,
          'new_password': newPassword,
        },
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw AuthException('Password change failed: $e');
    }
  }

  /// Requests password reset email
  /// 
  /// [email] - Email address to send reset link to
  /// 
  /// Throws [AuthException] on failure
  Future<void> requestPasswordReset(String email) async {
    try {
      await _dio.post(
        '${ApiEndpoints.baseUrl}/auth/forgot-password',
        data: {'email': email},
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw AuthException('Password reset request failed: $e');
    }
  }

  /// Handles token expiration
  Future<void> _handleTokenExpired() async {
    try {
      await refreshToken();
    } catch (e) {
      // Refresh failed, clear auth data
      await StorageService.clearAuthData();
    }
  }

  /// Converts Dio errors to AuthExceptions with user-friendly messages
  AuthException _handleDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return AuthException('Connection timeout. Please check your internet connection.');
      
      case DioExceptionType.connectionError:
        return AuthException('Unable to connect to server. Please check your internet connection.');
      
      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final responseData = error.response?.data;
        
        if (statusCode == 401) {
          return AuthException('Invalid credentials. Please check your email and password.');
        } else if (statusCode == 422) {
          // Validation errors
          if (responseData is Map && responseData.containsKey('detail')) {
            final detail = responseData['detail'];
            if (detail is List) {
              final errors = detail.map((e) => e['msg'] ?? e.toString()).join(', ');
              return AuthException(errors);
            } else if (detail is String) {
              return AuthException(detail);
            }
          }
          return AuthException('Invalid data provided. Please check your input.');
        } else if (statusCode == 409) {
          return AuthException('Email already exists. Please use a different email or try logging in.');
        } else if (statusCode! >= 500) {
          return AuthException('Server error. Please try again later.');
        }
        
        // Try to extract error message from response
        if (responseData is Map && responseData.containsKey('message')) {
          return AuthException(responseData['message']);
        }
        
        return AuthException('Request failed with status $statusCode');
      
      default:
        return AuthException('An unexpected error occurred. Please try again.');
    }
  }
}

/// Exception thrown for authentication-related errors
class AuthException implements Exception {
  final String message;
  final String? code;
  
  const AuthException(this.message, {this.code});
  
  @override
  String toString() => message;
}