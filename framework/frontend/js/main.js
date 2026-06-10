/**
 * Main App Orchestrator - Bootstraps the application, registers global event listeners
 */
window.AppState = {
    activeSessionId: null
};

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

// Expose setInputText globally for suggestion cards
window.setInputText = function (text) {
    const chatInput = document.getElementById("chat-input");
    if (chatInput) {
        chatInput.value = text;
        chatInput.focus();
    }
};

async function initApp() {
    const newChatBtn = document.getElementById("new-chat-btn");
    const chatForm = document.getElementById("chat-form");
    const uploadBtn = document.getElementById("upload-image-btn");
    const fileInput = document.getElementById("image-file-input");
    const clearImageBtn = document.getElementById("clear-image-btn");
    const chatMain = document.getElementById("chat-main");

    if (newChatBtn && window.SessionManager) {
        newChatBtn.addEventListener("click", window.SessionManager.handleCreateSession);
    }
    
    if (chatForm && window.InputHandler) {
        chatForm.addEventListener("submit", window.InputHandler.handleSendMessage);
    }

    if (uploadBtn && fileInput && window.InputHandler) {
        uploadBtn.addEventListener("click", () => fileInput.click());
        fileInput.addEventListener("change", window.InputHandler.handleImageSelect);
    }
    
    if (clearImageBtn && window.InputHandler) {
        clearImageBtn.addEventListener("click", window.InputHandler.clearSelectedImage);
    }

    if (chatMain && window.InputHandler) {
        // Prevent defaults for all drag events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            chatMain.addEventListener(eventName, window.InputHandler.preventDefaults, false);
        });

        // Highlight/show overlay on dragenter and dragover
        ['dragenter', 'dragover'].forEach(eventName => {
            chatMain.addEventListener(eventName, () => {
                if (window.AppState.activeSessionId) {
                    window.InputHandler.showDragOverlay();
                }
            }, false);
        });

        // Unhighlight/hide overlay on dragleave and drop
        ['dragleave', 'drop'].forEach(eventName => {
            chatMain.addEventListener(eventName, window.InputHandler.hideDragOverlay, false);
        });

        // Handle drop
        chatMain.addEventListener('drop', window.InputHandler.handleDrop, false);
    }

    // Initial load of sessions
    if (window.SessionManager) {
        await window.SessionManager.loadSessions();
    }
}
