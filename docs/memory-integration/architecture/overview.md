# System Architecture Overview

This document provides a comprehensive overview of the memory integration system architecture.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph AI Agents                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Memory Agent │  │ Custom Agent │  │ Agent Factory│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────┬───────────────────────────────────────────────────┘
              │ MCP Protocol
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP-Mem0 Server                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ save_memory  │  │search_memories│  │get_all_memories│        │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────┬───────────────────────────────────────────────────┘
              │ Mem0 API
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Memory Storage Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │ pgvector     │  │ OpenAI       │          │
│  │ Database     │  │ Extension    │  │ Embeddings   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## 🧩 Core Components

### 1. LangGraph AI Agents

**Purpose**: Intelligent agents with memory capabilities

**Components**:
- `BaseMemoryAgent`: Foundation class for all memory-enhanced agents
- `MemoryAgent`: Specialized agent for memory operations
- `AgentFactory`: Factory pattern for creating different agent types

**Key Features**:
- Context-aware responses using stored memories
- Automatic memory saving and retrieval
- Modular design for different use cases

### 2. MCP-Mem0 Server

**Purpose**: Bridge between agents and memory storage

**Components**:
- FastMCP server implementation
- Memory operation tools (save, search, retrieve)
- Mem0 client integration

**Protocol**: Model Context Protocol (MCP) over stdio transport

**Tools Provided**:
- `save_memory`: Store information to long-term memory
- `search_memories`: Semantic search through stored memories
- `get_all_memories`: Retrieve complete memory context

### 3. Memory Storage Layer

**Components**:

#### PostgreSQL Database
- **Version**: PostgreSQL 15
- **Purpose**: Primary data storage
- **Tables**: 
  - `vecs.mem0_memories`: Vector embeddings and metadata
  - `vecs.mem0migrations`: Schema versioning

#### pgvector Extension
- **Purpose**: Vector similarity search
- **Features**: Efficient nearest neighbor search
- **Embedding Dimensions**: 1536 (OpenAI text-embedding-3-small)

#### OpenAI Services
- **LLM**: GPT-4o-mini for text processing
- **Embeddings**: text-embedding-3-small for vector generation

## 🔄 Data Flow

### Memory Save Operation

1. **Agent Request**: User asks agent to remember something
2. **MCP Call**: Agent calls `save_memory` tool via MCP protocol
3. **Processing**: mcp-mem0 server processes the content with LLM
4. **Embedding**: OpenAI generates vector embedding
5. **Storage**: Vector and metadata stored in PostgreSQL
6. **Response**: Confirmation returned to agent

```
User Input → Agent → MCP → mcp-mem0 → OpenAI → PostgreSQL
                                    ↓
Agent ← MCP ← mcp-mem0 ← Confirmation ← Storage Complete
```

### Memory Search Operation

1. **Search Query**: Agent searches for relevant memories
2. **Embedding**: Query converted to vector embedding
3. **Vector Search**: pgvector finds similar memories
4. **Retrieval**: Matching memories returned with similarity scores
5. **Context**: Agent uses memories to enhance response

```
Search Query → Embedding → Vector Search → Similarity Match → Context
                ↓              ↓              ↓              ↓
            OpenAI → pgvector → PostgreSQL → Agent Response
```

## 🔧 Technology Stack

### Backend Infrastructure
- **Database**: PostgreSQL 15
- **Vector Search**: pgvector extension
- **Server**: FastMCP (Python)
- **Protocol**: Model Context Protocol

### AI/ML Services
- **LLM Provider**: OpenAI
- **Text Model**: GPT-4o-mini
- **Embedding Model**: text-embedding-3-small
- **Memory Framework**: Mem0

### Python Libraries
- **Agent Framework**: LangGraph
- **LLM Integration**: LangChain
- **MCP Adapters**: langchain-mcp-adapters
- **Logging**: structlog
- **Database**: psycopg2, SQLAlchemy

## 🎯 Design Principles

### 1. Modular Architecture
- Separate concerns (storage, processing, agents)
- Pluggable components
- Easy to extend and modify

### 2. Protocol-Based Communication
- MCP for agent-to-memory communication
- Language-agnostic protocol
- Future-proof integration

### 3. Persistent Memory
- Durable storage in PostgreSQL
- Vector search for semantic similarity
- Cross-session memory retention

### 4. Factory Pattern
- Flexible agent creation
- Specialized agent types
- Consistent interfaces

### 5. Performance Optimization
- Efficient vector search with pgvector
- Connection pooling and caching
- Async operations throughout

## 🔒 Security Considerations

### Data Protection
- API keys stored in environment variables
- Database connections secured with authentication
- Memory content encrypted at rest (PostgreSQL)

### Access Control
- User-specific memory isolation (user_id in Mem0)
- Agent-level permission controls
- Secure MCP communication

### Privacy
- No sensitive data logged
- Configurable memory retention policies
- Option for local-only deployment

## 📊 Performance Characteristics

### Memory Operations
- **Save**: ~2-3 seconds (includes LLM processing)
- **Search**: ~1-2 seconds (vector similarity search)
- **Retrieve**: ~1 second (direct database query)

### Scalability
- **Concurrent Agents**: Tested up to 5 concurrent operations
- **Memory Capacity**: Limited by PostgreSQL storage
- **Vector Search**: O(log n) with proper indexing

### Resource Usage
- **Memory**: ~100MB per agent instance
- **CPU**: Moderate during LLM calls
- **Storage**: ~1KB per memory entry + vectors

## 🔄 Integration Points

### External Systems
- **OpenAI API**: LLM and embedding services
- **PostgreSQL**: Primary data storage
- **LangChain**: Agent framework integration

### Internal Interfaces
- **MCP Protocol**: Agent-to-memory communication
- **Mem0 API**: Memory management operations
- **Agent Factory**: Agent creation and management

## 🚀 Future Extensibility

### Planned Enhancements
- Multiple LLM provider support
- Enhanced vector search algorithms
- Memory categorization and tagging
- Cross-agent memory sharing

### Integration Opportunities
- Knowledge graph integration (Neo4j)
- Real-time collaboration features
- Advanced analytics and insights
- Custom memory retention policies

This architecture provides a robust, scalable foundation for memory-enhanced AI agents while maintaining flexibility for future enhancements and integrations.