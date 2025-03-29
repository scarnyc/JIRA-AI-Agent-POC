import os
import logging
from flask import Flask, render_template, request, jsonify
from jira_batch_creator import process_summaries

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
