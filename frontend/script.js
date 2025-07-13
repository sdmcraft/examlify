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
document.addEventListener('DOMContentLoaded', () => {
    testConnection();
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