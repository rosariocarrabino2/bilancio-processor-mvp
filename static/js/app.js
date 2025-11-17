// Bilancio Processor - Frontend Logic

let selectedFile = null;
let outputFilename = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFileBtn = document.getElementById('removeFileBtn');
const processBtn = document.getElementById('processBtn');
const progressArea = document.getElementById('progressArea');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultArea = document.getElementById('resultArea');
const resultDetails = document.getElementById('resultDetails');
const downloadBtn = document.getElementById('downloadBtn');
const newProcessBtn = document.getElementById('newProcessBtn');
const errorArea = document.getElementById('errorArea');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');

// Event Listeners
selectFileBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
removeFileBtn.addEventListener('click', resetUpload);
processBtn.addEventListener('click', processFile);
downloadBtn.addEventListener('click', downloadFile);
newProcessBtn.addEventListener('click', resetAll);
retryBtn.addEventListener('click', resetAll);

// Drag and Drop
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

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

uploadArea.addEventListener('click', () => fileInput.click());

// File Handling
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.ms-excel',
                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    const validExtensions = ['.pdf', '.xls', '.xlsx'];

    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
        showError('Formato file non supportato. Usa PDF, XLS o XLSX');
        return;
    }

    // Validate file size (16MB max)
    const maxSize = 16 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File troppo grande. Massimo 16MB');
        return;
    }

    selectedFile = file;
    showFileInfo(file);
}

function showFileInfo(file) {
    // Format file size
    const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
    const sizeInKB = (file.size / 1024).toFixed(2);
    const formattedSize = sizeInMB > 1 ? `${sizeInMB} MB` : `${sizeInKB} KB`;

    fileName.textContent = file.name;
    fileSize.textContent = formattedSize;

    // Show file info and process button
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    processBtn.style.display = 'block';

    // Add fade-in animation
    fileInfo.classList.add('fade-in');
    processBtn.classList.add('fade-in');
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';

    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    processBtn.style.display = 'none';
}

function resetAll() {
    resetUpload();
    progressArea.style.display = 'none';
    resultArea.style.display = 'none';
    errorArea.style.display = 'none';
    outputFilename = null;
}

// Processing
async function processFile() {
    if (!selectedFile) return;

    // Hide previous results
    resultArea.style.display = 'none';
    errorArea.style.display = 'none';

    // Show progress
    fileInfo.style.display = 'none';
    processBtn.style.display = 'none';
    progressArea.style.display = 'block';
    progressArea.classList.add('fade-in');

    // Prepare form data
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        // Simulate progress
        updateProgress(20, 'Caricamento file...');

        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        updateProgress(60, 'Estrazione dati con AI...');

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Errore nel processing');
        }

        updateProgress(100, 'Completato!');

        // Show success
        setTimeout(() => {
            showSuccess(data);
        }, 500);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    }
}

function updateProgress(percent, text) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

function showSuccess(data) {
    progressArea.style.display = 'none';
    resultArea.style.display = 'block';
    resultArea.classList.add('fade-in');

    outputFilename = data.output_file;

    // Show details
    let detailsHTML = `
        <p><strong>Conti estratti:</strong> ${data.num_accounts}</p>
    `;

    if (data.warnings && data.warnings.length > 0) {
        detailsHTML += `
            <p style="color: #f6ad55; margin-top: 10px;">
                <strong>Avvisi:</strong><br>
                ${data.warnings.join('<br>')}
            </p>
        `;
    }

    resultDetails.innerHTML = detailsHTML;
}

function showError(message) {
    progressArea.style.display = 'none';
    fileInfo.style.display = 'none';
    processBtn.style.display = 'none';
    errorArea.style.display = 'block';
    errorArea.classList.add('fade-in');

    errorMessage.textContent = message;
}

// Download
function downloadFile() {
    if (!outputFilename) return;

    window.location.href = `/api/download/${outputFilename}`;
}

// Format bytes to human readable
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
