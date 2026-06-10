/**
 * Trace Renderer - Handles the LangGraph agent thinking trace steps
 */
(function() {
    function clearTrace() {
        const container = document.getElementById("trace-container");
        if (container) container.innerHTML = "";
    }

    function showTraceLoading() {
        const container = document.getElementById("trace-container");
        if (!container) return;
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
        if (!container) return;
        const loader = container.querySelector(".loading-trace");
        if (loader) {
            loader.remove();
        }
    }

    function renderTraceSteps(steps) {
        const container = document.getElementById("trace-container");
        if (!container) return;
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

    // Expose to window
    window.TraceRenderer = {
        clearTrace,
        showTraceLoading,
        hideTraceLoading,
        renderTraceSteps
    };
})();
