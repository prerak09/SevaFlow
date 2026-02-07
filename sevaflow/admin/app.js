/**
 * SEVAFLOW Admin Dashboard - Application Logic
 * 
 * Handles:
 * - API communication
 * - View management
 * - Complaint operations
 * - UI interactions
 */

// ============================================
// Configuration
// ============================================
const API_BASE = '';  // Same origin
const ADMIN_SECRET = 'sevaflow_admin_2024';  // Should match .env

// ============================================
// State
// ============================================
let currentView = 'dashboard';
let currentPage = 1;
let totalPages = 1;
let currentFilters = {};
let selectedComplaint = null;

// ============================================
// API Helpers
// ============================================
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'X-Admin-Secret': ADMIN_SECRET,
        ...options.headers
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============================================
// Toast Notifications
// ============================================
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');

    toastMessage.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ============================================
// View Management
// ============================================
function switchView(viewName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.toggle('active', view.id === `${viewName}-view`);
    });

    // Update title
    const titles = {
        'dashboard': 'Dashboard Overview',
        'complaints': 'All Complaints',
        'departments': 'Departments'
    };
    document.getElementById('page-title').textContent = titles[viewName] || 'SEVAFLOW';

    currentView = viewName;

    // Load view data
    switch (viewName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'complaints':
            loadComplaints();
            break;
        case 'departments':
            loadDepartments();
            break;
    }
}

// ============================================
// Dashboard
// ============================================
async function loadDashboard() {
    try {
        const stats = await apiCall('/api/admin/stats');

        document.getElementById('stat-total').textContent = stats.total_complaints;
        document.getElementById('stat-pending').textContent = stats.pending;
        document.getElementById('stat-progress').textContent = stats.in_progress;
        document.getElementById('stat-resolved').textContent = stats.resolved;

        // Load recent complaints
        const data = await apiCall('/api/complaints?per_page=5');
        renderRecentComplaints(data.complaints);

    } catch (error) {
        showToast('Failed to load dashboard', 'error');
    }
}

function renderRecentComplaints(complaints) {
    const container = document.getElementById('recent-complaints-table');

    if (complaints.length === 0) {
        container.innerHTML = '<p style="color: var(--gray-500); text-align: center; padding: 40px;">No complaints yet</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Issue</th>
                    <th>Location</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                ${complaints.map(c => `
                    <tr>
                        <td><span class="complaint-id">${c.complaint_id}</span></td>
                        <td>${escapeHtml(c.issue_type)}</td>
                        <td>${escapeHtml(truncate(c.location, 25))}</td>
                        <td>${escapeHtml(c.department)}</td>
                        <td><span class="badge badge-status-${c.status}">${formatStatus(c.status)}</span></td>
                        <td><span class="badge badge-priority-${c.priority}">${c.priority.toUpperCase()}</span></td>
                        <td>
                            <button class="btn btn-secondary action-btn" onclick="openStatusModal('${c.complaint_id}', '${c.status}')">
                                Update
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// ============================================
// Complaints List
// ============================================
async function loadComplaints() {
    try {
        // Load departments for filter dropdown
        await loadDepartmentOptions();

        // Build query params
        let params = new URLSearchParams();
        params.append('page', currentPage);
        params.append('per_page', 20);

        if (currentFilters.status) params.append('status', currentFilters.status);
        if (currentFilters.department) params.append('department', currentFilters.department);
        if (currentFilters.priority) params.append('priority', currentFilters.priority);

        const data = await apiCall(`/api/complaints?${params.toString()}`);

        renderComplaintsTable(data.complaints);
        renderPagination(data.total, data.page, data.per_page);

    } catch (error) {
        showToast('Failed to load complaints', 'error');
    }
}

async function loadDepartmentOptions() {
    try {
        const data = await apiCall('/api/admin/departments');
        const select = document.getElementById('filter-department');

        // Keep "All Departments" option
        select.innerHTML = '<option value="">All Departments</option>';

        data.departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.name;
            option.textContent = dept.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load departments:', error);
    }
}

function renderComplaintsTable(complaints) {
    const container = document.getElementById('complaints-table');

    if (complaints.length === 0) {
        container.innerHTML = '<p style="color: var(--gray-500); text-align: center; padding: 60px;">No complaints found matching the filters</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Issue</th>
                    <th>Location</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Created</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                ${complaints.map(c => `
                    <tr>
                        <td><span class="complaint-id">${c.complaint_id}</span></td>
                        <td title="${escapeHtml(c.issue_type)}">${escapeHtml(truncate(c.issue_type, 30))}</td>
                        <td title="${escapeHtml(c.location)}">${escapeHtml(truncate(c.location, 25))}</td>
                        <td>${escapeHtml(c.department)}</td>
                        <td><span class="badge badge-status-${c.status}">${formatStatus(c.status)}</span></td>
                        <td><span class="badge badge-priority-${c.priority}">${c.priority.toUpperCase()}</span></td>
                        <td>${formatDate(c.created_at)}</td>
                        <td>
                            <button class="btn btn-secondary action-btn" onclick="openStatusModal('${c.complaint_id}', '${c.status}')">
                                Update
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function renderPagination(total, page, perPage) {
    totalPages = Math.ceil(total / perPage);
    const container = document.getElementById('pagination');

    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = `
        <button ${page <= 1 ? 'disabled' : ''} onclick="goToPage(${page - 1})">← Prev</button>
        <span class="pagination-info">Page ${page} of ${totalPages}</span>
        <button ${page >= totalPages ? 'disabled' : ''} onclick="goToPage(${page + 1})">Next →</button>
    `;

    container.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadComplaints();
}

function applyFilters() {
    currentFilters = {
        status: document.getElementById('filter-status').value,
        department: document.getElementById('filter-department').value,
        priority: document.getElementById('filter-priority').value
    };
    currentPage = 1;
    loadComplaints();
}

function clearFilters() {
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-department').value = '';
    document.getElementById('filter-priority').value = '';
    currentFilters = {};
    currentPage = 1;
    loadComplaints();
}

// ============================================
// Departments
// ============================================
async function loadDepartments() {
    try {
        const data = await apiCall('/api/admin/departments');
        renderDepartments(data.departments);
    } catch (error) {
        showToast('Failed to load departments', 'error');
    }
}

function renderDepartments(departments) {
    const container = document.getElementById('departments-grid');

    container.innerHTML = departments.map(dept => `
        <div class="department-card">
            <h3>🏢 ${escapeHtml(dept.name)}</h3>
            <p class="department-info">📧 ${escapeHtml(dept.contact)}</p>
            <span class="department-sla">⏱️ SLA: ${dept.sla_hours} hours</span>
        </div>
    `).join('');
}

// ============================================
// Status Update Modal
// ============================================
function openStatusModal(complaintId, currentStatus) {
    selectedComplaint = complaintId;

    document.getElementById('modal-complaint-id').textContent = complaintId;
    document.getElementById('modal-current-status').textContent = formatStatus(currentStatus);
    document.getElementById('new-status').value = currentStatus;
    document.getElementById('status-notes').value = '';
    document.getElementById('notify-citizen').checked = true;

    document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    selectedComplaint = null;
}

async function confirmStatusUpdate() {
    if (!selectedComplaint) return;

    const newStatus = document.getElementById('new-status').value;
    const notes = document.getElementById('status-notes').value;
    const notifyCitizen = document.getElementById('notify-citizen').checked;

    try {
        await apiCall(`/api/admin/complaints/${selectedComplaint}/status`, {
            method: 'PATCH',
            body: JSON.stringify({
                new_status: newStatus,
                notes: notes || null,
                notify_citizen: notifyCitizen
            })
        });

        showToast(`Complaint ${selectedComplaint} updated to ${formatStatus(newStatus)}`, 'success');
        closeModal();

        // Refresh current view
        if (currentView === 'dashboard') {
            loadDashboard();
        } else if (currentView === 'complaints') {
            loadComplaints();
        }

    } catch (error) {
        showToast(`Failed to update: ${error.message}`, 'error');
    }
}

// ============================================
// Utility Functions
// ============================================
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function formatStatus(status) {
    return status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

// ============================================
// Event Listeners
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(item.dataset.view);
        });
    });

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        switchView(currentView);
        showToast('Data refreshed', 'success');
    });

    // Filter buttons
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('clear-filters').addEventListener('click', clearFilters);

    // Modal
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-cancel').addEventListener('click', closeModal);
    document.getElementById('modal-confirm').addEventListener('click', confirmStatusUpdate);
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
        if (e.target === document.getElementById('modal-overlay')) {
            closeModal();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });

    // Initial load
    loadDashboard();
});
