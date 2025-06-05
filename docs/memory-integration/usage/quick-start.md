# Quick Start Guide

Get up and running with memory-enhanced AI agents in minutes!

## 🚀 Prerequisites

Ensure you have completed the [Installation Guide](../setup/installation.md) before proceeding.

## ⚡ 5-Minute Quick Start

### 1. Verify Installation

```bash
cd memory-integration

# Test database connection
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -d mem0db -c "SELECT 1;"

# Test Python environment
python -c "import langchain_mcp_adapters; print('✅ Dependencies ready')"
```

### 2. Create Your First Memory Agent

```python
# quick_start.py
import asyncio
from agent_factory import create_memory_agent

async def main():
    # Create a memory-enhanced agent
    agent = await create_memory_agent()
    print("✅ Memory agent created!")
    
    # Save some memories
    await agent.save_memory("I love working with AI agents")
    await agent.save_memory("My favorite programming language is Python")
    await agent.save_memory("I'm building a knowledge management system")
    
    # Search for memories
    result = await agent.search_memories("programming language")
    print(f"Found: {result['response']}")
    
    # Ask a contextual question
    result = await agent.invoke("What do you know about my preferences?")
    print(f"Agent knows: {result['response']}")
    
    await agent.close()
    print("✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Run Your First Agent

```bash
python quick_start.py
```

Expected output:
```
✅ Memory agent created!
Found: Your favorite programming language is Python.
Agent knows: Based on your memories, I know that you love working with AI agents, your favorite programming language is Python, and you're building a knowledge management system.
✅ Demo completed!
```

## 🎯 Core Concepts

### Memory Operations

#### Save Memory
```python
# Save important information
result = await agent.save_memory("Meeting with client tomorrow at 2 PM")
```

#### Search Memories
```python
# Find relevant memories
result = await agent.search_memories("client meeting")
```

#### Get All Memories
```python
# Retrieve complete memory context
result = await agent.retrieve_memories()
```

### Context-Aware Conversations

```python
# Agents automatically use memories for context
result = await agent.invoke("When is my next meeting?")
# Agent will search memories and provide relevant information
```

## 🏭 Agent Factory Pattern

### Create Different Agent Types

```python
from agent_factory import AgentFactory, AgentConfig

# Create factory
factory = AgentFactory()

# Create specialized agents
memory_agent = await factory.create_memory_agent()

# Create custom agent
custom_config = AgentConfig(
    name="ProjectAgent",
    role="project management and tracking",
    temperature=0.1
)
project_agent = await factory.create_custom_agent(custom_config)
```

## 💡 Common Patterns

### 1. Personal Assistant Pattern

```python
async def personal_assistant_demo():
    agent = await create_memory_agent()
    
    # Save personal preferences
    await agent.save_memory("I prefer dark mode in all applications")
    await agent.save_memory("I work best in the morning hours")
    await agent.save_memory("I use VS Code as my primary editor")
    
    # Ask for personalized recommendations
    result = await agent.invoke("What editor settings would you recommend?")
    print(result['response'])
    
    await agent.close()
```

### 2. Learning Assistant Pattern

```python
async def learning_assistant_demo():
    agent = await create_memory_agent()
    
    # Save learning progress
    await agent.save_memory("Completed Python basics course")
    await agent.save_memory("Currently learning machine learning")
    await agent.save_memory("Struggling with neural network concepts")
    
    # Get personalized learning advice
    result = await agent.invoke("What should I study next?")
    print(result['response'])
    
    await agent.close()
```

### 3. Project Tracking Pattern

```python
async def project_tracking_demo():
    agent = await create_memory_agent()
    
    # Save project information
    await agent.save_memory("Project: codon-kg - Knowledge graph system")
    await agent.save_memory("Tech stack: Python, Neo4j, LangGraph")
    await agent.save_memory("Deadline: End of Q1")
    
    # Get project status
    result = await agent.invoke("What's the status of my current project?")
    print(result['response'])
    
    await agent.close()
```

## 🔧 Configuration Options

### Environment Variables

```bash
# In mcp-mem0/.env
LLM_CHOICE=gpt-4o-mini          # or gpt-4, gpt-3.5-turbo
EMBEDDING_MODEL_CHOICE=text-embedding-3-small
TRANSPORT=stdio                  # or sse
```

### Agent Configuration

```python
config = AgentConfig(
    name="MyAgent",
    role="specialized assistant",
    temperature=0.1,              # 0.0 = deterministic, 1.0 = creative
    model="gpt-4o-mini",         # OpenAI model to use
    max_tokens=4000,             # Maximum response length
    system_prompt="Custom prompt..."  # Override default prompt
)
```

## 🧪 Testing Your Setup

### Quick Health Check

```python
# health_check.py
import asyncio
from agent_factory import create_memory_agent

async def health_check():
    try:
        agent = await create_memory_agent()
        
        # Test save
        save_result = await agent.save_memory("Health check test")
        assert save_result['status'] == 'success', "Save failed"
        
        # Test search
        search_result = await agent.search_memories("health check")
        assert search_result['status'] == 'success', "Search failed"
        
        # Test retrieve
        retrieve_result = await agent.retrieve_memories()
        assert retrieve_result['status'] == 'success', "Retrieve failed"
        
        await agent.close()
        print("✅ All systems operational!")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    asyncio.run(health_check())
```

## 📊 Memory Management

### View Stored Memories

```bash
# Check database directly
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -d mem0db -c "SELECT COUNT(*) FROM vecs.mem0_memories;"
```

### Clear All Memories (if needed)

```bash
# ⚠️ WARNING: This deletes all stored memories
psql -d mem0db -c "DELETE FROM vecs.mem0_memories;"
```

## 🎯 Next Steps

1. **Explore Examples**: Check out [Agent Examples](agent-examples.md) for more patterns
2. **Memory Best Practices**: Read [Memory Management](memory-management.md) guide
3. **Architecture Deep Dive**: Review [System Overview](../architecture/overview.md)
4. **Run Tests**: Execute the [Test Suite](../testing/test-suite.md)
5. **Troubleshooting**: If issues arise, see [Troubleshooting Guide](troubleshooting.md)

## 💡 Tips for Success

1. **Be Specific**: Save detailed, specific memories rather than vague ones
2. **Use Context**: Ask contextual questions to see the agent use memories
3. **Regular Cleanup**: Periodically review and clean old memories
4. **Test Thoroughly**: Use the test suite to verify functionality
5. **Monitor Performance**: Watch for slow responses and optimize as needed

## 🆘 Need Help?

- **Common Issues**: Check [Troubleshooting](troubleshooting.md)
- **Detailed Setup**: Review [Installation Guide](../setup/installation.md)
- **Architecture Questions**: See [System Overview](../architecture/overview.md)
- **Code Examples**: Browse [Agent Examples](agent-examples.md)

Happy building with memory-enhanced AI agents! 🚀