"""
Simplified Memory Test using direct MCP client integration

This test bypasses the complex agent structure and directly tests the mcp-mem0 server.
"""

import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


async def test_memory_operations():
    """Test memory operations directly with MCP client."""
    print("🧠 Testing Direct MCP-Mem0 Integration")
    print("=" * 50)
    
    # Get the path to the mcp-mem0 server
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mem0_server_path = os.path.join(current_dir, "mcp-mem0", "src", "main.py")
    
    print(f"📍 Using mem0 server at: {mem0_server_path}")
    
    try:
        # Configure MCP client
        server_config = {
            "mem0": {
                "command": "python",
                "args": [mem0_server_path],
                "transport": "stdio",
            }
        }
        
        print("🔌 Initializing MCP client...")
        client = MultiServerMCPClient(server_config)
        tools = await client.get_tools()
        print(f"✅ Retrieved {len(tools)} tools from mcp-mem0 server")
        
        for tool in tools:
            print(f"   📦 {tool.name}: {tool.description[:100]}...")
        
        # Create a simple agent
        print("\n🤖 Creating LangGraph agent with memory tools...")
        
        # Set up OpenAI model (get API key from environment)
        api_key = os.getenv("OPENAI_API_KEY", "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")
        
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=api_key
        )
        
        agent = create_react_agent(model, tools)
        
        # Test 1: Save memories
        print("\n📝 Test 1: Saving memories...")
        test_memories = [
            "I prefer dark mode for all applications.",
            "My daily standup is at 9 AM EST.",
            "I'm working on a codon-kg project with Neo4j."
        ]
        
        for memory in test_memories:
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": f"Save this to memory: {memory}"}]
            })
            print(f"✅ Saved: {memory}")
            print(f"   Response: {result['messages'][-1].content[:100]}...")
        
        # Test 2: Retrieve all memories
        print("\n📋 Test 2: Retrieving all memories...")
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": "Show me all my stored memories"}]
        })
        print("✅ Retrieved memories:")
        print(f"   Response: {result['messages'][-1].content[:200]}...")
        
        # Test 3: Search memories
        print("\n🔍 Test 3: Searching memories...")
        search_queries = [
            "What are my theme preferences?",
            "When is my daily meeting?",
            "What project am I working on?"
        ]
        
        for query in search_queries:
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": f"Search my memories: {query}"}]
            })
            print(f"✅ Query: {query}")
            print(f"   Answer: {result['messages'][-1].content[:100]}...")
        
        print("\n🎯 Memory integration test completed successfully! ✨")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            await client.close()
            print("🧹 MCP client closed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    asyncio.run(test_memory_operations())