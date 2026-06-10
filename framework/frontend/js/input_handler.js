/**
 * Input Handler - Manages user input, image upload select/drag-and-drop, and message sending flow
 */
(function() {
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function showDragOverlay() {
        const overlay = document.getElementById("drag-drop-overlay");
        if (overlay) {
            overlay.style.display = "flex";
        }
    }

    function hideDragOverlay() {
        const overlay = document.getElementById("drag-drop-overlay");
        if (overlay) {
            overlay.style.display = "none";
        }
    }

    function handleDrop(e) {
        if (!window.AppState.activeSessionId) return;
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            const file = files[0];
            if (file.type.startsWith("image/")) {
                const fileInput = document.getElementById("image-file-input");
                if (fileInput) {
                    try {
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(file);
                        fileInput.files = dataTransfer.files;
                        fileInput.dispatchEvent(new Event("change"));
                    } catch (err) {
                        console.error("Failed to assign dropped file:", err);
                    }
                }
            }
        }
    }

    async function handleImageSelect(e) {
        const file = e.target.files[0];
        if (file) {
            try {
                const base64 = await toBase64(file);
                const previewContainer = document.getElementById("image-preview-container");
                const previewImg = document.getElementById("image-preview");
                if (previewContainer && previewImg) {
                    previewImg.src = base64;
                    previewContainer.style.display = "block";
                }
            } catch (err) {
                console.error("Error loading image preview:", err);
            }
        }
    }

    function clearSelectedImage() {
        const fileInput = document.getElementById("image-file-input");
        const previewContainer = document.getElementById("image-preview-container");
        const previewImg = document.getElementById("image-preview");
        if (fileInput) fileInput.value = "";
        if (previewContainer) previewContainer.style.display = "none";
        if (previewImg) previewImg.src = "";
    }

    function toBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    async function handleSendMessage(e) {
        e.preventDefault();
        const input = document.getElementById("chat-input");
        const content = input.value.trim();
        const fileInput = document.getElementById("image-file-input");
        const hasImage = fileInput && fileInput.files && fileInput.files[0];
        const activeSessionId = window.AppState.activeSessionId;

        if ((!content && !hasImage) || !activeSessionId) return;

        let base64Image = null;
        if (hasImage) {
            try {
                base64Image = await toBase64(fileInput.files[0]);
            } catch (err) {
                console.error("Error reading image file:", err);
                return;
            }
        }

        if (window.MessageRenderer) {
            window.MessageRenderer.renderMessage("user", content, base64Image);
        }
        input.value = "";
        clearSelectedImage();

        if (window.TraceRenderer) {
            window.TraceRenderer.clearTrace();
            window.TraceRenderer.showTraceLoading();
        }

        try {
            const response = await window.ApiClient.sendMessage(activeSessionId, content, base64Image);

            if (window.TraceRenderer) {
                window.TraceRenderer.hideTraceLoading();
                window.TraceRenderer.renderTraceSteps(response.thinking_steps);
            }

            if (window.MessageRenderer) {
                window.MessageRenderer.renderMessage("assistant", response.response_content);
            }

            if (window.SessionManager) {
                await window.SessionManager.loadSessions();
            }
        } catch (err) {
            console.error("Error sending message:", err);
            if (window.TraceRenderer) {
                window.TraceRenderer.hideTraceLoading();
            }
            if (window.MessageRenderer) {
                window.MessageRenderer.renderMessage("assistant", "Sorry, an error occurred while processing your request.");
            }
        }
    }

    // Expose to window
    window.InputHandler = {
        preventDefaults,
        showDragOverlay,
        hideDragOverlay,
        handleDrop,
        handleImageSelect,
        clearSelectedImage,
        handleSendMessage
    };
})();
