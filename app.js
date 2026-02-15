// Initialize Lucide icons
lucide.createIcons();

const DATA_URL = 'data/storage.json';
const GRID = document.getElementById('articles-grid');
const REFRESH_BTN = document.getElementById('refresh-btn');
const LAST_UPDATED = document.getElementById('last-updated');
const FILTER_BTNS = document.querySelectorAll('.filter-btn');

let allArticles = [];
let savedArticles = JSON.parse(localStorage.getItem('savedArticles') || '[]');

async function loadData() {
    try {
        // fetching from stored global variable (loaded via <script src="data/data.js">)
        const data = window.DASHBOARD_DATA;

        if (!data) {
            throw new Error("No data found. Is data/data.js loaded?");
        }

        allArticles = data.articles || [];
        // Merge with local saved state just in case
        allArticles.forEach(a => {
            if (savedArticles.includes(a.id)) {
                a.is_saved = true;
            }
        });

        updateTimestamp(data.last_updated);
        renderArticles(allArticles);
    } catch (error) {
        console.error("Failed to load data:", error);
        GRID.innerHTML = `<div class="loading-state"><p>Error loading data. Ensure data/data.js exists.</p></div>`;
    }
}

function updateTimestamp(isoString) {
    if (!isoString) return;
    const date = new Date(isoString);
    LAST_UPDATED.innerText = `Updated: ${date.toLocaleTimeString()}`;
}

function renderArticles(articles) {
    GRID.innerHTML = '';

    if (articles.length === 0) {
        GRID.innerHTML = `<div class="loading-state"><p>No articles found for this filter.</p></div>`;
        return;
    }

    articles.forEach(article => {
        const card = document.createElement('div');
        card.className = 'card';
        const isSaved = savedArticles.includes(article.id);

        // Format Date
        const date = new Date(article.published_at);
        const timeAgo = getTimeAgo(date);

        // Visual Source Name
        let sourceName = article.source;
        if (sourceName === 'theverge') sourceName = 'The Verge';
        if (sourceName === 'wired') sourceName = 'Wired';
        if (sourceName === 'techcrunch') sourceName = 'TechCrunch';
        if (sourceName === 'therundown') sourceName = 'The Rundown';

        // Image Logic
        let imageHtml = '';
        if (article.image_url) {
            imageHtml = `<div class="card-image" style="background-image: url('${article.image_url}');"></div>`;
        } else {
            // Placeholder Pattern
            imageHtml = `<div class="card-image placeholder"><span>AI</span></div>`;
        }

        card.innerHTML = `
            ${imageHtml}
            <div class="card-content">
                <div class="card-meta">
                    <span class="source-tag">${sourceName}</span>
                    <span class="date">${timeAgo}</span>
                </div>
                <h3 class="card-title">
                    <a href="${article.url}" target="_blank">${article.title}</a>
                </h3>
                <div class="card-footer">
                    <button class="save-btn ${isSaved ? 'saved' : ''}" onclick="toggleSave('${article.id}')">
                        <i data-lucide="heart"></i>
                    </button>
                    <a href="${article.url}" target="_blank" class="read-link">Read Case Study &rarr;</a>
                </div>
            </div>
        `;
        GRID.appendChild(card);
    });

    // Re-init icons for new DOM elements
    lucide.createIcons();
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    let interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + "h ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + "m ago";
    return Math.floor(seconds) + "s ago";
}

window.toggleSave = function (id) {
    const index = savedArticles.indexOf(id);
    if (index === -1) {
        savedArticles.push(id);
    } else {
        savedArticles.splice(index, 1);
    }
    localStorage.setItem('savedArticles', JSON.stringify(savedArticles));

    // Update UI state immediately without full re-render
    // But for filter consistency, we might want to re-render if in "Saved" view
    // For now, just reload data merge to keep it simple
    loadData().then(() => {
        // Re-apply current filter
        const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
        applyFilter(activeFilter);
    });
}

function applyFilter(filter) {
    let filtered = allArticles;
    if (filter === 'saved') {
        filtered = allArticles.filter(a => savedArticles.includes(a.id));
    } else if (filter !== 'all') {
        filtered = allArticles.filter(a => a.source === filter);
    }
    renderArticles(filtered);
}

// Event Listeners
REFRESH_BTN.addEventListener('click', loadData);

FILTER_BTNS.forEach(btn => {
    btn.addEventListener('click', (e) => {
        // UI
        FILTER_BTNS.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');

        // Logic
        applyFilter(e.target.dataset.filter);
    });
});

// Init
loadData();
