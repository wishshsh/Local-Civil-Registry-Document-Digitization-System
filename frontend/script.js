// Global variables
let uploadedFiles = {
    cert: [],
    marriage: []
};

let records = [
    { id: 'BC-001', type: 'birth', name: 'Juan Dela Cruz', date: '2024-01-15', status: 'Processed' },
    { id: 'DC-001', type: 'death', name: 'Maria Santos', date: '2024-01-20', status: 'Pending' },
    { id: 'MC-001', type: 'marriage-cert', name: 'Pedro & Ana Garcia', date: '2024-02-01', status: 'Processed' },
    { id: 'ML-001', type: 'marriage-license', name: 'Jose & Carmen Reyes', date: '2024-02-05', status: 'Approved' }
];

// Navigation history
let navigationHistory = ['login'];
let currentHistoryIndex = 0;
let isLoggedIn = false;

// Page URLs mapping (for potential future use)
const pageUrls = {
    'login': 'https://localcivilregistry.gov.ph',
    'services': 'https://localcivilregistry.gov.ph/services',
    'certifications': 'https://localcivilregistry.gov.ph/services/certifications',
    'certTemplateView': 'https://localcivilregistry.gov.ph/services/certifications/template',
    'marriageLicense': 'https://localcivilregistry.gov.ph/services/marriage-license',
    'marriageTemplateView': 'https://localcivilregistry.gov.ph/services/marriage-license/template',
    'records': 'https://localcivilregistry.gov.ph/records'
};

// Page Navigation with history
function showPage(pageName, addToHistory = true) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    
    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) {
        targetPage.classList.add('active');
        
        // Update navigation history
        if (addToHistory) {
            // Remove forward history when navigating to a new page
            navigationHistory = navigationHistory.slice(0, currentHistoryIndex + 1);
            navigationHistory.push(pageName);
            currentHistoryIndex = navigationHistory.length - 1;
        }
    }

    // Show records when navigating to records page
    if (pageName === 'records') {
        displayRecords(records);
    }
}

// Home navigation
function goHome() {
    if (isLoggedIn) {
        showPage('services');
    }
}

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        isLoggedIn = false;
        document.getElementById('headerButtons').style.display = 'none';
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        uploadedFiles = { cert: [], marriage: [] };
        navigationHistory = ['login'];
        currentHistoryIndex = 0;
        showPage('login', false);
    }
}

// Login
function login(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Simple validation (in real app, this would be server-side)
    if (username && password) {
        isLoggedIn = true;
        document.getElementById('headerButtons').style.display = 'flex';
        showPage('services');
    } else {
        alert('Please enter valid credentials');
    }
}

// File Upload
function handleFileUpload(event, type) {
    const files = Array.from(event.target.files);
    uploadedFiles[type] = uploadedFiles[type].concat(files);
    displayUploadedFiles(type);
}

function displayUploadedFiles(type) {
    const container = document.getElementById(type + 'Files');
    container.innerHTML = '';
    
    uploadedFiles[type].forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
            <button class="file-remove" onclick="removeFile('${type}', ${index})">Remove</button>
        `;
        container.appendChild(fileItem);
    });
}

function removeFile(type, index) {
    uploadedFiles[type].splice(index, 1);
    displayUploadedFiles(type);
}

// Process Functions
function processCertification() {
    if (uploadedFiles.cert.length === 0) {
        alert('Please upload at least one file');
        return;
    }
    showPage('certTemplateView');
}

function saveCertification() {
    if (confirm('Save certification and return to services?')) {
        alert('Certification saved successfully!');
        
        // Add record
        const newRecord = {
            id: 'BC-' + String(records.length + 1).padStart(3, '0'),
            type: 'birth',
            name: 'New Applicant',
            date: new Date().toISOString().split('T')[0],
            status: 'Pending'
        };
        records.push(newRecord);
        
        // Clear files and inputs
        uploadedFiles.cert = [];
        displayUploadedFiles('cert');
        document.getElementById('certFileInput').value = '';
        
        showPage('services');
    }
}

function processMarriage() {
    if (uploadedFiles.marriage.length === 0) {
        alert('Please upload at least one file');
        return;
    }
    showPage('marriageTemplateView');
}

function saveMarriage() {
    if (confirm('Save marriage license application and return to services?')) {
        alert('Marriage license application saved successfully!');
        
        // Add record
        const newRecord = {
            id: 'ML-' + String(records.length + 1).padStart(3, '0'),
            type: 'marriage-license',
            name: 'New Couple',
            date: new Date().toISOString().split('T')[0],
            status: 'Pending'
        };
        records.push(newRecord);
        
        // Clear files and inputs
        uploadedFiles.marriage = [];
        displayUploadedFiles('marriage');
        document.getElementById('marriageFileInput').value = '';
        
        showPage('services');
    }
}

// Records Management
function displayRecords(recordsToDisplay) {
    const tbody = document.getElementById('recordsTableBody');
    tbody.innerHTML = '';

    if (recordsToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-records">No records found</td></tr>';
        return;
    }

    recordsToDisplay.forEach(record => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.onclick = () => viewRecord(record);
        row.innerHTML = `
            <td>${record.id}</td>
            <td>${formatType(record.type)}</td>
            <td>${record.name}</td>
            <td>${record.date}</td>
            <td>${record.status}</td>
        `;
        tbody.appendChild(row);
    });
}

function viewRecord(record) {
    alert(`Record Details:\n\nID: ${record.id}\nType: ${formatType(record.type)}\nName: ${record.name}\nDate: ${record.date}\nStatus: ${record.status}`);
}

function formatType(type) {
    const types = {
        'birth': 'Birth Certificate',
        'death': 'Death Certificate',
        'marriage-cert': 'Marriage Certificate',
        'marriage-license': 'Marriage License'
    };
    return types[type] || type;
}

function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        searchRecords();
    }
}

function searchRecords() {
    filterRecords();
}

function filterRecords() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const typeFilter = document.getElementById('typeSelect').value;
    const statusFilter = document.getElementById('statusSelect').value;
    const dateFilter = document.getElementById('dateFilter').value;

    let filtered = records.filter(record => {
        // Search filter
        const matchesSearch = searchTerm === '' || 
            record.name.toLowerCase().includes(searchTerm) ||
            record.id.toLowerCase().includes(searchTerm);
        
        // Type filter
        const matchesType = !typeFilter || record.type === typeFilter;
        
        // Status filter
        const matchesStatus = !statusFilter || record.status === statusFilter;
        
        // Date filter
        let matchesDate = true;
        if (dateFilter) {
            const recordDate = new Date(record.date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            switch(dateFilter) {
                case 'today':
                    const todayStart = new Date(today);
                    matchesDate = recordDate >= todayStart;
                    break;
                case 'week':
                    const weekStart = new Date(today);
                    weekStart.setDate(today.getDate() - 7);
                    matchesDate = recordDate >= weekStart;
                    break;
                case 'month':
                    const monthStart = new Date(today);
                    monthStart.setDate(today.getDate() - 30);
                    matchesDate = recordDate >= monthStart;
                    break;
                case 'year':
                    const yearStart = new Date(today);
                    yearStart.setFullYear(today.getFullYear() - 1);
                    matchesDate = recordDate >= yearStart;
                    break;
            }
        }
        
        return matchesSearch && matchesType && matchesStatus && matchesDate;
    });

    displayRecords(filtered);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('typeSelect').value = '';
    document.getElementById('statusSelect').value = '';
    document.getElementById('dateFilter').value = '';
    displayRecords(records);
}

// Drag and Drop functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(area => {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            area.addEventListener(eventName, function() {
                this.style.borderColor = '#1ec77c';
                this.style.background = '#f0fdf7';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, function() {
                this.style.borderColor = '#999';
                this.style.background = 'white';
            }, false);
        });

        // Handle dropped files
        area.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            
            // Determine type based on ID
            let type = 'cert';
            if (this.id.includes('marriage') || this.parentElement.id.includes('marriage')) {
                type = 'marriage';
            }
            
            // Add files to array
            uploadedFiles[type] = uploadedFiles[type].concat(Array.from(files));
            displayUploadedFiles(type);
            
            // Update the file input
            const fileInput = document.getElementById(type + 'FileInput');
            if (fileInput) {
                const dt = new DataTransfer();
                uploadedFiles[type].forEach(file => dt.items.add(file));
                fileInput.files = dt.files;
            }
        }, false);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 's' && isLoggedIn) {
            e.preventDefault();
            showPage('services');
        }
        if (e.altKey && e.key === 'r' && isLoggedIn) {
            e.preventDefault();
            showPage('records');
        }
    });
});
