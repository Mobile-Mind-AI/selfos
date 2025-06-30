import 'package:json_annotation/json_annotation.dart';
import 'user.dart';

part 'auth_response.g.dart';

/// Authentication response from login/register endpoints
/// 
/// Contains the JWT access token, user information, and optional refresh token.
@JsonSerializable()
class AuthResponse {
  /// JWT access token for API authentication
  @JsonKey(name: 'access_token')
  final String accessToken;
  
  /// Token type (usually "bearer")
  @JsonKey(name: 'token_type')
  final String tokenType;
  
  /// Optional refresh token for token renewal
  final String? refreshToken;
  
  /// Token expiration time in seconds
  final int? expiresIn;
  
  /// Authenticated user information
  final User? user;

  const AuthResponse({
    required this.accessToken,
    this.tokenType = 'bearer',
    this.refreshToken,
    this.expiresIn,
    this.user,
  });

  /// Creates an AuthResponse from JSON
  factory AuthResponse.fromJson(Map<String, dynamic> json) => 
      _$AuthResponseFromJson(json);

  /// Converts AuthResponse to JSON
  Map<String, dynamic> toJson() => _$AuthResponseToJson(this);

  /// Gets the full authorization header value
  String get authorizationHeader => '$tokenType $accessToken';

  /// Checks if the token is likely expired (if expiresIn is available)
  bool get isExpired {
    if (expiresIn == null) return false;
    // This is a simple check - in practice you'd want to store the issued time
    // and calculate based on that
    return false; // TODO: Implement proper expiration checking
  }

  @override
  String toString() {
    return 'AuthResponse(tokenType: $tokenType, user: ${user?.email}, expiresIn: $expiresIn)';
  }
}

/// Registration response from the /auth/register endpoint
/// 
/// Contains the newly created user information and success status.
@JsonSerializable()
class RegisterResponse {
  /// Unique user identifier
  final String uid;
  
  /// User's email address
  final String email;
  
  /// Optional display name
  final String? displayName;
  
  /// Registration success message
  final String? message;

  const RegisterResponse({
    required this.uid,
    required this.email,
    this.displayName,
    this.message,
  });

  /// Creates a RegisterResponse from JSON
  factory RegisterResponse.fromJson(Map<String, dynamic> json) => 
      _$RegisterResponseFromJson(json);

  /// Converts RegisterResponse to JSON
  Map<String, dynamic> toJson() => _$RegisterResponseToJson(this);

  @override
  String toString() {
    return 'RegisterResponse(uid: $uid, email: $email, displayName: $displayName)';
  }
}

/// API error response model
/// 
/// Represents error responses from the authentication API.
@JsonSerializable()
class ApiError {
  /// Error message
  final String message;
  
  /// Error code or type
  final String? code;
  
  /// Detailed error information
  final Map<String, dynamic>? details;
  
  /// HTTP status code
  final int? statusCode;

  const ApiError({
    required this.message,
    this.code,
    this.details,
    this.statusCode,
  });

  /// Creates an ApiError from JSON
  factory ApiError.fromJson(Map<String, dynamic> json) => 
      _$ApiErrorFromJson(json);

  /// Converts ApiError to JSON
  Map<String, dynamic> toJson() => _$ApiErrorToJson(this);

  /// Creates an ApiError from an exception
  factory ApiError.fromException(Exception exception) {
    return ApiError(
      message: exception.toString(),
      code: 'client_error',
    );
  }

  /// Creates a network error
  factory ApiError.networkError() {
    return const ApiError(
      message: 'Network error. Please check your connection.',
      code: 'network_error',
    );
  }

  /// Creates a validation error
  factory ApiError.validation(List<String> errors) {
    return ApiError(
      message: errors.join(', '),
      code: 'validation_error',
      details: {'errors': errors},
    );
  }

  @override
  String toString() {
    return 'ApiError(message: $message, code: $code, statusCode: $statusCode)';
  }
}