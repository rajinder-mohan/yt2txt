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

// Auto-refresh every 30 seconds
setInterval(() => {
    if (authToken) {
        loadData();
    }
}, 30000);

