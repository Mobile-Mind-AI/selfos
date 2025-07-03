// widgets/assistant_hero_section.dart
import 'package:flutter/material.dart';
import 'dart:typed_data';
import 'dart:math' as math;
import '../common/assistant_avatar.dart';

class AssistantHeroSection extends StatefulWidget {
  final Map<String, dynamic> selectedAvatarData;
  final Map<String, Uint8List> globalCustomAvatars;
  final String assistantName;

  const AssistantHeroSection({
    super.key,
    required this.selectedAvatarData,
    required this.globalCustomAvatars,
    required this.assistantName,
  });

  @override
  State<AssistantHeroSection> createState() => _AssistantHeroSectionState();
}

class _AssistantHeroSectionState extends State<AssistantHeroSection>
    with TickerProviderStateMixin {

  late AnimationController _orbitController;
  late AnimationController _pulseController;
  late Animation<double> _orbitAnimation;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();

    _orbitController = AnimationController(
      duration: const Duration(seconds: 8),
      vsync: this,
    );

    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );

    _orbitAnimation = Tween<double>(
      begin: 0.0,
      end: 2 * math.pi,
    ).animate(CurvedAnimation(
      parent: _orbitController,
      curve: Curves.linear,
    ));

    _pulseAnimation = Tween<double>(
      begin: 0.95,
      end: 1.05,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));

    // Start animations
    _orbitController.repeat();
    _pulseController.repeat(reverse: true);
  }

  @override
  void dispose() {
    _orbitController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      children: [
        // Centered hero section with selected avatar and orbiting dots
        Center(
          child: AnimatedBuilder(
            animation: Listenable.merge([_orbitAnimation, _pulseAnimation]),
            builder: (context, child) {
              return Container(
                width: 160,
                height: 160,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // Main selected avatar with pulse animation (no background square)
                    Transform.scale(
                      scale: _pulseAnimation.value,
                      child: AssistantAvatar(
                        avatarId: widget.selectedAvatarData['id'],
                        imagePath: widget.selectedAvatarData['isCustom'] == true
                            ? null
                            : widget.selectedAvatarData['imagePath'],
                        imageData: widget.selectedAvatarData['isCustom'] == true
                            ? widget.selectedAvatarData['imageData']
                            : widget.globalCustomAvatars[widget.selectedAvatarData['id']],
                        icon: widget.selectedAvatarData['icon'],
                        gradientColors: widget.selectedAvatarData['colors'] != null
                            ? List<Color>.from(widget.selectedAvatarData['colors'])
                            : null,
                        size: 120.0,
                        isSelected: false,
                        isBackendStored: widget.selectedAvatarData['isBackendStored'] == true,
                      ),
                    ),
                    // Orbiting colored dots
                    ..._buildOrbitingDots(theme),
                  ],
                ),
              );
            },
          ),
        ),

        const SizedBox(height: 24),

        Text(
          widget.assistantName.isNotEmpty ? widget.assistantName : 'Your Assistant',
          style: theme.textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.onSurface,
          ),
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 12),

        Text(
          'Give your AI companion a name and choose how they\'ll appear. '
          'They\'ll be with you throughout your journey, helping you achieve your goals.',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  List<Widget> _buildOrbitingDots(ThemeData theme) {
    const dotColors = [
      Colors.orange,
      Colors.blue,
      Colors.green,
      Colors.purple,
      Colors.red,
      Colors.teal,
    ];

    return List.generate(6, (index) {
      final baseAngle = (index * 60) * (math.pi / 180);
      final currentAngle = baseAngle + _orbitAnimation.value;
      final orbitRadius = 57.0; // Fixed radius for 160px container

      return Transform.translate(
        offset: Offset(
          orbitRadius * math.cos(currentAngle),
          orbitRadius * math.sin(currentAngle),
        ),
        child: Transform.scale(
          scale: 0.8 + 0.2 * _pulseAnimation.value,
          child: Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: dotColors[index].withOpacity(0.8),
              borderRadius: BorderRadius.circular(4),
              boxShadow: [
                BoxShadow(
                  color: dotColors[index].withOpacity(0.3),
                  blurRadius: 4,
                  spreadRadius: 1,
                ),
              ],
            ),
          ),
        ),
      );
    });
  }
}