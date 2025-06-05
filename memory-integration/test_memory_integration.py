#!/usr/bin/env python3
"""
Test Script for Memory Integration

Tests the mcp-mem0 server integration with LangGraph agents.
"""

import asyncio
import structlog
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from agent_factory import get_agent_factory
from config import get_config

# Configure logging
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

logger = structlog.get_logger(__name__)

async def test_memory_agent():
    """Test the memory agent functionality."""
    print("\n🧠 Testing Memory Agent...")
    
    factory = await get_agent_factory()
    agent = await factory.create_agent("memory", "test_session")
    
    try:
        # Test 1: Save a memory
        print("\n1. Testing memory saving...")
        result = await agent.save_memory("Meeting with client John Doe scheduled for Friday 3 PM")
        print(f"Save result: {result}")
        
        # Test 2: Save another memory
        print("\n2. Saving another memory...")
        result = await agent.save_memory("Client prefers email communication over phone calls")
        print(f"Save result: {result}")
        
        # Test 3: Retrieve all memories
        print("\n3. Retrieving all memories...")
        memories = await agent.retrieve_memories()
        print(f"All memories: {memories}")
        
        # Test 4: Search for specific memories
        print("\n4. Searching for meeting-related memories...")
        search_result = await agent.search_memories("meeting")
        print(f"Meeting memories: {search_result}")
        
        # Test 5: Search for client preferences
        print("\n5. Searching for client preferences...")
        prefs_result = await agent.search_memories("client preferences")
        print(f"Client preferences: {prefs_result}")
        
        return True
        
    except Exception as e:
        logger.error("Memory agent test failed", error=str(e))
        print(f"❌ Memory agent test failed: {e}")
        return False
    
    finally:
        await agent.close()

async def test_conversation_agent():
    """Test the conversation agent with memory context."""
    print("\n💬 Testing Conversation Agent...")
    
    factory = await get_agent_factory()
    agent = await factory.create_agent("conversation", "test_session")
    
    try:
        # Test 1: Ask about previous memories
        print("\n1. Asking about previous information...")
        response = await agent.invoke("What do you know about my client meetings?")
        print(f"Response: {response['response']}")
        
        # Test 2: Add new information through conversation
        print("\n2. Adding new information through conversation...")
        response = await agent.invoke("I just had a successful meeting with client John. He approved the project budget of $50,000.")
        print(f"Response: {response['response']}")
        
        # Test 3: Ask follow-up questions
        print("\n3. Asking follow-up questions...")
        response = await agent.invoke("What's the budget for John's project?")
        print(f"Response: {response['response']}")
        
        # Test 4: Test memory context
        print("\n4. Testing memory context...")
        response = await agent.invoke("How should I communicate with John based on what you know?")
        print(f"Response: {response['response']}")
        
        return True
        
    except Exception as e:
        logger.error("Conversation agent test failed", error=str(e))
        print(f"❌ Conversation agent test failed: {e}")
        return False
    
    finally:
        await agent.close()

async def test_task_agent():
    """Test the task agent functionality."""
    print("\n📋 Testing Task Agent...")
    
    factory = await get_agent_factory()
    agent = await factory.create_agent("task", "test_session")
    
    try:
        # Test 1: Create a task
        print("\n1. Creating a task...")
        response = await agent.invoke("I need to prepare a project proposal for John Doe by next Friday")
        print(f"Response: {response['response']}")
        
        # Test 2: Add task details
        print("\n2. Adding task details...")
        response = await agent.invoke("The proposal should include timeline, budget breakdown, and team composition")
        print(f"Response: {response['response']}")
        
        # Test 3: Check task status
        print("\n3. Checking tasks...")
        response = await agent.invoke("What tasks do I have coming up?")
        print(f"Response: {response['response']}")
        
        return True
        
    except Exception as e:
        logger.error("Task agent test failed", error=str(e))
        print(f"❌ Task agent test failed: {e}")
        return False
    
    finally:
        await agent.close()

async def test_learning_agent():
    """Test the learning agent functionality."""
    print("\n📚 Testing Learning Agent...")
    
    factory = await get_agent_factory()
    agent = await factory.create_agent("learning", "test_session")
    
    try:
        # Test 1: Learn something new
        print("\n1. Learning new information...")
        response = await agent.invoke("I'm learning about machine learning. Can you help me remember that neural networks have input, hidden, and output layers?")
        print(f"Response: {response['response']}")
        
        # Test 2: Add more knowledge
        print("\n2. Adding more knowledge...")
        response = await agent.invoke("Also remember that backpropagation is used to train neural networks by adjusting weights")
        print(f"Response: {response['response']}")
        
        # Test 3: Test knowledge recall
        print("\n3. Testing knowledge recall...")
        response = await agent.invoke("What do you know about neural networks?")
        print(f"Response: {response['response']}")
        
        return True
        
    except Exception as e:
        logger.error("Learning agent test failed", error=str(e))
        print(f"❌ Learning agent test failed: {e}")
        return False
    
    finally:
        await agent.close()

async def test_configuration():
    """Test configuration validation."""
    print("\n⚙️  Testing Configuration...")
    
    config = get_config()
    validation = config.validate_config()
    
    print(f"Configuration status: {validation['status']}")
    if validation['issues']:
        print("Configuration issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Configuration is valid")
        return True

async def test_agent_factory():
    """Test the agent factory functionality."""
    print("\n🏭 Testing Agent Factory...")
    
    factory = await get_agent_factory()
    
    try:
        # Test 1: List agent types
        agent_types = factory.list_agent_types()
        print(f"Available agent types: {agent_types}")
        
        # Test 2: Get agent info
        agent_info = factory.get_agent_info()
        print("Agent information:")
        for agent_type, info in agent_info.items():
            print(f"  {agent_type}: {info['description']}")
        
        # Test 3: Create agents of different types
        for agent_type in agent_types:
            print(f"\nCreating {agent_type} agent...")
            agent = await factory.create_agent(agent_type, f"test_{agent_type}")
            print(f"✅ Created {agent.name}")
            await agent.close()
        
        return True
        
    except Exception as e:
        logger.error("Agent factory test failed", error=str(e))
        print(f"❌ Agent factory test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Starting Memory Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Agent Factory", test_agent_factory),
        ("Memory Agent", test_memory_agent),
        ("Conversation Agent", test_conversation_agent),
        ("Task Agent", test_task_agent),
        ("Learning Agent", test_learning_agent),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'=' * 20} {test_name} {'=' * 20}")
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
                
        except Exception as e:
            logger.error("Test failed with exception", test=test_name, error=str(e))
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🧪 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())