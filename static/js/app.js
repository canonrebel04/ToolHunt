// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
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
searchButton.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

exampleTags.forEach(tag => {
    tag.addEventListener('click', () => {
        const tagText = tag.textContent.trim();
        // Remove icon and extract just the text
        const cleanText = tagText.split(' ').slice(1).join(' ');
        searchInput.value = cleanText;
        performSearch();
    });
});

sortOptions.addEventListener('change', () => {
    const query = searchInput.value.trim();
    if (query && toolsGrid.children.length > 0 && !toolsGrid.querySelector('.no-results')) {
        performSearch(); // Re-search with current query to re-sort
    }
});

// ── Search Function with retry, abort, timeout ───────────────────────

function performSearch(resetOffset = true) {
    const query = searchInput.value.trim();

    if (!query) {
        showAlert('Please enter a search query to hunt for tools', 'warning');
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

    // Show loading indicator
    loadingIndicator.style.display = 'block';
    loadingIndicator.querySelector('h3').textContent = 'Scanning Arsenal...';
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
        showTimeoutError();
    }, FETCH_TIMEOUT_MS);

    // Build the request body and store for retry
    const body = JSON.stringify({
        query: currentQuery,
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
            resultsCount.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Search failed`;
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
            <i class="fas fa-exclamation-triangle" style="color: var(--danger);"></i>
            <h3 style="color: var(--danger);">Connection Error</h3>
            <p>${message}</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle"></i> Retry attempt ${attempt} of ${MAX_RETRIES}
            </p>
            <button class="retry-btn" onclick="retrySearch()">
                <i class="fas fa-sync-alt"></i> Retry Search
            </button>
            ${remaining > 0 ? `<p style="margin-top: 8px; font-size: 0.8rem; color: var(--gray);">${remaining} retr${remaining !== 1 ? 'ies' : 'y'} remaining</p>` : ''}
        </div>
    `;
}

function showTimeoutError() {
    toolsGrid.innerHTML = `
        <div class="no-results error-state">
            <i class="fas fa-hourglass-end" style="color: var(--warning);"></i>
            <h3 style="color: var(--warning);">Request Timed Out</h3>
            <p>The search request took too long to respond (over ${FETCH_TIMEOUT_MS / 1000} seconds).</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle"></i> The backend may be overloaded or unreachable
            </p>
            <button class="retry-btn" onclick="retrySearch()">
                <i class="fas fa-sync-alt"></i> Retry Search
            </button>
        </div>
    `;
    resultsContainer.style.display = 'block';
    if (resultsCount) {
        resultsCount.innerHTML = `<i class="fas fa-hourglass-end"></i> Request timed out`;
    }
}

function showOfflineFallback() {
    toolsGrid.innerHTML = `
        <div class="no-results error-state offline-fallback">
            <i class="fas fa-wifi-slash" style="color: var(--gray);"></i>
            <h3 style="color: var(--gray);">Offline Mode</h3>
            <p>The backend is currently unavailable after ${MAX_RETRIES} retry attempts.</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle"></i> Try browsing by category below:
            </p>
            <div class="fallback-categories">
                ${FALLBACK_CATEGORIES.map(cat => `
                    <div class="fallback-category-tile" data-category="${cat.query}" style="--cat-color: ${cat.color};">
                        <i class="fas ${cat.icon}"></i>
                        <span>${cat.name}</span>
                    </div>
                `).join('')}
            </div>
            <button class="retry-btn retry-btn-primary" onclick="retrySearch()">
                <i class="fas fa-sync-alt"></i> Try Again
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
        resultsCount.innerHTML = `<i class="fas fa-search-minus"></i> No tools found in arsenal`;
        return;
    }
    const shown = toolsGrid.querySelectorAll('.tool-card').length;
    if (shown === currentTotal) {
        resultsCount.innerHTML = `<i class="fas fa-crosshairs"></i> Showing all ${currentTotal} cybersecurity tool${currentTotal !== 1 ? 's' : ''} in arsenal`;
    } else {
        const from = currentOffset + 1;
        const to = currentOffset + shown;
        resultsCount.innerHTML = `<i class="fas fa-crosshairs"></i> Showing ${from}-${to} of ${currentTotal} cybersecurity tool${currentTotal !== 1 ? 's' : ''} in arsenal`;
    }
}

// Display Results (initial or refreshed)
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
            sortedTools.sort((a, b) => (a.category || 'Uncategorized').localeCompare(b.category || 'Uncategorized'));
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
                <i class="fas fa-search-minus"></i>
                <h3>No Tools Found in Arsenal</h3>
                <p>No cybersecurity tools match your query. Try different keywords like:</p>
                <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
                    <span style="background: rgba(0, 255, 136, 0.1); padding: 8px 15px; border-radius: 15px; font-size: 0.9rem;">• scanner • enumeration • exploit • forensics •</span>
                </div>
            </div>
        `;
        return;
    }

    // Populate tools grid
    sortedTools.forEach((tool, index) => {
        const toolCard = document.createElement('div');
        toolCard.className = 'tool-card';

        // Determine category class for styling
        const categoryClass = getCategoryClass(tool.category);

        toolCard.innerHTML = `
            <div class="card-header">
                <h3>${tool.name || 'Unknown Tool'}</h3>
                <span class="category ${categoryClass}">${tool.category || 'Uncategorized'}</span>
            </div>
            <div class="card-body">
                <p>${tool.description || 'No description available'}</p>
            </div>
            <div class="card-footer">
                <a href="${tool.link || '#'}" target="_blank" rel="noopener noreferrer" class="tool-link" ${!tool.link ? 'tabindex="-1" aria-disabled="true" style="opacity: 0.5; pointer-events: none;"' : `aria-label="Access ${tool.name || 'Unknown Tool'} (opens in new tab)"`}>
                    <i class="fas fa-external-link-alt"></i> ${tool.link ? 'Access Tool' : 'No Link Available'}
                </a>
            </div>
        `;

        // Add staggered animation
        toolCard.style.animationDelay = `${index * 0.1}s`;
        toolCard.style.animation = 'fadeInUp 0.6s ease forwards';
        toolCard.style.opacity = '0';

        toolsGrid.appendChild(toolCard);
    });

    // Handle load more button
    updateLoadMoreButton();
}

// Append more results (load more)
function appendResults(tools) {
    const sortBy = sortOptions ? sortOptions.value : 'relevance';
    let sortedTools = [...tools];

    switch(sortBy) {
        case 'category':
            sortedTools.sort((a, b) => (a.category || 'Uncategorized').localeCompare(b.category || 'Uncategorized'));
            break;
    }

    const existingCards = toolsGrid.querySelectorAll('.tool-card').length;
    sortedTools.forEach((tool, index) => {
        const toolCard = document.createElement('div');
        toolCard.className = 'tool-card';

        const categoryClass = getCategoryClass(tool.category);

        toolCard.innerHTML = `
            <div class="card-header">
                <h3>${tool.name || 'Unknown Tool'}</h3>
                <span class="category ${categoryClass}">${tool.category || 'Uncategorized'}</span>
            </div>
            <div class="card-body">
                <p>${tool.description || 'No description available'}</p>
            </div>
            <div class="card-footer">
                <a href="${tool.link || '#'}" target="_blank" rel="noopener noreferrer" class="tool-link" ${!tool.link ? 'tabindex="-1" aria-disabled="true" style="opacity: 0.5; pointer-events: none;"' : `aria-label="Access ${tool.name || 'Unknown Tool'} (opens in new tab)"`}>
                    <i class="fas fa-external-link-alt"></i> ${tool.link ? 'Access Tool' : 'No Link Available'}
                </a>
            </div>
        `;

        toolCard.style.animationDelay = `${(existingCards + index) * 0.1}s`;
        toolCard.style.animation = 'fadeInUp 0.6s ease forwards';
        toolCard.style.opacity = '0';

        toolsGrid.appendChild(toolCard);
    });

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
    loadMoreBtn.innerHTML = '<i class="fas fa-arrow-down"></i> Load More Tools';
    loadMoreBtn.addEventListener('click', () => {
        currentOffset += PAGE_LIMIT;
        performSearch(false);
    });
    toolsGrid.parentNode.appendChild(loadMoreBtn);
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
            <i class="fas fa-exclamation-triangle" style="color: var(--danger);"></i>
            <h3 style="color: var(--danger);">System Error</h3>
            <p>${message}</p>
            <p style="margin-top: 15px; font-size: 0.9rem; color: var(--gray);">
                <i class="fas fa-info-circle"></i> Check network connection and try again
            </p>
        </div>
    `;
}

// Show alert function
function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
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
    alert.innerHTML = `<i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'}\"></i> ${message}`;

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
        searchInput.addEventListener('input', (e) => {
            if (e.target.value.length > 0) {
                e.target.style.borderColor = 'rgba(0, 255, 136, 0.5)';
            } else {
                e.target.style.borderColor = 'var(--border)';
            }
        });

        // Add terminal-like focus effects
        searchInput.addEventListener('focus', () => {
            searchInput.parentElement.style.transform = 'scale(1.02)';
        });

        searchInput.addEventListener('blur', () => {
            searchInput.parentElement.style.transform = 'scale(1)';
        });
    }

    // Optionally check backend health silently on page load
    checkBackendHealth().then(healthy => {
        if (!healthy) {
            console.warn('[ToolHunt] Backend health check failed — searches may fail');
        }
    });
});
