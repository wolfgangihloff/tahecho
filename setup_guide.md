# Tahecho Setup Guide

## ✅ Current Status

Your Tahecho project is **partially set up and working**:

- ✅ **LangChain 0.3.x** - Successfully migrated and working
- ✅ **OpenAI Integration** - Using new `init_chat_model` approach
- ✅ **Environment Variables** - Properly configured
- ✅ **Python Dependencies** - All installed via Poetry
- ❌ **Neo4j Database** - Not running (required for full functionality)

## Required Environment Variables

Your `.env` file should contain:

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Jira Configuration (OPTIONAL)
JIRA_INSTANCE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_jira_username
JIRA_API_TOKEN=your_jira_api_token
JIRA_CLOUD=True
```

## Testing Your Setup

### 1. Test LangChain Setup (Working ✅)
```bash
poetry run python app_minimal.py
```

### 2. Test Full Setup
```bash
poetry run python test_setup.py
```

## Running Options

### Option 1: Minimal Mode (No Neo4j)
```bash
poetry run python app_minimal.py
```
- ✅ Works immediately
- ✅ Tests LangChain integration
- ❌ No database persistence
- ❌ No Jira integration

### Option 2: Full Mode (With Neo4j)

#### Start Neo4j Database:
```bash
# Option A: Using Docker (recommended)
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test1234 neo4j:latest

# Option B: Using Docker Compose (if you have docker-compose.yml)
docker-compose up -d neo4j
```

#### Run Full Application:
```bash
poetry run python app.py
```

## Troubleshooting

### Docker Issues
If Docker isn't running:
1. Start Docker Desktop
2. Or install Docker: https://docs.docker.com/get-docker/

### Neo4j Connection Issues
- Make sure Neo4j is running: `docker ps | grep neo4j`
- Check if port 7687 is available: `lsof -i :7687`
- Restart Neo4j: `docker restart neo4j`

### Environment Variables
- Ensure `.env` file exists in project root
- Check variable names match exactly
- Restart terminal after adding new variables

## Next Steps

1. **For immediate testing**: Use `app_minimal.py` to test the LangChain integration
2. **For full functionality**: Start Neo4j and use `app.py`
3. **For development**: The setup is ready for development work

## Development Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Run linting
poetry run flake8
poetry run mypy .
``` 