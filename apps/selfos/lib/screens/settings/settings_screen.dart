import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/auth_provider.dart';
import '../../models/user.dart';
import 'assistant_configuration_screen.dart';

/// Settings and preferences screen
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final user = ref.watch(currentUserProvider);

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            floating: true,
            title: const Text('Settings'),
            automaticallyImplyLeading: false,
          ),

          SliverList(
            delegate: SliverChildListDelegate([
              // User Profile Section
              _buildProfileSection(theme, user),

              // App Settings
              _buildSection(
                theme,
                'App Settings',
                [
                  _buildSettingsItem(
                    theme,
                    Icons.notifications_outlined,
                    'Notifications',
                    'Manage your notification preferences',
                    () {
                      // TODO: Open notifications settings
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.dark_mode_outlined,
                    'Theme',
                    'Light, dark, or system default',
                    () {
                      // TODO: Open theme settings
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.language_outlined,
                    'Language',
                    'English (US)',
                    () {
                      // TODO: Open language settings
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.sync_outlined,
                    'Sync',
                    'Backup and sync your data',
                    () {
                      // TODO: Open sync settings
                    },
                  ),
                ],
              ),

              // AI Settings
              _buildSection(
                theme,
                'AI Assistant',
                [
                  _buildSettingsItem(
                    theme,
                    Icons.psychology_outlined,
                    'AI Preferences',
                    'Customize your AI assistant',
                    () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const AssistantConfigurationScreen(),
                        ),
                      );
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.memory_outlined,
                    'Context & Memory',
                    'Manage AI conversation history',
                    () {
                      // TODO: Open memory settings
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.security_outlined,
                    'Privacy',
                    'Control data sharing and privacy',
                    () {
                      // TODO: Open privacy settings
                    },
                  ),
                ],
              ),

              // Account & Data
              _buildSection(
                theme,
                'Account & Data',
                [
                  _buildSettingsItem(
                    theme,
                    Icons.person_outline,
                    'Profile',
                    'Edit your profile information',
                    () {
                      // TODO: Open profile editor
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.lock_outline,
                    'Change Password',
                    'Update your account password',
                    () {
                      _showChangePasswordDialog(context, ref);
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.download_outlined,
                    'Export Data',
                    'Download your personal data',
                    () {
                      // TODO: Export data
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.delete_outline,
                    'Delete Account',
                    'Permanently delete your account',
                    () {
                      _showDeleteAccountDialog(context, ref);
                    },
                    isDestructive: true,
                  ),
                ],
              ),

              // Support & About
              _buildSection(
                theme,
                'Support & About',
                [
                  _buildSettingsItem(
                    theme,
                    Icons.help_outline,
                    'Help & Support',
                    'Get help and contact support',
                    () {
                      // TODO: Open help
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.feedback_outlined,
                    'Send Feedback',
                    'Help us improve SelfOS',
                    () {
                      // TODO: Open feedback
                    },
                  ),
                  _buildSettingsItem(
                    theme,
                    Icons.info_outline,
                    'About',
                    'Version 1.0.0',
                    () {
                      _showAboutDialog(context);
                    },
                  ),
                ],
              ),

              // Sign Out
              const SizedBox(height: 32),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: OutlinedButton(
                  onPressed: () => _showSignOutDialog(context, ref),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: theme.colorScheme.error,
                    side: BorderSide(color: theme.colorScheme.error),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.logout),
                      SizedBox(width: 8),
                      Text('Sign Out'),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 32),
            ]),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileSection(ThemeData theme, User? user) {
    return Container(
      margin: const EdgeInsets.all(16),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              CircleAvatar(
                radius: 30,
                backgroundColor: theme.colorScheme.primaryContainer,
                child: user?.photoUrl != null
                  ? ClipOval(
                      child: Image.network(
                        user!.photoUrl!,
                        width: 60,
                        height: 60,
                        fit: BoxFit.cover,
                      ),
                    )
                  : Text(
                      user?.displayName?.substring(0, 1).toUpperCase() ?? 'U',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        color: theme.colorScheme.onPrimaryContainer,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      user?.displayName ?? 'User',
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      user?.email ?? '',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.7),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Member since ${DateTime.now().year}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                onPressed: () {
                  // TODO: Edit profile
                },
                icon: const Icon(Icons.edit),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSection(ThemeData theme, String title, List<Widget> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(32, 24, 16, 8),
          child: Text(
            title,
            style: theme.textTheme.titleSmall?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        ...items,
      ],
    );
  }

  Widget _buildSettingsItem(
    ThemeData theme,
    IconData icon,
    String title,
    String subtitle,
    VoidCallback onTap, {
    bool isDestructive = false,
  }) {
    return ListTile(
      leading: Icon(
        icon,
        color: isDestructive
          ? theme.colorScheme.error
          : theme.colorScheme.onSurface.withOpacity(0.7),
      ),
      title: Text(
        title,
        style: theme.textTheme.bodyLarge?.copyWith(
          color: isDestructive ? theme.colorScheme.error : null,
        ),
      ),
      subtitle: Text(subtitle),
      trailing: Icon(
        Icons.chevron_right,
        color: theme.colorScheme.onSurface.withOpacity(0.5),
      ),
      onTap: onTap,
    );
  }

  void _showSignOutDialog(BuildContext context, WidgetRef ref) {
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

  void _showChangePasswordDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Change Password'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              decoration: InputDecoration(
                labelText: 'Current Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            SizedBox(height: 16),
            TextField(
              decoration: InputDecoration(
                labelText: 'New Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            SizedBox(height: 16),
            TextField(
              decoration: InputDecoration(
                labelText: 'Confirm New Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              // TODO: Change password
              Navigator.pop(context);
            },
            child: const Text('Change Password'),
          ),
        ],
      ),
    );
  }

  void _showDeleteAccountDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Account'),
        content: const Text(
          'This action cannot be undone. All your data will be permanently deleted.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              // TODO: Delete account
            },
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.error,
            ),
            child: const Text('Delete Account'),
          ),
        ],
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showAboutDialog(
      context: context,
      applicationName: 'SelfOS',
      applicationVersion: '1.0.0',
      applicationIcon: const Icon(Icons.psychology, size: 48),
      children: [
        const Text('Personal Growth Operating System'),
        const SizedBox(height: 16),
        const Text('Built with Flutter and powered by AI to help you achieve your goals.'),
      ],
    );
  }
}
