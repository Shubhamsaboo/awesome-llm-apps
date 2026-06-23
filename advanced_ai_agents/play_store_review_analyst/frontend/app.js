// DOM Elements
const form = document.getElementById('analysisForm');
const appIdentifierInput = document.getElementById('appIdentifier');
const targetDateInput = document.getElementById('targetDate');
const statusDiv = document.getElementById('statusDiv');
const errorDiv = document.getElementById('errorDiv');
const resultsDiv = document.getElementById('resultsDiv');
const statusText = document.getElementById('statusText');
const errorText = document.getElementById('errorText');
const btnText = document.getElementById('btnText');
const spinner = document.getElementById('spinner');

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitAnalysis();
});

// async function submitAnalysis() {
//     try {
//         // Get form values
//         let appIdentifier = appIdentifierInput.value.trim();
//         const targetDate = targetDateInput.value;

//         // Validate input
//         if (!appIdentifier) {
//             showError('Please enter an app link or package ID');
//             return;
//         }

//         // Extract package ID from Play Store URL if provided
//         if (appIdentifier.includes('play.google.com')) {
//             const match = appIdentifier.match(/id=([a-zA-Z0-9._-]+)/);
//             if (match) {
//                 appIdentifier = match[1];
//             }
//         }

//         // Show loading state
//         setLoading(true);
//         hideAllResults();
//         showStatus('Initializing analysis...');

//         // Prepare request data
//         const requestData = {
//             app_identifier: appIdentifier,
//         };

//         // Only include target_date if it's provided
//         if (targetDate) {
//             requestData.target_date = targetDate;
//         }

//         // Call backend API
//         let response;
//         try {
//             response = await fetch('/analyze', {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/json',
//                 },
//                 body: JSON.stringify(requestData),
//             });
//         } catch (networkError) {
//             console.error('Network error:', networkError);
//             throw new Error(`Network error: ${networkError.message}. Is the backend server running?`);
//         }

//         let data;
//         try {
//             data = await response.json();
//         } catch (parseError) {
//             console.error('JSON parse error:', parseError);
//             throw new Error(`Server response error: ${response.status} ${response.statusText}`);
//         }

//         if (!response.ok) {
//             // Handle different error response formats
//             const errorMessage = data.detail || data.message || 'Analysis failed';
//             throw new Error(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
//         }

//         // Show results
//         showResults(data);
//         setLoading(false);

//     } catch (error) {
//         console.error('Error:', error);
//         // Properly extract error message
//         let errorMessage = 'An unexpected error occurred';
//         if (error instanceof Error) {
//             errorMessage = error.message;
//         } else if (typeof error === 'string') {
//             errorMessage = error;
//         } else if (error && typeof error === 'object') {
//             errorMessage = error.message || error.detail || JSON.stringify(error);
//         }
//         showError(errorMessage);
//         setLoading(false);
//     }
// }

async function submitAnalysis() {
    try {
        let appIdentifier = appIdentifierInput.value.trim();
        const targetDate = targetDateInput.value;

        if (!appIdentifier) {
            showError('Please enter an app link or package ID');
            return;
        }

        // Extract package ID from URL if provided
        if (appIdentifier.includes('play.google.com')) {
            const match = appIdentifier.match(/id=([a-zA-Z0-9._-]+)/);
            if (match) {
                appIdentifier = match[1];
            }
        }

        // First, check for existing data
        setLoading(true);
        hideAllResults();
        showStatus('Checking for existing data...');

        const checkResponse = await fetch('/check-existing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ app_identifier: appIdentifier })
        });

        const checkData = await checkResponse.json();

        if (checkData.status === 'found') {
            setLoading(false);
            showExistingDataPrompt(checkData.data, appIdentifier, targetDate);
            return;
        }

        // No existing data, proceed with fresh analysis
        setLoading(false);
        await runAnalysis(appIdentifier, targetDate, false, false, false);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An unexpected error occurred');
        setLoading(false);
    }
}

function showExistingDataPrompt(existingData, appIdentifier, targetDate) {

    // Validate input
    if (!existingData) {
        console.error('showExistingDataPrompt called with undefined existingData!');
        showError('Invalid data received from server');
        return;
    }

    console.log('showExistingDataPrompt called with:', existingData);


    const existingDiv = document.getElementById('existingDataDiv');
    const infoDiv = document.getElementById('existingDataInfo');

    // Safely get categorization status
    const catStatus = existingData.categorization_status || {
        total_categorized: 0,
        llm_provider: null,
        llm_model: null,
        completed: false
    };

    const totalReviews = existingData.total_reviews || 0;
    const categorized = catStatus.total_categorized || 0;
    const isComplete = catStatus.completed || categorized === totalReviews;
    const progressPercent = totalReviews > 0 ? ((categorized / totalReviews) * 100).toFixed(1) : 0;
    const progress = totalReviews > 0
        ? `${categorized} / ${totalReviews} categorized (${progressPercent}%)`
        : 'Not started';

    // Build status message based on completion
    let statusMessage = '';
    if (isComplete) {
        statusMessage = `
            <div class="success-box">
                <p>✅ <strong>Categorization Complete!</strong> All ${totalReviews} reviews have been processed.</p>
            </div>
        `;
    } else if (categorized > 0) {
        statusMessage = `
            <div class="warning-box">
                <p>⚠️ <strong>Incomplete Categorization:</strong> Only ${categorized} of ${totalReviews} reviews (${progressPercent}%) have been categorized.</p>
            </div>
        `;
    } else {
        statusMessage = `
            <div class="info-box">
                <p>ℹ️ <strong>Not Started:</strong> Reviews have been scraped but not yet categorized.</p>
            </div>
        `;
    }

    infoDiv.innerHTML = `
        ${statusMessage}
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">📊 Total Reviews:</span>
                <span class="info-value">${totalReviews.toLocaleString()}</span>
            </div>
            <div class="info-item">
                <span class="info-label">✅ Categorization Progress:</span>
                <span class="info-value">${progress}</span>
            </div>
            ${catStatus.llm_provider ? `
            <div class="info-item">
                <span class="info-label">🤖 Previous LLM:</span>
                <span class="info-value">${catStatus.llm_provider} (${catStatus.llm_model})</span>
            </div>
            ` : ''}
        </div>
        <p class="help-text">
            💡 <strong>Tip:</strong> ${isComplete
                ? 'You can use the existing analysis or re-categorize if you want fresh results.'
                : 'Resume categorization to save API costs and continue from where you left off!'}
        </p>
    `;

    // Dynamically populate buttons based on completion status
    const buttonsDiv = document.getElementById('existingDataButtons');
    if (isComplete) {
        // All reviews categorized - offer to use or re-categorize
        buttonsDiv.innerHTML = `
            <button class="btn btn-primary" onclick="useExistingData()">
                ✅ Use Existing Analysis
            </button>
            <button class="btn btn-secondary" onclick="startFreshAnalysis()">
                🔄 Re-categorize All
            </button>
            <button class="btn btn-secondary" onclick="hideExistingData()">
                ❌ Cancel
            </button>
        `;
    } else if (categorized > 0) {
        // Incomplete - offer to resume or start fresh
        buttonsDiv.innerHTML = `
            <button class="btn btn-primary" onclick="resumeCategorization()">
                ▶️ Resume Categorization (${totalReviews - categorized} remaining)
            </button>
            <button class="btn btn-secondary" onclick="useExistingData()">
                ✅ Use Partial Data (${progressPercent}%)
            </button>
            <button class="btn btn-secondary" onclick="startFreshAnalysis()">
                🔄 Start Fresh
            </button>
            <button class="btn btn-secondary" onclick="hideExistingData()">
                ❌ Cancel
            </button>
        `;
    } else {
        // Not started - offer to start or re-scrape
        buttonsDiv.innerHTML = `
            <button class="btn btn-primary" onclick="resumeCategorization()">
                ▶️ Start Categorization
            </button>
            <button class="btn btn-secondary" onclick="startFreshAnalysis()">
                🔄 Re-scrape Reviews
            </button>
            <button class="btn btn-secondary" onclick="hideExistingData()">
                ❌ Cancel
            </button>
        `;
    }

    // Store for later use
    window.pendingAnalysis = { appIdentifier, targetDate, existingData, isComplete, categorized };

    hideAllResults();
    existingDiv.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function resumeCategorization() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    // Use existing reviews and resume extraction from where we left off
    await runAnalysis(appIdentifier, targetDate, true, true);
}

async function useExistingData() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    // Use existing reviews and existing categorization
    await runAnalysis(appIdentifier, targetDate, true, true);
}

async function startFreshAnalysis() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    // Clear all progress and start fresh
    await runAnalysis(appIdentifier, targetDate, false, false, true);
}

function hideExistingData() {
    document.getElementById('existingDataDiv').style.display = 'none';
    document.getElementById('llmChangeDiv').style.display = 'none';
}

// async function runAnalysis(appIdentifier, targetDate, useExisting, resumeExtraction, clearProgress = false) {
//     try {
//         setLoading(true);
//         hideAllResults();
//         showStatus('Initializing analysis...');

//         const requestData = {
//             app_identifier: appIdentifier,
//             use_existing: useExisting,
//             resume_extraction: resumeExtraction,
//             clear_progress: clearProgress
//         };

//         if (targetDate) {
//             requestData.target_date = targetDate;
//         }

//         const response = await fetch('/analyze', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(requestData)
//         });

//         const data = await response.json();

//         // Handle LLM change
//         if (data.status === 'llm_changed') {
//             setLoading(false);
//             showLLMChangePrompt(data, appIdentifier, targetDate);
//             return;
//         }

//         if (!response.ok) {
//             throw new Error(data.detail || data.message || 'Analysis failed');
//         }

//         showResults(data);
//         setLoading(false);

//     } catch (error) {
//         console.error('Error:', error);
//         showError(error.message || 'An unexpected error occurred');
//         setLoading(false);
//     }
// }

async function runAnalysis(appIdentifier, targetDate, useExisting, resumeExtraction, clearProgress = false) {
    try {
        setLoading(true);
        hideAllResults();
        showStatus('Initializing analysis...');

        const requestData = {
            app_identifier: appIdentifier,
            use_existing: useExisting,
            resume_extraction: resumeExtraction,
            clear_progress: clearProgress
        };

        if (targetDate) {
            requestData.target_date = targetDate;
        }

        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        // Handle existing data found
        if (data.status === 'existing_data_found') {
            console.log('=== EXISTING DATA FOUND ===');
            console.log('Full response:', data);
            console.log('existing_data:', data.existing_data);
            
            setLoading(false);
            
            // Safety check
            if (!data.existing_data) {
                console.error('ERROR: existing_data is undefined!');
                showError('Invalid response from server - existing data is missing');
                return;
            }
            
            showExistingDataPrompt(data.existing_data, appIdentifier, targetDate);
            return;
        }

        // Handle LLM change
        if (data.status === 'llm_changed') {
            setLoading(false);
            showLLMChangePrompt(data, appIdentifier, targetDate);
            return;
        }

        // Handle errors
        if (data.status === 'error' || !response.ok) {
            throw new Error(data.detail || data.message || 'Analysis failed');
        }

        // Success - show results
        console.log('[FRONTEND] ✅ Received success response from backend');
        console.log('[FRONTEND] Response keys:', Object.keys(data));
        console.log('[FRONTEND] trend_analysis:', data.trend_analysis);
        console.log('[FRONTEND] Recommendations:', data.trend_analysis?.actionable_recommendations);

        showResults(data);
        setLoading(false);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An unexpected error occurred');
        setLoading(false);
    }
}

function showLLMChangePrompt(data, appIdentifier, targetDate) {
    const llmDiv = document.getElementById('llmChangeDiv');
    const infoDiv = document.getElementById('llmChangeInfo');
    
    const prev = data.previous_llm;
    const curr = data.current_llm;
    const existing = data.existing_data;
    
    infoDiv.innerHTML = `
        <div class="warning-box">
            <p>⚠️ The LLM provider/model has changed since the last categorization.</p>
        </div>
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Previous LLM:</span>
                <span class="info-value">${prev.provider} (${prev.model})</span>
            </div>
            <div class="info-item">
                <span class="info-label">Current LLM:</span>
                <span class="info-value">${curr.provider} (${curr.model})</span>
            </div>
            <div class="info-item">
                <span class="info-label">Previously Categorized:</span>
                <span class="info-value">${existing.categorization_status.total_categorized} / ${existing.total_reviews} reviews</span>
            </div>
        </div>
        <p class="help-text">
            ℹ️ Different LLMs may categorize topics differently. You can either:
            <br>• Re-categorize everything with the new LLM (recommended for consistency)
            <br>• Use the previous categorization (faster, but mixed LLM results)
        </p>
    `;
    
    window.pendingAnalysis = { appIdentifier, targetDate, data };
    
    llmDiv.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function recategorizWithNewLLM() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    // Use existing reviews but restart categorization
    await runAnalysis(appIdentifier, targetDate, true, false, false);
}

async function useOldCategorization() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    // Use existing everything
    await runAnalysis(appIdentifier, targetDate, true, true, false);
}

function setLoading(isLoading) {
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = isLoading;
    if (isLoading) {
        btnText.style.display = 'none';
        spinner.style.display = 'inline';
    } else {
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

function showStatus(message) {
    statusDiv.style.display = 'block';
    statusText.textContent = message;
}

function showError(message) {
    errorDiv.style.display = 'block';
    errorText.textContent = message;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
let currentAnalysisData = null; // Store for CSV export
function showResults(data) {
    if (data.status !== 'success') {
        showError(data.message || 'Analysis failed');
        return;
    }

    console.log('Received data:', data); // Debug log

    // Store data globally for CSV export
    currentAnalysisData = data;

    // Populate basic info
    document.getElementById('resultApp').textContent = data.app_name || 'Unknown';
    document.getElementById('resultDate').textContent = new Date().toLocaleDateString();
    document.getElementById('resultReviews').textContent = (data.total_reviews || 0).toLocaleString();
    document.getElementById('resultTopics').textContent = data.topics_extracted || 0;

    // Get trend analysis data - THE KEY FIX IS HERE
    const trendAnalysis = data.trend_analysis || {};
    console.log('Trend analysis:', trendAnalysis); // Debug log
    
    const recommendations = trendAnalysis.actionable_recommendations || [];
    const severityScores = trendAnalysis.severity_scores || {};
    const insights = trendAnalysis.insights || {};
    const freqTable = trendAnalysis.frequency_table || {};

    console.log('Recommendations:', recommendations); // Debug log
    console.log('Severity scores:', severityScores); // Debug log

    // Count critical issues
    const criticalCount = recommendations.filter(r => r.classification === 'CRITICAL').length;
    document.getElementById('resultCritical').textContent = criticalCount;
    document.getElementById('resultTrendingUp').textContent = insights.trending_up?.length || 0;

    // Populate recommendations
    populateRecommendations(recommendations);

    // Populate top topics
    populateTopTopics(severityScores);

    // Draw trend chart
    drawTrendChart(freqTable, insights.top_topics || []);

    // Setup report links
    const markdownFile = data.report_markdown.replace(/\\/g, '/').split('/').pop();
    const htmlFile = data.report_html.replace(/\\/g, '/').split('/').pop();

    document.getElementById('reportMarkdownLink').href = `/report/${markdownFile}`;
    document.getElementById('reportMarkdownLink').download = markdownFile;
    document.getElementById('reportHtmlLink').href = `/report/${htmlFile}`;

    // Show results
    resultsDiv.style.display = 'block';
    statusDiv.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function populateRecommendations(recommendations) {
    const container = document.getElementById('recommendationsList');
    
    if (!container) {
        console.error('recommendationsList container not found!');
        return;
    }
    
    container.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="no-data">No recommendations available</p>';
        return;
    }

    console.log('Populating', recommendations.length, 'recommendations'); // Debug log

    recommendations.forEach(rec => {
        const classificationLower = rec.classification.toLowerCase();
        const trendIcon = rec.trend_percentage > 10 ? '📈' : (rec.trend_percentage < -10 ? '📉' : '➡️');
        
        const recCard = document.createElement('div');
        recCard.className = `recommendation-card ${classificationLower}`;
        recCard.innerHTML = `
            <div class="rec-header">
                <div class="rec-priority">
                    <span class="priority-badge ${classificationLower}">
                        Priority ${rec.priority}
                    </span>
                    <span class="severity-badge ${classificationLower}">
                        ${rec.classification}
                    </span>
                </div>
            </div>
            <div class="rec-topic">${rec.topic}</div>
            <div class="rec-action">${rec.action}</div>
            <div class="rec-details">
                <div class="rec-metric">
                    <span class="metric-icon">👥</span>
                    <span>${rec.affected_users} affected users</span>
                </div>
                <div class="rec-metric">
                    <span class="metric-icon">⭐</span>
                    <span>Avg ${rec.avg_rating}★</span>
                </div>
                <div class="rec-metric">
                    <span class="metric-icon">${trendIcon}</span>
                    <span>${Math.abs(rec.trend_percentage).toFixed(1)}% ${rec.trend_percentage > 0 ? 'increase' : 'decrease'}</span>
                </div>
            </div>
        `;
        container.appendChild(recCard);
    });
}

function populateTopTopics(severityScores) {
    const container = document.getElementById('topTopicsList');
    
    if (!container) {
        console.error('topTopicsList container not found!');
        return;
    }
    
    container.innerHTML = '';

    if (!severityScores || Object.keys(severityScores).length === 0) {
        container.innerHTML = '<p class="no-data">No topics available</p>';
        return;
    }

    console.log('Populating topics, count:', Object.keys(severityScores).length); // Debug log

    // Sort by severity score
    const sorted = Object.entries(severityScores)
        .sort(([, a], [, b]) => b.score - a.score)
        .slice(0, 10);

    sorted.forEach(([topic, data], index) => {
        const classificationLower = data.classification.toLowerCase();
        const scorePercent = data.score;
        
        const topicCard = document.createElement('div');
        topicCard.className = 'topic-card';
        topicCard.innerHTML = `
            <div class="topic-rank">#${index + 1}</div>
            <div class="topic-content">
                <div class="topic-header">
                    <div class="topic-name">${topic}</div>
                    <span class="severity-badge ${classificationLower}">
                        ${data.classification}
                    </span>
                </div>
                <div class="topic-metrics">
                    <div class="metric">
                        <span class="metric-label">Severity:</span>
                        <span class="metric-value">${data.score}/100</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Reviews:</span>
                        <span class="metric-value">${data.total_reviews}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg Rating:</span>
                        <span class="metric-value">${data.avg_rating}★</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Low Ratings:</span>
                        <span class="metric-value">${data.low_rating_percentage}%</span>
                    </div>
                </div>
                <div class="severity-bar">
                    <div class="severity-fill ${classificationLower}" style="width: ${scorePercent}%"></div>
                </div>
            </div>
        `;
        container.appendChild(topicCard);
    });
}

function drawTrendChart(freqTable, topTopics) {
    const canvas = document.getElementById('trendChart');
    
    if (!canvas) {
        console.error('trendChart canvas not found!');
        return;
    }
    
    const ctx = canvas.getContext('2d');

    // Clear any existing chart
    if (window.trendChartInstance) {
        window.trendChartInstance.destroy();
    }

    // Check if we have data
    if (!freqTable || Object.keys(freqTable).length === 0) {
        console.warn('No frequency table data for chart');
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No trend data available', canvas.width / 2, canvas.height / 2);
        return;
    }

    console.log('Drawing chart with', Object.keys(freqTable).length, 'topics'); // Debug log

    // Get dates
    const allDates = new Set();
    Object.values(freqTable).forEach(dateFreq => {
        Object.keys(dateFreq).forEach(date => allDates.add(date));
    });
    const dates = Array.from(allDates).sort();

    if (dates.length === 0) {
        console.warn('No dates found in frequency table');
        return;
    }

    // Prepare datasets for top 5 topics
    const colors = [
        'rgb(255, 99, 132)',
        'rgb(54, 162, 235)',
        'rgb(255, 206, 86)',
        'rgb(75, 192, 192)',
        'rgb(153, 102, 255)'
    ];

    // Get top topics (use all if less than 5)
    const topicsToShow = topTopics && topTopics.length > 0 
        ? topTopics.slice(0, 5) 
        : Object.keys(freqTable).slice(0, 5);

    console.log('Showing topics:', topicsToShow); // Debug log

    const datasets = topicsToShow.map((topic, idx) => {
        const data = dates.map(date => freqTable[topic]?.[date] || 0);
        return {
            label: topic,
            data: data,
            borderColor: colors[idx % colors.length],
            backgroundColor: colors[idx % colors.length].replace('rgb', 'rgba').replace(')', ', 0.1)'),
            tension: 0.4,
            fill: true
        };
    });

    window.trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Review Frequency Over Time (Top 5 Topics)',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Reviews'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

function downloadTableCSV() {
    if (!currentAnalysisData) {
        showError('No data available for export');
        return;
    }

    const trendAnalysis = currentAnalysisData.trend_analysis || {};
    const severityScores = trendAnalysis.severity_scores || {};

    if (!severityScores || Object.keys(severityScores).length === 0) {
        showError('No severity data available for export');
        return;
    }

    // Build CSV
    let csv = 'Topic,Severity Score,Classification,Total Reviews,Avg Rating,Low Rating %\n';

    Object.entries(severityScores)
        .sort(([, a], [, b]) => b.score - a.score)
        .forEach(([topic, data]) => {
            csv += `"${topic}",${data.score},${data.classification},${data.total_reviews},${data.avg_rating},${data.low_rating_percentage}\n`;
        });

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentAnalysisData.app_name}_analysis.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// function populateRecommendations(recommendations) {
//     const container = document.getElementById('recommendationsList');
//     container.innerHTML = '';

//     if (!recommendations || recommendations.length === 0) {
//         container.innerHTML = '<p class="no-data">No recommendations available</p>';
//         return;
//     }

//     recommendations.forEach(rec => {
//         const classificationLower = rec.classification.toLowerCase();
//         const trendIcon = rec.trend_percentage > 10 ? '📈' : (rec.trend_percentage < -10 ? '📉' : '➡️');
        
//         const recCard = document.createElement('div');
//         recCard.className = `recommendation-card ${classificationLower}`;
//         recCard.innerHTML = `
//             <div class="rec-header">
//                 <div class="rec-priority">
//                     <span class="priority-badge ${classificationLower}">
//                         Priority ${rec.priority}
//                     </span>
//                     <span class="severity-badge ${classificationLower}">
//                         ${rec.classification}
//                     </span>
//                 </div>
//             </div>
//             <div class="rec-topic">${rec.topic}</div>
//             <div class="rec-action">${rec.action}</div>
//             <div class="rec-details">
//                 <div class="rec-metric">
//                     <span class="metric-icon">👥</span>
//                     <span>${rec.affected_users} affected users</span>
//                 </div>
//                 <div class="rec-metric">
//                     <span class="metric-icon">⭐</span>
//                     <span>Avg ${rec.avg_rating}★</span>
//                 </div>
//                 <div class="rec-metric">
//                     <span class="metric-icon">${trendIcon}</span>
//                     <span>${Math.abs(rec.trend_percentage)}% ${rec.trend_percentage > 0 ? 'increase' : 'decrease'}</span>
//                 </div>
//             </div>
//         `;
//         container.appendChild(recCard);
//     });
// }

// function populateTopTopics(severityScores) {
//     const container = document.getElementById('topTopicsList');
//     container.innerHTML = '';

//     if (!severityScores || Object.keys(severityScores).length === 0) {
//         container.innerHTML = '<p class="no-data">No topics available</p>';
//         return;
//     }

//     // Sort by severity score
//     const sorted = Object.entries(severityScores)
//         .sort(([, a], [, b]) => b.score - a.score)
//         .slice(0, 10);

//     sorted.forEach(([topic, data], index) => {
//         const classificationLower = data.classification.toLowerCase();
//         const scorePercent = data.score;
        
//         const topicCard = document.createElement('div');
//         topicCard.className = 'topic-card';
//         topicCard.innerHTML = `
//             <div class="topic-rank">#${index + 1}</div>
//             <div class="topic-content">
//                 <div class="topic-header">
//                     <div class="topic-name">${topic}</div>
//                     <span class="severity-badge ${classificationLower}">
//                         ${data.classification}
//                     </span>
//                 </div>
//                 <div class="topic-metrics">
//                     <div class="metric">
//                         <span class="metric-label">Severity:</span>
//                         <span class="metric-value">${data.score}/100</span>
//                     </div>
//                     <div class="metric">
//                         <span class="metric-label">Reviews:</span>
//                         <span class="metric-value">${data.total_reviews}</span>
//                     </div>
//                     <div class="metric">
//                         <span class="metric-label">Avg Rating:</span>
//                         <span class="metric-value">${data.avg_rating}★</span>
//                     </div>
//                     <div class="metric">
//                         <span class="metric-label">Low Ratings:</span>
//                         <span class="metric-value">${data.low_rating_percentage}%</span>
//                     </div>
//                 </div>
//                 <div class="severity-bar">
//                     <div class="severity-fill ${classificationLower}" style="width: ${scorePercent}%"></div>
//                 </div>
//             </div>
//         `;
//         container.appendChild(topicCard);
//     });
// }

function drawTrendChart(freqTable, topTopics) {
    const canvas = document.getElementById('trendChart');
    const ctx = canvas.getContext('2d');

    // Clear any existing chart
    if (window.trendChartInstance) {
        window.trendChartInstance.destroy();
    }

    // Get dates
    const allDates = new Set();
    Object.values(freqTable).forEach(dateFreq => {
        Object.keys(dateFreq).forEach(date => allDates.add(date));
    });
    const dates = Array.from(allDates).sort();

    // Prepare datasets for top 5 topics
    const colors = [
        'rgb(255, 99, 132)',
        'rgb(54, 162, 235)',
        'rgb(255, 206, 86)',
        'rgb(75, 192, 192)',
        'rgb(153, 102, 255)'
    ];

    const datasets = topTopics.slice(0, 5).map((topic, idx) => {
        const data = dates.map(date => freqTable[topic]?.[date] || 0);
        return {
            label: topic,
            data: data,
            borderColor: colors[idx % colors.length],
            backgroundColor: colors[idx % colors.length].replace('rgb', 'rgba').replace(')', ', 0.1)'),
            tension: 0.4,
            fill: true
        };
    });

    window.trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Review Frequency Over Time (Top 5 Topics)',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Reviews'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

// function downloadTableCSV() {
//     if (!currentAnalysisData) {
//         showError('No data available for export');
//         return;
//     }

//     const trendAnalysis = currentAnalysisData.trend_analysis || {};
//     const severityScores = trendAnalysis.severity_scores || {};
//     const freqTable = trendAnalysis.frequency_table || {};

//     // Build CSV
//     let csv = 'Topic,Severity Score,Classification,Total Reviews,Avg Rating,Low Rating %\n';

//     Object.entries(severityScores)
//         .sort(([, a], [, b]) => b.score - a.score)
//         .forEach(([topic, data]) => {
//             csv += `"${topic}",${data.score},${data.classification},${data.total_reviews},${data.avg_rating},${data.low_rating_percentage}\n`;
//         });

//     // Download
//     const blob = new Blob([csv], { type: 'text/csv' });
//     const url = window.URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = `${currentAnalysisData.app_name}_analysis.csv`;
//     a.click();
//     window.URL.revokeObjectURL(url);
// }

function hideAllResults() {
    statusDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    resultsDiv.style.display = 'none';
    document.getElementById('existingDataDiv').style.display = 'none';
    document.getElementById('llmChangeDiv').style.display = 'none';
}

function resetForm() {
    form.reset();
    hideAllResults();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Set today's date as default max date
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    targetDateInput.max = today;
});
