// Global variables
let currentToken = null;
let currentUser = null;

// API base URL
const API_BASE_URL = 'http://localhost:8000/api';

// DOM elements
const loginSection = document.getElementById('login-section');
const createExamSection = document.getElementById('create-exam-section');
const viewExamSection = document.getElementById('view-exam-section');
const examDisplaySection = document.getElementById('exam-display-section');

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);

    // Create exam form
    document.getElementById('create-exam-form').addEventListener('submit', handleCreateExam);

    // View exam form
    document.getElementById('view-exam-form').addEventListener('submit', handleViewExam);

    // Check if user is already logged in
    checkAuthStatus();
});

// Authentication functions
async function handleLogin(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const username = formData.get('username');
    const password = formData.get('password');

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
        });

        if (response.ok) {
            const data = await response.json();
            currentToken = data.access_token;
            currentUser = data.user;

            // Store token in localStorage
            localStorage.setItem('jwt_token', currentToken);
            localStorage.setItem('user', JSON.stringify(currentUser));

            showMessage('login-message', 'Login successful!', 'success');
            showSection('create-exam-section');

            // Update navigation
            updateNavigation();
        } else {
            const errorData = await response.json();
            showMessage('login-message', `Login failed: ${errorData.detail}`, 'error');
        }
    } catch (error) {
        showMessage('login-message', `Login error: ${error.message}`, 'error');
    }
}

function checkAuthStatus() {
    const token = localStorage.getItem('jwt_token');
    const user = localStorage.getItem('user');

    if (token && user) {
        currentToken = token;
        currentUser = JSON.parse(user);
        showSection('create-exam-section');
        updateNavigation();
    }
}

function logout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('user');

    showSection('login-section');
    updateNavigation();

    // Clear any displayed data
    document.getElementById('exam-display-section').style.display = 'none';
}

function updateNavigation() {
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        if (currentToken) {
            tab.style.display = 'inline-block';
        } else {
            if (tab.textContent === 'Logout') {
                tab.style.display = 'none';
            }
        }
    });
}

// Exam creation functions
async function handleCreateExam(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const examData = {
        title: formData.get('title'),
        description: formData.get('description') || null,
        duration_minutes: formData.get('duration_minutes') ? parseInt(formData.get('duration_minutes')) : null,
        pdf_url: formData.get('pdf_url')
    };

    try {
        const response = await fetch(`${API_BASE_URL}/exams`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(examData)
        });

        if (response.ok) {
            const exam = await response.json();
            showMessage('create-exam-message', `Exam created successfully! Exam ID: ${exam.id}`, 'success');

            // Auto-fill the view exam form
            document.getElementById('exam-id').value = exam.id;
            document.getElementById('jwt-token').value = currentToken;

            // Show the exam data if it was processed
            if (exam.processed_data) {
                displayExam(exam.processed_data);
            }
        } else {
            const errorData = await response.json();
            showMessage('create-exam-message', `Failed to create exam: ${errorData.detail}`, 'error');
        }
    } catch (error) {
        showMessage('create-exam-message', `Error creating exam: ${error.message}`, 'error');
    }
}

// Exam viewing functions
async function handleViewExam(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const examId = formData.get('exam_id');
    const jwtToken = formData.get('jwt_token');

    try {
        const response = await fetch(`${API_BASE_URL}/exams/${examId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${jwtToken}`
            }
        });

        if (response.ok) {
            const exam = await response.json();

            if (exam.processed_data) {
                displayExam(exam.processed_data);
            } else {
                showMessage('view-exam-message', 'No processed data found for this exam', 'warning');
            }
        } else {
            const errorData = await response.json();
            showMessage('view-exam-message', `Failed to fetch exam: ${errorData.detail}`, 'error');
        }
    } catch (error) {
        showMessage('view-exam-message', `Error fetching exam: ${error.message}`, 'error');
    }
}

// Display functions
function displayExam(examData) {
    const metadata = examData.metadata;
    const questions = examData.questions;

    // Update exam header
    document.getElementById('exam-title-display').textContent = metadata.title || 'Untitled Exam';
    document.getElementById('exam-subject').textContent = metadata.subject ? `Subject: ${metadata.subject}` : '';
    document.getElementById('exam-topic').textContent = metadata.topic ? `Topic: ${metadata.topic}` : '';
    document.getElementById('exam-duration-display').textContent = metadata.duration_minutes ? `Duration: ${metadata.duration_minutes} minutes` : '';
    document.getElementById('exam-difficulty').textContent = metadata.difficulty_level ? `Difficulty: ${metadata.difficulty_level}` : '';

    // Update PDF source link
    const pdfLink = document.getElementById('pdf-source-link');
    if (metadata.pdf_url) {
        pdfLink.href = metadata.pdf_url;
        pdfLink.style.display = 'inline';
    } else {
        pdfLink.style.display = 'none';
    }

    // Display questions
    const questionsContainer = document.getElementById('questions-container');
    questionsContainer.innerHTML = '';

    if (questions && questions.length > 0) {
        questions.forEach((question, index) => {
            const questionCard = createQuestionCard(question, index + 1);
            questionsContainer.appendChild(questionCard);
        });
    } else {
        questionsContainer.innerHTML = '<p class="no-questions">No questions found in this exam.</p>';
    }

    // Show exam display section
    showSection('exam-display-section');
}

// Create individual question card
function createQuestionCard(question, questionNumber) {
    const card = document.createElement('div');
    card.className = 'question-card';

    const confidenceClass = getConfidenceClass(question.confidence);
    const confidenceText = question.confidence || 'UNSURE';

    card.innerHTML = `
        <div class="question-header">
            <span class="question-number">${questionNumber}</span>
            <span class="question-confidence ${confidenceClass}">${confidenceText}</span>
        </div>

        <div class="question-text">${question.question_text}</div>

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

// Utility functions
function getConfidenceClass(confidence) {
    switch (confidence?.toUpperCase()) {
        case 'HIGH': return 'confidence-high';
        case 'MEDIUM': return 'confidence-medium';
        case 'LOW': return 'confidence-low';
        default: return 'confidence-unsure';
    }
}

function toggleHint(questionNumber) {
    const hintSection = document.getElementById(`hint-${questionNumber}`);
    const button = event.target;

    if (hintSection.style.display === 'none' || !hintSection.style.display) {
        hintSection.style.display = 'block';
        button.textContent = 'Hide Hint';
    } else {
        hintSection.style.display = 'none';
        button.textContent = 'Show Hint';
    }
}

function toggleSolution(questionNumber) {
    const solutionSection = document.getElementById(`solution-${questionNumber}`);
    const button = event.target;

    if (solutionSection.style.display === 'none' || !solutionSection.style.display) {
        solutionSection.style.display = 'block';
        button.textContent = 'Hide Solution';
    } else {
        solutionSection.style.display = 'none';
        button.textContent = 'Show Solution';
    }
}

function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });

    // Show the requested section
    document.getElementById(sectionId).style.display = 'block';

    // Update navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Find and activate the corresponding tab
    const tabMap = {
        'create-exam-section': 0,
        'view-exam-section': 1
    };

    if (tabMap[sectionId] !== undefined) {
        document.querySelectorAll('.nav-tab')[tabMap[sectionId]].classList.add('active');
    }
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `message ${type}`;

    // Clear message after 5 seconds
    setTimeout(() => {
        element.textContent = '';
        element.className = 'message';
    }, 5000);
}