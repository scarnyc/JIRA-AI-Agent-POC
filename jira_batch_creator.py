import re
from main import create_jira_issue_langgraph

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
            # Call the function from main.py to create the issue
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
