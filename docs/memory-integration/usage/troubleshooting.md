# Troubleshooting Guide

Common issues and solutions for the memory integration system.

## 🚨 Quick Diagnostics

### System Health Check

```bash
# Run quick diagnostic
cd memory-integration
python quick_e2e_test.py
```

### Component Status Check

```bash
# PostgreSQL status
brew services list | grep postgresql

# Database connection
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -d mem0db -c "SELECT 1;"

# Python environment
python -c "import langchain_mcp_adapters; print('✅ Dependencies OK')"
```

## 🔧 Common Issues

### 1. PostgreSQL Connection Issues

#### Problem: "connection to server failed"

```
psycopg2.OperationalError: connection to server at "localhost", port 5432 failed
```

**Solutions:**

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if stopped
brew services start postgresql@15

# Check PostgreSQL logs
tail -f /opt/homebrew/var/log/postgresql@15.log

# Verify database exists
psql -l | grep mem0db

# Create database if missing
createdb mem0db
```

#### Problem: "password authentication failed"

**Solutions:**

```bash
# Reset password for current user
psql -d mem0db -c "ALTER USER $(whoami) WITH PASSWORD 'password';"

# Update .env file with correct credentials
cd mcp-mem0
vim .env  # Update DATABASE_URL
```

#### Problem: Wrong PostgreSQL version

**Solutions:**

```bash
# Check installed versions
brew list | grep postgresql

# Uninstall other versions
brew uninstall postgresql@14 postgresql@16

# Add correct PATH
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
```

### 2. pgvector Extension Issues

#### Problem: "extension 'vector' is not available"

```
ERROR: extension "vector" is not available
DETAIL: Could not open extension control file
```

**Solutions:**

```bash
# Check if extension files exist
ls /opt/homebrew/opt/postgresql@15/share/postgresql@15/extension/vector*

# Rebuild and reinstall pgvector
cd pgvector-build
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
make clean && make

# Copy extension files
cp vector.control sql/vector--*.sql /opt/homebrew/opt/postgresql@15/share/postgresql@15/extension/
cp vector.so /opt/homebrew/opt/postgresql@15/lib/postgresql/

# Restart PostgreSQL
brew services restart postgresql@15

# Create extension
psql -d mem0db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Problem: "could not access file '$libdir/vector'"

**Solutions:**

```bash
# Check library path
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
pg_config --pkglibdir

# Copy vector.so to correct location
cp pgvector-build/vector.so /opt/homebrew/opt/postgresql@15/lib/postgresql/

# Verify file exists
ls -la /opt/homebrew/opt/postgresql@15/lib/postgresql/vector.so
```

### 3. Python Environment Issues

#### Problem: "ModuleNotFoundError"

```
ModuleNotFoundError: No module named 'langchain_mcp_adapters'
```

**Solutions:**

```bash
# Install missing dependencies
pip install langchain-mcp-adapters langgraph langchain-openai structlog

# Verify installation
python -c "import langchain_mcp_adapters; print('OK')"

# Check Python environment
which python
pip list | grep langchain
```

#### Problem: "ImportError" from mcp-mem0

**Solutions:**

```bash
# Reinstall mcp-mem0
cd mcp-mem0
pip install -e .

# Check dependencies
pip check

# Update if needed
pip install --upgrade mem0ai httpx mcp
```

### 4. MCP Server Issues

#### Problem: "MCP server startup failed"

**Solutions:**

```bash
# Test server import
cd mcp-mem0
python -c "from src.main import mcp; print('OK')"

# Check environment variables
cat .env

# Verify database URL
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"

# Test server directly
python src/main.py --help
```

#### Problem: "Connection closed" MCP errors

**Solutions:**

```bash
# Check server configuration
cd mcp-mem0
cat .env | grep TRANSPORT

# Verify stdio transport
echo "TRANSPORT=stdio" >> .env

# Test with simple client
python -c "
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

async def test():
    client = MultiServerMCPClient({'mem0': {'command': 'python', 'args': ['src/main.py'], 'transport': 'stdio'}})
    tools = await client.get_tools()
    print(f'Tools: {[t.name for t in tools]}')

asyncio.run(test())
"
```

### 5. OpenAI API Issues

#### Problem: "Invalid API key"

```
openai.AuthenticationError: Incorrect API key provided
```

**Solutions:**

```bash
# Check API key
echo $OPENAI_API_KEY

# Update .env file
cd mcp-mem0
echo "LLM_API_KEY=your-actual-api-key" >> .env

# Test API key
python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv('LLM_API_KEY'))
print('API key valid')
"
```

#### Problem: "Rate limit exceeded"

**Solutions:**

```bash
# Check rate limits in OpenAI dashboard
# Wait before retrying
# Consider upgrading to higher tier

# Use different model with higher limits
cd mcp-mem0
sed -i '' 's/gpt-4/gpt-3.5-turbo/g' .env
```

### 6. Memory Operation Issues

#### Problem: "Memory not persisted"

**Solutions:**

```bash
# Check database contents
psql -d mem0db -c "SELECT COUNT(*) FROM vecs.mem0_memories;"

# Check table structure
psql -d mem0db -c "\d vecs.mem0_memories"

# Check recent memories
psql -d mem0db -c "SELECT created_at, metadata FROM vecs.mem0_memories ORDER BY created_at DESC LIMIT 5;"

# Reset database if corrupted
psql -d mem0db -c "DROP SCHEMA vecs CASCADE;"
psql -d mem0db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Problem: "Search returns no results"

**Solutions:**

```bash
# Check embedding dimensions
psql -d mem0db -c "SELECT vector_dims(embedding) FROM vecs.mem0_memories LIMIT 1;"

# Check data exists
psql -d mem0db -c "SELECT metadata->>'text' FROM vecs.mem0_memories LIMIT 5;"

# Test embedding service
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv('LLM_API_KEY'))
response = client.embeddings.create(input='test', model='text-embedding-3-small')
print(f'Embedding dims: {len(response.data[0].embedding)}')
"
```

### 7. Performance Issues

#### Problem: "Operations very slow"

**Solutions:**

```bash
# Check system resources
top | grep postgres
top | grep python

# Check database performance
psql -d mem0db -c "SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del FROM pg_stat_user_tables;"

# Add database indexes if needed
psql -d mem0db -c "CREATE INDEX IF NOT EXISTS idx_mem0_memories_user_id ON vecs.mem0_memories USING btree (((metadata->>'user_id')));"

# Check OpenAI API latency
curl -w "Time: %{time_total}s\n" -X POST https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### Problem: "Memory usage high"

**Solutions:**

```bash
# Check Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Clean up old agent instances
# Restart Python process
# Consider connection pooling
```

## 🔍 Debug Mode

### Enable Detailed Logging

```python
# debug_setup.py
import logging
import structlog

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### Step-by-Step Debugging

```python
# debug_agent.py
import asyncio
from agent_factory import create_memory_agent

async def debug_agent():
    print("🔍 Starting debug session...")
    
    try:
        print("1. Creating agent...")
        agent = await create_memory_agent()
        print("✅ Agent created")
        
        print("2. Testing save operation...")
        result = await agent.save_memory("Debug test memory")
        print(f"Save result: {result}")
        
        print("3. Testing search operation...")
        result = await agent.search_memories("debug test")
        print(f"Search result: {result}")
        
        print("4. Testing retrieve operation...")
        result = await agent.retrieve_memories()
        print(f"Retrieve result: {result}")
        
        await agent.close()
        print("✅ Debug session completed")
        
    except Exception as e:
        print(f"❌ Debug session failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent())
```

## 📊 System Monitoring

### Database Monitoring

```sql
-- Monitor database activity
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows
FROM pg_stat_user_tables 
WHERE schemaname = 'vecs';

-- Check connection count
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';

-- Check database size
SELECT 
    pg_size_pretty(pg_database_size('mem0db')) as database_size;
```

### Performance Monitoring

```python
# monitor.py
import time
import psutil
import asyncio
from agent_factory import create_memory_agent

async def monitor_performance():
    """Monitor system performance during operations."""
    
    agent = await create_memory_agent()
    process = psutil.Process()
    
    # Baseline metrics
    start_memory = process.memory_info().rss / 1024 / 1024
    start_time = time.time()
    
    print(f"Baseline memory: {start_memory:.1f} MB")
    
    # Perform operations
    for i in range(10):
        await agent.save_memory(f"Performance test {i}")
        
        current_memory = process.memory_info().rss / 1024 / 1024
        current_time = time.time() - start_time
        
        print(f"Op {i+1}: {current_memory:.1f} MB (+{current_memory-start_memory:.1f}), {current_time:.1f}s")
    
    await agent.close()

if __name__ == "__main__":
    asyncio.run(monitor_performance())
```

## 🛡️ Recovery Procedures

### Database Recovery

```bash
# Backup current database
pg_dump mem0db > mem0db_backup.sql

# Reset database
dropdb mem0db
createdb mem0db
psql -d mem0db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Restore from backup (if needed)
psql -d mem0db < mem0db_backup.sql
```

### Environment Recovery

```bash
# Reset Python environment
pip uninstall -y langchain-mcp-adapters langgraph langchain-openai
pip install langchain-mcp-adapters langgraph langchain-openai structlog

# Reset mcp-mem0
cd mcp-mem0
pip uninstall -y mem0-mcp
pip install -e .

# Reset configuration
cp .env.example .env
# Edit .env with correct values
```

### Complete System Reset

```bash
# Stop all services
brew services stop postgresql@15

# Remove all data
rm -rf /opt/homebrew/var/postgresql@15

# Reinitialize
brew services start postgresql@15
createdb mem0db

# Follow installation guide from beginning
```

## 📞 Getting Help

### Log Collection

```bash
# Collect system logs
echo "=== PostgreSQL Status ===" > debug_info.txt
brew services list | grep postgresql >> debug_info.txt

echo "=== Database Info ===" >> debug_info.txt
psql -d mem0db -c "\l" >> debug_info.txt 2>&1

echo "=== Python Environment ===" >> debug_info.txt
python --version >> debug_info.txt
pip list | grep -E "(langchain|mcp|mem0)" >> debug_info.txt

echo "=== Error Logs ===" >> debug_info.txt
tail -20 /opt/homebrew/var/log/postgresql@15.log >> debug_info.txt 2>&1
```

### Support Checklist

Before asking for help, ensure you have:

1. ✅ Followed the installation guide completely
2. ✅ Checked all prerequisites are met
3. ✅ Verified PostgreSQL and pgvector are working
4. ✅ Confirmed OpenAI API key is valid
5. ✅ Run the diagnostic scripts
6. ✅ Checked this troubleshooting guide
7. ✅ Collected relevant logs and error messages

### Common Resolution Steps

1. **Restart Services**: `brew services restart postgresql@15`
2. **Clear Python Cache**: `find . -name "*.pyc" -delete`
3. **Reset Environment**: Source fresh environment variables
4. **Check Permissions**: Ensure file permissions are correct
5. **Update Dependencies**: `pip install --upgrade <package>`

Remember: Most issues are environment-related and can be resolved by carefully following the installation guide and checking each component individually.