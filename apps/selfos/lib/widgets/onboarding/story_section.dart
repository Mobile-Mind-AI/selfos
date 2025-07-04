import 'package:flutter/material.dart';

/// Widget for the story section in personal configuration
class StorySection extends StatelessWidget {
  final TextEditingController currentSituationController;
  final TextEditingController aspirationsController;
  final Set<String> interests;
  final Set<String> challenges;
  final List<String> interestSuggestions;
  final List<String> challengeSuggestions;
  final VoidCallback onSave;

  const StorySection({
    super.key,
    required this.currentSituationController,
    required this.aspirationsController,
    required this.interests,
    required this.challenges,
    required this.interestSuggestions,
    required this.challengeSuggestions,
    required this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📖 Your Story',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Help your AI understand your journey',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
        const SizedBox(height: 16),
        
        // Current situation
        StoryField(
          title: 'Current Situation',
          hint: 'Where are you in life right now?',
          controller: currentSituationController,
          maxLength: 150,
          onSave: onSave,
        ),
        
        const SizedBox(height: 16),
        
        // Interests
        TagSection(
          title: 'Interests',
          hint: 'What are you passionate about?',
          selectedTags: interests,
          suggestions: interestSuggestions,
          onSave: onSave,
        ),
        
        const SizedBox(height: 16),
        
        // Challenges
        TagSection(
          title: 'Challenges',
          hint: 'What would you like to improve?',
          selectedTags: challenges,
          suggestions: challengeSuggestions,
          onSave: onSave,
        ),
        
        const SizedBox(height: 16),
        
        // Aspirations
        StoryField(
          title: 'Aspirations',
          hint: 'What do you hope to achieve?',
          controller: aspirationsController,
          maxLength: 150,
          onSave: onSave,
        ),
      ],
    );
  }
}

/// Text field for story elements like current situation and aspirations
class StoryField extends StatefulWidget {
  final String title;
  final String hint;
  final TextEditingController controller;
  final int maxLength;
  final VoidCallback onSave;

  const StoryField({
    super.key,
    required this.title,
    required this.hint,
    required this.controller,
    this.maxLength = 100,
    required this.onSave,
  });

  @override
  State<StoryField> createState() => _StoryFieldState();
}

class _StoryFieldState extends State<StoryField> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Focus(
          onFocusChange: (hasFocus) {
            if (!hasFocus) {
              // Save when the field loses focus
              print('📝 Story field "${widget.title}" lost focus, saving to backend...');
              widget.onSave();
            }
          },
          child: TextField(
            controller: widget.controller,
            decoration: InputDecoration(
              hintText: widget.hint,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: theme.colorScheme.surfaceVariant.withOpacity(0.3),
              contentPadding: const EdgeInsets.all(12),
              counterText: '${widget.controller.text.length}/${widget.maxLength}',
              counterStyle: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.5),
              ),
            ),
            maxLength: widget.maxLength,
            maxLines: 3,
            textCapitalization: TextCapitalization.sentences,
            onSubmitted: (value) => widget.onSave(),
            onChanged: (value) => setState(() {}), // Update counter
          ),
        ),
      ],
    );
  }
}

/// Tag selection widget for interests and challenges
class TagSection extends StatefulWidget {
  final String title;
  final String hint;
  final Set<String> selectedTags;
  final List<String> suggestions;
  final VoidCallback onSave;

  const TagSection({
    super.key,
    required this.title,
    required this.hint,
    required this.selectedTags,
    required this.suggestions,
    required this.onSave,
  });

  @override
  State<TagSection> createState() => _TagSectionState();
}

class _TagSectionState extends State<TagSection> {
  final TextEditingController _customController = TextEditingController();

  @override
  void dispose() {
    _customController.dispose();
    super.dispose();
  }

  void _addCustomTag() {
    final value = _customController.text.trim();
    if (value.isNotEmpty && !widget.selectedTags.contains(value)) {
      setState(() {
        widget.selectedTags.add(value);
        _customController.clear();
      });
      widget.onSave();
    }
  }

  void _removeTag(String tag) {
    setState(() {
      widget.selectedTags.remove(tag);
    });
    widget.onSave();
  }

  void _addSuggestionTag(String tag) {
    if (!widget.selectedTags.contains(tag)) {
      setState(() {
        widget.selectedTags.add(tag);
      });
      widget.onSave();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        
        // Selected tags and suggestions
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            // Suggestion chips
            ...widget.suggestions.map((suggestion) {
              final isSelected = widget.selectedTags.contains(suggestion);
              return FilterChip(
                label: Text(suggestion),
                selected: isSelected,
                onSelected: (selected) {
                  if (selected) {
                    _addSuggestionTag(suggestion);
                  } else {
                    _removeTag(suggestion);
                  }
                },
                labelStyle: theme.textTheme.bodySmall,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                backgroundColor: theme.colorScheme.surfaceVariant.withOpacity(0.3),
              );
            }),
            // Custom added chips that aren't in suggestions
            ...widget.selectedTags.where((tag) => !widget.suggestions.contains(tag)).map((tag) {
              return FilterChip(
                label: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(tag),
                    const SizedBox(width: 4),
                    Icon(Icons.star, size: 12, color: theme.colorScheme.primary),
                  ],
                ),
                selected: true,
                onSelected: (selected) {
                  _removeTag(tag);
                },
                labelStyle: theme.textTheme.bodySmall,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                backgroundColor: theme.colorScheme.primaryContainer.withOpacity(0.3),
              );
            }),
          ],
        ),
        
        const SizedBox(height: 12),
        
        // Custom input
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _customController,
                decoration: InputDecoration(
                  hintText: 'Add custom ${widget.title.toLowerCase()}...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  filled: true,
                  fillColor: theme.colorScheme.surfaceVariant.withOpacity(0.2),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  isDense: true,
                ),
                textCapitalization: TextCapitalization.words,
                onSubmitted: (value) => _addCustomTag(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: _addCustomTag,
              icon: const Icon(Icons.add),
              style: IconButton.styleFrom(
                backgroundColor: theme.colorScheme.primary.withOpacity(0.1),
                foregroundColor: theme.colorScheme.primary,
              ),
            ),
          ],
        ),
      ],
    );
  }
}