import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/onboarding_provider.dart';
import '../../providers/auth_provider.dart';
import '../../config/routes.dart';
import '../../services/onboarding/onboarding_manager.dart';
import '../../services/sync/sync_manager.dart';
import 'welcome_step.dart';
import 'assistant_creation_step.dart';
import 'personal_configuration_step.dart';


/// Represents the main onboarding flow screen for the SelfOS application.
///
/// This widget manages the onboarding process using a stateful approach.
/// It includes navigation between steps, progress tracking, and data collection.
///
/// Extends:
/// - `ConsumerStatefulWidget`: A stateful widget that integrates with Riverpod for state management.
class OnboardingFlowScreen extends ConsumerStatefulWidget {
  const OnboardingFlowScreen({super.key});

  @override
  ConsumerState<OnboardingFlowScreen> createState() => _OnboardingFlowScreenState();
}
/// Represents the state for the `OnboardingFlowScreen` widget.
///
/// This class manages the stateful behavior of the onboarding flow, including
/// navigation between steps, progress tracking, and data collection. It also
/// handles animations, user interactions, and offline-first updates.
///
/// Extends:
/// - `ConsumerState<OnboardingFlowScreen>`: A Riverpod consumer state that allows
///   access to providers for state management.
class _OnboardingFlowScreenState extends ConsumerState<OnboardingFlowScreen>
    with TickerProviderStateMixin {
  
  late PageController _pageController;
  late AnimationController _progressAnimationController;
  late Animation<double> _progressAnimation;
  
  int _currentStep = 0;
  final int _totalSteps = 3;
  
  // Onboarding data collected across steps
  final Map<String, dynamic> _onboardingData = {};
  
  // OnboardingManager for offline-first updates
  final OnboardingManager _onboardingManager = OnboardingManager.instance;
  
  /// Initializes the state for the `_OnboardingFlowScreenState` widget.
  ///
  /// This method sets up the `PageController` for managing page navigation,
  /// and the `AnimationController` for handling progress animations. It also
  /// initializes the progress animation and updates the progress bar.
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
    
    // Wait for initial sync to complete
    _waitForInitialSync();
  }
  
  /// Wait for initial sync to complete before allowing onboarding to proceed
  Future<void> _waitForInitialSync() async {
    // Give sync a moment to complete
    await Future.delayed(const Duration(seconds: 2));
    
    // Force a state update to ensure any synced data is available
    if (mounted) {
      setState(() {});
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    _progressAnimationController.dispose();
    super.dispose();
  }

  void _updateProgress() {
    final progress = (_currentStep + 1) / _totalSteps;
    _progressAnimationController.animateTo(progress);
  }

  /// Builds the header section for the onboarding flow screen.
  ///
  /// This method constructs the header widget, which includes a progress bar
  /// and step titles. It provides navigation to the previous step if applicable.
  ///
  /// Parameters:
  /// - [theme]: The `ThemeData` object used to style the header components.
  ///
  /// Returns:
  ///   A `Widget` representing the header section with progress tracking and navigation.
  void _nextStep([Map<String, dynamic>? stepData]) async {
    print('🎯 FLUTTER: _nextStep called from step $_currentStep');
    
    if (stepData != null) {
      _onboardingData.addAll(stepData);
    }
      
      // For welcome step (step 0), just proceed without API call
      if (_currentStep == 0) {
        print('🎯 FLUTTER: Processing welcome step navigation');
        if (_currentStep < _totalSteps - 1) {
          print('🎯 FLUTTER: Moving from step 0 to step 1');
          setState(() {
            _currentStep++;
          });
          await _pageController.nextPage(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          );
          _updateProgress();
          print('🎯 FLUTTER: Navigation to step 1 complete');
        }
        return;
      }
      
      // For other steps, use offline-first onboarding state manager
      if (_currentStep >= 1 && _currentStep <= 2) {
        try {
          // Get user ID from auth - wait for auth to be loaded
          final authState = ref.read(authStateProvider);
          String? userId;
          
          // If auth is still loading, wait a bit
          if (authState.isLoading) {
            print('🎯 FLUTTER: Auth state is loading, waiting...');
            await Future.delayed(const Duration(milliseconds: 500));
            final updatedAuthState = ref.read(authStateProvider);
            if (updatedAuthState.isLoggedIn && updatedAuthState.user != null) {
              userId = updatedAuthState.user!.uid;
              print('🎯 FLUTTER: Got user ID after waiting: $userId');
            }
          } else if (authState.isLoggedIn && authState.user != null) {
            userId = authState.user!.uid;
            print('🎯 FLUTTER: Got user ID: $userId');
          } else {
            print('🎯 FLUTTER: Auth state is not authenticated - isLoggedIn: ${authState.isLoggedIn}, user: ${authState.user}');
          }
          
          if (userId == null) {
            print('🎯 FLUTTER: No user ID available - continuing offline');
            // Don't return - continue with offline-first approach
          } else {
            // Update onboarding state locally
            final backendStep = _mapFrontendToBackendStep(_currentStep);
            if (backendStep != null) {
              // Get or create onboarding state for user
              final existingState = await _onboardingManager.getOnboardingState(userId);
              
              if (existingState != null) {
                // Update step progress
                await _onboardingManager.updateStepProgress(
                  existingState['id'],
                  backendStep,
                  _getCompletedSteps(backendStep),
                );
                
                // Update temp data separately
                await _onboardingManager.updateTempData(
                  existingState['id'],
                  _onboardingData,
                );
              } else {
                // Create new onboarding state
                await _onboardingManager.createOnboardingState(
                  userId: userId,
                  currentStep: backendStep,
                  completedSteps: _getCompletedSteps(backendStep),
                  tempData: _onboardingData,
                );
              }
              
              print('🎯 FLUTTER: Updated onboarding state locally for step $backendStep');
            }
          }
        } catch (e) {
          print('🎯 FLUTTER: Error updating onboarding state: $e');
          // Don't show error - offline-first means we continue anyway
        }
      }
      
      // Always proceed to next step (offline-first approach)
      if (_currentStep < _totalSteps - 1) {
        setState(() {
          _currentStep++;
        });
        _pageController.nextPage(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
        _updateProgress();
        print('🎯 FLUTTER: Advanced to step $_currentStep');
      } else {
        // We've reached the end of the onboarding flow, complete it
        print('🎯 FLUTTER: Reached end of onboarding flow, completing...');
        _completeOnboarding();
      }
  }

  /// Navigates to the previous step in the onboarding process.
  ///
  /// This method decreases the `_currentStep` index and updates the UI to reflect
  /// the previous step. It also animates the `PageController` to transition
  /// to the previous page and updates the progress bar accordingly.
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

  /// Completes the onboarding process for the user.
  ///
  /// This method finalizes the onboarding flow by updating the backend state,
  /// synchronizing data, and navigating to the main application screen. It handles
  /// offline-first updates and ensures the onboarding state is marked as completed.
  ///
  /// The method retrieves the user ID from the authentication provider, updates
  /// the onboarding state locally and in the backend, and triggers a sync operation
  /// to ensure data consistency. If successful, it navigates to the home screen.
  ///
  /// Handles errors gracefully by showing appropriate error messages to the user.
  ///
  /// Returns:
  ///   A `Future` that completes when the onboarding process is finalized.
  Future<void> _completeOnboarding() async {
    try {
      print('🎯 FLUTTER: Attempting to complete onboarding...');
      print('🎯 FLUTTER: Current onboarding data: $_onboardingData');
      
      // Get user ID from auth - wait for auth to be loaded
      final authState = ref.read(authStateProvider);
      String? userId;
      
      // If auth is still loading, wait a bit
      if (authState.isLoading) {
        print('🎯 FLUTTER: Auth state is loading for completion, waiting...');
        await Future.delayed(const Duration(milliseconds: 500));
        final updatedAuthState = ref.read(authStateProvider);
        if (updatedAuthState.isLoggedIn && updatedAuthState.user != null) {
          userId = updatedAuthState.user!.uid;
          print('🎯 FLUTTER: Got user ID for completion after waiting: $userId');
        }
      } else if (authState.isLoggedIn && authState.user != null) {
        userId = authState.user!.uid;
        print('🎯 FLUTTER: Got user ID for completion: $userId');
      } else {
        print('🎯 FLUTTER: Auth state is not authenticated for completion - isLoggedIn: ${authState.isLoggedIn}, user: ${authState.user}');
      }
      
      if (userId != null) {
        // Ensure we have an onboarding state in the backend
        final existingState = await _onboardingManager.getOnboardingState(userId);
        if (existingState != null) {
          // Mark the onboarding as completed in the local state first
          await _onboardingManager.completeOnboardingState(
            existingState['id'],
            assistantProfileId: _onboardingData['assistant_profile_id'], // Use the correct key
          );
          
          // Trigger immediate sync to ensure backend has the state
          print('🎯 FLUTTER: Triggering sync before completing onboarding...');
          print('🎯 FLUTTER: Assistant profile ID: ${_onboardingData['assistant_profile_id']}');
          
          try {
            // Process sync queue once and wait for completion
            print('🎯 FLUTTER: Processing sync queue...');
            await SyncManager.instance.processSyncQueue();
            
            // Wait for sync to complete before checking status
            await Future.delayed(const Duration(seconds: 2));
            
            // Check if there are still pending operations
            final status = await SyncManager.instance.currentStatus;
            if (status.pendingOperations > 0) {
              print('🎯 FLUTTER: ${status.pendingOperations} operations still pending, processing again...');
              // Process once more if needed
              await SyncManager.instance.processSyncQueue();
              await Future.delayed(const Duration(seconds: 1));
            }
          } catch (syncError) {
            print('⚠️ FLUTTER: Sync failed but continuing: $syncError');
          }
        }
      }
      
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


  /// Builds the main UI for the onboarding flow screen.
  ///
  /// This method constructs the scaffold for the onboarding screen, including
  /// the header section with progress tracking and the main content area with
  /// step-specific widgets. It uses Riverpod for state management and Flutter's
  /// `ThemeData` for styling.
  ///
  /// Parameters:
  /// - [context]: The `BuildContext` object that provides access to the widget tree.
  ///
  /// Returns:
  ///   A `Widget` representing the onboarding flow screen.
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
            
            // Main content
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  WelcomeStep(
                    onNext: _nextStep,
                  ),
                  AssistantCreationStep(
                    onNext: _nextStep,
                    onPrevious: _previousStep,
                  ),
                  PersonalConfigurationStep(
                    onNext: _nextStep,
                    onPrevious: _previousStep,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds the header section for the onboarding flow screen.
  ///
  /// This method constructs the header widget, which includes a progress bar
  /// and step titles. It provides navigation to the previous step if applicable.
  ///
  /// Parameters:
  /// - [theme]: The `ThemeData` object used to style the header components.
  ///
  /// Returns:
  ///   A `Widget` representing the header section with progress tracking and navigation.
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
        return 'Step 1: AI Assistant Configuration';
      case 2:
        return 'Step 2: Personal Configuration';
      default:
        return 'Setup';
    }
  }

  String? _getStepName(int step) {
    switch (step) {
      case 1:
        return 'assistant_creation';  // Maps to backend step 2 (and auto-marks 3,4)
      case 2:
        return 'personal_config';    // Maps to backend step 5 (life areas + goal setup)
      default:
        return null;
    }
  }
  
  /// Map frontend step to backend step number
  int? _mapFrontendToBackendStep(int frontendStep) {
    switch (frontendStep) {
      case 1:
        return 2; // AI Assistant Configuration
      case 2:
        return 5; // Personal Configuration
      default:
        return null;
    }
  }
  
  /// Get list of completed steps based on current step
  List<int> _getCompletedSteps(int currentStep) {
    final completed = <int>[];
    for (int i = 1; i < currentStep; i++) {
      completed.add(i);
    }
    // Auto-mark related steps as completed
    if (currentStep >= 2) {
      completed.addAll([1, 2, 3, 4]); // Mark all AI config steps as complete
    }
    return completed;
  }
}