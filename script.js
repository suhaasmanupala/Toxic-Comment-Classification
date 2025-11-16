let toxicityChart = null;
let userId = localStorage.getItem('userId') || prompt('Enter a User ID:') || 'guest';
localStorage.setItem('userId', userId);

// Theme and contrast toggles
const themeToggle = document.getElementById('theme-toggle');
const contrastToggle = document.getElementById('contrast-toggle');
themeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
});
contrastToggle.addEventListener('click', () => {
    document.body.classList.toggle('high-contrast');
    localStorage.setItem('contrast', document.body.classList.contains('high-contrast') ? 'high' : 'low');
});
if (localStorage.getItem('theme') === 'dark') document.documentElement.classList.add('dark');
if (localStorage.getItem('contrast') === 'high') document.body.classList.add('high-contrast');

// Real-time feedback
const commentInput = document.getElementById('comment-input');
const realtimeFeedback = document.getElementById('realtime-feedback');
commentInput.addEventListener('input', async () => {
    const comment = commentInput.value.trim();
    if (!comment) {
        realtimeFeedback.textContent = '';
        return;
    }
    try {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment, user_id: userId })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}, URL: http://localhost:5000/predict`);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(`Backend error: ${data.error}`);
        }
        realtimeFeedback.textContent = `Real-time: ${data.prediction} (Confidence: ${(data.confidence * 100).toFixed(2)}%), Sentiment: ${data.sentiment > 0 ? 'Positive' : data.sentiment < 0 ? 'Negative' : 'Neutral'}`;
    } catch (error) {
        console.error('Real-time feedback error:', error);
        realtimeFeedback.textContent = `Error: ${error.message}. Ensure the Flask server is running at http://localhost:5000.`;
    }
});

// Prediction
const predictBtn = document.getElementById('predict-btn');
const resultsSection = document.getElementById('results');
const predictionText = document.getElementById('prediction-text');
const explanationText = document.getElementById('explanation-text');
const historyTable = document.getElementById('history-table');
predictBtn.addEventListener('click', async () => {
    const comment = commentInput.value.trim();
    if (!comment) {
        alert('Please enter a comment.');
        return;
    }
    try {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment, user_id: userId })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}, URL: http://localhost:5000/predict`);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(`Backend error: ${data.error}`);
        }

        // Display results
        resultsSection.classList.remove('hidden');
        predictionText.textContent = `Prediction: ${data.prediction} (Confidence: ${(data.confidence * 100).toFixed(2)}%), Sentiment: ${data.sentiment > 0 ? 'Positive' : data.sentiment < 0 ? 'Negative' : 'Neutral'}`;
        explanationText.innerHTML = `Key Words: ${data.explanation.map(word => `<span style="color: red">${word}</span>`).join(', ')}`;

        // Update chart
        const ctx = document.getElementById('toxicity-chart').getContext('2d');
        if (toxicityChart) toxicityChart.destroy();
        toxicityChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Toxic', 'Severe Toxic', 'Obscene', 'Threat', 'Insult', 'Identity Hate'],
                datasets: [{
                    label: 'Toxicity Scores',
                    data: data.scores.map(score => score * 100),
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    r: { beginAtZero: true, max: 100 }
                }
            }
        });

        // Update word cloud
        WordCloud(document.getElementById('word-cloud'), {
            list: data.explanation.map(word => [word, 50]),
            weightFactor: 2,
            color: 'blue'
        });

        // Update history
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="py-2">${comment}</td>
            <td class="py-2">${data.prediction}</td>
            <td class="py-2">${(data.confidence * 100).toFixed(2)}%</td>
        `;
        historyTable.prepend(row);

        // Update badges
        updateBadges(data.badges);
    } catch (error) {
        console.error('Prediction error:', error);
        alert(`Error analyzing comment: ${error.message}`);
    }
});

// Feedback submission
const feedbackBtn = document.getElementById('feedback-btn');
const feedbackInput = document.getElementById('feedback-input');
feedbackBtn.addEventListener('click', async () => {
    const issue = feedbackInput.value.trim();
    if (!issue) {
        alert('Please enter feedback.');
        return;
    }
    try {
        const response = await fetch('http://localhost:5000/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, comment: commentInput.value, issue })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}, URL: http://localhost:5000/feedback`);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(`Backend error: ${data.error}`);
        }
        alert('Feedback submitted successfully.');
        feedbackInput.value = '';
    } catch (error) {
        console.error('Feedback error:', error);
        alert(`Error submitting feedback: ${error.message}`);
    }
});

// Load history and badges
async function loadHistoryAndBadges() {
    try {
        const response = await fetch(`http://localhost:5000/history?user_id=${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}, URL: http://localhost:5000/history`);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(`Backend error: ${data.error}`);
        }
        historyTable.innerHTML = data.history.map(item => `
            <tr>
                <td class="py-2">${item.comment}</td>
                <td class="py-2">${item.prediction}</td>
                <td class="py-2">${(item.confidence * 100).toFixed(2)}%</td>
            </tr>
        `).join('');
        updateBadges(data.badges);
    } catch (error) {
        console.error('History load error:', error);
        historyTable.innerHTML = `<tr><td colspan="3">Error loading history: ${error.message}</td></tr>`;
    }
}

function updateBadges(badges) {
    const badgesDiv = document.getElementById('badges');
    badgesDiv.innerHTML = badges.map(badge => `
        <div class="bg-yellow-200 text-yellow-800 px-3 py-1 rounded-full">${badge}</div>
    `).join('');
}

loadHistoryAndBadges();