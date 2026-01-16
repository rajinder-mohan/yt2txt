let authToken = localStorage.getItem('authToken');
let currentUsername = localStorage.getItem('username');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        showDashboard();
        loadData();
    } else {
        showLogin();
    }
    
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('refreshBtn').addEventListener('click', loadData);
    document.getElementById('searchInput').addEventListener('input', filterVideos);
    document.getElementById('statusFilter').addEventListener('change', filterVideos);
    document.getElementById('submitChannelBtn').addEventListener('click', handleChannelSubmit);
    document.getElementById('createUserBtn').addEventListener('click', handleCreateUser);
    document.getElementById('refreshUsersBtn').addEventListener('click', loadUsers);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // Modal
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('transcriptModal').classList.add('hidden');
    });
});

function showLogin() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    if (currentUsername) {
        document.getElementById('usernameDisplay').textContent = `Logged in as: ${currentUsername}`;
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.token;
            currentUsername = data.username;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('username', currentUsername);
            showDashboard();
            loadData();
            errorDiv.textContent = '';
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Login failed';
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
    }
}

function handleLogout() {
    if (authToken) {
        fetch('/api/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: authToken })
        });
    }
    authToken = null;
    currentUsername = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    showLogin();
}


function displayVideos(videos) {
    const tbody = document.getElementById('videosTableBody');
    
    if (videos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No videos found</td></tr>';
        return;
    }
    
    tbody.innerHTML = videos.map(video => `
        <tr>
            <td><a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank">${video.video_id}</a></td>
            <td>${video.video_url || '-'}</td>
            <td><span class="status-badge status-${video.status}">${video.status}</span></td>
            <td>
                ${video.transcript 
                    ? `<span class="transcript-preview" onclick="showTranscript('${video.video_id}', \`${escapeHtml(video.transcript.substring(0, 100))}...\`)">${escapeHtml(video.transcript.substring(0, 50))}...</span>`
                    : '-'}
            </td>
            <td class="error-preview">${video.error_message ? escapeHtml(video.error_message) : '-'}</td>
            <td>${formatDate(video.created_at)}</td>
            <td>${formatDate(video.updated_at)}</td>
            <td>
                ${video.transcript 
                    ? `<button onclick="showFullTranscript('${video.video_id}')" class="btn-secondary">View Full</button>`
                    : '-'}
            </td>
        </tr>
    `).join('');
}

let allVideos = [];

async function showFullTranscript(videoId) {
    try {
        const response = await fetch(`/api/admin/videos`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const videos = await response.json();
            const video = videos.find(v => v.video_id === videoId);
            if (video && video.transcript) {
                document.getElementById('transcriptContent').textContent = video.transcript;
                document.getElementById('transcriptModal').classList.remove('hidden');
            }
        }
    } catch (error) {
        console.error('Error loading transcript:', error);
    }
}

function showTranscript(videoId, preview) {
    showFullTranscript(videoId);
}

function filterVideos() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    
    const filtered = allVideos.filter(video => {
        const matchesSearch = !searchTerm || 
            video.video_id.toLowerCase().includes(searchTerm) ||
            (video.video_url && video.video_url.toLowerCase().includes(searchTerm));
        const matchesStatus = !statusFilter || video.status === statusFilter;
        return matchesSearch && matchesStatus;
    });
    
    displayVideos(filtered);
}

async function loadData() {
    try {
        // Load stats
        const statsResponse = await fetch('/api/admin/stats', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            document.getElementById('statTotal').textContent = stats.total;
            document.getElementById('statSuccess').textContent = stats.success;
            document.getElementById('statFailed').textContent = stats.failed;
            document.getElementById('statProcessing').textContent = stats.processing;
        }
        
        // Load videos
        const videosResponse = await fetch('/api/admin/videos', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (videosResponse.ok) {
            allVideos = await videosResponse.json();
            filterVideos();
        } else if (videosResponse.status === 401) {
            handleLogout();
        }
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function handleChannelSubmit() {
    const channelUrl = document.getElementById('channelUrlInput').value.trim();
    const maxVideos = document.getElementById('maxVideosInput').value;
    const statusDiv = document.getElementById('channelStatus');
    const submitBtn = document.getElementById('submitChannelBtn');
    
    if (!channelUrl) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please enter a channel URL';
        return;
    }
    
    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Submitting channel URL...';
    
    try {
        const requestBody = {
            channel_url: channelUrl,
            max_results: maxVideos ? parseInt(maxVideos) : null
        };
        
        const response = await fetch('/api/channel/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(requestBody)
        });
        
        if (response.ok) {
            const data = await response.json();
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = `Success! Found ${data.total_videos} videos. Processing started. ${data.message || ''}`;
            
            // Clear form
            document.getElementById('channelUrlInput').value = '';
            document.getElementById('maxVideosInput').value = '';
            
            // Refresh data after a delay
            setTimeout(() => {
                loadData();
            }, 2000);
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to process channel';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Connection error. Please try again.';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Channel';
    }
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const activeTab = document.getElementById(tabName + 'Tab');
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    // Load data for specific tabs
    if (tabName === 'users') {
        loadUsers();
    } else if (tabName === 'videos') {
        loadData();
    }
}

async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const users = await response.json();
            displayUsers(users);
        } else if (response.status === 401) {
            handleLogout();
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="loading">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${escapeHtml(user.username)}</td>
            <td>${user.created_at ? formatDate(user.created_at) : '-'}</td>
            <td>
                ${user.username === currentUsername 
                    ? '<span style="color: #666;">Cannot delete yourself</span>' 
                    : `<button onclick="deleteUser('${escapeHtml(user.username)}')" class="btn-secondary" style="background: #dc3545;">Delete</button>`}
            </td>
        </tr>
    `).join('');
}

async function handleCreateUser() {
    const username = document.getElementById('newUsernameInput').value.trim();
    const password = document.getElementById('newPasswordInput').value;
    const statusDiv = document.getElementById('userFormStatus');
    const createBtn = document.getElementById('createUserBtn');
    
    if (!username || username.length < 3) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Username must be at least 3 characters';
        return;
    }
    
    if (!password || password.length < 6) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Password must be at least 6 characters';
        return;
    }
    
    createBtn.disabled = true;
    createBtn.textContent = 'Creating...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Creating user...';
    
    try {
        const response = await fetch('/api/admin/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = `User '${username}' created successfully!`;
            
            // Clear form
            document.getElementById('newUsernameInput').value = '';
            document.getElementById('newPasswordInput').value = '';
            
            // Refresh users list
            loadUsers();
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to create user';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Connection error. Please try again.';
    } finally {
        createBtn.disabled = false;
        createBtn.textContent = 'Create User';
    }
}

async function deleteUser(username) {
    if (!confirm(`Are you sure you want to delete user '${username}'?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${encodeURIComponent(username)}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            loadUsers();
        } else {
            const error = await response.json();
            alert(error.detail || 'Failed to delete user');
        }
    } catch (error) {
        alert('Connection error. Please try again.');
    }
}

// Auto-refresh every 30 seconds
setInterval(() => {
    if (authToken) {
        // Only refresh if videos tab is active
        const videosTab = document.getElementById('videosTab');
        if (videosTab && videosTab.classList.contains('active')) {
            loadData();
        }
    }
}, 30000);

