# JIRA AI Agent POC

A web-based tool that allows users to create multiple Jira issues in batch. Built with Flask and integrated with the Jira API using LangGraph ReAct agent.

## Demo

Click on the link to watch the demo:

https://drive.google.com/file/d/15FwEoQl3gkTTJe78q1ThP9oXb6mxdzPK/view?usp=drive_link

## Features

- Create multiple Jira issues at once
- Support for comma-separated summaries and descriptions
- Real-time status updates for each issue creation
- Error handling and feedback

## Configuration

The following environment variables are required:

- `GEM_API_KEY`: Google Gemini API key
- `JIRA_USERNAME`: Jira username
- `JIRA_API_TOKEN`: Jira API token
- `JIRA_INSTANCE_URL`: Your Jira instance URL
- `PROJECT_KEY`: Jira project key
- `JIRA_CLOUD`: Set to "True" for Jira Cloud, "False" for Server (optional)

## Usage

1. Enter issue summaries and descriptions in the format:
   ```
   Summary, Description
   ```
   (one per line)

2. Click "Create Issues" to process the batch
3. View real-time results and status for each issue

## Running the Application

The application runs on https://jira-ai-agent-poc-willscardino.replit.app/

## Application Logic

1. **Web Interface** (`templates/index.html`):
   - Provides a textarea where users enter multiple JIRA issues
   - Each line follows format: "Summary, Description"
   - Shows real-time feedback as issues are created

2. **Main Application Flow** (`main.py` and `app.py`):
   - Flask server runs on port 5000
   - Two main routes:
     - `/`: Shows the input form
     - `/create_issues`: Handles POST requests to create issues

3. **Issue Processing** (`jira_batch_creator.py`):
   - `parse_summaries()`: Splits input text into individual issues
   - `process_summaries()`: For each issue:
     1. Parses summary and description
     2. Calls `create_jira_issue_langgraph()` to create the issue
     3. Returns success/error status for each issue

4. **JIRA Integration** (`main.py`):
   - Uses LangGraph ReAct agent to interact with JIRA
   - `create_jira_issue_langgraph()`:
     - Takes summary and description
     - Formats proper JSON for JIRA API
     - Creates issue via agent
     - Returns response/error

## PRD

https://docs.google.com/document/d/1C642V9Ut3UddNH2gt0VZPZGZ5YpnUk5GlxV9QxoGcX8/edit?pli=1&tab=t.4ybsqm6bvynq

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
