#!/usr/bin/env python3
"""
Demo script to show Tahecho's different running modes.
"""

import os
from dotenv import load_dotenv
from utils.graph_db import graph_db_manager

def demo_full_mode():
    """Demonstrate full mode with graph database."""
    print("🔍 Testing FULL MODE (with Neo4j)...")
    
    # Enable graph database
    os.environ["GRAPH_DB_ENABLED"] = "True"
    
    # Try to connect
    connected = graph_db_manager.connect()
    
    if connected:
        print("✅ FULL MODE: Graph database connected")
        print("   Available features:")
        print("   - Complex relationship analysis")
        print("   - Historical change tracking")
        print("   - Dependency chain analysis")
        print("   - Advanced graph-based queries")
        print("   - All Jira operations")
        return True
    else:
        print("⚠️  FULL MODE: Graph database not available")
        print("   Falling back to LIMITED MODE")
        return False

def demo_limited_mode():
    """Demonstrate limited mode without graph database."""
    print("\n🔍 Testing LIMITED MODE (without Neo4j)...")
    
    # Disable graph database
    os.environ["GRAPH_DB_ENABLED"] = "False"
    
    # Reset connection
    graph_db_manager.is_connected = False
    graph_db_manager.graph = None
    
    # Try to connect (should fail gracefully)
    connected = graph_db_manager.connect()
    
    if not connected:
        print("✅ LIMITED MODE: Graph database disabled")
        print("   Available features:")
        print("   - Basic Jira operations")
        print("   - Direct issue queries")
        print("   - Task management")
        print("   - Status updates")
        print("   - MCP agent functionality")
        print("   Limited features:")
        print("   - No relationship analysis")
        print("   - No historical changes")
        print("   - No dependency chains")
        return True
    else:
        print("❌ LIMITED MODE: Unexpectedly connected to graph database")
        return False

def demo_auto_detection():
    """Demonstrate automatic mode detection."""
    print("\n🔍 Testing AUTO-DETECTION MODE...")
    
    # Enable graph database but don't force connection
    os.environ["GRAPH_DB_ENABLED"] = "True"
    
    # Reset connection
    graph_db_manager.is_connected = False
    graph_db_manager.graph = None
    
    # Let the system auto-detect
    connected = graph_db_manager.connect()
    
    if connected:
        print("✅ AUTO-DETECTION: Graph database found and connected")
        print("   Running in FULL MODE")
    else:
        print("✅ AUTO-DETECTION: Graph database not available")
        print("   Running in LIMITED MODE")
    
    return True

def main():
    """Run all demo modes."""
    print("🚀 Tahecho Mode Demonstration")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Test different modes
    modes = [
        ("Full Mode", demo_full_mode),
        ("Limited Mode", demo_limited_mode),
        ("Auto-Detection", demo_auto_detection)
    ]
    
    for mode_name, mode_func in modes:
        try:
            result = mode_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {mode_name}")
        except Exception as e:
            print(f"❌ FAIL {mode_name}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("📋 Mode Summary")
    print("=" * 50)
    print("""
FULL MODE (with Neo4j):
  - All features available
  - Complex analysis and reasoning
  - Historical data and relationships
  - Best user experience

LIMITED MODE (without Neo4j):
  - Basic Jira operations only
  - Direct issue management
  - No advanced analysis
  - Still functional for basic tasks

AUTO-DETECTION:
  - Automatically chooses best available mode
  - Graceful fallback to limited mode
  - No configuration required
  - Recommended for most users
""")

if __name__ == "__main__":
    main() 