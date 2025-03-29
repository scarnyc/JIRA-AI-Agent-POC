#python
# Imports for Flask app and Jira integration
import os
import logging
import re
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Jira integration imports
try:
    from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
    from langchain_community.utilities.jira import JiraAPIWrapper
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage
    jira_imports_failed = False
except ImportError as e:
    logger.error(f"Failed to import Jira integration modules: {str(e)}")
    jira_imports_failed = True

# Environment variables (ensure these are set in your environment)
GEM_API_KEY = os.environ.get("GEM_API_KEY")
JIRA_USERNAME = os.environ.get("JIRA_USERNAME")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
JIRA_INSTANCE_URL = os.environ.get("JIRA_INSTANCE_URL")
JIRA_CLOUD = os.environ.get("JIRA_CLOUD", "False") # Default to False if not set
PROJECT_KEY = os.environ.get("PROJECT_KEY")

# Check for missing environment variables
required_vars = ["GEM_API_KEY", "JIRA_USERNAME", "JIRA_API_TOKEN", "JIRA_INSTANCE_URL", "PROJECT_KEY"]
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    print(f"WARNING: Missing required environment variables: {', '.join(missing_vars)}")
    print("The application will load, but Jira integration will not function properly until these are set.")

# Initialize variables for Jira integration
llm = None
jira = None
toolkit = None
tools = None
agent_executor = None

# Only initialize if all required env vars are present
if not missing_vars:
    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-exp-03-25", # Consider if a different Gemini model is needed
            google_api_key=GEM_API_KEY,
            temperature=0.1,
            # Add convert_system_message_to_human=True if needed for compatibility
            # convert_system_message_to_human=True
        )

        # Initialize Jira API wrapper with proper configuration
        jira = JiraAPIWrapper(
            jira_username=JIRA_USERNAME,
            jira_api_token=JIRA_API_TOKEN,
            jira_instance_url=JIRA_INSTANCE_URL,
            jira_cloud=(JIRA_CLOUD.lower() == "true")
        )

        # Create the toolkit and get tools
        toolkit = JiraToolkit.from_jira_api_wrapper(jira)
        tools = toolkit.get_tools()

        # Create the LangGraph ReAct agent [cite: 16, 26]
        # Note: Ensure the LLM is compatible. You might need to wrap it or adjust settings.
        # LangGraph agents often work best with models specifically fine-tuned for function calling/tool use.
        agent_executor = create_react_agent(llm, tools)
        
        print("Jira integration initialized successfully!")
    except Exception as e:
        print(f"Error initializing Jira integration: {str(e)}")
        missing_vars = ["INITIALIZATION_ERROR"]

def create_jira_issue_langgraph(summary, description=None):
    """Helper function to create a Jira issue using LangGraph ReAct agent"""
    # Check if integration is available
    if missing_vars:
        error_msg = f"ERROR: Jira integration not available. Missing environment variables: {', '.join(missing_vars)}"
        print(error_msg)
        return error_msg
    
    if not agent_executor:
        error_msg = "ERROR: Jira integration not properly initialized"
        print(error_msg)
        return error_msg
    
    try:
        prompt = f"Make a new issue in project {PROJECT_KEY} with summary '{summary}'"
        if description:
            prompt += f" and description '{description}'"

        # Invoke the agent using the structure expected by create_react_agent [cite: 17, 27]
        # The input is typically a dictionary with a "messages" key
        response = agent_executor.invoke({"messages": [HumanMessage(content=prompt)]})

        # Extract the final response from the agent's output messages
        # The exact structure might vary slightly based on LangGraph version
        final_response = response['messages'][-1].content
        return final_response

    except Exception as e:
        error_msg = f"Error creating Jira issue with LangGraph agent: {str(e)}"
        print(error_msg)
        return error_msg

# Functions for batch processing (from jira_batch_creator.py)
def parse_summaries(summaries_text):
    """
    Parse the summaries text input, handling different list formats and empty lines.
    Returns a list of cleaned summaries.
    """
    # Split the text by lines
    lines = summaries_text.split('\n')
    
    # Clean up summaries
    cleaned_summaries = []
    for line in lines:
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Remove common list markers (*, -, 1., etc.)
        cleaned_line = re.sub(r'^\s*(?:\*|\-|\d+\.|\•|\+)\s*', '', line).strip()
        
        # Skip if line is empty after cleaning
        if cleaned_line:
            cleaned_summaries.append(cleaned_line)
    
    return cleaned_summaries

def process_summaries(summaries_text, description=""):
    """
    Process each summary and create a Jira issue for it.
    Returns a list of results with status and details for each summary.
    """
    # Parse summaries from the input text
    summaries = parse_summaries(summaries_text)
    
    # Process each summary
    results = []
    for i, summary in enumerate(summaries):
        try:
            # Call the function to create the issue
            response = create_jira_issue_langgraph(summary, description)
            
            # Check if the response contains a successful issue creation message
            # (This is a simple heuristic; adjust based on actual response format)
            if response and ("created" in response.lower() or "success" in response.lower()):
                # Extract issue key if present (format like "ABC-123")
                match = re.search(r'([A-Z]+-\d+)', response)
                issue_key = match.group(1) if match else "Unknown"
                
                results.append({
                    "summary": summary,
                    "success": True,
                    "message": f"SUCCESS: Issue {issue_key} created",
                    "details": response
                })
            else:
                # Response exists but doesn't indicate success
                results.append({
                    "summary": summary,
                    "success": False,
                    "message": "ERROR: Issue creation failed",
                    "details": response or "No response received"
                })
        except Exception as e:
            # Exception occurred during issue creation
            results.append({
                "summary": summary,
                "success": False,
                "message": f"ERROR: {str(e)}",
                "details": str(e)
            })
    
    return results

# Flask routes
@app.route('/')
def index():
    """Render the main page with the batch issue creator form."""
    return render_template('index.html')

@app.route('/create_issues', methods=['POST'])
def create_issues():
    """Process submitted summaries and create Jira issues."""
    try:
        # Get form data
        summaries_text = request.form.get('summaries', '')
        description = request.form.get('description', '')
        
        # Process summaries and create issues
        results = process_summaries(summaries_text, description)
        
        return jsonify({"success": True, "results": results})
    except Exception as e:
        logger.error(f"Error in create_issues: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Server startup
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)