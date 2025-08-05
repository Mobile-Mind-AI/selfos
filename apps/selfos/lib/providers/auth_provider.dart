import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_service.dart';
import '../models/user.dart';
import '../models/auth_request.dart';

/// Provider for the current user data
final currentUserProvider = StateProvider<User?>((ref) {
  return null;
});

/// Provider for authentication state
final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});

/// Authentication state
class AuthState {
  final bool isLoggedIn;
  final bool isLoading;
  final String? error;
  final User? user;

  const AuthState({
    this.isLoggedIn = false,
    this.isLoading = false,
    this.error,
    this.user,
  });

  AuthState copyWith({
    bool? isLoggedIn,
    bool? isLoading,
    String? error,
    User? user,
  }) {
    return AuthState(
      isLoggedIn: isLoggedIn ?? this.isLoggedIn,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      user: user ?? this.user,
    );
  }
}

/// Authentication state notifier
class AuthNotifier extends StateNotifier<AuthState> {
  final Ref ref;
  late final AuthService _authService;

  AuthNotifier(this.ref) : super(const AuthState()) {
    _authService = AuthService();
    _checkInitialAuthState();
  }

  Future<void> _checkInitialAuthState() async {
    state = state.copyWith(isLoading: true);
    
    try {
      final isAuthenticated = await _authService.isAuthenticated();
      if (isAuthenticated) {
        final user = await _authService.getStoredUser();
        state = state.copyWith(
          isLoggedIn: true,
          isLoading: false,
          user: user,
        );
        // Update the current user provider
        ref.read(currentUserProvider.notifier).state = user;
      } else {
        state = state.copyWith(isLoggedIn: false, isLoading: false);
      }
    } catch (e) {
      state = state.copyWith(
        isLoggedIn: false,
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<bool> signIn(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final loginRequest = LoginRequest.emailPassword(email: email, password: password);
      final authResponse = await _authService.login(loginRequest);
      final user = await _authService.getCurrentUser();
      
      state = state.copyWith(
        isLoggedIn: true,
        isLoading: false,
        user: user,
      );
      ref.read(currentUserProvider.notifier).state = user;
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoggedIn: false,
        isLoading: false,
        error: e.toString(),
      );
      return false;
    }
  }

  Future<bool> signUp(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final registerRequest = RegisterRequest.emailPassword(email: email, password: password, confirmPassword: password);
      final registerResponse = await _authService.register(registerRequest);
      
      // After registration, user needs to login
      final loginRequest = LoginRequest.emailPassword(email: email, password: password);
      final authResponse = await _authService.login(loginRequest);
      final user = await _authService.getCurrentUser();
      
      state = state.copyWith(
        isLoggedIn: true,
        isLoading: false,
        user: user,
      );
      ref.read(currentUserProvider.notifier).state = user;
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoggedIn: false,
        isLoading: false,
        error: e.toString(),
      );
      return false;
    }
  }

  Future<void> signOut() async {
    state = state.copyWith(isLoading: true);
    
    try {
      await _authService.logout();
      state = const AuthState(isLoggedIn: false, isLoading: false);
      ref.read(currentUserProvider.notifier).state = null;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }
}