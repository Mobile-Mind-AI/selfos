import 'package:flutter/material.dart';

/// Navigation buttons for onboarding steps
class NavigationButtons extends StatelessWidget {
  final bool isSaving;
  final VoidCallback onNext;
  final VoidCallback onPrevious;
  final String nextLabel;
  final String previousLabel;
  final bool nextEnabled;

  const NavigationButtons({
    super.key,
    this.isSaving = false,
    required this.onNext,
    required this.onPrevious,
    this.nextLabel = 'Continue',
    this.previousLabel = 'Previous',
    this.nextEnabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: nextEnabled ? onNext : null,
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: isSaving
                ? Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            theme.colorScheme.onPrimary,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Saving...',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: theme.colorScheme.onPrimary,
                        ),
                      ),
                    ],
                  )
                : Text(
                    nextLabel,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
          ),
        ),
        
        const SizedBox(height: 12),
        
        TextButton(
          onPressed: onPrevious,
          child: Text(
            previousLabel,
            style: TextStyle(
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
        ),
      ],
    );
  }
}