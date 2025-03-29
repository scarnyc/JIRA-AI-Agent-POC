document.addEventListener('DOMContentLoaded', function() {
    const issueForm = document.getElementById('issue-form');
    const createButton = document.getElementById('create-button');
    const resultsCard = document.getElementById('results-card');
    const resultsContainer = document.getElementById('results-container');
    const progressIndicator = document.getElementById('progress-indicator');
    const currentCount = document.getElementById('current-count');
    const totalCount = document.getElementById('total-count');
    const completionMessage = document.getElementById('completion-message');

    issueForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Clear previous results
        resultsContainer.innerHTML = '';
        completionMessage.style.display = 'none';
        
        // Show results card
        resultsCard.style.display = 'block';
        
        // Get form data
        const formData = new FormData(issueForm);
        const summariesText = formData.get('summaries');
        
        // Count non-empty lines for progress tracking
        const nonEmptyLines = summariesText.split('\n')
            .filter(line => line.trim() !== '')
            .length;
        
        // Update progress display
        totalCount.textContent = nonEmptyLines;
        currentCount.textContent = '0';
        progressIndicator.style.display = 'block';
        
        // Disable submit button during processing
        createButton.disabled = true;
        createButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
        
        try {
            // Send the form data to the server
            const response = await fetch('/create_issues', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Unknown error occurred');
            }
            
            // Display results
            data.results.forEach((result, index) => {
                // Update progress counter
                currentCount.textContent = (index + 1).toString();
                
                // Create result item
                const resultItem = document.createElement('div');
                resultItem.className = 'mb-2 p-2 border-bottom';
                
                // Format the summary with original format markers
                const originalSummary = summariesText.split('\n')
                    .filter(line => line.trim() !== '')
                    [index] || result.summary;
                
                // Create result content with proper styling based on success/failure
                const statusClass = result.success ? 'success-message' : 'error-message';
                const statusIcon = result.success ? 
                    '<i class="fas fa-check-circle me-2"></i>' : 
                    '<i class="fas fa-exclamation-circle me-2"></i>';
                
                resultItem.innerHTML = `
                    <div><strong>${originalSummary}</strong></div>
                    <div class="${statusClass}">
                        ${statusIcon}${result.message}
                    </div>
                    <div class="small text-muted mt-1">${result.details}</div>
                `;
                
                resultsContainer.appendChild(resultItem);
            });
            
            // Show completion message
            completionMessage.style.display = 'block';
            
        } catch (error) {
            // Display error message
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error: ${error.message}
                </div>
            `;
        } finally {
            // Hide progress indicator
            progressIndicator.style.display = 'none';
            
            // Re-enable submit button
            createButton.disabled = false;
            createButton.innerHTML = '<i class="fas fa-plus-circle me-2"></i>Create Jira Issues';
        }
    });
});
