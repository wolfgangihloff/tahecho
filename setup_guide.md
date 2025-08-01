# Tahecho Setup Guide

## Overview
Tahecho is a personal assistant that can work with or without a graph database (Neo4j). The app will automatically detect if Neo4j is available and adjust its functionality accordingly.

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required Variables
```bash
# OpenAI API Key (required)
OPENAI_API_KEY=your_openai_api_key_here

# Jira Configuration (required for Jira functionality)
JIRA_INSTANCE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_email@domain.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_CLOUD=True
```

### Optional Graph Database Variables
```bash
# Graph Database Configuration (optional)
GRAPH_DB_ENABLED=True  # Set to False to disable graph database completely
NEO4J_URI=bolt://neo4j:7687  # Default Neo4j connection URI
NEO4J_USERNAME=neo4j  # Default Neo4j username
NEO4J_PASSWORD=test1234  # Default Neo4j password
```

## Running Modes

### Mode 1: Full Mode (with Neo4j)
When `GRAPH_DB_ENABLED=True` and Neo4j is running:
- Full functionality including complex relationship analysis
- Historical change tracking
- Dependency chain analysis
- Advanced graph-based queries

### Mode 2: Limited Mode (without Neo4j)
When `GRAPH_DB_ENABLED=False` or Neo4j is not available:
- Basic Jira operations via MCP agent
- Direct issue queries and management
- No complex relationship analysis
- No historical change tracking

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create your `.env` file with the required variables listed above.

### 3. Test Setup
Run the diagnostic script to verify your configuration:
```bash
python tests/smoke/test_setup.py
```

### 4. Start Neo4j (Optional - for Full Mode)
If you want full functionality with graph database:

#### Using Docker:
```bash
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test1234 \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:latest
```

#### Using Docker Compose:
```bash
docker-compose up -d neo4j
```

### 5. Run the Application

#### Full Mode (with Neo4j):
```bash
chainlit run app.py
```

#### Minimal Mode (without Neo4j):
```bash
chainlit run app_minimal.py
```

## Configuration Options

### Disabling Graph Database Completely
Set in your `.env` file:
```bash
GRAPH_DB_ENABLED=False
```

### Custom Neo4j Connection
If your Neo4j is running on a different host or port:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
```

## Troubleshooting

### Graph Database Connection Issues
1. Check if Neo4j is running: `docker ps | grep neo4j`
2. Verify connection settings in `.env`
3. Test connection: `python -c "from utils.graph_db import graph_db_manager; print(graph_db_manager.connect())"`

### App Won't Start
1. Verify all required environment variables are set
2. Check OpenAI API key is valid
3. Ensure Jira credentials are correct
4. Run diagnostic script: `python tests/smoke/test_setup.py`

### Limited Functionality
If you see "Running in limited mode" message:
- Neo4j is not available or not configured
- App will still work for basic Jira operations
- For full functionality, start Neo4j and ensure `GRAPH_DB_ENABLED=True`

## Features by Mode

| Feature | Full Mode | Limited Mode |
|---------|-----------|--------------|
| Basic Jira queries | ✅ | ✅ |
| Issue status updates | ✅ | ✅ |
| Task management | ✅ | ✅ |
| Relationship analysis | ✅ | ❌ |
| Dependency chains | ✅ | ❌ |
| Historical changes | ✅ | ❌ |
| Complex reasoning | ✅ | ❌ |

The app will automatically detect the available mode and adjust its behavior accordingly. 