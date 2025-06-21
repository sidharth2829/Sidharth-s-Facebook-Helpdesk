// Socket.IO functionality for Facebook Helpdesk

// Initialize Socket.IO connection
let socket = null;
let currentConversationId = null;

function initializeSocket() {
    // Get the host from the current URL
    const host = window.location.protocol + '//' + window.location.host;
    
    // Connect to Socket.IO server
    socket = io(host);
    
    // Connection events
    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server');
    });
    
    socket.on('error', (error) => {
        console.error('Socket.IO connection error:', error);
    });
    
    // Message events
    socket.on('new_message', (message) => {
        // If the message belongs to the current conversation, add it to the UI
        if (message.conversation_id == currentConversationId) {
            addMessageToUI(message);
        }
    });
    
    // Conversation update events
    socket.on('conversation_update', (data) => {
        updateConversationListItem(data);
    });
    
    // Join response from server
    socket.on('join_response', (data) => {
        console.log('Joined room:', data.room);
    });
}

function joinConversationRoom(conversationId) {
    // Leave current room if we're in one
    if (currentConversationId && socket) {
        socket.emit('leave', { conversation_id: currentConversationId });
    }
    
    // Set new current conversation
    currentConversationId = conversationId;
    
    // Join new room
    if (socket && conversationId) {
        socket.emit('join', { conversation_id: conversationId });
    }
}

function addMessageToUI(message) {
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `d-flex ${message.sender_type === 'agent' ? 'justify-content-end' : 'justify-content-start'}`;
    
    messageDiv.innerHTML = `
        <div class="message ${message.sender_type}">
            ${message.message_text}
            <div class="small mt-1 text-muted">${message.timestamp}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function updateConversationListItem(data) {
    const conversationItem = document.querySelector(`.conversation-item[data-conversation-id="${data.conversation_id}"]`);
    if (!conversationItem) return;
    
    // Update the last message text
    const messagePreview = conversationItem.querySelector('p.text-muted');
    if (messagePreview) {
        messagePreview.textContent = data.last_message;
    }
    
    // Update timestamp
    const timestamp = conversationItem.querySelector('small.text-muted');
    if (timestamp) {
        timestamp.textContent = data.updated_at;
    }
    
    // Move conversation to top of list if not already
    const conversationList = document.getElementById('conversation-list');
    if (conversationList && conversationList.firstChild !== conversationItem) {
        conversationList.insertBefore(conversationItem, conversationList.firstChild);
    }
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO
    initializeSocket();
    
    // Get the initial conversation ID
    const activeConversation = document.querySelector('.conversation-item.active');
    if (activeConversation) {
        joinConversationRoom(activeConversation.getAttribute('data-conversation-id'));
    }
});
