# SelfOS Documentation

This directory contains the comprehensive documentation for the SelfOS platform. The documentation is organized for clarity and maintainability.

## 📋 Documentation Overview

### Core Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[🚀 DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** | Complete development setup, commands, and workflows | Developers |
| **[📚 API_REFERENCE.md](API_REFERENCE.md)** | Complete API documentation with examples | API consumers, Frontend developers |
| **[🏗️ ARCHITECTURE.md](ARCHITECTURE.md)** | System design, components, and improvement roadmap | Technical architects, Senior developers |
| **[� BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md)** | Backend implementation details and model documentation | Backend developers |
| **[🔄 HIERARCHY_SYSTEM.md](HIERARCHY_SYSTEM.md)** | Hierarchical goals and projects implementation | Backend developers |

### Project Management

| Document | Purpose | Audience |
|----------|---------|----------|
| **[📅 MVP-2025-07.md](MVP-2025-07.md)** | MVP roadmap, status, and comprehensive technical assessment | Product managers, Stakeholders |
| **[🎯 UNIVERSAL_INPUT_PLAN.md](UNIVERSAL_INPUT_PLAN.md)** | AI-powered universal input system specification | Product managers, AI developers |

### Specialized Technical Docs

| Document | Purpose | Audience |
|----------|---------|----------|
| **[💾 DATABASE_OPTIMIZATION.md](DATABASE_OPTIMIZATION.md)** | Database performance, indexing, and archival strategies | Database administrators, Backend developers |
| **[🏃 HABITS_SYSTEM.md](HABITS_SYSTEM.md)** | Habits tracking and management system | Backend developers |
| **[📧 EMAIL_SERVICE.md](EMAIL_SERVICE.md)** | Email service implementation and configuration | Backend developers, DevOps |
| **[🤖 MCP_SERVER.md](MCP_SERVER.md)** | Model Context Protocol server documentation | AI developers, Integration developers |
| **[🛠️ TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common issues and debugging procedures | All developers, DevOps |

## 🚀 Quick Start

1. **New to the project?** → Start with [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. **Need API information?** → Check [API_REFERENCE.md](API_REFERENCE.md)
3. **Understanding the system?** → Read [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Working on backend?** → Review [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md)
5. **Having issues?** → Consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📊 Current System Status

### Core Features Implemented
- ✅ **Authentication**: Firebase-based user authentication
- ✅ **User Management**: User profiles and preferences
- ✅ **Goals System**: SMART goals with hierarchical structure
- ✅ **Projects System**: Project management with life area associations
- ✅ **Tasks System**: Task tracking with dependencies
- ✅ **Life Areas**: Personal life categorization
- ✅ **Habits Tracking**: Habit creation and monitoring
- ✅ **Journal System**: Personal reflection and documentation
- ✅ **Story Sessions**: Content generation and storytelling
- ✅ **Media Attachments**: File upload and management
- ✅ **Entity Knowledge Graph**: Automatic entity extraction and relationships
- ✅ **MCP Server**: AI integration through Model Context Protocol

### Backend Architecture
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic for schema management
- **Authentication**: Firebase Admin SDK
- **Caching**: Redis for session storage
- **Testing**: pytest with 85+ passing tests

## 🔄 Recent Updates (August 2025)

### 🛠️ Critical Stabilization Fixes (Branch: stabilization-20250821)
- **✅ Resolved Critical Import Errors**
  - Created centralized `models/associations.py` to break circular dependencies
  - Fixed SQLAlchemy association table imports across all models
  - Eliminated 146+ import-related test failures

- **✅ Synchronized Coverage Configuration**
  - Aligned coverage targets to 75% across pytest.ini and pyproject.toml
  - Fixed CI pipeline coverage inconsistencies
  - Standardized test configuration parameters

- **✅ Created Missing Service Dependencies**
  - Added `services/habit_service.py` with complete CRUD operations
  - Added `services/journal_service.py` with entry management and search
  - Added `services/tag_service.py` with tag associations and statistics
  - Resolved service layer dependencies for all models

- **✅ Fixed SQLAlchemy Relationship Issues**
  - Resolved relationship ambiguity in User and AssistantProfile models
  - Added explicit foreign_keys parameters to eliminate warnings
  - Enhanced model relationship definitions for better ORM performance

- **✅ Updated Test Expectations**
  - Fixed test_api_structure to handle 422 response codes
  - Updated main API tests (5/5 passing)
  - Improved test isolation and module execution

### System Enhancements
- **Added Entity Knowledge Graph** (migration 017)
  - Automatic entity extraction from user content
  - Relationship detection and importance scoring
  - Support for people, places, organizations, dates
  - Integration with goals, projects, and tasks

### Code Organization
- **Modularized Models**: Split models.py into domain-specific modules
  - `models/user.py`: User and authentication
  - `models/goals.py`: Goals management
  - `models/projects.py`: Project management
  - `models/tasks.py`: Task tracking
  - `models/life_areas.py`: Life area categorization
  - `models/habits.py`: Habit tracking
  - `models/journal.py`: Journal entries
  - `models/entities.py`: Knowledge graph entities
  - `models/assistant.py`: AI assistant configurations
  - `models/feedback.py`: User feedback tracking
  - `models/media.py`: Media attachments
  - `models/memory.py`: Memory and conversation storage
  - `models/preferences.py`: User preferences
  - `models/story.py`: Story generation sessions
  - `models/content.py`: Content management
  - `models/associations.py`: **NEW** - Centralized association tables

### Project Cleanup
- ✅ Removed temporary test files and scripts
- ✅ Removed UI/Flutter app (to be rebuilt)
- ✅ Cleaned Python cache and compiled files
- ✅ Updated .gitignore for better exclusions
- ✅ Consolidated documentation

## 📝 Contributing to Documentation

### Guidelines
1. **Update existing documents** rather than creating new ones
2. **Maintain clear, concise writing** with practical examples
3. **Include code examples** for technical implementations
4. **Cross-reference related sections** for better navigation
5. **Test all code examples** before documenting them

### Document Structure
- Use clear headings with emoji for visual scanning
- Include table of contents for longer documents
- Provide both conceptual explanations and practical examples
- Include troubleshooting sections where applicable

### Maintenance
- Review and update documentation with each major release
- Validate all links and references quarterly
- Update status badges and metrics regularly
- Gather feedback from document users for improvements

## � Test Status Summary

### Current Status (Post-Stabilization)
- **✅ Main API Tests**: 5/5 passing (100%)
- **✅ Critical Import Errors**: Resolved
- **✅ Coverage Configuration**: Synchronized at 75%
- **⚠️ Remaining Test Failures**: 57/215 tests (mostly unit/integration edge cases)

### Test Categories
| Category | Status | Notes |
|----------|--------|-------|
| **Main API** | ✅ 5/5 passing | Core endpoints functional |
| **Import System** | ✅ Resolved | Circular dependencies fixed |
| **Unit Tests** | ⚠️ Partial failures | Edge cases and mock dependencies |
| **Integration Tests** | ⚠️ Partial failures | Complex workflow scenarios |
| **Coverage** | ✅ Synchronized | 75% target across all configs |

## 🔮 Next Steps

### Immediate Priorities
1. **Address remaining unit test failures** (~45 remaining)
2. **Fix integration test edge cases** (~12 remaining)
3. **Complete MCP tools** for Projects and Tasks
4. **Implement AI Engine** with LangChain integration
5. **Add Memory/RAG system** with vector embeddings

### Technical Debt Resolution
- Migrate Pydantic V1 validators to V2 style (`@field_validator`)
- Update FastAPI event handlers to lifespan pattern
- Upgrade SQLAlchemy to 2.0+ patterns
- Address deprecation warnings in test output

### Future Development
- Rebuild Flutter frontend application
- Implement real-time notifications
- Add social media integrations
- Deploy production infrastructure

---

*This documentation structure supports both new contributors getting started quickly and experienced developers finding detailed technical information efficiently.*
