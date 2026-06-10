/**
 * Session Manager - Handles session state, session list updates, and selection loading
 */
(function() {
    async function loadSessions() {
        try {
            const sessions = await window.ApiClient.getSessions();
            const listContainer = document.getElementById("sessions-list");
            if (!listContainer) return;
            listContainer.innerHTML = "";

            if (sessions.length === 0) {
                // Auto create first session if none exists
                await handleCreateSession();
                return;
            }

            sessions.forEach(session => {
                const li = document.createElement("li");
                li.className = `session-item ${session.session_id === window.AppState.activeSessionId ? 'active' : ''}`;
                li.dataset.sessionId = session.session_id;

                // Format a simple display title
                const shortId = session.session_id.substring(0, 8);
                const truncatedMessage = session.last_message.length > 25
                    ? session.last_message.substring(0, 22) + "..."
                    : session.last_message;

                li.innerHTML = `
                    <span class="session-title">Chat #${shortId}</span>
                    <span class="session-subtitle">${truncatedMessage}</span>
                `;

                li.addEventListener("click", () => selectSession(session.session_id));
                listContainer.appendChild(li);
            });

            // If no session is active but list has sessions, select first one
            if (!window.AppState.activeSessionId && sessions.length > 0) {
                selectSession(sessions[0].session_id);
            }
        } catch (err) {
            console.error("Error loading sessions:", err);
        }
    }

    async function handleCreateSession() {
        try {
            const session = await window.ApiClient.createSession();
            window.AppState.activeSessionId = session.session_id;
            await loadSessions();
            await selectSession(window.AppState.activeSessionId);
        } catch (err) {
            console.error("Error creating session:", err);
        }
    }

    async function selectSession(sessionId) {
        window.AppState.activeSessionId = sessionId;

        // Update active class on list
        document.querySelectorAll(".session-item").forEach(item => {
            if (item.dataset.sessionId === sessionId) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });

        const shortId = sessionId.substring(0, 8);
        const activeTitle = document.getElementById("active-session-title");
        const activeId = document.getElementById("active-session-id");
        if (activeTitle) activeTitle.innerText = `Session #${shortId}`;
        if (activeId) activeId.innerText = `Session ID: ${sessionId}`;

        // Enable inputs
        const chatInput = document.getElementById("chat-input");
        const sendBtn = document.getElementById("send-btn");
        const uploadBtn = document.getElementById("upload-image-btn");

        if (chatInput) {
            chatInput.disabled = false;
            chatInput.placeholder = "Ask the agent anything...";
        }
        if (sendBtn) sendBtn.disabled = false;
        if (uploadBtn) uploadBtn.disabled = false;

        // Load messages
        await loadMessages(sessionId);

        // Clear trace panel
        if (window.TraceRenderer) {
            window.TraceRenderer.clearTrace();
        }
    }

    async function loadMessages(sessionId) {
        const container = document.getElementById("messages-container");
        if (!container) return;
        container.innerHTML = "";

        try {
            const messages = await window.ApiClient.getSessionMessages(sessionId);

            if (messages.length === 0) {
                // Render welcome screen if empty
                const welcome = document.createElement("div");
                welcome.className = "welcome-screen";
                welcome.innerHTML = `
                    <i class="fa-solid fa-compass welcome-icon"></i>
                    <h1>Welcome to ServoBot Agent</h1>
                    <p>This agent is built using clean architecture boundaries and powered by LangGraph. You can inspect the step-by-step thinking loop on the right panel.</p>
                `;
                container.appendChild(welcome);
                return;
            }

            messages.forEach(msg => {
                if (window.MessageRenderer) {
                    window.MessageRenderer.renderMessage(msg.role, msg.content, msg.image);
                }
            });

            if (window.MessageRenderer) {
                window.MessageRenderer.scrollToBottom();
            }
        } catch (err) {
            console.error("Error loading messages:", err);
        }
    }

    // Expose to window
    window.SessionManager = {
        loadSessions,
        handleCreateSession,
        selectSession,
        loadMessages
    };
})();
