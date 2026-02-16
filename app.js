// Initialize Lucide icons
lucide.createIcons();

// Supabase Configuration
const SUPABASE_URL = 'https://irtvdtwhvoaxhhflerhp.supabase.co';
const SUPABASE_KEY = 'sb_publishable_1tHVs0poyOY9PcNS9ylTlw_Jk6nlJb2';
const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

const GRID = document.getElementById('articles-grid');
const REFRESH_BTN = document.getElementById('refresh-btn');
const LAST_UPDATED = document.getElementById('last-updated');
const FILTER_BTNS = document.querySelectorAll('.filter-btn');

// Auth Elements
const LOGIN_BTN = document.getElementById('login-btn');
const LOGOUT_BTN = document.getElementById('logout-btn');
const AUTH_MODAL = document.getElementById('auth-modal');
const AUTH_FORM = document.getElementById('auth-form');
const AUTH_TABS = document.querySelectorAll('.auth-tab');
const USER_PROFILE = document.getElementById('user-profile');
const USERNAME_DISPLAY = document.getElementById('username-display');

// Social Elements
const SIDEBAR = document.getElementById('social-sidebar');
const COMMENTS_LIST = document.getElementById('comments-container');
const COMMENT_INPUT = document.getElementById('comment-input');
const SUBMIT_COMMENT = document.getElementById('submit-comment');

let allArticles = [];
let savedArticleIds = new Set();
let currentUser = null;
let currentArticleId = null;

// --- Auth Logic ---
async function checkUser() {
    const { data: { user } } = await supabaseClient.auth.getUser();
    currentUser = user;
    if (user) {
        LOGIN_BTN.style.display = 'none';
        USER_PROFILE.style.display = 'flex';
        USERNAME_DISPLAY.innerText = user.user_metadata.username || user.email.split('@')[0];
    } else {
        LOGIN_BTN.style.display = 'block';
        USER_PROFILE.style.display = 'none';
    }
}

LOGIN_BTN.onclick = () => AUTH_MODAL.style.display = 'flex';
document.getElementById('close-modal').onclick = () => AUTH_MODAL.style.display = 'none';

AUTH_TABS.forEach(tab => {
    tab.onclick = () => {
        AUTH_TABS.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('signup-fields').style.display = tab.dataset.tab === 'signup' ? 'block' : 'none';
        document.getElementById('auth-submit').innerText = tab.dataset.tab === 'signup' ? 'Register' : 'Connect';
    };
});

AUTH_FORM.onsubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const isSignUp = document.querySelector('.auth-tab.active').dataset.tab === 'signup';

    let result;
    if (isSignUp) {
        const username = document.getElementById('auth-username').value;
        result = await supabaseClient.auth.signUp({
            email,
            password,
            options: { data: { username } }
        });
    } else {
        result = await supabaseClient.auth.signInWithPassword({ email, password });
    }

    if (result.error) {
        document.getElementById('auth-error').innerText = result.error.message;
    } else {
        AUTH_MODAL.style.display = 'none';
        checkUser();
    }
};

LOGOUT_BTN.onclick = async () => {
    await supabaseClient.auth.signOut();
    checkUser();
};

// --- Data Loading ---
async function loadData() {
    try {
        const { data, error } = await supabaseClient
            .from('articles')
            .select('*')
            .order('published_at', { ascending: false });

        if (error) throw error;

        allArticles = data;

        // Load saved IDs if user is logged in
        if (currentUser) {
            const { data: savedData } = await supabaseClient
                .from('user_saved_articles')
                .select('article_id')
                .eq('user_id', currentUser.id);
            savedArticleIds = new Set(savedData?.map(s => s.article_id) || []);
        }

        renderArticles(allArticles);
        LAST_UPDATED.innerText = `Uplink Active: ${new Date().toLocaleTimeString()}`;
    } catch (error) {
        console.error("Failed to load data:", error);
        GRID.innerHTML = `<div class="loading-state"><p>Satellite connection lost. Retrying...</p></div>`;
    }
}

function renderArticles(articles) {
    if (!articles || articles.length === 0) {
        GRID.innerHTML = `
            <div class="loading-state">
                <i data-lucide="alert-triangle" style="width: 48px; height: 48px; margin-bottom: 1rem; color: var(--accent-sec);"></i>
                <p>No signal detected in this sector.</p>
                <p style="font-size: 1rem; margin-top: 1rem; color: var(--text-muted);">The scraper may need a manual kickstart.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    GRID.innerHTML = '';
    articles.forEach(article => {
        const card = document.createElement('div');
        card.className = 'card';

        const date = new Date(article.published_at);
        const timeAgo = getTimeAgo(date);

        const imageHtml = article.image_url
            ? `<div class="card-image" style="background-image: url('${article.image_url}');"></div>`
            : `<div class="card-image placeholder"><span>AI</span></div>`;

        const isSaved = savedArticleIds.has(article.id);

        card.innerHTML = `
            ${imageHtml}
            <div class="card-content">
                <div class="card-meta">
                    <span class="source-tag">${article.source.toUpperCase()}</span>
                    <span class="date">${timeAgo}</span>
                </div>
                <h3 class="card-title">
                    <a href="${article.url}" target="_blank">${article.title}</a>
                </h3>
                <div class="card-footer">
                    <div class="social-actions">
                        <div class="social-indicator" onclick="openSocial('${article.id}', '${article.title}')">
                            <i data-lucide="message-square"></i>
                            <span>${article.comment_count || 0}</span>
                        </div>
                        <button class="save-btn ${isSaved ? 'saved' : ''}" onclick="toggleSave('${article.id}')">
                            <i data-lucide="heart"></i>
                        </button>
                    </div>
                    <a href="${article.url}" target="_blank" class="read-link">Read &rarr;</a>
                </div>
            </div>
        `;
        GRID.appendChild(card);
    });
    lucide.createIcons();
}

async function toggleSave(articleId) {
    if (!currentUser) return alert("Uplink required to save archives.");

    if (savedArticleIds.has(articleId)) {
        await supabaseClient.from('user_saved_articles').delete().eq('user_id', currentUser.id).eq('article_id', articleId);
        savedArticleIds.delete(articleId);
    } else {
        await supabaseClient.from('user_saved_articles').insert({ user_id: currentUser.id, article_id: articleId });
        savedArticleIds.add(articleId);
    }

    const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
    applyFilter(activeFilter);
}

function applyFilter(filter) {
    let filtered = allArticles;
    if (filter === 'saved') {
        filtered = allArticles.filter(a => savedArticleIds.has(a.id));
    } else if (filter !== 'all') {
        filtered = allArticles.filter(a => a.source === filter);
    }
    renderArticles(filtered);
}

// --- Social System ---
async function openSocial(articleId, title) {
    currentArticleId = articleId;
    document.getElementById('sidebar-title').innerText = title;
    SIDEBAR.classList.add('open');
    loadComments(articleId);
}

document.getElementById('close-sidebar').onclick = () => SIDEBAR.classList.remove('open');

async function loadComments(articleId) {
    COMMENTS_LIST.innerHTML = '<p>Retrieving logs...</p>';
    const { data, error } = await supabaseClient
        .from('comments')
        .select('*, profiles(username)')
        .eq('article_id', articleId)
        .order('created_at', { ascending: true });

    if (error) return;

    COMMENTS_LIST.innerHTML = data.length ? '' : '<p>No data found in this sector.</p>';
    data.forEach(comment => {
        const div = document.createElement('div');
        div.className = 'comment-item';
        div.innerHTML = `
            <div class="comment-header">
                <span class="comment-user">${comment.profiles?.username || 'Unknown Agent'}</span>
                <span class="comment-date">${getTimeAgo(new Date(comment.created_at))}</span>
            </div>
            <div class="comment-content">${comment.content}</div>
        `;
        COMMENTS_LIST.appendChild(div);
    });
}

SUBMIT_COMMENT.onclick = async () => {
    if (!currentUser) return alert("You must uplink (login) to post updates.");
    const content = COMMENT_INPUT.value.trim();
    if (!content) return;

    const { error } = await supabaseClient.from('comments').insert({
        article_id: currentArticleId,
        user_id: currentUser.id,
        content: content
    });

    if (!error) {
        COMMENT_INPUT.value = '';
        loadComments(currentArticleId);
    }
};

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return "just now";
    let interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + "h ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + "m ago";
    return Math.floor(seconds) + "s ago";
}

// --- Global Initialization ---
checkUser();
loadData();

// Refresh and Filters
REFRESH_BTN.onclick = loadData;
FILTER_BTNS.forEach(btn => {
    btn.onclick = (e) => {
        FILTER_BTNS.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        applyFilter(e.target.dataset.filter);
    };
});
