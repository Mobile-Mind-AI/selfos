// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AuthResponse _$AuthResponseFromJson(Map<String, dynamic> json) => AuthResponse(
  accessToken: json['access_token'] as String,
  tokenType: json['token_type'] as String? ?? 'bearer',
  refreshToken: json['refreshToken'] as String?,
  expiresIn: (json['expiresIn'] as num?)?.toInt(),
  user: json['user'] == null
      ? null
      : User.fromJson(json['user'] as Map<String, dynamic>),
);

Map<String, dynamic> _$AuthResponseToJson(AuthResponse instance) =>
    <String, dynamic>{
      'access_token': instance.accessToken,
      'token_type': instance.tokenType,
      'refreshToken': instance.refreshToken,
      'expiresIn': instance.expiresIn,
      'user': instance.user,
    };

RegisterResponse _$RegisterResponseFromJson(Map<String, dynamic> json) =>
    RegisterResponse(
      uid: json['uid'] as String,
      email: json['email'] as String,
      displayName: json['displayName'] as String?,
      message: json['message'] as String?,
    );

Map<String, dynamic> _$RegisterResponseToJson(RegisterResponse instance) =>
    <String, dynamic>{
      'uid': instance.uid,
      'email': instance.email,
      'displayName': instance.displayName,
      'message': instance.message,
    };

ApiError _$ApiErrorFromJson(Map<String, dynamic> json) => ApiError(
  message: json['message'] as String,
  code: json['code'] as String?,
  details: json['details'] as Map<String, dynamic>?,
  statusCode: (json['statusCode'] as num?)?.toInt(),
);

Map<String, dynamic> _$ApiErrorToJson(ApiError instance) => <String, dynamic>{
  'message': instance.message,
  'code': instance.code,
  'details': instance.details,
  'statusCode': instance.statusCode,
};
