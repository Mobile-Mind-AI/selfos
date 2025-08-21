# SelfOS – Your Personalized Life Operating System

> **Mission:** Empower individuals to live intentionally by turning their goals, values, and dreams into actionable, trackable, and emotionally rewarding experiences.

> **Vision:** Build the world's most adaptive personal assistant — one that listens like a friend, thinks like a strategist, creates like an artist, and evolves alongside you. A true second brain with a soul.

> **Core Values:**
- **Human-Centered AI**: AI should augment personal meaning, not replace it.
- **Radical Personalization**: Everyone's life rhythm, goals, and identity are unique.
- **Wholeness Over Hustle**: Success is measured in joy, balance, and growth — not just tasks.
- **Transparency**: You control your data, stories, and experience.
- **Creativity as Output**: Your progress becomes inspiration — in beautiful, shareable form.

---

## 🚀 Main Features

- **Conversational Life Planning**: Set goals and dreams through natural chat. The AI breaks them down into structured, adaptable tasks.
- **Life Area Balance**: Define your core values (e.g., Health, Relationships, Creativity) and track balance across them.
- **Hierarchical Project Management**: Organize with Life Areas → Projects → Goals → Tasks structure.
- **Media-Aware Task Management**: Attach sketches, videos, and audio to any task or project.
- **AI Integration via MCP**: Standardized Model Context Protocol server for seamless AI agent interactions.
- **Proactive Coaching**: Get nudges when an area is neglected, or energy/motivation shifts.
- **Personal Memory Engine**: Remembers what matters to *you* — from routines to dreams.
- **Narrative & Video Storytelling**: Auto-generates story scripts and short videos of your project journeys.
- **Integrated Social Sharing**: Export stories directly to TikTok, Instagram, YouTube.
- **Self-Improving AI**: Learns from your preferences, habits, and feedback.

---

## 🏗 High-Level Architecture

```
        API Gateway (FastAPI)
             ↓
├── Backend API (Core CRUD & Business Logic)
├── MCP Server (Model Context Protocol for AI Integration)
├── AI Engine (Claude/GPT + Local LLM)
├── Memory Engine (RAG + Vector Embeddings)
├── Storytelling Engine (Narrative + Media)
├── Email Service (SMTP + Templates)
├── Notification Service
└── Integrations (Calendar, Obsidian, Trello, Social APIs)
             ↓
     Persistence Layer
(PostgreSQL, Redis, Weaviate Vector DB)
             ↓
      Event Bus (Redis Streams)
```

> 📁 See `docs/` for detailed breakdowns of each service, their APIs, and design decisions.

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Docker & Docker Compose installed
- Python 3.11+ for running backend tests locally
- Firebase service account JSON – obtain credentials as described in `docs/DEVELOPER_GUIDE.md`

### Start Services
```bash
# Before starting, set Firebase service account (required for auth):
# export GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json

# Start core services (DB, Redis, Backend API)
docker-compose up --build

# Or use the convenience script:
./start-services.sh
```

### Health Checks
```bash
# Backend API
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# MCP Server (if running)
curl http://localhost:8001/health
# Expected: {"status": "healthy", "server": "selfos-mcp-server"}
```

### Run Backend Tests
```bash
cd apps/backend_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_tests.py
```

### Quick Reference
- **👨‍💻 [Developer Guide](docs/DEVELOPER_GUIDE.md)** - Comprehensive development instructions
- **🤖 [MCP Server Documentation](docs/MCP_SERVER.md)** - AI integration details
- **📚 [API Reference](docs/API_REFERENCE.md)** - API endpoints and schemas

---
## 🛠 Get Involved
We’re building something deeply meaningful. If you’re a:
- Developer who believes AI should reflect *humans*, not replace them
- Designer who values beauty, emotion, and clarity
- Creator who wants to show their journey — not just their results

Join us.
