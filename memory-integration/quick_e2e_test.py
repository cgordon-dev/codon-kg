"""
Quick End-to-End Test - Core Functionality Verification
"""

import asyncio
import os
import sys
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_factory import create_memory_agent


async def quick_e2e_test():
    """Quick end-to-end test of core functionality."""
    print("🚀 QUICK END-TO-END TEST")
    print("=" * 40)
    
    results = {}
    
    # Test 1: PostgreSQL Connection
    print("\n1️⃣ Testing PostgreSQL...")
    try:
        result = subprocess.run([
            "/opt/homebrew/opt/postgresql@15/bin/psql", 
            "-d", "mem0db", 
            "-c", "SELECT 1;"
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✅ PostgreSQL working")
            results["postgresql"] = True
        else:
            print("❌ PostgreSQL failed")
            results["postgresql"] = False
    except Exception as e:
        print(f"❌ PostgreSQL error: {e}")
        results["postgresql"] = False
    
    # Test 2: Memory Agent Core Operations
    print("\n2️⃣ Testing Memory Agent...")
    try:
        agent = await create_memory_agent()
        
        # Save memory
        save_result = await agent.save_memory("Quick test: System verified")
        save_ok = save_result["status"] == "success"
        
        # Search memory
        search_result = await agent.search_memories("quick test")
        search_ok = search_result["status"] == "success"
        
        await agent.close()
        
        if save_ok and search_ok:
            print("✅ Memory operations working")
            results["memory_ops"] = True
        else:
            print("❌ Memory operations failed")
            results["memory_ops"] = False
            
    except Exception as e:
        print(f"❌ Memory agent error: {e}")
        results["memory_ops"] = False
    
    # Test 3: Memory Persistence
    print("\n3️⃣ Testing Memory Persistence...")
    try:
        # Create new agent and check if previous memory exists
        agent2 = await create_memory_agent()
        retrieve_result = await agent2.retrieve_memories()
        
        if "quick test" in retrieve_result["response"].lower() or "system verified" in retrieve_result["response"].lower():
            print("✅ Memory persistence working")
            results["persistence"] = True
        else:
            print("❌ Memory persistence failed")
            results["persistence"] = False
        
        await agent2.close()
        
    except Exception as e:
        print(f"❌ Persistence test error: {e}")
        results["persistence"] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 QUICK TEST RESULTS")
    print("=" * 40)
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test.upper():<15} {status}")
    
    print(f"\nRESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 SYSTEM IS FULLY FUNCTIONAL! 🎉")
        return True
    else:
        print("⚠️  Some issues detected")
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_e2e_test())
    print(f"\nExit code: {0 if success else 1}")