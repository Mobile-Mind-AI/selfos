import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/onboarding_provider.dart';
import '../../config/routes.dart';
import 'welcome_step.dart';
import 'assistant_creation_step.dart';
import 'life_areas_step.dart';
import 'first_goal_step.dart';
import 'completion_step.dart';

/// Onboarding flow screen that guides users through setting up their assistant
/// and initial preferences in a gamified, narrative style.
/// 
/// This implements the "Start Your Story" concept where the user is the hero
/// creating their AI assistant companion.
class OnboardingFlowScreen extends ConsumerStatefulWidget {
  const OnboardingFlowScreen({super.key});

  @override
  ConsumerState<OnboardingFlowScreen> createState() => _OnboardingFlowScreenState();
}

class _OnboardingFlowScreenState extends ConsumerState<OnboardingFlowScreen>
    with TickerProviderStateMixin {
  
  late PageController _pageController;
  late AnimationController _progressAnimationController;
  late Animation<double> _progressAnimation;
  
  int _currentStep = 0;
  final int _totalSteps = 5;
  
  // Onboarding data collected across steps
  final Map<String, dynamic> _onboardingData = {};
  
  // Rate limiting for navigation
  Timer? _navigationTimer;
  bool _isNavigating = false;
  DateTime? _lastNavigationAttempt;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _progressAnimationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _progressAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _progressAnimationController,
      curve: Curves.easeInOut,
    ));
    _updateProgress();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _progressAnimationController.dispose();
    _navigationTimer?.cancel();
    super.dispose();
  }

  void _updateProgress() {
    final progress = (_currentStep + 1) / _totalSteps;
    _progressAnimationController.animateTo(progress);
  }

  void _nextStep([Map<String, dynamic>? stepData]) async {
    // Prevent rapid navigation (minimum 2 seconds between step updates)
    if (_isNavigating) {
      print('🎯 FLUTTER: Navigation in progress, ignoring request');
      return;
    }
    
    if (_lastNavigationAttempt != null && 
        DateTime.now().difference(_lastNavigationAttempt!) < const Duration(seconds: 2)) {
      print('🎯 FLUTTER: Rate limiting navigation - too soon since last attempt');
      return;
    }
    
    setState(() {
      _isNavigating = true;
    });
    _lastNavigationAttempt = DateTime.now();
    
    if (stepData != null) {
      _onboardingData.addAll(stepData);
    }
    
    try {
      // For welcome step (step 0), just proceed without API call
      if (_currentStep == 0) {
        if (_currentStep < _totalSteps - 1) {
          setState(() {
            _currentStep++;
          });
          _pageController.nextPage(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          );
          _updateProgress();
        }
        return;
      }
      
      // For other steps (1-3), send step update to backend
      if (_currentStep >= 1 && _currentStep <= 3) {
        final stepName = _getStepName(_currentStep);
        if (stepName != null && stepData != null) {
          print('🎯 FLUTTER: Sending step update: $stepName (step $_currentStep) with data: $stepData');
          
          final success = await ref.read(onboardingProvider.notifier)
              .updateOnboardingStep(stepName, stepData);
          
          if (!success) {
            // Show error and don't proceed
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Failed to save progress. Please try again.'),
                  backgroundColor: Colors.red,
                ),
              );
            }
            return; // Don't proceed to next step if API call failed
          }
          
          print('🎯 FLUTTER: Step update successful, proceeding to next step');
        } else {
          print('🎯 FLUTTER: WARNING - No step name or data for step $_currentStep');
        }
      }
      
      // Only proceed to next step if API call was successful (or not needed)
      if (_currentStep < _totalSteps - 1) {
        setState(() {
          _currentStep++;
        });
        _pageController.nextPage(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
        _updateProgress();
        print('🎯 FLUTTER: Advanced to step ${_currentStep + 1}');
      }
    } finally {
      // Reset navigation state after a delay
      _navigationTimer?.cancel();
      _navigationTimer = Timer(const Duration(seconds: 3), () {
        if (mounted) {
          setState(() {
            _isNavigating = false;
          });
        }
      });
    }
  }

  void _previousStep() {
    if (_currentStep > 0) {
      setState(() {
        _currentStep--;
      });
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
      _updateProgress();
    }
  }

  Future<void> _completeOnboarding() async {
    try {
      print('🎯 FLUTTER: Attempting to complete onboarding...');
      print('🎯 FLUTTER: Current onboarding data: $_onboardingData');
      
      // Complete onboarding via provider
      final success = await ref.read(onboardingProvider.notifier).completeOnboarding();
      
      print('🎯 FLUTTER: Complete onboarding result: $success');
      
      if (success) {
        // Navigate to main app
        if (mounted) {
          print('🎯 FLUTTER: Navigating to home...');
          context.go(RoutePaths.home);
        }
      } else {
        // Show error message
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Failed to complete onboarding. Please try again.'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      print('🎯 FLUTTER: Error completing onboarding: $e');
      // Show error message
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error completing onboarding: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _skipOnboarding() async {
    // Show confirmation dialog
    final shouldSkip = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Skip Onboarding?'),
        content: const Text(
          'You can always set up your assistant later in settings. '
          'Would you like to continue with default settings?'
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Skip'),
          ),
        ],
      ),
    );

    if (shouldSkip == true) {
      try {
        // Skip onboarding via provider
        final success = await ref.read(onboardingProvider.notifier).skipOnboarding();
        
        if (success) {
          // Navigate to main app
          if (mounted) {
            context.go(RoutePaths.home);
          }
        } else {
          // Show error message
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Failed to skip onboarding. Please try again.'),
                backgroundColor: Colors.red,
              ),
            );
          }
        }
      } catch (e) {
        // Show error message
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Error skipping onboarding: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // Header with progress bar
            _buildHeader(theme),
            
            // Navigation status indicator
            if (_isNavigating)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Saving progress...',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.7),
                      ),
                    ),
                  ],
                ),
              ),
            
            // Main content
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  WelcomeStep(
                    onNext: _nextStep,
                    onSkip: _skipOnboarding,
                  ),
                  AssistantCreationStep(
                    onNext: _nextStep,
                    onPrevious: _previousStep,
                  ),
                  LifeAreasStep(
                    onNext: _nextStep,
                    onPrevious: _previousStep,
                  ),
                  FirstGoalStep(
                    onNext: _nextStep,
                    onPrevious: _previousStep,
                  ),
                  CompletionStep(
                    onboardingData: _onboardingData,
                    onComplete: _completeOnboarding,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          // Progress bar
          Row(
            children: [
              Expanded(
                child: AnimatedBuilder(
                  animation: _progressAnimation,
                  builder: (context, child) {
                    return LinearProgressIndicator(
                      value: _progressAnimation.value,
                      backgroundColor: theme.colorScheme.surfaceVariant,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        theme.colorScheme.primary,
                      ),
                      minHeight: 6,
                    );
                  },
                ),
              ),
              const SizedBox(width: 16),
              Text(
                '${_currentStep + 1}/$_totalSteps',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          // Step titles
          Row(
            children: [
              Expanded(
                child: Text(
                  _getStepTitle(_currentStep),
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ),
              if (_currentStep > 0)
                IconButton(
                  onPressed: _previousStep,
                  icon: Icon(
                    Icons.arrow_back_ios,
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                  ),
                  tooltip: 'Previous step',
                ),
            ],
          ),
        ],
      ),
    );
  }

  String _getStepTitle(int step) {
    switch (step) {
      case 0:
        return 'Welcome to SelfOS';
      case 1:
        return 'Meet Your Assistant';
      case 2:
        return 'Life Areas';
      case 3:
        return 'Your First Goal';
      case 4:
        return 'Ready to Begin!';
      default:
        return 'Setup';
    }
  }

  String? _getStepName(int step) {
    switch (step) {
      case 1:
        return 'assistant_creation';  // Maps to backend step 2 (and auto-marks 3,4)
      case 2:
        return 'life_areas';         // Maps to backend step 5
      case 3:
        return 'first_goal';         // Maps to backend step 6
      default:
        return null;
    }
  }
}