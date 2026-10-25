// Security sanitization functions
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function sanitizeUrl(url) {
    if (!url) return '';
    // Prevent javascript:, vbscript:, data: protocols
    const sanitized = String(url).replace(/[\x00-\x20]/g, '').trim();
    if (/^(?:javascript|vbscript|data):/i.test(sanitized)) {
        return '#';
    }
    return sanitized;
}

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const searchForm = document.getElementById('searchForm');
const resultsContainer = document.getElementById('resultsContainer');
const toolsGrid = document.getElementById('toolsGrid');
const resultsCount = document.getElementById('resultsCount');
const loadingIndicator = document.getElementById('loadingIndicator');
const sortOptions = document.getElementById('sortOptions');
const exampleTags = document.querySelectorAll('.example-tag');

// Pagination state
let currentOffset = 0;
let currentQuery = '';
let currentTotal = 0;
let currentHasMore = false;
const PAGE_LIMIT = 10;

// ── Error boundary state ─────────────────────────────────────────────

let retryCount = 0;
const MAX_RETRIES = 3;
let currentAbortController = null;
let timeoutId = null;
const FETCH_TIMEOUT_MS = 15000; // 15 seconds
let lastFailedPayload = null;    // stores the last fetch body for retry

// ── Fallback categories (no backend needed) ──────────────────────────

const FALLBACK_CATEGORIES = [
    { name: 'Network', icon: 'fa-network-wired', query: 'network scanner tools', color: '#00ff88' },
    { name: 'Web', icon: 'fa-globe', query: 'web application security', color: '#00d4ff' },
    { name: 'Password', icon: 'fa-key', query: 'password cracking tools', color: '#ff3366' },
    { name: 'Forensics', icon: 'fa-microscope', query: 'digital forensics tools', color: '#9d4edd' },
    { name: 'Exploitation', icon: 'fa-bug', query: 'penetration testing exploitation', color: '#ffaa00' },
    { name: 'Vulnerability', icon: 'fa-shield-alt', query: 'vulnerability scanner tools', color: '#ff6600' },
];

// ── Health check ─────────────────────────────────────────────────────

async function checkBackendHealth() {
    try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 3000);
        const response = await fetch('/health', { signal: controller.signal });
        clearTimeout(timer);
        if (!response.ok) return false;
        const data = await response.json();
        return data.status === 'ok';
    } catch {
        return false;
    }
}

// ── Abort any in-flight request ──────────────────────────────────────

function abortInFlightRequest() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
    if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
    }
}

// Update time in status bar
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString();
}
updateTime();
setInterval(updateTime, 1000);

// Event Listeners
if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        performSearch();
    });
}

exampleTags.forEach(tag => {
    tag.addEventListener('click', () => {
        const tagText = tag.textContent.trim();
        // The icon does not contribute textContent, so we don't need to split/slice.
        searchInput.value = tagText;
        performSearch();
    });
});

// ── Category filter (All / Security / General) ─────────────────────
let currentCategory = 'all';
document.querySelectorAll('.category-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        currentCategory = chip.dataset.category || 'all';
        document.querySelectorAll('.category-chip').forEach(c => {
            const on = c === chip;
            c.classList.toggle('active', on);
            c.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
        if (searchInput.value.trim()) {
            performSearch();
        }
    });
});

if (sortOptions) {
    sortOptions.addEventListener('change', () => {
        const query = searchInput.value.trim();
        if (query && toolsGrid.children.length > 0 && !toolsGrid.querySelector('.no-results')) {
            performSearch(); // Re-search with current query to re-sort
        }
    });
}

// ── Search Function with retry, abort, timeout ───────────────────────

function performSearch(resetOffset = true) {
    const query = searchInput.value.trim();

    if (!query) {
        showAlert('Please enter a search query to hunt for tools', 'warning');
        if (searchInput) {
            searchInput.setAttribute('aria-invalid', 'true');
            searchInput.style.borderColor = '#ffaa00';
            searchInput.focus();
        }
        return;
    }

    // Reset retry count on a new search (not on manual retry)
    if (resetOffset) {
        retryCount = 0;
        currentOffset = 0;
        currentQuery = query;
    }

    // Abort any previous in-flight request to prevent race conditions
    abortInFlightRequest();

    // Show loading indicator and disable inputs
    loadingIndicator.style.display = 'block';
    loadingIndicator.querySelector('h3').textContent = 'Scanning Arsenal...';

    searchButton.disabled = true;
    searchButton.style.opacity = '0.7';
    searchButton.style.cursor = 'not-allowed';
    searchButton.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Hunting...';
    searchInput.disabled = true;
    searchInput.style.opacity = '0.7';
    searchInput.style.cursor = 'not-allowed';

    if (resetOffset) {
        resultsContainer.style.display = 'none';
    }

    // Create new AbortController for this request
    currentAbortController = new AbortController();
    const signal = currentAbortController.signal;

    // Set up timeout
    timeoutId = setTimeout(() => {
        if (currentAbortController) {
            currentAbortController.abort();
            currentAbortController = null;
        }
        loadingIndicator.style.display = 'none';
        resultsContainer.style.display = 'block';

        searchButton.disabled = false;
        searchButton.style.opacity = '1';
        searchButton.style.cursor = 'pointer';
        searchButton.innerHTML = '<i class="fas fa-crosshairs" aria-hidden="true"></i> Hunt Tools';
        searchInput.disabled = false;
        searchInput.style.opacity = '1';
        searchInput.style.cursor = 'text';

        showTimeoutError();
    }, FETCH_TIMEOUT_MS);

    // Build the request body and store for retry
    const body = JSON.stringify({
        query: currentQuery,
        category: currentCategory,
        limit: PAGE_LIMIT,
        offset: currentOffset
    });
    if (resetOffset) {
        lastFailedPayload = body;
    }

    // Call Flask backend
    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: body,
        signal: signal,
    })
    .then(response => {
        // Clear timeout since we got a response
        if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
        }

        if (!response.ok) {
            // Try to parse error body
            return response.json().then(errData => {
                throw { status: response.status, ...errData };
            }).catch(err => {
                if (err && err.error) throw err;
                throw { status: response.status, error: `HTTP ${response.status}` };
            });
        }
        return response.json();
    })
    .then(data => {
        // Reset retry count on success
        retryCount = 0;

        if (data.error) {
            throw { error: data.error, code: data.code || 'UNKNOWN', retryable: data.retryable !== false };
        }

        const results = data.results || [];
        currentHasMore = data.has_more || false;
        currentTotal = data.total || 0;

        if (resetOffset) {
            // New search — replace results
            displayResults(results, true);
        } else {
            // Load more — append results
            appendResults(results);
        }

        // Update results count with range info
        updateResultsCount();

        // Hide loading, show results
        loadingIndicator.style.display = 'none';
        resultsContainer.style.display = 'block';
        currentAbortController = null;

        if (resetOffset && resultsCount) {
            resultsCount.setAttribute('tabindex', '-1');
            resultsCount.focus();
        }

        searchButton.disabled = false;
        searchButton.style.opacity = '1';
        searchButton.style.cursor = 'pointer';
        searchButton.innerHTML = '<i class="fas fa-crosshairs" aria-hidden="true"></i> Hunt Tools';
        searchInput.disabled = false;
        searchInput.style.opacity = '1';
        searchInput.style.cursor = 'text';

        // Re-enable load more button if it exists
        const loadMoreBtn = document.querySelector('.load-more');
        if (loadMoreBtn) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.style.opacity = '1';
            loadMoreBtn.style.cursor = 'pointer';
            loadMoreBtn.innerHTML = '<i class="fas fa-arrow-down" aria-hidden="true"></i> Load More Tools';
        }
    })
    .catch(error => {
        // Clear timeout if still active
        if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
        }

        loadingIndicator.style.display = 'none';
        currentAbortController = null;

        // Ignore abort errors triggered by new search or manual abort
        if (error && error.name === 'AbortError') {
            // Only show error if this was a timeout, not a user-initiated abort
            return;
        }

        searchButton.disabled = false;
        searchButton.style.opacity = '1';
        searchButton.style.cursor = 'pointer';
        searchButton.innerHTML = '<i class="fas fa-crosshairs" aria-hidden="true"></i> Hunt Tools';
        searchInput.disabled = false;
        searchInput.style.opacity = '1';
        searchInput.style.cursor = 'text';

        // Re-enable load more button if it exists
        const loadMoreBtn = document.querySelector('.load-more');
        if (loadMoreBtn) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.style.opacity = '1';
            loadMoreBtn.style.cursor = 'pointer';
            loadMoreBtn.innerHTML = '<i class="fas fa-arrow-down" aria-hidden="true"></i> Load More Tools';
        }

        console.error('Error:', error);

        const isRetryable = error.retryable !== false;
        const errorMessage = error.error || 'Failed to connect to the tool database';

        // Show error state with potential retry
        resultsContainer.style.display = 'block';

        if (isRetryable && retryCount < MAX_RETRIES) {
            // Show retry interface
            retryCount++;
            showRetryError(errorMessage, retryCount);
        } else if (retryCount >= MAX_RETRIES) {
            // Max retries exhausted — show offline fallback
            showOfflineFallback();
        } else {
            // Non-retryable error (e.g. bad request)
            showError(errorMessage);
        }

        // Update results count for error state
        if (resultsCount) {
            resultsCount.innerHTML = `<i class="fas fa-exclamation-triangle" aria-hidden="true"></i> Search failed`;
        }
    });
}

// ── Retry function ───────────────────────────────────────────────────

function retrySearch() {
    if (lastFailedPayload) {
        // Restore the query from the last failed payload
        try {
            const parsed = JSON.parse(lastFailedPayload);
            searchInput.value = parsed.query;
        } catch { /* ignore */ }
    }
    performSearch(false);  // false = don't reset offset, use existing retryCount
}

// ── Error Display States ─────────────────────────────────────────────

function showRetryError(message, attempt) {
    const remaining = MAX_RETRIES - attempt;
    toolsGrid.innerHTML = `
        <div class="no-results error-state">
            <i class="fas fa-exclamation-triangle" style="color: var(--danger);" aria-hidden="true"></i>
            <h3 style="color: var(--danger);">Connection Error</h3>
            <p>${escapeHtml(message)}</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle" aria-hidden="true"></i> Retry attempt ${attempt} of ${MAX_RETRIES}
            </p>
            <button class="retry-btn" onclick="retrySearch()">
                <i class="fas fa-sync-alt" aria-hidden="true"></i> Retry Search
            </button>
            ${remaining > 0 ? `<p style="margin-top: 8px; font-size: 0.8rem; color: var(--gray);">${remaining} retr${remaining !== 1 ? 'ies' : 'y'} remaining</p>` : ''}
        </div>
    `;
}

function showTimeoutError() {
    toolsGrid.innerHTML = `
        <div class="no-results error-state">
            <i class="fas fa-hourglass-end" style="color: var(--warning);" aria-hidden="true"></i>
            <h3 style="color: var(--warning);">Request Timed Out</h3>
            <p>The search request took too long to respond (over ${FETCH_TIMEOUT_MS / 1000} seconds).</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle" aria-hidden="true"></i> The backend may be overloaded or unreachable
            </p>
            <button class="retry-btn" onclick="retrySearch()">
                <i class="fas fa-sync-alt" aria-hidden="true"></i> Retry Search
            </button>
        </div>
    `;
    resultsContainer.style.display = 'block';
    if (resultsCount) {
        resultsCount.innerHTML = `<i class="fas fa-hourglass-end" aria-hidden="true"></i> Request timed out`;
    }
}

function showOfflineFallback() {
    toolsGrid.innerHTML = `
        <div class="no-results error-state offline-fallback">
            <i class="fas fa-wifi-slash" style="color: var(--gray);" aria-hidden="true"></i>
            <h3 style="color: var(--gray);">Offline Mode</h3>
            <p>The backend is currently unavailable after ${MAX_RETRIES} retry attempts.</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle" aria-hidden="true"></i> Try browsing by category below:
            </p>
            <div class="fallback-categories">
                ${FALLBACK_CATEGORIES.map(cat => `
                    <button type="button" class="fallback-category-tile" data-category="${cat.query}" style="--cat-color: ${cat.color};">
                        <i class="fas ${cat.icon}" aria-hidden="true"></i>
                        <span>${cat.name}</span>
                    </button>
                `).join('')}
            </div>
            <button class="retry-btn retry-btn-primary" onclick="retrySearch()">
                <i class="fas fa-sync-alt" aria-hidden="true"></i> Try Again
            </button>
        </div>
    `;

    // Attach click handlers to fallback category tiles
    document.querySelectorAll('.fallback-category-tile').forEach(tile => {
        tile.addEventListener('click', () => {
            const query = tile.dataset.category;
            searchInput.value = query;
            retryCount = 0;  // Reset retry count for fresh search
            performSearch(true);
        });
    });
}

// ── Update results count showing range ───────────────────────────────

function updateResultsCount() {
    if (currentTotal === 0) {
        resultsCount.innerHTML = `<i class="fas fa-search-minus" aria-hidden="true"></i> No tools found in arsenal`;
        return;
    }
    const shown = toolsGrid.querySelectorAll('.tool-card').length;
    if (shown === currentTotal) {
        resultsCount.innerHTML = `<i class="fas fa-crosshairs" aria-hidden="true"></i> Showing all ${currentTotal} cybersecurity tool${currentTotal !== 1 ? 's' : ''} in arsenal`;
    } else {
        const from = currentOffset + 1;
        const to = currentOffset + shown;
        resultsCount.innerHTML = `<i class="fas fa-crosshairs" aria-hidden="true"></i> Showing ${from}-${to} of ${currentTotal} cybersecurity tool${currentTotal !== 1 ? 's' : ''} in arsenal`;
    }
}

// Display Results (initial or refreshed)

// ── Docs slide-over panel ────────────────────────────────────────────

function buildToolCardHtml(tool) {
    const categoryClass = getCategoryClass(tool.subcategory);
    const id = escapeHtml(tool.id || '');
    const link = sanitizeUrl(tool.link || '#');
    const hasLink = !!tool.link;
    return `
            <div class="card-header">
                <h3>${escapeHtml(tool.name || 'Unknown Tool')}</h3>
                ${categoryBadges(tool, categoryClass)}
            </div>
            <div class="card-body">
                <p>${escapeHtml(tool.description || 'No description available')}</p>
            </div>
            <div class="card-footer">
                <div class="card-actions">
                    <button type="button" class="docs-btn" data-tool-id="${id}" ${id ? '' : 'disabled'}>
                        <i class="fas fa-book" aria-hidden="true"></i> Docs
                    </button>
                    <a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer" class="tool-link compact" ${!hasLink ? 'style="opacity: 0.5; cursor: not-allowed;" aria-disabled="true" tabindex="-1" onclick="return false;" title="Tool link is currently unavailable"' : ''}>
                        <i class="fas fa-external-link-alt" aria-hidden="true"></i> ${hasLink ? 'Open' : 'No Link'}
                        <span class="visually-hidden">(opens in a new tab)</span>
                    </a>
                </div>
            </div>
        `;
}

function wireDocsButtons(root) {
    (root || document).querySelectorAll('.docs-btn[data-tool-id]').forEach((btn) => {
        if (btn.dataset.wired) return;
        btn.dataset.wired = '1';
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            openDocsPanel(btn.dataset.toolId);
        });
    });
}

function closeDocsPanel() {
    const panel = document.getElementById('docsPanel');
    const backdrop = document.getElementById('docsBackdrop');
    if (panel) {
        panel.classList.remove('open');
        panel.setAttribute('hidden', '');
    }
    if (backdrop) {
        backdrop.classList.remove('open');
        backdrop.setAttribute('hidden', '');
    }
    document.body.classList.remove('docs-panel-open');
}

async function openDocsPanel(toolId) {
    if (!toolId) return;
    const panel = document.getElementById('docsPanel');
    const backdrop = document.getElementById('docsBackdrop');
    const body = document.getElementById('docsPanelBody');
    const title = document.getElementById('docsPanelTitle');
    if (!panel || !body) {
        window.location.href = `/tool/${encodeURIComponent(toolId)}`;
        return;
    }
    body.innerHTML = '<p class="muted">Loading docs…</p>';
    if (title) title.textContent = toolId;
    panel.removeAttribute('hidden');
    backdrop && backdrop.removeAttribute('hidden');
    requestAnimationFrame(() => {
        panel.classList.add('open');
        backdrop && backdrop.classList.add('open');
    });
    document.body.classList.add('docs-panel-open');

    let tool = null;
    let doc = null;
    try {
        const [tr, dr] = await Promise.all([
            fetch(`/api/tools/${encodeURIComponent(toolId)}`),
            fetch(`/api/tools/${encodeURIComponent(toolId)}/docs`),
        ]);
        if (tr.ok) tool = await tr.json();
        if (dr.ok) doc = await dr.json();
        else if (dr.status === 404) doc = null;
    } catch (_) {
        body.innerHTML = '<p class="muted">Failed to load docs.</p>';
        return;
    }
    if (!tool) {
        body.innerHTML = '<p class="muted">Tool not found.</p>';
        return;
    }
    if (title) title.textContent = tool.name || toolId;
    body.innerHTML = renderDocsPanel(tool, doc);
    wirePanelInteractions(body, tool.id || toolId, doc);
}

function renderDocsPanel(tool, doc) {
    doc = doc || {};
    const summary = escapeHtml(doc.summary || tool.description || 'No summary yet.');
    const cat = escapeHtml(tool.category || '');
    const sub = escapeHtml(tool.subcategory || '');
    let html = `
        <p class="detail-summary">${summary}</p>
        <div class="badges" style="margin-bottom:12px;">
            ${cat ? `<span class="category ${cat}">${cat}</span>` : ''}
            ${sub ? `<span class="category subcategory">${sub}</span>` : ''}
        </div>
        <p><a class="full-page-link" href="/tool/${encodeURIComponent(tool.id || '')}"><i class="fas fa-expand" aria-hidden="true"></i> Open full page</a></p>
    `;

    const install = doc.install || [];
    if (install.length) {
        html += `<section class="detail-section"><h2><i class="fas fa-download" aria-hidden="true"></i> Install</h2>`;
        html += `<div class="install-tabs" role="tablist">`;
        install.forEach((item, i) => {
            html += `<button type="button" class="install-tab${i === 0 ? ' active' : ''}" data-panel="p-install-${i}">${escapeHtml(item.method || 'cmd')}</button>`;
        });
        html += `</div>`;
        install.forEach((item, i) => {
            html += `<div class="install-panel${i === 0 ? ' active' : ''}" id="p-install-${i}">
                <pre class="code-block"><code>${escapeHtml(item.cmd || '')}</code></pre>
                <button type="button" class="copy-btn" data-copy="${escapeHtml(item.cmd || '')}"><i class="fas fa-copy" aria-hidden="true"></i> Copy</button>
            </div>`;
        });
        html += `</section>`;
    }

    if (doc.usage || (doc.examples || []).length) {
        html += `<section class="detail-section"><h2><i class="fas fa-bolt" aria-hidden="true"></i> Quick start</h2>`;
        if (doc.usage) html += `<pre class="code-block"><code>${escapeHtml(doc.usage)}</code></pre>`;
        (doc.examples || []).slice(0, 3).forEach((ex) => {
            html += `<div class="example-row">
                <pre class="code-block"><code>${escapeHtml(ex.cmd || '')}</code></pre>
                ${ex.explanation ? `<p class="example-note">${escapeHtml(ex.explanation)}</p>` : ''}
                <button type="button" class="copy-btn" data-copy="${escapeHtml(ex.cmd || '')}"><i class="fas fa-copy" aria-hidden="true"></i> Copy</button>
            </div>`;
        });
        html += `</section>`;
    }

    if ((doc.subcommands || []).length) {
        html += `<section class="detail-section"><h2>Subcommands</h2><ul class="subcommand-list">`;
        doc.subcommands.forEach((s) => {
            const name = typeof s === 'object' ? s.name : s;
            const desc = typeof s === 'object' ? (s.description || '') : '';
            html += `<li><code>${escapeHtml(name || '')}</code><span>${escapeHtml(desc)}</span></li>`;
        });
        html += `</ul></section>`;
    }

    if ((doc.flags || []).length) {
        html += `<section class="detail-section">
            <h2>Flags <span class="muted">(${doc.flags.length})</span></h2>
            <input type="search" class="flag-filter" id="panelFlagFilter" placeholder="Filter flags…" autocomplete="off">
            <div class="flags-table-wrap"><table class="flags-table" id="panelFlagsTable"><thead><tr><th>Flag</th><th>Description</th></tr></thead><tbody>`;
        doc.flags.forEach((f) => {
            const search = escapeHtml(`${f.name || ''} ${f.short || ''} ${f.description || ''} ${f.section || ''}`);
            html += `<tr data-flag-search="${search}">
                <td class="flag-names">${f.short ? `<code>${escapeHtml(f.short)}</code>` : ''}${f.name ? `<code>${escapeHtml(f.name)}</code>` : ''}${f.arg ? `<span class="flag-arg">${escapeHtml(f.arg)}</span>` : ''}</td>
                <td>${escapeHtml(f.description || '')}</td>
            </tr>`;
        });
        html += `</tbody></table></div></section>`;
    } else if (!doc.id) {
        html += `<section class="detail-section"><p class="muted">No structured docs yet for this tool. Tier 1 coverage is rolling out.</p></section>`;
    }

    html += `<section class="detail-section">
        <h2><i class="fas fa-magic" aria-hidden="true"></i> Command explainer</h2>
        <form class="explain-form" id="panelExplainForm" data-tool-id="${escapeHtml(tool.id || '')}">
            <input type="text" id="panelExplainInput" placeholder="Paste a command…" autocomplete="off" spellcheck="false">
            <button type="submit">Explain</button>
        </form>
        <div id="panelExplainResult" class="explain-result" hidden></div>
    </section>`;

    if ((doc.sources || []).length) {
        html += `<section class="detail-section"><h2>Sources</h2><ul class="source-list">${doc.sources.map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ul></section>`;
    }
    return html;
}

function wirePanelInteractions(root, toolId, doc) {
    root.querySelectorAll('.copy-btn').forEach((btn) => {
        btn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(btn.dataset.copy || '');
                const prev = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i>';
                setTimeout(() => { btn.innerHTML = prev; }, 1200);
            } catch (_) { /* ignore */ }
        });
    });
    const tabs = root.querySelectorAll('.install-tab');
    tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            tabs.forEach((t) => t.classList.remove('active'));
            root.querySelectorAll('.install-panel').forEach((p) => p.classList.remove('active'));
            tab.classList.add('active');
            const panel = root.querySelector('#' + tab.dataset.panel) || document.getElementById(tab.dataset.panel);
            if (panel) panel.classList.add('active');
        });
    });
    const filter = root.querySelector('#panelFlagFilter');
    const table = root.querySelector('#panelFlagsTable');
    if (filter && table) {
        filter.addEventListener('input', () => {
            const q = filter.value.trim().toLowerCase();
            table.querySelectorAll('tbody tr').forEach((row) => {
                const hay = (row.dataset.flagSearch || '').toLowerCase();
                row.hidden = q !== '' && !hay.includes(q);
            });
        });
    }
    const form = root.querySelector('#panelExplainForm');
    const result = root.querySelector('#panelExplainResult');
    if (form && result) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const command = (root.querySelector('#panelExplainInput') || {}).value || '';
            result.hidden = false;
            result.textContent = 'Explaining…';
            try {
                const resp = await fetch(`/api/tools/${encodeURIComponent(toolId)}/explain`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command }),
                });
                const data = await resp.json();
                if (!resp.ok) { result.textContent = data.error || 'Explain failed'; return; }
                result.innerHTML = (data.tokens || []).map((t) =>
                    `<div class="explain-token kind-${escapeHtml(t.kind || '')}"><code>${escapeHtml(t.token || '')}</code><span>${escapeHtml(t.note || '')}</span></div>`
                ).join('');
            } catch (_) {
                result.textContent = 'Network error';
            }
        });
    }
}


function displayResults(tools, reset = true) {
    // Ensure tools is an array
    if (!Array.isArray(tools)) {
        tools = [];
    }

    // Sort tools based on selected option (removed 'name' option)
    const sortBy = sortOptions ? sortOptions.value : 'relevance';
    let sortedTools = [...tools];

    switch(sortBy) {
        case 'category':
            sortedTools.sort((a, b) => `${a.category || ''}/${a.subcategory || ''}`.localeCompare(`${b.category || ''}/${b.subcategory || ''}`));
            break;
        // 'relevance' keeps original order (from search)
    }

    // Clear previous results on reset
    if (reset) {
        toolsGrid.innerHTML = '';
    }

    // Display message if no results
    if (sortedTools.length === 0 && reset) {
        toolsGrid.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search-minus" aria-hidden="true"></i>
                <h3>No Tools Found in Arsenal</h3>
                <p>No cybersecurity tools match your query. Try different keywords like:</p>
                <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
                    <button type="button" class="example-tag" onclick="document.getElementById('searchInput').value='scanner'; performSearch();">scanner</button>
                    <button type="button" class="example-tag" onclick="document.getElementById('searchInput').value='enumeration'; performSearch();">enumeration</button>
                    <button type="button" class="example-tag" onclick="document.getElementById('searchInput').value='exploit'; performSearch();">exploit</button>
                    <button type="button" class="example-tag" onclick="document.getElementById('searchInput').value='forensics'; performSearch();">forensics</button>
                </div>
            </div>
        `;
        return;
    }

    // Populate tools grid
    const fragment = document.createDocumentFragment();
    sortedTools.forEach((tool, index) => {
        const toolCard = document.createElement('div');
        toolCard.className = 'tool-card';

        toolCard.innerHTML = buildToolCardHtml(tool);

        // Add staggered animation
        toolCard.style.animationDelay = `${index * 0.1}s`;
        toolCard.style.animation = 'fadeInUp 0.6s ease forwards';
        toolCard.style.opacity = '0';

        fragment.appendChild(toolCard);
    });
    toolsGrid.appendChild(fragment);
    wireDocsButtons(toolsGrid);

    // Handle load more button
    updateLoadMoreButton();
}

// Append more results (load more)
function appendResults(tools) {
    const sortBy = sortOptions ? sortOptions.value : 'relevance';
    let sortedTools = [...tools];

    switch(sortBy) {
        case 'category':
            sortedTools.sort((a, b) => `${a.category || ''}/${a.subcategory || ''}`.localeCompare(`${b.category || ''}/${b.subcategory || ''}`));
            break;
    }

    const existingCards = toolsGrid.querySelectorAll('.tool-card').length;
    const fragment = document.createDocumentFragment();
    sortedTools.forEach((tool, index) => {
        const toolCard = document.createElement('div');
        toolCard.className = 'tool-card';

        toolCard.innerHTML = buildToolCardHtml(tool);

        toolCard.style.animationDelay = `${(existingCards + index) * 0.1}s`;
        toolCard.style.animation = 'fadeInUp 0.6s ease forwards';
        toolCard.style.opacity = '0';

        // Make the card focusable if it's the first appended item to manage focus
        if (index === 0) {
            toolCard.setAttribute('tabindex', '-1');
            toolCard.id = `appended-card-${existingCards}`;
        }

        fragment.appendChild(toolCard);
    });
    toolsGrid.appendChild(fragment);
    wireDocsButtons(toolsGrid);

    // Focus the first newly appended item for accessibility
    if (sortedTools.length > 0) {
        const firstNewCard = document.getElementById(`appended-card-${existingCards}`);
        if (firstNewCard) {
            firstNewCard.focus();
        }
    }

    updateLoadMoreButton();
}

// Update the load more button visibility
function updateLoadMoreButton() {
    // Remove existing load more button
    const existingBtn = document.querySelector('.load-more');
    if (existingBtn) {
        existingBtn.remove();
    }

    if (!currentHasMore) {
        return;
    }

    const loadMoreBtn = document.createElement('button');
    loadMoreBtn.className = 'load-more';
    loadMoreBtn.innerHTML = '<i class="fas fa-arrow-down" aria-hidden="true"></i> Load More Tools';
    loadMoreBtn.addEventListener('click', () => {
        loadMoreBtn.disabled = true;
        loadMoreBtn.style.opacity = '0.7';
        loadMoreBtn.style.cursor = 'not-allowed';
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Loading...';
        currentOffset += PAGE_LIMIT;
        performSearch(false);
    });
    toolsGrid.parentNode.appendChild(loadMoreBtn);
}

// Category + subcategory badges (all values escaped)
function categoryBadges(tool, categoryClass) {
    const main = (tool.category || '').toLowerCase();
    const label = main === 'general' ? 'General' : (main === 'security' ? 'Security' : 'Uncategorized');
    let html = `<span class="category ${main === 'general' ? 'general' : 'security'}">${escapeHtml(label)}</span>`;
    if (tool.subcategory) {
        html += ` <span class="category subcategory ${categoryClass}">${escapeHtml(tool.subcategory)}</span>`;
    }
    return `<span class="badges">${html}</span>`;
}

// Get category class for styling
function getCategoryClass(category) {
    if (!category) return '';
    const cat = category.toLowerCase();
    if (cat.includes('network')) return 'network';
    if (cat.includes('password')) return 'password';
    if (cat.includes('vulnerability') || cat.includes('vuln')) return 'vulnerability';
    if (cat.includes('forensic')) return 'forensics';
    if (cat.includes('web')) return 'web';
    return '';
}

// Show error with cybersecurity theme
function showError(message) {
    toolsGrid.innerHTML = `
        <div class="no-results">
            <i class="fas fa-exclamation-triangle" style="color: var(--danger);" aria-hidden="true"></i>
            <h3 style="color: var(--danger);">System Error</h3>
            <p>${escapeHtml(message)}</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle" aria-hidden="true"></i> Check network connection and try again
            </p>
        </div>
    `;
}

// Show alert function
function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.setAttribute('role', 'alert');
    alert.setAttribute('aria-live', 'assertive');
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'warning' ? 'rgba(255, 170, 0, 0.9)' : 'rgba(0, 255, 136, 0.9)'};
        color: var(--dark);
        padding: 15px 25px;
        border-radius: 10px;
        font-weight: 600;
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        border: 2px solid ${type === 'warning' ? '#ffaa00' : '#00ff88'};
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    `;
    alert.innerHTML = `<i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'}\" aria-hidden="true"></i> ${escapeHtml(message)}`;

    document.body.appendChild(alert);

    // Remove after 3 seconds
    setTimeout(() => {
        alert.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

// Add slide animations for alerts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// ── Initialize ───────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
    // Ensure all elements exist before setting up
    if (resultsContainer) {
        resultsContainer.style.display = 'block';
    }

    // Add typing effect to search input
    if (searchInput) {
        const shortcutHint = document.getElementById('shortcutHint');

        searchInput.addEventListener('input', (e) => {
            e.target.removeAttribute('aria-invalid');
            if (e.target.value.length > 0) {
                e.target.style.borderColor = 'rgba(0, 255, 136, 0.5)';
                if (shortcutHint) shortcutHint.classList.add('hidden');
            } else {
                e.target.style.borderColor = 'var(--border)';
                if (shortcutHint) shortcutHint.classList.remove('hidden');
            }
        });

        // Add terminal-like focus effects
        searchInput.addEventListener('focus', () => {
            searchInput.parentElement.style.transform = 'scale(1.02)';
        });

        searchInput.addEventListener('blur', () => {
            searchInput.parentElement.style.transform = 'scale(1)';
        });

        document.addEventListener('keydown', (e) => {
            const activeTag = document.activeElement ? document.activeElement.tagName : '';
            if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(activeTag)) {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }


    const docsClose = document.getElementById('docsPanelClose');
    const docsBackdrop = document.getElementById('docsBackdrop');
    if (docsClose) docsClose.addEventListener('click', closeDocsPanel);
    if (docsBackdrop) docsBackdrop.addEventListener('click', closeDocsPanel);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeDocsPanel();
    });

    // Optionally check backend health silently on page load
    checkBackendHealth().then(healthy => {
        if (!healthy) {
            console.warn('[ToolHunt] Backend health check failed — searches may fail');
        }
    });
});
