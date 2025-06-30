import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../services/auth_provider.dart';
import '../config/routes.dart';
import '../models/user.dart';

/// Main application shell with sidebar navigation
class MainShell extends ConsumerStatefulWidget {
  final Widget child;

  const MainShell({
    super.key,
    required this.child,
  });

  @override
  ConsumerState<MainShell> createState() => _MainShellState();
}

class _MainShellState extends ConsumerState<MainShell> {
  int _selectedIndex = 0;

  final List<NavigationItem> _navigationItems = [
    NavigationItem(
      icon: Icons.today_outlined,
      selectedIcon: Icons.today,
      label: 'Today',
      route: RoutePaths.home,
    ),
    NavigationItem(
      icon: Icons.chat_outlined,
      selectedIcon: Icons.chat,
      label: 'Chat',
      route: RoutePaths.chat,
    ),
    NavigationItem(
      icon: Icons.flag_outlined,
      selectedIcon: Icons.flag,
      label: 'Goals',
      route: RoutePaths.goals,
    ),
    NavigationItem(
      icon: Icons.task_outlined,
      selectedIcon: Icons.task,
      label: 'Tasks',
      route: RoutePaths.tasks,
    ),
    NavigationItem(
      icon: Icons.trending_up_outlined,
      selectedIcon: Icons.trending_up,
      label: 'Progress',
      route: RoutePaths.progress,
    ),
    NavigationItem(
      icon: Icons.settings_outlined,
      selectedIcon: Icons.settings,
      label: 'Settings',
      route: RoutePaths.settings,
    ),
  ];

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _updateSelectedIndex();
  }

  void _updateSelectedIndex() {
    final currentLocation = GoRouterState.of(context).matchedLocation;
    final index = _navigationItems.indexWhere((item) => item.route == currentLocation);
    if (index != -1 && index != _selectedIndex) {
      setState(() {
        _selectedIndex = index;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final user = ref.watch(currentUserProvider);
    final isWideScreen = MediaQuery.of(context).size.width > 768;

    return Scaffold(
      body: Row(
        children: [
          // Sidebar Navigation
          Container(
            width: isWideScreen ? 280 : 72,
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              border: Border(
                right: BorderSide(
                  color: theme.colorScheme.outline.withOpacity(0.2),
                  width: 1,
                ),
              ),
            ),
            child: Column(
              children: [
                _buildHeader(theme, user, isWideScreen),
                Expanded(
                  child: _buildNavigationItems(theme, isWideScreen),
                ),
                _buildUserProfile(theme, user, isWideScreen),
              ],
            ),
          ),

          // Main Content Area
          Expanded(
            child: Container(
              color: theme.colorScheme.background,
              child: widget.child,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(ThemeData theme, User? user, bool isWideScreen) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  theme.colorScheme.primary,
                  theme.colorScheme.primaryContainer,
                ],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              Icons.psychology,
              color: theme.colorScheme.onPrimary,
              size: 24,
            ),
          ),

          if (isWideScreen) ...[
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'SelfOS',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  if (user != null)
                    Text(
                      'Welcome back, ${user.displayName?.split(' ').first ?? 'User'}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.7),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildNavigationItems(ThemeData theme, bool isWideScreen) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      itemCount: _navigationItems.length,
      itemBuilder: (context, index) {
        final item = _navigationItems[index];
        final isSelected = _selectedIndex == index;

        return Container(
          margin: const EdgeInsets.symmetric(vertical: 2),
          child: ListTile(
            leading: Icon(
              isSelected ? item.selectedIcon : item.icon,
              color: isSelected
                ? theme.colorScheme.primary
                : theme.colorScheme.onSurface.withOpacity(0.7),
            ),
            title: isWideScreen ? Text(
              item.label,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: isSelected
                  ? theme.colorScheme.primary
                  : theme.colorScheme.onSurface.withOpacity(0.8),
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ) : null,
            selected: isSelected,
            selectedTileColor: theme.colorScheme.primaryContainer.withOpacity(0.3),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            onTap: () => _onNavigationTap(index, item.route),
            contentPadding: EdgeInsets.symmetric(
              horizontal: isWideScreen ? 16 : 8,
              vertical: 4,
            ),
          ),
        );
      },
    );
  }

  Widget _buildUserProfile(ThemeData theme, User? user, bool isWideScreen) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border(
          top: BorderSide(
            color: theme.colorScheme.outline.withOpacity(0.2),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: theme.colorScheme.primaryContainer,
            child: user?.photoUrl != null
              ? ClipOval(
                  child: Image.network(
                    user!.photoUrl!,
                    width: 40,
                    height: 40,
                    fit: BoxFit.cover,
                  ),
                )
              : Text(
                  user?.displayName?.substring(0, 1).toUpperCase() ?? 'U',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.bold,
                  ),
                ),
          ),

          if (isWideScreen) ...[
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    user?.displayName ?? 'User',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    user?.email ?? '',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.6),
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],

          IconButton(
            icon: Icon(
              Icons.more_vert,
              color: theme.colorScheme.onSurface.withOpacity(0.7),
            ),
            onPressed: () => _showUserMenu(context),
            tooltip: 'User menu',
          ),
        ],
      ),
    );
  }

  void _onNavigationTap(int index, String route) {
    setState(() {
      _selectedIndex = index;
    });
    context.go(route);
  }

  void _showUserMenu(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(authProvider.notifier).logout();
            },
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }
}

/// Navigation item model
class NavigationItem {
  final IconData icon;
  final IconData selectedIcon;
  final String label;
  final String route;

  const NavigationItem({
    required this.icon,
    required this.selectedIcon,
    required this.label,
    required this.route,
  });
}