# Tahecho - AI-Powered Jira Assistant

Tahecho is your new product team member that likes to make process effective, easy and help everyone on the team, it wears the hats of scrum master, agile coach, product owner or project manager.

## Features

You can ask the bot things as:
* "Show me my Jira issues"
* "What tasks are assigned to me?"
* "List my Jira tasks"
* "Create a summary of the task Project X finished this week."
* "Create an email of Project X for the stakeholders."

## Integrations
* Jira Cloud
* Neo4j Graph Database
* OpenAI GPT-4

## Architecture

Tahecho uses a multi-agent system built with LangChain and LangGraph:
- **Manager Agent**: Orchestrates and routes tasks to specialized agents
- **MCP Agent**: Handles direct Jira operations (create, read, update issues)
- **Graph Agent**: Performs complex reasoning using Neo4j graph database
- **Task Classifier**: Determines which agent should handle each request

## Setup and Installation

### Prerequisites

- Python 3.11+
- Neo4j Database (local or cloud)
- Jira Cloud account with API access
- OpenAI API key

### Using Docker (Production)

1. Make sure you have Docker and Docker Compose installed on your system
2. Clone this repository
3. Create a `.env` file based on `.env.example`
   * For Jira API tokens, go to: https://id.atlassian.com/manage-profile/security/api-tokens
4. Build and start the Docker container:
   ```bash
   docker compose up --build
   ```

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tahecho
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # - OPENAI_API_KEY
   # - JIRA_INSTANCE_URL
   # - JIRA_USERNAME
   # - JIRA_API_TOKEN
   ```

5. **Set up Neo4j (choose one option)**

   **Option A: Local Neo4j**
   ```bash
   # Install Neo4j Desktop or use Docker
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test1234 neo4j:5
   ```

   **Option B: Neo4j AuraDB (Cloud)**
   - Create account at https://neo4j.com/cloud/platform/aura-graph-database/
   - Update connection string in your code

6. **Set up MCP Server (optional for local development)**
   ```bash
   # The MCP server is included in Docker setup
   # For local development, you can run it separately or mock the tools
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

## Development Workflow

### Test-Driven Development (TDD)

We follow the **Red-Green-Refactor** cycle:

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=utils --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run tests in watch mode (requires pytest-watch)
ptw

# Run tests with verbose output
pytest -v
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

### Docker (Production)
```bash
docker compose up --build
```
The application will be available at http://localhost:8000

### Local Development
```bash
python app.py
```
The application will be available at http://localhost:8000

### Stop the Application
```bash
# Docker
docker compose down

# Local
Ctrl+C
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | Yes |
| `JIRA_INSTANCE_URL` | Jira Cloud instance URL | Yes |
| `JIRA_USERNAME` | Jira username/email | Yes |
| `JIRA_API_TOKEN` | Jira API token | Yes |
| `JIRA_CLOUD` | Set to "true" for Jira Cloud | Yes |

### Neo4j Configuration

Update the connection string in `utils/utils.py`:
```python
uri = "bolt://localhost:7687"  # Local Neo4j
# or
uri = "bolt://your-aura-instance.neo4j.io:7687"  # AuraDB
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Neo4j Connection**: Verify Neo4j is running and accessible
   ```bash
   # Test connection
   python -c "from py2neo import Graph; g = Graph('bolt://localhost:7687', auth=('neo4j', 'test1234')); print('Connected!')"
   ```

3. **Jira API Issues**: Check your API token and permissions
   ```bash
   # Test Jira connection
   python -c "from jira_integration.jira_client import jira_client; print(jira_client.get_instance())"
   ```

4. **OpenAI API Issues**: Verify your API key and quota
   ```bash
   # Test OpenAI connection
   python -c "from openai import OpenAI; client = OpenAI(api_key='your-key'); print('Valid key!')"
   ```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Write tests first (TDD approach)
4. Implement the feature
5. Ensure all tests pass
6. Submit a pull request

### Development Guidelines

- Follow TDD: Write tests before implementation
- Maintain 90%+ test coverage
- Use type hints throughout
- Follow PEP 8 style guidelines
- Write clear commit messages
- Update documentation for new features

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Third-Party Software

This project uses third-party software components. For detailed information about these components and their licenses, please see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
