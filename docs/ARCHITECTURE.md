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

## Future Architecture Considerations

### Planned Enhancements
1. **Microservices Decomposition**: Split monolithic backend
2. **Event-Driven Architecture**: Async processing with message queues
3. **Multi-tenant Support**: Isolated data per organization
4. **Real-time Features**: WebSockets for live updates
5. **Advanced Caching**: Multi-layer caching strategy

### Technology Evolution
- **Container Orchestration**: Kubernetes for production
- **Service Mesh**: Istio for microservices communication
- **Observability Stack**: Prometheus + Grafana + Jaeger
- **CI/CD Pipeline**: Advanced deployment strategies

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