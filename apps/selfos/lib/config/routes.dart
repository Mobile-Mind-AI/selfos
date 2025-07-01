import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_provider.dart';
import '../screens/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/signup_screen.dart';
import '../screens/main_shell.dart';
import '../screens/home/today_screen.dart';
import '../screens/chat/chat_screen.dart';
import '../screens/goals/goals_screen.dart';
import '../screens/progress/progress_screen.dart';
import '../screens/settings/settings_screen.dart';
import '../screens/tasks/tasks_screen.dart';

/// Application routing configuration using GoRouter
///
/// This configuration provides:
/// - Route definitions for all screens
/// - Authentication-based route protection
/// - Automatic redirects based on auth state
/// - Deep linking support
/// - Type-safe navigation
///
/// Routes:
/// - `/` - Splash/Initial screen (redirects based on auth)
/// - `/login` - Login screen
/// - `/signup` - Signup screen
/// - `/home` - Main dashboard (protected)
/// - `/goals` - Goals management (protected)
/// - `/tasks` - Tasks management (protected)
/// - `/settings` - App settings (protected)

/// Route paths constants
class RoutePaths {
  static const String splash = '/';
  static const String login = '/login';
  static const String signup = '/signup';
  static const String home = '/home';
  static const String chat = '/chat';
  static const String goals = '/goals';
  static const String tasks = '/tasks';
  static const String progress = '/progress';
  static const String settings = '/settings';
}

/// Provider for GoRouter configuration
/// 
/// This provider creates a GoRouter instance with authentication-aware routing.
/// It automatically redirects users based on their authentication state.
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  
  return GoRouter(
    debugLogDiagnostics: true,
    
    // Initial location
    initialLocation: RoutePaths.splash,
    
    // Redirect logic based on authentication state
    redirect: (context, state) {
      final isAuthenticated = authState is AuthStateAuthenticated;
      final isInitial = authState is AuthStateInitial;
      final isLoading = authState is AuthStateLoading;
      
      final currentPath = state.matchedLocation;
      final isAuthRoute = currentPath == RoutePaths.login || currentPath == RoutePaths.signup;
      final isSplashRoute = currentPath == RoutePaths.splash;

      if (kDebugMode) {
        print('🚦 ROUTER: Current path: $currentPath');
        print('🚦 ROUTER: Auth state: ${authState.runtimeType}');
      }

      // Stay on splash while initializing
      if ((isInitial || isLoading) && isSplashRoute) {
        return null;
      }

      // Redirect authenticated users from auth/splash to home
      if (isAuthenticated && (isAuthRoute || isSplashRoute)) {
        return RoutePaths.home;
      }

      // Redirect unauthenticated users from splash to login
      if (!isAuthenticated && !isInitial && !isLoading && isSplashRoute) {
        return RoutePaths.login;
      }

      // Redirect unauthenticated users from protected routes to login
      if (!isAuthenticated && !isAuthRoute && !isSplashRoute) {
        return RoutePaths.login;
      }

      return null;
    },
    
    routes: [
      GoRoute(
        path: RoutePaths.splash,
        name: 'splash',
        builder: (context, state) => const SplashScreen(),
      ),

      GoRoute(
        path: RoutePaths.login,
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),

      GoRoute(
        path: RoutePaths.signup,
        name: 'signup',
        builder: (context, state) => const SignupScreen(),
      ),
      // Protected routes with shell wrapper
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: RoutePaths.home,
            name: 'home',
            builder: (context, state) => const TodayScreen(),
          ),
          GoRoute(
            path: RoutePaths.chat,
            name: 'chat',
            builder: (context, state) => const ChatScreen(),
          ),
          GoRoute(
            path: RoutePaths.goals,
            name: 'goals',
            builder: (context, state) => const GoalsScreen(),
          ),
          GoRoute(
            path: RoutePaths.tasks,
            name: 'tasks',
            builder: (context, state) => const TasksScreen(),
          ),
          GoRoute(
            path: RoutePaths.progress,
            name: 'progress',
            builder: (context, state) => const ProgressScreen(),
          ),
          GoRoute(
            path: RoutePaths.settings,
            name: 'settings',
            builder: (context, state) => const SettingsScreen(),
          ),
        ],
      ),
    ],

    // Error page
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Page not found: ${state.matchedLocation}'),
      ),
    ),
  );
});

/// Splash screen shown during app initialization
/// 
/// This screen is displayed while the app determines the user's
/// authentication state and decides which screen to show.
class SplashScreen extends ConsumerWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // App logo
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: theme.colorScheme.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(30),
              ),
              child: Icon(
                Icons.psychology,
                size: 60,
                color: theme.colorScheme.primary,
              ),
            ),
            
            const SizedBox(height: 32),
            
            // App name
            Text(
              'SelfOS',
              style: theme.textTheme.headlineLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.primary,
              ),
            ),
            
            const SizedBox(height: 8),
            
            Text(
              'Personal Growth Operating System',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.7),
              ),
            ),
            
            const SizedBox(height: 48),
            
            // Loading indicator
            CircularProgressIndicator(
              color: theme.colorScheme.primary,
            ),
          ],
        ),
      ),
    );
  }
}

/// Placeholder home screen
/// 
/// This is a temporary home screen that will be replaced with
/// the actual dashboard implementation.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('SelfOS Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign Out',
            onPressed: () => _showLogoutDialog(context, ref),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.home,
              size: 64,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Welcome to SelfOS!',
              style: theme.textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            if (user != null)
              Text(
                'Hello, ${user.displayName ?? user.email}',
                style: theme.textTheme.bodyLarge,
              ),
            const SizedBox(height: 32),
            Text(
              'Dashboard coming soon...',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const SizedBox(height: 48),
            ElevatedButton.icon(
              onPressed: () => _showLogoutDialog(context, ref),
              icon: const Icon(Icons.logout),
              label: const Text('Sign Out'),
              style: ElevatedButton.styleFrom(
                foregroundColor: theme.colorScheme.error,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Shows logout confirmation dialog
void _showLogoutDialog(BuildContext context, WidgetRef ref) {
  showDialog(
    context: context,
    builder: (BuildContext context) {
      return AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.of(context).pop();
              await ref.read(authProvider.notifier).logout();
            },
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.error,
            ),
            child: const Text('Sign Out'),
          ),
        ],
      );
    },
  );
}

/// Placeholder goals screen
class GoalsScreen extends StatelessWidget {
  const GoalsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Goals')),
      body: const Center(
        child: Text('Goals screen coming soon...'),
      ),
    );
  }
}

/// Placeholder tasks screen
class TasksScreen extends StatelessWidget {
  const TasksScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tasks')),
      body: const Center(
        child: Text('Tasks screen coming soon...'),
      ),
    );
  }
}

/// Placeholder settings screen
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Settings screen coming soon...'),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => ref.read(authProvider.notifier).logout(),
              child: const Text('Sign Out'),
            ),
          ],
        ),
      ),
    );
  }
}

/// Error screen for routing errors
class ErrorScreen extends StatelessWidget {
  final Exception? error;
  
  const ErrorScreen({super.key, this.error});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(title: const Text('Error')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: theme.colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'Something went wrong',
              style: theme.textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            if (error != null)
              Text(
                error.toString(),
                style: theme.textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => context.go(RoutePaths.home),
              child: const Text('Go Home'),
            ),
          ],
        ),
      ),
    );
  }
}