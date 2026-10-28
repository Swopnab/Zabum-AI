/**
 * Zabum AI - Frontend Application
 * Privacy-first Personal AI Assistant with Persistent Memory and Knowledge Retrieval
 */

const API_BASE = window.location.origin;

// State
let currentConversationId = null;
let conversations = [];
let memories = [];
let documents = [];
let isSending = false;

// DOM Elements
const sidebar = document.getElementById('sidebar');
const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
const closeSidebarBtn = document.getElementById('closeSidebarBtn');
const newChatBtn = document.getElementById('newChatBtn');

const tabChatsBtn = document.getElementById('tabChatsBtn');
const tabMemoryBtn = document.getElementById('tabMemoryBtn');
const tabDocsBtn = document.getElementById('tabDocsBtn');

const paneChats = document.getElementById('paneChats');
const paneMemory = document.getElementById('paneMemory');
const paneDocs = document.getElementById('paneDocs');

const conversationList = document.getElementById('conversationList');
const memoryList = document.getElementById('memoryList');
const documentList = document.getElementById('documentList');
const memorySearchInput = document.getElementById('memorySearchInput');

const memoryCountBadge = document.getElementById('memoryCountBadge');
const docsCountBadge = document.getElementById('docsCountBadge');

const statusDot = document.getElementById('statusDot');
const statusTitle = document.getElementById('statusTitle');
const statusDetail = document.getElementById('statusDetail');

const activeChatTitle = document.getElementById('activeChatTitle');
const headerModelName = document.getElementById('headerModelName');
const headerMemoryBtn = document.getElementById('headerMemoryBtn');
const headerKnowledgeBtn = document.getElementById('headerKnowledgeBtn');

const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesFeed = document.getElementById('messagesFeed');
const typingIndicator = document.getElementById('typingIndicator');

const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const attachFileBtn = document.getElementById('attachFileBtn');
const chatFileInput = document.getElementById('chatFileInput');
const dropOverlay = document.getElementById('dropOverlay');
const uploadProgressPill = document.getElementById('uploadProgressPill');
const uploadProgressText = document.getElementById('uploadProgressText');

// Modals
const memoryModal = document.getElementById('memoryModal');
const memoryModalTitle = document.getElementById('memoryModalTitle');
const editMemoryId = document.getElementById('editMemoryId');
const memoryContentInput = document.getElementById('memoryContentInput');
const memoryCategorySelect = document.getElementById('memoryCategorySelect');
const saveMemoryBtn = document.getElementById('saveMemoryBtn');
const openAddMemoryBtn = document.getElementById('openAddMemoryBtn');

const uploadModal = document.getElementById('uploadModal');
const openUploadBtn = document.getElementById('openUploadBtn');
const modalDropZone = document.getElementById('modalDropZone');
const modalFileInput = document.getElementById('modalFileInput');
const modalUploadStatus = document.getElementById('modalUploadStatus');
const modalUploadStatusText = document.getElementById('modalUploadStatusText');

const chunkModal = document.getElementById('chunkModal');
const chunkModalTitle = document.getElementById('chunkModalTitle');
const docMetaPanel = document.getElementById('docMetaPanel');
const docExtractedTextBox = document.getElementById('docExtractedTextBox');
const docChunksContainer = document.getElementById('docChunksContainer');

const renameModal = document.getElementById('renameModal');
const renameConvId = document.getElementById('renameConvId');
const renameConvInput = document.getElementById('renameConvInput');
const confirmRenameBtn = document.getElementById('confirmRenameBtn');

const toastContainer = document.getElementById('toastContainer');

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', async () => {
    initEventListeners();
    await checkSystemStatus();
    await loadConversations();
    await loadMemories();
    await loadDocuments();

    // Auto-create or open newest conversation if available
    if (conversations.length > 0) {
        selectConversation(conversations[0].id);
    } else {
        createNewChat();
    }

    // Periodic health check
    setInterval(checkSystemStatus, 30000);
});

// ==================== EVENT LISTENERS ====================

function initEventListeners() {
    // Sidebar toggle (mobile/desktop)
    toggleSidebarBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    closeSidebarBtn.addEventListener('click', () => sidebar.classList.remove('open'));

    // New Chat
    newChatBtn.addEventListener('click', () => createNewChat());

    // Navigation Tabs
    tabChatsBtn.addEventListener('click', () => switchTab('chats'));
    tabMemoryBtn.addEventListener('click', () => switchTab('memory'));
    tabDocsBtn.addEventListener('click', () => switchTab('docs'));

    headerMemoryBtn.addEventListener('click', () => switchTab('memory'));
    headerKnowledgeBtn.addEventListener('click', () => switchTab('docs'));

    // Chat input handling
    chatInput.addEventListener('input', handleChatInput);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', () => sendMessage());

    // Starter Prompt Cards
    document.querySelectorAll('.starter-card').forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.getAttribute('data-prompt');
            chatInput.value = prompt;
            handleChatInput();
            sendMessage();
        });
    });

    // File attachments
    attachFileBtn.addEventListener('click', () => chatFileInput.click());
    chatFileInput.addEventListener('change', (e) => handleFileUpload(e.target.files[0]));

    // Drag & Drop on chat main
    const chatMain = document.getElementById('chatMain');
    ['dragenter', 'dragover'].forEach(name => {
        chatMain.addEventListener(name, (e) => {
            e.preventDefault();
            dropOverlay.classList.add('active');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        chatMain.addEventListener(name, (e) => {
            e.preventDefault();
            if (e.type === 'dragleave' && e.target === dropOverlay) {
                dropOverlay.classList.remove('active');
            } else if (e.type === 'drop') {
                dropOverlay.classList.remove('active');
                if (e.dataTransfer.files.length > 0) {
                    handleFileUpload(e.dataTransfer.files[0]);
                }
            }
        });
    });

    // Modals
    document.querySelectorAll('.close-modal-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modalId = btn.getAttribute('data-modal');
            if (modalId) closeModal(modalId);
        });
    });

    // Memory modal
    openAddMemoryBtn.addEventListener('click', () => openAddMemoryModal());
    saveMemoryBtn.addEventListener('click', () => saveMemory());
    memorySearchInput.addEventListener('input', () => {
        loadMemories(memorySearchInput.value.trim());
    });

    // Knowledge upload modal
    openUploadBtn.addEventListener('click', () => {
        modalUploadStatus.style.display = 'none';
        openModal('uploadModal');
    });

    modalDropZone.addEventListener('click', () => modalFileInput.click());
    modalFileInput.addEventListener('change', (e) => handleFileUpload(e.target.files[0], true));

    modalDropZone.addEventListener('dragover', (e) => e.preventDefault());
    modalDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0], true);
        }
    });

    // Rename conversation modal
    confirmRenameBtn.addEventListener('click', () => confirmRenameConversation());
}

// ==================== SYSTEM STATUS ====================

async function checkSystemStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        if (!res.ok) throw new Error('Status check failed');
        const data = await res.json();

        if (data.ai_provider && data.ai_provider.available) {
            statusDot.className = 'status-dot online';
            statusTitle.textContent = data.ai_provider.name === 'MockProvider' ? 'Fictional demo' : 'Local AI ready';
            statusDetail.textContent = data.ai_provider.message;
            headerModelName.textContent = data.ai_provider.name === 'MockProvider' ? 'Demo · no model inference' : data.ai_provider.name;
        } else {
            statusDot.className = 'status-dot offline';
            statusTitle.textContent = 'Ollama Offline';
            statusDetail.textContent = 'Run "ollama serve"';
            headerModelName.textContent = 'Offline Mode (Mock/Help)';
        }
    } catch (e) {
        statusDot.className = 'status-dot offline';
        statusTitle.textContent = 'Backend Offline';
        statusDetail.textContent = 'Check Python server';
    }
}

// ==================== CONVERSATIONS ====================

async function loadConversations() {
    try {
        const res = await fetch(`${API_BASE}/api/conversations`);
        const data = await res.json();
        conversations = data.conversations || [];
        renderConversationList();
    } catch (e) {
        console.error('Failed to load conversations:', e);
    }
}

function renderConversationList() {
    conversationList.innerHTML = '';
    if (conversations.length === 0) {
        conversationList.innerHTML = '<div class="section-desc" style="text-align: center; margin-top: 10px;">No chats yet</div>';
        return;
    }

    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = `conv-item ${conv.id === currentConversationId ? 'active' : ''}`;
        item.innerHTML = `
            <span class="conv-title" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</span>
            <div class="conv-actions">
                <button class="btn-icon-xs edit-title-btn" title="Rename" data-id="${conv.id}">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9"></path>
                        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                    </svg>
                </button>
                <button class="btn-icon-xs delete delete-conv-btn" title="Delete" data-id="${conv.id}">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;

        item.addEventListener('click', (e) => {
            if (e.target.closest('.conv-actions')) return;
            selectConversation(conv.id);
            if (window.innerWidth <= 768) sidebar.classList.remove('open');
        });

        item.tabIndex = 0; item.setAttribute('role', 'button');
        item.setAttribute('aria-label', `Open chat: ${conv.title}`);
        item.addEventListener('keydown', e => { if (e.target === item && ['Enter',' '].includes(e.key)) { e.preventDefault(); item.click(); } });
        const editBtn = item.querySelector('.edit-title-btn');
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openRenameModal(conv.id, conv.title);
        });

        const deleteBtn = item.querySelector('.delete-conv-btn');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        });

        conversationList.appendChild(item);
    });
}

async function createNewChat() {
    try {
        const res = await fetch(`${API_BASE}/api/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' })
        });
        const data = await res.json();
        if (data.conversation) {
            conversations.unshift(data.conversation);
            selectConversation(data.conversation.id);
            switchTab('chats');
        }
    } catch (e) {
        showToast('Failed to create new chat', 'error');
    }
}

async function selectConversation(convId) {
    currentConversationId = convId;
    renderConversationList();

    const conv = conversations.find(c => c.id === convId);
    if (conv) {
        activeChatTitle.textContent = conv.title;
    }

    try {
        const res = await fetch(`${API_BASE}/api/conversations/${convId}`);
        const data = await res.json();
        renderMessages(data.messages || []);
    } catch (e) {
        console.error('Failed to load messages for conversation:', e);
    }
}

function openRenameModal(convId, currentTitle) {
    renameConvId.value = convId;
    renameConvInput.value = currentTitle;
    openModal('renameModal');
    setTimeout(() => renameConvInput.focus(), 100);
}

async function confirmRenameConversation() {
    const convId = renameConvId.value;
    const newTitle = renameConvInput.value.trim();
    if (!newTitle) return;

    try {
        const res = await fetch(`${API_BASE}/api/conversations/${convId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        if (res.ok) {
            const data = await res.json();
            const idx = conversations.findIndex(c => c.id == convId);
            if (idx !== -1) {
                conversations[idx] = data.conversation;
            }
            if (currentConversationId == convId) {
                activeChatTitle.textContent = newTitle;
            }
            renderConversationList();
            closeModal('renameModal');
            showToast('Conversation renamed', 'success');
        }
    } catch (e) {
        showToast('Failed to rename conversation', 'error');
    }
}

async function deleteConversation(convId) {
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    try {
        const res = await fetch(`${API_BASE}/api/conversations/${convId}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            conversations = conversations.filter(c => c.id != convId);
            if (currentConversationId == convId) {
                if (conversations.length > 0) {
                    selectConversation(conversations[0].id);
                } else {
                    createNewChat();
                }
            } else {
                renderConversationList();
            }
            showToast('Conversation deleted', 'success');
        }
    } catch (e) {
        showToast('Failed to delete conversation', 'error');
    }
}

// ==================== MESSAGING & CHAT PIPELINE ====================

function renderMessages(messages) {
    messagesFeed.innerHTML = '';
    if (!messages || messages.length === 0) {
        welcomeScreen.style.display = 'block';
        messagesFeed.style.display = 'none';
        return;
    }

    welcomeScreen.style.display = 'none';
    messagesFeed.style.display = 'flex';

    messages.forEach(msg => {
        appendMessageElement(msg);
    });

    scrollToBottom();
}

function appendMessageElement(msg) {
    welcomeScreen.style.display = 'none';
    messagesFeed.style.display = 'flex';

    const row = document.createElement('div');
    row.className = `message-row ${msg.role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = msg.role === 'assistant' ? 'Z' : 'Y';

    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-content-wrapper';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (msg.role === 'assistant') {
        bubble.innerHTML = renderMarkdown(msg.content);
        attachCodeCopyButtons(bubble);

        // Render sources accordion if sources are present
        if (msg.sources && msg.sources.length > 0) {
            const sourcesDiv = createSourcesAccordion(msg.sources);
            bubble.appendChild(sourcesDiv);
        }
    } else {
        bubble.textContent = msg.content;
    }

    contentWrapper.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(contentWrapper);

    messagesFeed.appendChild(row);
    scrollToBottom();
}

// Adapted from UI Vault's original Quiet accordion pattern; no external component.
function createSourcesAccordion(sources) {
    const details = document.createElement('details');
    details.className = 'sources-accordion';
    const summary = document.createElement('summary');
    summary.textContent = `Retrieved context (${sources.length}) · inspect passages`;
    details.appendChild(summary);
    for (const src of sources) {
        const article = document.createElement('div');
        const button = document.createElement('button');
        button.className = 'source-link';
        button.textContent = `${src.citation_id || 'Source'} · ${src.document_name || 'Saved memory'} · ${src.page_number ? 'page ' + src.page_number : 'page unavailable'}`;
        button.disabled = !src.document_id;
        button.onclick = () => openDocInspectionModal(src.document_id, src.chunk_id);
        const passage = document.createElement('blockquote');
        passage.textContent = src.content_preview || src.content || '';
        article.append(button, passage);
        details.appendChild(article);
    }
    return details;
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isSending) return;

    isSending = true;
    chatInput.value = '';
    handleChatInput();
    sendBtn.disabled = true;

    // Append optimistic user message
    appendMessageElement({ role: 'user', content: text });

    // Show typing indicator
    typingIndicator.style.display = 'flex';
    scrollToBottom();

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: text,
                mode: document.getElementById("answerMode").value
            })
        });

        typingIndicator.style.display = 'none';

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || 'Failed to generate response');
        }

        const data = await res.json();

        // Update active conversation ID and title
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            const conv = conversations.find(c => c.id == currentConversationId);
            if (conv) {
                conv.title = data.conversation_title;
                activeChatTitle.textContent = data.conversation_title;
            } else {
                conversations.unshift({
                    id: data.conversation_id,
                    title: data.conversation_title
                });
            }
            renderConversationList();
        }

        // Render AI message
        if (data.assistant_message) {
            appendMessageElement(data.assistant_message);
        }

        const suggestions = document.getElementById('memorySuggestions');
        suggestions.replaceChildren();
        for (const candidate of data.memory_suggestions || []) {
            const row = document.createElement('div');
            const label = document.createElement('span');
            label.textContent = `Remember this? ${candidate.content} `;
            const approve = document.createElement('button');
            approve.textContent = 'Approve';
            approve.onclick = async () => {
                approve.disabled = true;
                try {
                    const response = await fetch(`${API_BASE}/api/memories`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(candidate)});
                    if (!response.ok) throw new Error('Memory was not saved');
                    row.remove(); await loadMemories(); showToast('Memory approved and saved', 'success');
                } catch (error) { approve.disabled = false; showToast(error.message, 'error'); }
            };
            const dismiss = document.createElement('button');
            dismiss.textContent = 'Dismiss'; dismiss.onclick = () => row.remove();
            row.append(label, approve, dismiss); suggestions.appendChild(row);
        }
        // Reload memories if new ones were learned
        if (data.memories_created && data.memories_created.length > 0) {
            await loadMemories();
            showToast(`Saved ${data.memories_created.length} new memory to context!`, 'success');
        }

    } catch (e) {
        typingIndicator.style.display = 'none';
        appendMessageElement({
            role: 'assistant',
            content: `⚠️ **Connection Error**: ${e.message}\n\nMake sure the Zabum AI backend is running and Ollama is available.`
        });
    } finally {
        isSending = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function handleChatInput() {
    chatInput.style.height = 'auto';
    chatInput.style.height = `${Math.min(chatInput.scrollHeight, 160)}px`;
    sendBtn.disabled = !chatInput.value.trim();
}

function scrollToBottom() {
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// ==================== MEMORY MANAGEMENT ====================

async function loadMemories(searchQuery = '') {
    try {
        let url = `${API_BASE}/api/memories`;
        if (searchQuery) url += `?q=${encodeURIComponent(searchQuery)}`;
        const res = await fetch(url);
        const data = await res.json();
        memories = data.memories || [];
        memoryCountBadge.textContent = memories.length;
        renderMemoryList();
    } catch (e) {
        console.error('Failed to load memories:', e);
    }
}

function renderMemoryList() {
    memoryList.innerHTML = '';
    if (memories.length === 0) {
        memoryList.innerHTML = '<div class="section-desc" style="text-align: center; margin-top: 10px;">No memories stored</div>';
        return;
    }

    memories.forEach(mem => {
        const card = document.createElement('div');
        card.className = 'memory-card';
        const tagClass = `tag-${mem.category || 'general'}`;
        card.innerHTML = `
            <div class="card-header-row">
                <span class="tag-pill ${tagClass}">${escapeHtml(mem.category || 'general')}</span>
                <div style="display: flex; gap: 4px;">
                    <button class="btn-icon-xs edit-mem-btn" title="Edit memory" data-id="${mem.id}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 20h9"></path>
                            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                        </svg>
                    </button>
                    <button class="btn-icon-xs delete delete-mem-btn" title="Delete memory" data-id="${mem.id}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="memory-text">${escapeHtml(mem.content)}</div>
        `;

        card.querySelector('.edit-mem-btn').addEventListener('click', () => openEditMemoryModal(mem));
        card.querySelector('.delete-mem-btn').addEventListener('click', () => deleteMemory(mem.id));

        memoryList.appendChild(card);
    });
}

function openAddMemoryModal() {
    editMemoryId.value = '';
    memoryContentInput.value = '';
    memoryCategorySelect.value = 'preference';
    memoryModalTitle.textContent = 'Add Personal Memory';
    openModal('memoryModal');
    setTimeout(() => memoryContentInput.focus(), 100);
}

function openEditMemoryModal(mem) {
    editMemoryId.value = mem.id;
    memoryContentInput.value = mem.content;
    memoryCategorySelect.value = mem.category || 'general';
    memoryModalTitle.textContent = 'Edit Personal Memory';
    openModal('memoryModal');
    setTimeout(() => memoryContentInput.focus(), 100);
}

async function saveMemory() {
    const id = editMemoryId.value;
    const content = memoryContentInput.value.trim();
    const category = memoryCategorySelect.value;

    if (!content) {
        showToast('Memory content cannot be empty', 'error');
        return;
    }

    try {
        if (id) {
            // Update
            await checkedFetch(`${API_BASE}/api/memories/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, category })
            });
            showToast('Memory updated', 'success');
        } else {
            // Create
            await checkedFetch(`${API_BASE}/api/memories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, category })
            });
            showToast('Memory created', 'success');
        }
        closeModal('memoryModal');
        await loadMemories();
    } catch (e) {
        showToast('Failed to save memory', 'error');
    }
}

async function deleteMemory(memId) {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    try {
        await checkedFetch(`${API_BASE}/api/memories/${memId}`, { method: 'DELETE' });
        showToast('Memory deleted', 'success');
        await loadMemories();
    } catch (e) {
        showToast('Failed to delete memory', 'error');
    }
}

// ==================== KNOWLEDGE BASE & OCR INGESTION ====================

async function loadDocuments() {
    try {
        const res = await fetch(`${API_BASE}/api/documents`);
        const data = await res.json();
        documents = data.documents || [];
        docsCountBadge.textContent = documents.length;
        renderDocumentList();
    } catch (e) {
        console.error('Failed to load documents:', e);
    }
}

function renderDocumentList() {
    documentList.innerHTML = '';
    if (documents.length === 0) {
        documentList.innerHTML = '<div class="section-desc" style="text-align: center; margin-top: 10px;">No documents indexed</div>';
        return;
    }

    documents.forEach(doc => {
        const card = document.createElement('div');
        card.className = 'doc-card';
        const tagClass = `tag-${doc.file_type || 'document'}`;
        card.innerHTML = `
            <div class="card-header-row">
                <span class="tag-pill ${tagClass}">${escapeHtml(doc.file_type || 'doc')}</span>
                <div style="display: flex; gap: 4px;">
                    <button class="btn-icon-xs inspect-doc-btn" title="Inspect Chunks" data-id="${doc.id}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                    </button>
                    <button class="btn-icon-xs delete delete-doc-btn" title="Delete document" data-id="${doc.id}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="doc-name" title="${escapeHtml(doc.original_name)}">${escapeHtml(doc.original_name)}</div>
            <div class="doc-meta">
                <span>${escapeHtml(doc.summary || 'Indexed')}</span>
            </div>
        `;

        card.querySelector('.inspect-doc-btn').addEventListener('click', () => openDocInspectionModal(doc.id));
        card.querySelector('.delete-doc-btn').addEventListener('click', () => deleteDocument(doc.id));

        documentList.appendChild(card);
    });
}

async function handleFileUpload(file, isModal = false) {
    if (!file) return;

    const isImage = file.type.startsWith('image/');
    const progressLabel = isImage ? 'Extracting text with TrOCR...' : 'Ingesting and chunking for RAG...';

    if (isModal) {
        modalUploadStatus.style.display = 'flex';
        modalUploadStatusText.textContent = progressLabel;
    } else {
        uploadProgressPill.style.display = 'flex';
        uploadProgressText.textContent = progressLabel;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const readiness = document.getElementById('documentReadiness');
        const meter = document.getElementById('uploadMeter');
        readiness.textContent = `Uploading ${file.name}…`; meter.hidden = false; meter.value = 0;
        const res = await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE}/api/documents/upload`);
            xhr.upload.onprogress = e => { if (e.lengthComputable) meter.value = e.loaded / e.total * 100; };
            xhr.upload.onload = () => { meter.removeAttribute('value'); readiness.textContent = 'Extracting and indexing. This document is not ready yet…'; };
            xhr.onload = () => resolve({ok:xhr.status >= 200 && xhr.status < 300, json:async () => JSON.parse(xhr.responseText)});
            xhr.onerror = () => reject(new Error('Connection lost; check Documents before retrying'));
            xhr.timeout = 300000; xhr.ontimeout = () => reject(new Error('Processing timed out; check Documents before retrying'));
            xhr.send(formData);
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || 'Upload failed');
        }

        const data = await res.json();
        document.getElementById("documentReadiness").textContent = `${file.name} · ready to search`;
        showToast(`Successfully indexed "${file.name}"!`, 'success');
        await loadDocuments();

        if (isModal) {
            closeModal('uploadModal');
        }

        // Notify in current chat
        if (currentConversationId) {
            appendMessageElement({
                role: 'assistant',
                content: `📎 **Document Ingested:** \`${file.name}\`\n\n*Extracted Summary*: ${data.document.summary || 'Processed successfully.'}\n\nYou can now ask me questions about this content!`
            });
        }
    } catch (e) {
        document.getElementById("documentReadiness").textContent = `Not ready: ${e.message}`;
        showToast(`Upload error: ${e.message}`, 'error');
    } finally {
        document.getElementById("uploadMeter").hidden = true;
        uploadProgressPill.style.display = 'none';
        modalUploadStatus.style.display = 'none';
        chatFileInput.value = '';
        modalFileInput.value = '';
    }
}

async function openDocInspectionModal(docId, chunkId) {
    try {
        const res = await fetch(`${API_BASE}/api/documents/${docId}/chunks`);
        if (!res.ok) throw new Error("Source unavailable; it may have been deleted");
        const data = await res.json();
        const doc = data.document;
        const chunks = data.chunks || [];

        chunkModalTitle.textContent = doc.original_name;
        docMetaPanel.innerHTML = `
            <strong>File:</strong> ${escapeHtml(doc.original_name)} | 
            <strong>Type:</strong> ${doc.file_type} | 
            <strong>Indexed:</strong> ${new Date(doc.created_at).toLocaleString()} | 
            <strong>Chunks:</strong> ${chunks.length}
        `;

        docExtractedTextBox.textContent = doc.extracted_text || 'No extracted text';

        docChunksContainer.innerHTML = '';
        chunks.forEach(c => {
            const chunkDiv = document.createElement('div');
            chunkDiv.className = 'chunk-card';
            chunkDiv.id = `chunk-${c.id}`;
            if (c.id === chunkId) chunkDiv.classList.add('selected-passage');
            chunkDiv.innerHTML = `
                <div class="chunk-index-tag">Chunk #${c.chunk_index + 1} · ${c.page_number ? "page " + c.page_number : "page unavailable"} (${c.content.length} chars)</div>
                <div>${escapeHtml(c.content)}</div>
            `;
            docChunksContainer.appendChild(chunkDiv);
        });

        openModal('chunkModal');
        if (chunkId) document.getElementById(`chunk-${chunkId}`)?.scrollIntoView({block:'nearest'});
    } catch (e) {
        showToast('Source unavailable. The document may have been deleted.', 'error');
    }
}

async function deleteDocument(docId) {
    if (!confirm('Remove this document and its search index? Quotes already saved in chats remain. Delete those chats separately to remove their history.')) return;
    try {
        await checkedFetch(`${API_BASE}/api/documents/${docId}`, { method: 'DELETE' });
        showToast('Document deleted', 'success');
        await loadDocuments();
    } catch (e) {
        showToast('Failed to delete document', 'error');
    }
}

// ==================== TAB SWITCHING ====================

function switchTab(tabName) {
    [tabChatsBtn, tabMemoryBtn, tabDocsBtn].forEach(b => b.classList.remove('active'));
    [paneChats, paneMemory, paneDocs].forEach(p => p.classList.remove('active'));

    if (tabName === 'chats') {
        tabChatsBtn.classList.add('active');
        paneChats.classList.add('active');
    } else if (tabName === 'memory') {
        tabMemoryBtn.classList.add('active');
        paneMemory.classList.add('active');
    } else if (tabName === 'docs') {
        tabDocsBtn.classList.add('active');
        paneDocs.classList.add('active');
    }
}

// ==================== MODAL UTILITIES ====================

let modalReturnFocus;
function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (!el) return;
    modalReturnFocus = document.activeElement;
    el.style.display = 'flex';
    const panel = el.querySelector('.modal-card');
    panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true');
    panel.setAttribute('aria-label', panel.querySelector('.modal-title')?.textContent || 'Workspace dialog');
    document.getElementById('appLayout').inert = true;
    el.querySelector('button,input,textarea,select')?.focus();
    el.onkeydown = event => {
        if (event.key === 'Escape') { event.preventDefault(); closeModal(modalId); }
        if (event.key !== 'Tab') return;
        const targets = [...el.querySelectorAll('button,input,textarea,select,a[href]')].filter(n=>!n.disabled && n.getClientRects().length);
        const first=targets[0],last=targets.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault();last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) {event.preventDefault();first?.focus();}
    };
}
function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.style.display = 'none';
    document.getElementById('appLayout').inert = false;
    if (modalReturnFocus?.isConnected) modalReturnFocus.focus();
}

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role',type === 'error' ? 'alert' : 'status');
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 200);
    }, 3500);
}

// ==================== LIGHTWEIGHT MARKDOWN PARSER ====================

function renderMarkdown(text) {
    if (!text) return '';

    let html = escapeHtml(text);

    // 1. Code blocks with language tags ```lang ... ```
    html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
        const cleanLang = lang || 'code';
        return `
            <div class="code-block-container">
                <div class="code-block-header">
                    <span>${cleanLang}</span>
                    <button class="btn-copy-code" data-code="${encodeURIComponent(code)}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        Copy
                    </button>
                </div>
                <pre><code>${code}</code></pre>
            </div>
        `;
    });

    // 2. Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 3. Headers
    html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    html = html.replace(/^&gt; (.*$)/gm, '<blockquote>$1</blockquote>');

    // 4. Bold & Italic
    html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // 5. Blockquotes
    html = html.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');

    // 6. Bullet lists
    html = html.replace(/^\s*[-*+]\s+(.*)$/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

    // 7. Paragraphs & Line Breaks
    const paragraphs = html.split(/\n\n+/);
    html = paragraphs.map(p => {
        p = p.trim();
        if (p.startsWith('<div class="code-block-container"') || p.startsWith('<h1>') || p.startsWith('<h2>') || p.startsWith('<h3>') || p.startsWith('<ul>') || p.startsWith('<blockquote>')) {
            return p;
        }
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');

    return html;
}

function attachCodeCopyButtons(container) {
    container.querySelectorAll('.btn-copy-code').forEach(btn => {
        btn.addEventListener('click', () => {
            const rawCode = decodeURIComponent(btn.getAttribute('data-code'));
            navigator.clipboard.writeText(rawCode).then(() => {
                const originalText = btn.innerHTML;
                btn.innerHTML = '<span>✓ Copied</span>';
                setTimeout(() => btn.innerHTML = originalText, 2000);
            });
        });
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Memory controls persist on the server, not only in this tab.
document.addEventListener('DOMContentLoaded', async () => {
    const toggle = document.getElementById('memoryEnabled');
    try { const r = await fetch(`${API_BASE}/api/preferences`); if (!r.ok) throw Error(); toggle.checked = (await r.json()).memory_enabled; }
    catch { toggle.disabled = true; showToast('Memory preference could not be loaded', 'error'); }
    toggle.onchange = async () => {
        const desired = toggle.checked; toggle.disabled = true;
        try { const r = await fetch(`${API_BASE}/api/preferences`, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({memory_enabled:desired})}); if (!r.ok) throw Error(); document.getElementById('memorySuggestions').replaceChildren(); }
        catch { toggle.checked = !desired; showToast('Preference was not saved', 'error'); }
        finally { toggle.disabled = false; }
    };
});

document.addEventListener('DOMContentLoaded',()=>{
    const syncSidebar=()=>{
        const mobile=innerWidth<=768, open=sidebar.classList.contains('open');
        sidebar.inert=mobile&&!open;
        document.getElementById('toggleSidebarBtn').setAttribute('aria-expanded',String(!mobile||open));
    };
    new MutationObserver(syncSidebar).observe(sidebar,{attributes:true,attributeFilter:['class']});
    window.addEventListener('resize',syncSidebar);syncSidebar();
});

async function checkedFetch(url,options) {
    const response=await fetch(url,options);
    if(!response.ok)throw new Error('Changes were not saved. Please retry.');
    return response;
}
