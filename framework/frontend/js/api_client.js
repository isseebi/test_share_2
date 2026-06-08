const API_BASE = ""; // Relative path works fine as we serve static files from FastAPI directly

const ApiClient = {
    async getSessions() {
        const response = await fetch(`${API_BASE}/api/sessions`);
        if (!response.ok) {
            throw new Error(`Failed to fetch sessions: ${response.statusText}`);
        }
        return await response.json();
    },

    async createSession() {
        const response = await fetch(`${API_BASE}/api/sessions`, {
            method: "POST"
        });
        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.statusText}`);
        }
        return await response.json();
    },

    async getSessionMessages(sessionId) {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`);
        if (!response.ok) {
            throw new Error(`Failed to get messages: ${response.statusText}`);
        }
        return await response.json();
    },

    async sendMessage(sessionId, content) {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ content })
        });
        if (!response.ok) {
            throw new Error(`Failed to send message: ${response.statusText}`);
        }
        return await response.json();
    }
};

window.ApiClient = ApiClient;
