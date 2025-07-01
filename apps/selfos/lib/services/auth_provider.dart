import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../models/auth_request.dart';
import '../models/auth_response.dart';
import 'auth_service.dart';
import 'social_login_service.dart';

/// Authentication state representing the current user's auth status
/// 
/// This sealed class represents all possible authentication states in the app.
sealed class AuthState {
  const AuthState();
}

/// Initial state - checking if user is authenticated
class AuthStateInitial extends AuthState {
  const AuthStateInitial();
}

/// User is authenticated with valid session
class AuthStateAuthenticated extends AuthState {
  final User user;

  const AuthStateAuthenticated(this.user);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is AuthStateAuthenticated && other.user == user;
  }

  @override
  int get hashCode => user.hashCode;
}

/// User is not authenticated
class AuthStateUnauthenticated extends AuthState {
  const AuthStateUnauthenticated();
}

/// Authentication operation in progress
class AuthStateLoading extends AuthState {
  final String? message;

  const AuthStateLoading([this.message]);
}

/// Authentication error occurred
class AuthStateError extends AuthState {
  final String message;
  final Exception? exception;

  const AuthStateError(this.message, [this.exception]);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is AuthStateError && other.message == message;
  }

  @override
  int get hashCode => message.hashCode;
}

/// Authentication provider - manages global auth state
/// 
/// This provider handles all authentication state management using Riverpod.
/// It provides reactive authentication state that automatically updates
/// throughout the app when the user's auth status changes.
/// 
/// Usage:
/// ```dart
/// // Watch auth state
/// final authState = ref.watch(authProvider);
/// 
/// // Trigger login
/// await ref.read(authProvider.notifier).login(loginRequest);
/// 
/// // Check if authenticated
/// final isAuthenticated = ref.read(authProvider) is AuthStateAuthenticated;
/// ```
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;

  AuthNotifier(this._authService) : super(const AuthStateInitial()) {
    initialize();
  }

  /// Initializes authentication state on app startup
  ///
  /// This method should be called from the splash screen to determine
  /// the user's authentication status and load cached user data.
  Future<void> initialize() async {
    try {
      if (kDebugMode) {
        print('🔐 AUTH: Initializing authentication state...');
      }

      state = const AuthStateLoading('Checking authentication...');

      final isAuthenticated = await _authService.isAuthenticated();

      if (kDebugMode) {
        print('🔐 AUTH: Is authenticated: $isAuthenticated');
      }

      if (isAuthenticated) {
        final user = await _authService.getStoredUser();
        if (kDebugMode) {
          print('🔐 AUTH: Retrieved user: ${user?.email}');
        }
        if (user != null) {
          state = AuthStateAuthenticated(user);
          if (kDebugMode) {
            print('🔐 AUTH: Set state to authenticated');
          }

          // Optionally refresh user data from server
          _refreshUserData();
        } else {
          if (kDebugMode) {
            print('🔐 AUTH: No user data found, setting unauthenticated');
          }
          state = const AuthStateUnauthenticated();
        }
      } else {
        if (kDebugMode) {
          print('🔐 AUTH: Not authenticated, setting unauthenticated');
        }
        state = const AuthStateUnauthenticated();
      }
    } catch (e) {
      if (kDebugMode) {
        print('🔐 AUTH: Error during initialization: $e');
      }
      state = AuthStateError('Failed to initialize authentication: $e');
    }
  }

  /// Refreshes user data from server in the background
  Future<void> _refreshUserData() async {
    try {
      final user = await _authService.getCurrentUser();
      if (state is AuthStateAuthenticated) {
        state = AuthStateAuthenticated(user);
      }
    } catch (e) {
      // Silent fail - don't change state if refresh fails
      print('Failed to refresh user data: $e');
    }
  }

  /// Authenticates user with email and password
  /// 
  /// [request] - Login request containing credentials
  /// 
  /// Returns true on success, false on failure
  Future<bool> login(LoginRequest request) async {
    state = const AuthStateLoading('Signing in...');

    try {
      final authResponse = await _authService.login(request);

      if (kDebugMode) {
        print('🔐 AUTH: Login successful, storing credentials...');
      }

      // Get user data from response
      User? user = authResponse.user;
      if (user == null) {
        if (kDebugMode) {
          print('🔐 AUTH: No user in auth response, fetching from server...');
        }
        user = await _authService.getCurrentUser();
      } else {
        if (kDebugMode) {
          print('🔐 AUTH: Using user from auth response: ${user.email}');
        }
      }

      state = AuthStateAuthenticated(user);
      return true;
    } on AuthException catch (e) {
      state = AuthStateError(e.message, e);
      return false;
    } catch (e) {
      state = AuthStateError(
          'Login failed: $e', e is Exception ? e : Exception(e.toString()));
      return false;
    }
  }

  /// Registers a new user account
  /// 
  /// [request] - Registration request containing user details
  /// 
  /// Returns true on success, false on failure
  Future<bool> register(RegisterRequest request) async {
    state = const AuthStateLoading('Creating account...');

    try {
      await _authService.register(request);

      // After successful registration, attempt to login
      final loginRequest = LoginRequest.emailPassword(
        email: request.username,
        password: request.password,
      );

      return await login(loginRequest);
    } on AuthException catch (e) {
      state = AuthStateError(e.message, e);
      return false;
    } catch (e) {
      state = AuthStateError('Registration failed: $e',
          e is Exception ? e : Exception(e.toString()));
      return false;
    }
  }

  /// Logs out the current user
  /// 
  /// [notifyServer] - Whether to notify the server about logout
  Future<void> logout({bool notifyServer = true}) async {
    state = const AuthStateLoading('Signing out...');

    try {
      if (kDebugMode) {
        print('🔐 AUTH: Logging out user...');
      }
      await _authService.logout(notifyServer: notifyServer);
      if (kDebugMode) {
        print('🔐 AUTH: Logout successful, clearing credentials');
      }
      state = const AuthStateUnauthenticated();
    } catch (e) {
      if (kDebugMode) {
        print('🔐 AUTH: Logout error: $e, clearing local state');
      }
      // Even if server logout fails, clear local state
      state = const AuthStateUnauthenticated();
    }
  }

  /// Social login with external provider
  /// 
  /// [provider] - Social provider (google, apple, etc.)
  /// [socialToken] - Token from social provider
  /// [email] - Optional email from social provider
  /// 
  /// Returns true on success, false on failure
  Future<bool> socialLogin({
    required String provider,
    required String socialToken,
    String? email,
  }) async {
    state = AuthStateLoading('Signing in with ${provider.toUpperCase()}...');

    try {
      if (kDebugMode) {
        print(
            '🔐 AUTH: Social login attempt - provider: $provider, email: $email');
        print('🔐 AUTH: Social token length: ${socialToken.length}');
      }

      final authResponse = await _authService.socialLogin(
        provider: provider,
        socialToken: socialToken,
        email: email,
      );

      // Get user data from response
      User? user = authResponse.user;
      if (user == null) {
        if (kDebugMode) {
          print('🔐 AUTH: No user in auth response, fetching from server...');
        }
        user = await _authService.getCurrentUser();
      } else {
        if (kDebugMode) {
          print('🔐 AUTH: Using user from auth response: ${user.email}');
        }
      }

      state = AuthStateAuthenticated(user);
      return true;
    } on AuthException catch (e) {
      state = AuthStateError(e.message, e);
      return false;
    } catch (e) {
      state = AuthStateError('Social login failed: $e',
          e is Exception ? e : Exception(e.toString()));
      return false;
    }
  }

  /// Google Sign-In
  /// 
  /// Handles Google OAuth flow and authenticates with backend
  /// 
  /// Returns true on success, false on failure
  Future<bool> signInWithGoogle() async {
    try {
      final result = await SocialLoginService.signInWithGoogle();

      return await socialLogin(
        provider: result.provider,
        socialToken: result.accessToken,
        email: result.email,
      );
    } on SocialLoginException catch (e) {
      state = AuthStateError(e.message, e);
      return false;
    } catch (e) {
      state = AuthStateError('Google Sign-In failed: $e',
          e is Exception ? e : Exception(e.toString()));
      return false;
    }
  }

  /// Apple Sign-In
  /// 
  /// Handles Apple OAuth flow and authenticates with backend
  /// 
  /// Returns true on success, false on failure
  Future<bool> signInWithApple() async {
    try {
      final result = await SocialLoginService.signInWithApple();

      // For Apple Sign-In, use userIdentifier as the consistent token
      // This ensures the same user gets the same UID across sign-ins
      return await socialLogin(
        provider: result.provider,
        socialToken: result.uid ?? result.accessToken,
        email: result.email,
      );
    } on SocialLoginException catch (e) {
      state = AuthStateError(e.message, e);
      return false;
    } catch (e) {
      state = AuthStateError('Apple Sign-In failed: $e',
          e is Exception ? e : Exception(e.toString()));
      return false;
    }
  }

  /// Refreshes current user data from server
  /// 
  /// Updates the user data while maintaining authenticated state.
  Future<void> refreshUser() async {
    if (state is! AuthStateAuthenticated) return;

    try {
      final user = await _authService.getCurrentUser();
      state = AuthStateAuthenticated(user);
    } catch (e) {
      // If refresh fails, don't change auth state
      print('Failed to refresh user: $e');
    }
  }

  /// Changes user password
  /// 
  /// [currentPassword] - Current password for verification
  /// [newPassword] - New password to set
  /// 
  /// Returns true on success, false on failure
  Future<bool> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    if (state is! AuthStateAuthenticated) return false;

    try {
      await _authService.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
      return true;
    } on AuthException catch (e) {
      state = AuthStateError(e.message, e);
      return false;
    } catch (e) {
      state = AuthStateError('Password change failed: $e',
          e is Exception ? e : Exception(e.toString()));
      return false;
    }
  }

  /// Requests password reset email
  /// 
  /// [email] - Email address to send reset link to
  /// 
  /// Returns true on success, false on failure
  Future<bool> requestPasswordReset(String email) async {
    state = const AuthStateLoading('Sending reset email...');

    try {
      await _authService.requestPasswordReset(email);
      state = const AuthStateUnauthenticated();
      return true;
    } on AuthException catch (e) {
      state = AuthStateError(e.message, e);
      return false;
    } catch (e) {
      state = AuthStateError('Password reset failed: $e',
          e is Exception ? e : Exception(e.toString()));
      return false;
    }
  }

  /// Clears any error state
  /// 
  /// Useful for dismissing error messages in the UI.
  void clearError() {
    if (state is AuthStateError) {
      state = const AuthStateUnauthenticated();
    }
  }

  /// Gets the current user if authenticated
  /// 
  /// Returns the [User] object if authenticated, null otherwise.
  User? get currentUser {
    final currentState = state;
    return currentState is AuthStateAuthenticated ? currentState.user : null;
  }

  /// Checks if user is currently authenticated
  bool get isAuthenticated => state is AuthStateAuthenticated;

  /// Checks if an auth operation is in progress
  bool get isLoading => state is AuthStateLoading;

  /// Gets current error message if in error state
  String? get errorMessage {
    final currentState = state;
    return currentState is AuthStateError ? currentState.message : null;
  }
}

/// Provider for AuthService instance
/// 
/// Creates and provides a singleton instance of AuthService.
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

/// Main authentication provider
/// 
/// Provides global authentication state management.
/// Use this provider to access and modify authentication state throughout the app.
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.read(authServiceProvider);
  return AuthNotifier(authService);
});

/// Convenience provider for checking if user is authenticated
/// 
/// Returns true if user is authenticated, false otherwise.
final isAuthenticatedProvider = Provider<bool>((ref) {
  final authState = ref.watch(authProvider);
  return authState is AuthStateAuthenticated;
});

/// Convenience provider for getting current user
/// 
/// Returns the current [User] if authenticated, null otherwise.
final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authProvider);
  return authState is AuthStateAuthenticated ? authState.user : null;
});

/// Provider for checking if auth operation is in progress
/// 
/// Returns true if any auth operation is loading, false otherwise.
final authLoadingProvider = Provider<bool>((ref) {
  final authState = ref.watch(authProvider);
  return authState is AuthStateLoading;
});

/// Provider for getting current auth error message
/// 
/// Returns error message if in error state, null otherwise.
final authErrorProvider = Provider<String?>((ref) {
  final authState = ref.watch(authProvider);
  return authState is AuthStateError ? authState.message : null;
});