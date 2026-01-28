let authToken = localStorage.getItem('authToken');
let currentUsername = localStorage.getItem('username');
let isProcessing = false;
let videosDataTable = null;

// Confirm modal state
let confirmModalResolve = null;

// Show confirm modal (replaces confirm())
function showConfirmModal(title, message) {
    return new Promise((resolve) => {
        document.getElementById('confirmModalTitle').textContent = title;
        document.getElementById('confirmModalMessage').textContent = message;
        const modal = document.getElementById('confirmModal');
        modal.classList.remove('hidden');
        confirmModalResolve = resolve;
    });
}

// Close confirm modal
function closeConfirmModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.add('hidden');
    if (confirmModalResolve) {
        confirmModalResolve(false);
        confirmModalResolve = null;
    }
}

// Show toast notification (replaces alert for success/info)
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Set processing state (disable/enable buttons)
function setProcessingState(processing) {
    isProcessing = processing;
    const buttons = document.querySelectorAll('#bulkGetDataBtn, #bulkTranscribeBtn, #bulkGenerateContentBtn, #bulkIgnoreBtn, #bulkUnignoreBtn, #selectAllVideos');
    buttons.forEach(btn => {
        if (btn) {
            btn.disabled = processing;
            if (processing) {
                btn.style.opacity = '0.6';
                btn.style.cursor = 'not-allowed';
            } else {
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            }
        }
    });
    
    // Disable checkboxes
    const checkboxes = document.querySelectorAll('.video-checkbox');
    checkboxes.forEach(cb => {
        if (cb) cb.disabled = processing;
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    if (authToken) {
        // Verify token is still valid before showing dashboard
        try {
            const response = await fetch('/api/admin/stats', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            if (response.ok) {
                showDashboard();
                loadData();
            } else if (response.status === 401) {
                // Token invalid, clear and show login
                authToken = null;
                currentUsername = null;
                localStorage.removeItem('authToken');
                localStorage.removeItem('username');
                showLogin();
            } else {
                showDashboard();
                loadData();
            }
        } catch (error) {
            // If check fails, still try to show dashboard (might be network issue)
            showDashboard();
            loadData();
        }
    } else {
        showLogin();
    }
    
    // Confirm modal event listeners
    document.getElementById('confirmModalOk').addEventListener('click', () => {
        const modal = document.getElementById('confirmModal');
        modal.classList.add('hidden');
        if (confirmModalResolve) {
            confirmModalResolve(true);
            confirmModalResolve = null;
        }
    });
    
    document.getElementById('confirmModalCancel').addEventListener('click', closeConfirmModal);
    
    // Close confirm modal when clicking outside
    document.getElementById('confirmModal').addEventListener('click', (e) => {
        if (e.target.id === 'confirmModal') {
            closeConfirmModal();
        }
    });
    
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('refreshBtn').addEventListener('click', loadData);
    document.getElementById('searchInput').addEventListener('input', filterVideos);
    document.getElementById('statusFilter').addEventListener('change', filterVideos);
    const channelFilter = document.getElementById('channelFilter');
    if (channelFilter) {
        channelFilter.addEventListener('change', filterVideos);
    }
    const showIgnoredCheckbox = document.getElementById('showIgnoredCheckbox');
    if (showIgnoredCheckbox) {
        showIgnoredCheckbox.addEventListener('change', loadData);
    }
    document.getElementById('submitChannelBtn').addEventListener('click', handleChannelSubmit);
    const addManualVideosBtn = document.getElementById('addManualVideosBtn');
    if (addManualVideosBtn) {
        addManualVideosBtn.addEventListener('click', handleAddManualVideos);
    }
    document.getElementById('createUserBtn').addEventListener('click', handleCreateUser);
    document.getElementById('refreshUsersBtn').addEventListener('click', loadUsers);
    
    // Transcripts tab
    const refreshTranscriptsBtn = document.getElementById('refreshTranscriptsBtn');
    const transcriptSearchInput = document.getElementById('transcriptSearchInput');
    const transcriptChannelFilter = document.getElementById('transcriptChannelFilter');
    if (refreshTranscriptsBtn) {
        refreshTranscriptsBtn.addEventListener('click', loadTranscripts);
    }
    if (transcriptSearchInput) {
        transcriptSearchInput.addEventListener('input', filterTranscripts);
    }
    if (transcriptChannelFilter) {
        transcriptChannelFilter.addEventListener('change', filterTranscripts);
    }
    
    // HTML extraction buttons
    const extractIdsBtn = document.getElementById('extractIdsBtn');
    const processExtractedIdsBtn = document.getElementById('processExtractedIdsBtn');
    const clearHtmlBtn = document.getElementById('clearHtmlBtn');
    if (extractIdsBtn) {
        extractIdsBtn.addEventListener('click', handleExtractIds);
    }
    if (processExtractedIdsBtn) {
        processExtractedIdsBtn.addEventListener('click', handleProcessExtractedIds);
    }
    if (clearHtmlBtn) {
        clearHtmlBtn.addEventListener('click', handleClearHtml);
    }
    
    // Proxy management buttons
    const saveProxyBtn = document.getElementById('saveProxyBtn');
    const testProxyBtn = document.getElementById('testProxyBtn');
    const deleteProxyBtn = document.getElementById('deleteProxyBtn');
    if (saveProxyBtn) {
        saveProxyBtn.addEventListener('click', handleSaveProxy);
    }
    if (testProxyBtn) {
        testProxyBtn.addEventListener('click', handleTestProxy);
    }
    if (deleteProxyBtn) {
        deleteProxyBtn.addEventListener('click', handleDeleteProxy);
    }
    
    // AI processing buttons
    const processAIBtn = document.getElementById('processAIBtn');
    const clearAIBtn = document.getElementById('clearAIBtn');
    const openaiTemperature = document.getElementById('openaiTemperature');
    const openaiPromptSelect = document.getElementById('openaiPromptSelect');
    const saveCustomPromptBtn = document.getElementById('saveCustomPromptBtn');
    const loadPromptBtn = document.getElementById('loadPromptBtn');
    if (processAIBtn) {
        processAIBtn.addEventListener('click', handleAIProcess);
    }
    if (clearAIBtn) {
        clearAIBtn.addEventListener('click', handleClearAI);
    }
    if (openaiTemperature) {
        openaiTemperature.addEventListener('input', (e) => {
            const tempValue = document.getElementById('tempValue');
            if (tempValue) {
                tempValue.textContent = e.target.value;
            }
        });
    }
    if (openaiPromptSelect) {
        openaiPromptSelect.addEventListener('change', handlePromptSelectChange);
    }
    if (saveCustomPromptBtn) {
        saveCustomPromptBtn.addEventListener('click', handleSaveCustomPrompt);
    }
    if (loadPromptBtn) {
        loadPromptBtn.addEventListener('click', handleLoadPrompt);
    }
    const openaiPrompt = document.getElementById('openaiPrompt');
    if (openaiPrompt) {
        openaiPrompt.addEventListener('input', () => {
            const promptSelect = document.getElementById('openaiPromptSelect');
            if (promptSelect && !promptSelect.value && openaiPrompt.value.trim()) {
                saveCustomPromptBtn.style.display = 'inline-block';
            } else {
                saveCustomPromptBtn.style.display = 'none';
            }
        });
    }
    
    // Bulk operation buttons
    const selectAllVideos = document.getElementById('selectAllVideos');
    const bulkGetDataBtn = document.getElementById('bulkGetDataBtn');
    const bulkTranscribeBtn = document.getElementById('bulkTranscribeBtn');
    const bulkGenerateContentBtn = document.getElementById('bulkGenerateContentBtn');
    const bulkIgnoreBtn = document.getElementById('bulkIgnoreBtn');
    const bulkUnignoreBtn = document.getElementById('bulkUnignoreBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    if (selectAllVideos) {
        selectAllVideos.addEventListener('change', handleSelectAllVideos);
    }
    if (bulkGetDataBtn) {
        bulkGetDataBtn.addEventListener('click', handleBulkGetData);
    }
    if (bulkTranscribeBtn) {
        bulkTranscribeBtn.addEventListener('click', handleBulkTranscribe);
    }
    if (bulkGenerateContentBtn) {
        bulkGenerateContentBtn.addEventListener('click', handleBulkGenerateContent);
    }
    if (bulkIgnoreBtn) {
        bulkIgnoreBtn.addEventListener('click', handleBulkIgnore);
    }
    if (bulkUnignoreBtn) {
        bulkUnignoreBtn.addEventListener('click', handleBulkUnignore);
    }
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', handleClearSelection);
    }
    
    // Prompts management
    const createPromptBtn = document.getElementById('createPromptBtn');
    const promptForm = document.getElementById('promptForm');
    const cancelPromptBtn = document.getElementById('cancelPromptBtn');
    if (createPromptBtn) {
        createPromptBtn.addEventListener('click', () => showPromptForm());
    }
    if (promptForm) {
        promptForm.addEventListener('submit', handleSavePrompt);
    }
    if (cancelPromptBtn) {
        cancelPromptBtn.addEventListener('click', () => hidePromptForm());
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
    const loginScreen = document.getElementById('loginScreen');
    const dashboard = document.getElementById('dashboard');
    
    if (loginScreen) {
        loginScreen.classList.add('hidden');
    }
    if (dashboard) {
        dashboard.classList.remove('hidden');
    }
    
    if (currentUsername) {
        const usernameDisplay = document.getElementById('usernameDisplay');
        if (usernameDisplay) {
            usernameDisplay.textContent = `Logged in as: ${currentUsername}`;
        }
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    const loginForm = document.getElementById('loginForm');
    
    // Disable form during login
    if (loginForm) {
        loginForm.querySelector('button[type="submit"]').disabled = true;
    }
    errorDiv.textContent = '';
    
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
            
            // Show dashboard first
            showDashboard();
            
            // Update URL to root (remove any query params)
            if (window.location.pathname !== '/' || window.location.search) {
                window.history.replaceState({}, '', '/');
            }
            
            // Load data in background (don't block dashboard display)
            try {
                await loadData();
            } catch (loadError) {
                console.error('Error loading initial data:', loadError);
                // Dashboard is already shown, just log the error
            }
            
            errorDiv.textContent = '';
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Login failed';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Connection error. Please try again.';
    } finally {
        // Re-enable form
        if (loginForm) {
            loginForm.querySelector('button[type="submit"]').disabled = false;
        }
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


let selectedVideoIds = new Set();

function displayVideos(videos) {
    const tbody = document.getElementById('videosTableBody');
    
    if (videos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="loading">No videos found</td></tr>';
        return;
    }
    
    tbody.innerHTML = videos.map(video => {
        const isSelected = selectedVideoIds.has(video.video_id);
        return `
        <tr ${video.ignored ? 'style="opacity: 0.6; background-color: #f5f5f5;"' : ''}>
            <td><input type="checkbox" class="video-checkbox" data-video-id="${video.video_id}" ${isSelected ? 'checked' : ''}></td>
            <td><a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank">${video.video_id}</a></td>
            <td title="${video.title ? escapeHtml(video.title) : ''}">${video.title ? escapeHtml(video.title) : '-'}</td>
            <td>${video.channel_name ? escapeHtml(video.channel_name) : '-'}</td>
            <td>${video.video_url ? `<a href="${video.video_url}" target="_blank" title="${video.video_url}">${video.video_url.length > 30 ? escapeHtml(video.video_url.substring(0, 30)) + '...' : escapeHtml(video.video_url)}</a>` : '-'}</td>
            <td><span class="status-badge status-${video.status}">${video.status}</span></td>
            <td>
                ${video.transcript 
                    ? `<span class="transcript-preview" onclick="showTranscript('${video.video_id}', \`${escapeHtml(video.transcript.substring(0, 100))}...\`)">${escapeHtml(video.transcript.substring(0, 50))}...</span>`
                    : '-'}
            </td>
            <td>
                <button onclick="showGeneratedContent('${video.video_id}', '${escapeHtml(video.title || video.video_id)}')" class="btn-secondary" style="font-size: 0.85rem;">
                    View Content
                </button>
            </td>
            <td class="error-preview">${video.error_message ? escapeHtml(video.error_message.substring(0, 50)) + (video.error_message.length > 50 ? '...' : '') : '-'}</td>
            <td>${formatDate(video.created_at)}</td>
            <td>${formatDate(video.updated_at)}</td>
            <td>
                ${video.transcript 
                    ? `<button onclick="showFullTranscript('${video.video_id}')" class="btn-secondary" style="font-size: 0.85rem; margin-right: 0.25rem;">View Full</button>`
                    : ''}
                ${video.ignored 
                    ? `<button onclick="toggleIgnoreVideo('${video.video_id}', false)" class="btn-secondary" style="font-size: 0.85rem; background: #28a745;">Unignore</button>`
                    : `<button onclick="toggleIgnoreVideo('${video.video_id}', true)" class="btn-secondary" style="font-size: 0.85rem; background: #dc3545;">Ignore</button>`}
            </td>
        </tr>
    `;
    }).join('');
    
    // Attach checkbox listeners
    tbody.querySelectorAll('.video-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleVideoCheckboxChange);
    });
    
    updateBulkActionsVisibility();
}

function handleVideoCheckboxChange(e) {
    const videoId = e.target.dataset.videoId;
    if (e.target.checked) {
        selectedVideoIds.add(videoId);
    } else {
        selectedVideoIds.delete(videoId);
    }
    updateBulkActionsVisibility();
    updateSelectAllCheckbox();
}

function handleSelectAllVideos(e) {
    const checkboxes = document.querySelectorAll('.video-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = e.target.checked;
        const videoId = cb.dataset.videoId;
        if (e.target.checked) {
            selectedVideoIds.add(videoId);
        } else {
            selectedVideoIds.delete(videoId);
        }
    });
    updateBulkActionsVisibility();
}

function updateSelectAllCheckbox() {
    const selectAll = document.getElementById('selectAllVideos');
    if (selectAll) {
        const checkboxes = document.querySelectorAll('.video-checkbox');
        const checkedCount = document.querySelectorAll('.video-checkbox:checked').length;
        selectAll.checked = checkboxes.length > 0 && checkedCount === checkboxes.length;
        selectAll.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    }
}

function updateBulkActionsVisibility() {
    const bulkActions = document.getElementById('bulkActionsVideos');
    const selectedCount = document.getElementById('selectedCountVideos');
    if (bulkActions && selectedCount) {
        // Get count from both Set and actual checked checkboxes
        const checkedBoxes = document.querySelectorAll('.video-checkbox:checked');
        const countFromCheckboxes = checkedBoxes.length;
        const countFromSet = selectedVideoIds.size;
        
        // Use the larger count (in case they're out of sync)
        const count = Math.max(countFromCheckboxes, countFromSet);
        
        if (count > 0) {
            bulkActions.style.display = 'block';
            selectedCount.textContent = count;
        } else {
            bulkActions.style.display = 'none';
        }
    }
}

function handleClearSelection() {
    selectedVideoIds.clear();
    document.querySelectorAll('.video-checkbox').forEach(cb => cb.checked = false);
    const selectAll = document.getElementById('selectAllVideos');
    if (selectAll) selectAll.checked = false;
    updateBulkActionsVisibility();
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
                const modal = document.getElementById('transcriptModal');
                const content = document.getElementById('transcriptContent');
                
                // Show video info in modal header
                const title = video.title || video.video_id;
                const channel = video.channel_name || 'Unknown Channel';
                const videoUrl = `https://www.youtube.com/watch?v=${video.video_id}`;
                
                content.innerHTML = `
                    <div style="margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #ddd;">
                        <h3 style="margin: 0 0 0.5rem 0;"><a href="${videoUrl}" target="_blank">${escapeHtml(title)}</a></h3>
                        <p style="margin: 0; color: #666;">Channel: ${escapeHtml(channel)}</p>
                        <p style="margin: 0; color: #666;">Video ID: <a href="${videoUrl}" target="_blank">${video.video_id}</a></p>
                    </div>
                    <div style="white-space: pre-wrap; line-height: 1.6;">${escapeHtml(video.transcript)}</div>
                `;
                modal.classList.remove('hidden');
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
    // Reload DataTable with new filters
    if (videosDataTable) {
        videosDataTable.ajax.reload();
    } else {
        initializeDataTable();
    }
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
        
        // Initialize or reload DataTable
        initializeDataTable();
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

function initializeDataTable() {
    const table = document.getElementById('videosTable');
    if (!table) return;
    
    // Destroy existing DataTable if it exists
    if (videosDataTable) {
        videosDataTable.destroy();
        videosDataTable = null;
    }
    
    // Get current filter values
    const showIgnored = document.getElementById('showIgnoredCheckbox')?.checked || false;
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const channelFilter = document.getElementById('channelFilter')?.value || '';
    const searchInput = document.getElementById('searchInput')?.value || '';
    
    // Initialize DataTable with server-side processing
    videosDataTable = new DataTable('#videosTable', {
        processing: true,
        serverSide: true,
        ajax: {
            url: '/api/videos',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            data: function(d) {
                // DataTables parameters
                d.show_ignored = showIgnored;
                d.status = statusFilter || null;
                d.channel = channelFilter || null;
                d.search = searchInput || null;
                d.limit = d.length;
                d.offset = d.start;
            },
            dataSrc: function(json) {
                // Update allVideos for checkbox handling
                allVideos = json.videos || [];
                
                // Populate channel filter with unique channel names (only on first load)
                if (!channelFilter) {
                    const channels = [...new Set(allVideos.map(v => v.channel_name).filter(Boolean))].sort();
                    const channelFilterEl = document.getElementById('channelFilter');
                    if (channelFilterEl && channelFilterEl.options.length <= 1) {
                        channels.forEach(ch => {
                            const option = document.createElement('option');
                            option.value = ch;
                            option.textContent = ch;
                            channelFilterEl.appendChild(option);
                        });
                    }
                }
                
                return json.videos || [];
            },
            error: function(xhr, error, thrown) {
                if (xhr.status === 401) {
                    handleLogout();
                } else {
                    console.error('DataTable error:', error);
                }
            }
        },
        columns: [
            {
                data: null,
                orderable: false,
                searchable: false,
                render: function(data, type, row) {
                    const isSelected = selectedVideoIds.has(row.video_id);
                    return `<input type="checkbox" class="video-checkbox" data-video-id="${row.video_id}" ${isSelected ? 'checked' : ''} ${isProcessing ? 'disabled' : ''} onchange="handleVideoCheckboxChange(event)">`;
                }
            },
            {
                data: 'video_id',
                render: function(data) {
                    return `<a href="https://www.youtube.com/watch?v=${data}" target="_blank">${data}</a>`;
                }
            },
            {
                data: 'title',
                render: function(data) {
                    return data ? escapeHtml(data) : '-';
                }
            },
            {
                data: 'channel_name',
                render: function(data) {
                    return data ? escapeHtml(data) : '-';
                }
            },
            {
                data: 'video_url',
                render: function(data) {
                    if (!data) return '-';
                    return `<a href="${data}" target="_blank" title="${data}">${data.length > 30 ? escapeHtml(data.substring(0, 30)) + '...' : escapeHtml(data)}</a>`;
                }
            },
            {
                data: 'status',
                render: function(data) {
                    return `<span class="status-badge status-${data}">${data}</span>`;
                }
            },
            {
                data: 'transcript',
                orderable: false,
                render: function(data, type, row) {
                    if (!data) return '-';
                    return `<span class="transcript-preview" onclick="showTranscript('${row.video_id}', \`${escapeHtml(data.substring(0, 100))}...\`)">${escapeHtml(data.substring(0, 50))}...</span>`;
                }
            },
            {
                data: null,
                orderable: false,
                searchable: false,
                render: function(data, type, row) {
                    return `<button onclick="showGeneratedContent('${row.video_id}', '${escapeHtml((row.title || row.video_id).replace(/'/g, "\\'"))}')" class="btn-secondary" style="font-size: 0.85rem;">View Content</button>`;
                }
            },
            {
                data: 'error_message',
                orderable: false,
                render: function(data) {
                    return data ? escapeHtml(data.substring(0, 50)) + (data.length > 50 ? '...' : '') : '-';
                }
            },
            {
                data: 'created_at',
                render: function(data) {
                    return formatDate(data);
                }
            },
            {
                data: 'updated_at',
                render: function(data) {
                    return formatDate(data);
                }
            },
            {
                data: null,
                orderable: false,
                searchable: false,
                render: function(data, type, row) {
                    let html = '<div style="display: flex; flex-direction: column; gap: 0.25rem;">';
                    
                    // Get Data button
                    html += `<button onclick="handleSingleGetData('${row.video_id}')" class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Get Data</button>`;
                    
                    // Transcribe button
                    html += `<button onclick="handleSingleTranscribe('${row.video_id}')" class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Transcribe</button>`;
                    
                    // Generate Content button
                    html += `<button onclick="handleSingleGenerateContent('${row.video_id}')" class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Generate Content</button>`;
                    
                    // View Full Transcript button (if transcript exists)
                    if (row.transcript) {
                        html += `<button onclick="showFullTranscript('${row.video_id}')" class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">View Transcript</button>`;
                    }
                    
                    // Ignore/Unignore button
                    if (row.ignored) {
                        html += `<button onclick="toggleIgnoreVideo('${row.video_id}', false)" class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem; background: #28a745;">Unignore</button>`;
                    } else {
                        html += `<button onclick="toggleIgnoreVideo('${row.video_id}', true)" class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem; background: #dc3545;">Ignore</button>`;
                    }
                    
                    html += '</div>';
                    return html;
                }
            }
        ],
        order: [[10, 'desc']], // Sort by updated_at descending
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        language: {
            processing: 'Loading videos...',
            search: 'Search:',
            lengthMenu: 'Show _MENU_ videos',
            info: 'Showing _START_ to _END_ of _TOTAL_ videos',
            infoEmpty: 'No videos found',
            infoFiltered: '(filtered from _MAX_ total videos)',
            zeroRecords: 'No matching videos found'
        }
    });
    
    // Attach checkbox listeners and sync state after table is drawn
    table.addEventListener('draw.dt', function() {
        // Sync checkbox states with selectedVideoIds Set
        document.querySelectorAll('.video-checkbox').forEach(checkbox => {
            const videoId = checkbox.dataset.videoId;
            checkbox.checked = selectedVideoIds.has(videoId);
            
            // Remove old listeners and add new one
            const newCheckbox = checkbox.cloneNode(true);
            checkbox.parentNode.replaceChild(newCheckbox, checkbox);
            newCheckbox.addEventListener('change', handleVideoCheckboxChange);
        });
        
        // Update select all checkbox
        updateSelectAllCheckbox();
        
        // Update bulk actions visibility
        updateBulkActionsVisibility();
    });
}

// Single video action handlers
async function handleSingleGetData(videoId) {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    try {
        const response = await fetch('/api/bulk/get-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ video_ids: [videoId] })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Retrieved data for video ${videoId}`, 'success');
            if (videosDataTable) {
                videosDataTable.ajax.reload();
            }
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error getting data', 'error');
        }
    } catch (error) {
        showToast('Error getting data: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        setProcessingState(false);
    }
}

async function handleSingleTranscribe(videoId) {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    const confirmed = await showConfirmModal('Transcribe Video', `Transcribe video ${videoId}? This may take a while.`);
    if (!confirmed) {
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    try {
        const response = await fetch('/api/bulk/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ video_ids: [videoId] })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Transcription started for video ${videoId}`, 'success');
            if (videosDataTable) {
                videosDataTable.ajax.reload();
            }
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error transcribing video', 'error');
        }
    } catch (error) {
        showToast('Error transcribing video: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        setProcessingState(false);
    }
}

async function handleSingleGenerateContent(videoId) {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    // Show prompt selection dialog
    const promptId = prompt('Enter prompt ID (or leave empty for custom prompt):');
    const customPrompt = prompt('Enter custom prompt (if not using saved prompt):');
    
    if (!promptId && !customPrompt) {
        showToast('Please provide either a prompt ID or custom prompt', 'info');
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    try {
        const response = await fetch('/api/bulk/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                video_ids: [videoId],
                prompt_id: promptId ? parseInt(promptId) : null,
                prompt: customPrompt || null
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Generated content for video ${videoId}`, 'success');
            if (videosDataTable) {
                videosDataTable.ajax.reload();
            }
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error generating content', 'error');
        }
    } catch (error) {
        showToast('Error generating content: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        setProcessingState(false);
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
        } else if (tabName === 'transcripts') {
            loadTranscripts();
        } else if (tabName === 'settings') {
            loadProxy();
            // Only load settings if the tab exists
            const settingsTab = document.getElementById('settingsTab');
            if (settingsTab) {
                loadSettings();
                loadProxy();
            }
        } else if (tabName === 'channel') {
            // Channel tab doesn't need to load data
        } else if (tabName === 'ai') {
            loadPrompts(); // Load prompts for AI tab dropdown
        } else if (tabName === 'prompts') {
            loadPrompts();
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
    const confirmed = await showConfirmModal('Delete User', `Are you sure you want to delete user '${username}'?`);
    if (!confirmed) {
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
            showToast(error.detail || 'Failed to delete user', 'error');
        }
    } catch (error) {
        showToast('Connection error. Please try again.', 'error');
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

// Proxy Management Functions
async function loadProxy() {
    try {
        const response = await fetch('/api/admin/settings/ytdlp_proxy', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const proxyInput = document.getElementById('ytdlpProxyInput');
        const proxyStatusText = document.getElementById('proxyStatusText');
        
        if (response.ok) {
            const data = await response.json();
            const proxy = data.value || '';
            
            if (proxyInput) {
                proxyInput.value = proxy;
            }
            
            if (proxyStatusText) {
                if (proxy) {
                    // Mask password in display
                    const maskedProxy = proxy.replace(/:([^:@]+)@/, ':****@');
                    proxyStatusText.textContent = `Proxy configured: ${maskedProxy}`;
                } else {
                    proxyStatusText.textContent = 'No proxy configured';
                }
            }
        } else if (response.status === 401) {
            handleLogout();
        }
    } catch (error) {
        console.error('Error loading proxy:', error);
        const proxyStatusText = document.getElementById('proxyStatusText');
        if (proxyStatusText) {
            proxyStatusText.textContent = 'Error loading proxy status';
        }
    }
}

async function handleSaveProxy() {
    const proxyInput = document.getElementById('ytdlpProxyInput');
    const statusDiv = document.getElementById('proxyStatus');
    const saveBtn = document.getElementById('saveProxyBtn');
    
    if (!proxyInput) return;
    
    const proxy = proxyInput.value.trim();
    
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Saving proxy configuration...';
    
    try {
        const response = await fetch('/api/admin/settings/ytdlp_proxy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ value: proxy })
        });
        
        if (response.ok) {
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = 'Proxy saved successfully!';
            await loadProxy(); // Refresh status
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to save proxy';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Error saving proxy: ' + error.message;
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Proxy';
    }
}

async function handleTestProxy() {
    const proxyInput = document.getElementById('ytdlpProxyInput');
    const statusDiv = document.getElementById('proxyStatus');
    const testBtn = document.getElementById('testProxyBtn');
    
    if (!proxyInput) return;
    
    const proxy = proxyInput.value.trim();
    
    if (!proxy) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please enter a proxy URL first';
        return;
    }
    
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Testing proxy connection...';
    
    try {
        const response = await fetch('/api/admin/test-proxy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ proxy: proxy })
        });
        
        if (response.ok) {
            const data = await response.json();
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = data.message || 'Proxy test successful!';
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Proxy test failed';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Error testing proxy: ' + error.message;
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = 'Test Proxy';
    }
}

async function handleDeleteProxy() {
    const statusDiv = document.getElementById('proxyStatus');
    const deleteBtn = document.getElementById('deleteProxyBtn');
    
    if (!await showConfirmModal('Delete Proxy', 'Are you sure you want to delete the proxy configuration?')) {
        return;
    }
    
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Deleting proxy configuration...';
    
    try {
        const response = await fetch('/api/admin/settings/ytdlp_proxy', {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = 'Proxy deleted successfully!';
            await loadProxy(); // Refresh status
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to delete proxy';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Error deleting proxy: ' + error.message;
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.textContent = 'Delete Proxy';
    }
}

// Transcripts Tab Functions
async function loadTranscripts() {
    try {
        const response = await fetch('/api/admin/videos', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const videos = await response.json();
            // Filter only processed videos with transcripts
            allTranscripts = videos.filter(v => 
                v.transcript && 
                (v.status === 'success' || v.status === 'processed')
            );
            
            // Populate channel filter
            const channels = [...new Set(allTranscripts.map(v => v.channel_name).filter(Boolean))].sort();
            const channelFilter = document.getElementById('transcriptChannelFilter');
            if (channelFilter) {
                const currentValue = channelFilter.value;
                channelFilter.innerHTML = '<option value="">All Channels</option>' + 
                    channels.map(ch => `<option value="${escapeHtml(ch)}">${escapeHtml(ch)}</option>`).join('');
                if (currentValue) {
                    channelFilter.value = currentValue;
                }
            }
            
            filterTranscripts();
        } else if (response.status === 401) {
            handleLogout();
        }
    } catch (error) {
        console.error('Error loading transcripts:', error);
        const tbody = document.getElementById('transcriptsTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="9" class="loading">Error loading transcripts</td></tr>';
        }
    }
}

function displayTranscripts(transcripts) {
    const tbody = document.getElementById('transcriptsTableBody');
    
    if (!tbody) return;
    
    if (transcripts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No transcripts found</td></tr>';
        return;
    }
    
    function formatDuration(seconds) {
        if (!seconds) return '-';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    function formatViews(viewCount) {
        if (!viewCount) return '-';
        if (viewCount >= 1000000) {
            return (viewCount / 1000000).toFixed(1) + 'M';
        } else if (viewCount >= 1000) {
            return (viewCount / 1000).toFixed(1) + 'K';
        }
        return viewCount.toString();
    }
    
    tbody.innerHTML = transcripts.map(video => `
        <tr>
            <td><a href="https://www.youtube.com/watch?v=${video.video_id}" target="_blank">${video.video_id}</a></td>
            <td>${video.title ? escapeHtml(video.title) : '-'}</td>
            <td>${video.channel_name ? escapeHtml(video.channel_name) : '-'}</td>
            <td>${formatDuration(video.duration)}</td>
            <td>${formatViews(video.view_count)}</td>
            <td>${video.upload_date ? formatDate(video.upload_date) : '-'}</td>
            <td>
                <span class="transcript-preview" onclick="showFullTranscript('${video.video_id}')" style="cursor: pointer; color: #2196F3;">
                    ${escapeHtml(video.transcript.substring(0, 80))}...
                </span>
            </td>
            <td>${formatDate(video.updated_at)}</td>
            <td>
                <button onclick="showFullTranscript('${video.video_id}')" class="btn-primary">View Full</button>
            </td>
        </tr>
    `).join('');
}

function filterTranscripts() {
    const searchTerm = (document.getElementById('transcriptSearchInput')?.value || '').toLowerCase();
    const channelFilter = (document.getElementById('transcriptChannelFilter')?.value || '').toLowerCase();
    
    const filtered = allTranscripts.filter(video => {
        const matchesSearch = !searchTerm || 
            video.video_id.toLowerCase().includes(searchTerm) ||
            (video.title && video.title.toLowerCase().includes(searchTerm)) ||
            (video.channel_name && video.channel_name.toLowerCase().includes(searchTerm)) ||
            (video.transcript && video.transcript.toLowerCase().includes(searchTerm));
        const matchesChannel = !channelFilter || 
            (video.channel_name && video.channel_name.toLowerCase() === channelFilter);
        return matchesSearch && matchesChannel;
    });
    
    displayTranscripts(filtered);
}

// Manual Video Addition Function
async function handleAddManualVideos() {
    const channelNameInput = document.getElementById('manualChannelName');
    const videoInput = document.getElementById('manualVideoInput');
    const statusDiv = document.getElementById('manualVideoStatus');
    const addBtn = document.getElementById('addManualVideosBtn');
    
    const channelName = channelNameInput.value.trim();
    const videoInputText = videoInput.value.trim();
    
    if (!channelName) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please enter a channel/author name';
        return;
    }
    
    if (!videoInputText) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please enter video IDs or URLs';
        return;
    }
    
    addBtn.disabled = true;
    addBtn.textContent = 'Adding Videos...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Processing videos...';
    
    try {
        const response = await fetch('/api/manual-add-videos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                channel_name: channelName,
                videos: videoInputText
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = `Successfully added ${data.stored} video(s) to database${data.skipped > 0 ? `, ${data.skipped} already existed` : ''}!`;
            
            // Clear inputs
            channelNameInput.value = '';
            videoInput.value = '';
            
            // Refresh video list
            loadData();
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to add videos';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Error adding videos: ' + error.message;
    } finally {
        addBtn.disabled = false;
        addBtn.textContent = 'Add Videos';
    }
}

// HTML Extraction Functions
let extractedVideoIds = [];

async function handleExtractIds() {
    const htmlInput = document.getElementById('htmlInput');
    const statusDiv = document.getElementById('extractionStatus');
    const extractBtn = document.getElementById('extractIdsBtn');
    const extractedIdsContainer = document.getElementById('extractedIdsContainer');
    const extractedIdsList = document.getElementById('extractedIdsList');
    const extractedCount = document.getElementById('extractedCount');
    const processBtn = document.getElementById('processExtractedIdsBtn');
    
    const html = htmlInput.value.trim();
    
    if (!html) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please paste HTML content first';
        return;
    }
    
    extractBtn.disabled = true;
    extractBtn.textContent = 'Extracting...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = 'Extracting video IDs from HTML...';
    
    try {
        const response = await fetch('/api/extract-video-ids', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ html: html })
        });
        
        if (response.ok) {
            const data = await response.json();
            extractedVideoIds = data.video_ids;
            
            if (extractedVideoIds.length === 0) {
                statusDiv.className = 'channel-status error';
                statusDiv.textContent = 'No video IDs found in the HTML. Make sure you copied the full page source.';
                extractedIdsContainer.style.display = 'none';
                processBtn.style.display = 'none';
            } else {
                const stored = data.stored || 0;
                const skipped = data.skipped || 0;
                
                statusDiv.className = 'channel-status success';
                if (stored > 0) {
                    statusDiv.textContent = `Successfully extracted ${extractedVideoIds.length} unique video ID(s)! ${stored} new video(s) stored in database${skipped > 0 ? `, ${skipped} already existed` : ''}.`;
                } else {
                    statusDiv.textContent = `Extracted ${extractedVideoIds.length} unique video ID(s), but all already exist in database.`;
                }
                
                // Display extracted IDs
                extractedCount.textContent = extractedVideoIds.length;
                extractedIdsList.textContent = extractedVideoIds.join(', ');
                extractedIdsContainer.style.display = 'block';
                processBtn.style.display = 'inline-block';
                
                // Refresh video list if new videos were stored
                if (stored > 0) {
                    loadData();
                }
            }
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to extract video IDs';
            extractedIdsContainer.style.display = 'none';
            processBtn.style.display = 'none';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Error extracting video IDs: ' + error.message;
        extractedIdsContainer.style.display = 'none';
        processBtn.style.display = 'none';
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Extract Video IDs';
    }
}

async function handleProcessExtractedIds() {
    if (extractedVideoIds.length === 0) {
        const statusDiv = document.getElementById('extractionStatus');
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'No video IDs to process. Please extract IDs first.';
        return;
    }
    
    const statusDiv = document.getElementById('extractionStatus');
    const processBtn = document.getElementById('processExtractedIdsBtn');
    
    processBtn.disabled = true;
    processBtn.textContent = 'Processing...';
    statusDiv.className = 'channel-status info';
    statusDiv.textContent = `Processing ${extractedVideoIds.length} video(s)...`;
    
    try {
        // Convert video IDs to full URLs for the API
        const videoUrls = extractedVideoIds.map(id => `https://www.youtube.com/watch?v=${id}`);
        
        const response = await fetch('/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                videos: videoUrls
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const successCount = data.results ? data.results.filter(r => r.status === 'success').length : 0;
            const errorCount = data.errors ? data.errors.length : 0;
            
            statusDiv.className = 'channel-status success';
            statusDiv.textContent = `Processing started! ${successCount} successful, ${errorCount} errors. Check the Videos tab for progress.`;
            
            // Refresh the videos list
            setTimeout(() => {
                loadData();
            }, 2000);
        } else {
            const error = await response.json();
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = error.detail || 'Failed to process videos';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Error processing videos: ' + error.message;
    } finally {
        processBtn.disabled = false;
        processBtn.textContent = 'Process Extracted Videos';
    }
}

function handleClearHtml() {
    document.getElementById('htmlInput').value = '';
    document.getElementById('extractionStatus').textContent = '';
    document.getElementById('extractionStatus').className = 'channel-status';
    document.getElementById('extractedIdsContainer').style.display = 'none';
    document.getElementById('processExtractedIdsBtn').style.display = 'none';
    extractedVideoIds = [];
}

// Note: Auto-refresh of the videos table has been disabled to avoid unexpected reloads
// If you want manual refresh, use the Refresh button in the UI which calls loadData() explicitly.

async function handleAIProcess() {
    const promptInput = document.getElementById('openaiPrompt');
    const promptSelect = document.getElementById('openaiPromptSelect');
    const modelSelect = document.getElementById('openaiModel');
    const temperatureInput = document.getElementById('openaiTemperature');
    const maxTokensInput = document.getElementById('openaiMaxTokens');
    const apiKeyInput = document.getElementById('openaiApiKey');
    const statusDiv = document.getElementById('aiStatus');
    const responseContainer = document.getElementById('aiResponseContainer');
    const responseDiv = document.getElementById('aiResponse');
    const usageDiv = document.getElementById('aiUsage');
    const usageDetails = document.getElementById('aiUsageDetails');
    const processBtn = document.getElementById('processAIBtn');
    
    const promptId = promptSelect ? promptSelect.value : null;
    const customPrompt = promptInput ? promptInput.value.trim() : '';
    
    if (!promptId && !customPrompt) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Please select a saved prompt or enter a custom prompt';
        return;
    }
    
    const model = modelSelect ? modelSelect.value : 'gpt-3.5-turbo';
    const temperature = temperatureInput ? parseFloat(temperatureInput.value) : 0.7;
    const maxTokens = maxTokensInput ? parseInt(maxTokensInput.value) : 1000;
    const apiKey = apiKeyInput ? apiKeyInput.value.trim() : null;
    
    processBtn.disabled = true;
    processBtn.textContent = 'Processing...';
    statusDiv.className = 'channel-status';
    statusDiv.textContent = 'Processing with AI...';
    responseContainer.style.display = 'none';
    usageDiv.style.display = 'none';
    
    try {
        const requestBody = {
            model: model,
            temperature: temperature,
            max_tokens: maxTokens
        };
        
        if (promptId) {
            requestBody.prompt_id = parseInt(promptId);
        } else {
            requestBody.prompt = customPrompt;
        }
        
        if (apiKey) {
            requestBody.openai_api_key = apiKey;
        }
        
        const response = await fetch('/api/ai/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.error) {
                statusDiv.className = 'channel-status error';
                statusDiv.textContent = `Error: ${data.error}`;
            } else {
                statusDiv.className = 'channel-status success';
                statusDiv.textContent = 'AI processing completed successfully';
                
                // Display response
                responseDiv.textContent = data.response || 'No response generated';
                responseContainer.style.display = 'block';
                
                // Display usage if available
                if (data.usage) {
                    usageDetails.innerHTML = `
                        <div><strong>Prompt Tokens:</strong> ${data.usage.prompt_tokens || 'N/A'}</div>
                        <div><strong>Completion Tokens:</strong> ${data.usage.completion_tokens || 'N/A'}</div>
                        <div><strong>Total Tokens:</strong> ${data.usage.total_tokens || 'N/A'}</div>
                    `;
                    usageDiv.style.display = 'block';
                }
                
                // Show save button if custom prompt was used
                if (!promptId && customPrompt) {
                    const saveBtn = document.getElementById('saveCustomPromptBtn');
                    if (saveBtn) saveBtn.style.display = 'inline-block';
                }
            }
        } else {
            statusDiv.className = 'channel-status error';
            statusDiv.textContent = data.detail || 'Failed to process with AI';
        }
    } catch (error) {
        statusDiv.className = 'channel-status error';
        statusDiv.textContent = 'Error processing with AI: ' + error.message;
    } finally {
        processBtn.disabled = false;
        processBtn.textContent = 'Process with AI';
    }
}

function handleClearAI() {
    const promptInput = document.getElementById('openaiPrompt');
    const modelSelect = document.getElementById('openaiModel');
    const temperatureInput = document.getElementById('openaiTemperature');
    const maxTokensInput = document.getElementById('openaiMaxTokens');
    const apiKeyInput = document.getElementById('openaiApiKey');
    const tempValue = document.getElementById('tempValue');
    
    if (promptInput) promptInput.value = '';
    if (modelSelect) modelSelect.value = 'gpt-3.5-turbo';
    if (temperatureInput) temperatureInput.value = '0.7';
    if (tempValue) tempValue.textContent = '0.7';
    if (maxTokensInput) maxTokensInput.value = '1000';
    if (apiKeyInput) apiKeyInput.value = '';
    
    const statusDiv = document.getElementById('aiStatus');
    const responseContainer = document.getElementById('aiResponseContainer');
    const usageDiv = document.getElementById('aiUsage');
    
    if (statusDiv) {
        statusDiv.textContent = '';
        statusDiv.className = 'channel-status';
    }
    if (responseContainer) responseContainer.style.display = 'none';
    if (usageDiv) usageDiv.style.display = 'none';
}

// Bulk Operations
async function handleBulkGetData() {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    const videoIds = Array.from(selectedVideoIds);
    if (videoIds.length === 0) {
        showToast('Please select at least one video', 'info');
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    const btn = document.getElementById('bulkGetDataBtn');
    const originalText = btn ? btn.textContent : 'Get Data';
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Processing...';
    }
    
    try {
        const response = await fetch('/api/bulk/get-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ video_ids: videoIds })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Retrieved data for ${data.results.length} video(s)`, 'success');
            await loadData(); // Refresh table
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error getting data', 'error');
        }
    } catch (error) {
        showToast('Error getting data: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        setProcessingState(false);
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

async function handleBulkTranscribe() {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    // Get selected video IDs from both Set and actual checked checkboxes
    const checkedBoxes = document.querySelectorAll('.video-checkbox:checked');
    const videoIdsFromCheckboxes = Array.from(checkedBoxes).map(cb => cb.dataset.videoId);
    const videoIdsFromSet = Array.from(selectedVideoIds);
    
    // Use checkboxes as source of truth, but also sync the Set
    const videoIds = videoIdsFromCheckboxes.length > 0 ? videoIdsFromCheckboxes : videoIdsFromSet;
    
    // Sync Set with checkboxes
    selectedVideoIds.clear();
    videoIds.forEach(id => selectedVideoIds.add(id));
    
    if (videoIds.length === 0) {
        showToast('Please select at least one video', 'info');
        return;
    }
    
    const confirmed = await showConfirmModal('Transcribe Videos', `Transcribe ${videoIds.length} video(s)? This may take a while.`);
    if (!confirmed) {
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    const btn = document.getElementById('bulkTranscribeBtn');
    const originalText = btn ? btn.textContent : 'Transcribe';
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Processing...';
    }
    
    try {
        const response = await fetch('/api/bulk/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ video_ids: videoIds })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Transcription started for ${videoIds.length} video(s)`, 'success');
            await loadData(); // Refresh table
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error transcribing videos', 'error');
        }
    } catch (error) {
        showToast('Error transcribing videos: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        setProcessingState(false);
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

async function handleBulkGenerateContent() {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    // Get selected video IDs from both Set and actual checked checkboxes
    const checkedBoxes = document.querySelectorAll('.video-checkbox:checked');
    const videoIdsFromCheckboxes = Array.from(checkedBoxes).map(cb => cb.dataset.videoId);
    const videoIdsFromSet = Array.from(selectedVideoIds);
    
    // Use checkboxes as source of truth, but also sync the Set
    const videoIds = videoIdsFromCheckboxes.length > 0 ? videoIdsFromCheckboxes : videoIdsFromSet;
    
    // Sync Set with checkboxes
    selectedVideoIds.clear();
    videoIds.forEach(id => selectedVideoIds.add(id));
    
    if (videoIds.length === 0) {
        showToast('Please select at least one video', 'info');
        return;
    }
    
    // Show prompt selection dialog
    const promptId = prompt('Enter prompt ID (or leave empty for custom prompt):');
    const customPrompt = prompt('Enter custom prompt (if not using saved prompt):');
    
    if (!promptId && !customPrompt) {
        showToast('Please provide either a prompt ID or custom prompt', 'info');
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    const btn = document.getElementById('bulkGenerateContentBtn');
    const originalText = btn ? btn.textContent : 'Generate Content';
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Processing...';
    }
    
    try {
        const response = await fetch('/api/bulk/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                video_ids: videoIds,
                prompt_id: promptId ? parseInt(promptId) : null,
                prompt: customPrompt || null
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`Generated content for ${data.results.length} video(s)`, 'success');
            await loadData(); // Refresh table
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error generating content', 'error');
        }
    } catch (error) {
        showToast('Error generating content: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        setProcessingState(false);
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

// Prompts Management
let allPrompts = [];

async function loadPrompts() {
    try {
        const response = await fetch('/api/prompts', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            allPrompts = await response.json();
            displayPrompts();
            updatePromptSelect();
        }
    } catch (error) {
        console.error('Error loading prompts:', error);
    }
}

function displayPrompts() {
    const container = document.getElementById('promptsList');
    if (!container) return;
    
    if (allPrompts.length === 0) {
        container.innerHTML = '<p style="color: #666;">No prompts found. Create your first prompt above.</p>';
        return;
    }
    
    container.innerHTML = allPrompts.map(prompt => `
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 1rem; margin-bottom: 1rem; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <div>
                    <h4 style="margin: 0 0 0.25rem 0;">${escapeHtml(prompt.name)}</h4>
                    ${prompt.description ? `<p style="margin: 0; color: #666; font-size: 0.9rem;">${escapeHtml(prompt.description)}</p>` : ''}
                    ${prompt.operation_type ? `<span style="display: inline-block; margin-top: 0.5rem; padding: 0.25rem 0.5rem; background: #e3f2fd; color: #1976d2; border-radius: 3px; font-size: 0.85rem;">${escapeHtml(prompt.operation_type)}</span>` : ''}
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <button onclick="editPrompt(${prompt.id})" class="btn-secondary" style="font-size: 0.85rem;">Edit</button>
                    <button onclick="deletePrompt(${prompt.id})" class="btn-secondary" style="font-size: 0.85rem; background: #dc3545;">Delete</button>
                </div>
            </div>
            ${prompt.system_prompt ? `<div style="margin-top: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 3px; font-size: 0.85rem;"><strong>System:</strong> ${escapeHtml(prompt.system_prompt.substring(0, 100))}${prompt.system_prompt.length > 100 ? '...' : ''}</div>` : ''}
            ${prompt.user_prompt_template ? `<div style="margin-top: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 3px; font-size: 0.85rem;"><strong>User Template:</strong> ${escapeHtml(prompt.user_prompt_template.substring(0, 100))}${prompt.user_prompt_template.length > 100 ? '...' : ''}</div>` : ''}
        </div>
    `).join('');
}

function updatePromptSelect() {
    const select = document.getElementById('openaiPromptSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">-- Use Custom Prompt --</option>' +
        allPrompts.map(p => `<option value="${p.id}">${escapeHtml(p.name)}${p.operation_type ? ` (${p.operation_type})` : ''}</option>`).join('');
}

function showPromptForm(promptId = null) {
    const formContainer = document.getElementById('promptFormContainer');
    const formTitle = document.getElementById('promptFormTitle');
    const form = document.getElementById('promptForm');
    
    if (formContainer) {
        formContainer.style.display = 'block';
        if (promptId) {
            const prompt = allPrompts.find(p => p.id === promptId);
            if (prompt) {
                formTitle.textContent = 'Edit Prompt';
                document.getElementById('promptId').value = prompt.id;
                document.getElementById('promptName').value = prompt.name || '';
                document.getElementById('promptDescription').value = prompt.description || '';
                document.getElementById('promptOperationType').value = prompt.operation_type || '';
                document.getElementById('promptSystemPrompt').value = prompt.system_prompt || '';
                document.getElementById('promptUserTemplate').value = prompt.user_prompt_template || '';
            }
        } else {
            formTitle.textContent = 'Create Prompt';
            form.reset();
            document.getElementById('promptId').value = '';
        }
        formContainer.scrollIntoView({ behavior: 'smooth' });
    }
}

function hidePromptForm() {
    const formContainer = document.getElementById('promptFormContainer');
    if (formContainer) {
        formContainer.style.display = 'none';
        document.getElementById('promptForm').reset();
        document.getElementById('promptId').value = '';
    }
}

async function handleSavePrompt(e) {
    e.preventDefault();
    const promptId = document.getElementById('promptId').value;
    const name = document.getElementById('promptName').value.trim();
    const description = document.getElementById('promptDescription').value.trim();
    const operationType = document.getElementById('promptOperationType').value;
    const systemPrompt = document.getElementById('promptSystemPrompt').value.trim();
    const userTemplate = document.getElementById('promptUserTemplate').value.trim();
    
    if (!name) {
        showToast('Name is required', 'info');
        return;
    }
    
    try {
        const url = promptId ? `/api/prompts/${promptId}` : '/api/prompts';
        const method = promptId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                name,
                description: description || null,
                system_prompt: systemPrompt || null,
                user_prompt_template: userTemplate || null,
                operation_type: operationType || null
            })
        });
        
        if (response.ok) {
            hidePromptForm();
            loadPrompts();
            showToast('Prompt saved successfully', 'success');
        } else {
            const error = await response.json();
            showToast('Error saving prompt: ' + (error.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('Error saving prompt: ' + error.message, 'error');
    }
}

async function deletePrompt(promptId) {
    const confirmed = await showConfirmModal('Delete Prompt', 'Are you sure you want to delete this prompt?');
    if (!confirmed) {
        return;
    }
    
    try {
        const response = await fetch(`/api/prompts/${promptId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            loadPrompts();
        } else {
            showToast('Error deleting prompt', 'error');
        }
    } catch (error) {
        showToast('Error deleting prompt: ' + error.message, 'error');
    }
}

function editPrompt(promptId) {
    showPromptForm(promptId);
}

// Generated Content Functions
async function showGeneratedContent(videoId, videoTitle) {
    try {
        const response = await fetch(`/api/videos/${videoId}/generated-content`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const contents = await response.json();
            displayGeneratedContent(videoId, videoTitle, contents);
        } else if (response.status === 401) {
            handleLogout();
        } else {
            showToast('Error loading generated content', 'error');
        }
    } catch (error) {
        console.error('Error loading generated content:', error);
        showToast('Error loading generated content: ' + error.message, 'error');
    }
}

function displayGeneratedContent(videoId, videoTitle, contents) {
    const modal = document.getElementById('generatedContentModal');
    const header = document.getElementById('generatedContentHeader');
    const list = document.getElementById('generatedContentList');
    
    document.getElementById('gcVideoId').textContent = videoId;
    document.getElementById('gcVideoTitle').textContent = videoTitle || videoId;
    
    if (contents.length === 0) {
        list.innerHTML = '<p style="color: #666; padding: 2rem; text-align: center;">No generated content found for this video.</p>';
    } else {
        list.innerHTML = contents.map((content, index) => `
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 1rem; margin-bottom: 1rem; background: white;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                    <div>
                        <h4 style="margin: 0 0 0.25rem 0;">Content #${contents.length - index}</h4>
                        <div style="font-size: 0.85rem; color: #666;">
                            ${content.model ? `<span>Model: ${escapeHtml(content.model)}</span>` : ''}
                            ${content.temperature !== null ? `<span style="margin-left: 1rem;">Temp: ${content.temperature}</span>` : ''}
                            ${content.max_tokens ? `<span style="margin-left: 1rem;">Max Tokens: ${content.max_tokens}</span>` : ''}
                        </div>
                        ${content.prompt_text ? `<div style="margin-top: 0.5rem; font-size: 0.85rem; color: #666;"><strong>Prompt:</strong> ${escapeHtml(content.prompt_text.substring(0, 100))}${content.prompt_text.length > 100 ? '...' : ''}</div>` : ''}
                        ${content.created_at ? `<div style="margin-top: 0.25rem; font-size: 0.85rem; color: #666;">Created: ${formatDate(content.created_at)}</div>` : ''}
                    </div>
                    <button onclick="deleteGeneratedContent(${content.id}, '${videoId}')" class="btn-secondary" style="font-size: 0.85rem; background: #dc3545; padding: 0.25rem 0.5rem;">Delete</button>
                </div>
                <div style="padding: 0.75rem; background: #f8f9fa; border-radius: 3px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; font-size: 0.9rem; line-height: 1.6;">
                    ${escapeHtml(content.generated_text)}
                </div>
                ${content.usage_info ? `
                    <div style="margin-top: 0.75rem; padding: 0.5rem; background: #e7f3ff; border-left: 4px solid #2196F3; border-radius: 3px; font-size: 0.85rem;">
                        <strong>Usage:</strong>
                        <div>Prompt Tokens: ${content.usage_info.prompt_tokens || 'N/A'}</div>
                        <div>Completion Tokens: ${content.usage_info.completion_tokens || 'N/A'}</div>
                        <div>Total Tokens: ${content.usage_info.total_tokens || 'N/A'}</div>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    modal.classList.remove('hidden');
}

function closeGeneratedContentModal() {
    const modal = document.getElementById('generatedContentModal');
    modal.classList.add('hidden');
}

async function deleteGeneratedContent(contentId, videoId) {
    const confirmed = await showConfirmModal('Delete Generated Content', 'Are you sure you want to delete this generated content?');
    if (!confirmed) {
        return;
    }
    
    try {
        const response = await fetch(`/api/generated-content/${contentId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Reload the content list
            const videoTitle = document.getElementById('gcVideoTitle').textContent;
            showGeneratedContent(videoId, videoTitle);
        } else {
            showToast('Error deleting generated content', 'error');
        }
    } catch (error) {
        console.error('Error deleting generated content:', error);
        showToast('Error deleting generated content: ' + error.message, 'error');
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('generatedContentModal');
    if (e.target === modal) {
        closeGeneratedContentModal();
    }
});

// Ignore video functions
async function toggleIgnoreVideo(videoId, ignored) {
    try {
        const response = await fetch(`/api/videos/${videoId}/ignore?ignored=${ignored}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const result = await response.json();
            loadData(); // Reload videos
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.detail || 'Failed to update video'), 'error');
        }
    } catch (error) {
        console.error('Error toggling ignore status:', error);
        showToast('Error: ' + error.message, 'error');
    }
}

async function handleBulkIgnore() {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    // Get selected video IDs from both Set and actual checked checkboxes
    const checkedBoxes = document.querySelectorAll('.video-checkbox:checked');
    const videoIdsFromCheckboxes = Array.from(checkedBoxes).map(cb => cb.dataset.videoId);
    const videoIdsFromSet = Array.from(selectedVideoIds);
    
    // Use checkboxes as source of truth, but also sync the Set
    const videoIds = videoIdsFromCheckboxes.length > 0 ? videoIdsFromCheckboxes : videoIdsFromSet;
    
    // Sync Set with checkboxes
    selectedVideoIds.clear();
    videoIds.forEach(id => selectedVideoIds.add(id));
    
    if (videoIds.length === 0) {
        showToast('Please select videos to ignore', 'info');
        return;
    }
    
    const confirmed = await showConfirmModal('Ignore Videos', `Ignore ${videoIds.length} video(s)?`);
    if (!confirmed) {
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    const btn = document.getElementById('bulkIgnoreBtn');
    const originalText = btn ? btn.textContent : 'Ignore Selected';
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Processing...';
    }
    
    try {
        const response = await fetch('/api/videos/bulk-ignore', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_ids: videoIds,
                ignored: true
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(`Ignored ${result.count || videoIds.length} video(s)`, 'success');
            selectedVideoIds.clear();
            await loadData();
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.detail || 'Failed to ignore videos'), 'error');
        }
    } catch (error) {
        console.error('Error ignoring videos:', error);
        showToast('Error: ' + error.message, 'error');
    }
}

async function handleBulkUnignore() {
    if (isProcessing) {
        showToast('Another operation is in progress. Please wait...', 'info');
        return;
    }
    
    // Get selected video IDs from both Set and actual checked checkboxes
    const checkedBoxes = document.querySelectorAll('.video-checkbox:checked');
    const videoIdsFromCheckboxes = Array.from(checkedBoxes).map(cb => cb.dataset.videoId);
    const videoIdsFromSet = Array.from(selectedVideoIds);
    
    // Use checkboxes as source of truth, but also sync the Set
    const videoIds = videoIdsFromCheckboxes.length > 0 ? videoIdsFromCheckboxes : videoIdsFromSet;
    
    // Sync Set with checkboxes
    selectedVideoIds.clear();
    videoIds.forEach(id => selectedVideoIds.add(id));
    
    if (videoIds.length === 0) {
        showToast('Please select videos to unignore', 'info');
        return;
    }
    
    const confirmed = await showConfirmModal('Unignore Videos', `Unignore ${videoIds.length} video(s)?`);
    if (!confirmed) {
        return;
    }
    
    isProcessing = true;
    setProcessingState(true);
    
    const btn = document.getElementById('bulkUnignoreBtn');
    const originalText = btn ? btn.textContent : 'Unignore Selected';
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Processing...';
    }
    
    try {
        const response = await fetch('/api/videos/bulk-ignore', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_ids: videoIds,
                ignored: false
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(`Unignored ${result.count || videoIds.length} video(s)`, 'success');
            selectedVideoIds.clear();
            await loadData();
        } else if (response.status === 401) {
            handleLogout();
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.detail || 'Failed to unignore videos'), 'error');
        }
    } catch (error) {
        console.error('Error unignoring videos:', error);
        showToast('Error: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        setProcessingState(false);
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

function handlePromptSelectChange(e) {
    const promptId = e.target.value;
    const customPromptTextarea = document.getElementById('openaiPrompt');
    const saveCustomPromptBtn = document.getElementById('saveCustomPromptBtn');
    
    if (promptId) {
        const prompt = allPrompts.find(p => p.id == promptId);
        if (prompt) {
            // Show that a saved prompt is selected
            customPromptTextarea.placeholder = `Using saved prompt: ${prompt.name}. Enter custom prompt below to override.`;
            saveCustomPromptBtn.style.display = 'none';
        }
    } else {
        customPromptTextarea.placeholder = 'Enter your prompt here, or select a saved prompt above...';
        if (customPromptTextarea.value.trim()) {
            saveCustomPromptBtn.style.display = 'inline-block';
        }
    }
}

function handleLoadPrompt() {
    const select = document.getElementById('openaiPromptSelect');
    if (!select || !select.value) {
        showToast('Please select a prompt first', 'info');
        return;
    }
    
    const prompt = allPrompts.find(p => p.id == select.value);
    if (prompt) {
        // Combine system and user prompts for display
        let combined = '';
        if (prompt.system_prompt) {
            combined += prompt.system_prompt + '\n\n';
        }
        if (prompt.user_prompt_template) {
            combined += prompt.user_prompt_template;
        }
        document.getElementById('openaiPrompt').value = combined;
    }
}

function handleSaveCustomPrompt() {
    const customPrompt = document.getElementById('openaiPrompt').value.trim();
    if (!customPrompt) {
        showToast('Please enter a prompt first', 'info');
        return;
    }
    
    // Use a simple prompt for name input (can be enhanced later with modal)
    const name = prompt('Enter a name for this prompt:');
    if (!name) return;
    
    showPromptForm();
    document.getElementById('promptName').value = name;
    document.getElementById('promptUserTemplate').value = customPrompt;
}

