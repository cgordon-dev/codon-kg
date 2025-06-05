# Test Suite Documentation

Comprehensive testing documentation for the memory integration system.

## 🧪 Test Overview

The test suite includes multiple levels of testing to ensure system reliability:

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Component interaction testing  
3. **End-to-End Tests** - Full system workflow testing
4. **Performance Tests** - Load and performance validation

## 🚀 Quick Test Execution

### Run All Tests

```bash
cd memory-integration

# Quick system verification
python quick_e2e_test.py

# Comprehensive test suite
python final_test.py

# Full end-to-end test (longer)
python end_to_end_test.py
```

### Expected Results

```
🎯 FINAL SYSTEM VERIFICATION TEST
==================================================

📊 Database Status:
✅ Database contains X memories

🔄 Complete Memory Workflow:
✅ Memory operations working

🔧 System Components:
✅ PostgreSQL 15
✅ pgvector extension
✅ mcp-mem0 server
✅ LangChain MCP adapters
✅ OpenAI API
✅ Memory persistence
✅ Agent factory pattern

🏁 FINAL SYSTEM STATUS
🎉 SYSTEM IS FULLY OPERATIONAL! 🎉
```

## 📋 Test Categories

### 1. Infrastructure Tests

#### PostgreSQL Connection Test

```python
# Test database connectivity
def test_postgresql_connection():
    result = subprocess.run([
        "/opt/homebrew/opt/postgresql@15/bin/psql", 
        "-d", "mem0db", 
        "-c", "SELECT version();"
    ], capture_output=True, text=True, timeout=10)
    
    assert result.returncode == 0, "PostgreSQL connection failed"
    assert "PostgreSQL 15" in result.stdout, "Wrong PostgreSQL version"
```

#### pgvector Extension Test

```python
# Test vector operations
def test_pgvector_extension():
    result = subprocess.run([
        "/opt/homebrew/opt/postgresql@15/bin/psql",
        "-d", "mem0db",
        "-c", "SELECT '[1,2,3]'::vector;"
    ], capture_output=True, text=True, timeout=10)
    
    assert result.returncode == 0, "Vector operations failed"
    assert "[1,2,3]" in result.stdout, "Vector parsing failed"
```

### 2. MCP Integration Tests

#### MCP Server Test

```python
async def test_mcp_server():
    """Test mcp-mem0 server functionality."""
    from langchain_mcp_adapters.client import MultiServerMCPClient
    
    mem0_server_path = "mcp-mem0/src/main.py"
    server_config = {
        "mem0": {
            "command": "python",
            "args": [mem0_server_path],
            "transport": "stdio",
        }
    }
    
    client = MultiServerMCPClient(server_config)
    tools = await client.get_tools()
    
    assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"
    
    tool_names = [tool.name for tool in tools]
    expected_tools = ["save_memory", "search_memories", "get_all_memories"]
    
    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Missing tool: {expected_tool}"
```

#### Direct MCP Operations Test

```python
async def test_direct_mcp_operations():
    """Test direct MCP memory operations."""
    client = MultiServerMCPClient(server_config)
    tools = await client.get_tools()
    agent = create_react_agent(model, tools)
    
    # Test save operation
    save_result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "Save this memory: 'Test memory content'"}]
    })
    assert "successfully" in save_result["messages"][-1].content.lower()
    
    # Test retrieve operation
    retrieve_result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "What memories do I have?"}]
    })
    assert "test memory" in retrieve_result["messages"][-1].content.lower()
```

### 3. Agent Functionality Tests

#### Memory Agent Test

```python
async def test_memory_agent():
    """Test memory-enhanced agent functionality."""
    agent = await create_memory_agent()
    
    # Test save operation
    save_result = await agent.save_memory("Agent test memory")
    assert save_result["status"] == "success", f"Save failed: {save_result}"
    
    # Test search operation
    search_result = await agent.search_memories("agent test")
    assert search_result["status"] == "success", f"Search failed: {search_result}"
    
    # Test retrieve operation
    retrieve_result = await agent.retrieve_memories()
    assert retrieve_result["status"] == "success", f"Retrieve failed: {retrieve_result}"
    
    await agent.close()
```

#### Agent Factory Test

```python
async def test_agent_factory():
    """Test agent factory pattern."""
    factory = AgentFactory()
    
    # Test memory agent creation
    memory_agent = await factory.create_memory_agent()
    assert memory_agent.config.name == "MemoryAgent"
    
    # Test custom agent creation
    custom_config = AgentConfig(
        name="TestAgent",
        role="testing",
        temperature=0.1
    )
    custom_agent = await factory.create_custom_agent(custom_config)
    assert custom_agent.config.name == "TestAgent"
    
    # Test agent retrieval
    retrieved = factory.get_agent("memory_agent")
    assert retrieved is not None
    
    await factory.close_all_agents()
```

### 4. Memory Persistence Tests

#### Cross-Session Persistence Test

```python
async def test_memory_persistence():
    """Test memory persistence across agent sessions."""
    
    # Session 1: Save memories
    agent1 = await create_memory_agent()
    test_memory = f"Persistence test {time.time()}"
    await agent1.save_memory(test_memory)
    await agent1.close()
    
    # Small delay to ensure persistence
    await asyncio.sleep(2)
    
    # Session 2: Retrieve memories
    agent2 = await create_memory_agent()
    result = await agent2.retrieve_memories()
    
    assert test_memory in result["response"], "Memory not persisted"
    await agent2.close()
```

#### Database Integrity Test

```python
def test_database_integrity():
    """Test database data integrity."""
    result = subprocess.run([
        "/opt/homebrew/opt/postgresql@15/bin/psql",
        "-d", "mem0db",
        "-c", "SELECT COUNT(*) FROM vecs.mem0_memories;"
    ], capture_output=True, text=True, timeout=5)
    
    assert result.returncode == 0, "Database query failed"
    
    # Extract count from output
    lines = result.stdout.strip().split('\n')
    count_line = [line for line in lines if line.strip().isdigit()][0]
    count = int(count_line.strip())
    
    assert count > 0, "No memories found in database"
```

### 5. Performance Tests

#### Concurrent Operations Test

```python
async def test_concurrent_operations():
    """Test system performance under concurrent load."""
    agent = await create_memory_agent()
    
    # Create multiple concurrent save operations
    tasks = []
    for i in range(5):
        task = agent.save_memory(f"Concurrent test memory {i}")
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    # Verify all operations succeeded
    for result in results:
        assert result["status"] == "success", "Concurrent operation failed"
    
    # Performance assertion (adjust based on your requirements)
    assert duration < 30, f"Concurrent operations too slow: {duration}s"
    
    await agent.close()
```

#### Search Performance Test

```python
async def test_search_performance():
    """Test memory search performance."""
    agent = await create_memory_agent()
    
    # Perform search operation
    start_time = time.time()
    result = await agent.search_memories("performance test")
    duration = time.time() - start_time
    
    assert result["status"] == "success", "Search operation failed"
    assert duration < 10, f"Search too slow: {duration}s"
    
    await agent.close()
```

## 🛠️ Custom Test Creation

### Basic Test Template

```python
import asyncio
import pytest
from agent_factory import create_memory_agent

class TestMemorySystem:
    @pytest.mark.asyncio
    async def test_custom_functionality(self):
        """Test custom functionality."""
        agent = await create_memory_agent()
        
        try:
            # Your test logic here
            result = await agent.save_memory("Test content")
            assert result["status"] == "success"
            
        finally:
            await agent.close()
```

### Integration Test Template

```python
async def test_integration_workflow():
    """Test complete integration workflow."""
    
    # Setup
    agent = await create_memory_agent()
    test_data = "Integration test data"
    
    try:
        # Test workflow steps
        save_result = await agent.save_memory(test_data)
        search_result = await agent.search_memories("integration")
        context_result = await agent.invoke("What do you know about integration?")
        
        # Assertions
        assert save_result["status"] == "success"
        assert search_result["status"] == "success"
        assert "integration" in context_result["response"].lower()
        
    finally:
        await agent.close()
```

## 📊 Test Reports

### Running with Coverage

```bash
# Install coverage
pip install coverage pytest pytest-asyncio

# Run tests with coverage
coverage run -m pytest test_*.py
coverage report
coverage html  # Generate HTML report
```

### Performance Benchmarking

```python
# benchmark.py
import asyncio
import time
from agent_factory import create_memory_agent

async def benchmark_operations():
    """Benchmark memory operations."""
    agent = await create_memory_agent()
    
    # Benchmark save operations
    save_times = []
    for i in range(10):
        start = time.time()
        await agent.save_memory(f"Benchmark test {i}")
        save_times.append(time.time() - start)
    
    # Benchmark search operations
    search_times = []
    for i in range(10):
        start = time.time()
        await agent.search_memories("benchmark")
        search_times.append(time.time() - start)
    
    await agent.close()
    
    print(f"Average save time: {sum(save_times)/len(save_times):.2f}s")
    print(f"Average search time: {sum(search_times)/len(search_times):.2f}s")

if __name__ == "__main__":
    asyncio.run(benchmark_operations())
```

## 🔧 Test Configuration

### Environment Setup for Testing

```bash
# test_env.sh
export TEST_DATABASE_URL="postgresql://$(whoami):password@localhost:5432/mem0db_test"
export TEST_MODE=true
export LOG_LEVEL=DEBUG
```

### Test Database Setup

```bash
# Create separate test database
createdb mem0db_test
psql -d mem0db_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 🚨 Troubleshooting Tests

### Common Test Failures

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   brew services list | grep postgresql
   brew services restart postgresql@15
   ```

2. **Memory Persistence Failures**
   ```bash
   # Check database contents
   psql -d mem0db -c "SELECT COUNT(*) FROM vecs.mem0_memories;"
   ```

3. **MCP Server Issues**
   ```bash
   # Test server directly
   cd mcp-mem0
   python src/main.py --help
   ```

4. **OpenAI API Failures**
   ```bash
   # Verify API key
   echo $OPENAI_API_KEY
   # Check rate limits and billing
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run tests with verbose output
python -v test_script.py
```

## 📈 Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Memory Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python final_test.py
```

This comprehensive test suite ensures your memory integration system is reliable, performant, and ready for production use.