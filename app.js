// ==========================================
// 이곳에 아까 구글 시트에서 복사한 웹 앱 URL을 붙여넣으세요!
const WEB_APP_URL = "https://script.google.com/macros/s/AKfycby-4JCXDGA50bcQOsHeVUokOa75erd_gqUun7IeiLgik3ZgDAgjNEO5zC-Zf11YV3XHyQ/exec";
// ==========================================

let galleryData = [];
let activeFilter = 'all';
let successOnly = false;
let currentBase64Image = null;

// DOM Elements
const galleryGrid = document.getElementById('galleryGrid');
const loaderContainer = document.getElementById('loaderContainer');
const categoryFilter = document.getElementById('categoryFilter');

const themeToggleBtn = document.getElementById('themeToggleBtn');
const openAddModalBtn = document.getElementById('openAddModalBtn');
const addModal = document.getElementById('addModal');
const detailModal = document.getElementById('detailModal');

// Init
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    fetchGalleryData();
    setupEventListeners();
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    themeToggleBtn.textContent = isDark ? '☀️' : '🌙';
}

themeToggleBtn.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeToggleBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
});

// Fetch Data from Google Apps Script
async function fetchGalleryData() {
    try {
        loaderContainer.classList.remove('hidden');
        galleryGrid.innerHTML = '';

        const response = await fetch(WEB_APP_URL);
        const data = await response.json();

        galleryData = data;
        renderFilters();
        renderGallery();
    } catch (error) {
        console.error('Error fetching data:', error);
        loaderContainer.innerHTML = '<p style="color:var(--accent)">데이터를 불러오는데 실패했습니다. URL을 확인해 주세요.</p>';
    }
}

// Render Filters
function renderFilters() {
    // Extract unique categories
    const categories = [...new Set(galleryData.map(item => item.category))].filter(Boolean);

    let filterHtml = `<button class="filter-btn active" data-filter="all">전체보기</button>`;
    categories.forEach(cat => {
        filterHtml += `<button class="filter-btn" data-filter="${cat}">${cat}</button>`;
    });

    categoryFilter.innerHTML = filterHtml;

    // Bind events
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            activeFilter = e.target.getAttribute('data-filter');
            renderGallery();
        });
    });
}

// Render Gallery
function renderGallery() {
    loaderContainer.classList.add('hidden');

    let filteredData = activeFilter === 'all'
        ? galleryData
        : galleryData.filter(item => item.category === activeFilter);

    if (successOnly) {
        filteredData = filteredData.filter(item => item.status !== 'fail');
    }

    if (filteredData.length === 0) {
        galleryGrid.innerHTML = '<p style="color:var(--text-muted); padding:2rem;">표시할 프롬프트가 없습니다.</p>';
        return;
    }

    let html = '';
    filteredData.forEach((item, index) => {
        // 보안 정책 때문에 깨지는 구글 드라이브 원본 링크 대신, 공식 썸네일 API로 우회 변환
        let imgUrl = item.url;
        if (imgUrl && imgUrl.includes('/uc?id=')) {
            const fileId = imgUrl.split('id=')[1];
            imgUrl = `https://drive.google.com/thumbnail?id=${fileId}&sz=w1000`;
        }

        const isFail = item.status === 'fail';
        html += `
            <div class="gallery-item${isFail ? ' is-fail' : ''}" data-index="${galleryData.indexOf(item)}">
                <span class="item-badge">${item.category}</span>
                <span class="status-badge ${isFail ? 'fail' : 'success'}"></span>
                ${item.thinking ? `<span class="has-thinking-badge">🧠 AI분석</span>` : ''}
                <img src="${imgUrl}" alt="${item.category}" class="item-img" loading="lazy" referrerpolicy="no-referrer">
            </div>
        `;


    });

    galleryGrid.innerHTML = html;

    // Bind click to open detail
    document.querySelectorAll('.gallery-item').forEach(item => {
        item.addEventListener('click', () => {
            const index = item.getAttribute('data-index');
            openDetailModal(galleryData[index]);
        });
    });
}

// Modal Magement
function setupEventListeners() {
    // Open Add Modal
    openAddModalBtn.addEventListener('click', () => {
        addModal.classList.add('open');
    });

    // Success toggle
    document.getElementById('successOnlyToggle').addEventListener('change', (e) => {
        successOnly = e.target.checked;
        renderGallery();
    });

    // Close Modals
    document.getElementById('closeDetailBtn').addEventListener('click', () => detailModal.classList.remove('open'));
    document.getElementById('detailOverlay').addEventListener('click', () => detailModal.classList.remove('open'));

    document.getElementById('closeAddBtn').addEventListener('click', () => closeAddModal());
    document.getElementById('addOverlay').addEventListener('click', () => closeAddModal());

    function closeAddModal() {
        addModal.classList.remove('open');
        document.getElementById('addForm').reset();
        removeImage();
        document.getElementById('customCategoryInput').classList.add('hidden');
    }

    // Detail - Copy Prompt
    document.getElementById('copyPromptBtn').addEventListener('click', () => {
        const promptText = document.getElementById('detailPrompt').value;
        navigator.clipboard.writeText(promptText).then(() => {
            const feedback = document.getElementById('copyFeedback');
            feedback.style.opacity = '1';
            setTimeout(() => feedback.style.opacity = '0', 2000);
        });
    });

    // Detail - Copy Thinking
    document.getElementById('copyThinkingBtn').addEventListener('click', () => {
        const thinkingText = document.getElementById('detailThinking').value;
        navigator.clipboard.writeText(thinkingText).then(() => {
            const feedback = document.getElementById('copyThinkingFeedback');
            feedback.style.opacity = '1';
            setTimeout(() => feedback.style.opacity = '0', 2000);
        });
    });

    // Add Form - Category selection
    const categorySelect = document.getElementById('categorySelect');
    const customCategoryInput = document.getElementById('customCategoryInput');

    categorySelect.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
            customCategoryInput.classList.remove('hidden');
            customCategoryInput.setAttribute('required', 'true');
            customCategoryInput.focus();
        } else {
            customCategoryInput.classList.add('hidden');
            customCategoryInput.removeAttribute('required');
        }
    });

    // Image Upload Handlers
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag & Drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    document.getElementById('removeImgBtn').addEventListener('click', (e) => {
        e.stopPropagation();
        removeImage();
    });

    // Handle Form Submit
    document.getElementById('addForm').addEventListener('submit', handleFormSubmit);

    // Edit and Delete Handlers
    document.getElementById('startEditBtn').addEventListener('click', () => {
        document.getElementById('detailViewMode').classList.add('hidden');
        document.getElementById('detailActions').classList.add('hidden');
        document.getElementById('detailEditMode').classList.remove('hidden');

        document.getElementById('editCategoryInput').value = currentViewItem.category || '';
        document.getElementById('editTitleInput').value = currentViewItem.title || '';
        document.getElementById('editPromptInput').value = currentViewItem.prompt || '';
        document.getElementById('editThinkingInput').value = currentViewItem.thinking || '';
        document.getElementById('editAnalysisInput').value = currentViewItem.analysis || '';

        const statusVal = currentViewItem.status === 'fail' ? 'fail' : 'success';
        const radio = document.querySelector(`input[name="editStatusRadios"][value="${statusVal}"]`);
        if (radio) radio.checked = true;
    });

    document.getElementById('cancelEditBtn').addEventListener('click', () => {
        document.getElementById('detailViewMode').classList.remove('hidden');
        document.getElementById('detailActions').classList.remove('hidden');
        document.getElementById('detailEditMode').classList.add('hidden');
    });

    document.getElementById('detailEditMode').addEventListener('submit', handleEditSubmit);
    document.getElementById('deletePostBtn').addEventListener('click', handleDeletePost);
}

let currentViewItem = null;

async function handleEditSubmit(e) {
    e.preventDefault();
    if (!currentViewItem) return;

    const submitBtn = document.getElementById('saveEditBtn');
    const btnText = document.getElementById('editBtnText');

    submitBtn.disabled = true;
    btnText.textContent = '저장 중...';

    try {
        const status = document.querySelector('input[name="editStatusRadios"]:checked').value;

        const formData = new URLSearchParams();
        formData.append("action", "edit");
        formData.append("fileId", currentViewItem.id);
        formData.append("category", document.getElementById('editCategoryInput').value.trim());
        formData.append("title", document.getElementById('editTitleInput').value.trim());
        formData.append("prompt", document.getElementById('editPromptInput').value.trim());
        formData.append("status", status);
        formData.append("thinking", document.getElementById('editThinkingInput').value.trim());
        formData.append("analysis", document.getElementById('editAnalysisInput').value.trim());

        const response = await fetch(WEB_APP_URL, {
            method: 'POST',
            body: formData,
        });

        const result = await response.json();

        if (result.success) {
            showToast("수정되었습니다.");
            document.getElementById('closeDetailBtn').click();
            fetchGalleryData();
        } else {
            alert('수정 실패: ' + result.error);
        }
    } catch (error) {
        console.error('Edit Error:', error);
        alert('네트워크 오류가 발생했습니다.');
    } finally {
        submitBtn.disabled = false;
        btnText.textContent = '수정 완료';
    }
}

async function handleDeletePost() {
    if (!currentViewItem) return;
    if (!confirm('정말 이 게시물을 삭제하시겠습니까? (복구할 수 없습니다)')) return;

    const btn = document.getElementById('deletePostBtn');
    const orgText = btn.textContent;
    btn.textContent = '⏳';
    document.getElementById('startEditBtn').classList.add('hidden');

    try {
        const formData = new URLSearchParams();
        formData.append("action", "delete");
        formData.append("fileId", currentViewItem.id);

        const response = await fetch(WEB_APP_URL, {
            method: 'POST',
            body: formData,
        });

        const result = await response.json();

        if (result.success) {
            showToast("삭제되었습니다.");
            document.getElementById('closeDetailBtn').click();
            fetchGalleryData();
        } else {
            alert('삭제 실패: ' + result.error);
        }
    } catch (error) {
        console.error('Delete Error:', error);
        alert('네트워크 오류가 발생했습니다.');
    } finally {
        btn.textContent = orgText;
        document.getElementById('startEditBtn').classList.remove('hidden');
    }
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('이미지 파일만 업로드 가능합니다.');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        currentBase64Image = e.target.result;

        document.getElementById('imagePreview').src = currentBase64Image;
        document.getElementById('imagePreview').classList.remove('hidden');
        document.getElementById('removeImgBtn').classList.remove('hidden');
        document.getElementById('uploadPrompt').classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    currentBase64Image = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('imagePreview').classList.add('hidden');
    document.getElementById('removeImgBtn').classList.add('hidden');
    document.getElementById('uploadPrompt').classList.remove('hidden');
}

async function handleFormSubmit(e) {
    e.preventDefault();

    if (!currentBase64Image) {
        alert('이미지를 등록해주세요.');
        return;
    }

    const categorySelectVal = document.getElementById('categorySelect').value;
    const category = categorySelectVal === 'custom'
        ? document.getElementById('customCategoryInput').value.trim()
        : categorySelectVal;

    const title = document.getElementById('titleInput').value.trim();
    const prompt = document.getElementById('promptInput').value.trim();
    const status = document.querySelector('input[name="statusRadios"]:checked').value;

    // Prepare UI for loading
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('submitSpinner');

    submitBtn.disabled = true;
    btnText.textContent = '클라우드 업로드 중...';
    spinner.classList.remove('hidden');

    try {
        const formData = new URLSearchParams();
        formData.append("action", "upload");
        formData.append("base64", currentBase64Image);
        formData.append("mimeType", "image/png");
        formData.append("filename", `prompt_${Date.now()}.png`);
        formData.append("category", category);
        formData.append("title", title);
        formData.append("prompt", prompt);
        formData.append("status", document.querySelector('input[name="statusRadios"]:checked').value);
        formData.append("thinking", document.getElementById('thinkingInput').value.trim());
        formData.append("analysis", document.getElementById('analysisInput').value.trim());

        const response = await fetch(WEB_APP_URL, {
            method: 'POST',
            body: formData,
            // Mode no-cors is NOT used here because application/x-www-form-urlencoded is a simple request
        });

        const result = await response.json();

        if (result.success) {
            showToast("저장되었습니다.");
            document.getElementById('closeAddBtn').click();
            // Refresh data
            fetchGalleryData();
        } else {
            alert('오류 발생: ' + result.error);
        }
    } catch (error) {
        console.error('Upload Error:', error);
        alert('업로드 중 네트워크 오류가 발생했습니다. (CORS 문제가 발생했다면 Apps Script가 모든 사용자 권한으로 배포되었는지 확인하세요)');
    } finally {
        submitBtn.disabled = false;
        btnText.textContent = '클라우드에 저장하기';
        spinner.classList.add('hidden');
    }
}

function openDetailModal(item) {
    currentViewItem = item;

    // Reset view modes
    document.getElementById('detailViewMode').classList.remove('hidden');
    document.getElementById('detailEditMode').classList.add('hidden');
    document.getElementById('detailActions').classList.remove('hidden');

    let imgUrl = item.url;
    if (imgUrl && imgUrl.includes('/uc?id=')) {
        const fileId = imgUrl.split('id=')[1];
        imgUrl = `https://drive.google.com/thumbnail?id=${fileId}&sz=w1600`;
    }

    const detailImg = document.getElementById('detailImage');
    detailImg.src = imgUrl;
    detailImg.setAttribute('referrerpolicy', 'no-referrer');

    document.getElementById('detailTitle').textContent = item.title || "제목 없음";
    document.getElementById('detailCategory').textContent = item.category;
    document.getElementById('detailDate').textContent = item.date;
    document.getElementById('detailPrompt').value = item.prompt;

    // AI 사고과정 섹션 — 데이터 있을 때만 표시
    const thinkingBox = document.getElementById('detailThinkingBox');
    const thinkingTA = document.getElementById('detailThinking');
    if (item.thinking && item.thinking.trim()) {
        thinkingTA.value = item.thinking;
        thinkingBox.classList.remove('hidden');
    } else {
        thinkingTA.value = '';
        thinkingBox.classList.add('hidden');
    }

    // 분석 메모 섹션 — 데이터 있을 때만 표시
    const analysisBox = document.getElementById('detailAnalysisBox');
    const analysisTA = document.getElementById('detailAnalysis');
    if (item.analysis && item.analysis.trim()) {
        analysisTA.value = item.analysis;
        analysisBox.classList.remove('hidden');
    } else {
        analysisTA.value = '';
        analysisBox.classList.add('hidden');
    }

    detailModal.classList.add('open');
}

function showToast(msg = "저장되었습니다!") {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// Utility
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
