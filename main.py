#python
# Imports for Flask app and Jira integration
import os
import logging
import re
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # Change this in production

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        submitted_password = request.form.get('password')
        logger.debug(f"Login attempt - Submitted password length: {len(submitted_password) if submitted_password else 0}")
        logger.debug(f"Expected password length: {len(ADMIN_PASSWORD) if ADMIN_PASSWORD else 0}")
        if submitted_password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        logger.warning("Invalid password attempt")
        return render_template('login.html', error="Invalid password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

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
        # Initialize LLM with timeout and optimized settings
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=GEM_API_KEY,
            temperature=0.1,
            timeout=30,
            max_retries=2,
            max_output_tokens=1024
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
        logger.error(error_msg)
        raise Exception(error_msg)
    
    if not agent_executor:
        error_msg = "ERROR: Jira integration not properly initialized"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    try:
        logger.info(f"Creating Jira issue with summary: {summary}")
        logger.info(f"Description: {description}")
        
        # Create a properly formatted JSON structure
        issue_data = {
            "summary": summary,
            "description": description if description else "",
            "project": {"key": PROJECT_KEY},
            "issuetype": {"name": "Task"}
        }
        
        prompt = f"Create a Jira issue with this exact data: {issue_data}"
        
        # Invoke the agent using the structure expected by create_react_agent
        response = agent_executor.invoke({"messages": [HumanMessage(content=prompt)]})

        # Extract the final response from the agent's output messages
        if response and 'messages' in response and response['messages']:
            final_response = response['messages'][-1].content
            
            # Log the full response for debugging
            logger.debug(f"Full agent response: {response}")
            logger.debug(f"Final response content: {final_response}")
            
            # Check if the response indicates success and contains an issue key
            if "created" in final_response.lower() and "ABD-" in final_response:
                return final_response
            else:
                error_msg = f"Issue creation failed: {final_response}"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            error_msg = "Invalid response format from agent"
            logger.error(error_msg)
            raise Exception(error_msg)

    except Exception as e:
        error_msg = f"Error creating Jira issue: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

# Functions for batch processing (from jira_batch_creator.py)
def parse_summaries_and_descriptions(summaries_text):
    """
    Parse the input text which contains comma-separated summaries and descriptions.
    Format: "Summary, Description" (one per line)
    Returns a list of dictionaries with 'summary' and 'description' keys.
    """
    # Split the text by lines
    lines = summaries_text.split('\n')
    
    # Clean up and parse each line
    parsed_items = []
    for line in lines:
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Remove common list markers (1., etc.) at the beginning
        cleaned_line = re.sub(r'^\s*(?:\*|\-|\d+\.|\•|\+)\s*', '', line).strip()
        
        # Skip if line is empty after cleaning
        if not cleaned_line:
            continue
        
        # Split by first comma to separate summary and description
        parts = cleaned_line.split(',', 1)
        summary = parts[0].strip()
        
        # If there's a description part, use it; otherwise, leave it empty
        description = parts[1].strip() if len(parts) > 1 else ""
        
        # Add to the list if we have a valid summary
        if summary:
            parsed_items.append({
                'summary': summary,
                'description': description
            })
    
    return parsed_items

def process_summaries(summaries_text, global_description=""):
    """
    Process each summary and its description and create a Jira issue for it.
    Returns a list of results with status and details for each issue.
    """
    # Parse summaries and descriptions from the input text using our new parsing function
    issues = parse_summaries_and_descriptions(summaries_text)
    
    # Process each issue
    results = []
    for i, issue in enumerate(issues):
        try:
            summary = issue['summary']
            # Use individual description if provided, otherwise use global description
            description = issue['description'] if issue['description'] else global_description
            
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
                "summary": issue['summary'],
                "success": False,
                "message": f"ERROR: {str(e)}",
                "details": str(e)
            })
    
    return results

# Flask routes
@app.route('/')
@login_required
def index():
    """Render the main page with the batch issue creator form."""
    return render_template('index.html')

@app.route('/create_issues', methods=['POST'])
def create_issues():
    """Process submitted issues with summaries and descriptions and create Jira issues."""
    try:
        # Get form data
        summaries_text = request.form.get('summaries', '')
        
        # Process summaries and create issues (passing empty global description)
        results = process_summaries(summaries_text)
        
        return jsonify({"success": True, "results": results})
    except Exception as e:
        logger.error(f"Error in create_issues: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Server startup
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)