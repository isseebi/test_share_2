/**
 * Layout Manager - Handles resizable sidebars and collapsible toggle states with LocalStorage persistence
 */
document.addEventListener("DOMContentLoaded", () => {
    initLayout();
});

function initLayout() {
    const appContainer = document.getElementById("app-container");
    const sidebarLeft = document.getElementById("sidebar-left");
    const sidebarRight = document.getElementById("sidebar-right");
    const resizerLeft = document.getElementById("resizer-left");
    const resizerRight = document.getElementById("resizer-right");

    const collapseLeftBtn = document.getElementById("collapse-left-btn");
    const collapseRightBtn = document.getElementById("collapse-right-btn");
    const expandLeftBtn = document.getElementById("expand-left-btn");
    const expandRightBtn = document.getElementById("expand-right-btn");

    // Limits
    const MIN_LEFT_WIDTH = 220;
    const MAX_LEFT_WIDTH = 450;
    const MIN_RIGHT_WIDTH = 250;
    const MAX_RIGHT_WIDTH = 550;

    // Load saved settings
    const savedLeftWidth = localStorage.getItem("sidebar-left-width");
    const savedRightWidth = localStorage.getItem("sidebar-right-width");
    const leftCollapsed = localStorage.getItem("sidebar-left-collapsed") === "true";
    const rightCollapsed = localStorage.getItem("sidebar-right-collapsed") === "true";

    if (savedLeftWidth && appContainer) {
        appContainer.style.setProperty("--left-width", savedLeftWidth);
    }
    if (savedRightWidth && appContainer) {
        appContainer.style.setProperty("--right-width", savedRightWidth);
    }

    if (leftCollapsed) {
        setSidebarLeftState(true);
    }
    if (rightCollapsed) {
        setSidebarRightState(true);
    }

    // Collapse Left Sidebar
    if (collapseLeftBtn) {
        collapseLeftBtn.addEventListener("click", () => setSidebarLeftState(true));
    }
    if (expandLeftBtn) {
        expandLeftBtn.addEventListener("click", () => setSidebarLeftState(false));
    }

    // Collapse Right Sidebar
    if (collapseRightBtn) {
        collapseRightBtn.addEventListener("click", () => setSidebarRightState(true));
    }
    if (expandRightBtn) {
        expandRightBtn.addEventListener("click", () => setSidebarRightState(false));
    }

    // Helper functions for collapse/expand state
    function setSidebarLeftState(collapsed) {
        if (!appContainer || !sidebarLeft || !resizerLeft) return;
        if (collapsed) {
            appContainer.classList.add("collapsed-left");
            sidebarLeft.classList.add("collapsed");
            resizerLeft.classList.add("collapsed");
            if (expandLeftBtn) expandLeftBtn.style.display = "flex";
        } else {
            appContainer.classList.remove("collapsed-left");
            sidebarLeft.classList.remove("collapsed");
            resizerLeft.classList.remove("collapsed");
            if (expandLeftBtn) expandLeftBtn.style.display = "none";
        }
        localStorage.setItem("sidebar-left-collapsed", collapsed);
    }

    function setSidebarRightState(collapsed) {
        if (!appContainer || !sidebarRight || !resizerRight) return;
        if (collapsed) {
            appContainer.classList.add("collapsed-right");
            sidebarRight.classList.add("collapsed");
            resizerRight.classList.add("collapsed");
            if (expandRightBtn) expandRightBtn.style.display = "flex";
        } else {
            appContainer.classList.remove("collapsed-right");
            sidebarRight.classList.remove("collapsed");
            resizerRight.classList.remove("collapsed");
            if (expandRightBtn) expandRightBtn.style.display = "none";
        }
        localStorage.setItem("sidebar-right-collapsed", collapsed);
    }

    // Resize Left Sidebar (Dragging)
    if (resizerLeft) {
        resizerLeft.addEventListener("mousedown", (e) => {
            e.preventDefault();
            if (appContainer) appContainer.classList.add("resizing");
            resizerLeft.classList.add("dragging");

            function onMouseMove(moveEvent) {
                let newWidth = moveEvent.clientX;
                if (newWidth < MIN_LEFT_WIDTH) newWidth = MIN_LEFT_WIDTH;
                if (newWidth > MAX_LEFT_WIDTH) newWidth = MAX_LEFT_WIDTH;
                
                if (appContainer) {
                    appContainer.style.setProperty("--left-width", `${newWidth}px`);
                }
            }

            function onMouseUp() {
                if (appContainer) appContainer.classList.remove("resizing");
                resizerLeft.classList.remove("dragging");
                
                // Save final width
                if (appContainer) {
                    const finalWidth = appContainer.style.getPropertyValue("--left-width");
                    localStorage.setItem("sidebar-left-width", finalWidth);
                }

                document.removeEventListener("mousemove", onMouseMove);
                document.removeEventListener("mouseup", onMouseUp);
            }

            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", onMouseUp);
        });
    }

    // Resize Right Sidebar (Dragging)
    if (resizerRight) {
        resizerRight.addEventListener("mousedown", (e) => {
            e.preventDefault();
            if (appContainer) appContainer.classList.add("resizing");
            resizerRight.classList.add("dragging");

            function onMouseMove(moveEvent) {
                let newWidth = window.innerWidth - moveEvent.clientX;
                if (newWidth < MIN_RIGHT_WIDTH) newWidth = MIN_RIGHT_WIDTH;
                if (newWidth > MAX_RIGHT_WIDTH) newWidth = MAX_RIGHT_WIDTH;

                if (appContainer) {
                    appContainer.style.setProperty("--right-width", `${newWidth}px`);
                }
            }

            function onMouseUp() {
                if (appContainer) appContainer.classList.remove("resizing");
                resizerRight.classList.remove("dragging");

                // Save final width
                if (appContainer) {
                    const finalWidth = appContainer.style.getPropertyValue("--right-width");
                    localStorage.setItem("sidebar-right-width", finalWidth);
                }

                document.removeEventListener("mousemove", onMouseMove);
                document.removeEventListener("mouseup", onMouseUp);
            }

            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", onMouseUp);
        });
    }
}
