import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'dart:io';

/// Service for handling social login providers (Google, Apple)
/// 
/// This service provides a unified interface for different social login providers.
/// It handles the OAuth flow for each provider and returns standardized user data.
class SocialLoginService {
  /// Google Sign-In instance
  static final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );

  /// Sign in with Google
  /// 
  /// Returns a map containing user data and access token
  /// Throws [SocialLoginException] on failure
  static Future<SocialLoginResult> signInWithGoogle() async {
    try {
      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: Starting Google Sign-In...');
      }

      // Trigger the authentication flow
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      
      if (googleUser == null) {
        throw SocialLoginException('Google Sign-In was cancelled by user');
      }

      // Obtain the auth details from the request
      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;

      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: GoogleAuth - accessToken: ${googleAuth.accessToken != null ? "present" : "null"}');
        print('🔐 SOCIAL_LOGIN: GoogleAuth - idToken: ${googleAuth.idToken != null ? "present" : "null"}');
      }

      // For Google Sign In, we should use idToken as the primary token for backend verification
      final token = googleAuth.idToken ?? googleAuth.accessToken;
      
      if (token == null) {
        throw SocialLoginException('Failed to get Google authentication tokens');
      }

      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: Google Sign-In successful for ${googleUser.email}');
        print('🔐 SOCIAL_LOGIN: Using token type: ${googleAuth.idToken != null ? "idToken" : "accessToken"}');
      }

      return SocialLoginResult(
        provider: 'google',
        accessToken: token,
        idToken: googleAuth.idToken,
        email: googleUser.email,
        displayName: googleUser.displayName,
        photoUrl: googleUser.photoUrl,
        uid: googleUser.id,
      );
    } catch (e) {
      if (kDebugMode) {
        print('❌ SOCIAL_LOGIN: Google Sign-In failed: $e');
      }
      
      if (e is SocialLoginException) {
        rethrow;
      }
      throw SocialLoginException('Google Sign-In failed: $e');
    }
  }

  /// Sign in with Apple
  /// 
  /// Returns a map containing user data and authorization code
  /// Throws [SocialLoginException] on failure
  static Future<SocialLoginResult> signInWithApple() async {
    try {
      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: Starting Apple Sign-In...');
      }

      // Check if Apple Sign-In is available
      if (!Platform.isIOS && !Platform.isMacOS) {
        throw SocialLoginException('Apple Sign-In is only available on iOS and macOS');
      }

      // Check if Apple Sign-In is available on the platform
      try {
        final isAvailable = await SignInWithApple.isAvailable();
        if (!isAvailable) {
          if (Platform.isMacOS) {
            throw SocialLoginException('Apple Sign-In requires proper configuration on macOS. Please use Google Sign-In instead.');
          } else {
            throw SocialLoginException('Apple Sign-In is not available on this device.');
          }
        }
      } catch (e) {
        if (Platform.isMacOS) {
          throw SocialLoginException('Apple Sign-In is not configured for this macOS app. Please use Google Sign-In instead.');
        } else {
          throw SocialLoginException('Apple Sign-In setup error: ${e.toString()}');
        }
      }

      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: Requesting Apple ID credential...');
      }

      // Try with minimal scopes first to isolate the issue
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
        ],
      ).catchError((error) {
        if (kDebugMode) {
          print('❌ SOCIAL_LOGIN: Apple credential request failed: $error');
          print('❌ SOCIAL_LOGIN: Error type: ${error.runtimeType}');
        }
        throw error;
      });

      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: Apple credential received');
        print('🔐 SOCIAL_LOGIN: - userIdentifier: ${credential.userIdentifier}');
        print('🔐 SOCIAL_LOGIN: - email: ${credential.email ?? "null"}');
        print('🔐 SOCIAL_LOGIN: - givenName: ${credential.givenName ?? "null"}');
        print('🔐 SOCIAL_LOGIN: - familyName: ${credential.familyName ?? "null"}');
        print('🔐 SOCIAL_LOGIN: - authorizationCode length: ${credential.authorizationCode.length}');
        print('🔐 SOCIAL_LOGIN: - identityToken: ${credential.identityToken != null ? "present" : "null"}');
      }

      if (credential.authorizationCode.isEmpty) {
        throw SocialLoginException('Failed to get Apple authorization code');
      }

      // Construct display name from given name and family name
      String? displayName;
      if (credential.givenName != null || credential.familyName != null) {
        displayName = '${credential.givenName ?? ''} ${credential.familyName ?? ''}'.trim();
        if (displayName.isEmpty) displayName = null;
      }

      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: Apple Sign-In successful for ${credential.email ?? 'user'}');
      }

      return SocialLoginResult(
        provider: 'apple',
        accessToken: credential.authorizationCode,
        idToken: credential.identityToken,
        email: credential.email,
        displayName: displayName,
        uid: credential.userIdentifier,
      );
    } catch (e) {
      if (kDebugMode) {
        print('❌ SOCIAL_LOGIN: Apple Sign-In failed: $e');
      }
      
      if (e is SocialLoginException) {
        rethrow;
      }
      throw SocialLoginException('Apple Sign-In failed: $e');
    }
  }

  /// Sign out from Google
  static Future<void> signOutGoogle() async {
    try {
      await _googleSignIn.signOut();
      if (kDebugMode) {
        print('🔐 SOCIAL_LOGIN: Google Sign-Out successful');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ SOCIAL_LOGIN: Google Sign-Out failed: $e');
      }
      // Don't throw error for sign out failures
    }
  }

  /// Check if Apple Sign-In is available
  static Future<bool> isAppleSignInAvailable() async {
    try {
      if (!Platform.isIOS && !Platform.isMacOS) {
        return false;
      }
      
      // On macOS, Apple Sign-In requires specific entitlements and signing
      if (Platform.isMacOS) {
        try {
          final isAvailable = await SignInWithApple.isAvailable();
          if (kDebugMode) {
            print('🔐 SOCIAL_LOGIN: Apple Sign-In availability on macOS: $isAvailable');
          }
          return isAvailable;
        } catch (e) {
          if (kDebugMode) {
            print('❌ SOCIAL_LOGIN: Apple Sign-In not properly configured on macOS: $e');
          }
          return false;
        }
      }
      
      // On iOS, check availability
      return await SignInWithApple.isAvailable();
    } catch (e) {
      if (kDebugMode) {
        print('❌ SOCIAL_LOGIN: Apple Sign-In availability check failed: $e');
      }
      return false;
    }
  }

  /// Check if user is signed in with Google
  static Future<bool> isSignedInWithGoogle() async {
    try {
      return await _googleSignIn.isSignedIn();
    } catch (e) {
      return false;
    }
  }
}

/// Result of a social login attempt
class SocialLoginResult {
  final String provider;
  final String accessToken;
  final String? idToken;
  final String? email;
  final String? displayName;
  final String? photoUrl;
  final String? uid;

  const SocialLoginResult({
    required this.provider,
    required this.accessToken,
    this.idToken,
    this.email,
    this.displayName,
    this.photoUrl,
    this.uid,
  });

  @override
  String toString() {
    return 'SocialLoginResult(provider: $provider, email: $email, displayName: $displayName)';
  }
}

/// Exception thrown for social login errors
class SocialLoginException implements Exception {
  final String message;
  final String? code;
  
  const SocialLoginException(this.message, {this.code});
  
  @override
  String toString() => message;
}