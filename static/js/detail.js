(function () {
    "use strict";

    function escapeHtml(unsafe) {
        if (!unsafe) return "";
        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    async function copyText(text, btn) {
        try {
            await navigator.clipboard.writeText(text);
            if (btn) {
                const prev = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i> Copied';
                setTimeout(() => { btn.innerHTML = prev; }, 1500);
            }
        } catch (_) {
            /* ignore */
        }
    }

    document.querySelectorAll(".copy-btn").forEach((btn) => {
        btn.addEventListener("click", () => copyText(btn.dataset.copy || "", btn));
    });

    // Install tabs
    const tabs = document.querySelectorAll(".install-tab");
    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            tabs.forEach((t) => {
                t.classList.remove("active");
                t.setAttribute("aria-selected", "false");
            });
            document.querySelectorAll(".install-panel").forEach((p) => p.classList.remove("active"));
            tab.classList.add("active");
            tab.setAttribute("aria-selected", "true");
            const panel = document.getElementById(tab.dataset.panel);
            if (panel) panel.classList.add("active");
        });
    });

    // Flag filter
    const filter = document.getElementById("flagFilter");
    const table = document.getElementById("flagsTable");
    if (filter && table) {
        filter.addEventListener("input", () => {
            const q = filter.value.trim().toLowerCase();
            table.querySelectorAll("tbody tr").forEach((row) => {
                const hay = (row.dataset.flagSearch || "").toLowerCase();
                row.hidden = q !== "" && !hay.includes(q);
            });
        });
    }

    // Command explainer
    const form = document.getElementById("explainForm");
    const result = document.getElementById("explainResult");
    if (form && result) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const input = document.getElementById("explainInput");
            const command = (input && input.value) || "";
            const toolId = form.dataset.toolId;
            result.hidden = false;
            result.textContent = "Explaining…";
            try {
                const resp = await fetch(`/api/tools/${encodeURIComponent(toolId)}/explain`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ command }),
                });
                const data = await resp.json();
                if (!resp.ok) {
                    result.textContent = data.error || "Explain failed";
                    return;
                }
                result.innerHTML = (data.tokens || [])
                    .map((t) => {
                        const cls = escapeHtml(t.kind || "arg");
                        const note = escapeHtml(t.note || "");
                        const tok = escapeHtml(t.token || "");
                        return `<div class="explain-token kind-${cls}"><code>${tok}</code><span>${note}</span></div>`;
                    })
                    .join("");
                if ((data.unknown_flags || []).length) {
                    result.innerHTML += `<p class="muted">Unknown flags (not in verified help): ${data.unknown_flags.map(escapeHtml).join(", ")}</p>`;
                }
            } catch (err) {
                result.textContent = "Network error explaining command";
            }
        });
    }
})();
