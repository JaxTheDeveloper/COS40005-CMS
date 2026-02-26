# Sprint 4: UML Diagrams & Architecture Visualizations

## Overview

This document provides comprehensive UML and architecture diagrams for the AI-Driven Event Refinement System implemented in Sprint 4.

---

## 📊 Diagram Index

### 1. System Architecture Diagram
**File**: `sprint4_system_architecture.puml`

**Purpose**: Shows the complete system components and their interactions.

**Components Visualized**:
- **Frontend Layer**: React App, EventRefinementChatbot, StaffEventManager
- **API Gateway**: Django REST Framework with JWT authentication
- **Business Logic Endpoints**:
  - `import_csv()` - Public (no auth) CSV upload endpoint
  - `refine_chatbot()` - Authenticated, routes to n8n
  - `apply_suggestion()` - Authenticated, persists refinements
- **Orchestration Layer**: N8N workflows (CSV pipeline ✅, Refinement workflow 🔄)
- **AI Integration**: Groq API (llama-3.3-70b-versatile)
- **Data Layer**: PostgreSQL 18, Event model with JSONB, Redis cache

**Key Connections**:
- Frontend communicates with Django via REST (JWT Bearer tokens)
- Django forwards refinement requests to n8n webhooks
- N8N calls Groq LLM and returns results to Django callback
- All database operations persisted to PostgreSQL

---

### 2. Deployment Architecture Diagram
**File**: `sprint4_deployment_architecture.puml`

**Purpose**: Shows Docker containerization, networking, and volume management.

**Infrastructure Elements**:
- **Docker Host (Windows)**: Contains all containers
- **Docker Bridge Network (`postgres`)**: Internal DNS resolution
  - `cos40005_backend:8000` (Django)
  - `cos40005_postgres:5432` (PostgreSQL)
  - `cos40005_n8n:5678` (N8N)
  - `cos40005_redis:6379` (Redis)
  - `cos40005_pgadmin:5050` (Admin UI)
- **Volumes**:
  - `n8n_data`: Persists workflow configurations
  - `postgres_data`: Persists database
- **Port Bindings**: 8000, 5678, 5050, 3000 exposed to host
- **Critical Configuration**: Host header override in n8n HTTP node to bypass Django ALLOWED_HOSTS validation

**Network Communication**:
- Frontend (React Dev) → Backend API (HTTP + JWT)
- Backend ↔ N8N: Webhook POST with Host override
- N8N → Groq API: HTTPS (external, via API key)
- Backend ↔ PostgreSQL: psycopg2 ORM
- Backend ↔ Redis: Session/cache store

---

### 3. Use Cases Diagram
**File**: `sprint4_usecases.puml`

**Purpose**: Captures all user interactions and system behaviors from business perspective.

**Primary Actors**:
- **Staff User**: Event refinement workflows
- **System Admin**: Workflow management, configuration

**Secondary Actors**:
- **N8N Workflow Engine**: Orchestration
- **Groq LLM Service**: Content generation

**Key Use Cases**:

#### Direct Edit Path (Immediate)
1. Staff views event table
2. Clicks "Refine" button
3. Modal opens with EventRefinementChatbot
4. Selects "Direct Edit" mode
5. Types content directly in tab
6. Sees real-time preview
7. Clicks "Apply" → Event updated (no LLM)
8. **Latency**: <200ms

#### AI Suggestions Path (LLM-Powered)
1. Same steps 1-4 as above
2. Selects "AI Suggestions" mode
3. Enters refinement prompt ("Make engaging for PhD researchers")
4. Clicks "Generate Suggestions"
5. System triggers n8n → Groq LLM
6. Receives 3 alternatives
7. Reviews preview options
8. Selects best suggestion
9. Clicks "Apply"
10. **Latency**: 15-20 seconds (dominated by Groq inference)

#### CSV Bulk Import Path
1. Admin/Staff uploads CSV file
2. N8N workflow triggered via webhook
3. extractFromFile node parses CSV
4. Data validated and transformed
5. Bulk INSERT creates Events
6. Response shows imported count
7. Events appear in dashboard

---

### 4. Sequence Diagram - Refinement Flow
**File**: `sprint4_refinement_sequence.puml`

**Purpose**: Detailed time-sequenced interaction for AI suggestions workflow.

**Actors**:
- Staff UI (React component)
- Django Backend API
- N8N Workflow Engine
- Groq LLM API
- PostgreSQL Database

**Step-by-Step Flow**:

1. **UI Interaction** (t=0ms)
   - Staff clicks "Refine" → Opens modal
   - Selects "AI Suggestions" mode
   - Enters prompt: "Make engaging for PhD"
   - Clicks "Generate"

2. **Request to Backend** (t=0-10ms)
   - React sends: `POST /api/core/events/42/refine-chatbot/`
   - Payload: `{refinement_type: "prompt", content: "...", field_name: "social_post_en"}`

3. **Backend Processing** (t=10-50ms)
   - Django validates JWT token (IsAuthenticated)
   - Validates event exists
   - Validates field_name in whitelist
   - Prepares n8n webhook payload with callback URL

4. **N8N Orchestration** (t=50-100ms)
   - N8N receives webhook
   - Conditional IF node routes to LLM path (refinement_type == "prompt")
   - LangChain agent formatted with system prompt

5. **Groq LLM Inference** (t=100-15100ms - **dominant latency**)
   - N8N calls: `POST https://api.groq.com/openai/v1/chat/completions`
   - Request: `{model: "llama-3.3-70b-versatile", messages: [...], temperature: 0.8, n: 3}`
   - Groq processes and returns 3 suggestions (~15-20 seconds)

6. **Result Processing** (t=15100-15200ms)
   - N8N extracts 3 suggestions from Groq response
   - Formats as array: `["Alternative 1", "Alternative 2", "Alternative 3"]`

7. **Callback to Backend** (t=15200-15250ms)
   - N8N posts: `POST /api/core/events/42/apply-suggestion/`
   - Payload includes suggestions array

8. **Backend Database Update** (t=15250-15300ms)
   - Django updates: `UPDATE events SET generated_content = JSONB, generation_status = 'completed'`
   - Single atomic transaction
   - Returns updated event as JSON

9. **Frontend Display** (t=15300-15400ms)
   - React receives suggestions
   - Stops loading spinner
   - Renders 3 suggestion cards

10. **Staff Selection** (t>15400ms - User time)
    - Staff reviews alternatives
    - Clicks card #2: "Explore cutting-edge research..."
    - Clicks "Apply Suggestion"
    - Closes modal

**Total Latency**: ~20-25 seconds (mostly Groq inference)

---

### 5. Frontend Mockup
**File**: `sprint4_frontend_mockup.puml`

**Purpose**: Visual wireframe of EventRefinementChatbot component UI.

**Layout**:
```
┌─ MODAL DIALOG ─────────────────────────────────┐
│ Event Refinement Chatbot - Research Summit 2026 │ [X]
├─────────────────────────────────────────────────┤
│                                                 │
│ Refinement Mode:                               │
│ [●] Direct Edit    [ ] AI Suggestions          │
│                                                 │
├─────────────────────────────────────────────────┤
│ Content Tabs:                                  │
│ social_post_en | social_post_vn | email... >  │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─ TEXT EDITOR (Direct Edit Mode) ──────────┐ │
│ │ Join us for groundbreaking research...    │ │
│ │ on AI ethics and sustainable technology!  │ │
│ │ Limited seats available. Register now.    │ │
│ │                                            │ │
│ │ [Char count: 89/500]                     │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ REAL-TIME PREVIEW ────────────────────────┐ │
│ │ 📱 Social Media Post                       │ │
│ │ Join us for groundbreaking research...    │ │
│ │ on AI ethics and sustainable technology!  │ │
│ │ Limited seats available. Register now.    │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ [Apply to Event] [Clear] [Publish] [Cancel]    │
│                                                 │
└─────────────────────────────────────────────────┘

AI SUGGESTIONS MODE (Alternative View):
┌─────────────────────────────────────────────────┐
│ Enter Refinement Prompt:                        │
│ [Make this more engaging for PhDs............]  │
│                                                 │
│          [Generate Suggestions ▶]             │
│                                                 │
│ ⟳ Loading... (15-20 seconds)                  │
│                                                 │
│ ┌─ Alternative 1 ────────────────────────────┐ │
│ │ Connect with elite researchers...         │ │
│ │ [Select] [Preview]                        │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ Alternative 2 (✓ Selected) ───────────────┐ │
│ │ Explore cutting-edge research...          │ │
│ │ [Select] [Preview]                        │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ Alternative 3 ────────────────────────────┐ │
│ │ Be part of groundbreaking work...         │ │
│ │ [Select] [Preview]                        │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ [Apply] [Regenerate] [Cancel]                 │
└─────────────────────────────────────────────────┘
```

**Component Features**:
- **Mode Toggle**: Direct Edit vs. AI Suggestions
- **6 Content Tabs**: social_post_en, social_post_vn, email_body_en, email_body_vn, article_body_en, article_body_vn
- **Real-time Preview**: Updates as staff types (Direct) or selects (AI)
- **Suggestion Cards**: Grid layout with selection state
- **Action Buttons**: Apply, Clear, Publish, Cancel, Regenerate
- **Character Counter**: Shows usage for direct edit
- **Loading State**: Spinner during Groq API call

---

### 6. Data Flow Diagram
**File**: `sprint4_dataflow.puml`

**Purpose**: Shows data transformation through system from input to output.

**Data Flow Stages**:

1. **Input Sources**
   - CSV file (multipart upload)
   - Refinement prompt (text input)
   - Direct edit content (text input)

2. **Validation & Routing** (Processes 1-5)
   - Parse CSV → extractFromFile node
   - Validate rows, columns
   - Transform to Event model
   - Route based on refinement type (prompt vs. direct)
   - Validate JWT token

3. **Conditional LLM Processing** (Processes 6-8)
   - **If prompt mode**: Call Groq API with prompt + context
   - **If direct mode**: Skip LLM, pass through
   - Generate 3 alternatives (prompt) or return single content (direct)
   - Format response

4. **Persistence** (Processes 9-10)
   - Update Event.generated_content JSONB field
   - Set generation_status to 'completed'
   - Write to PostgreSQL (atomic transaction)

5. **Response & Display** (Processes 11+)
   - Serialize Event to JSON
   - Return API response
   - Update Frontend state
   - Display to staff

**Data Stores**:
- PostgreSQL Event Table: Primary persistence
- Redis Cache: JWT token validation, session storage

---

## 🔄 How to View These Diagrams

### Option 1: PlantUML Online Editor
1. Visit: https://www.plantuml.com/plantuml/uml/
2. Copy content from any `.puml` file
3. Paste into editor
4. View rendered diagram

### Option 2: VS Code PlantUML Extension
1. Install: "PlantUML" extension (jebbs.plantuml)
2. Open any `.puml` file
3. Use: Alt+D to preview
4. Export as PNG/SVG if needed

### Option 3: Docker PlantUML Server
```bash
docker run -d -p 8080:8080 plantuml/plantuml-server:latest
# Access: http://localhost:8080/uml/
```

---

## 📝 Integration with Sprint Report

These diagrams directly support sections:

| Diagram | Section | Purpose |
|---------|---------|---------|
| System Architecture | Updated Architecture | Show component relationships |
| Deployment | N8N + Backend | Illustrate containerization |
| Use Cases | Sprint Demonstration | Document user workflows |
| Sequence | Refinement Flow | Detail API interactions |
| Mockup | Frontend | Visualize UI/UX |
| Data Flow | APIs | Show data transformation |

---

## 🚀 Viewing All Diagrams

**Generate PNG exports from all files**:
```bash
# Requires PlantUML CLI installed
for file in sprint4_*.puml; do
  plantuml "$file" -o ../diagrams
done
```

**Include in documentation**:
Each `.puml` file can be embedded in Markdown using image references or PlantUML plugin.

---

**Created**: January 25, 2026  
**Project**: COS40005 CMS - AI Event Refinement System  
**Sprint**: 4  
**Status**: Complete ✅
