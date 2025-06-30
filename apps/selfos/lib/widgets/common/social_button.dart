import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';
import '../../services/social_login_service.dart';

/// Social login provider enumeration
enum SocialProvider {
  google,
  apple,
}

extension SocialProviderExtension on SocialProvider {
  /// Display name for the provider
  String get displayName {
    switch (this) {
      case SocialProvider.google:
        return 'Google';
      case SocialProvider.apple:
        return 'Apple';
    }
  }

  /// Icon for the provider
  IconData get icon {
    switch (this) {
      case SocialProvider.google:
        return Icons.g_mobiledata; // Google icon
      case SocialProvider.apple:
        return Icons.apple; // Apple icon
    }
  }

  /// Primary color for the provider
  Color get color {
    switch (this) {
      case SocialProvider.google:
        return const Color(0xFF4285F4); // Google blue
      case SocialProvider.apple:
        return Colors.black; // Apple black
    }
  }

  /// Text color for the provider button
  Color get textColor {
    switch (this) {
      case SocialProvider.google:
        return Colors.white;
      case SocialProvider.apple:
        return Colors.white;
    }
  }

  /// Whether this provider is available on the current platform
  bool get isAvailable {
    switch (this) {
      case SocialProvider.google:
        return true; // Available on all platforms
      case SocialProvider.apple:
        return Platform.isIOS || Platform.isMacOS; // Available on Apple platforms
    }
  }
}

/// Social login button widget
/// 
/// A reusable button component for social authentication providers.
/// Supports Google and Apple Sign-In with platform-specific styling.
class SocialButton extends StatelessWidget {
  final SocialProvider provider;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isCompact;

  const SocialButton({
    super.key,
    required this.provider,
    this.onPressed,
    this.isLoading = false,
    this.isCompact = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    // Don't show button if provider is not available on this platform
    if (!provider.isAvailable) {
      return const SizedBox.shrink();
    }

    return Material(
      elevation: 1,
      borderRadius: BorderRadius.circular(12),
      color: provider.color,
      child: InkWell(
        onTap: isLoading ? null : onPressed,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          height: isCompact ? 44 : 52,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: theme.colorScheme.outline.withOpacity(0.2),
            ),
          ),
          child: isLoading
              ? _buildLoadingState()
              : _buildNormalState(),
        ),
      ),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          valueColor: AlwaysStoppedAnimation<Color>(provider.textColor),
        ),
      ),
    );
  }

  Widget _buildNormalState() {
    if (isCompact) {
      return Center(
        child: Icon(
          provider.icon,
          color: provider.textColor,
          size: 24,
        ),
      );
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          provider.icon,
          color: provider.textColor,
          size: 20,
        ),
        const SizedBox(width: 12),
        Text(
          provider.displayName,
          style: TextStyle(
            color: provider.textColor,
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

/// Social login section widget
/// 
/// A complete social login section with divider and multiple provider buttons.
/// Automatically filters out unavailable providers for the current platform.
class SocialLoginSection extends StatefulWidget {
  final List<SocialProvider> providers;
  final Function(SocialProvider) onProviderTap;
  final bool isLoading;
  final String dividerText;

  const SocialLoginSection({
    super.key,
    this.providers = const [SocialProvider.google, SocialProvider.apple],
    required this.onProviderTap,
    this.isLoading = false,
    this.dividerText = 'or continue with',
  });

  @override
  State<SocialLoginSection> createState() => _SocialLoginSectionState();
}

class _SocialLoginSectionState extends State<SocialLoginSection> {
  List<SocialProvider> _availableProviders = [];
  bool _isCheckingAvailability = true;

  @override
  void initState() {
    super.initState();
    _checkProviderAvailability();
  }

  Future<void> _checkProviderAvailability() async {
    final available = <SocialProvider>[];
    
    for (final provider in widget.providers) {
      switch (provider) {
        case SocialProvider.google:
          // Google is always available
          available.add(provider);
          break;
        case SocialProvider.apple:
          // Check Apple Sign-In availability dynamically
          try {
            final isAvailable = await SocialLoginService.isAppleSignInAvailable();
            if (isAvailable) {
              available.add(provider);
            }
          } catch (e) {
            // Apple Sign-In not available, skip it
            if (kDebugMode) {
              print('Apple Sign-In not available: $e');
            }
          }
          break;
      }
    }
    
    if (mounted) {
      setState(() {
        _availableProviders = available;
        _isCheckingAvailability = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    if (_isCheckingAvailability) {
      return const SizedBox(
        height: 60,
        child: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }
    
    final availableProviders = _availableProviders;
    
    if (availableProviders.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      children: [
        // Divider with text
        Row(
          children: [
            const Expanded(child: Divider()),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                widget.dividerText,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ),
            const Expanded(child: Divider()),
          ],
        ),
        
        const SizedBox(height: 24),
        
        // Provider buttons
        _buildProviderButtons(availableProviders),
      ],
    );
  }

  Widget _buildProviderButtons(List<SocialProvider> providers) {
    if (providers.length == 1) {
      // Single button - full width
      return SocialButton(
        provider: providers.first,
        onPressed: () => widget.onProviderTap(providers.first),
        isLoading: widget.isLoading,
      );
    } else if (providers.length == 2) {
      // Two buttons - side by side
      return Row(
        children: [
          Expanded(
            child: SocialButton(
              provider: providers[0],
              onPressed: () => widget.onProviderTap(providers[0]),
              isLoading: widget.isLoading,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: SocialButton(
              provider: providers[1],
              onPressed: () => widget.onProviderTap(providers[1]),
              isLoading: widget.isLoading,
            ),
          ),
        ],
      );
    } else {
      // More than two - vertical list
      return Column(
        children: providers.map((provider) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: SocialButton(
            provider: provider,
            onPressed: () => widget.onProviderTap(provider),
            isLoading: widget.isLoading,
          ),
        )).toList(),
      );
    }
  }
}