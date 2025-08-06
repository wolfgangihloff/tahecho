# Tahecho - AI-Powered Jira Assistant

Tahecho is your new product team member that likes to make process effective, easy and help everyone on the team, it wears the hats of scrum master, agile coach, product owner or project manager.

## Features

You can ask the bot things like:
* **"What tickets are assigned to me?"** - Lists your assigned Jira tickets
* **"Please create a new ticket in project PGA with the content: Implement user authentication feature"** - Creates new tickets
* **"Show me all tickets in the PGA project"** - Lists all tickets in a project
* **"Get details for ticket PGA-123"** - Gets detailed information about specific tickets
* "Create a summary of the task Project X finished this week."
* "Create an email of Project X for the stakeholders."

## Running Modes

Tahecho can run in two modes:

### Full Mode (with Neo4j Graph Database)
- **Complex relationship analysis** - Understand dependencies between issues
- **Historical change tracking** - See what changed and when
- **Dependency chain analysis** - Find blocking relationships
- **Advanced graph-based queries** - Semantic search and reasoning
- **All basic Jira operations** - Create, read, update issues

### Limited Mode (without Neo4j)
- **Basic Jira operations** - Direct issue management
- **Task queries and updates** - Status changes, assignments
- **MCP agent functionality** - Direct Jira API access
- **No advanced analysis** - Limited to basic operations

The app automatically detects which mode to use based on Neo4j availability.

## Integrations
* **Jira Cloud** - Full API integration using MCP Atlassian server
* **Neo4j Graph Database** (optional) - For advanced relationship analysis
* **OpenAI GPT-4** - For natural language processing
* **MCP (Model Context Protocol)** - For structured Jira interactions

## Architecture

Tahecho uses a multi-agent system built with LangChain and LangGraph:
- **Manager Agent**: Orchestrates and routes tasks to specialized agents
- **Jira MCP Agent**: Handles Jira-specific operations using MCP Atlassian server
- **MCP Agent**: Handles direct Jira operations (create, read, update issues)
- **Graph Agent**: Performs complex reasoning using Neo4j graph database (when available)
- **Task Classifier**: Determines which agent should handle each request

## Setup and Installation

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- Jira Cloud account with API access
- OpenAI API key
- Neo4j Database (optional, for full mode)
- [uv](https://github.com/astral-sh/uv) for MCP server management (installed automatically)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tahecho
   ```

2. **Install dependencies**
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install project dependencies
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # - OPENAI_API_KEY (required)
   # - JIRA_INSTANCE_URL (required)
   # - JIRA_USERNAME (required)
   # - JIRA_API_TOKEN (required)
   # - GRAPH_DB_ENABLED (optional, defaults to True)
   ```

4. **Test your setup**
   ```bash
   poetry run python tests/smoke/test_setup.py
   ```

5. **Start the MCP-Atlassian server** (required for Jira integration)
   ```bash
   # Option 1: Use the helper script (recommended)
   python start_mcp_server.py
   
   # Option 2: Start manually
   uvx mcp-atlassian
   ```

6. **Run the application**
   ```bash
   # Using Poetry (recommended)
   poetry run chainlit run app.py
   
   # For development with auto-reload
   poetry run chainlit run app.py --watch
   
   # Or minimal mode (no Neo4j required)
   poetry run chainlit run app_minimal.py
   ```

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up Neo4j (optional - for full mode)**

   **Neo4j AuraDB (Cloud)**
   - Create account at https://neo4j.com/cloud/platform/aura-graph-database/
   - Update connection string in your `.env` file
   
   **Local Neo4j Installation**
   - Download and install Neo4j Desktop from https://neo4j.com/download/
   - Create a new database with APOC plugin enabled
   - Update connection details in your `.env` file

4. **Run the application**
   ```bash
   poetry run chainlit run app.py
   ```

## Jira MCP Integration

Tahecho uses the [MCP Atlassian server](https://github.com/sooperset/mcp-atlassian) to provide seamless integration with Jira. 

### Setup Requirements

**IMPORTANT**: You must start the MCP-Atlassian server before using Jira features:

```bash
# Make sure your .env file contains your Jira credentials:
# JIRA_INSTANCE_URL=https://your-company.atlassian.net
# JIRA_USERNAME=your.email@company.com
# JIRA_API_TOKEN=your_api_token

# Start the MCP server (it reads from .env automatically)
uvx mcp-atlassian
```

Keep this server running in a separate terminal while using Tahecho.

### Supported Operations
- **Search tickets**: Find tickets assigned to you or in specific projects
- **Create tickets**: Generate new tasks, bugs, or stories
- **Get ticket details**: Retrieve comprehensive information about specific tickets
- **Update tickets**: Modify status, assignees, and other fields
- **JQL queries**: Use Jira Query Language for advanced filtering

### Example Queries
```
User: What tickets are assigned to me?
Assistant: You currently have 3 tickets assigned to you:
1. PGA-123: Implement new feature (In Progress)
2. PGA-456: Fix bug in login (To Do)  
3. PGA-789: Review documentation (Done)

User: Please create a new ticket in project PGA with the content: Implement user authentication feature
Assistant: Successfully created ticket PGA-124: Implement user authentication feature

User: Show me all tickets in the PGA project
Assistant: Here are the current tickets in the PGA project:
1. PGA-123: Implement new feature - Status: In Progress
2. PGA-456: Fix bug in login - Status: To Do
[... additional tickets]
```

### MCP Server Requirements
The integration automatically manages the MCP Atlassian server, but requires:
- Valid Jira Cloud credentials in your `.env` file
- Network access to your Jira instance
- The `uv` package manager (installed automatically with Poetry)

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | Yes | - |
| `JIRA_INSTANCE_URL` | Jira Cloud instance URL | Yes | - |
| `JIRA_USERNAME` | Jira username/email | Yes | - |
| `JIRA_API_TOKEN` | Jira API token | Yes | - |
| `JIRA_CLOUD` | Set to "true" for Jira Cloud | Yes | True |
| `GRAPH_DB_ENABLED` | Enable/disable graph database | No | True |
| `NEO4J_URI` | Neo4j connection URI | No | bolt://neo4j:7687 |
| `NEO4J_USERNAME` | Neo4j username | No | neo4j |
| `NEO4J_PASSWORD` | Neo4j password | No | test1234 |

### Disabling Graph Database

To run without Neo4j, set in your `.env` file:
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

## Testing and Diagnostics

### Test Setup
```bash
# Run comprehensive setup test
python tests/smoke/test_setup.py

# Demo different running modes
python demo_modes.py
```

### Troubleshooting

**Graph Database Issues:**
```bash
# Test connection
python -c "from utils.graph_db import graph_db_manager; print(graph_db_manager.connect())"
```

**App Won't Start:**
1. Verify all required environment variables are set
2. Check OpenAI API key is valid
3. Ensure Jira credentials are correct
4. Run diagnostic script: `python tests/smoke/test_setup.py`

**Limited Functionality:**
If you see "Running in limited mode" message:
- Neo4j is not available or not configured
- App will still work for basic Jira operations
- For full functionality, start Neo4j and ensure `GRAPH_DB_ENABLED=True`

**Jira MCP Issues:**
If Jira operations fail:
1. Verify Jira credentials are correct in `.env`
2. Test MCP server setup: `poetry run python scripts/setup_mcp_jira.py`
3. Check network connectivity to your Jira instance
4. Ensure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Module Import Errors:**
If you get `ModuleNotFoundError: No module named 'tahecho'`:
- Always use `poetry run` prefix for commands
- Example: `poetry run chainlit run app.py`
- Don't run `chainlit run app.py` directly

## Development Workflow

### Test-Driven Development (TDD)

We follow the **Red-Green-Refactor** cycle:

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test categories
poetry run pytest tests/unit/          # Unit tests
poetry run pytest tests/integration/   # Integration tests
poetry run pytest tests/smoke/         # Smoke tests

# Test Jira MCP integration specifically
poetry run python scripts/test_jira_integration.py

# Run tests in watch mode (requires pytest-watch)
poetry run ptw

# Run tests with verbose output
poetry run pytest -v
```

### Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_agents/        # Agent unit tests
│   ├── test_utils/         # Utility function tests
│   └── test_config/        # Configuration tests
├── integration/            # Integration tests (external dependencies)
│   ├── test_jira/         # Jira API integration
│   ├── test_neo4j/        # Neo4j integration
│   └── test_workflow/     # End-to-end workflow tests
├── fixtures/              # Test fixtures and mocks
│   ├── jira_mocks.py     # Jira API mocks
│   ├── neo4j_mocks.py    # Neo4j mocks
│   └── agent_mocks.py    # Agent mocks
└── conftest.py           # Pytest configuration
```

### Writing Tests

**Unit Test Example:**
```python
def test_task_classifier_mcp_task():
    """Test that Jira-related tasks are classified as MCP tasks."""
    # Arrange
    classifier = TaskClassifier()
    state = create_initial_state("Show me all open bugs in DTS project")
    
    # Act
    result_state = classifier.classify_task(state)
    
    # Assert
    assert result_state.task_type == "mcp"
```

**Integration Test Example:**
```python
def test_mcp_agent_creates_jira_issue():
    """Test that MCP agent can create a Jira issue."""
    # Arrange
    agent = LangChainMCPAgent()
    state = create_initial_state("Create a new task called 'Test Task' in project DTS")
    
    # Act
    result_state = agent.execute(state)
    
    # Assert
    assert "created" in result_state.agent_results["mcp_agent"].lower()
```

### Pre-commit Hooks

Install pre-commit hooks for code quality:
```bash
pip install pre-commit
pre-commit install
```

This will run:
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- pytest (tests)

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8
mypy .

# Run all quality checks
pre-commit run --all-files
```

## Running the Application

### Local Development
```bash
# Standard mode - using Poetry
poetry run chainlit run app.py

# Development mode with auto-reload (recommended for development)
poetry run chainlit run app.py --watch

# Development with debug mode and custom port
poetry run chainlit run app.py --watch --debug --port 8001

# Minimal mode (no Neo4j required)
poetry run chainlit run app_minimal.py

# If you get "ModuleNotFoundError: No module named 'tahecho'", use Poetry
```

The application will be available at http://localhost:8000

**💡 Development Tip:** Use the `--watch` flag to automatically reload the app when you make code changes - no need to stop and restart manually!

### Stop the Application
```bash
Ctrl+C
```

## Features by Mode

| Feature | Full Mode | Limited Mode |
|---------|-----------|--------------|
| Basic Jira queries | ✅ | ✅ |
| Issue status updates | ✅ | ✅ |
| Task management | ✅ | ✅ |
| **Jira MCP Integration** | ✅ | ✅ |
| **Create/Update tickets** | ✅ | ✅ |
| **JQL search queries** | ✅ | ✅ |
| **Ticket details retrieval** | ✅ | ✅ |
| Relationship analysis | ✅ | ❌ |
| Dependency chains | ✅ | ❌ |
| Historical changes | ✅ | ❌ |
| Complex reasoning | ✅ | ❌ |

The app will automatically detect the available mode and adjust its behavior accordingly.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## BSI TR-03183 Compliance

This project complies with German BSI TR-03183 cybersecurity standards, specifically Part 2 "Software Bill of Materials (SBOM)".

### SBOM Generation

#### Automated Generation (Recommended)
SBOM reports are automatically generated on every commit to the main branch via GitHub Actions and published to [GitHub Pages](https://your-username.github.io/tahecho/).

#### Manual Generation
Generate a Software Bill of Materials in CycloneDX format locally:

```bash
# Using Poetry script
poetry run generate-sbom

# Or directly
python scripts/generate_sbom.py
```

This will create:
- `sbom.json` - CycloneDX JSON format (BSI preferred)
- `sbom.xml` - CycloneDX XML format

### Compliance Features

✅ **CycloneDX Format** - Industry standard SBOM format supported by BSI  
✅ **Component Tracking** - All dependencies and their versions documented  
✅ **License Information** - Complete license compliance documentation  
✅ **Vulnerability Ready** - SBOM format supports vulnerability reporting  
✅ **Metadata** - BSI TR-03183 compliance markers included  
✅ **Automated CI/CD** - GitHub Actions generate reports on every commit  
✅ **GitHub Pages** - Reports published to dedicated compliance page
