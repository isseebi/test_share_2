let activeSessionId = null;

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

    newChatBtn.addEventListener("click", handleCreateSession);
    chatForm.addEventListener("submit", handleSendMessage);

    // Initial load of sessions
    await loadSessions();
}

async function loadSessions() {
    try {
        const sessions = await window.ApiClient.getSessions();
        const listContainer = document.getElementById("sessions-list");
        listContainer.innerHTML = "";

        if (sessions.length === 0) {
            // Auto create first session if none exists
            await handleCreateSession();
            return;
        }

        sessions.forEach(session => {
            const li = document.createElement("li");
            li.className = `session-item ${session.session_id === activeSessionId ? 'active' : ''}`;
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
        if (!activeSessionId && sessions.length > 0) {
            selectSession(sessions[0].session_id);
        }
    } catch (err) {
        console.error("Error loading sessions:", err);
    }
}

async function handleCreateSession() {
    try {
        const session = await window.ApiClient.createSession();
        activeSessionId = session.session_id;
        await loadSessions();
        await selectSession(activeSessionId);
    } catch (err) {
        console.error("Error creating session:", err);
    }
}

async function selectSession(sessionId) {
    activeSessionId = sessionId;

    // Update active class on list
    document.querySelectorAll(".session-item").forEach(item => {
        if (item.dataset.sessionId === sessionId) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    const shortId = sessionId.substring(0, 8);
    document.getElementById("active-session-title").innerText = `Session #${shortId}`;
    document.getElementById("active-session-id").innerText = `Session ID: ${sessionId}`;

    // Enable inputs
    document.getElementById("chat-input").disabled = false;
    document.getElementById("chat-input").placeholder = "Ask the agent anything...";
    document.getElementById("send-btn").disabled = false;

    // Load messages
    await loadMessages(sessionId);

    // Clear trace panel
    clearTrace();
}

async function loadMessages(sessionId) {
    const container = document.getElementById("messages-container");
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
            renderMessage(msg.role, msg.content);
        });

        scrollToBottom();
    } catch (err) {
        console.error("Error loading messages:", err);
    }
}

function renderMessage(role, content) {
    const container = document.getElementById("messages-container");

    // Remove welcome screen if it's there
    const welcome = container.querySelector(".welcome-screen");
    if (welcome) {
        container.innerHTML = "";
    }

    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    // Handle PID simulation JSON block extraction and graph rendering
    if (content.includes("STRUCTURED_DATA_JSON_START")) {
        // Strip all JSON blocks from the bubble text
        const bubbleText = content.replace(/STRUCTURED_DATA_JSON_START[\s\S]*?STRUCTURED_DATA_JSON_END/g, "").trim();
        bubble.innerText = bubbleText;
        row.appendChild(bubble);
        container.appendChild(row);

        // Parse and render each JSON block
        const regex = /STRUCTURED_DATA_JSON_START([\s\S]*?)STRUCTURED_DATA_JSON_END/g;
        let match;
        while ((match = regex.exec(content)) !== null) {
            const jsonStr = match[1].trim();
            try {
                const data = JSON.parse(jsonStr);
                if (data.image) {
                    renderImage(container, data.image);
                    if (data.image_torque) {
                        renderImage(container, data.image_torque);
                    }
                } else if (data.time && data.position && data.metrics) {
                    renderPIDChart(container, data);
                }
            } catch (e) {
                console.error("Failed to parse PID data for chart rendering", e);
            }
        }
    } else {
        bubble.innerText = content;
        row.appendChild(bubble);
        container.appendChild(row);
    }


    scrollToBottom();
}

function renderImage(container, imageSrc) {
    const wrapper = document.createElement("div");
    wrapper.className = "message-row assistant";
    wrapper.style.width = "75%";
    wrapper.style.marginLeft = "0";
    wrapper.style.marginBottom = "15px";

    const img = document.createElement("img");
    img.src = imageSrc;
    img.alt = "Simulation Output";
    img.style.width = "100%";
    img.style.height = "auto";
    img.style.borderRadius = "8px";
    img.style.border = "1px solid rgba(255, 255, 255, 0.1)";

    wrapper.appendChild(img);
    container.appendChild(wrapper);
}

function renderPIDChart(container, data) {
    const chartDiv = document.createElement("div");
    chartDiv.className = "pid-chart-container message-row assistant";
    chartDiv.style.width = "75%";
    chartDiv.style.marginLeft = "0";

    const title = document.createElement("div");
    title.className = "pid-chart-title";
    title.innerHTML = `
        <span><i class="fa-solid fa-square-poll-horizontal"></i> PID Step Response Curve</span>
        <span>Overshoot: ${data.metrics.overshoot_percentage.toFixed(1)}%</span>
    `;
    chartDiv.appendChild(title);

    // Create SVG
    const svgWidth = 450;
    const svgHeight = 200;
    const padding = { top: 15, right: 15, bottom: 25, left: 35 };

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", svgHeight);
    svg.setAttribute("viewBox", `0 0 ${svgWidth} ${svgHeight}`);
    svg.style.background = "#0e0d22";
    svg.style.borderRadius = "8px";

    // Extract values
    const times = data.time;
    const positions = data.position;
    const target = 1.0; // Target is always 1.0 in simulator

    const minTime = 0;
    const maxTime = Math.max(...times);
    const minPos = 0;
    const maxPos = Math.max(target * 1.3, ...positions);

    // Coordinate mapping helpers
    const getX = (t) => padding.left + ((t - minTime) / (maxTime - minTime)) * (svgWidth - padding.left - padding.right);
    const getY = (p) => svgHeight - padding.bottom - ((p - minPos) / (maxPos - minPos)) * (svgHeight - padding.top - padding.bottom);

    // Gridlines / axes
    const gridColor = "rgba(255,255,255,0.07)";
    const axisColor = "rgba(255,255,255,0.3)";

    // Y Axis Target Line
    const targetY = getY(target);
    const targetLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    targetLine.setAttribute("x1", padding.left);
    targetLine.setAttribute("y1", targetY);
    targetLine.setAttribute("x2", svgWidth - padding.right);
    targetLine.setAttribute("y2", targetY);
    targetLine.setAttribute("stroke", "#ff007f");
    targetLine.setAttribute("stroke-width", "1.5");
    targetLine.setAttribute("stroke-dasharray", "4,4");
    svg.appendChild(targetLine);

    // Label for target line
    const targetText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    targetText.setAttribute("x", padding.left + 5);
    targetText.setAttribute("y", targetY - 4);
    targetText.setAttribute("fill", "#ff007f");
    targetText.setAttribute("font-size", "9px");
    targetText.textContent = "Target (1.0)";
    svg.appendChild(targetText);

    // Bottom Axis Line
    const axisLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    axisLine.setAttribute("x1", padding.left);
    axisLine.setAttribute("y1", svgHeight - padding.bottom);
    axisLine.setAttribute("x2", svgWidth - padding.right);
    axisLine.setAttribute("y2", svgHeight - padding.bottom);
    axisLine.setAttribute("stroke", axisColor);
    svg.appendChild(axisLine);

    // Left Axis Line
    const leftAxisLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    leftAxisLine.setAttribute("x1", padding.left);
    leftAxisLine.setAttribute("y1", padding.top);
    leftAxisLine.setAttribute("x2", padding.left);
    leftAxisLine.setAttribute("y2", svgHeight - padding.bottom);
    leftAxisLine.setAttribute("stroke", axisColor);
    svg.appendChild(leftAxisLine);

    // Draw position response curve
    let pathD = "";
    for (let i = 0; i < times.length; i++) {
        const x = getX(times[i]);
        const y = getY(positions[i]);
        if (i === 0) {
            pathD += `M ${x} ${y}`;
        } else {
            pathD += ` L ${x} ${y}`;
        }
    }

    const curve = document.createElementNS("http://www.w3.org/2000/svg", "path");
    curve.setAttribute("d", pathD);
    curve.setAttribute("fill", "none");
    curve.setAttribute("stroke", "#06b6d4");
    curve.setAttribute("stroke-width", "2.5");
    curve.setAttribute("filter", "drop-shadow(0px 0px 5px rgba(6,182,212,0.5))");
    svg.appendChild(curve);

    // Axis labels
    const tLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    tLabel.setAttribute("x", svgWidth / 2);
    tLabel.setAttribute("y", svgHeight - 5);
    tLabel.setAttribute("fill", "rgba(255,255,255,0.6)");
    tLabel.setAttribute("font-size", "10px");
    tLabel.setAttribute("text-anchor", "middle");
    tLabel.textContent = "Time (seconds)";
    svg.appendChild(tLabel);

    const yLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    yLabel.setAttribute("x", 10);
    yLabel.setAttribute("y", svgHeight / 2);
    yLabel.setAttribute("fill", "rgba(255,255,255,0.6)");
    yLabel.setAttribute("font-size", "10px");
    yLabel.setAttribute("transform", `rotate(-90 10 ${svgHeight / 2})`);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.textContent = "Position (rad)";
    svg.appendChild(yLabel);

    // Grid coordinates ticks
    [0.0, 0.5, 1.0, maxPos.toFixed(1)].forEach(val => {
        const y = getY(val);
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", padding.left - 6);
        text.setAttribute("y", y + 3);
        text.setAttribute("fill", "rgba(255,255,255,0.4)");
        text.setAttribute("font-size", "9px");
        text.setAttribute("text-anchor", "end");
        text.textContent = val;
        svg.appendChild(text);
    });

    chartDiv.appendChild(svg);
    container.appendChild(chartDiv);
    scrollToBottom();
}

async function handleSendMessage(e) {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    const content = input.value.trim();
    if (!content || !activeSessionId) return;

    // Render user message immediately
    renderMessage("user", content);
    input.value = "";

    // Clear trace panel and display a spinner/placeholder
    clearTrace();
    showTraceLoading();

    try {
        const response = await window.ApiClient.sendMessage(activeSessionId, content);

        // Hide tracer loading
        hideTraceLoading();

        // Render thinking trace steps
        renderTraceSteps(response.thinking_steps);

        // Render assistant final response
        renderMessage("assistant", response.response_content);

        // Reload sessions to refresh the last message subtitle
        await loadSessions();
    } catch (err) {
        console.error("Error sending message:", err);
        hideTraceLoading();
        renderMessage("assistant", "Sorry, an error occurred while processing your request.");
    }
}

function clearTrace() {
    const container = document.getElementById("trace-container");
    container.innerHTML = "";
}

function showTraceLoading() {
    const container = document.getElementById("trace-container");
    const loader = document.createElement("div");
    loader.className = "trace-placeholder loading-trace";
    loader.innerHTML = `
        <i class="fa-solid fa-circle-notch fa-spin" style="color: var(--accent-cyan);"></i>
        <p>Agent is running the LangGraph thinking loop...</p>
    `;
    container.appendChild(loader);
}

function hideTraceLoading() {
    const container = document.getElementById("trace-container");
    const loader = container.querySelector(".loading-trace");
    if (loader) {
        loader.remove();
    }
}

function renderTraceSteps(steps) {
    const container = document.getElementById("trace-container");
    if (!steps || steps.length === 0) {
        container.innerHTML = `
            <div class="trace-placeholder">
                <i class="fa-solid fa-ban"></i>
                <p>No execution trace was returned.</p>
            </div>
        `;
        return;
    }

    steps.forEach((step, idx) => {
        const card = document.createElement("div");
        card.className = "trace-step-card";

        const badgeClass = step.status || "success";
        const shortMsg = step.message || "";
        const detailsJson = step.details ? JSON.stringify(step.details, null, 2) : "";

        card.innerHTML = `
            <div class="trace-step-header">
                <span class="trace-node-name">${step.node}</span>
                <span class="trace-step-badge ${badgeClass}">${badgeClass}</span>
            </div>
            <div class="trace-step-message">${shortMsg}</div>
        `;

        if (detailsJson && detailsJson !== "{}") {
            const detailsId = `details-${idx}`;
            card.innerHTML += `
                <button class="trace-details-toggle" onclick="toggleDetails('${detailsId}')">
                    <i class="fa-solid fa-chevron-down"></i> Details
                </button>
                <pre id="${detailsId}" class="trace-details-content" style="display: none;">${detailsJson}</pre>
            `;
        }

        container.appendChild(card);
    });
}

window.toggleDetails = function (elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        const isHidden = el.style.display === "none";
        el.style.display = isHidden ? "block" : "none";
    }
};

function scrollToBottom() {
    const container = document.getElementById("messages-container");
    container.scrollTop = container.scrollHeight;
}
