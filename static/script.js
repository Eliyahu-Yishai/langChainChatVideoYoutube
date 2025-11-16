// DOM Elements
const videoSection = document.getElementById('videoSection');
const chatSection = document.getElementById('chatSection');
const videoInputsContainer = document.getElementById('videoInputsContainer');
const addInputBtn = document.getElementById('addInputBtn');
const loadVideoBtn = document.getElementById('loadVideoBtn');
const videoStatus = document.getElementById('videoStatus');
const chatContainer = document.getElementById('chatContainer');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const changeVideoBtn = document.getElementById('changeVideoBtn');
const loadedVideosList = document.getElementById('loadedVideosList');
const addVideoInput = document.getElementById('addVideoInput');
const addVideoBtn = document.getElementById('addVideoBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const toggleManageBtn = document.getElementById('toggleManageBtn');
const manageControls = document.getElementById('manageControls');
const videoCountText = document.getElementById('videoCountText');

let currentVideoIds = [];
let inputCounter = 0;
let isManagementExpanded = false;

// Event Listeners
loadVideoBtn.addEventListener('click', loadVideo);
sendBtn.addEventListener('click', sendQuestion);
changeVideoBtn.addEventListener('click', changeVideo);
addInputBtn.addEventListener('click', addVideoInputField);
addVideoBtn.addEventListener('click', addVideoToSession);
toggleManageBtn.addEventListener('click', toggleVideoManagement);

questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendQuestion();
});

addVideoInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addVideoToSession();
});

// Initialize with one input field for the initial video load section
(function initializeVideoInputs() {
    addVideoInputField();
})();

// Add Video Input Field Function (for initial load screen)
function addVideoInputField() {
    const inputGroup = document.createElement('div');
    inputGroup.className = 'video-input-group';
    inputGroup.dataset.inputId = inputCounter++;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'video-input';
    input.placeholder = 'Paste YouTube URL here (e.g., https://www.youtube.com/watch?v=...)';

    // Allow Enter key to load videos
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadVideo();
    });

    inputGroup.appendChild(input);

    // Add remove button if there's already at least one input
    const existingInputs = videoInputsContainer.querySelectorAll('.video-input-group');
    if (existingInputs.length > 0) {
        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn-remove';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = () => removeVideoInput(inputGroup);
        inputGroup.appendChild(removeBtn);
    }

    videoInputsContainer.appendChild(inputGroup);
    input.focus();
}

// Remove Video Input Function
function removeVideoInput(inputGroup) {
    inputGroup.remove();

    // If no inputs left, add one
    const remainingInputs = videoInputsContainer.querySelectorAll('.video-input-group');
    if (remainingInputs.length === 0) {
        addVideoInput();
    }
}

// Load Video Function
async function loadVideo() {
    // Collect all input values
    const inputs = videoInputsContainer.querySelectorAll('.video-input');
    const urls = Array.from(inputs)
        .map(input => input.value.trim())
        .filter(url => url.length > 0);

    if (urls.length === 0) {
        showStatus('Please enter at least one YouTube URL', 'error');
        return;
    }

    // Show loading overlay
    loadingOverlay.style.display = 'flex';
    loadVideoBtn.disabled = true;

    try {
        const response = await fetch('/process-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to process videos');
        }

        // Success
        currentVideoIds = data.video_ids || [];

        // Update the loaded videos list
        updateLoadedVideosList();

        // Show warnings for failed videos if any
        if (data.failed_videos && data.failed_videos.length > 0) {
            const failedInfo = data.failed_videos
                .map(v => `${v.video_id}: ${v.error}`)
                .join('; ');
            console.warn('Some videos failed:', failedInfo);
        }

        // Hide video section, show chat section
        videoSection.style.display = 'none';
        chatSection.style.display = 'block';

        // Clear previous chat
        const welcomeMsg = currentVideoIds.length === 1
            ? 'Video loaded! Ask me anything about this video.'
            : 'Videos loaded! Ask me anything about these videos.';
        chatContainer.innerHTML = `<div class="welcome-message">${welcomeMsg}</div>`;

        const successMsg = data.failed_videos && data.failed_videos.length > 0
            ? `${currentVideoIds.length} video(s) processed successfully, ${data.failed_videos.length} failed`
            : `${currentVideoIds.length} video(s) processed successfully!`;
        showStatus(successMsg, 'success');

    } catch (error) {
        showStatus(error.message, 'error');
    } finally {
        loadingOverlay.style.display = 'none';
        loadVideoBtn.disabled = false;
    }
}

// Send Question Function
async function sendQuestion() {
    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    // Disable input while processing
    questionInput.disabled = true;
    sendBtn.disabled = true;

    // Add user message to chat
    addMessage(question, 'user');

    // Clear input
    questionInput.value = '';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to get response');
        }

        // Add AI response to chat
        addMessage(data.answer, 'ai');

    } catch (error) {
        addMessage(`Error: ${error.message}`, 'ai');
    } finally {
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

// Add Message to Chat
function addMessage(text, type) {
    // Remove welcome message if it exists
    const welcomeMsg = chatContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    if (type !== 'system') {
        const label = document.createElement('div');
        label.className = 'message-label';
        label.textContent = type === 'user' ? 'You' : 'AI';
        messageDiv.appendChild(label);
    }

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    messageDiv.appendChild(content);

    chatContainer.appendChild(messageDiv);

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Show Status Message
function showStatus(message, type) {
    videoStatus.textContent = message;
    videoStatus.className = `status-message ${type}`;
    videoStatus.style.display = 'block';

    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            videoStatus.style.display = 'none';
        }, 5000);
    }
}

// Change Video Function
function changeVideo() {
    // Reset to video input section
    chatSection.style.display = 'none';
    videoSection.style.display = 'block';

    // Clear all inputs and reset to one input
    videoInputsContainer.innerHTML = '';
    inputCounter = 0;
    addVideoInputField();

    videoStatus.style.display = 'none';
    currentVideoIds = [];
    isManagementExpanded = false;
}

// Toggle Video Management
function toggleVideoManagement() {
    isManagementExpanded = !isManagementExpanded;

    if (isManagementExpanded) {
        manageControls.style.display = 'block';
        toggleManageBtn.textContent = 'Manage ▲';
    } else {
        manageControls.style.display = 'none';
        toggleManageBtn.textContent = 'Manage ▼';
    }

    // Update video list to show/hide remove buttons
    updateLoadedVideosList();
}

// Update Loaded Videos List
function updateLoadedVideosList() {
    loadedVideosList.innerHTML = '';

    // Update count text
    const count = currentVideoIds.length;
    videoCountText.textContent = `${count} video${count !== 1 ? 's' : ''} loaded`;

    currentVideoIds.forEach(videoId => {
        const videoItem = document.createElement('div');
        videoItem.className = 'video-item';

        const videoIdSpan = document.createElement('span');
        videoIdSpan.className = 'video-id-text';
        videoIdSpan.textContent = videoId;

        videoItem.appendChild(videoIdSpan);

        // Only show remove button when management is expanded
        if (isManagementExpanded) {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn-video-remove';
            removeBtn.innerHTML = '×';
            removeBtn.onclick = () => removeVideoFromSession(videoId);
            videoItem.appendChild(removeBtn);
        }

        loadedVideosList.appendChild(videoItem);
    });
}

// Add Video to Session
async function addVideoToSession() {
    const url = addVideoInput.value.trim();

    if (!url) {
        return;
    }

    // Show loading
    addVideoBtn.disabled = true;
    addVideoInput.disabled = true;

    try {
        const response = await fetch('/add-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to add video');
        }

        // Update video IDs
        currentVideoIds = data.video_ids;

        // Clear input
        addVideoInput.value = '';

        // Add success message to chat
        addMessage(`✓ Video ${data.video_id} added to knowledge base!`, 'system');

        // Auto-collapse management UI
        if (isManagementExpanded) {
            toggleVideoManagement();
        } else {
            updateLoadedVideosList();
        }

    } catch (error) {
        addMessage(`✗ Error adding video: ${error.message}`, 'system');
    } finally {
        addVideoBtn.disabled = false;
        addVideoInput.disabled = false;
    }
}

// Remove Video from Session
async function removeVideoFromSession(videoId) {
    if (!confirm(`Remove video ${videoId} from the session?`)) {
        return;
    }

    // Show loading
    loadingOverlay.style.display = 'flex';

    try {
        const response = await fetch('/remove-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_id: videoId }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to remove video');
        }

        // Update video IDs
        currentVideoIds = data.video_ids;

        // Add message to chat
        addMessage(`✓ Video ${videoId} removed from knowledge base.`, 'system');

        // Auto-collapse management UI
        if (isManagementExpanded) {
            toggleVideoManagement();
        } else {
            updateLoadedVideosList();
        }

    } catch (error) {
        addMessage(`✗ Error removing video: ${error.message}`, 'system');
    } finally {
        loadingOverlay.style.display = 'none';
    }
}
