# Universal Input Implementation Plan

**Date:** 2025-07-01  
**Priority:** High - Core MVP Feature  
**Status:** Planning Phase

## 1. Concept Overview

The Universal Input system replaces multiple explicit buttons ("Add Task", "Add Goal", etc.) with a single intelligent text input field. Users simply type what they're thinking, and AI classifies the intent and extracts structured data.

### Key Benefits
- **Intuitive UX**: Natural language interaction
- **Faster workflow**: No decision fatigue about what to create
- **Magical experience**: AI-powered intelligence
- **Reduced cognitive load**: Users think in natural language, not app structure

## 2. AI Classification System

### Intent Types
The AI will classify user input into four categories:

1. **Task** - Short, concrete actions
   - Example: "Finish quarterly report by Friday"
   - Characteristics: Specific, actionable, time-bound

2. **Goal** - Long-term, measurable aspirations  
   - Example: "Learn Spanish language"
   - Characteristics: Aspirational, measurable, ongoing

3. **Project** - Complex goals with multiple steps
   - Example: "Plan trip to Japan next spring"
   - Characteristics: Multi-step, complex, time-bounded

4. **Life Area** - High-level categories for organization
   - Example: "Work" or "Health and fitness"
   - Characteristics: Category, organizational, broad

### Entity Extraction
For each classified intent, AI extracts structured information:

```json
{
  "intent": "task",
  "title": "Finish quarterly report",
  "dueDate": "2025-07-04",
  "priority": "high",
  "tags": ["work", "reporting"],
  "estimatedDuration": 480,
  "context": "office work"
}
```

### AI Model Architecture
- **Primary Model**: GPT-4 or Claude for classification and extraction
- **Fallback**: Local model for offline/fast responses
- **Confidence Scoring**: Each classification includes confidence level
- **Ambiguity Handling**: System asks for clarification when uncertain

## 3. API Design

### New Endpoint: `/api/v1/parse-intent`

**Request:**
```json
{
  "text": "Finish quarterly report by Friday",
  "context": {
    "userId": "user_123",
    "currentDate": "2025-07-01",
    "timezone": "America/New_York"
  }
}
```

**Response:**
```json
{
  "intent": "task",
  "confidence": 0.95,
  "extracted_data": {
    "title": "Finish quarterly report",
    "dueDate": "2025-07-04",
    "priority": "high",
    "tags": ["work", "reporting"],
    "estimatedDuration": 480
  },
  "suggestions": [
    {
      "field": "priority",
      "options": ["low", "medium", "high"],
      "recommended": "high"
    }
  ],
  "ambiguities": []
}
```

**Ambiguous Response:**
```json
{
  "intent": "ambiguous",
  "confidence": 0.60,
  "possible_intents": [
    {
      "intent": "goal",
      "confidence": 0.60,
      "extracted_data": {...}
    },
    {
      "intent": "project", 
      "confidence": 0.55,
      "extracted_data": {...}
    }
  ],
  "clarification_question": "Is this a long-term goal or a specific project with steps?"
}
```

### Enhanced Creation Endpoints

Modify existing endpoints to accept parsed data:

**`POST /api/v1/tasks`** (Enhanced)
```json
{
  "title": "Finish quarterly report",
  "dueDate": "2025-07-04T17:00:00Z",
  "priority": "high",
  "tags": ["work", "reporting"],
  "estimatedDuration": 480,
  "source": "universal_input",
  "originalInput": "Finish quarterly report by Friday",
  "aiConfidence": 0.95
}
```

## 4. Frontend Implementation

### Universal Input Component

```dart
class UniversalInput extends StatefulWidget {
  final Function(ParsedIntent) onIntentParsed;
  final Function(String) onTextChanged;
  
  @override
  _UniversalInputState createState() => _UniversalInputState();
}
```

### User Flow

1. **Input Phase**
   - User types in universal input field
   - Real-time suggestions appear as they type
   - Debounced API calls to `/parse-intent`

2. **Confirmation Phase**
   - System shows parsed result with preview
   - "Create Task: 'Finish quarterly report' (Due: Friday). Correct?"
   - Options: [Yes, Create] [Edit] [Change Type]

3. **Creation Phase**
   - Confirmed data sent to appropriate endpoint
   - Success feedback with quick actions
   - Input field clears for next entry

### UI/UX Design

```
┌─────────────────────────────────────────┐
│ 💭 What's on your mind?                 │
│ ┌─────────────────────────────────────┐ │
│ │ Finish quarterly report by Friday  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 🎯 Creating Task:                       │
│ "Finish quarterly report"               │
│ Due: Friday, July 4                     │
│ Priority: High                          │
│                                         │
│ [✅ Create Task] [✏️ Edit] [🔄 Change]  │
└─────────────────────────────────────────┘
```

### State Management

```dart
// Universal Input State
class UniversalInputState {
  final String inputText;
  final ParsedIntent? parsedIntent;
  final bool isLoading;
  final String? error;
  final bool showConfirmation;
}

// Providers
final universalInputProvider = StateNotifierProvider<UniversalInputNotifier, UniversalInputState>();
final intentParsingProvider = Provider<IntentParsingService>();
```

## 5. Backend Implementation

### AI Service Integration

```python
class IntentClassificationService:
    def __init__(self):
        self.primary_model = OpenAIProvider()
        self.fallback_model = LocalProvider()
        
    async def classify_intent(self, text: str, context: dict) -> ParsedIntent:
        """Classify user intent and extract entities"""
        
        # Build enhanced prompt with context
        prompt = self._build_classification_prompt(text, context)
        
        try:
            # Primary AI model
            result = await self.primary_model.complete(prompt)
            return self._parse_ai_response(result)
        except Exception:
            # Fallback to local model
            return await self.fallback_model.classify(text)
    
    def _build_classification_prompt(self, text: str, context: dict) -> str:
        """Build context-aware prompt for classification"""
        return f"""
        Classify the following user input into one of these categories:
        - task: Short, concrete action (usually < 1 day)
        - goal: Long-term aspiration (weeks to months)
        - project: Complex goal with multiple steps
        - life_area: High-level category for organization
        
        User input: "{text}"
        Current date: {context['currentDate']}
        User timezone: {context['timezone']}
        
        Extract structured data and return JSON:
        {{
            "intent": "task|goal|project|life_area",
            "confidence": 0.0-1.0,
            "title": "extracted title",
            "dueDate": "ISO date if mentioned",
            "priority": "low|medium|high",
            "tags": ["extracted", "tags"],
            "estimatedDuration": minutes_if_applicable
        }}
        """
```

### Enhanced Prompt Templates

```python
# libs/prompts/intent_classification.py
INTENT_CLASSIFICATION_PROMPT = """
You are an intelligent task management assistant. Analyze user input and classify it into the most appropriate category.

Categories:
1. TASK - Concrete, actionable items (usually < 1 day)
   Examples: "Call dentist", "Send email to John", "Buy groceries"
   
2. GOAL - Long-term aspirations or objectives (weeks to months) 
   Examples: "Learn Spanish", "Lose 10 pounds", "Read 12 books this year"
   
3. PROJECT - Complex endeavors with multiple steps (days to weeks)
   Examples: "Plan wedding", "Renovate kitchen", "Launch new product"
   
4. LIFE_AREA - Organizational categories or life domains
   Examples: "Health", "Career", "Relationships", "Finance"

Context:
- Current date: {current_date}
- User timezone: {timezone}
- Time: {current_time}

User input: "{user_input}"

Extract and return JSON with high confidence:
{{
    "intent": "task|goal|project|life_area",
    "confidence": 0.0-1.0,
    "title": "clean, actionable title",
    "dueDate": "ISO date if mentioned or implied",
    "priority": "low|medium|high based on urgency cues",
    "tags": ["relevant", "tags", "from", "content"],
    "estimatedDuration": duration_in_minutes_if_extractable,
    "notes": "additional context or details"
}}

If ambiguous, set confidence < 0.7 and explain why.
"""
```

## 6. Implementation Timeline

### Phase 1: Core AI Classification (Week 1)
- [ ] Implement `IntentClassificationService`
- [ ] Create `/api/v1/parse-intent` endpoint
- [ ] Build enhanced prompts with context
- [ ] Add confidence scoring and ambiguity detection
- [ ] Unit tests for classification service

### Phase 2: Frontend Universal Input (Week 2)
- [ ] Create `UniversalInput` Flutter component
- [ ] Implement state management with Riverpod
- [ ] Build confirmation UI with preview
- [ ] Add edit and change type functionality
- [ ] Real-time suggestions and debouncing

### Phase 3: Integration & Polish (Week 3)
- [ ] Connect frontend to parse-intent API
- [ ] Enhance creation endpoints with AI metadata
- [ ] Add fallback handling for AI failures
- [ ] Implement offline mode with local classification
- [ ] Performance optimization and caching

### Phase 4: Testing & Refinement (Week 4)
- [ ] End-to-end testing of full flow
- [ ] A/B testing against traditional button interface
- [ ] User feedback collection and iteration
- [ ] Performance monitoring and optimization
- [ ] Documentation and training materials

## 7. Success Metrics

### Technical Metrics
- **Classification Accuracy**: >90% correct intent classification
- **Response Time**: <500ms for parse-intent API
- **Confidence Distribution**: >80% of classifications above 0.8 confidence
- **Error Rate**: <5% API failures with proper fallbacks

### User Experience Metrics
- **Task Creation Speed**: 50% faster than button-based interface
- **User Satisfaction**: >4.5/5 rating for natural language input
- **Adoption Rate**: >80% of users prefer universal input
- **Completion Rate**: >95% of parsed intents result in created items

### Business Metrics
- **Feature Usage**: Universal input used for >80% of item creation
- **User Retention**: Improved by >20% with AI-powered interface
- **Support Tickets**: Reduced by >30% due to intuitive interface
- **Time to Value**: New users create first item 60% faster

## 8. Risk Mitigation

### Technical Risks
- **AI Model Downtime**: Implement robust fallback with local model
- **Classification Errors**: Allow easy correction and learning
- **Performance Issues**: Cache common patterns, optimize prompts
- **Privacy Concerns**: Process sensitive data locally when possible

### User Experience Risks
- **Over-Engineering**: Maintain simple manual creation as backup
- **User Confusion**: Clear feedback and explanation of AI decisions
- **False Expectations**: Set proper expectations about AI capabilities
- **Accessibility**: Ensure screen readers and keyboard navigation work

## 9. Future Enhancements

### Advanced AI Features
- **Learning from Corrections**: Improve model based on user feedback
- **Personal Context**: Learn user patterns and preferences
- **Bulk Processing**: Handle multiple items in single input
- **Voice Input**: Integrate speech-to-text for hands-free operation

### Smart Suggestions
- **Related Items**: Suggest related tasks/goals during creation
- **Template Recognition**: Detect common patterns and suggest templates
- **Calendar Integration**: Intelligent scheduling based on availability
- **Priority Learning**: Learn user priority patterns over time

### Collaboration Features
- **Shared Context**: Understand team goals and projects
- **Assignment Detection**: Auto-detect when tasks should be assigned
- **Meeting Integration**: Extract action items from meeting notes
- **Email Integration**: Parse emails for tasks and deadlines

---

This Universal Input system represents a significant leap forward in user experience, transforming SelfOS from a traditional task manager into an intelligent personal assistant that understands natural language and intent.