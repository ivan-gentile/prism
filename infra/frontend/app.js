// PRISM-AD Frontend Application

const API_BASE_URL = 'http://127.0.0.1:8000';

// Example clinical cases
const exampleCases = {
    mild: `65-year-old female presenting with mild memory complaints over the past year.
MMSE score: 26/30, showing minor deficits in delayed recall.
Patient is ApoE4 negative.
CSF analysis: Aβ42 650 pg/mL (borderline), p-tau 35 pg/mL (normal).
No significant impairment in daily activities.
Family history: Mother diagnosed with AD at age 82.`,

    moderate: `72-year-old male with progressive cognitive decline over 18 months.
MMSE score: 22/30, MoCA: 19/30.
Patient is ApoE4 heterozygous (1 copy).
CSF biomarkers: Aβ42 450 pg/mL (low), p-tau 48 pg/mL (elevated), t-tau 580 pg/mL.
Mild difficulty with financial management but maintains basic ADLs.
Hippocampal volume reduction noted on MRI.`,

    high: `78-year-old female with significant memory loss and confusion.
MMSE score: 18/30, severe deficits in orientation and recall.
ApoE4 homozygous (2 copies).
CSF: Aβ42 380 pg/mL (very low), p-tau 65 pg/mL (high).
Amyloid PET positive with SUVR 1.62.
Requires assistance with medications and finances.
Episodes of getting lost in familiar places.`,

    comprehensive: `75-year-old male with memory complaints and cognitive decline over 2 years.
MMSE score: 23/30, showing deficits in recall and orientation.
Patient is ApoE4 positive (1 copy).
CSF analysis: Aβ42 480 pg/mL (low), p-tau 42 pg/mL (elevated).
Amyloid PET positive with SUVR 1.48.
Patient has difficulty managing finances but still independent in basic activities.
Neuropsych testing shows impaired executive function and processing speed.
FDG-PET shows hypometabolism in posterior cingulate and temporal regions.
Depression screening negative. No significant vascular burden on MRI.`
};

// Load example case
function loadExample(type = 'comprehensive') {
    const input = document.getElementById('clinicalInput');
    input.value = exampleCases[type] || exampleCases.comprehensive;
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
}

// Clear input
function clearInput() {
    document.getElementById('clinicalInput').value = '';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('processingSection').style.display = 'none';
}

// Perform assessment
async function performAssessment() {
    const input = document.getElementById('clinicalInput').value.trim();
    
    if (!input) {
        alert('Please enter clinical information or load an example case.');
        return;
    }
    
    // Show processing section
    document.getElementById('processingSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('progressLog').innerHTML = '';
    
    // Disable button
    const assessBtn = document.getElementById('assessBtn');
    assessBtn.disabled = true;
    assessBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    try {
        // Use streaming endpoint for real-time updates
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: input })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let finalResult = null;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    try {
                        const json = JSON.parse(data);
                        
                        if (json.event === 'progress') {
                            // Add progress message to log
                            addProgressMessage(json.data);
                        } else if (json.event === 'complete') {
                            // Processing complete
                            console.log('Processing complete');
                        } else if (json.event === 'error') {
                            throw new Error(json.data);
                        } else if (json.status === 'success') {
                            // Final result received
                            finalResult = json;
                        }
                    } catch (e) {
                        // If it's not JSON, treat as progress message
                        if (data.trim()) {
                            addProgressMessage(data);
                        }
                    }
                }
            }
        }
        
        // If we got a final result, display it
        if (finalResult) {
            displayResults(finalResult);
        } else {
            // Fallback to regular endpoint if streaming didn't provide results
            const fallbackResponse = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: input })
            });
            
            const fallbackData = await fallbackResponse.json();
            displayResultsFromText(fallbackData.response);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during assessment. Please check the console for details.');
    } finally {
        // Re-enable button
        assessBtn.disabled = false;
        assessBtn.innerHTML = '<i class="fas fa-stethoscope"></i> Perform Assessment';
    }
}

// Add progress message to log
function addProgressMessage(message) {
    const log = document.getElementById('progressLog');
    const item = document.createElement('div');
    item.className = 'progress-item';
    item.textContent = message;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
}

// Display results from structured data
function displayResults(data) {
    // Hide processing section
    document.getElementById('processingSection').style.display = 'none';
    
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
    
    // Update risk level with color coding
    const riskLevel = document.getElementById('riskLevel');
    riskLevel.textContent = data.risk_level || 'Not Assessed';
    riskLevel.className = 'risk-value';
    if (data.risk_level?.toLowerCase().includes('high')) {
        riskLevel.classList.add('high-risk');
    } else if (data.risk_level?.toLowerCase().includes('moderate')) {
        riskLevel.classList.add('moderate-risk');
    } else {
        riskLevel.classList.add('low-risk');
    }
    
    // Update FDA stage
    document.getElementById('fdaStage').textContent = data.fda_stage || 'Not Determined';
    
    // Update confidence
    const confidence = data.confidence_score || 'N/A';
    document.getElementById('confidence').textContent = 
        typeof confidence === 'number' ? `${(confidence * 100).toFixed(0)}%` : confidence;
    
    // Update executive summary
    document.getElementById('executiveSummary').textContent = 
        data.executive_summary || 'No summary available.';
    
    // Update key findings
    const findingsList = document.querySelector('.findings-list');
    findingsList.innerHTML = '';
    if (data.key_findings && data.key_findings.length > 0) {
        data.key_findings.forEach(finding => {
            const li = document.createElement('li');
            li.textContent = finding;
            findingsList.appendChild(li);
        });
    } else {
        findingsList.innerHTML = '<li>No specific findings available.</li>';
    }
    
    // Update recommendations
    const recommendationsList = document.querySelector('.recommendations-list');
    recommendationsList.innerHTML = '';
    if (data.clinical_recommendations && data.clinical_recommendations.length > 0) {
        data.clinical_recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            recommendationsList.appendChild(li);
        });
    } else {
        recommendationsList.innerHTML = '<li>No specific recommendations available.</li>';
    }
    
    // Update follow-up timeline
    document.getElementById('followUp').textContent = 
        data.follow_up_timeline || 'Follow-up timeline to be determined by clinical team.';
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Display results from text response (fallback)
function displayResultsFromText(responseText) {
    // Hide processing section
    document.getElementById('processingSection').style.display = 'none';
    
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
    
    // Parse the text response
    const riskMatch = responseText.match(/Risk Level:\*?\*?\s*([^\n]*)/i);
    const fdaMatch = responseText.match(/FDA Stage:\*?\*?\s*([^\n]*)/i);
    const confidenceMatch = responseText.match(/Confidence:\*?\*?\s*([^\n]*)/i);
    
    // Update risk level
    const riskLevel = document.getElementById('riskLevel');
    riskLevel.textContent = riskMatch ? riskMatch[1] : 'Not Assessed';
    riskLevel.className = 'risk-value';
    if (riskLevel.textContent.toLowerCase().includes('high')) {
        riskLevel.classList.add('high-risk');
    } else if (riskLevel.textContent.toLowerCase().includes('moderate')) {
        riskLevel.classList.add('moderate-risk');
    } else {
        riskLevel.classList.add('low-risk');
    }
    
    // Update FDA stage
    document.getElementById('fdaStage').textContent = 
        fdaMatch ? fdaMatch[1] : 'Not Determined';
    
    // Update confidence
    document.getElementById('confidence').textContent = 
        confidenceMatch ? confidenceMatch[1] : 'N/A';
    
    // Extract executive summary
    const summaryMatch = responseText.match(/Executive Summary:\*?\*?\s*([^*\n][^\n]*(?:\n[^*\n][^\n]*)*)/i);
    document.getElementById('executiveSummary').textContent = 
        summaryMatch ? summaryMatch[1].trim() : 'Assessment completed. See details below.';
    
    // Extract findings and recommendations (simple parsing)
    const findingsList = document.querySelector('.findings-list');
    const recommendationsList = document.querySelector('.recommendations-list');
    
    findingsList.innerHTML = '<li>Clinical assessment completed</li>';
    recommendationsList.innerHTML = '<li>Please consult with healthcare provider for detailed recommendations</li>';
    
    // Extract bullet points
    const bullets = responseText.match(/[•●]\s*([^\n]+)/g);
    if (bullets) {
        findingsList.innerHTML = '';
        recommendationsList.innerHTML = '';
        
        bullets.slice(0, 3).forEach(bullet => {
            const li = document.createElement('li');
            li.textContent = bullet.replace(/[•●]\s*/, '');
            findingsList.appendChild(li);
        });
        
        if (bullets.length > 3) {
            bullets.slice(3, 6).forEach(bullet => {
                const li = document.createElement('li');
                li.textContent = bullet.replace(/[•●]\s*/, '');
                recommendationsList.appendChild(li);
            });
        }
    }
    
    // Extract follow-up
    const followUpMatch = responseText.match(/Follow-up:\*?\*?\s*([^\n]*)/i);
    document.getElementById('followUp').textContent = 
        followUpMatch ? followUpMatch[1] : 'Regular monitoring recommended.';
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Download report
function downloadReport() {
    const results = {
        timestamp: new Date().toISOString(),
        riskLevel: document.getElementById('riskLevel').textContent,
        fdaStage: document.getElementById('fdaStage').textContent,
        confidence: document.getElementById('confidence').textContent,
        executiveSummary: document.getElementById('executiveSummary').textContent,
        keyFindings: Array.from(document.querySelectorAll('.findings-list li')).map(li => li.textContent),
        recommendations: Array.from(document.querySelectorAll('.recommendations-list li')).map(li => li.textContent),
        followUp: document.getElementById('followUp').textContent
    };
    
    const dataStr = JSON.stringify(results, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `PRISM-AD_Report_${new Date().toISOString().slice(0, 10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('clinicalInput');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
});
