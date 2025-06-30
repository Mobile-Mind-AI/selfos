import 'package:json_annotation/json_annotation.dart';

part 'user.g.dart';

/// User model representing a SelfOS user
/// 
/// This model represents the authenticated user data returned from the API.
/// It includes basic user information and authentication state.
@JsonSerializable()
class User {
  /// Unique user identifier from Firebase Auth
  final String uid;
  
  /// User's email address
  final String email;
  
  /// Optional display name
  final String? displayName;
  
  /// Optional profile picture URL
  final String? photoUrl;
  
  /// User roles/permissions
  final List<String> roles;
  
  /// Whether the user's email is verified
  final bool emailVerified;
  
  /// Account creation timestamp
  final DateTime? createdAt;
  
  /// Last login timestamp
  final DateTime? lastLoginAt;

  const User({
    required this.uid,
    required this.email,
    this.displayName,
    this.photoUrl,
    this.roles = const ['user'],
    this.emailVerified = false,
    this.createdAt,
    this.lastLoginAt,
  });

  /// Creates a User from JSON
  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);

  /// Converts User to JSON
  Map<String, dynamic> toJson() => _$UserToJson(this);

  /// Creates a copy of this User with updated fields
  User copyWith({
    String? uid,
    String? email,
    String? displayName,
    String? photoUrl,
    List<String>? roles,
    bool? emailVerified,
    DateTime? createdAt,
    DateTime? lastLoginAt,
  }) {
    return User(
      uid: uid ?? this.uid,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      photoUrl: photoUrl ?? this.photoUrl,
      roles: roles ?? this.roles,
      emailVerified: emailVerified ?? this.emailVerified,
      createdAt: createdAt ?? this.createdAt,
      lastLoginAt: lastLoginAt ?? this.lastLoginAt,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is User && other.uid == uid && other.email == email;
  }

  @override
  int get hashCode => uid.hashCode ^ email.hashCode;

  @override
  String toString() {
    return 'User(uid: $uid, email: $email, displayName: $displayName)';
  }
}