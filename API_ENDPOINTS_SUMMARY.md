# SelfOS API Endpoints Summary

## Assistant Profile Endpoints

### Get All Assistant Profiles
```
GET /api/assistant_profiles
```

**Purpose**: Retrieves all assistant profiles for the authenticated user

**Authentication**: Required (uses `get_current_user` dependency)

**Response**: Returns a list of `AssistantProfileOut` schemas

**Note**: The client is responsible for filtering to find the default assistant (`is_default: true`). If no assistant is marked as default, the client should use the first one in the list.

**Example Response**:
```json
[
  {
    "id": "uuid-here",
    "name": "My Assistant",
    "avatar_url": "https://...",
    "style": {
      "formality": 50,
      "directness": 50,
      "humor": 30,
      "empathy": 70,
      "motivation": 60
    },
    "language": "en",
    "is_default": true,
    "is_public": false,
    // ... other fields
  },
  // ... more assistants if any
]
```

## Personal Profile Handling

The personal profile is now properly storing data in dedicated columns instead of stuffing everything into the `preferences` JSON field:

### Database Columns Used:
- `preferred_name` - User's preferred name
- `avatar_id` - Avatar reference
- `current_situation` - Current life situation (text)
- `interests` - List of interests (JSON array)
- `challenges` - List of challenges (JSON array)
- `aspirations` - List of aspirations (JSON array)
- `motivation` - What motivates them (text)
- `work_style` - Work style preference (string, max 50 chars)
- `communication_frequency` - How often they want updates (string, max 50 chars)
- `goal_approach` - How they approach goals (string, max 50 chars)
- `motivation_style` - What motivates them most (string, max 50 chars)
- `preferences` - ONLY for extra/custom preferences (JSON)
- `custom_answers` - Custom question answers (JSON)
- `selected_life_areas` - Selected life area IDs (JSON array)

### Design Note
All preference fields (`work_style`, `communication_frequency`, `goal_approach`, `motivation_style`) are strings rather than enums to allow maximum flexibility. Users can provide custom answers that aren't restricted to predefined choices. The `custom_answers` field is for additional questions/answers beyond the standard fields.

### Sync Support
Both `/api/sync/batch` and `/api/personal-config/profile` endpoints support all these fields properly.
