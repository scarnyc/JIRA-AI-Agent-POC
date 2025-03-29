#python
import os
from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent # Import create_react_agent
from langchain_core.messages import HumanMessage # Import HumanMessage if needed for structuring input

# Environment variables (ensure these are set in your environment)
GEM_API_KEY = os.environ.get("GEM_API_KEY")
JIRA_USERNAME = os.environ.get("JIRA_USERNAME")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
JIRA_INSTANCE_URL = os.environ.get("JIRA_INSTANCE_URL")
JIRA_CLOUD = os.environ.get("JIRA_CLOUD", "False") # Default to False if not set
PROJECT_KEY = os.environ.get("PROJECT_KEY")

# Validate environment variables
required_vars = ["GEM_API_KEY", "JIRA_USERNAME", "JIRA_API_TOKEN", "JIRA_INSTANCE_URL", "PROJECT_KEY"]
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

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

def create_jira_issue_langgraph(summary, description=None):
    """Helper function to create a Jira issue using LangGraph ReAct agent"""
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
        print(f"Error creating Jira issue with LangGraph agent: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    result = create_jira_issue_langgraph("Make more fried rice (LangGraph)", "Remember to make more fried rice using the LangGraph agent.")
    print("\nLangGraph Agent Result:")
    print(result)