// API Base URL (runtime-config.js can override this without rebuild)
const API_BASE = (typeof getApiBaseUrl === 'function')
    ? getApiBaseUrl()
    : `${window.location.origin}/api`;
const API_TIMEOUT_MS = 25000;

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Token management
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
}

function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

function setRefreshToken(token) {
    if (!token) return;
    localStorage.setItem('refresh_token', token);
}

function removeRefreshToken() {
    localStorage.removeItem('refresh_token');
}

function getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function removeUser() {
    localStorage.removeItem('user');
}

// API call helper with robust error handling
async function apiCall(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
    };

    const controller = options.signal ? null : new AbortController();
    const timeoutId = controller
        ? setTimeout(() => controller.abort(), API_TIMEOUT_MS)
        : null;

    let response;
    try {
        response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
            signal: options.signal || (controller ? controller.signal : undefined)
        });
    } catch (err) {
        if (err && err.name === 'AbortError') {
            throw new Error('Server is taking too long to respond. Please try again in a moment.');
        }
        throw new Error('Unable to reach server. Please check connection or try again shortly.');
    } finally {
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
    }

    let data;
    try {
        data = await response.json();
    } catch {
        throw new Error('Invalid response from server');
    }

    if (response.status === 401) {
        const shouldRetry = !options._retry && !!getRefreshToken();
        if (shouldRetry) {
            const refreshed = await tryRefreshToken();
            if (refreshed) {
                return apiCall(endpoint, { ...options, _retry: true });
            }
        }

        removeToken();
        removeRefreshToken();
        removeUser();
        window.location.href = 'login.html';
        throw new Error('Session expired. Please login again.');
    }

    if (!response.ok) {
        const msg = data.message || data.error || 'Something went wrong';
        throw new Error(msg);
    }

    return data;
}

async function tryRefreshToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
        const response = await fetch(`${API_BASE}/auth/refresh-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (!response.ok) return false;

        const data = await response.json();
        if (!data.token) return false;

        setToken(data.token);
        if (data.refresh_token) {
            setRefreshToken(data.refresh_token);
        }
        return true;
    } catch {
        return false;
    }
}

// Show alert
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Logout
function logout() {
    removeToken();
    removeRefreshToken();
    removeUser();
    window.location.href = 'login.html';
}

// Check authentication
function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

const WORKFLOW_STATUS_META = {
    received: { badgeClass: 'badge-received', label: 'Received', translateKey: 'status_received' },
    assigned: { badgeClass: 'badge-assigned', label: 'Assigned to Department', translateKey: 'status_assigned' },
    manual_review: { badgeClass: 'badge-investigation', label: 'Manual Review Required', translateKey: 'status_manual_review' },
    progress: { badgeClass: 'badge-progress', label: 'Under Progress', translateKey: 'status_under_progress' },
    investigation: { badgeClass: 'badge-investigation', label: 'Investigation', translateKey: 'status_investigation' },
    reviewed: { badgeClass: 'badge-reviewed', label: 'Reviewed', translateKey: 'status_reviewed' },
    resolved: { badgeClass: 'badge-resolved', label: 'Resolved', translateKey: 'status_resolved' },
    closed: { badgeClass: 'badge-closed', label: 'Closed', translateKey: 'status_closed' },
};

function normalizeWorkflowStatus(status) {
    if (!status) return 'received';
    const raw = String(status).trim().toLowerCase();

    if (raw === 'received') return 'received';
    if (raw === 'assigned' || raw === 'assigned to department') return 'assigned';
    if (raw === 'manual review required') return 'manual_review';
    if (raw === 'in progress' || raw === 'under progress') return 'progress';
    if (raw.includes('investigation')) return 'investigation';
    if (raw === 'reviewed') return 'reviewed';
    if (raw === 'resolved') return 'resolved';
    if (raw === 'closed' || raw === 'rejected') return 'closed';
    return 'received';
}

function getStatusBadgeClass(status) {
    const key = normalizeWorkflowStatus(status);
    return WORKFLOW_STATUS_META[key].badgeClass;
}

function getStatusDisplayLabel(status) {
    if (!status) return WORKFLOW_STATUS_META.received.label;
    const key = normalizeWorkflowStatus(status);
    if (
        typeof status === 'string'
        && status.toLowerCase().includes('fraud')
    ) {
        return status;
    }
    return WORKFLOW_STATUS_META[key].label;
}

function renderStatusBadge(status) {
    const key = normalizeWorkflowStatus(status);
    const meta = WORKFLOW_STATUS_META[key];
    const safeLabel = escapeHtml(getStatusDisplayLabel(status));
    
    // If it's a fraud status or something dynamic, we might not have a key
    if (typeof status === 'string' && status.toLowerCase().includes('fraud')) {
        return `<span class="badge badge-investigation">${safeLabel}</span>`;
    }

    return `<span class="badge ${meta.badgeClass}" data-translate="${meta.translateKey}">${safeLabel}</span>`;
}

// Get home URL based on user role
function getHomeUrl() {
    const user = getUser();
    if (!user) return 'index.html';
    if (user.role === 'ADMIN') return 'admin.html';
    if (user.role === 'OFFICER') return 'officer.html';
    return 'index.html';
}

// Update header with user info
function updateHeader() {
    const user = getUser();
    if (!user) return;

    const userInfoDiv = document.querySelector('.user-info');
    if (userInfoDiv) {
        let roleKey = 'role_citizen';
        if (user.role === 'ADMIN') roleKey = 'role_admin';
        if (user.role === 'OFFICER') roleKey = 'role_officer';

        userInfoDiv.innerHTML = `
            <span>${user.name}</span>
            <span class="badge ${user.role === 'ADMIN' ? 'badge-resolved' : user.role === 'OFFICER' ? 'badge-progress' : 'badge-received'}" data-translate="${roleKey}">${user.role}</span>
        `;
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Add logout button handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Update header
    updateHeader();

    // Register Service Worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
});
