"""
End-to-End Test of Memory Integration System

This script performs a comprehensive test of the entire memory integration system,
including PostgreSQL, mcp-mem0 server, MCP client, and memory-enhanced agents.
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any
import subprocess

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_factory import create_memory_agent, AgentFactory, AgentConfig
from simple_memory_test import test_memory_operations as test_direct_mcp


async def test_postgresql_connection():
    """Test PostgreSQL database connection and pgvector extension."""
    print("🐘 Testing PostgreSQL Connection...")
    
    try:
        # Test basic connection
        result = subprocess.run([
            "/opt/homebrew/opt/postgresql@15/bin/psql", 
            "-d", "mem0db", 
            "-c", "SELECT version();"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ PostgreSQL connection successful")
            print(f"   Version: {result.stdout.split()[1]}")
        else:
            print(f"❌ PostgreSQL connection failed: {result.stderr}")
            return False
        
        # Test pgvector extension
        result = subprocess.run([
            "/opt/homebrew/opt/postgresql@15/bin/psql",
            "-d", "mem0db",
            "-c", "SELECT extname FROM pg_extension WHERE extname = 'vector';"
        ], capture_output=True, text=True, timeout=10)
        
        if "vector" in result.stdout:
            print("✅ pgvector extension is installed and available")
        else:
            print("❌ pgvector extension not found")
            return False
        
        # Test vector operations
        result = subprocess.run([
            "/opt/homebrew/opt/postgresql@15/bin/psql",
            "-d", "mem0db", 
            "-c", "SELECT '[1,2,3]'::vector;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Vector operations working correctly")
            return True
        else:
            print(f"❌ Vector operations failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False


async def test_mcp_server_standalone():
    """Test the mcp-mem0 server in standalone mode."""
    print("\n🔧 Testing MCP-Mem0 Server Standalone...")
    
    try:
        # Test server import and basic functionality
        mem0_server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp-mem0", "src", "main.py")
        
        if not os.path.exists(mem0_server_path):
            print(f"❌ MCP server not found at: {mem0_server_path}")
            return False
        
        # Test server imports
        import sys
        sys.path.append(os.path.dirname(mem0_server_path))
        
        try:
            from main import mcp
            print("✅ MCP server imports successfully")
        except Exception as e:
            print(f"❌ MCP server import failed: {e}")
            return False
        
        print("✅ MCP-Mem0 server configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False


async def test_direct_mcp_integration():
    """Test direct MCP client integration."""
    print("\n🔌 Testing Direct MCP Integration...")
    
    try:
        # This calls our existing simple_memory_test function
        await test_direct_mcp()
        print("✅ Direct MCP integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Direct MCP integration failed: {e}")
        return False


async def test_memory_agent_functionality():
    """Test memory-enhanced agent functionality."""
    print("\n🤖 Testing Memory-Enhanced Agent...")
    
    try:
        # Create memory agent
        agent = await create_memory_agent()
        print("✅ Memory agent created successfully")
        
        # Test save operation
        save_result = await agent.save_memory("End-to-end test: System integration verified at " + time.strftime("%Y-%m-%d %H:%M:%S"))
        if save_result["status"] == "success":
            print("✅ Memory save operation successful")
        else:
            print(f"❌ Memory save failed: {save_result.get('error', 'Unknown error')}")
            return False
        
        # Test search operation
        search_result = await agent.search_memories("end-to-end test")
        if search_result["status"] == "success":
            print("✅ Memory search operation successful")
        else:
            print(f"❌ Memory search failed: {search_result.get('error', 'Unknown error')}")
            return False
        
        # Test retrieve operation
        retrieve_result = await agent.retrieve_memories()
        if retrieve_result["status"] == "success":
            print("✅ Memory retrieve operation successful")
        else:
            print(f"❌ Memory retrieve failed: {retrieve_result.get('error', 'Unknown error')}")
            return False
        
        # Cleanup
        await agent.close()
        print("✅ Memory agent test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Memory agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_factory_pattern():
    """Test the modular agent factory pattern."""
    print("\n🏭 Testing Agent Factory Pattern...")
    
    try:
        # Create factory
        factory = AgentFactory()
        print("✅ Agent factory created")
        
        # Create multiple agent types
        memory_agent = await factory.create_memory_agent()
        print("✅ Memory agent created via factory")
        
        # Create custom agent
        custom_config = AgentConfig(
            name="TestAgent",
            role="end-to-end testing",
            temperature=0.1,
            system_prompt="You are a test agent for verifying system functionality."
        )
        custom_agent = await factory.create_custom_agent(custom_config)
        print("✅ Custom agent created via factory")
        
        # Test agent retrieval
        retrieved_agent = factory.get_agent("memory_agent")
        if retrieved_agent:
            print("✅ Agent retrieval working")
        else:
            print("❌ Agent retrieval failed")
            return False
        
        # Test both agents
        memory_result = await memory_agent.save_memory("Factory pattern test successful")
        custom_result = await custom_agent.invoke("Test message for custom agent")
        
        if memory_result["status"] == "success" and custom_result["status"] == "success":
            print("✅ Both agents functioning correctly")
        else:
            print("❌ Agent functionality test failed")
            return False
        
        # Cleanup
        await factory.close_all_agents()
        print("✅ Agent factory pattern test completed")
        return True
        
    except Exception as e:
        print(f"❌ Agent factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_persistence():
    """Test memory persistence across different agent sessions."""
    print("\n💾 Testing Memory Persistence...")
    
    try:
        # Session 1: Save some memories
        print("  📝 Session 1: Saving memories...")
        agent1 = await create_memory_agent()
        
        test_memories = [
            "User prefers working in the morning",
            "Current project: codon-kg memory integration", 
            "Favorite programming language: Python",
            "Meeting scheduled for Friday at 2 PM"
        ]
        
        for memory in test_memories:
            result = await agent1.save_memory(memory)
            if result["status"] != "success":
                print(f"❌ Failed to save memory: {memory}")
                return False
        
        await agent1.close()
        print("✅ Session 1 completed - memories saved")
        
        # Small delay to ensure persistence
        await asyncio.sleep(2)
        
        # Session 2: Retrieve and search memories
        print("  🔍 Session 2: Retrieving memories...")
        agent2 = await create_memory_agent()
        
        # Test retrieval
        all_memories = await agent2.retrieve_memories()
        if "codon-kg" not in all_memories["response"].lower():
            print("❌ Memory persistence failed - project memory not found")
            return False
        
        # Test search
        search_result = await agent2.search_memories("programming language")
        if "python" not in search_result["response"].lower():
            print("❌ Memory search failed - language preference not found")
            return False
        
        # Test contextual query
        context_result = await agent2.invoke("What do you know about my work preferences?")
        if "morning" not in context_result["response"].lower():
            print("❌ Contextual memory query failed")
            return False
        
        await agent2.close()
        print("✅ Memory persistence test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Memory persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_system_performance():
    """Test system performance under load."""
    print("\n⚡ Testing System Performance...")
    
    try:
        agent = await create_memory_agent()
        
        # Test concurrent operations
        start_time = time.time()
        
        tasks = []
        for i in range(5):
            task = agent.save_memory(f"Performance test memory {i+1}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Check all operations succeeded
        for i, result in enumerate(results):
            if result["status"] != "success":
                print(f"❌ Concurrent operation {i+1} failed")
                return False
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 5 concurrent memory operations completed in {duration:.2f} seconds")
        
        # Test search performance
        start_time = time.time()
        search_result = await agent.search_memories("performance test")
        search_duration = time.time() - start_time
        
        if search_result["status"] == "success":
            print(f"✅ Memory search completed in {search_duration:.2f} seconds")
        else:
            print("❌ Memory search performance test failed")
            return False
        
        await agent.close()
        print("✅ Performance test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


async def run_end_to_end_tests():
    """Run comprehensive end-to-end tests of the entire system."""
    print("🧪 COMPREHENSIVE END-TO-END SYSTEM TEST")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: PostgreSQL Infrastructure
    test_results["postgresql"] = await test_postgresql_connection()
    
    # Test 2: MCP Server
    test_results["mcp_server"] = await test_mcp_server_standalone()
    
    # Test 3: Direct MCP Integration  
    test_results["mcp_integration"] = await test_direct_mcp_integration()
    
    # Test 4: Memory Agent Functionality
    test_results["memory_agent"] = await test_memory_agent_functionality()
    
    # Test 5: Agent Factory Pattern
    test_results["agent_factory"] = await test_agent_factory_pattern()
    
    # Test 6: Memory Persistence
    test_results["memory_persistence"] = await test_memory_persistence()
    
    # Test 7: System Performance
    test_results["performance"] = await test_system_performance()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper().replace('_', ' '):<25} {status}")
        if result:
            passed_tests += 1
    
    print("\n" + "-" * 60)
    print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - SYSTEM FULLY FUNCTIONAL! 🎉")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW ISSUES ABOVE")
        return False


if __name__ == "__main__":
    # Run the comprehensive test suite
    success = asyncio.run(run_end_to_end_tests())
    sys.exit(0 if success else 1)