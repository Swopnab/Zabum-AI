// Zabum AI Frontend - Demo Application
const API_URL = 'http://localhost:5001';

const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadBtn = document.getElementById('uploadBtn');
const statusSection = document.getElementById('statusSection');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('resultsSection');

let selectedFile = null;

// Upload area click handler
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// File selection handler
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        uploadBtn.disabled = false;
        uploadArea.querySelector('.upload-prompt').innerHTML = `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <p><strong>${file.name}</strong></p>
            <p class="hint">Click to change file</p>
        `;
    }
});

// Drag and drop handlers
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        selectedFile = file;
        fileInput.files = e.dataTransfer.files;
        uploadBtn.disabled = false;
        uploadArea.querySelector('.upload-prompt').innerHTML = `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <p><strong>${file.name}</strong></p>
            <p class="hint">Click to change file</p>
        `;
    }
});

// Upload button handler
uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    // Show status section
    statusSection.style.display = 'block';
    resultsSection.style.display = 'none';
    uploadBtn.disabled = true;

    try {
        // Step 1: OCR
        statusText.textContent = '🔍 Extracting text with TrOCR...';
        await sleep(500);

        // Create form data
        const formData = new FormData();
        formData.append('image', selectedFile);

        // Send to backend
        const response = await fetch(`${API_URL}/api/process`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        // Step 2: LLM Processing
        statusText.textContent = '🤖 Generating tags with Llama 3.2...';

        const result = await response.json();

        // Step 3: Show results
        statusText.textContent = '✅ Processing complete!';
        await sleep(500);

        displayResults(result);

    } catch (error) {
        console.error('Error:', error);
        statusText.textContent = `❌ Error: ${error.message}`;

        // Show more helpful error for Ollama
        if (error.message.includes('fetch')) {
            statusText.innerHTML = `
                ❌ Cannot connect to backend. Make sure:<br>
                1. Backend is running (python app.py)<br>
                2. Ollama is installed and running (ollama serve)
            `;
        }
    } finally {
        uploadBtn.disabled = false;
    }
});

function displayResults(result) {
    statusSection.style.display = 'none';
    resultsSection.style.display = 'block';

    // Extracted text
    document.getElementById('extractedText').textContent =
        result.extracted_text || 'No text detected';

    // Tags
    const tagsContainer = document.getElementById('tagsContainer');
    tagsContainer.innerHTML = '';
    (result.tags || []).forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'tag';
        tagEl.textContent = tag;
        tagsContainer.appendChild(tagEl);
    });

    // Category
    document.getElementById('categoryBadge').textContent =
        result.category || 'unknown';

    // Summary
    document.getElementById('summaryText').textContent =
        result.summary || 'No summary available';

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Check backend status on load
async function checkBackend() {
    try {
        const response = await fetch(`${API_URL}/`);
        const data = await response.json();
        console.log('✅ Backend connected:', data);
    } catch (error) {
        console.warn('⚠️  Backend not available. Make sure to run: python app.py');
    }
}

checkBackend();
