let datasetInfo = null;
let fullDatasetVisible = false;
let currentNumericCols = [];


const CHART_COLORS = [
    '#ff6b6b', '#ffd93d', '#6bcb77', '#4d96ff', '#ff922b',
    '#cc5de8', '#20c997', '#f06595', '#74c0fc', '#a9e34b'
];

// ===== DYNAMIC GREETING =====
function updateGreeting() {
    const el = document.getElementById('dash-greeting');
    if (!el) return;
    const username = el.dataset.username || 'User';
    const hour = new Date().getHours();
    let greeting;
    if (hour < 12) greeting = 'Good Morning';
    else if (hour < 17) greeting = 'Good Afternoon';
    else if (hour < 21) greeting = 'Good Evening';
    else greeting = 'Good Night';
    el.textContent = `${greeting}, ${username}!`;
}
document.addEventListener('DOMContentLoaded', updateGreeting);

// ===== TOAST NOTIFICATION =====
function showToast(message, icon = 'fa-check-circle', type = 'success') {
    let toast = document.getElementById('toast-notif');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast-notif';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    const colors = {
        success: 'linear-gradient(135deg, #3b1f8c, #6c63ff)',
        warning: 'linear-gradient(135deg, #7a4f00, #ffd700)',
        error:   'linear-gradient(135deg, #7a0000, #ff6464)',
        info:    'linear-gradient(135deg, #004a7a, #00c8ff)',
    };
    toast.style.background = colors[type] || colors.success;
    toast.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), 3000);
}

// ===== NAVIGATION =====

function showSection(section, event) {
    if (event) event.preventDefault();

    document.querySelectorAll('.section').forEach(sec => {
        sec.classList.remove('active');
    });

    document.getElementById('section-' + section).classList.add('active');

    if (section === 'timeseries') {
        loadTimeSeriesColumns();
    }
    if (section === 'dashboard') {
        loadDashboardOverview();
    }
}

function togglePreviewMenu() {
    const submenu = document.getElementById('preview-submenu');
    const arrow   = document.getElementById('preview-arrow');
    if (submenu.style.display === 'none') {
        submenu.style.display = 'block';
        arrow.classList.replace('fa-chevron-down', 'fa-chevron-up');
    } else {
        submenu.style.display = 'none';
        arrow.classList.replace('fa-chevron-up', 'fa-chevron-down');
    }
}

function toggleAdvancedMenu() {
    const menu  = document.getElementById('advanced-submenu');
    const arrow = document.getElementById('advanced-arrow');
    if (menu.style.display === 'none') {
        menu.style.display = 'block';
        arrow.classList.replace('fa-chevron-down', 'fa-chevron-up');
    } else {
        menu.style.display = 'none';
        arrow.classList.replace('fa-chevron-up', 'fa-chevron-down');
    }
}


function toggleVizMenu() {
    const menu  = document.getElementById('viz-submenu');
    const arrow = document.getElementById('viz-arrow');
    if (menu.style.display === 'none') {
        menu.style.display = 'block';
        arrow.classList.replace('fa-chevron-down', 'fa-chevron-up');
    } else {
        menu.style.display = 'none';
        arrow.classList.replace('fa-chevron-up', 'fa-chevron-down');
    }
}

function showVizTab(tab, event) {
    if (event) event.preventDefault();
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById('section-visualization').classList.add('active');
    document.querySelectorAll('.viz-tab-content').forEach(t => t.style.display = 'none');
    document.getElementById('viz-tab-' + tab).style.display = 'block';

    const titles = {
        univariate: 'Univariate Analysis',
        bivariate: 'Bivariate Analysis',
        multivariate: 'Multivariate Analysis',
        catvsnum: 'Categorical vs Numerical Analysis',
        catvscat: 'Categorical vs Categorical Analysis',     
        numvsnum: 'Numerical vs Numerical Analysis'
    };
    document.getElementById('viz-section-title').textContent = titles[tab] || 'Visualizations';

    if (datasetInfo) {
        autoGenerateViz(tab);
    } else {
        const containerMap = {
            univariate:   ['uni-num-charts', 'uni-cat-charts'],
            bivariate:    ['bi-charts'],
            multivariate: ['multi-charts'],
            catvsnum:     ['cvn-charts'],
            catvscat:     ['cvc-charts'],
            numvsnum:     ['nvn-charts']
        };
        const sectionMap = {
            univariate:   ['univariate', 'categorical'],
            bivariate:    ['bivariate'],
            multivariate: ['multivariate'],
            catvsnum:     ['catvsnum'],
            catvscat:     ['catvscat'],
            numvsnum:     ['numvsnum']
        };
        const containers = containerMap[tab] || [];
        const sections   = sectionMap[tab] || [];
        containers.forEach((cId, i) => {
            const c = document.getElementById(cId);
            if (c && c.innerHTML.trim() === '') {
                loadDefaultCharts(sections[i], cId);
            }
        });
    }
}

function autoGenerateViz(tab) {
    if (tab === 'univariate') {
        const numSel = document.getElementById('uni-num-col');
        const catSel = document.getElementById('uni-cat-col');
        if (numSel && numSel.options.length > 1) {
            numSel.selectedIndex = 1;
            const c = document.getElementById('uni-num-charts');
            if (c && c.innerHTML.trim() === '') generateUnivariate('numerical');
        }
        if (catSel && catSel.options.length > 1) {
            catSel.selectedIndex = 1;
            const c = document.getElementById('uni-cat-charts');
            if (c && c.innerHTML.trim() === '') generateUnivariate('categorical');
        }

    } else if (tab === 'bivariate') {
        const col1 = document.getElementById('bi-col1');
        const col2 = document.getElementById('bi-col2');
        const c    = document.getElementById('bi-charts');
        if (col1 && col2 && col1.options.length > 2 && c && c.innerHTML.trim() === '') {
            col1.selectedIndex = 1;
            col2.selectedIndex = 2;
            generateBivariate();
        }

    } else if (tab === 'multivariate') {
        const c = document.getElementById('multi-charts');
        if (c && c.innerHTML.trim() === '') generateMultivariate();

    } else if (tab === 'catvsnum') {
        const numSel = document.getElementById('cvn-num-col');
        const catSel = document.getElementById('cvn-cat-col');
        const c      = document.getElementById('cvn-charts');

        if (numSel && catSel &&
            numSel.options.length > 1 &&
            catSel.options.length > 1 &&
            c && c.innerHTML.trim() === '') {

            numSel.selectedIndex = 1;
            catSel.selectedIndex = 1;
            generateCatVsNum();
        }

    } else if (tab === 'catvscat') {
        const col1 = document.getElementById('cvc-col1');
        const col2 = document.getElementById('cvc-col2');
        const c    = document.getElementById('cvc-charts');

        if (col1 && col2 &&
            col1.options.length > 1 &&
            col2.options.length > 1 &&
            c && c.innerHTML.trim() === '') {

            col1.selectedIndex = 1;
            col2.selectedIndex = col2.options.length > 2 ? 2 : 1;
            generateCatVsCat();
        }

    } else if (tab === 'numvsnum') {
        const col1 = document.getElementById('nvn-col1');
        const col2 = document.getElementById('nvn-col2');
        const c    = document.getElementById('nvn-charts');

        if (col1 && col2 &&
            col1.options.length > 1 &&
            col2.options.length > 1 &&
            c && c.innerHTML.trim() === '') {

            col1.selectedIndex = 1;
            col2.selectedIndex = col2.options.length > 2 ? 2 : 1;
            generateNumVsNum();
        }
    }
}

async function loadDefaultCharts(section, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const placeholders = {
        univariate: [
            { icon: '📊', title: 'Histogram', sub: 'Pilih kolom numerik untuk melihat distribusi' },
            { icon: '📦', title: 'Boxplot', sub: 'Deteksi outlier dan rentang data' },
            { icon: '〰️', title: 'Density Plot', sub: 'Estimasi distribusi probabilitas' },
            { icon: '📈', title: 'QQ Plot', sub: 'Uji normalitas distribusi data' },
            { icon: '🎻', title: 'Violin Plot', sub: 'Distribusi + boxplot dalam satu chart' },
        ],
        categorical: [
            { icon: '📊', title: 'Bar Chart', sub: 'Pilih kolom kategorikal untuk melihat frekuensi' },
            { icon: '🥧', title: 'Pie Chart', sub: 'Proporsi setiap kategori' },
            { icon: '📋', title: 'Count Plot', sub: 'Jumlah data per kategori' },
            { icon: '📉', title: 'Pareto Chart', sub: '80/20 rule — kategori dominan' },
        ],
        bivariate: [
            { icon: '✦', title: 'Scatter Plot', sub: 'Pilih 2 kolom numerik untuk melihat hubungan' },
            { icon: '🌡️', title: 'Correlation Heatmap', sub: 'Kekuatan hubungan antar variabel' },
            { icon: '📐', title: 'Regression Plot', sub: 'Garis regresi linear' },
            { icon: '🫧', title: 'Bubble Chart', sub: 'Scatter dengan dimensi ukuran tambahan' },
        ],
        multivariate: [
            { icon: '🌡️', title: 'Correlation Heatmap', sub: 'Pilih kolom-kolom numerik lalu Generate' },
            { icon: '🔢', title: 'Pair Plot', sub: 'Scatter matrix semua pasangan variabel' },
            { icon: '🫧', title: 'Bubble Chart', sub: 'Tiga dimensi dalam satu chart' },
        ],
        catvsnum: [
            { icon: '📦', title: 'Boxplot by Category', sub: 'Pilih kolom kategorikal & numerik' },
            { icon: '🎻', title: 'Violin by Category', sub: 'Distribusi per kategori' },
            { icon: '📊', title: 'Grouped Bar Chart', sub: 'Rata-rata nilai per kategori' },
            { icon: '•••', title: 'Strip Plot', sub: 'Sebaran titik data per kategori' },
        ],
        catvscat: [
            { icon: '📊', title: 'Grouped Bar Chart', sub: 'Pilih 2 kolom kategorikal untuk melihat hubungan' },
            { icon: '📊', title: 'Stacked Bar Chart', sub: 'Distribusi kategori secara bertumpuk' },
            { icon: '🌡️', title: 'Crosstab Heatmap', sub: 'Frekuensi kombinasi antar kategori' },
            { icon: '📊', title: 'Stacked Bar 100%', sub: 'Proporsi kategori secara persentase' },
        ],
        numvsnum: [
            { icon: '✦', title: 'Scatter Plot', sub: 'Pilih 2 kolom numerik untuk melihat hubungan' },
            { icon: '📐', title: 'Regression Plot', sub: 'Garis regresi linear antar dua variabel' },
            { icon: '🌡️', title: 'Density Heatmap', sub: 'Kepadatan distribusi 2D' },
            { icon: '📉', title: 'Residual Plot', sub: 'Analisis sisa/error dari regresi' },
        ],
    };

    const items = placeholders[section] || [];
    container.innerHTML = items.map(item => `
        <div class="chart-card" style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;opacity:0.75;">
            <div style="font-size:52px;margin-bottom:14px;line-height:1;">${item.icon}</div>
            <div style="font-size:15px;font-weight:700;color:#c4c6d8;margin-bottom:8px;">${item.title}</div>
            <div style="font-size:12px;color:#8b8fa8;text-align:center;max-width:200px;line-height:1.5;">${item.sub}</div>
        </div>
    `).join('');
}

function updatePDFButtons() {
    fetch('/cleaning/status')
        .then(r => r.json())
        .then(data => {
            const btnAfter = document.getElementById('btn-pdf-after');
            if (btnAfter) {
                if (data.is_cleaned) {
                    btnAfter.classList.remove('disabled-link');
                    btnAfter.title = '';
                } else {
                    btnAfter.classList.add('disabled-link');
                    btnAfter.title = 'Lakukan cleaning terlebih dahulu';
                }
            }
        });
}

function downloadPDF(event, cleaned = false) {
    if (event) event.preventDefault();
    if (cleaned) {
        fetch('/cleaning/status')
            .then(r => r.json())
            .then(data => {
                if (!data.is_cleaned) {
                    alert('❌ Data belum di-cleaning. Silakan lakukan cleaning terlebih dahulu.');
                    return;
                }
                window.location.href = `/download/pdf?cleaned=true`;
            });
    } else {
        window.location.href = `/download/pdf?cleaned=false`;
    }
}


document.addEventListener('DOMContentLoaded', updatePDFButtons);

// ===== FILE UPLOAD =====

document.getElementById('file-input').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) uploadFile(file);
});

const uploadArea = document.getElementById('upload-area');
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.background = 'rgba(108, 99, 255, 0.1)';
});
uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.background = 'transparent';
});
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.background = 'transparent';
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
});

// Dashboard's own upload widget (shown when no dataset is loaded yet)
// reuses the same #file-input + uploadFile() pipeline as the Upload Data page
const dashUploadArea = document.getElementById('dash-upload-area');
if (dashUploadArea) {
    dashUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dashUploadArea.style.background = 'rgba(108, 99, 255, 0.1)';
    });
    dashUploadArea.addEventListener('dragleave', () => {
        dashUploadArea.style.background = 'transparent';
    });
    dashUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dashUploadArea.style.background = 'transparent';
        const file = e.dataTransfer.files[0];
        if (file) uploadFile(file);
    });
}

function uploadFile(file) {
    const formData = new FormData();
    document.getElementById('upload-area').innerHTML = `
    <div style="text-align:center;padding:20px;">
        <div class="spinner"></div>
        <p style="color:#6c63ff;margin-top:12px;font-weight:600;">
            Uploading & processing dataset...
        </p>
        <p style="color:#8b8fa8;font-size:0.85rem;margin-top:4px;">
            Mohon tunggu sebentar
        </p>
    </div>`;
    formData.append('file', file);

    fetch('/upload', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('upload-area').innerHTML = `
    <i class="fas fa-cloud-upload-alt"></i>
    <p>Drag &amp; Drop your file here or click to browse</p>
    <small>Supported: CSV, Excel (.xlsx), Text (.txt)</small>
    <input type="file" id="file-input" accept=".csv,.xlsx,.txt" style="display:none;">
    <button class="btn" onclick="document.getElementById('file-input').click()">
        <i class="fas fa-folder-open"></i> Browse File
    </button>`;

                document.getElementById('file-input').addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) uploadFile(file);
                });

                datasetInfo = data.info;
                window.fullDataset = data.info.full_data;

                originalData = data.info.full_data;
                cleanedData = data.info.full_data;

                displayFullDataset(originalData);

                document.getElementById('upload-status').style.display = 'flex';
                document.getElementById('upload-message').innerText =
                    `${data.info.filename} uploaded successfully`;

                document.getElementById('summary-cards').style.display = 'grid';
                document.getElementById('card-rows').innerText      = data.info.rows;
                document.getElementById('card-cols').innerText      = data.info.columns;
                document.getElementById('card-numeric').innerText   = data.info.numeric_cols.length;
                document.getElementById('card-categorical').innerText = data.info.categorical_cols.length;
                document.getElementById('card-missing').innerText   = data.info.missing_total;

                const missingCard = document.getElementById('card-missing');
                if (data.info.missing_total > 100) {
                    missingCard.style.color = '#ff6464';
                } else if (data.info.missing_total > 0) {
                    missingCard.style.color = '#ffd700';
                } else {
                    missingCard.style.color = '#00c864';
                }

                displayDatasetInfo(data.info);
                displayPreview(data.info.preview);
                populateVizColumns(data.info);

                ['uni-num-charts','uni-cat-charts','bi-charts','multi-charts','cvn-charts','cvc-charts','nvn-charts'].forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.innerHTML = '';
                });

                loadNumericalStats();
                loadCategoricalStats();
                loadInsights();
                showDiagnosticReport(data.info);
                loadTimeSeriesColumns();
                loadDashboardOverview();
                // Re-generate timeseries setelah cleaning
                const tsCol = document.getElementById('ts-col-select')?.value;
                const dateCol = document.getElementById('date-column')?.value;
                if (dateCol && tsCol) generateTimeSeries();

                showToast(`${data.info.filename} berhasil diupload!`, 'fa-cloud-upload-alt', 'success');
            }
        })
        .catch(error => {
            console.error(error);
            showToast('Upload gagal!', 'fa-times-circle', 'error');
        });
}


// ===== DISPLAY DATASET INFO =====

function displayDatasetInfo(info) {
    let warningHTML = '';
    if (info.missing_total > 100) {
        warningHTML = `<div style="background:rgba(255,100,100,0.1);border-left:4px solid #ff6464;
                    border-radius:8px;padding:12px 15px;margin-bottom:15px;color:#ff6464;">
            <i class="fas fa-exclamation-triangle"></i>
            <strong> Peringatan:</strong> Terdeteksi ${info.missing_total} missing values 
            (${info.missing_percent}%). Silakan pilih metode cleaning di bawah.
        </div>`;
    } else if (info.missing_total > 0) {
        warningHTML = `<div style="background:rgba(255,215,0,0.1);border-left:4px solid #ffd700;
                    border-radius:8px;padding:12px 15px;margin-bottom:15px;color:#ffd700;">
            <i class="fas fa-exclamation-circle"></i>
            <strong> Perhatian:</strong> Terdeteksi ${info.missing_total} missing values 
            (${info.missing_percent}%). Pertimbangkan untuk melakukan cleaning.
        </div>`;
    } else {
        warningHTML = `<div style="background:rgba(0,200,100,0.1);border-left:4px solid #00c864;
                    border-radius:8px;padding:12px 15px;margin-bottom:15px;color:#00c864;">
            <i class="fas fa-check-circle"></i>
            <strong> Data Bersih:</strong> Tidak ada missing values ditemukan.
        </div>`;
    }

    document.getElementById('dataset-info').innerHTML = `
        ${warningHTML}
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-top:10px;">
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">FILENAME</p>
                <p style="color:#ffffff;font-weight:600;">${info.filename}</p>
            </div>
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">FILE SIZE</p>
                <p style="color:#ffffff;font-weight:600;">${info.file_size}</p>
            </div>
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">TOTAL ROWS</p>
                <p style="color:#6c63ff;font-weight:600;font-size:1.2rem;">${info.rows}</p>
            </div>
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">TOTAL COLUMNS</p>
                <p style="color:#6c63ff;font-weight:600;font-size:1.2rem;">${info.columns}</p>
            </div>
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">NUMERIC COLUMNS</p>
                <p style="color:#00c864;font-weight:600;">${info.numeric_cols.length} kolom</p>
                <p style="color:#8b8fa8;font-size:0.75rem;">${info.numeric_cols.join(', ')}</p>
            </div>
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">CATEGORICAL COLUMNS</p>
                <p style="color:#ffd700;font-weight:600;">${info.categorical_cols.length} kolom</p>
                <p style="color:#8b8fa8;font-size:0.75rem;">${info.categorical_cols.join(', ')}</p>
            </div>
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">DATETIME COLUMNS</p>
                <p style="color:#6c63ff;font-weight:600;">${info.datetime_cols.length > 0 ? info.datetime_cols.join(', ') : 'None'}</p>
            </div>
            <div style="background:#1a1d2e;border-radius:10px;padding:15px;border:1px solid #2d3148;">
                <p style="color:#8b8fa8;font-size:0.75rem;margin-bottom:5px;">MISSING VALUES</p>
                <p style="color:${info.missing_total > 0 ? '#ff6464' : '#00c864'};font-weight:600;font-size:1.2rem;">${info.missing_total}</p>
                <p style="color:#8b8fa8;font-size:0.75rem;">${info.missing_percent}%</p>
            </div>
        </div>
    `;
}


// ===== DIAGNOSTIC REPORT =====

function showDiagnosticReport(info) {
    const report  = document.getElementById('diagnostic-report');
    const content = document.getElementById('diagnostic-content');
    if (!report || !content) return;
    report.style.display = 'block';

    let issues = [];

    fetch('/stats/numerical')
        .then(r => r.json())
        .then(numData => {
            for (const col in numData) {
                const item = numData[col];
                if (item.missing_count > 0) {
                    issues.push({
                        col, type: 'Missing Values',
                        detail: `${item.missing_count} missing (${item.missing_percent}%)`,
                        severity: item.missing_percent > 10 ? 'high' : 'medium',
                        action: 'Fill Missing with Mean'
                    });
                }
                if (item.outliers > 10) {
                    issues.push({
                        col, type: 'Outliers Detected',
                        detail: `${item.outliers} outliers ditemukan`,
                        severity: 'medium',
                        action: 'Perlu diperhatikan'
                    });
                }
            }
            return fetch('/stats/categorical');
        })
        .then(r => r.json())
        .then(catData => {
            for (const col in catData) {
                const item = catData[col];
                if (item.missing_count > 0) {
                    issues.push({
                        col, type: 'Missing Values',
                        detail: `${item.missing_count} missing (${item.missing_percent}%)`,
                        severity: item.missing_percent > 10 ? 'high' : 'medium',
                        action: 'Fill Missing with Mode'
                    });
                }
                if (item.unique > 50) {
                    issues.push({
                        col, type: 'High Cardinality',
                        detail: `${item.unique} unique values — kemungkinan case inconsistent`,
                        severity: 'medium',
                        action: 'Standardize Text Case'
                    });
                }
            }

            if (issues.length === 0) {
                content.innerHTML = `
                    <div style="background:rgba(0,200,100,0.1);border-radius:10px;
                                padding:15px;color:#00c864;text-align:center;">
                        <i class="fas fa-check-circle"></i>
                        <strong> Data terlihat bersih!</strong> Tidak ada masalah signifikan ditemukan.
                    </div>`;
                return;
            }

            let html = `<div class="table-container"><table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
                <thead><tr>
                    <th style="background:#2d3148;padding:10px;color:#6c63ff;">Kolom</th>
                    <th style="background:#2d3148;padding:10px;color:#6c63ff;">Masalah</th>
                    <th style="background:#2d3148;padding:10px;color:#6c63ff;">Detail</th>
                    <th style="background:#2d3148;padding:10px;color:#6c63ff;">Severity</th>
                    <th style="background:#2d3148;padding:10px;color:#6c63ff;">Rekomendasi</th>
                </tr></thead><tbody>`;

            issues.forEach(issue => {
                const color = issue.severity === 'high' ? '#ff6464' : '#ffd700';
                html += `<tr>
                    <td style="padding:10px;border-bottom:1px solid #2d3148;color:#fff;">${issue.col}</td>
                    <td style="padding:10px;border-bottom:1px solid #2d3148;color:${color};">
                        <i class="fas fa-exclamation-triangle"></i> ${issue.type}
                    </td>
                    <td style="padding:10px;border-bottom:1px solid #2d3148;color:#c0c0c0;">${issue.detail}</td>
                    <td style="padding:10px;border-bottom:1px solid #2d3148;">
                        <span style="background:${color}33;color:${color};padding:3px 10px;
                                    border-radius:20px;font-size:0.75rem;">${issue.severity.toUpperCase()}</span>
                    </td>
                    <td style="padding:10px;border-bottom:1px solid #2d3148;color:#6c63ff;">${issue.action}</td>
                </tr>`;
            });

            html += '</tbody></table></div>';
            content.innerHTML = html;
        });
}


// ===== DISPLAY PREVIEW =====

function displayPreview(previewData) {
    if (previewData.length === 0) return;

    const columns = Object.keys(previewData[0]);

    let headHTML = '<tr>';
    columns.forEach(col => { headHTML += `<th>${col}</th>`; });
    headHTML += '</tr>';
    document.getElementById('preview-head').innerHTML = headHTML;

    let bodyHTML = '';
    previewData.forEach(row => {
        bodyHTML += '<tr>';
        columns.forEach(col => { bodyHTML += `<td>${row[col]}</td>`; });
        bodyHTML += '</tr>';
    });
    document.getElementById('preview-body').innerHTML = bodyHTML;

    const datatypeTable = document.getElementById('datatypeTable');
    if (datatypeTable && datasetInfo.auto_types) {
        datatypeTable.innerHTML = '';
        datasetInfo.auto_types.forEach(item => {
            let badge = '';
            if      (item.detected === 'Numerical')   badge = '<span class="badge num">Numerical</span>';
            else if (item.detected === 'Categorical')  badge = '<span class="badge cat">Categorical</span>';
            else if (item.detected === 'Datetime')     badge = '<span class="badge date">Datetime</span>';
            else                                       badge = '<span class="badge text">Text</span>';

            datatypeTable.innerHTML += `
                <tr>
                    <td>${item.column}</td>
                    <td>${item.dtype}</td>
                    <td>${badge}</td>
                </tr>`;
        });
    }
}


// ===== STATS =====

function loadNumericalStats() {
    fetch('/stats/numerical')
        .then(response => response.json())
        .then(data => {
            let html = '';
            for (const col in data) {
                const item = data[col];
                const badge = item.normality === 'Normal'
                    ? `<span class="badge-normal">Normal</span>`
                    : `<span class="badge-notnormal">Not Normal</span>`;
                const missingClass  = item.missing_percent > 10 ? 'cell-red' : item.missing_percent > 0 ? 'cell-yellow' : 'cell-green';
                const outlierClass  = item.outliers > 10 ? 'cell-red' : item.outliers > 0 ? 'cell-yellow' : 'cell-green';
                const skewnessClass = Math.abs(item.skewness) > 1 ? 'cell-red' : Math.abs(item.skewness) > 0.5 ? 'cell-yellow' : 'cell-green';
                html += `<tr>
                    <td>${col}</td>
                    <td>${item.mean}</td><td>${item.median}</td>
                    <td>${item.min}</td><td>${item.max}</td>
                    <td>${item.std}</td><td>${item.variance}</td><td>${item.mode}</td>
                    <td class="${skewnessClass}">${item.skewness}</td>
                    <td>${item.kurtosis}</td>
                    <td class="${missingClass}">${item.missing_count}</td>
                    <td class="${missingClass}">${item.missing_percent}%</td>
                    <td>${badge}</td>
                    <td class="${outlierClass}">${item.outliers}</td>
                </tr>`;
            }
            document.getElementById('numerical-body').innerHTML = html;
        });
}

function loadCategoricalStats() {
    fetch('/stats/categorical')
        .then(response => response.json())
        .then(data => {
            let html = '';
            for (const col in data) {
                const item = data[col];
                html += `<tr>
                    <td>${col}</td><td>${item.unique}</td><td>${item.mode}</td>
                    <td>${item.mode_freq}</td><td>${item.mode_percent}%</td>
                    <td>${item.missing_count}</td><td>${item.missing_percent}%</td>
                </tr>`;
            }
            document.getElementById('categorical-body').innerHTML = html;
        });
}


// ===== INSIGHTS =====

function loadInsights() {
    fetch('/insights')
        .then(response => response.json())
        .then(data => {
            let html = '';
            data.forEach(insight => {
                html += `<div class="insight-item">
                    <i class="fas fa-lightbulb"></i>
                    <span>${insight}</span>
                </div>`;
            });
            const insightBox = document.getElementById('insights-container');
            if (insightBox) insightBox.innerHTML = html;
        });
}


// ===== VISUALIZATIONS =====

function populateVizColumns(info) {
    const numericGroup     = document.getElementById('numeric-options');
    const categoricalGroup = document.getElementById('categorical-options');
    if (numericGroup)     numericGroup.innerHTML = '';
    if (categoricalGroup) categoricalGroup.innerHTML = '';

    info.numeric_cols.forEach(col => {
        if (numericGroup)
            numericGroup.innerHTML += `<option value="${col}">${col}</option>`;
    });
    info.categorical_cols.forEach(col => {
        if (categoricalGroup)
            categoricalGroup.innerHTML += `<option value="${col}">${col}</option>`;
    });

    const uniNum = document.getElementById('uni-num-col');
    if (uniNum) {
        uniNum.innerHTML = '<option value="">-- Select Column --</option>';
        info.numeric_cols.forEach(col => {
            uniNum.innerHTML += `<option value="${col}">${col}</option>`;
        });
    }

    const uniCat = document.getElementById('uni-cat-col');
    if (uniCat) {
        uniCat.innerHTML = '<option value="">-- Select Column --</option>';
        // Filter: buang kolom datetime yang nyasar ke categorical
        const pureCatCols = info.categorical_cols.filter(col =>
            !(info.datetime_cols || []).includes(col)
        );
        pureCatCols.forEach(col => {
            uniCat.innerHTML += `<option value="${col}">${col}</option>`;
        });
    }

    const biCol1 = document.getElementById('bi-col1');
    const biCol2 = document.getElementById('bi-col2');
    if (biCol1 && biCol2) {
        [biCol1, biCol2].forEach(sel => {
            sel.innerHTML = '<option value="">-- Select Column --</option>';
            info.numeric_cols.forEach(col => {
                sel.innerHTML += `<option value="${col}">${col}</option>`;
            });
        });
        if (info.numeric_cols.length >= 2) {
            biCol1.value = info.numeric_cols[0];
            biCol2.value = info.numeric_cols[1];
        }
    }

    const checkboxList = document.getElementById('multi-checkbox-list');
    if (checkboxList) {
        checkboxList.innerHTML = '';
        info.numeric_cols.forEach((col, i) => {
            const label = document.createElement('label');
            label.style.cssText = 'display:flex;align-items:center;gap:8px;color:#e0e0e0;font-size:0.85rem;cursor:pointer;';
            const cb = document.createElement('input');
            cb.type    = 'checkbox';
            cb.value   = col;
            cb.checked = i < 3;
            cb.style.cssText = 'accent-color:#6c63ff;width:15px;height:15px;cursor:pointer;';
            label.appendChild(cb);
            label.appendChild(document.createTextNode(col));
            checkboxList.appendChild(label);
        });
    }

    const multiHue    = document.getElementById('multi-hue');
    const multiBubble = document.getElementById('multi-bubble');
    if (multiHue) {
        multiHue.innerHTML = '<option value="">-- None --</option>';
        info.categorical_cols.forEach(col => {
            multiHue.innerHTML += `<option value="${col}">${col}</option>`;
        });
    }
    if (multiBubble) {
        multiBubble.innerHTML = '<option value="">-- None --</option>';
        info.numeric_cols.forEach(col => {
            multiBubble.innerHTML += `<option value="${col}">${col}</option>`;
        });
    }

    const cvnNum = document.getElementById('cvn-num-col');
    const cvnCat = document.getElementById('cvn-cat-col');
    if (cvnNum && cvnCat) {
        cvnNum.innerHTML = '<option value="">-- Select --</option>';
        cvnCat.innerHTML = '<option value="">-- Select --</option>';
        info.numeric_cols.forEach(col => {
            cvnNum.innerHTML += `<option value="${col}">${col}</option>`;
        });
        info.categorical_cols.forEach(col => {
            cvnCat.innerHTML += `<option value="${col}">${col}</option>`;
        });
        if (info.numeric_cols.length)     cvnNum.value = info.numeric_cols[0];
        if (info.categorical_cols.length) cvnCat.value = info.categorical_cols[0];
    }

    // ===== CAT VS CAT =====
    const cvcCol1 = document.getElementById('cvc-col1');
    const cvcCol2 = document.getElementById('cvc-col2');
    if (cvcCol1 && cvcCol2) {
        cvcCol1.innerHTML = '<option value="">-- Select --</option>';
        cvcCol2.innerHTML = '<option value="">-- Select --</option>';

        // Filter: hanya kolom categorical, BUKAN datetime cols
        const pureCatCols = info.categorical_cols.filter(col =>
            !(info.datetime_cols || []).includes(col)
        );

        pureCatCols.forEach(col => {
            cvcCol1.innerHTML += `<option value="${col}">${col}</option>`;
            cvcCol2.innerHTML += `<option value="${col}">${col}</option>`;
        });
        if (pureCatCols.length >= 1) cvcCol1.value = pureCatCols[0];
        if (pureCatCols.length >= 2) cvcCol2.value = pureCatCols[1];
    }

    // ===== NUM VS NUM =====
    const nvnCol1 = document.getElementById('nvn-col1');
    const nvnCol2 = document.getElementById('nvn-col2');
    if (nvnCol1 && nvnCol2) {
        nvnCol1.innerHTML = '<option value="">-- Select --</option>';
        nvnCol2.innerHTML = '<option value="">-- Select --</option>';
        info.numeric_cols.forEach(col => {
            nvnCol1.innerHTML += `<option value="${col}">${col}</option>`;
            nvnCol2.innerHTML += `<option value="${col}">${col}</option>`;
        });
        if (info.numeric_cols.length >= 1) nvnCol1.value = info.numeric_cols[0];
        if (info.numeric_cols.length >= 2) nvnCol2.value = info.numeric_cols[1];
    }
}

let lastVizTab    = null;
let lastVizParams = null;

function refreshVisualizations() {
    if (!datasetInfo) { showToast('Upload data dulu!', 'fa-exclamation-circle', 'warning'); return; }

    loadNumericalStats();
    loadCategoricalStats();
    loadInsights();

    lastVizTab = null;
    lastVizParams = null;
    ['uni-num-charts','uni-cat-charts','bi-charts','multi-charts','cvn-charts','cvc-charts','nvn-charts'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });

    showVizTab('univariate', null);
    showToast('Visualisasi berhasil di-refresh', 'fa-sync-alt', 'success');
    // Re-generate timeseries
    const tsCol = document.getElementById('ts-col-select')?.value;
    const dateCol = document.getElementById('date-column')?.value;
    if (dateCol && tsCol) generateTimeSeries();
}


// ===== VIZ TAB SWITCHING =====

function switchVizTab(tab, btn) {
    document.querySelectorAll('.viz-tab-content').forEach(t => t.style.display = 'none');
    document.querySelectorAll('.viz-tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('viz-tab-' + tab).style.display = 'block';
    btn.classList.add('active');
}

function switchUniSub(sub, btn) {
    document.querySelectorAll('.uni-sub-content').forEach(t => t.style.display = 'none');
    document.querySelectorAll('.viz-sub-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('uni-sub-' + sub).style.display = 'block';
    if (btn) {
        btn.classList.add('active');
    } else {
        document.querySelectorAll('.viz-sub-btn').forEach(b => {
            const onclickAttr = b.getAttribute('onclick') || '';
            if (onclickAttr.includes(`'${sub}'`)) b.classList.add('active');
        });
    }
}

// ===== RENDER CHART GRID =====

function renderChartGrid(containerId, charts, fullWidthTitles = []) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    const isMultivariate = containerId === 'multi-charts';

    const grid = document.createElement('div');
    grid.style.cssText = `
        display:grid;
        grid-template-columns:1fr;
        gap:24px;
        width:100%;
    `;
    container.appendChild(grid);

    const hasOddItem = !isMultivariate && charts.length % 2 === 1;

    charts.forEach((item, i) => {

        const isFullWidth =
            isMultivariate ||
            fullWidthTitles.includes(item.title);

        const isLastOdd =
            hasOddItem &&
            i === charts.length - 1;

        const wrapper = document.createElement('div');

        if (isFullWidth) {
            wrapper.style.cssText = `
                grid-column: 1 / -1;
                width: 100%;
                overflow: hidden;
                background: linear-gradient(135deg, #3b1f8c, #6c63ff);
                border-radius: 12px;
                padding: 16px;
                border: 1px solid rgba(108,99,255,0.3);
                box-sizing: border-box;
            `;
        }
        else if (isLastOdd) {
            wrapper.style.cssText = `
                grid-column: 1 / -1;
                width: 100%;
                overflow: hidden;
                background: linear-gradient(135deg, #3b1f8c, #6c63ff);
                border-radius: 12px;
                padding: 16px;
                border: 1px solid rgba(108,99,255,0.3);
                box-sizing: border-box;
            `;
        }
        else {
            wrapper.style.cssText = `
                width: 100%;
                min-width: 0;
                overflow: hidden;
                background: linear-gradient(135deg, #3b1f8c, #6c63ff);
                border-radius: 12px;
                padding: 16px;
                border: 1px solid rgba(108,99,255,0.3);
                box-sizing: border-box;
            `;
        }

        const titleEl = document.createElement('div');
        titleEl.textContent = item.title;
        titleEl.style.cssText = `
            color: #ffffff;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            padding-left: 2px;
        `;

        const chartEl = document.createElement('div');
        chartEl.id = containerId + '-chart-' + i;

        chartEl.style.cssText = `
            width:100%;
            max-width:100%;
            min-width:0;
            display:block;
            height:${item.title === 'Pair Plot' ? 900 : 500}px;
        `;

        wrapper.appendChild(titleEl);
        wrapper.appendChild(chartEl);
        grid.appendChild(wrapper);

        const parsed = JSON.parse(item.chart);

        parsed.layout.paper_bgcolor = '#2a1060';
        parsed.layout.plot_bgcolor  = '#1a0a4a';

        parsed.layout.margin = {
            l: 60,
            r: 20,
            t: 20,
            b: 60
        };

        parsed.layout.height =
            item.title === 'Pair Plot' ? 900 : 500;


        delete parsed.layout.width;
        parsed.layout.autosize = true;

    
        Plotly.newPlot(chartEl.id, parsed.data, parsed.layout, {
            responsive: true,
            displayModeBar: true
        }).then(() => {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    const w = chartEl.getBoundingClientRect().width;
                    Plotly.relayout(chartEl.id, {
                        width: w || chartEl.offsetWidth,
                        autosize: false
                    });
                });
            });
        });
    });

    setTimeout(() => {
        charts.forEach((item, i) => {
            const el = document.getElementById(containerId + '-chart-' + i);
            if (el) Plotly.Plots.resize(el);
        });
    }, 300);

    setTimeout(() => {
        charts.forEach((item, i) => {
            const el = document.getElementById(containerId + '-chart-' + i);
            if (el) Plotly.Plots.resize(el);
        });
    }, 800);
}

function showChartLoading(containerId) {
    document.getElementById(containerId).innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:50px;">
            <div class="spinner"></div>
            <p style="color:#8b8fa8;margin-top:15px;">Generating charts...</p>
        </div>`;
}

// ===== UNIVARIATE =====

async function generateUnivariate(varType) {
    lastVizTab    = 'univariate';
    lastVizParams = { varType };
    const col = varType === 'numerical'
        ? document.getElementById('uni-num-col').value
        : document.getElementById('uni-cat-col').value;

    if (!col) { showToast('Pilih kolom terlebih dahulu!', 'fa-exclamation-circle', 'warning'); return; }

    const containerId = varType === 'numerical' ? 'uni-num-charts' : 'uni-cat-charts';
    showChartLoading(containerId);

    try {
        const res  = await fetch('/visualize/univariate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column: col, var_type: varType })
        });
        const data = await res.json();
        if (data.error) { showToast('Error: ' + data.error, 'fa-times-circle', 'error'); return; }
        renderChartGrid(containerId, data.charts);
    } catch (err) {
        console.error(err);
        showToast('Gagal generate chart.', 'fa-times-circle', 'error');
    }
}

// ===== BIVARIATE =====

async function generateBivariate() {
    lastVizTab    = 'bivariate';
    lastVizParams = {};
    const col1 = document.getElementById('bi-col1').value;
    const col2 = document.getElementById('bi-col2').value;
    if (!col1 || !col2)  { showToast('Pilih 2 kolom!', 'fa-exclamation-circle', 'warning'); return; }
    if (col1 === col2)   { showToast('Pilih kolom yang berbeda!', 'fa-exclamation-circle', 'warning'); return; }
    showChartLoading('bi-charts');
    try {
        const res  = await fetch('/visualize/bivariate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ col1, col2 })
        });
        const data = await res.json();
        if (data.error) { showToast('Error: ' + data.error, 'fa-times-circle', 'error'); return; }
        renderChartGrid('bi-charts', data.charts, ['Regression Plot']);
    } catch (err) { showToast('Gagal generate chart.', 'fa-times-circle', 'error'); }
}

// ===== MULTIVARIATE =====

async function generateMultivariate() {
    lastVizTab    = 'multivariate';
    lastVizParams = {};
    const columns = Array.from(
        document.querySelectorAll('#multi-checkbox-list input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    const hue        = document.getElementById('multi-hue')?.value    || null;
    const bubbleSize = document.getElementById('multi-bubble')?.value || null;
    if (columns.length < 2) { showToast('Pilih minimal 2 kolom!', 'fa-exclamation-circle', 'warning'); return; }
    showChartLoading('multi-charts');
    try {
        const res  = await fetch('/visualize/multivariate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns, hue, bubble_size: bubbleSize })
        });
        const data = await res.json();
        if (data.error) { showToast('Error: ' + data.error, 'fa-times-circle', 'error'); return; }
        renderChartGrid('multi-charts', data.charts);
    } catch (err) { showToast('Gagal generate chart.', 'fa-times-circle', 'error'); }
}

// ===== CAT VS NUM =====

async function generateCatVsNum() {
    lastVizTab    = 'catvsnum';
    lastVizParams = {};
    const numCol = document.getElementById('cvn-num-col').value;
    const catCol = document.getElementById('cvn-cat-col').value;

    if (!numCol || !catCol) { showToast('Pilih kolom numerik dan kategorikal!', 'fa-exclamation-circle', 'warning'); return; }

    showChartLoading('cvn-charts');

    try {
        const res  = await fetch('/visualize/cat-vs-num', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ num_col: numCol, cat_col: catCol })
        });
        const data = await res.json();
        if (data.error) { showToast('Error: ' + data.error, 'fa-times-circle', 'error'); return; }
        renderChartGrid('cvn-charts', data.charts);
    } catch (err) {
        console.error(err);
        showToast('Gagal generate chart.', 'fa-times-circle', 'error');
    }
}

// ===== CAT VS CAT =====

async function generateCatVsCat() {
    lastVizTab    = 'catvscat';
    lastVizParams = {};

    const col1 = document.getElementById('cvc-col1').value;
    const col2 = document.getElementById('cvc-col2').value;

    if (!col1 || !col2) {
        showToast('Pilih 2 kolom kategorikal!', 'fa-exclamation-circle', 'warning');
        return;
    }

    showChartLoading('cvc-charts');

    try {
        const res = await fetch('/visualize/cat-vs-cat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ col1, col2 })
        });

        const data = await res.json();

        if (data.error) {
            showToast('Error: ' + data.error, 'fa-times-circle', 'error');
            return;
        }

        renderChartGrid('cvc-charts', data.charts);

    } catch (err) {
        console.error(err);
        showToast('Gagal generate chart.', 'fa-times-circle', 'error');
    }
}

// ===== NUM VS NUM =====

async function generateNumVsNum() {
    lastVizTab    = 'numvsnum';
    lastVizParams = {};

    const col1 = document.getElementById('nvn-col1').value;
    const col2 = document.getElementById('nvn-col2').value;

    if (!col1 || !col2) {
        showToast('Pilih 2 kolom numerik!', 'fa-exclamation-circle', 'warning');
        return;
    }

    showChartLoading('nvn-charts');

    try {
        const res = await fetch('/visualize/num-vs-num', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ col1, col2 })
        });

        const data = await res.json();

        if (data.error) {
            showToast('Error: ' + data.error, 'fa-times-circle', 'error');
            return;
        }

        renderChartGrid('nvn-charts', data.charts);

    } catch (err) {
        console.error(err);
        showToast('Gagal generate chart.', 'fa-times-circle', 'error');
    }
}

// ===== DATA CLEANING =====

function cleanData(method) {
    fetch('/clean', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({method})
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            cleanedData = data.full_data;
            displayPreview(data.preview);
            displayFullDataset(data.full_data);
            document.getElementById('card-missing').innerText = data.after_missing;
            document.getElementById('card-rows').innerText = data.rows;

            if (datasetInfo) {
                datasetInfo.missing_total   = data.after_missing;
                datasetInfo.missing_percent = data.missing_percent  !== undefined ? data.missing_percent  : datasetInfo.missing_percent;
                datasetInfo.duplicate_count = data.duplicate_count  !== undefined ? data.duplicate_count  : 0;
                datasetInfo.duplicate_percent = data.duplicate_percent !== undefined ? data.duplicate_percent : 0;
                datasetInfo.outlier_count =
                    data.outlier_count !== undefined
                    ? data.outlier_count
                    : datasetInfo.outlier_count;

                datasetInfo.outlier_percent =
                    data.outlier_percent !== undefined
                    ? data.outlier_percent
                    : datasetInfo.outlier_percent;
                datasetInfo.rows = data.rows;
            }

            if (data.numeric_cols && data.categorical_cols) {
                if (datasetInfo) {
                    datasetInfo.numeric_cols = data.numeric_cols;
                    datasetInfo.categorical_cols = data.categorical_cols;
                }
                populateVizColumns({
                    numeric_cols: data.numeric_cols,
                    categorical_cols: data.categorical_cols
                });
                ['uni-num-charts','uni-cat-charts','bi-charts','multi-charts','cvn-charts','cvc-charts','nvn-charts'].forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.innerHTML = '';
                });
            }

            const cleanStatus = document.getElementById('clean-status');
            if (cleanStatus) cleanStatus.style.display = 'inline';

            loadNumericalStats();
            loadCategoricalStats();
            loadInsights();
            renderDataQuality();

            showToast('Cleaning berhasil diterapkan!', 'fa-check-circle', 'success');
        }
    });
}

function selectAllCleaning() {
    document.querySelectorAll('.cleaning-checklist input').forEach(cb => { cb.checked = true; });
}

async function cleanSelected() {
    const selected = [];
    document.querySelectorAll('.cleaning-checklist input:checked').forEach(cb => {
        selected.push(cb.value);
    });

    if (selected.length === 0) {
        showToast('Pilih minimal satu cleaning tool', 'fa-exclamation-circle', 'warning');
        return;
    }

    let lastData = null;

    for (const method of selected) {
        const response = await fetch('/clean', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ method })
        });
        const data = await response.json();

        if (data.status === 'success') {
            lastData = data;
            cleanedData = data.full_data;
            displayPreview(data.preview);
            displayFullDataset(data.full_data);
            document.getElementById('card-missing').innerText = data.after_missing;
            document.getElementById('card-rows').innerText = data.rows;
        }
    }

    if (lastData && lastData.numeric_cols && lastData.categorical_cols) {
        if (datasetInfo) {
            datasetInfo.numeric_cols = lastData.numeric_cols;
            datasetInfo.categorical_cols = lastData.categorical_cols;
        }
        populateVizColumns({
            numeric_cols: lastData.numeric_cols,
            categorical_cols: lastData.categorical_cols
        });
        lastVizTab = null;
        lastVizParams = null;
        ['uni-num-charts','uni-cat-charts','bi-charts','multi-charts','cvn-charts','cvc-charts','nvn-charts'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '';
        });
    }
    if (datasetInfo && lastData) {
        datasetInfo.missing_percent = lastData.missing_percent;
        datasetInfo.duplicate_percent = lastData.duplicate_percent;
        datasetInfo.outlier_percent = lastData.outlier_percent;

        datasetInfo.duplicate_count = lastData.duplicate_count;
        datasetInfo.outlier_count = lastData.outlier_count;

        datasetInfo.rows = lastData.rows;
    }

    renderDataQuality();
    showToast('Cleaning selesai!', 'fa-check-circle', 'success');
    loadNumericalStats();
    loadCategoricalStats();
    loadInsights();
}

async function undoCleaning() {
    const response = await fetch('/undo_cleaning', { method: 'POST' });
    const result = await response.json();

    if (result.status === 'success') {
        cleanedData = result.full_data;
        displayPreview(result.preview);
        document.getElementById('card-rows').innerText = result.rows;
        document.getElementById('card-missing').innerText = result.missing_total;
        loadNumericalStats();
        loadCategoricalStats();
        loadInsights();
        showToast('Dataset dikembalikan ke kondisi awal', 'fa-undo', 'info');
        
        // ── Mengunci kembali tombol download PDF After secara interaktif ──
        if (typeof updatePDFButtons === 'function') { 
            updatePDFButtons(); 
        }
    }
}

async function saveCleanedDataset() {
    const response = await fetch('/save_cleaned', { method: 'POST' });
    const result = await response.json();
    if (result.status === 'success') {
        showToast('Dataset berhasil disimpan: ' + result.filename, 'fa-save', 'success');
        
        // Mengaktifkan tombol download PDF After secara interaktif tanpa reload
        if (typeof updatePDFButtons === 'function') { 
            updatePDFButtons(); 
        }
    }
}

function downloadCleanedDataset() {
    window.location.href = '/download_cleaned';
    showToast('Mengunduh dataset...', 'fa-download', 'info');
}


// ===== FULL DATASET TOGGLE =====

function toggleFullDataset() {
    const container = document.getElementById('fullDatasetContainer');
    const btn       = document.getElementById('viewAllBtn');
    if (!fullDatasetVisible) {
        displayFullDataset(window.fullDataset);
        container.style.display = 'block';
        btn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Full Dataset';
        fullDatasetVisible = true;
    } else {
        container.style.display = 'none';
        btn.innerHTML = '<i class="fas fa-table"></i> View Full Dataset';
        fullDatasetVisible = false;
    }
}

function displayFullDataset(data) {
    if (!data || data.length === 0) return;
    const columns = Object.keys(data[0]);

    let headHTML = '<tr>';
    columns.forEach(col => { headHTML += `<th>${col}</th>`; });
    headHTML += '</tr>';
    document.getElementById('full-head').innerHTML = headHTML;

    let bodyHTML = '';
    data.forEach(row => {
        bodyHTML += '<tr>';
        columns.forEach(col => { bodyHTML += `<td>${row[col]}</td>`; });
        bodyHTML += '</tr>';
    });
    document.getElementById('full-body').innerHTML = bodyHTML;
}


// ===== THEME =====

function toggleTheme() {
    document.body.classList.toggle('light-mode');
    const btn = document.getElementById('theme-btn');
    if (document.body.classList.contains('light-mode')) {
        btn.innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
    } else {
        btn.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
    }
}


let originalData = [];
let cleanedData = [];

function showBeforeData() {
    displayPreview(originalData);
    document.getElementById('beforeBtn').classList.add('active');
    document.getElementById('afterBtn').classList.remove('active');
}

function showAfterData() {
    displayPreview(cleanedData);
    document.getElementById('afterBtn').classList.add('active');
    document.getElementById('beforeBtn').classList.remove('active');
}

async function loadTimeSeriesColumns() {
    try {
        const response = await fetch('/timeseries');
        const data = await response.json();
        const dateSelect = document.getElementById('date-column');
        if (!dateSelect) return;

        dateSelect.innerHTML = '<option value="">-- Select Date Column --</option>';
        data.date_cols.forEach(col => {
            dateSelect.innerHTML += `<option value="${col}">${col}</option>`;
        });

        const skipCols = ['order_id', 'id'];
        currentNumericCols = data.numeric_cols.filter(col =>
            !skipCols.some(skip => col.toLowerCase().includes(skip))
        );

        if (data.date_cols.length === 0) {
            document.getElementById('timeseries-chart').innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 40px;text-align:center;">
        <i class="fas fa-calendar-times" style="font-size:64px;margin-bottom:20px;color:#ff6464;"></i>
        <p style="font-size:22px;font-weight:700;color:#ff6464;margin-bottom:12px;">Tidak ada kolom tanggal ditemukan</p>
        <p style="font-size:15px;color:#8b8fa8;line-height:1.6;">Pastikan file CSV kamu memiliki kolom bertipe tanggal<br>(contoh: order_date, tanggal, date, dll)</p>
    </div>`;
            return;
        }

        // 1. Isi dropdown variabel numerik terlebih dahulu agar tidak kosong
        const tsColSelect = document.getElementById('ts-col-select');
        if (tsColSelect) {
            tsColSelect.innerHTML = '<option value="">-- Select Variable --</option>';
            currentNumericCols.forEach(col => {
                tsColSelect.innerHTML += `<option value="${col}">${col}</option>`;
            });
            // Set default ke variabel index pertama
            if (currentNumericCols.length > 0) {
                tsColSelect.value = currentNumericCols[0];
            }
        }

        // 2. Set default tanggal dan panggil otomatis untuk 1 kolom pertama
        if (data.date_cols.length > 0) {
            dateSelect.value = data.date_cols[0];
            if (tsColSelect && tsColSelect.value) {
                generateTimeSeries();
            }
        }
    } catch (err) {
        console.error('Gagal load kolom time series:', err);
    }
}

async function generateTimeSeries() {
    const dateCol = document.getElementById('date-column').value;
    const selectedCol = document.getElementById('ts-col-select')?.value;

    if (!dateCol || !selectedCol) {
        showToast('Pilih kolom tanggal dan variabel!', 'fa-exclamation-circle', 'warning');
        return;
    }

    try {
        const response = await fetch('/generate_timeseries', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date_col: dateCol, numeric_cols: [selectedCol] })
        });

        const data = await response.json();
        if (data.error) { showToast('Error: ' + data.error, 'fa-times-circle', 'error'); return; }

        const chartContainer = document.getElementById('timeseries-chart');
        const insightContainer = document.getElementById('timeseries-insight');
        chartContainer.innerHTML = '';
        chartContainer.style.cssText = 'display:block;';
        insightContainer.innerHTML = '';

        const div = document.createElement('div');
        div.style.cssText = 'background:#1e2140;border-radius:12px;padding:15px;border:1px solid #3d3f6b;';
        chartContainer.appendChild(div);

        const chartDiv = document.createElement('div');
        chartDiv.id = 'ts-chart-0';
        div.appendChild(chartDiv);

        const chart = JSON.parse(data.charts[0]);
        chart.layout.paper_bgcolor = '#1e2140';
        chart.layout.plot_bgcolor = '#252847';
        chart.layout.height = 420;
        Plotly.newPlot('ts-chart-0', chart.data, chart.layout, { responsive: true });

        const insightDiv = document.createElement('div');
        insightDiv.className = 'insight-item';
        insightDiv.style.marginTop = '10px';
        insightDiv.innerHTML = `<i class="fas fa-lightbulb"></i> ${data.insights[0]}`;
        div.appendChild(insightDiv);

    } catch (err) {
        console.error('Gagal generate time series:', err);
        showToast('Terjadi error saat generate time series.', 'fa-times-circle', 'error');
    }
}

function openMemberModal() {
    document.getElementById('memberModalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeMemberModal(e) {
    const overlay = document.getElementById('memberModalOverlay');
    if (!e || e.target === overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeMemberModal();
});

function toggleReportMenu() {
    const menu = document.getElementById('report-submenu');
    const arrow = document.getElementById('report-arrow');
    if (menu.style.display === 'none') {
        menu.style.display = 'block';
        arrow.classList.replace('fa-chevron-down', 'fa-chevron-up');
    } else {
        menu.style.display = 'none';
        arrow.classList.replace('fa-chevron-up', 'fa-chevron-down');
    }
}

function exportExcel(event) {
    if (event) event.preventDefault();
    window.open('/download/excel', '_blank');
    showToast('Mengunduh Excel...', 'fa-file-excel', 'info');
}

function exportCSV(event) {
    if (event) event.preventDefault();
    window.open('/download/csv', '_blank');
    showToast('Mengunduh CSV...', 'fa-file-csv', 'info');
}

// ===== DATA CLEANING TOOLS =====
const cleaningTools = [
  { id: 'drop', label: 'Drop Missing Values' },
  { id: 'mean', label: 'Fill with Mean' },
  { id: 'mode', label: 'Fill with Mode' },
  { id: 'dup',  label: 'Remove Duplicates' },
  { id: 'col',  label: 'Standardize Columns' },
  { id: 'text', label: 'Standardize Text Case' },
  { id: 'zsc',  label: 'Z-Score Normalize' },
];
const cleanSt = {};
cleaningTools.forEach(t => cleanSt[t.id] = false);
const cleanActionBtns = ['btn-selall','btn-clean','btn-reset','btn-refresh','btn-save','btn-dl'];

function setCleanActive(el) {
  cleanActionBtns.forEach(id => document.getElementById(id).classList.remove('active'));
  el.classList.add('active');
}
function renderCleanGrid() {
  document.getElementById('cleaning-grid').innerHTML = cleaningTools.map(t => `
    <div class="cw-item ${cleanSt[t.id]?'on':''}" id="ci_${t.id}" onclick="togClean('${t.id}')">
      <span class="cw-dot"></span>
      <span class="cw-lbl">${t.label}</span>
      <label class="cw-tog" onclick="event.stopPropagation()">
        <input type="checkbox" ${cleanSt[t.id]?'checked':''} onchange="togCleanCb('${t.id}',this.checked)">
        <span class="cw-sl"></span>
      </label>
    </div>`).join('');
  document.getElementById('cnt').textContent = Object.values(cleanSt).filter(Boolean).length + ' selected';
}
function togClean(id) { cleanSt[id]=!cleanSt[id]; renderCleanGrid(); }
function togCleanCb(id,v) { cleanSt[id]=v; document.getElementById('ci_'+id).classList.toggle('on',v); document.getElementById('cnt').textContent=Object.values(cleanSt).filter(Boolean).length+' selected'; }

function selAll(el) {
  setCleanActive(el);
  cleaningTools.forEach(t=>cleanSt[t.id]=true);
  renderCleanGrid();
  showToast('Semua operasi dipilih', 'fa-check-double', 'success');
}

function cwResetAll(el) {
  setCleanActive(el);
  cleaningTools.forEach(t=>cleanSt[t.id]=false);
  renderCleanGrid();
  document.getElementById('clean-status').textContent='Select an operation then click Clean';
  showToast('Reset berhasil', 'fa-redo', 'info');
}

function cwCleanSelected(el) {
  setCleanActive(el);
  const s = cleaningTools.filter(t => cleanSt[t.id]);
  if (s.length === 0) {
    document.getElementById('clean-status').textContent='No operation selected';
    showToast('Pilih minimal satu operasi!', 'fa-exclamation-circle', 'warning');
    return;
  }
  const idMap = { drop:'drop', mean:'fill_mean', mode:'fill_mode', dup:'remove_duplicates', col:'standardize_columns', text:'standardize_text', zsc:'standardize_numeric' };
  const selected = s.map(t => idMap[t.id]).filter(Boolean);
  (async () => {
    let lastData = null;
    for (const method of selected) {
      const response = await fetch('/clean', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({method}) });
      const data = await response.json();
      if (data.status === 'success') {
        lastData = data;
        cleanedData = data.full_data;
        displayPreview(data.preview);
        displayFullDataset(data.full_data);
        document.getElementById('card-missing').innerText = data.after_missing;
        document.getElementById('card-rows').innerText = data.rows;
      }
    }

    if (lastData && lastData.numeric_cols && lastData.categorical_cols) {
      if (datasetInfo) {
        datasetInfo.numeric_cols = lastData.numeric_cols;
        datasetInfo.categorical_cols = lastData.categorical_cols;
      }
      populateVizColumns({
        numeric_cols: lastData.numeric_cols,
        categorical_cols: lastData.categorical_cols
      });
      lastVizTab = null;
      lastVizParams = null;
      ['uni-num-charts','uni-cat-charts','bi-charts','multi-charts','cvn-charts','cvc-charts','nvn-charts'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
      });
    }

    document.getElementById('clean-status').textContent = 'Applied: ' + s.map(t=>t.label).join(', ');
    showToast('Cleaning selesai: ' + s.map(t=>t.label).join(', '), 'fa-check-circle', 'success');
    loadNumericalStats();
    loadCategoricalStats();
    loadInsights();

    // Re-generate timeseries setelah cleaning selesai diterapkan
    const tsCol = document.getElementById('ts-col-select')?.value;
    const dateCol = document.getElementById('date-column')?.value;
    if (dateCol && tsCol) generateTimeSeries();
  })();
}

function cwRefreshViz(el) {
  setCleanActive(el);
  refreshVisualizations();
  document.getElementById('clean-status').textContent='Visualizations refreshed';
}

function cwSaveDataset(el) {
  setCleanActive(el);
  saveCleanedDataset();
  document.getElementById('clean-status').textContent='Dataset saved';
}

function cwDownloadDataset(el) {
  setCleanActive(el);
  downloadCleanedDataset();
  document.getElementById('clean-status').textContent='Downloading...';
}

function cwToggleView(el,type) {
  ['btn-before','btn-after'].forEach(id=>document.getElementById(id).classList.remove('active'));
  el.classList.add('active');
  if(type==='before'){showBeforeData();}else{showAfterData();}
  document.getElementById('clean-status').textContent=type==='before'?'Showing data before cleaning':'Showing data after cleaning';
  showToast(type==='before'?'Menampilkan data sebelum cleaning':'Menampilkan data setelah cleaning', 'fa-eye', 'info');
}

const _origShowSection = showSection;
showSection = function(name, event) {
  _origShowSection(name, event);
  if (name === 'preview') renderCleanGrid();
};


window.addEventListener('resize', () => {
    document.querySelectorAll(
        '[id^="uni-"],[id^="bi-"],[id^="multi-"],[id^="cvn-"],[id^="cvc-"],[id^="nvn-"],[id^="ts-chart-"],[id^="dash-viz-"]'
    ).forEach(el => {

        if (
            el &&
            el.offsetWidth > 0 &&
            el.offsetHeight > 0 &&
            el.data
        ) {
            Plotly.Plots.resize(el);
        }

    });
});


// =====================================================
// ===== DASHBOARD OVERVIEW (landing page) =====
// =====================================================

function goToViz(tab, sub) {
    showVizTab(tab, null);
    if (sub) switchUniSub(sub, null);
}

function showMiniLoading(containerId) {
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = `<div style="text-align:center;padding:30px 10px;">
        <div class="spinner" style="width:28px;height:28px;border-width:3px;margin:8px auto;"></div>
    </div>`;
}

function miniEmptyMsg(text) {
    return `<div class="dash-mini-empty"><i class="fas fa-info-circle" style="margin-right:6px;"></i>${text}</div>`;
}

function loadDashboardOverview() {
    const emptyState = document.getElementById('dash-empty-state');
    const content    = document.getElementById('dash-content');
    if (!emptyState || !content) return;

    if (!datasetInfo) {
        emptyState.style.display = 'block';
        content.style.display = 'none';
        return;
    }

    emptyState.style.display = 'none';
    content.style.display = 'block';

    document.getElementById('dash-filename').textContent = datasetInfo.filename;
    document.getElementById('dash-filesize').textContent = datasetInfo.file_size;

    renderDashPreview(datasetInfo.preview.slice(0, 5));
    renderDashInsights();

    const btnAfter = document.getElementById('dash-btn-pdf-after');
    if (btnAfter) {
        fetch('/cleaning/status').then(r => r.json()).then(d => {
            btnAfter.classList.toggle('disabled-link', !d.is_cleaned);
            btnAfter.title = d.is_cleaned ? '' : 'Lakukan cleaning terlebih dahulu';
        }).catch(() => {});
    }

    Promise.all([
        fetch('/stats/numerical').then(r => r.json()),
        fetch('/stats/categorical').then(r => r.json())
    ]).then(([numStats, catStats]) => {
        window._colStats = { ...numStats, ...catStats };
        renderDashNumericalSummary(numStats);
        renderDashCategoricalSummary(catStats);
        renderMissingDonut(numStats, catStats);
        renderDataQuality();
    }).catch(err => console.error(err));

    loadDashMiniVisualizations();
}

// ----- Data Preview (first 5 rows) -----
function renderDashPreview(rows) {
    const headEl = document.getElementById('dash-preview-head');
    const bodyEl = document.getElementById('dash-preview-body');
    if (!headEl || !bodyEl) return;
    if (!rows || rows.length === 0) { headEl.innerHTML = ''; bodyEl.innerHTML = ''; return; }

    const columns = Object.keys(rows[0]);
    headEl.innerHTML = '<tr>' + columns.map(c => `<th>${c}</th>`).join('') + '</tr>';
    bodyEl.innerHTML = rows.map(row =>
        '<tr>' + columns.map(c => `<td>${row[c]}</td>`).join('') + '</tr>'
    ).join('');
}

// ----- Numerical Summary: condensed to key metrics only (full version lives in "Numerical Statistics") -----
function renderDashNumericalSummary(data) {
    const box = document.getElementById('dash-num-summary-wrap');
    if (!box) return;
    const cols = Object.keys(data);
    if (cols.length === 0) {
        box.innerHTML = '<div class="info-box" style="margin-bottom:0;">Tidak ada kolom numerik pada dataset ini.</div>';
        return;
    }

    const rows = [
        { label: 'Count',        get: c => datasetInfo.rows - data[c].missing_count },
        { label: 'Mean',         get: c => data[c].mean },
        { label: 'Std Dev',      get: c => data[c].std },
        { label: 'Missing (%)',  get: c => data[c].missing_percent + '%' },
        { label: 'Outliers (n)', get: c => data[c].outliers },
    ];

    let html = '<table><thead><tr><th>Statistic</th>' +
        cols.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
    rows.forEach(r => {
        html += `<tr><td style="color:#6c63ff;font-weight:600;">${r.label}</td>` +
            cols.map(c => `<td>${r.get(c)}</td>`).join('') + '</tr>';
    });
    html += '</tbody></table>';
    box.innerHTML = html;
}

// ----- Categorical Summary: capped to first 5 variables (full version lives in "Categorical Statistics") -----
function renderDashCategoricalSummary(data) {
    const box = document.getElementById('dash-cat-summary-wrap');
    if (!box) return;
    const allCols = Object.keys(data);
    if (allCols.length === 0) {
        box.innerHTML = '<div class="info-box" style="margin-bottom:0;">Tidak ada kolom kategorikal pada dataset ini.</div>';
        return;
    }

    const cols = allCols.slice(0, 5);
    let html = `<table><thead><tr>
        <th>Variable</th><th>Unique</th><th>Mode</th><th>Mode (%)</th>
    </tr></thead><tbody>`;
    cols.forEach(c => {
        const d = data[c];
        html += `<tr>
            <td style="color:#fff;font-weight:600;">${c}</td>
            <td>${d.unique}</td><td>${d.mode}</td><td>${d.mode_percent}%</td>
        </tr>`;
    });
    html += '</tbody></table>';
    if (allCols.length > 5) {
        html += `<p style="padding:10px 4px 0;color:#8b8fa8;font-size:0.78rem;">+${allCols.length - 5} kolom lainnya, lihat di Full Statistics</p>`;
    }
    box.innerHTML = html;
}

// ----- Automatic Insights (top 3, full list lives in "Insights") -----
function renderDashInsights() {
    const box = document.getElementById('dash-insights-list');
    if (!box) return;
    fetch('/insights')
        .then(r => r.json())
        .then(data => {
            if (!Array.isArray(data) || data.length === 0) {
                box.innerHTML = '<div class="info-box" style="margin-bottom:0;">Belum ada insight yang bisa ditampilkan.</div>';
                return;
            }
            const top = data.slice(0, 3);
            box.innerHTML = top.map(insight => `
                <div class="insight-item">
                    <i class="fas fa-lightbulb"></i>
                    <span>${insight}</span>
                </div>`).join('');
        })
        .catch(() => {
            box.innerHTML = '<div class="info-box" style="margin-bottom:0;">Gagal memuat insight.</div>';
        });
}

// ----- Missing Values Donut Chart -----
function renderMissingDonut(numStats, catStats) {
    const container = document.getElementById('dash-missing-donut');
    if (!container) return;

    const allCols = { ...numStats, ...catStats };
    const withMissing = Object.entries(allCols).filter(([, d]) => d.missing_count > 0);

    if (withMissing.length === 0) {
        container.innerHTML = `<div style="text-align:center;padding:40px 10px;color:#00c864;">
            <i class="fas fa-check-circle" style="font-size:2rem;"></i>
            <p style="margin-top:10px;">Tidak ada missing values ditemukan.</p>
        </div>`;
        return;
    }

    container.innerHTML = '';
    container.style.height = '280px';
    container.style.maxWidth = '100%';

    const labels = withMissing.map(([c]) => c);
    const values = withMissing.map(([, d]) => d.missing_percent);

    const trace = {
        type: 'pie',
        hole: 0.55,
        labels: labels,
        values: values,
        marker: { colors: CHART_COLORS },
        textinfo: 'label+percent',
        textfont: { color: '#fff', size: 11 },
    };
    const layout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#c0c0c0' },
        showlegend: true,
        legend: { orientation: 'v', font: { size: 11 } },
        margin: { l: 10, r: 10, t: 10, b: 10 },
        height: 280,
        autosize: true,
    };
    Plotly.newPlot(container.id, [trace], layout, { responsive: true, displayModeBar: false });
}

// ----- Data Quality Score -----
function renderDataQuality() {
    const box = document.getElementById('dash-quality-box');
    if (!box || !datasetInfo) return;

    // ==========================
    // Faktor 1 : Missing Values (45%)
    // ==========================
    const missingPct = datasetInfo.missing_percent || 0;
    const missingScore = Math.max(0, 100 - missingPct);

    // ==========================
    // Faktor 2 : Duplicate Rows (25%)
    // ==========================
    const dupPct = datasetInfo.duplicate_percent || 0;
    const dupScore = Math.max(0, 100 - dupPct);

    // ==========================
    // Faktor 3 : Outliers (20%)
    // ==========================
    const outlierPct = datasetInfo.outlier_percent || 0;
    const outlierScore = Math.max(
        0,
        100 - Math.min(outlierPct, 100)
    );

    // ==========================
    // Faktor 4 : Empty Columns (10%)
    // ==========================
    let allNullCols = 0;

    if (window._colStats && datasetInfo.columns) {
        allNullCols = Object.values(window._colStats)
            .filter(col => col.missing_count >= datasetInfo.rows)
            .length;
    }

    const allNullPct = datasetInfo.columns
        ? (allNullCols / datasetInfo.columns) * 100
        : 0;

    const allNullScore = Math.max(0, 100 - allNullPct);

    // ==========================
    // Final Score
    // ==========================
    const rawScore =
        missingScore * 0.45 +
        dupScore * 0.25 +
        outlierScore * 0.20 +
        allNullScore * 0.10;

    const score = Math.round(rawScore * 10) / 10;

    // ==========================
    // Label Kualitas
    // ==========================
    let label, color, desc;

    if (score >= 95) {
        label = 'Excellent';
        color = '#00c864';
        desc = 'Dataset sangat bersih dan siap dianalisis.';
    }
    else if (score >= 85) {
        label = 'Good';
        color = '#6c63ff';
        desc = 'Kualitas data baik dengan sedikit masalah.';
    }
    else if (score >= 70) {
        label = 'Fair';
        color = '#ffd700';
        desc = 'Perlu beberapa proses data cleaning.';
    }
    else {
        label = 'Needs Attention';
        color = '#ff6464';
        desc = 'Banyak masalah kualitas data ditemukan.';
    }

    // ==========================
    // Breakdown
    // ==========================
    const details = [
        {
            label: 'Missing Values',
            pct: missingPct,
            score: missingScore,
            weight: '45%'
        },
        {
            label: 'Baris Duplikat',
            pct: dupPct,
            score: dupScore,
            weight: '25%'
        },
        {
            label: 'Outliers',
            pct: outlierPct,
            score: outlierScore,
            weight: '20%'
        },
        {
            label: 'Kolom Kosong Total',
            pct: allNullPct,
            score: allNullScore,
            weight: '10%'
        }
    ];

    const detailRows = details.map(d => {

        const dColor =
            d.score >= 95 ? '#00c864' :
            d.score >= 85 ? '#6c63ff' :
            d.score >= 70 ? '#ffd700' :
            '#ff6464';

        return `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="color:#8b8fa8;font-size:0.78rem;">
                ${d.label}
                <span style="color:#555;font-size:0.7rem;">
                    (bobot ${d.weight})
                </span>
            </span>

            <span style="color:${dColor};font-weight:700;font-size:0.82rem;">
                ${d.score.toFixed(1)}%
                <span style="color:#555;font-size:0.7rem;">
                    (${d.pct.toFixed(2)}% bermasalah)
                </span>
            </span>
        </div>
        `;
    }).join('');

    // ==========================
    // Render UI
    // ==========================
    box.innerHTML = `
        <div style="text-align:center;padding:24px 10px 8px;">

            <i class="fas fa-shield-alt"
               style="font-size:2.2rem;color:${color};margin-bottom:10px;">
            </i>

            <h3 style="font-size:1.4rem;color:${color};margin-bottom:4px;">
                ${label}
            </h3>

            <p style="color:#8b8fa8;font-size:0.83rem;margin-bottom:14px;">
                ${desc}
            </p>

            <div style="
                background:#2d3148;
                border-radius:20px;
                height:14px;
                overflow:hidden;
            ">
                <div style="
                    background:${color};
                    height:100%;
                    width:${score}%;
                    border-radius:20px;
                    transition:width 0.6s;
                ">
                </div>
            </div>

            <p style="
                margin-top:8px;
                font-weight:700;
                color:#fff;
                font-size:1.1rem;
            ">
                ${score.toFixed(1)}%
            </p>

        </div>

        <div style="padding:0 16px 16px;">

            <p style="
                color:#8b8fa8;
                font-size:0.75rem;
                text-align:center;
                margin-bottom:10px;
                border-top:1px solid #2d3148;
                padding-top:10px;
            ">
                Breakdown Faktor Kualitas
            </p>

            ${detailRows}

        </div>
    `;
}

// ----- Mini Charts renderer (compact Plotly charts inside dashboard panels) -----
function renderMiniCharts(containerId, charts) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    charts.forEach((item, i) => {
        const card = document.createElement('div');
        card.className = 'dash-mini-chart-card';

        const title = document.createElement('div');
        title.className = 'dash-mini-chart-title';
        title.textContent = item.title;

        const chartEl = document.createElement('div');
        chartEl.id = containerId + '-c' + i;
        chartEl.style.cssText = 'height:190px;width:100%;max-width:100%;min-width:0;';

        card.appendChild(title);
        card.appendChild(chartEl);
        container.appendChild(card);

        const parsed = JSON.parse(item.chart);
        parsed.layout.paper_bgcolor = 'transparent';
        parsed.layout.plot_bgcolor  = 'rgba(255,255,255,0.04)';
        parsed.layout.margin        = { l: 36, r: 10, t: 8, b: 30 };
        parsed.layout.autosize      = true;
        parsed.layout.font          = { size: 9, color: '#f0f0ff' };
        if (parsed.layout.legend) parsed.layout.legend.font = { size: 8, color: '#f0f0ff' };
        delete parsed.layout.width;
        parsed.layout.height = 190;

        Plotly.newPlot(chartEl.id, parsed.data, parsed.layout, { responsive: true, displayModeBar: false });
    });
}

// ----- Mini Visualizations (auto-generated, real data, no manual column selection) -----
async function loadDashMiniVisualizations() {
    if (!datasetInfo) return;
    const numCols = datasetInfo.numeric_cols;
    const catCols = datasetInfo.categorical_cols;

    // Tampilkan loading semua panel sekaligus
    ['dash-viz-numuni','dash-viz-catuni','dash-viz-numnum','dash-viz-catnum','dash-viz-catcat','dash-viz-numnum2','dash-viz-timeseries']
        .forEach(id => showMiniLoading(id));

    // Helper fetch dengan error handling
    const safeFetch = async (url, opts) => {
        try {
            const r = await fetch(url, opts);
            return await r.json();
        } catch(e) { return { error: e.message }; }
    };

    // Buat semua promise sekaligus (parallel)
    const p_numuni = numCols.length > 0
        ? safeFetch('/visualize/univariate', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ column: numCols[0], var_type: 'numerical' })
          })
        : Promise.resolve(null);

    const p_catuni = catCols.length > 0
        ? safeFetch('/visualize/univariate', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ column: catCols[0], var_type: 'categorical' })
          })
        : Promise.resolve(null);

    const p_numnum = numCols.length >= 2
        ? safeFetch('/visualize/bivariate', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ col1: numCols[0], col2: numCols[1] })
          })
        : Promise.resolve(null);

    const p_catnum = (numCols.length >= 1 && catCols.length >= 1)
        ? safeFetch('/visualize/cat-vs-num', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ num_col: numCols[0], cat_col: catCols[0] })
          })
        : Promise.resolve(null);

    const p_catcat = catCols.length >= 2
        ? safeFetch('/visualize/cat-vs-cat', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ col1: catCols[0], col2: catCols[1] })
          })
        : Promise.resolve(null);

    const p_numnum2 = numCols.length >= 2
        ? safeFetch('/visualize/num-vs-num', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ col1: numCols[0], col2: numCols[1] })
          })
        : Promise.resolve(null);

    // Time series: 2 request berantai tapi parallel dg yang lain
    const p_ts = safeFetch('/timeseries').then(async tsCols => {
        if (tsCols.error || !tsCols.date_cols || !tsCols.date_cols.length || !tsCols.numeric_cols.length)
            return null;
        const chosenNumeric = tsCols.numeric_cols.slice(0, 2);
        const data = await safeFetch('/generate_timeseries', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ date_col: tsCols.date_cols[0], numeric_cols: chosenNumeric })
        });
        return data.error ? null : { data, chosenNumeric };
    });

    // Tunggu semua selesai bersamaan
    const [numuni, catuni, numnum, catnum, catcat, numnum2, ts] = await Promise.all([p_numuni, p_catuni, p_numnum, p_catnum, p_catcat, p_numnum2, p_ts]);

    // Render Numerical Univariate
    if (numuni && !numuni.error) {
        renderMiniCharts('dash-viz-numuni', numuni.charts.slice(0, 2));
        document.getElementById('dash-viewall-numuni').innerHTML =
            `View All (${numuni.charts.length}) <i class="fas fa-arrow-right"></i>`;
    } else {
        document.getElementById('dash-viz-numuni').innerHTML = miniEmptyMsg('Tidak ada kolom numerik.');
    }

    // Render Categorical Univariate
    if (catuni && !catuni.error) {
        renderMiniCharts('dash-viz-catuni', catuni.charts.slice(0, 2));
        document.getElementById('dash-viewall-catuni').innerHTML =
            `View All (${catuni.charts.length}) <i class="fas fa-arrow-right"></i>`;
    } else {
        document.getElementById('dash-viz-catuni').innerHTML = miniEmptyMsg('Tidak ada kolom kategorikal.');
    }

    // Render Numerical vs Numerical
    if (numnum && !numnum.error) {
        renderMiniCharts('dash-viz-numnum', numnum.charts.slice(0, 2));
        document.getElementById('dash-viewall-numnum').innerHTML =
            `View All (${numnum.charts.length}) <i class="fas fa-arrow-right"></i>`;
    } else {
        document.getElementById('dash-viz-numnum').innerHTML = miniEmptyMsg('Minimal butuh 2 kolom numerik.');
    }

    // Render Categorical vs Numerical
    if (catnum && !catnum.error) {
        const picks = [catnum.charts[0], catnum.charts[2]].filter(Boolean);
        renderMiniCharts('dash-viz-catnum', picks);
        document.getElementById('dash-viewall-catnum').innerHTML =
            `View All (${catnum.charts.length}) <i class="fas fa-arrow-right"></i>`;
    } else {
        document.getElementById('dash-viz-catnum').innerHTML = miniEmptyMsg('Butuh kolom numerik & kategorikal.');
    }

    // Render Categorical vs Categorical
    if (catcat && !catcat.error) {
        renderMiniCharts('dash-viz-catcat', catcat.charts.slice(0, 2));
        const el = document.getElementById('dash-viewall-catcat');
        if (el) el.innerHTML = `View All (${catcat.charts.length}) <i class="fas fa-arrow-right"></i>`;
    } else {
        const el = document.getElementById('dash-viz-catcat');
        if (el) el.innerHTML = miniEmptyMsg('Minimal butuh 2 kolom kategorikal.');
    }

    // Render Numerical vs Numerical (num-vs-num)
    if (numnum2 && !numnum2.error) {
        renderMiniCharts('dash-viz-numnum2', numnum2.charts.slice(0, 2));
        const el = document.getElementById('dash-viewall-numnum2');
        if (el) el.innerHTML = `View All (${numnum2.charts.length}) <i class="fas fa-arrow-right"></i>`;
    } else {
        const el = document.getElementById('dash-viz-numnum2');
        if (el) el.innerHTML = miniEmptyMsg('Minimal butuh 2 kolom numerik.');
    }

    // Render Time Series
    if (ts && ts.data && !ts.data.error && ts.data.charts) {
        const charts = ts.data.charts.map((c, i) => ({ title: `${ts.chosenNumeric[i]} Over Time`, chart: c }));
        renderMiniCharts('dash-viz-timeseries', charts);
        document.getElementById('dash-viewall-timeseries').innerHTML =
            `View Full Analysis <i class="fas fa-arrow-right"></i>`;
    } else {
        document.getElementById('dash-viz-timeseries').innerHTML = miniEmptyMsg('Tidak ada kolom tanggal terdeteksi pada dataset ini.');
    }
}