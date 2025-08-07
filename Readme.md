# Tahecho - AI-Powered Jira Assistant

> 📋 **[View SBOM Reports & BSI TR-03183 Compliance Dashboard](https://wolfgang.ihloff.github.io/tahecho/)**  
> Complete Software Bill of Materials, security compliance status, and dependency tracking.

Tahecho is your new product team member that likes to make process effective, easy and help everyone on the team, it wears the hats of scrum master, agile coach, product owner or project manager.

## Features

You can ask the bot things like:
* **"What tickets are assigned to me?"** - Lists your assigned Jira tickets
* **"Please create a new ticket in project PGA with the content: Implement user authentication feature"** - Creates new tickets
* **"Show me all tickets in the PGA project"** - Lists all tickets in a project
* **"Get details for ticket PGA-123"** - Gets detailed information about specific tickets
* "Create a summary of the task Project X finished this week."
* "Create an email of Project X for the stakeholders."

## Key Capabilities

Tahecho provides powerful Jira management through natural language:
- **All Jira operations** - Create, read, update, and search issues
- **Natural language interface** - Ask questions in plain English
- **Task management** - Status changes, assignments, and tracking
- **MCP integration** - Direct, reliable Jira API access
- **Multi-agent workflow** - Intelligent task routing and processing

## Integrations
* **Jira Cloud** - Full API integration using MCP Atlassian server
* **OpenAI GPT-4** - For natural language processing
* **MCP (Model Context Protocol)** - For structured Jira interactions

## 🔒 Security & Compliance

Tahecho maintains comprehensive security compliance with automated SBOM generation and BSI TR-03183 compliance.

📋 **[View Complete SBOM Documentation](docs/SBOM_COMPLIANCE.md)** - Detailed compliance information, dashboard access, and technical implementation details.

## Architecture

Tahecho uses a multi-agent system built with LangChain and LangGraph:
- **Manager Agent**: Orchestrates and routes tasks using LangGraph workflow
- **Task Classifier**: Determines which agent should handle each request (Jira vs general)
- **Jira MCP Agent**: Handles all Jira operations using MCP Atlassian server

## Setup and Installation

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management (**REQUIRED** - all commands must use Poetry)
- Jira Cloud account with API access
- OpenAI API key
- [uv](https://github.com/astral-sh/uv) for MCP server management (installed automatically)

### Quick Start

**⚠️ IMPORTANT: Always use `poetry run` for all commands to ensure the correct Python environment and dependencies.**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tahecho
   ```

2. **Install Poetry and dependencies**
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install project dependencies with Poetry
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```
   
   Create a `.env` file in the project root with these **required** variables:
   ```bash
   # OpenAI API Key (required)
   OPENAI_API_KEY=your_openai_api_key_here

   # Jira Configuration (required for Jira functionality)
   JIRA_INSTANCE_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your_email@domain.com
   JIRA_API_TOKEN=your_jira_api_token
   JIRA_CLOUD=True
   ```

4. **Test your setup** (use Poetry!)
   ```bash
   poetry run pytest tests/smoke/test_setup.py -v
   ```

5. **Start the MCP-Atlassian server** (required for Jira integration)
   ```bash
   # Option 1: Use the helper script (recommended)
   poetry run python scripts/setup_mcp_jira.py
   
   # Option 2: Start manually (must have uv installed)
   uvx mcp-atlassian
   ```

6. **Run the application** (use Poetry!)
   ```bash
   # Standard mode (recommended)
   poetry run chainlit run app.py
   
   # For development with auto-reload
   poetry run chainlit run app.py --watch
   
   # With debug mode and custom port
   poetry run chainlit run app.py --watch --debug --port 8001
   ```

### How It Works

Tahecho provides streamlined Jira operations through:
- **Direct Jira operations** via MCP agent
- **Natural language queries** for ticket management
- **Task creation and updates** with simple commands
- **JQL query support** for advanced filtering

### Development Setup

**⚠️ CRITICAL: Use Poetry for ALL commands to ensure correct dependencies and Python environment.**

1. **Poetry manages the virtual environment automatically - no need to create one manually**
   ```bash
   # Poetry creates and manages the virtual environment for you
   poetry install  # This installs dependencies in Poetry's managed environment
   ```

2. **Verify Poetry environment**
   ```bash
   # Check which Python Poetry is using
   poetry env info
   
   # Run commands in Poetry environment (always use this pattern)
   poetry run python --version
   ```

3. **Run the application** (always with Poetry!)
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

### Configuration Options

All configuration is done through the `.env` file with the variables listed above.

## Testing and Diagnostics

### Test Setup

**⚠️ ALWAYS use Poetry for tests to ensure correct Python environment:**

```bash
# Run comprehensive setup test (MUST use Poetry!)
poetry run pytest tests/smoke/test_setup.py -v

# Run all unit tests (MUST use Poetry!)
poetry run pytest tests/unit/ -v

# Run all tests (MUST use Poetry!)
poetry run pytest -v

# Run tests with coverage (MUST use Poetry!)
poetry run pytest --cov=src --cov-report=html

# Run specific test categories (MUST use Poetry!)
poetry run pytest tests/unit/ -v          # Unit tests
poetry run pytest tests/integration/ -v   # Integration tests
poetry run pytest tests/smoke/ -v         # Smoke tests
```

### Troubleshooting

**⚠️ CRITICAL: All troubleshooting commands MUST use Poetry to work correctly.**

**App Won't Start:**
1. Verify all required environment variables are set
2. Check OpenAI API key is valid
3. Ensure Jira credentials are correct
4. Run diagnostic script: `poetry run pytest tests/smoke/test_setup.py -v`
5. Verify Poetry environment: `poetry env info`



**Jira MCP Issues:**
If Jira operations fail:
1. Verify Jira credentials are correct in `.env`
2. Test MCP server setup: `poetry run python scripts/setup_mcp_jira.py`
3. Check network connectivity to your Jira instance
4. Ensure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Module Import Errors - THE MOST COMMON ISSUE:**
If you get `ModuleNotFoundError: No module named 'tahecho'`:
- **ALWAYS use `poetry run` prefix for ALL commands**
- ✅ Correct: `poetry run chainlit run app.py`
- ❌ Wrong: `chainlit run app.py` (will fail)
- ✅ Correct: `poetry run pytest tests/`
- ❌ Wrong: `pytest tests/` (will fail)
- ✅ Correct: `poetry run python script.py`
- ❌ Wrong: `python script.py` (will fail)

**Poetry Environment Issues:**
```bash
# Check Poetry is managing the right environment
poetry env info

# Rebuild Poetry environment if needed
poetry env remove python
poetry install

# Always run commands through Poetry
poetry run python --version  # Should show Python 3.11+
```

## Development Workflow

### Test-Driven Development (TDD)

We follow the **Red-Green-Refactor** cycle:

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

### Running Tests

**⚠️ CRITICAL: ALL test commands MUST use Poetry - this is non-negotiable for correct operation.**

```bash
# Run all tests (MUST use Poetry!)
poetry run pytest

# Run with coverage (MUST use Poetry!)
poetry run pytest --cov=src --cov-report=html

# Run specific test categories (MUST use Poetry!)
poetry run pytest tests/unit/          # Unit tests
poetry run pytest tests/integration/   # Integration tests
poetry run pytest tests/smoke/         # Smoke tests

# Test Jira MCP integration specifically (MUST use Poetry!)
poetry run python scripts/test_jira_integration.py

# Run tests in watch mode (MUST use Poetry!)
poetry run ptw

# Run tests with verbose output (MUST use Poetry!)
poetry run pytest -v

# Run tests with specific markers (MUST use Poetry!)
poetry run pytest -m unit      # Only unit tests
poetry run pytest -m jira      # Only Jira-related tests
poetry run pytest -m mcp       # Only MCP-related tests
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

**⚠️ IMPORTANT: Use Poetry for all code quality tools to ensure consistent environment.**

```bash
# Format code (use Poetry!)
poetry run black .
poetry run isort .

# Lint code (use Poetry!)
poetry run flake8
poetry run mypy .

# Run all quality checks (use Poetry!)
poetry run pre-commit run --all-files

# Install pre-commit hooks (use Poetry environment)
poetry run pre-commit install
```

## Running the Application

**⚠️ CRITICAL: ALWAYS use `poetry run` to start the application - this is mandatory.**

### Local Development
```bash
# Standard mode (MUST use Poetry!)
poetry run chainlit run app.py

# Development mode with auto-reload (MUST use Poetry! - recommended for development)
poetry run chainlit run app.py --watch

# Development with debug mode and custom port (MUST use Poetry!)
poetry run chainlit run app.py --watch --debug --port 8001

# Check Poetry environment before running
poetry env info  # Verify Python version and path
```

**❌ NEVER run these commands (they will fail):**
```bash
# These will NOT work and will give ModuleNotFoundError:
chainlit run app.py           # ❌ Missing poetry run
python app.py                 # ❌ Missing poetry run
uvicorn app:app              # ❌ Missing poetry run
```

The application will be available at http://localhost:8000

**💡 Development Tip:** Use the `--watch` flag to automatically reload the app when you make code changes - no need to stop and restart manually!

### Stop the Application
```bash
Ctrl+C
```

## Features

Tahecho provides comprehensive Jira management capabilities:

| Feature | Status |
|---------|--------|
| **Basic Jira queries** | ✅ |
| **Issue status updates** | ✅ |
| **Task management** | ✅ |
| **Jira MCP Integration** | ✅ |
| **Create/Update tickets** | ✅ |
| **JQL search queries** | ✅ |
| **Ticket details retrieval** | ✅ |
| **Natural language processing** | ✅ |
| **Multi-agent workflow** | ✅ |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## BSI TR-03183 Compliance

This project complies with German BSI TR-03183 cybersecurity standards, specifically Part 2 "Software Bill of Materials (SBOM)".

### SBOM Generation

#### Automated Generation (Recommended)
SBOM reports are automatically generated during CI/CD pipelines and published to the `public/` folder for web serving and compliance documentation.

#### Manual Generation
Generate a Software Bill of Materials in CycloneDX format locally:

```bash
# Using Poetry script (generates to public/ folder)
poetry run generate-sbom

# Or directly
python scripts/generate_sbom.py
```

This will create:
- `public/sbom.json` - CycloneDX JSON format (BSI preferred)
- `public/sbom.xml` - CycloneDX XML format

Files are automatically placed in the `public/` directory for web serving and compliance distribution.

### Compliance Features

✅ **CycloneDX Format** - Industry standard SBOM format supported by BSI  
✅ **Component Tracking** - All dependencies and their versions documented  
✅ **License Information** - Complete license compliance documentation  
✅ **Vulnerability Ready** - SBOM format supports vulnerability reporting  
✅ **Metadata** - BSI TR-03183 compliance markers included  
✅ **Automated CI/CD** - GitHub Actions generate reports on every commit  
✅ **GitHub Pages** - Reports published to dedicated compliance page
