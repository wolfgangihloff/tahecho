#!/usr/bin/env python3
"""
Script to set up and test MCP Atlassian server connection for Jira integration.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_mcp_atlassian_installation():
    """Check if mcp-atlassian is installed and available."""
    try:
        result = subprocess.run(
            ["uvx", "mcp-atlassian", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info("✅ mcp-atlassian is installed and available")
            return True
        else:
            logger.error("❌ mcp-atlassian is not properly installed")
            return False
    except FileNotFoundError:
        logger.error("❌ uvx not found. Please install uv first.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ mcp-atlassian command timed out")
        return False


def check_jira_config():
    """Check if Jira configuration is available."""
    required_vars = [
        "JIRA_INSTANCE_URL",
        "JIRA_USERNAME", 
        "JIRA_API_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not CONFIG.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing Jira configuration: {', '.join(missing_vars)}")
        return False
    
    logger.info("✅ Jira configuration is available")
    return True


def test_mcp_connection():
    """Test the MCP Atlassian server connection."""
    try:
        # Build the command to start the MCP server
        cmd = [
            "uvx", "mcp-atlassian",
            "--jira-url", CONFIG["JIRA_INSTANCE_URL"],
            "--jira-username", CONFIG["JIRA_USERNAME"],
            "--jira-token", CONFIG["JIRA_API_TOKEN"],
            "--enabled-tools", "jira_search,jira_get_issue,jira_create_issue,jira_get_all_projects"
        ]
        
        # For Jira Cloud, no additional flag is needed
        # The --jira-token and --jira-username flags indicate Cloud authentication
        
        logger.info("Testing MCP Atlassian server connection...")
        logger.info(f"Command: {' '.join(cmd[:4])} [HIDDEN] {' '.join(cmd[5:])}")
        
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        import time
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info("✅ MCP Atlassian server started successfully")
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ MCP server failed to start")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing MCP connection: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("🔧 Setting up MCP Jira integration...")
    
    # Check prerequisites
    if not check_mcp_atlassian_installation():
        logger.info("📦 Installing mcp-atlassian...")
        try:
            subprocess.run(["uvx", "install", "mcp-atlassian"], check=True)
            logger.info("✅ mcp-atlassian installed successfully")
        except subprocess.CalledProcessError:
            logger.error("❌ Failed to install mcp-atlassian")
            return False
    
    if not check_jira_config():
        logger.error("❌ Please configure Jira credentials in your .env file")
        return False
    
    if not test_mcp_connection():
        logger.error("❌ MCP connection test failed")
        return False
    
    logger.info("🎉 MCP Jira integration setup completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
