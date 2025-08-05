# SelfOS Architecture Overview

**Version:** v1.0  
**Last Updated:** 2024-06-30  
**Status:** Comprehensive Review Complete

## System Overview

SelfOS is a modular, microservices-based personal AI assistant platform designed for conversational life planning, goal management, and memory retrieval. The system follows clean architecture principles with clear separation of concerns.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Services   │
│   (Flutter)     │◄──►│   (FastAPI)     │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │    │   Memory Store  │
                       │ (PostgreSQL)    │    │ (Vector DB)     │
                       └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Frontend Application (`apps/selfos/`)
- **Technology**: Flutter (Web, Mobile, Desktop)
- **State Management**: Riverpod (implemented)
- **Authentication**: Firebase + JWT with secure storage (implemented)
- **Features**: Authentication complete, Main app screens missing
- **Platform Support**: Android, iOS, macOS, Web, Windows, Linux

**Status**: ⚠️ Partially implemented - Authentication complete, core screens missing (MVP BLOCKER)

### 2. Backend API (`apps/backend_api/`)
- **Technology**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM + Automated archival system
- **Authentication**: Firebase Admin SDK + Multi-provider social login
- **Caching**: Redis for session, rate limiting, and API caching
- **API Documentation**: Auto-generated with OpenAPI/Swagger
- **Testing**: 87% coverage, 174 tests passing
- **Advanced Features**: RLHF data collection, AI integration, media management

**Status**: 🟢 Production-ready with comprehensive features

#### Key Endpoints:
```
Authentication:
├── POST /auth/register (Email + Social: Google, Apple, Facebook)
├── POST /auth/login (Multi-provider support)
├── POST /auth/forgot-password
└── GET /auth/me

Core Entities:
├── GET/POST/PUT/DELETE /api/goals/ (Goal management with progress tracking)
├── GET/POST/PUT/DELETE /api/tasks/ (Task management with dependencies)
├── GET/POST/PUT/DELETE /api/life_areas/ (Life categorization)
├── GET/POST/PUT/DELETE /api/media/ (File upload and management)
└── GET/POST/PUT/DELETE /api/preferences/ (User settings)

AI & Analytics:
├── POST /api/ai/* (AI service integration)
├── CRUD /api/assistant_profiles/ (AI personality customization)
├── POST /api/conversation/ (Intent classification & chat)
├── POST/GET /api/feedback/ (RLHF data collection)
├── POST/GET /api/stories/ (AI content generation)
└── GET /health (System monitoring)
```

### 3. AI Engine (`apps/ai_engine/`)
- **Technology**: Python with multiple AI provider support
- **Providers**: OpenAI GPT-4, Anthropic Claude, Local Mock
- **Features**: Goal decomposition, Conversational AI, Context awareness
- **Orchestration**: Provider-agnostic interface with fallback handling

**Status**: 🟢 Fully implemented

#### Architecture:
```python
AIOrchestrator
├── OpenAIProvider
├── AnthropicProvider
└── LocalMockProvider

PromptEngine
├── GoalDecompositionPrompts
├── ConversationPrompts
└── ContextualPrompts
```

### 4. Memory Service (`apps/ai_engine/memory/`)
- **Technology**: Vector databases for semantic search
- **Providers**: Pinecone, Weaviate, Local embeddings
- **Features**: RAG (Retrieval Augmented Generation), Long-term memory
- **Integration**: Seamless with AI conversations

**Status**: 🟢 Fully implemented

### 5. Shared Libraries (`libs/`)

#### Shared Models (`libs/shared_models/`)
- **Purpose**: Common data models across services
- **Technology**: Pydantic for validation
- **Models**: User, Goal, Task, MemoryItem, AI requests

#### Prompt Templates (`libs/prompts/`)
- **Purpose**: Centralized prompt management
- **Features**: Context-aware prompts, Provider-specific optimization
- **Templates**: Goal decomposition, Conversation, System prompts

**Status**: 🟢 Both fully implemented

### 6. Assistant Personalization System
- **Technology**: AI personality customization with multi-trait personality engine
- **Database**: JSON-based personality storage with performance indexes
- **Integration**: Seamlessly integrated with conversation and intent classification systems
- **Features**: Multi-assistant support, onboarding flow, real-time personality preview

**Status**: 🟢 Fully implemented

#### Core Features:
- **5-Trait Personality System**: Formality, Directness, Humor, Empathy, Motivation (0-100 scale)
- **Multi-Assistant Support**: Up to 5 custom assistants per user with default management
- **Temperature Control**: Separate settings for dialogue creativity and intent classification consistency
- **Language & Model Support**: 8 languages, multiple AI models (GPT-3.5/4, Claude 3)
- **Onboarding Flow**: Guided assistant creation with personality preview

#### Database Schema:
```sql
CREATE TABLE assistant_profiles (
    id UUID PRIMARY KEY,
    user_id VARCHAR REFERENCES users(uid),
    name VARCHAR NOT NULL,
    style JSON NOT NULL DEFAULT '{"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60}',
    dialogue_temperature FLOAT DEFAULT 0.8,
    intent_temperature FLOAT DEFAULT 0.3,
    ai_model VARCHAR DEFAULT 'gpt-3.5-turbo',
    language VARCHAR DEFAULT 'en',
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### API Endpoints:
```
/api/assistant_profiles/
├── POST /onboarding          (Guided assistant creation)
├── GET /config              (Supported languages/models)
├── POST /preview            (Personality style preview)
├── GET /default             (Default assistant profile)
├── GET /                    (List user's assistants)
├── POST /                   (Create new assistant)
├── GET /{id}               (Get specific assistant)
├── PATCH /{id}             (Update assistant)
└── DELETE /{id}            (Delete assistant)
```

## Data Architecture

### Database Schema

```sql
-- Core User Management
users
├── id (UUID, Primary Key)
├── email (String, Unique)
├── full_name (String)
├── hashed_password (String)
├── is_active (Boolean)
├── created_at (Timestamp)
└── updated_at (Timestamp)

-- Goal Management
goals
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key)
├── title (String)
├── description (Text)
├── status (Enum: draft, active, completed, archived)
├── target_date (Date, Nullable)
├── life_area_id (UUID, Foreign Key, Nullable)
├── created_at (Timestamp)
└── updated_at (Timestamp)

-- Task Management  
tasks
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key) 
├── goal_id (UUID, Foreign Key, Nullable)
├── title (String)
├── description (Text)
├── status (Enum: pending, in_progress, completed)
├── priority (Enum: low, medium, high)
├── due_date (Date, Nullable)
├── completed_at (Timestamp, Nullable)
├── created_at (Timestamp)
└── updated_at (Timestamp)

-- Memory & Context
memory_items
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key)
├── content (Text)
├── metadata (JSON)
├── embedding_vector (Vector, Nullable)
├── timestamp (Timestamp)
└── created_at (Timestamp)
```

### Performance Optimizations

#### Database Indexes
```sql
-- Composite indexes for common queries
CREATE INDEX ix_goals_user_created ON goals(user_id, created_at DESC);
CREATE INDEX ix_tasks_user_status ON tasks(user_id, status);
CREATE INDEX ix_tasks_due_date ON tasks(user_id, due_date) WHERE due_date IS NOT NULL;
CREATE INDEX ix_memory_user_timestamp ON memory_items(user_id, timestamp DESC);
```

#### Archival Strategy
- **High-volume tables**: `story_sessions`, `feedback_logs`
- **Retention policies**: 365 days for stories, 90 days for feedback
- **Archive tables**: Automatic migration with `manage_db.py`

## Security Architecture

### Authentication Flow
```
1. User Login → Backend validates credentials
2. Backend generates JWT token
3. Frontend stores token securely
4. All API calls include Bearer token
5. Backend validates token on each request
```

### Security Features
- **JWT Authentication**: Stateless, secure token-based auth
- **Password Hashing**: bcrypt with salt
- **Input Validation**: Pydantic models with strict validation
- **CORS Configuration**: Controlled cross-origin access
- **Rate Limiting**: API endpoint protection (planned)
- **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries

### Security Gaps (To Address)
- ❌ Input sanitization comprehensive review
- ❌ Rate limiting implementation  
- ❌ API security scanning
- ❌ Secrets management (HashiCorp Vault)

## Deployment Architecture

### Development Environment
```yaml
# docker-compose.yml
services:
  postgres:     # Database
  redis:        # Caching
  backend_api:  # FastAPI application
  frontend:     # Flutter web (planned)
```

### Production Architecture (Planned)
```
Internet
    │
┌───▼────┐
│  CDN   │ (Static assets)
└───┬────┘
    │
┌───▼────┐
│Load    │ (nginx/HAProxy)
│Balancer│
└───┬────┘
    │
┌───▼────┐    ┌─────────┐    ┌─────────┐
│Backend │    │Database │    │AI APIs  │
│Cluster │◄──►│Cluster  │    │(External)│
└────────┘    └─────────┘    └─────────┘
    │              │
┌───▼────┐    ┌───▼────┐
│Redis   │    │Vector  │
│Cluster │    │Store   │
└────────┘    └────────┘
```

## Integration Patterns

### AI Provider Integration
```python
# Provider-agnostic interface
class AIProvider:
    async def complete_conversation(self, request: ConversationRequest) -> ConversationResponse
    async def decompose_goal(self, request: GoalDecompositionRequest) -> GoalDecompositionResponse
    async def health_check(self) -> Dict[str, Any]

# Implementation example
class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
```

### Memory Integration
```python
# Vector database abstraction
class VectorStore:
    async def store_memory(self, content: str, metadata: Dict) -> str
    async def search_memories(self, query: str, limit: int = 10) -> List[MemoryItem]
    async def delete_memory(self, memory_id: str) -> bool

# RAG implementation
class MemoryService:
    async def enhance_conversation(self, message: str, user_id: str) -> ConversationContext:
        relevant_memories = await self.vector_store.search_memories(message)
        return ConversationContext(message=message, memories=relevant_memories)
```

## Performance Characteristics

### Current Performance
- **API Response Time**: 95th percentile < 1.5s
- **Database Query Time**: Average < 100ms
- **AI Provider Response**: 2-10s (depends on provider)
- **Memory Retrieval**: < 500ms for semantic search

### Scalability Targets
- **Concurrent Users**: 1,000+ (current), 10,000+ (target)
- **API Throughput**: 100 RPS (current), 1,000+ RPS (target)
- **Database**: 10M+ records with consistent performance
- **Memory Store**: 100M+ embeddings with sub-second search

## Monitoring & Observability (Planned)

### Application Metrics
- **Response times** per endpoint
- **Error rates** and status codes
- **AI API usage** and costs
- **Database performance** metrics

### Infrastructure Metrics
- **CPU/Memory utilization**
- **Database connection pooling**
- **Cache hit rates**
- **Network latency**

### Alerting Strategy
- **Critical**: API downtime, database failures
- **Warning**: High response times, AI API errors
- **Info**: Deployment notifications, usage milestones

## System Assessment & Future Improvements

### Current System Grade: B+ (85/100)

**Strengths:**
- ✅ Clean architecture with excellent separation of concerns
- ✅ Sophisticated AI integration with multi-provider support
- ✅ Comprehensive testing framework (87% coverage, 174 tests)
- ✅ Well-normalized database schema with proper indexing
- ✅ Strong type safety with Pydantic validation

**Critical Areas for Improvement:**

#### 1. Incomplete Service Implementations
- **Story Generation Service**: Architecture exists but pipeline incomplete
- **Progress Service**: Empty service file needs user analytics and insights
- **Notification Service**: Minimal implementation missing email/push capabilities

#### 2. Production Infrastructure Gaps
- **Monitoring & Observability**: No metrics, logging aggregation, or alerting
- **Security Hardening**: CORS marked for review, missing security audit
- **Backup & Recovery**: Archival exists but no backup strategy
- **Performance Optimization**: No caching strategy beyond AI responses

#### 3. Missing API Features
- **Real-time capabilities**: No WebSocket support for live updates
- **Bulk operations**: No import/export functionality
- **Analytics endpoints**: No user insights or progress tracking APIs
- **Calendar integration**: No external calendar sync

### Immediate Action Items (1-2 weeks)

#### Priority 1: Complete Core Services
```python
# services/progress.py
def calculate_user_stats(user_id: str) -> UserStats
def get_achievement_progress(user_id: str) -> List[Achievement]
def generate_weekly_report(user_id: str) -> WeeklyReport

# services/storytelling.py
def generate_story_content(session: StorySession) -> str
def create_social_media_post(story: str) -> SocialMediaPost
def process_story_media(story_id: str) -> MediaProcessingResult

# services/notifications.py
def send_email_notification(user_id: str, template: str, data: dict)
def schedule_reminder(user_id: str, task_id: str, reminder_time: datetime)
def send_push_notification(user_id: str, title: str, body: str)
```

#### Priority 2: Production Readiness
- **Monitoring Infrastructure**: Structured logging, health checks, metrics collection
- **Security Hardening**: Input validation audit, rate limiting, CORS review
- **Test Gaps**: Performance testing, security testing, end-to-end workflows

### Short-term Goals (1-2 months)

#### Infrastructure & DevOps
- **Docker production configuration** with multi-stage builds
- **CI/CD pipeline** with automated testing and deployment
- **Database backup strategy** with point-in-time recovery
- **Environment configuration management** (dev/staging/prod)

#### Feature Completions
- **Media processing pipeline** with thumbnail generation and compression
- **WebSocket support** for real-time notifications
- **Calendar integration** with Google Calendar and Outlook
- **Bulk operations** for data import/export

#### Performance & Scalability
- **Database query optimization** with query analysis
- **Caching strategy** beyond AI responses (Redis for session data)
- **Load testing** with realistic traffic patterns
- **Database connection pooling** optimization

### Long-term Vision (3-6 months)

#### Advanced AI Features
- **RLHF training pipeline** to improve responses from user feedback
- **Proactive AI suggestions** based on user patterns
- **Habit analysis** and behavioral insights
- **Goal prediction** and recommendation engine

#### Platform Features
- **Multi-tenant architecture** for teams and organizations
- **Advanced analytics** with business intelligence dashboards
- **Third-party integrations** (Obsidian, Todoist, etc.)
- **Mobile-first API optimizations** for Flutter frontend

#### Enterprise Features
- **Role-based access control** (RBAC)
- **Audit logging** for compliance
- **Data export compliance** (GDPR)
- **Single sign-on (SSO)** integration

### Technical Debt & Code Quality

#### Service Layer Extraction
```python
# Move business logic from routers to services
# Example: routers/goals.py → services/goal_service.py
class GoalService:
    def create_goal_with_ai_decomposition(self, goal_data: GoalCreate) -> Goal:
        # Business logic here, not in router
```

#### Configuration Management
```python
# Centralize configuration in config/settings.py
class Settings(BaseSettings):
    database_url: str
    ai_providers: Dict[str, ProviderConfig]
    notification_settings: NotificationConfig
```

### Success Metrics

#### Short-term (2 weeks)
- [ ] All service implementations have basic functionality
- [ ] Test coverage increases to 90%+
- [ ] All critical security issues addressed
- [ ] Production monitoring in place

#### Medium-term (2 months)
- [ ] Full feature parity with MVP requirements
- [ ] Load testing passes with 100+ concurrent users
- [ ] Zero-downtime deployment capability
- [ ] Comprehensive documentation complete

#### Long-term (6 months)
- [ ] Enterprise-ready with RBAC and compliance
- [ ] AI features show measurable user engagement improvement
- [ ] Platform supports 1000+ active users
- [ ] Third-party integration ecosystem established

### Technology Evolution Roadmap
- **Container Orchestration**: Kubernetes for production
- **Service Mesh**: Istio for microservices communication
- **Observability Stack**: Prometheus + Grafana + Jaeger
- **CI/CD Pipeline**: Advanced deployment strategies with GitOps

## Development Principles

### Code Organization
- **Clean Architecture**: Domain-driven design with clear boundaries
- **Dependency Injection**: Loose coupling between components
- **Interface Segregation**: Provider-agnostic abstractions
- **Single Responsibility**: Each module has one clear purpose

### Testing Strategy
- **Unit Tests**: 85%+ coverage for core business logic
- **Integration Tests**: End-to-end API testing
- **Contract Tests**: API interface validation
- **Performance Tests**: Load testing for critical paths

### Documentation Standards
- **API Documentation**: Auto-generated from code
- **Architecture Decisions**: ADR format for major decisions
- **Code Comments**: Focus on why, not what
- **Examples**: Comprehensive usage examples

---

This architecture supports the current MVP requirements while providing a foundation for future scalability and feature expansion.