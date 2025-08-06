#!/usr/bin/env python3
"""
Test script to verify Jira configuration from .env file.
"""

import os
import sys
import requests
from requests.auth import HTTPBasicAuth
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load config
from config import CONFIG


def test_jira_connection():
    """Test connection to Jira with credentials from .env"""
    print("🧪 Testing Jira Configuration from .env")
    print("=" * 50)
    
    # Get configuration
    jira_url = CONFIG.get("JIRA_INSTANCE_URL", "")
    jira_username = CONFIG.get("JIRA_USERNAME", "")
    jira_token = CONFIG.get("JIRA_API_TOKEN", "")
    
    # Display configuration (mask token)
    print(f"📋 Configuration loaded:")
    print(f"   JIRA_INSTANCE_URL: {jira_url}")
    print(f"   JIRA_USERNAME: {jira_username}")
    print(f"   JIRA_API_TOKEN: {'***' + jira_token[-4:] if len(jira_token) > 4 else 'MISSING'}")
    print()
    
    # Check if all required fields are present
    missing_fields = []
    if not jira_url:
        missing_fields.append("JIRA_INSTANCE_URL")
    if not jira_username:
        missing_fields.append("JIRA_USERNAME")
    if not jira_token:
        missing_fields.append("JIRA_API_TOKEN")
    
    if missing_fields:
        print(f"❌ Missing required fields in .env: {', '.join(missing_fields)}")
        print("\n📝 Please add these to your .env file:")
        for field in missing_fields:
            print(f"   {field}=your_value_here")
        return False
    
    # Test 1: Basic connectivity
    print("🔗 Test 1: Basic connectivity to Jira")
    try:
        # Remove trailing slash and add api endpoint
        base_url = jira_url.rstrip('/')
        test_url = f"{base_url}/rest/api/2/myself"
        
        response = requests.get(
            test_url,
            auth=HTTPBasicAuth(jira_username, jira_token),
            timeout=10,
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Connection successful!")
            print(f"   Authenticated as: {user_info.get('displayName', 'Unknown')}")
            print(f"   Account ID: {user_info.get('accountId', 'Unknown')}")
            print(f"   Email: {user_info.get('emailAddress', 'Unknown')}")
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401)")
            print(f"   Please check your username and API token")
            return False
        elif response.status_code == 403:
            print(f"❌ Access forbidden (403)")
            print(f"   Your user may not have sufficient permissions")
            return False
        else:
            print(f"❌ Connection failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print(f"❌ Connection timeout to {jira_url}")
        print(f"   Please check if the URL is correct and accessible")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error to {jira_url}")
        print(f"   Please check if the URL is correct and you have internet access")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print()
    
    # Test 2: Search permissions
    print("🔍 Test 2: Search permissions")
    try:
        search_url = f"{base_url}/rest/api/2/search"
        jql = f"assignee = '{jira_username}'"
        
        response = requests.get(
            search_url,
            auth=HTTPBasicAuth(jira_username, jira_token),
            params={"jql": jql, "maxResults": 5},
            timeout=10,
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            search_result = response.json()
            total_issues = search_result.get('total', 0)
            print(f"✅ Search successful!")
            print(f"   Found {total_issues} tickets assigned to you")
            
            # Show first few tickets
            if total_issues > 0:
                print(f"   📋 Sample tickets:")
                for issue in search_result.get('issues', [])[:3]:
                    key = issue.get('key', 'Unknown')
                    summary = issue.get('fields', {}).get('summary', 'No summary')
                    status = issue.get('fields', {}).get('status', {}).get('name', 'Unknown')
                    print(f"      • {key}: {summary} ({status})")
            else:
                print(f"   ℹ️ No tickets currently assigned to {jira_username}")
                
        else:
            print(f"❌ Search failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False
    
    print()
    
    # Test 3: Environment variables for MCP server
    print("🔧 Test 3: Environment variables for MCP server")
    mcp_env_vars = {
        "JIRA_URL": jira_url,
        "JIRA_INSTANCE_URL": jira_url,
        "JIRA_USERNAME": jira_username,
        "JIRA_TOKEN": jira_token,
        "JIRA_API_TOKEN": jira_token
    }
    
    print("✅ Environment variables ready for MCP server:")
    for key, value in mcp_env_vars.items():
        masked_value = value
        if 'TOKEN' in key and value:
            masked_value = '***' + value[-4:] if len(value) > 4 else '***'
        print(f"   {key}={masked_value}")
    
    print()
    print("🎉 All tests passed! Your Jira configuration is working correctly.")
    print("🚀 The MCP integration should now be able to fetch real Jira data.")
    return True


if __name__ == "__main__":
    try:
        success = test_jira_connection()
        if success:
            print("\n✅ Configuration test PASSED")
            sys.exit(0)
        else:
            print("\n❌ Configuration test FAILED")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
