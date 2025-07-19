const API_BASE = 'http://localhost:8000';

// DOM elements
const loginSection = document.getElementById('login-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const dashboardBtn = document.getElementById('dashboardBtn');
const logoutBtn = document.getElementById('logoutBtn');

// Test API connection
async function testConnection() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('API Connection:', data);
    } catch (error) {
        console.error('API Connection failed:', error);
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('examForm');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    const formattedExam = document.getElementById('formattedExam');

    // API base URL - change this to match your backend URL
    const API_BASE_URL = 'http://localhost:8000';

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const examId = document.getElementById('examId').value;
        const jwtToken = document.getElementById('jwtToken').value.trim();

        if (!examId || !jwtToken) {
            showError('Please fill in all fields');
            return;
        }

        // Show loading, hide other sections
        showLoading();
        hideError();
        hideFormattedExam();

        try {
            const response = await fetch(`${API_BASE_URL}/api/exams/${examId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${jwtToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            displayFormattedExam(data);

        } catch (err) {
            showError(`Failed to fetch exam data: ${err.message}`);
        } finally {
            hideLoading();
        }
    });

    // Display formatted exam
    function displayFormattedExam(data) {
        // Extract metadata
        const metadata = data.questions_json?.metadata || {};
        const questions = data.questions_json?.questions || [];

        // Update exam header
        document.getElementById('examTitle').textContent = metadata.title || data.title || 'Untitled Exam';

        const examSubject = document.getElementById('examSubject');
        const examTopic = document.getElementById('examTopic');
        const examDuration = document.getElementById('examDuration');
        const examDifficulty = document.getElementById('examDifficulty');

        examSubject.textContent = metadata.subject ? `Subject: ${metadata.subject}` : '';
        examTopic.textContent = metadata.topic ? `Topic: ${metadata.topic}` : '';
        examDuration.textContent = metadata.duration_minutes ? `Duration: ${metadata.duration_minutes} min` : '';
        examDifficulty.textContent = metadata.difficulty_level ? `Difficulty: ${metadata.difficulty_level}` : '';

        // Clear previous questions
        const questionsContainer = document.getElementById('questionsContainer');
        questionsContainer.innerHTML = '';

        // Create question cards
        questions.forEach((question, index) => {
            const questionCard = createQuestionCard(question, index + 1);
            questionsContainer.appendChild(questionCard);
        });

        // Show formatted exam
        showFormattedExam();
    }

    // Create individual question card
    function createQuestionCard(question, questionNumber) {
        const card = document.createElement('div');
        card.className = 'question-card';

        const confidenceClass = getConfidenceClass(question.confidence);
        const confidenceText = question.confidence || 'UNSURE';

        // Generate diagrams HTML if diagrams exist
        const diagramsHTML = question.diagrams && question.diagrams.length > 0 ?
            question.diagrams.map((diagram, index) => `
                <div class="question-image">
                    <img src="data:image/png;base64,${diagram.base64_image}"
                         alt="Question ${questionNumber} diagram ${index + 1}"
                         class="question-img"
                         title="${diagram.description || ''}">
                </div>
            `).join('') : '';

        card.innerHTML = `
            <div class="question-header">
                <span class="question-number">${questionNumber}</span>
                <span class="question-confidence ${confidenceClass}">${confidenceText}</span>
            </div>

            <div class="question-text">${question.question_text}</div>

            ${diagramsHTML}

            ${question.options && question.options.length > 0 ? `
                <ul class="options-list">
                    ${question.options.map((option, optionIndex) => {
                        const isCorrect = question.correct_answer &&
                                         option.startsWith(question.correct_answer + '.');
                        return `<li class="option-item ${isCorrect ? 'correct-answer' : ''}">${option}</li>`;
                    }).join('')}
                </ul>
            ` : ''}

            <div class="question-actions">
                ${question.hint ? `
                    <button class="btn btn-small" onclick="toggleHint(${questionNumber})">
                        Show Hint
                    </button>
                ` : ''}

                ${question.explanation ? `
                    <button class="btn btn-small" onclick="toggleSolution(${questionNumber})">
                        Show Solution
                    </button>
                ` : ''}
            </div>

            ${question.hint ? `
                <div id="hint-${questionNumber}" class="hint-section">
                    <div class="hint-title">💡 Hint</div>
                    <div class="hint-content">${question.hint}</div>
                </div>
            ` : ''}

            ${question.explanation ? `
                <div id="solution-${questionNumber}" class="solution-section">
                    <div class="solution-title">📝 Solution</div>
                    <div class="solution-content">${question.explanation}</div>
                </div>
            ` : ''}
        `;

        return card;
    }

    // Get confidence class for styling
    function getConfidenceClass(confidence) {
        switch (confidence?.toUpperCase()) {
            case 'HIGH': return 'confidence-high';
            case 'MEDIUM': return 'confidence-medium';
            case 'LOW': return 'confidence-low';
            case 'UNSURE':
            default: return 'confidence-unsure';
        }
    }

    // Toggle hint visibility
    window.toggleHint = function(questionNumber) {
        const hintSection = document.getElementById(`hint-${questionNumber}`);
        const button = hintSection.previousElementSibling.querySelector('button');

        if (hintSection.classList.contains('show')) {
            hintSection.classList.remove('show');
            button.textContent = 'Show Hint';
        } else {
            hintSection.classList.add('show');
            button.textContent = 'Hide Hint';
        }
    };

    // Toggle solution visibility
    window.toggleSolution = function(questionNumber) {
        const solutionSection = document.getElementById(`solution-${questionNumber}`);
        const buttons = solutionSection.previousElementSibling.querySelectorAll('button');
        const solutionButton = buttons[buttons.length - 1]; // Last button is solution button

        if (solutionSection.classList.contains('show')) {
            solutionSection.classList.remove('show');
            solutionButton.textContent = 'Show Solution';
        } else {
            solutionSection.classList.add('show');
            solutionButton.textContent = 'Hide Solution';
        }
    };

    // Helper functions
    function showLoading() {
        loading.classList.remove('hidden');
    }

    function hideLoading() {
        loading.classList.add('hidden');
    }

    function showError(message) {
        errorMessage.textContent = message;
        error.classList.remove('hidden');
    }

    function hideError() {
        error.classList.add('hidden');
    }

    function showFormattedExam() {
        formattedExam.classList.remove('hidden');
        // Scroll to formatted exam
        formattedExam.scrollIntoView({ behavior: 'smooth' });
    }

    function hideFormattedExam() {
        formattedExam.classList.add('hidden');
    }

    // Auto-resize textarea
    const jwtTextarea = document.getElementById('jwtToken');
    jwtTextarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });

    // Add some helpful instructions
    const instructions = document.createElement('div');
    instructions.innerHTML = `
        <div style="background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin-top: 20px; font-size: 0.9rem;">
            <h4 style="margin: 0 0 10px 0; color: #1976d2;">How to get your JWT token:</h4>
            <ol style="margin: 0; padding-left: 20px; color: #424242;">
                <li>Go to <a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs</a></li>
                <li>Click on "Authorize" button at the top</li>
                <li>Enter your JWT token in the format: <code>Bearer your_token_here</code></li>
                <li>Or login via <code>POST /api/auth/login</code> to get a token</li>
            </ol>
        </div>
    `;
    document.querySelector('.container').appendChild(instructions);
});

// Simple navigation (placeholder for now)
loginBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showLogin();
});

dashboardBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showDashboard();
});

logoutBtn.addEventListener('click', (e) => {
    e.preventDefault();
    logout();
});

function showLogin() {
    loginSection.style.display = 'block';
    dashboardSection.style.display = 'none';
    loginBtn.style.display = 'none';
    dashboardBtn.style.display = 'none';
    logoutBtn.style.display = 'none';
}

function showDashboard() {
    loginSection.style.display = 'none';
    dashboardSection.style.display = 'block';
    loginBtn.style.display = 'none';
    dashboardBtn.style.display = 'inline';
    logoutBtn.style.display = 'inline';
}

function logout() {
    showLogin();
    loginBtn.style.display = 'inline';
}

// Form submission (placeholder)
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Login functionality will be implemented in Phase 1');
    showDashboard();
});