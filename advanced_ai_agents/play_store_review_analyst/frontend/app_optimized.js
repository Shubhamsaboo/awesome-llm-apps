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

let currentAnalysisData = null;

// ==========================
// FORM HANDLING
// ==========================

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitAnalysis();
});

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

        // Check for existing data
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

        // No existing data, proceed
        setLoading(false);
        await runAnalysis(appIdentifier, targetDate, false, false, false);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An unexpected error occurred');
        setLoading(false);
    }
}

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
            setLoading(false);
            if (!data.existing_data) {
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
        showResults(data);
        setLoading(false);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An unexpected error occurred');
        setLoading(false);
    }
}

// ==========================
// RESULTS DISPLAY (OPTIMIZED)
// ==========================

function showResults(data) {
    if (data.status !== 'success') {
        showError(data.message || 'Analysis failed');
        return;
    }

    currentAnalysisData = data;

    // Update header
    document.getElementById('appName').textContent = formatAppName(data.app_name || 'Unknown');
    document.getElementById('analysisDate').textContent = new Date().toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    const trendAnalysis = data.trend_analysis || {};
    const recommendations = trendAnalysis.actionable_recommendations || [];
    const severityScores = trendAnalysis.severity_scores || {};
    const insights = trendAnalysis.insights || {};
    const freqTable = trendAnalysis.frequency_table || {};

    // === KPI CARDS ===
    document.getElementById('kpiReviews').textContent = (data.total_reviews || 0).toLocaleString();
    document.getElementById('kpiTopics').textContent = data.topics_extracted || 0;

    const criticalCount = recommendations.filter(r => r.classification === 'CRITICAL').length;
    document.getElementById('kpiCritical').textContent = criticalCount;

    // Calculate average rating from severity scores
    const avgRating = calculateOverallAvgRating(severityScores);
    document.getElementById('kpiAvgRating').textContent = avgRating ? avgRating.toFixed(1) + '★' : 'N/A';

    // === DATA QUALITY ALERT ===
    showDataQualityAlert(data);

    // === PRIORITY ISSUES ===
    populatePriorities(recommendations.slice(0, 5));

    // === KEY INSIGHTS ===
    populateInsights(insights, severityScores, data);

    // === TOPIC DISTRIBUTION CHART ===
    populateTopicChart(severityScores);

    // === TIMELINE CHART (only if sufficient data) ===
    showTimelineChart(freqTable);

    // === DETAILED TABLE ===
    populateDetailsTable(severityScores);

    // Collapse input card after successful analysis
    document.getElementById('analysisForm').style.display = 'none';
    document.getElementById('toggleIcon').classList.remove('open');

    // Show results
    resultsDiv.style.display = 'block';
    statusDiv.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showDataQualityAlert(data) {
    const alertCard = document.getElementById('dataQualityAlert');
    const message = document.getElementById('dataQualityMessage');

    const totalReviews = data.total_reviews || 0;
    const topicsExtracted = data.topics_extracted || 0;

    // Show alert if data seems limited
    if (totalReviews < 500 || topicsExtracted < 10) {
        let alertText = '';
        if (totalReviews < 500) {
            alertText = `Analysis based on only ${totalReviews} reviews. `;
        }
        if (topicsExtracted < 10) {
            alertText += `Only ${topicsExtracted} topics identified. `;
        }
        alertText += 'Insights may be limited. Consider analyzing more reviews for better accuracy.';

        message.textContent = alertText;
        alertCard.style.display = 'flex';
    } else {
        alertCard.style.display = 'none';
    }
}

function populatePriorities(recommendations) {
    const container = document.getElementById('prioritiesList');
    container.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="no-data">No priority issues identified</p>';
        return;
    }

    recommendations.forEach((rec, index) => {
        const classificationLower = rec.classification.toLowerCase();

        const item = document.createElement('div');
        item.className = `priority-item ${classificationLower}`;
        item.innerHTML = `
            <div class="priority-rank">${index + 1}</div>
            <div class="priority-content">
                <div class="priority-topic">${rec.topic}</div>
                <div class="priority-meta">
                    <span class="priority-badge ${classificationLower}">${rec.classification}</span>
                    <span>👥 ${rec.affected_users} reviews</span>
                    <span>⭐ ${rec.avg_rating}★ avg</span>
                </div>
            </div>
        `;
        container.appendChild(item);
    });
}

function populateInsights(insights, severityScores, data) {
    const container = document.getElementById('insightsList');
    container.innerHTML = '';

    const insightsList = [];

    // Insight 1: Overall sentiment
    const avgRating = calculateOverallAvgRating(severityScores);
    if (avgRating !== null) {
        const sentiment = avgRating >= 4 ? '😊 Positive' : avgRating >= 3 ? '😐 Neutral' : '😟 Negative';
        insightsList.push({
            icon: avgRating >= 4 ? '✨' : avgRating >= 3 ? '⚖️' : '⚠️',
            text: `Overall sentiment is <strong>${sentiment}</strong> with ${avgRating.toFixed(1)}★ average rating`
        });
    }

    // Insight 2: Critical issues
    const criticalTopics = Object.entries(severityScores)
        .filter(([_, data]) => data.classification === 'CRITICAL')
        .length;

    if (criticalTopics > 0) {
        insightsList.push({
            icon: '🔴',
            text: `<strong>${criticalTopics} critical issues</strong> require immediate attention`
        });
    } else {
        insightsList.push({
            icon: '✅',
            text: 'No critical issues detected - app is performing well'
        });
    }

    // Insight 3: Top issue
    const topIssues = insights.top_topics || [];
    if (topIssues.length > 0) {
        const topIssue = topIssues[0];
        const issueData = severityScores[topIssue];
        if (issueData) {
            insightsList.push({
                icon: '🎯',
                text: `Most mentioned topic: <strong>${topIssue}</strong> (${issueData.total_reviews} reviews)`
            });
        }
    }

    // Insight 4: Trend information
    const trendingUp = insights.trending_up || [];
    const trendingDown = insights.trending_down || [];

    if (trendingUp.length > 0) {
        insightsList.push({
            icon: '📈',
            text: `<strong>${trendingUp.length} topics</strong> are trending upward`
        });
    } else if (trendingDown.length > 0) {
        insightsList.push({
            icon: '📉',
            text: `<strong>${trendingDown.length} topics</strong> are trending downward`
        });
    } else {
        insightsList.push({
            icon: 'ℹ️',
            text: 'Insufficient historical data for trend analysis'
        });
    }

    // Insight 5: Low-rated reviews
    const lowRatedTopics = Object.entries(severityScores)
        .filter(([_, data]) => data.avg_rating < 2.5)
        .length;

    if (lowRatedTopics > 0) {
        insightsList.push({
            icon: '⚡',
            text: `<strong>${lowRatedTopics} topics</strong> have very low ratings (<2.5★)`
        });
    }

    // Render insights
    insightsList.forEach(insight => {
        const item = document.createElement('div');
        item.className = 'insight-item';
        item.innerHTML = `
            <div class="insight-icon">${insight.icon}</div>
            <div class="insight-text">${insight.text}</div>
        `;
        container.appendChild(item);
    });
}

function populateTopicChart(severityScores) {
    const container = document.getElementById('topicChart');
    container.innerHTML = '';

    if (!severityScores || Object.keys(severityScores).length === 0) {
        container.innerHTML = '<p class="no-data">No topic data available</p>';
        return;
    }

    // Sort by total reviews
    const sorted = Object.entries(severityScores)
        .sort(([, a], [, b]) => b.total_reviews - a.total_reviews)
        .slice(0, 10);

    const maxReviews = sorted[0]?.[1].total_reviews || 1;

    sorted.forEach(([topic, data]) => {
        const percentage = (data.total_reviews / maxReviews) * 100;
        const classificationLower = data.classification.toLowerCase();

        const bar = document.createElement('div');
        bar.className = 'chart-bar';
        bar.innerHTML = `
            <div class="chart-label" title="${topic}">${truncate(topic, 20)}</div>
            <div class="chart-bar-container">
                <div class="chart-bar-fill ${classificationLower}" style="width: ${percentage}%">
                    <span class="chart-bar-value">${data.total_reviews}</span>
                </div>
            </div>
            <div class="chart-meta">
                <span>${data.avg_rating}★</span>
                <span>${data.classification}</span>
            </div>
        `;
        container.appendChild(bar);
    });
}

function showTimelineChart(freqTable) {
    const timelineCard = document.getElementById('timelineCard');
    const canvas = document.getElementById('trendChart');

    if (!freqTable || Object.keys(freqTable).length === 0) {
        timelineCard.style.display = 'none';
        return;
    }

    // Get all dates
    const allDates = new Set();
    Object.values(freqTable).forEach(dateFreq => {
        Object.keys(dateFreq).forEach(date => allDates.add(date));
    });
    const dates = Array.from(allDates).sort();

    // Only show if we have at least 3 days of data
    if (dates.length < 3) {
        timelineCard.style.display = 'none';
        return;
    }

    timelineCard.style.display = 'block';

    const ctx = canvas.getContext('2d');

    // Clear existing chart
    if (window.trendChartInstance) {
        window.trendChartInstance.destroy();
    }

    // Get top 5 topics
    const topTopics = Object.entries(freqTable)
        .map(([topic, dates]) => ({
            topic,
            total: Object.values(dates).reduce((sum, count) => sum + count, 0)
        }))
        .sort((a, b) => b.total - a.total)
        .slice(0, 5)
        .map(item => item.topic);

    const colors = [
        'rgb(79, 70, 229)',   // primary
        'rgb(239, 68, 68)',   // danger
        'rgb(245, 158, 11)',  // warning
        'rgb(16, 185, 129)',  // success
        'rgb(107, 114, 128)'  // gray
    ];

    const datasets = topTopics.map((topic, idx) => {
        const data = dates.map(date => freqTable[topic]?.[date] || 0);
        return {
            label: topic,
            data: data,
            borderColor: colors[idx],
            backgroundColor: colors[idx].replace('rgb', 'rgba').replace(')', ', 0.1)'),
            tension: 0.3,
            fill: false,
            borderWidth: 2
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
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: { size: 11 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                },
                y: {
                    ticks: { font: { size: 10 }, precision: 0 },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                }
            }
        }
    });
}

function populateDetailsTable(severityScores) {
    const container = document.getElementById('detailsTable');

    if (!severityScores || Object.keys(severityScores).length === 0) {
        container.innerHTML = '<p class="no-data">No detailed data available</p>';
        return;
    }

    const sorted = Object.entries(severityScores)
        .sort(([, a], [, b]) => b.score - a.score);

    let tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Topic</th>
                    <th>Classification</th>
                    <th>Severity</th>
                    <th>Reviews</th>
                    <th>Avg Rating</th>
                    <th>Low Rating %</th>
                </tr>
            </thead>
            <tbody>
    `;

    sorted.forEach(([topic, data], index) => {
        tableHTML += `
            <tr>
                <td>${index + 1}</td>
                <td>${topic}</td>
                <td><span class="priority-badge ${data.classification.toLowerCase()}">${data.classification}</span></td>
                <td>${data.score}/100</td>
                <td>${data.total_reviews}</td>
                <td>${data.avg_rating}★</td>
                <td>${data.low_rating_percentage}%</td>
            </tr>
        `;
    });

    tableHTML += '</tbody></table>';
    container.innerHTML = tableHTML;
}

// ==========================
// EXISTING DATA PROMPT
// ==========================

function showExistingDataPrompt(existingData, appIdentifier, targetDate) {
    if (!existingData) {
        showError('Invalid data received from server');
        return;
    }

    const existingDiv = document.getElementById('existingDataDiv');
    const infoDiv = document.getElementById('existingDataInfo');

    const catStatus = existingData.categorization_status || {};
    const totalReviews = existingData.total_reviews || 0;
    const categorized = catStatus.total_categorized || 0;
    const isComplete = catStatus.completed || categorized === totalReviews;
    const progressPercent = totalReviews > 0 ? ((categorized / totalReviews) * 100).toFixed(1) : 0;

    let statusMessage = '';
    if (isComplete) {
        statusMessage = `
            <div style="background: #d1fae5; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                <p>✅ <strong>Categorization Complete!</strong> All ${totalReviews} reviews processed.</p>
            </div>
        `;
    } else if (categorized > 0) {
        statusMessage = `
            <div style="background: #fff7ed; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                <p>⚠️ <strong>Incomplete:</strong> ${categorized} of ${totalReviews} reviews (${progressPercent}%) categorized.</p>
            </div>
        `;
    }

    infoDiv.innerHTML = `
        ${statusMessage}
        <div style="display: grid; gap: 8px;">
            <div style="padding: 8px; background: var(--gray-50); border-radius: 4px;">
                <strong>Total Reviews:</strong> ${totalReviews.toLocaleString()}
            </div>
            <div style="padding: 8px; background: var(--gray-50); border-radius: 4px;">
                <strong>Categorized:</strong> ${categorized.toLocaleString()} (${progressPercent}%)
            </div>
            ${catStatus.llm_provider ? `
            <div style="padding: 8px; background: var(--gray-50); border-radius: 4px;">
                <strong>LLM:</strong> ${catStatus.llm_provider} (${catStatus.llm_model})
            </div>
            ` : ''}
        </div>
    `;

    const buttonsDiv = document.getElementById('existingDataButtons');
    if (isComplete) {
        buttonsDiv.innerHTML = `
            <button class="btn-primary" onclick="useExistingData()">✅ Use Existing Analysis</button>
            <button class="btn-secondary" onclick="startFreshAnalysis()">🔄 Re-categorize All</button>
            <button class="btn-secondary" onclick="hideExistingData()">❌ Cancel</button>
        `;
    } else if (categorized > 0) {
        buttonsDiv.innerHTML = `
            <button class="btn-primary" onclick="resumeCategorization()">▶️ Resume (${totalReviews - categorized} remaining)</button>
            <button class="btn-secondary" onclick="useExistingData()">✅ Use Partial (${progressPercent}%)</button>
            <button class="btn-secondary" onclick="startFreshAnalysis()">🔄 Start Fresh</button>
            <button class="btn-secondary" onclick="hideExistingData()">❌ Cancel</button>
        `;
    } else {
        buttonsDiv.innerHTML = `
            <button class="btn-primary" onclick="resumeCategorization()">▶️ Start Categorization</button>
            <button class="btn-secondary" onclick="startFreshAnalysis()">🔄 Re-scrape Reviews</button>
            <button class="btn-secondary" onclick="hideExistingData()">❌ Cancel</button>
        `;
    }

    window.pendingAnalysis = { appIdentifier, targetDate };
    existingDiv.style.display = 'block';
}

async function resumeCategorization() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    await runAnalysis(appIdentifier, targetDate, true, true);
}

async function useExistingData() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    await runAnalysis(appIdentifier, targetDate, true, true);
}

async function startFreshAnalysis() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    await runAnalysis(appIdentifier, targetDate, false, false, true);
}

function hideExistingData() {
    document.getElementById('existingDataDiv').style.display = 'none';
    document.getElementById('llmChangeDiv').style.display = 'none';
}

// ==========================
// LLM CHANGE PROMPT
// ==========================

function showLLMChangePrompt(data, appIdentifier, targetDate) {
    const llmDiv = document.getElementById('llmChangeDiv');
    const infoDiv = document.getElementById('llmChangeInfo');

    const prev = data.previous_llm;
    const curr = data.current_llm;
    const existing = data.existing_data;

    infoDiv.innerHTML = `
        <div style="background: #fff7ed; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
            <p>⚠️ LLM provider/model has changed since last categorization.</p>
        </div>
        <div style="display: grid; gap: 8px;">
            <div style="padding: 8px; background: var(--gray-50); border-radius: 4px;">
                <strong>Previous LLM:</strong> ${prev.provider} (${prev.model})
            </div>
            <div style="padding: 8px; background: var(--gray-50); border-radius: 4px;">
                <strong>Current LLM:</strong> ${curr.provider} (${curr.model})
            </div>
            <div style="padding: 8px; background: var(--gray-50); border-radius: 4px;">
                <strong>Categorized:</strong> ${existing.categorization_status.total_categorized} / ${existing.total_reviews}
            </div>
        </div>
    `;

    window.pendingAnalysis = { appIdentifier, targetDate };
    llmDiv.style.display = 'block';
}

async function recategorizWithNewLLM() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    await runAnalysis(appIdentifier, targetDate, true, false, false);
}

async function useOldCategorization() {
    const { appIdentifier, targetDate } = window.pendingAnalysis;
    hideExistingData();
    await runAnalysis(appIdentifier, targetDate, true, true, false);
}

// ==========================
// UTILITY FUNCTIONS
// ==========================

function toggleInput() {
    const formElem = document.getElementById('analysisForm');
    const icon = document.getElementById('toggleIcon');

    if (formElem.style.display === 'none') {
        formElem.style.display = 'block';
        icon.classList.add('open');
    } else {
        formElem.style.display = 'none';
        icon.classList.remove('open');
    }
}

function toggleTable() {
    const table = document.getElementById('detailsTable');
    const icon = document.getElementById('tableToggleIcon');

    if (table.style.display === 'none') {
        table.style.display = 'block';
        icon.classList.add('open');
    } else {
        table.style.display = 'none';
        icon.classList.remove('open');
    }
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

function hideAllResults() {
    resultsDiv.style.display = 'none';
    statusDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    document.getElementById('existingDataDiv').style.display = 'none';
    document.getElementById('llmChangeDiv').style.display = 'none';
}

function resetForm() {
    form.reset();
    hideAllResults();
    document.getElementById('analysisForm').style.display = 'block';
    document.getElementById('toggleIcon').classList.add('open');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function formatAppName(name) {
    return name.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function truncate(str, maxLen) {
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function calculateOverallAvgRating(severityScores) {
    const entries = Object.values(severityScores);
    if (entries.length === 0) return null;

    let totalWeightedRating = 0;
    let totalReviews = 0;

    entries.forEach(data => {
        totalWeightedRating += data.avg_rating * data.total_reviews;
        totalReviews += data.total_reviews;
    });

    return totalReviews > 0 ? totalWeightedRating / totalReviews : null;
}

function downloadHTML() {
    if (!currentAnalysisData || !currentAnalysisData.report_html) return;

    const htmlFile = currentAnalysisData.report_html.replace(/\\/g, '/').split('/').pop();
    window.open(`/report/${htmlFile}`, '_blank');
}

function downloadCSV() {
    if (!currentAnalysisData) return;

    const data = currentAnalysisData.trend_analysis;
    if (!data || !data.severity_scores) return;

    let csv = 'Topic,Classification,Severity,Total Reviews,Avg Rating,Low Rating %\n';

    Object.entries(data.severity_scores)
        .sort(([, a], [, b]) => b.score - a.score)
        .forEach(([topic, d]) => {
            csv += `"${topic}","${d.classification}",${d.score},${d.total_reviews},${d.avg_rating},${d.low_rating_percentage}\n`;
        });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
}
