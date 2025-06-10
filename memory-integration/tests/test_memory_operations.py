"""
Test Script for Memory-Enhanced Agent Operations

This script tests the three main memory operations:
1. Save memory
2. Retrieve all memories  
3. Search memories
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_agent import create_memory_agent


async def test_memory_operations():
    """Test the memory operations with the mcp-mem0 server."""
    print("🧠 Testing Memory-Enhanced Agent Operations")
    print("=" * 50)
    
    # Create the memory agent
    try:
        agent = create_memory_agent()
        print("✅ Memory agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create memory agent: {e}")
        return
    
    try:
        # Test 1: Save a memory
        print("\n📝 Test 1: Saving memories...")
        memories_to_save = [
            "I prefer dark mode for all applications and websites.",
            "My daily standup meeting is at 9 AM EST on weekdays.",
            "I'm working on a project called 'codon-kg' which involves Neo4j knowledge graphs.",
            "I use Python as my primary programming language for data analysis."
        ]
        
        for memory in memories_to_save:
            result = agent.run(f"Save this information to my memory: {memory}")
            if result["status"] == "success":
                print(f"✅ Saved: {memory[:50]}...")
            else:
                print(f"❌ Failed to save: {memory[:50]}... - Error: {result.get('error', 'Unknown')}")
        
        # Test 2: Retrieve all memories
        print("\n📋 Test 2: Retrieving all memories...")
        result = agent.run("Please show me all of my stored memories.")
        if result["status"] == "success":
            print("✅ Successfully retrieved memories")
            print(f"Response: {result['response'][:200]}...")
        else:
            print(f"❌ Failed to retrieve memories - Error: {result.get('error', 'Unknown')}")
        
        # Test 3: Search memories
        print("\n🔍 Test 3: Searching memories...")
        search_queries = [
            "What are my preferences for application themes?",
            "When is my daily meeting?", 
            "What project am I working on?",
            "What programming language do I prefer?"
        ]
        
        for query in search_queries:
            result = agent.run(f"Search my memories to answer: {query}")
            if result["status"] == "success":
                print(f"✅ Query: {query}")
                print(f"   Answer: {result['response'][:100]}...")
            else:
                print(f"❌ Query failed: {query} - Error: {result.get('error', 'Unknown')}")
        
        print("\n🎯 Test 4: Contextual conversation with memory...")
        contextual_queries = [
            "Based on my preferences, what theme should I use for a new IDE?",
            "Schedule a code review meeting considering my existing meeting schedule.",
            "Suggest a task for my codon-kg project using my preferred language."
        ]
        
        for query in contextual_queries:
            result = agent.run(query)
            if result["status"] == "success":
                print(f"✅ Contextual query: {query}")
                print(f"   Response: {result['response'][:150]}...")
            else:
                print(f"❌ Contextual query failed: {query} - Error: {result.get('error', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            await agent.close()
            print("\n🧹 Agent cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    print("\n✨ Memory operations testing completed!")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_memory_operations())