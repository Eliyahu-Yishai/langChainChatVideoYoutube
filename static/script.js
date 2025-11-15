// DOM Elements
const videoSection = document.getElementById('videoSection');
const chatSection = document.getElementById('chatSection');
const videoUrlInput = document.getElementById('videoUrl');
const loadVideoBtn = document.getElementById('loadVideoBtn');
const videoStatus = document.getElementById('videoStatus');
const chatContainer = document.getElementById('chatContainer');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const changeVideoBtn = document.getElementById('changeVideoBtn');
const videoIdDisplay = document.getElementById('videoIdDisplay');
const loadingOverlay = document.getElementById('loadingOverlay');

let currentVideoId = null;

// Event Listeners
loadVideoBtn.addEventListener('click', loadVideo);
sendBtn.addEventListener('click', sendQuestion);
changeVideoBtn.addEventListener('click', changeVideo);

// Allow Enter key to submit
videoUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') loadVideo();
});

questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendQuestion();
});

// Load Video Function
async function loadVideo() {
    const url = videoUrlInput.value.trim();

    if (!url) {
        showStatus('Please enter a YouTube URL', 'error');
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
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to process video');
        }

        // Success
        currentVideoId = data.video_id;
        videoIdDisplay.textContent = `Video ID: ${currentVideoId}`;

        // Hide video section, show chat section
        videoSection.style.display = 'none';
        chatSection.style.display = 'block';

        // Clear previous chat
        chatContainer.innerHTML = '<div class="welcome-message">Video loaded! Ask me anything about this video.</div>';

        showStatus('Video processed successfully!', 'success');

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

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = type === 'user' ? 'You' : 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    messageDiv.appendChild(label);
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
    videoUrlInput.value = '';
    videoStatus.style.display = 'none';
    currentVideoId = null;
}

// Focus on video input on page load
videoUrlInput.focus();
