# Installation Guide

Complete step-by-step installation guide for the mcp-mem0 memory integration system.

## 🎯 Overview

This guide will help you set up:
- PostgreSQL 15 with pgvector extension
- mcp-mem0 server with proper configuration
- Python dependencies and environment
- LangGraph agents with memory capabilities

## 📋 Prerequisites

- macOS (tested on macOS Sequoia)
- Homebrew package manager
- Python 3.12+
- OpenAI API key
- Git

## 🔧 Step 1: PostgreSQL Setup

### Install PostgreSQL 15

```bash
# Install PostgreSQL 15 via Homebrew
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Add PostgreSQL to PATH (for current session)
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Make PATH change permanent (optional)
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
```

### Create Database

```bash
# Create the memory database
createdb mem0db

# Set password for current user
psql -d mem0db -c "ALTER USER $(whoami) WITH PASSWORD 'password';"

# Test connection
psql -d mem0db -c "SELECT version();"
```

## 🔢 Step 2: Install pgvector Extension

### Build from Source

```bash
# Navigate to your project directory
cd /path/to/your/project

# Clone pgvector
git clone https://github.com/pgvector/pgvector.git pgvector-build
cd pgvector-build

# Build with PostgreSQL 15
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
make

# Install extension files
mkdir -p /opt/homebrew/opt/postgresql@15/share/postgresql@15/extension/
mkdir -p /opt/homebrew/opt/postgresql@15/lib/postgresql@15/

# Copy extension files
cp vector.control sql/vector--*.sql /opt/homebrew/opt/postgresql@15/share/postgresql@15/extension/
cp vector.so /opt/homebrew/opt/postgresql@15/lib/postgresql/

# Restart PostgreSQL
brew services restart postgresql@15
```

### Enable Extension

```bash
# Enable vector extension in database
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -d mem0db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Test vector operations
psql -d mem0db -c "SELECT '[1,2,3]'::vector;"
```

## 🐍 Step 3: Python Environment Setup

### Install Dependencies

```bash
# Navigate to memory-integration directory
cd memory-integration

# Install core dependencies
pip install langchain-mcp-adapters langgraph langchain langchain-openai structlog

# Install mcp-mem0 server
cd mcp-mem0
pip install -e .
cd ..
```

### Configure Environment

```bash
# Navigate to mcp-mem0 directory
cd mcp-mem0

# Create .env file from example
cp .env.example .env

# Edit .env file with your settings
cat > .env << EOF
# Transport for MCP server
TRANSPORT=stdio

# LLM Configuration
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-api-key-here
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL_CHOICE=text-embedding-3-small

# Database Configuration
DATABASE_URL=postgresql://$(whoami):password@localhost:5432/mem0db
EOF
```

**Important**: Replace `your-openai-api-key-here` with your actual OpenAI API key.

## ✅ Step 4: Verification

### Test PostgreSQL Connection

```bash
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -d mem0db -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';"
```

Expected output: `count = 1`

### Test mcp-mem0 Server

```bash
cd mcp-mem0
python -c "from src.main import mcp; print('MCP server imports successfully')"
```

### Run Integration Test

```bash
cd ..  # Back to memory-integration directory
python simple_memory_test.py
```

Expected output: Successful memory operations (save, retrieve, search)

## 🚀 Step 5: Quick Start Test

Create a simple test script:

```python
# test_installation.py
import asyncio
from agent_factory import create_memory_agent

async def test():
    agent = await create_memory_agent()
    
    # Save a memory
    result = await agent.save_memory("Installation test successful!")
    print(f"Save: {result['status']}")
    
    # Search for the memory
    result = await agent.search_memories("installation test")
    print(f"Search: {result['status']}")
    
    await agent.close()
    print("✅ Installation verified!")

if __name__ == "__main__":
    asyncio.run(test())
```

Run the test:

```bash
python test_installation.py
```

## 🔧 Troubleshooting

### Common Issues

1. **PostgreSQL Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   brew services list | grep postgresql
   
   # Restart if needed
   brew services restart postgresql@15
   ```

2. **pgvector Extension Not Found**
   ```bash
   # Verify extension files exist
   ls /opt/homebrew/opt/postgresql@15/share/postgresql@15/extension/vector*
   
   # Re-copy files if missing
   cp pgvector-build/vector.control pgvector-build/sql/vector--*.sql /opt/homebrew/opt/postgresql@15/share/postgresql@15/extension/
   ```

3. **Python Import Errors**
   ```bash
   # Install missing dependencies
   pip install langchain-mcp-adapters langgraph langchain-openai structlog
   ```

4. **OpenAI API Errors**
   - Verify your API key is correct
   - Check API usage limits
   - Ensure billing is set up

### Log Locations

- PostgreSQL logs: `/opt/homebrew/var/log/postgresql@15.log`
- Application logs: Console output with structlog formatting

## 🎉 Next Steps

Once installation is complete:

1. Review the [System Overview](../architecture/overview.md)
2. Explore [Agent Examples](../usage/agent-examples.md)
3. Run the [Test Suite](../testing/test-suite.md)
4. Check out [Memory Management](../usage/memory-management.md) best practices

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain/tree/master/libs/community/langchain_community/adapters/mcp)
- [mcp-mem0 Original Repository](https://github.com/coleam00/mcp-mem0)