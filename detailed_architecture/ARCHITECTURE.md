# RTFM Discord Bot - System Architecture

**Task:** Design system architecture  
**Time Estimate:** 2 hours  
**Priority:** High - Foundation for entire project  
**Status:** ✅ Complete

---

## 📋 Deliverables Checklist

- ✅ Architecture diagram showing all services
- ✅ Document data flow
- ✅ Define service boundaries
- ✅ Discord Bot (listener + responder)
- ✅ Query Service (Kafka consumer + DB queries)
- ✅ Response Generator (Gemini integration)

---

## 🏗️ System Architecture Diagram

### Current Architecture (MVP - Simple)

```
┌────────────────────────────────────────────────────────────┐
│                    Discord Server                          │
│  (User types: "RTFM when is the meeting?")               │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────┐
│              Discord Bot Container                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  1. Listener (bot.py)                               │  │
│  │     - Captures all messages                         │  │
│  │     - Detects trigger phrase "RTFM"                 │  │
│  │     - Stores messages in ChromaDB                   │  │
│  └─────────────────┬───────────────────────────────────┘  │
│                    │                                        │
│  ┌─────────────────▼───────────────────────────────────┐  │
│  │  2. Query Service (database.py)                     │  │
│  │     - Generates embeddings                          │  │
│  │     - Performs similarity search                    │  │
│  │     - Retrieves top K relevant messages             │  │
│  └─────────────────┬───────────────────────────────────┘  │
│                    │                                        │
│  ┌─────────────────▼───────────────────────────────────┐  │
│  │  3. Response Generator (bot.py)                     │  │
│  │     - Formats context from search results           │  │
│  │     - Calls Google Gemini API                       │  │
│  │     - Generates natural language response           │  │
│  └─────────────────┬───────────────────────────────────┘  │
│                    │                                        │
│  ┌─────────────────▼───────────────────────────────────┐  │
│  │  4. Responder (bot.py)                              │  │
│  │     - Sends response back to Discord                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Embedded ChromaDB                                   │ │
│  │  - Vector embeddings storage                         │ │
│  │  - Metadata (username, timestamp)                    │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────┐
│              External Services                              │
│  ┌───────────────────────┐  ┌──────────────────────────┐  │
│  │  Google Gemini API    │  │  HuggingFace Models      │  │
│  │  - Response generation│  │  - Sentence embeddings   │  │
│  └───────────────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### Future Architecture (Microservices - 6 Week Goal)

```
┌────────────────────────────────────────────────────────────────┐
│                       Discord Servers                           │
│              (Multiple guilds/servers supported)                │
└────────────────────┬───────────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────────┐
│                    SERVICE 1: Discord Bot                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Responsibilities:                                        │  │
│  │  • Listen to Discord messages                            │  │
│  │  • Detect trigger phrases                                │  │
│  │  • Publish messages to Kafka                             │  │
│  │  • Receive responses from Kafka                          │  │
│  │  • Send responses to Discord                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────────┘
                     │
                     ↓ (publish to Kafka)
┌────────────────────────────────────────────────────────────────┐
│               INFRASTRUCTURE: Kafka + Zookeeper                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Topics:                                                  │  │
│  │  • discord_messages      - Raw messages from Discord     │  │
│  │  • discord_embeddings    - Embedding generation tasks    │  │
│  │  • discord_responses     - Generated responses           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬──────────────────────────────────────┬───────────────┘
          │                                      │
          │                                      │
          ↓ (consume)                            ↓ (consume)
┌──────────────────────────┐          ┌──────────────────────────┐
│  SERVICE 2:              │          │  SERVICE 3:              │
│  Embedding Worker        │          │  Indexing Worker         │
│  ┌────────────────────┐  │          │  ┌────────────────────┐  │
│  │ Responsibilities:  │  │          │  │ Responsibilities:  │  │
│  │ • Consume messages │  │          │  │ • Consume embeddings│ │
│  │ • Generate vectors │  │          │  │ • Store in ChromaDB│ │
│  │ • Publish to Kafka │  │          │  │ • Update metadata  │ │
│  └────────────────────┘  │          │  │   in PostgreSQL    │ │
│                          │          │  └────────────────────┘  │
│  (Scalable: 3+ workers) │          │  (Scalable: 2+ workers) │
└──────────┬───────────────┘          └───────────┬──────────────┘
           │                                      │
           │                                      │
           ↓                                      ↓
┌──────────────────────────────────────────────────────────────────┐
│                    SERVICE 4: Query Service                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Responsibilities:                                          │  │
│  │  • Listen for query requests (via Kafka)                   │  │
│  │  • Generate query embeddings                               │  │
│  │  • Perform similarity search in ChromaDB                   │  │
│  │  • Check Redis cache first                                 │  │
│  │  • Retrieve guild-specific context from PostgreSQL         │  │
│  │  • Publish results to Response Generator                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│              SERVICE 5: Response Generator                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Responsibilities:                                          │  │
│  │  • Consume query results from Kafka                        │  │
│  │  • Format context for Gemini API                           │  │
│  │  • Call Google Gemini API                                  │  │
│  │  • Cache responses in Redis                                │  │
│  │  • Publish response to Kafka                               │  │
│  │  • Bot service consumes and sends to Discord               │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ PostgreSQL   │  │   Redis      │  │      ChromaDB          │ │
│  │              │  │              │  │                        │ │
│  │ • Guild info │  │ • Query cache│  │ • Vector embeddings    │ │
│  │ • Configs    │  │ • Response   │  │ • Message content      │ │
│  │ • Metadata   │  │   cache      │  │ • Timestamps           │ │
│  │ • Usage logs │  │ • Session    │  │ • Metadata             │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                  MONITORING LAYER                                 │
│  ┌──────────────────────┐      ┌──────────────────────────────┐ │
│  │    Prometheus        │  →   │         Grafana              │ │
│  │  • Metrics collection│      │  • Dashboards                │ │
│  │  • Service health    │      │  • Alerts                    │ │
│  └──────────────────────┘      └──────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Documentation

### Current Data Flow (Simple Architecture)

#### Flow 1: Message Storage
```
1. User sends message in Discord
   ↓
2. Discord Bot receives message (bot.py::on_message)
   ↓
3. Message stored in ChromaDB with metadata (database.py::add_message)
   - Content: "Meet at 3 PM tomorrow"
   - Username: "Alice"
   - Timestamp: "2025-10-26 14:30:00"
   ↓
4. Embedding generated by sentence-transformers
   - Vector: [0.234, -0.567, 0.891, ...]
   ↓
5. Stored in ChromaDB persist_directory: ./discord_db
```

#### Flow 2: Query & Response
```
1. User types: "RTFM when is the meeting?"
   ↓
2. Bot detects trigger phrase (bot.py::on_message)
   ↓
3. Extract question: "when is the meeting?"
   ↓
4. Query ChromaDB (database.py::query)
   - Generate query embedding
   - Similarity search (k=10)
   - Filter by confidence (min=0.3)
   - Return top 5 results
   ↓
5. Build context from results:
   [2025-10-26] Alice: Meet at 3 PM tomorrow
   [2025-10-25] Bob: Don't forget meeting
   ...
   ↓
6. Call Gemini API (bot.py::generate_response)
   - Prompt: "Based on the following chat history..."
   - Context: Retrieved messages
   - Question: "when is the meeting?"
   ↓
7. Gemini generates response:
   "Based on the chat history, Alice mentioned the meeting 
    is at 3 PM tomorrow (October 27, 2025)."
   ↓
8. Send response to Discord channel
```

### Future Data Flow (Microservices Architecture)

#### Flow 1: Message Ingestion Pipeline
```
1. User sends message in Discord
   ↓
2. Discord Bot Service captures message
   ↓
3. Bot publishes to Kafka topic: 'discord_messages'
   Message: {
     content: "Meet at 3 PM",
     guild_id: "123456",
     channel_id: "789012",
     user_id: "345678",
     username: "Alice",
     timestamp: "2025-10-26T14:30:00Z"
   }
   ↓
4. Embedding Worker consumes from 'discord_messages'
   ↓
5. Worker generates embedding vector
   - Uses sentence-transformers
   - Output: [768-dim vector]
   ↓
6. Worker publishes to Kafka topic: 'discord_embeddings'
   Message: {
     original_content: "Meet at 3 PM",
     embedding: [0.234, -0.567, ...],
     metadata: {...},
     guild_id: "123456"
   }
   ↓
7. Indexing Worker consumes from 'discord_embeddings'
   ↓
8. Worker stores in ChromaDB
   - Vector: embedding
   - Metadata: username, timestamp, guild_id
   ↓
9. Worker updates PostgreSQL
   - message_id, guild_id, indexed_at
   - For analytics and tracking
```

#### Flow 2: Query Processing Pipeline
```
1. User types: "RTFM when is the meeting?"
   ↓
2. Discord Bot Service detects trigger
   ↓
3. Bot publishes to Kafka topic: 'discord_queries'
   Message: {
     query: "when is the meeting?",
     guild_id: "123456",
     user_id: "345678",
     channel_id: "789012"
   }
   ↓
4. Query Service consumes from 'discord_queries'
   ↓
5. Check Redis cache first
   cache_key = hash(query + guild_id)
   if cache_hit: return cached_response
   ↓
6. If cache miss:
   a) Generate query embedding
   b) Search ChromaDB (filtered by guild_id)
   c) Retrieve top K relevant messages
   d) Get guild-specific configs from PostgreSQL
   ↓
7. Query Service publishes to 'discord_contexts'
   Message: {
     query: "when is the meeting?",
     context: [
       {content: "Meet at 3 PM", user: "Alice", date: "..."},
       {content: "Don't forget", user: "Bob", date: "..."}
     ],
     guild_id: "123456",
     request_id: "uuid-1234"
   }
   ↓
8. Response Generator consumes from 'discord_contexts'
   ↓
9. Format prompt for Gemini:
   "Based on the following Discord chat history, answer: 
    when is the meeting?"
   ↓
10. Call Google Gemini API
    ↓
11. Receive generated response
    ↓
12. Cache in Redis (TTL: 1 hour)
    ↓
13. Response Generator publishes to 'discord_responses'
    Message: {
      response: "The meeting is at 3 PM tomorrow...",
      request_id: "uuid-1234",
      channel_id: "789012"
    }
    ↓
14. Discord Bot Service consumes from 'discord_responses'
    ↓
15. Bot sends response to Discord channel
```

---

## 🔧 Service Boundaries

### Current Architecture (Simple)

#### Service: Discord Bot Container
**Responsibility:** Everything  
**Components:**
- `bot.py` - Discord listener, trigger detection, response sender
- `database.py` - Vector database interface
- ChromaDB (embedded) - Vector storage

**Boundaries:**
- **Input:** Discord API (messages from users)
- **Output:** Discord API (responses to users)
- **Storage:** Local ChromaDB directory (`./discord_db`)
- **External APIs:** Google Gemini, HuggingFace models

**No clear separation** - monolithic design

### Future Architecture (Microservices)

#### Service 1: Discord Bot
**Primary Responsibility:** Discord interface layer  
**Components:**
- Discord.py client
- Message listener
- Trigger detection
- Response sender

**Boundaries:**
- **Input:** Discord API (websocket events)
- **Output:** Kafka topics (`discord_messages`, `discord_queries`)
- **Input:** Kafka topic (`discord_responses`)
- **Output:** Discord API (send messages)
- **No direct database access**
- **No AI/ML processing**

**Service Contract:**
```python
# Publishes to Kafka
{
  "topic": "discord_messages",
  "message": {
    "content": str,
    "guild_id": str,
    "user_id": str,
    "timestamp": ISO8601
  }
}

# Consumes from Kafka
{
  "topic": "discord_responses",
  "message": {
    "response": str,
    "channel_id": str,
    "request_id": str
  }
}
```

---

#### Service 2: Embedding Worker
**Primary Responsibility:** Convert text to vector embeddings  
**Components:**
- Kafka consumer
- Sentence-transformers model
- Kafka producer

**Boundaries:**
- **Input:** Kafka topic (`discord_messages`)
- **Output:** Kafka topic (`discord_embeddings`)
- **No database access**
- **No Discord API access**

**Service Contract:**
```python
# Consumes from Kafka
{
  "topic": "discord_messages",
  "message": {
    "content": str,
    "metadata": dict
  }
}

# Publishes to Kafka
{
  "topic": "discord_embeddings",
  "message": {
    "embedding": List[float],  # 768-dim vector
    "content": str,
    "metadata": dict
  }
}
```

**Scalability:** Can run multiple workers in parallel

---

#### Service 3: Indexing Worker
**Primary Responsibility:** Store embeddings in vector database  
**Components:**
- Kafka consumer
- ChromaDB client
- PostgreSQL client

**Boundaries:**
- **Input:** Kafka topic (`discord_embeddings`)
- **Output:** ChromaDB (vector storage)
- **Output:** PostgreSQL (metadata storage)
- **No Discord API access**
- **No AI/ML processing**

**Service Contract:**
```python
# Consumes from Kafka
{
  "topic": "discord_embeddings",
  "message": {
    "embedding": List[float],
    "content": str,
    "metadata": dict
  }
}

# Stores in ChromaDB
vector_db.add(
  embeddings=[embedding],
  documents=[content],
  metadatas=[metadata]
)

# Stores in PostgreSQL
INSERT INTO messages (guild_id, message_id, indexed_at)
```

**Scalability:** Can run multiple workers with partitioned Kafka topics

---

#### Service 4: Query Service
**Primary Responsibility:** Search vector database and retrieve context  
**Components:**
- Kafka consumer
- ChromaDB client
- Redis client
- PostgreSQL client
- Kafka producer

**Boundaries:**
- **Input:** Kafka topic (`discord_queries`)
- **Output:** Kafka topic (`discord_contexts`)
- **Read:** ChromaDB (similarity search)
- **Read/Write:** Redis (caching)
- **Read:** PostgreSQL (guild configs)
- **No Discord API access**
- **No Gemini API access**

**Service Contract:**
```python
# Consumes from Kafka
{
  "topic": "discord_queries",
  "message": {
    "query": str,
    "guild_id": str,
    "user_id": str
  }
}

# Publishes to Kafka
{
  "topic": "discord_contexts",
  "message": {
    "query": str,
    "context": List[dict],  # Retrieved messages
    "guild_id": str,
    "request_id": str
  }
}
```

---

#### Service 5: Response Generator
**Primary Responsibility:** Generate AI responses using Gemini  
**Components:**
- Kafka consumer
- Google Gemini API client
- Redis client (caching)
- Kafka producer

**Boundaries:**
- **Input:** Kafka topic (`discord_contexts`)
- **Output:** Kafka topic (`discord_responses`)
- **External API:** Google Gemini
- **Read/Write:** Redis (response caching)
- **No database access**
- **No Discord API access**

**Service Contract:**
```python
# Consumes from Kafka
{
  "topic": "discord_contexts",
  "message": {
    "query": str,
    "context": List[dict],
    "request_id": str
  }
}

# Calls Gemini API
gemini_response = model.generate_content(
  prompt=f"Based on: {context}, answer: {query}"
)

# Publishes to Kafka
{
  "topic": "discord_responses",
  "message": {
    "response": str,
    "request_id": str,
    "channel_id": str
  }
}
```

---

## 🗄️ Database Boundaries

### PostgreSQL
**Purpose:** Structured metadata and configuration  
**Tables:**
- `guilds` - Discord server information
- `messages` - Message metadata (not content)
- `user_preferences` - Per-guild settings
- `usage_logs` - API usage tracking

**Accessed by:**
- Indexing Worker (write)
- Query Service (read)
- Monitoring Service (read)

---

### Redis
**Purpose:** High-speed caching  
**Data:**
- Query responses (TTL: 1 hour)
- Embedding cache (TTL: 24 hours)
- Rate limiting counters
- Session data

**Accessed by:**
- Query Service (read/write)
- Response Generator (read/write)
- Discord Bot (read)

---

### ChromaDB
**Purpose:** Vector embeddings storage  
**Data:**
- Message embeddings (768-dim vectors)
- Message content
- Metadata (username, timestamp, guild_id)

**Accessed by:**
- Indexing Worker (write)
- Query Service (read)

---

## 📈 Scalability Considerations

### Current Architecture
- ❌ Single point of failure
- ❌ No horizontal scaling
- ❌ All processing in one container

### Future Architecture
- ✅ Each service can scale independently
- ✅ Kafka provides message buffering
- ✅ Workers can process in parallel
- ✅ Database layer separated
- ✅ Caching reduces API costs

**Scaling Strategy:**
```
Discord Bot:       1 instance (stateless)
Embedding Worker:  3-5 instances (CPU-bound)
Indexing Worker:   2-3 instances (I/O-bound)
Query Service:     2-3 instances (stateless)
Response Generator: 1-2 instances (API rate limits)
```

---

## 🎯 Summary

### Deliverables Completed

✅ **Architecture Diagram:**
- Current simple architecture documented
- Future microservices architecture designed
- All services and components shown

✅ **Data Flow Documentation:**
- Message ingestion pipeline detailed
- Query & response pipeline documented
- Each step with data structures

✅ **Service Boundaries:**
- Clear separation of concerns
- Input/Output contracts defined
- Database access patterns specified

✅ **Key Services Defined:**
- **Discord Bot:** Listener + Responder (clear boundaries)
- **Query Service:** Kafka consumer + DB queries (isolated)
- **Response Generator:** Gemini integration (dedicated service)

### Architecture Benefits

**Current (Simple):**
- Fast to implement ✅
- Easy to understand ✅
- Works for MVP ✅

**Future (Microservices):**
- Scales to 100+ Discord servers ✅
- Independent service deployment ✅
- Better monitoring and debugging ✅
- Cost-effective with caching ✅

---

**Status:** Architecture design complete and documented  
**Ready for:** Implementation (6-week timeline)  
**Foundation:** Provides clear blueprint for entire project
