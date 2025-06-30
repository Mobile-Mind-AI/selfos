// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LoginRequest _$LoginRequestFromJson(Map<String, dynamic> json) => LoginRequest(
  username: json['username'] as String,
  password: json['password'] as String,
  provider: json['provider'] as String?,
  socialToken: json['social_token'] as String?,
  email: json['email'] as String?,
);

Map<String, dynamic> _$LoginRequestToJson(LoginRequest instance) =>
    <String, dynamic>{
      'username': instance.username,
      'password': instance.password,
      'provider': instance.provider,
      'social_token': instance.socialToken,
      'email': instance.email,
    };

RegisterRequest _$RegisterRequestFromJson(Map<String, dynamic> json) =>
    RegisterRequest(
      username: json['username'] as String,
      password: json['password'] as String,
      confirmPassword: json['confirmPassword'] as String?,
      displayName: json['displayName'] as String?,
      provider: json['provider'] as String?,
      socialToken: json['social_token'] as String?,
      referralCode: json['referralCode'] as String?,
    );

Map<String, dynamic> _$RegisterRequestToJson(RegisterRequest instance) =>
    <String, dynamic>{
      'username': instance.username,
      'password': instance.password,
      'confirmPassword': instance.confirmPassword,
      'displayName': instance.displayName,
      'provider': instance.provider,
      'social_token': instance.socialToken,
      'referralCode': instance.referralCode,
    };
