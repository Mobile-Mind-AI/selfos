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
- **Media-Aware Task Management**: Attach sketches, videos, and audio to any task or project.
- **Proactive Coaching**: Get nudges when an area is neglected, or energy/motivation shifts.
- **Personal Memory Engine**: Remembers what matters to *you* — from routines to dreams.
- **Narrative & Video Storytelling**: Auto-generates story scripts and short videos of your project journeys.
- **Integrated Social Sharing**: Export stories directly to TikTok, Instagram, YouTube.
- **Self-Improving AI**: Learns from your preferences, habits, and feedback.

---

## 🆚 Comparative Advantages

| Feature                            | SelfOS                          | Traditional Planners        | AI Productivity Tools      |
|-----------------------------------|----------------------------------|-----------------------------|----------------------------|
| Deep Personalization              | ✅ Life areas, mood, habits       | ❌ Static priorities         | ⚠️ Some learning            |
| Rich Media Task Integration       | ✅ Attach images, videos, audio   | ❌ Notes only                | ⚠️ Few apps support media   |
| Automated Storytelling            | ✅ Narratives + video generator   | ❌ Manual summaries          | ❌ No native storytelling    |
| AI Memory & Long-Term Recall      | ✅ Vector-based memory            | ❌ None                      | ⚠️ Short context only        |
| Social-Ready Outputs              | ✅ Auto-generated + post-ready    | ❌ Not applicable            | ⚠️ Rare or basic             |
| Proactive Suggestions             | ✅ Event-driven, context-aware    | ❌ User-initiated only       | ⚠️ Limited context           |
| RLHF Personal AI Engine           | ✅ Custom LLM fine-tuning option  | ❌ N/A                       | ⚠️ Generalized LLMs          |

---

## 🏗 High-Level Architecture

```
User ↔️ Flutter Frontend (Web/Mobile/Desktop)
             ↓
        API Gateway
             ↓
├── Task & Life Manager
├── Personalization Engine
├── AI Engine (Claude/GPT + Local LLM)
├── Memory Engine (RAG + Pinecone)
├── Storytelling Engine (Narrative + Media)
├── Email Service (SMTP + Templates)
├── Notification Service
├── RLHF Trainer (Phase 3+)
└── Integrations (Calendar, Obsidian, Trello, Social APIs)
             ↓
     Persistence Layer
(PostgreSQL, MongoDB, S3, Redis, Vector DB)
             ↓
      Event Bus (Kafka/Redis Streams)
```

> 📁 See `docs/components/` for detailed breakdowns of each service, their APIs, and design decisions.

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Docker & Docker Compose installed
- (Optional) Python 3.11+ for running backend tests locally
- Firebase service account JSON – obtain credentials as described in [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md)
- (Optional) SMTP credentials for email functionality – see [docs/EMAIL_SERVICE.md](docs/EMAIL_SERVICE.md)

### Start Services
```bash
# Before starting, set Firebase service account (required for auth):
# export GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json
#
# Build and run DB, Redis, and Backend API
docker-compose up --build

# (Frontend is in 'frontend' profile – activate it when ready)
docker-compose --profile frontend up --build
```

### API Health Check
```bash
curl http://localhost:8000/
```  
Expected: { "message": "SelfOS Backend API" }

### Run Backend Tests
```bash
cd apps/backend_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

---
## 🛠 Get Involved
We’re building something deeply meaningful. If you’re a:
- Developer who believes AI should reflect *humans*, not replace them
- Designer who values beauty, emotion, and clarity
- Creator who wants to show their journey — not just their results

Join us.


