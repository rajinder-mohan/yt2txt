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
    
    // Cookie management buttons
    const saveCookiesBtn = document.getElementById('saveCookiesBtn');
    const testCookiesBtn = document.getElementById('testCookiesBtn');
    const deleteCookiesBtn = document.getElementById('deleteCookiesBtn');
    if (saveCookiesBtn) {
        saveCookiesBtn.addEventListener('click', handleSaveCookies);
    }
    if (testCookiesBtn) {
        testCookiesBtn.addEventListener('click', handleTestCookies);
    }
    if (deleteCookiesBtn) {
        deleteCookiesBtn.addEventListener('click', handleDeleteCookies);
    }
    
    // Tab switching - attach listeners
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (tabButtons.length > 0) {
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const tabName = btn.getAttribute('data-tab');
                if (tabName) {
                    switchTab(tabName);
                }
            });
        });
    }
    
    // Settings tab elements (optional - only if they exist)
    const saveWebhookBtn = document.getElementById('saveWebhookBtn');
    const testWebhookBtn = document.getElementById('testWebhookBtn');
    if (saveWebhookBtn) {
        saveWebhookBtn.addEventListener('click', handleSaveWebhook);
    }
    if (testWebhookBtn) {
        testWebhookBtn.addEventListener('click', handleTestWebhook);
    }
    
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
    
    // Check if webhook is enabled
    try {
        const settingsResponse = await fetch('/api/admin/settings/use_webhook', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        let useWebhook = false;
        let webhookUrl = null;
        
        if (settingsResponse.ok) {
            const settingsData = await settingsResponse.json();
            useWebhook = settingsData.value === 'true';
            
            if (useWebhook) {
                const webhookResponse = await fetch('/api/admin/settings/n8n_webhook_url', {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                if (webhookResponse.ok) {
                    const webhookData = await webhookResponse.json();
                    webhookUrl = webhookData.value;
                }
            }
        }
        
        // If webhook is enabled and URL exists, send to webhook
        if (useWebhook && webhookUrl) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Sending to webhook...';
            statusDiv.className = 'channel-status info';
            statusDiv.textContent = 'Sending channel URL to n8n webhook...';
            
            try {
                const webhookResponse = await fetch(webhookUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        channel_url: channelUrl,
                        max_results: maxVideos ? parseInt(maxVideos) : null
                    })
                });
                
                if (webhookResponse.ok) {
                    statusDiv.className = 'channel-status success';
                    statusDiv.textContent = 'Channel URL sent to n8n webhook successfully!';
                    
                    // Clear form
                    document.getElementById('channelUrlInput').value = '';
                    document.getElementById('maxVideosInput').value = '';
                } else {
                    statusDiv.className = 'channel-status error';
                    statusDiv.textContent = `Webhook returned error: ${webhookResponse.status}`;
                }
            } catch (error) {
                statusDiv.className = 'channel-status error';
                statusDiv.textContent = 'Failed to send to webhook: ' + error.message;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Channel';
            }
            return;
        }
    } catch (error) {
        console.error('Error checking webhook settings:', error);
    }
    
    // Default: Process directly
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
    try {
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
        
        // Show the selected tab content
        const activeTab = document.getElementById(tabName + 'Tab');
        if (activeTab) {
            activeTab.classList.add('active');
        } else {
            console.warn('Tab content not found:', tabName + 'Tab');
        }
        
        // Load data for specific tabs
        if (tabName === 'users') {
            loadUsers();
        } else if (tabName === 'videos') {
            loadData();
        } else if (tabName === 'settings') {
            // Only load settings if the tab exists
            const settingsTab = document.getElementById('settingsTab');
            if (settingsTab) {
                loadSettings();
            }
        } else if (tabName === 'channel') {
            // Channel tab doesn't need to load data
        }
    } catch (error) {
        console.error('Error switching tab:', error);
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

async function loadSettings() {
    const webhookUrlInput = document.getElementById('n8nWebhookUrlInput');
    const useWebhookCheckbox = document.getElementById('useWebhookCheckbox');
    
    // If settings elements don't exist, skip loading
    if (!webhookUrlInput && !useWebhookCheckbox) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/settings/n8n_webhook_url', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok && webhookUrlInput) {
            const data = await response.json();
            webhookUrlInput.value = data.value || '';
        } else if (response.status === 404 && webhookUrlInput) {
            // Setting doesn't exist yet, that's fine
            webhookUrlInput.value = '';
        } else if (response.status === 401) {
            handleLogout();
        }
        
        // Load webhook enabled setting
        if (useWebhookCheckbox) {
            const enabledResponse = await fetch('/api/admin/settings/use_webhook', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            
            if (enabledResponse.ok) {
                const enabledData = await enabledResponse.json();
                useWebhookCheckbox.checked = enabledData.value === 'true';
            }
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
    
    // Load cookies
    await loadCookies();
}

async function loadCookies() {
    const cookiesInput = document.getElementById('youtubeCookiesInput');
    const cookiesStatusText = document.getElementById('cookiesStatusText');
    
    if (!cookiesInput || !cookiesStatusText) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/cookies', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.has_cookies && data.cookies) {
                cookiesInput.value = data.cookies;
                const cookieCount = data.cookies.split(';').filter(c => c.trim() && c.includes('=')).length;
                cookiesStatusText.textContent = `Cookies are configured (${cookieCount} cookies found)`;
                cookiesStatusText.style.color = '#28a745';
            } else {
                cookiesInput.value = '';
                cookiesStatusText.textContent = 'No cookies configured';
                cookiesStatusText.style.color = '#dc3545';
            }
        } else if (response.status === 401) {
            handleLogout();
        }
    } catch (error) {
        console.error('Error loading cookies:', error);
        if (cookiesStatusText) {
            cookiesStatusText.textContent = 'Error loading cookies status';
            cookiesStatusText.style.color = '#dc3545';
        }
    }
}

async function handleSaveCookies() {
    const cookiesInput = document.getElementById('youtubeCookiesInput');
    const statusDiv = document.getElementById('cookiesStatus');
    const saveBtn = document.getElementById('saveCookiesBtn');
    
    if (!cookiesInput || !statusDiv || !saveBtn) {
        return;
    }
    
    const cookies = cookiesInput.value.trim();
    
    if (!cookies) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please enter cookies';
        return;
    }
    
    // Validate cookie format
    if (!cookies.includes('=')) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Invalid cookie format. Expected: name1=value1; name2=value2; ...';
        return;
    }
    
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Saving cookies...';
    
    try {
        const response = await fetch('/api/admin/cookies', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ cookies: cookies })
        });
        
        if (response.ok) {
            const data = await response.json();
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = `Cookies saved successfully! ${data.cookie_count || ''} cookies configured.`;
            await loadCookies(); // Refresh status
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to save cookies';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Connection error: ' + error.message;
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Cookies';
    }
}

async function handleTestCookies() {
    const cookiesInput = document.getElementById('youtubeCookiesInput');
    const statusDiv = document.getElementById('cookiesStatus');
    const testBtn = document.getElementById('testCookiesBtn');
    
    if (!cookiesInput || !statusDiv || !testBtn) {
        return;
    }
    
    const cookies = cookiesInput.value.trim();
    
    if (!cookies) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please enter cookies first';
        return;
    }
    
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Testing cookies format...';
    
    // Basic validation
    const cookieCount = cookies.split(';').filter(c => c.trim() && c.includes('=')).length;
    
    if (cookieCount === 0) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Invalid cookie format. No valid cookies found.';
    } else {
        statusDiv.className = 'channel-status success';
        statusDiv.textContent = `Cookie format is valid! Found ${cookieCount} cookies. Save them to use with YouTube requests.`;
    }
    
    testBtn.disabled = false;
    testBtn.textContent = 'Test Cookies';
}

async function handleDeleteCookies() {
    if (!confirm('Are you sure you want to delete all stored cookies? This may cause YouTube bot detection errors.')) {
        return;
    }
    
    const statusDiv = document.getElementById('cookiesStatus');
    const deleteBtn = document.getElementById('deleteCookiesBtn');
    const cookiesInput = document.getElementById('youtubeCookiesInput');
    
    if (!statusDiv || !deleteBtn) {
        return;
    }
    
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Deleting cookies...';
    
    try {
        const response = await fetch('/api/admin/cookies', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = 'Cookies deleted successfully';
            if (cookiesInput) {
                cookiesInput.value = '';
            }
            await loadCookies(); // Refresh status
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to delete cookies';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Connection error: ' + error.message;
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.textContent = 'Delete Cookies';
    }
}

async function handleSaveWebhook() {
    const webhookUrlInput = document.getElementById('n8nWebhookUrlInput');
    const useWebhookCheckbox = document.getElementById('useWebhookCheckbox');
    const statusDiv = document.getElementById('webhookStatus');
    const saveBtn = document.getElementById('saveWebhookBtn');
    
    // If elements don't exist, return early
    if (!webhookUrlInput || !useWebhookCheckbox || !statusDiv || !saveBtn) {
        console.warn('Settings elements not found');
        return;
    }
    
    const webhookUrl = webhookUrlInput.value.trim();
    const useWebhook = useWebhookCheckbox.checked;
    
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        // Save webhook URL
        if (webhookUrl) {
            const urlResponse = await fetch('/api/admin/settings/n8n_webhook_url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({ value: webhookUrl })
            });
            
            if (!urlResponse.ok) {
                throw new Error('Failed to save webhook URL');
            }
        }
        
        // Save use webhook setting
        const enabledResponse = await fetch('/api/admin/settings/use_webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ value: useWebhook ? 'true' : 'false' })
        });
        
        if (!enabledResponse.ok) {
            throw new Error('Failed to save webhook setting');
        }
        
        statusDiv.className = 'channel-status success';
        statusDiv.textContent = 'Settings saved successfully!';
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Failed to save settings: ' + error.message;
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Webhook URL';
    }
}

async function handleTestWebhook() {
    const webhookUrlInput = document.getElementById('n8nWebhookUrlInput');
    const statusDiv = document.getElementById('webhookStatus');
    const testBtn = document.getElementById('testWebhookBtn');
    
    // If elements don't exist, return early
    if (!webhookUrlInput || !statusDiv || !testBtn) {
        console.warn('Settings elements not found');
        return;
    }
    
    const webhookUrl = webhookUrlInput.value.trim();
    
    if (!webhookUrl) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please enter a webhook URL first';
        return;
    }
    
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Testing webhook connection...';
    
    try {
        const response = await fetch(webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                test: true,
                message: 'Test webhook from YouTube Transcription Service',
                timestamp: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = 'Webhook test successful! Webhook is reachable.';
        } else {
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = `Webhook returned status ${response.status}. Check your n8n workflow.`;
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Webhook test failed: ' + error.message;
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = 'Test Webhook';
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

