Tahecho is your new product team member that likes to make process effective, easy and help everyone on the team, it wears the hats of scrum master, agile coach, product owner or project manager.

## Use
You can ask the bot things as:
* "Show me my Jira issues"
* "What tasks are assigned to me?"
* "List my Jira tasks"
* "Create a summary of the task Project X finished this week."
* "Create an email of Project X for the stakeholders."

## Integrations
* Jira Cloud


## Setup and Installation
### Using Docker

1. Make sure you have Docker and Docker Compose installed on your system
2. Clone this repository
3. Create a `.env` file based on `.env.example`
   * For Jira API tokens, go to: https://id.atlassian.com/manage-profile/security/api-tokens
4. Build and start the Docker container:
   ```bash
   docker compose up --build
   ```

## Running the Application

The application will be automatically started when using Docker and will be available at http://localhost:8000

To stop the application:
```bash
docker compose down
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Third-Party Software

This project uses third-party software components. For detailed information about these components and their licenses, please see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
