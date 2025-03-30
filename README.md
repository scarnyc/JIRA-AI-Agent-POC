
# JIRA AI Agent

A web-based tool that allows users to create multiple Jira issues in batch. Built with Flask and integrated with the Jira API using LangGraph ReAct agent.

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

The application runs on port 5000. Click the Run button to start the server.
