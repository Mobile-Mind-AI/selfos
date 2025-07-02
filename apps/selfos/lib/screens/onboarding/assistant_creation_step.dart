import 'package:flutter/material.dart';

/// Assistant creation step where users name their assistant and choose an avatar.
/// 
/// This is step 2 in the onboarding flow: "Meet Your Assistant"
class AssistantCreationStep extends StatefulWidget {
  final Function(Map<String, dynamic>) onNext;
  final VoidCallback onPrevious;

  const AssistantCreationStep({
    super.key,
    required this.onNext,
    required this.onPrevious,
  });

  @override
  State<AssistantCreationStep> createState() => _AssistantCreationStepState();
}

class _AssistantCreationStepState extends State<AssistantCreationStep>
    with TickerProviderStateMixin {
  
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  
  final TextEditingController _nameController = TextEditingController();
  final FocusNode _nameFocus = FocusNode();
  
  String _selectedAvatar = 'smart_toy';
  bool _isNameValid = false;

  final List<Map<String, dynamic>> _avatarOptions = [
    {'icon': Icons.smart_toy, 'name': 'smart_toy', 'label': 'Robot'},
    {'icon': Icons.psychology, 'name': 'psychology', 'label': 'Brain'},
    {'icon': Icons.auto_awesome, 'name': 'auto_awesome', 'label': 'Magic'},
    {'icon': Icons.lightbulb_outline, 'name': 'lightbulb', 'label': 'Ideas'},
    {'icon': Icons.pets, 'name': 'pets', 'label': 'Companion'},
    {'icon': Icons.support_agent, 'name': 'support_agent', 'label': 'Agent'},
    {'icon': Icons.android, 'name': 'android', 'label': 'Android'},
    {'icon': Icons.face, 'name': 'face', 'label': 'Friendly'},
  ];

  @override
  void initState() {
    super.initState();
    
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    ));
    
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    ));
    
    _nameController.addListener(_validateName);
    
    // Start animation
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _nameController.dispose();
    _nameFocus.dispose();
    super.dispose();
  }

  void _validateName() {
    final name = _nameController.text.trim();
    setState(() {
      _isNameValid = name.length >= 2 && name.length <= 50;
    });
  }

  void _handleNext() {
    if (_isNameValid) {
      final data = {
        'assistant_name': _nameController.text.trim(),
        'assistant_avatar': _selectedAvatar,
      };
      widget.onNext(data);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: SlideTransition(
          position: _slideAnimation,
          child: Column(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Introduction
                      _buildIntroduction(theme),
                      
                      const SizedBox(height: 32),
                      
                      // Assistant name input
                      _buildNameInput(theme),
                      
                      const SizedBox(height: 32),
                      
                      // Avatar selection
                      _buildAvatarSelection(theme),
                      
                      const SizedBox(height: 32),
                      
                      // Preview
                      _buildPreview(theme),
                    ],
                  ),
                ),
              ),
              
              // Bottom actions
              _buildBottomActions(theme),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIntroduction(ThemeData theme) {
    return Column(
      children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                theme.colorScheme.primary.withOpacity(0.1),
                theme.colorScheme.secondary.withOpacity(0.1),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(60),
          ),
          child: Icon(
            Icons.person_add,
            size: 60,
            color: theme.colorScheme.primary,
          ),
        ),
        
        const SizedBox(height: 24),
        
        Text(
          'Meet Your Assistant',
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

  Widget _buildNameInput(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Assistant Name',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.onSurface,
          ),
        ),
        
        const SizedBox(height: 8),
        
        TextField(
          controller: _nameController,
          focusNode: _nameFocus,
          decoration: InputDecoration(
            hintText: 'e.g., Alex, Sage, Helper...',
            prefixIcon: Icon(
              Icons.badge,
              color: theme.colorScheme.primary,
            ),
            suffixIcon: _isNameValid
                ? Icon(
                    Icons.check_circle,
                    color: theme.colorScheme.primary,
                  )
                : null,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            errorText: _nameController.text.isNotEmpty && !_isNameValid
                ? 'Name must be 2-50 characters'
                : null,
          ),
          textCapitalization: TextCapitalization.words,
          maxLength: 50,
        ),
        
        const SizedBox(height: 8),
        
        Text(
          'Choose a name that feels right to you. This is how you\'ll think of your assistant.',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.6),
          ),
        ),
      ],
    );
  }

  Widget _buildAvatarSelection(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Choose an Avatar',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.onSurface,
          ),
        ),
        
        const SizedBox(height: 12),
        
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 4,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1,
          ),
          itemCount: _avatarOptions.length,
          itemBuilder: (context, index) {
            final avatar = _avatarOptions[index];
            final isSelected = _selectedAvatar == avatar['name'];
            
            return GestureDetector(
              onTap: () {
                setState(() {
                  _selectedAvatar = avatar['name'];
                });
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  color: isSelected
                      ? theme.colorScheme.primary.withOpacity(0.1)
                      : theme.colorScheme.surfaceVariant.withOpacity(0.5),
                  border: Border.all(
                    color: isSelected
                        ? theme.colorScheme.primary
                        : Colors.transparent,
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      avatar['icon'],
                      size: 32,
                      color: isSelected
                          ? theme.colorScheme.primary
                          : theme.colorScheme.onSurface.withOpacity(0.7),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      avatar['label'],
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: isSelected
                            ? theme.colorScheme.primary
                            : theme.colorScheme.onSurface.withOpacity(0.6),
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildPreview(ThemeData theme) {
    if (!_isNameValid) return const SizedBox.shrink();
    
    final selectedAvatarData = _avatarOptions.firstWhere(
      (avatar) => avatar['name'] == _selectedAvatar,
    );
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.colorScheme.primary.withOpacity(0.2),
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(25),
                ),
                child: Icon(
                  selectedAvatarData['icon'],
                  color: theme.colorScheme.primary,
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _nameController.text.trim(),
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                    Text(
                      'Your AI Assistant',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.chat_bubble_outline,
                  color: theme.colorScheme.primary,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Hi! I\'m ${_nameController.text.trim()}. I\'m excited to help you achieve your goals!',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.8),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomActions(ThemeData theme) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _isNameValid ? _handleNext : null,
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text(
              'Continue',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
        
        const SizedBox(height: 12),
        
        TextButton(
          onPressed: widget.onPrevious,
          child: Text(
            'Back',
            style: TextStyle(
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
        ),
      ],
    );
  }
}