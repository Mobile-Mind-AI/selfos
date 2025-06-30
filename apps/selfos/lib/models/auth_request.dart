import 'package:json_annotation/json_annotation.dart';

part 'auth_request.g.dart';

/// Login request model for authentication
/// 
/// Used to send login credentials to the /auth/login endpoint.
/// Supports both email/password and social login flows.
@JsonSerializable()
class LoginRequest {
  /// Username or email address
  final String username;
  
  /// Password for email/password login
  final String password;
  
  /// Optional: Login provider for social login (google, apple, etc.)
  final String? provider;
  
  /// Optional: Social login token/credential
  @JsonKey(name: 'social_token')
  final String? socialToken;

  /// Optional: Email for social login
  final String? email;

  const LoginRequest({
    required this.username,
    required this.password,
    this.provider,
    this.socialToken,
    this.email,
  });

  /// Creates a LoginRequest for email/password authentication
  factory LoginRequest.emailPassword({
    required String email,
    required String password,
  }) {
    return LoginRequest(
      username: email,
      password: password,
      provider: "email",
    );
  }

  /// Creates a LoginRequest for social authentication
  factory LoginRequest.social({
    required String provider,
    required String socialToken,
    String? email,
  }) {
    return LoginRequest(
      username: email ?? '',
      password: '',
      provider: provider,
      socialToken: socialToken,
      email: email,
    );
  }

  /// Creates a LoginRequest from JSON
  factory LoginRequest.fromJson(Map<String, dynamic> json) => 
      _$LoginRequestFromJson(json);

  /// Converts LoginRequest to JSON
  Map<String, dynamic> toJson() => _$LoginRequestToJson(this);

  @override
  String toString() {
    return 'LoginRequest(username: $username, provider: $provider)';
  }
}

/// Registration request model for creating new accounts
/// 
/// Used to send registration data to the /auth/register endpoint.
/// Supports both email/password and social registration flows.
@JsonSerializable()
class RegisterRequest {
  /// Username or email address
  final String username;
  
  /// Password for the new account
  final String password;
  
  /// Optional: Confirm password field
  final String? confirmPassword;
  
  /// Optional: Display name
  final String? displayName;
  
  /// Optional: Registration provider for social signup
  final String? provider;
  
  /// Optional: Social login token/credential
  @JsonKey(name: 'social_token')
  final String? socialToken;
  
  /// Optional: Referral code
  final String? referralCode;

  const RegisterRequest({
    required this.username,
    required this.password,
    this.confirmPassword,
    this.displayName,
    this.provider,
    this.socialToken,
    this.referralCode,
  });

  /// Creates a RegisterRequest for email/password registration
  factory RegisterRequest.emailPassword({
    required String email,
    required String password,
    required String confirmPassword,
    String? displayName,
    String? referralCode,
  }) {
    return RegisterRequest(
      username: email,
      password: password,
      confirmPassword: confirmPassword,
      displayName: displayName,
      provider: "email",
      referralCode: referralCode,
    );
  }

  /// Creates a RegisterRequest for social registration
  factory RegisterRequest.social({
    required String provider,
    required String socialToken,
    String? email,
    String? displayName,
    String? referralCode,
  }) {
    return RegisterRequest(
      username: email ?? '',
      password: '',
      provider: provider,
      socialToken: socialToken,
      displayName: displayName,
      referralCode: referralCode,
    );
  }

  /// Creates a RegisterRequest from JSON
  factory RegisterRequest.fromJson(Map<String, dynamic> json) => 
      _$RegisterRequestFromJson(json);

  /// Converts RegisterRequest to JSON
  Map<String, dynamic> toJson() => _$RegisterRequestToJson(this);

  /// Validates the registration request
  List<String> validate() {
    final errors = <String>[];
    
    if (username.isEmpty) {
      errors.add('Username/email is required');
    }
    
    if (provider == null) {
      // Email/password validation
      if (password.isEmpty) {
        errors.add('Password is required');
      } else if (password.length < 8) {
        errors.add('Password must be at least 8 characters');
      }
      
      if (confirmPassword != null && password != confirmPassword) {
        errors.add('Passwords do not match');
      }
      
      // Basic email validation
      if (!username.contains('@') || !username.contains('.')) {
        errors.add('Please enter a valid email address');
      }
    }
    
    return errors;
  }

  @override
  String toString() {
    return 'RegisterRequest(username: $username, displayName: $displayName, provider: $provider)';
  }
}